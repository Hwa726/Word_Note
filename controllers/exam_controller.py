# 2025-11-03 - 스마트 단어장 - 시험 컨트롤러
# 파일 위치: controllers/exam_controller.py

from typing import List, Dict, Optional
import time

from models.exam_model import ExamModel
from models.word_model import WordModel
from common.logger import get_logger

_logger = get_logger(__name__)


class ExamController:
    """
    시험 컨트롤러

    시험 시작, 답안 제출, 채점 등 시험 관련 비즈니스 로직을 담당
    """

    def __init__(self):
        self.exam_model = ExamModel()
        self.word_model = WordModel()

        # 현재 진행 중인 시험 정보
        self.current_exam = None
        self.current_questions = []
        self.user_answers = {}  # {question_number: answer}
        self.start_time = None

        _logger.info("ExamController 초기화")

    def start_exam(self, config: dict) -> dict:
        """
        시험 시작

        Args:
            config: {
                'exam_type': 'short_answer' | 'multiple_choice',
                'word_range': 'all' | 'favorites' | 'weak' | 'recent',
                'question_count': 20,
                'time_limit': 600  # 초 (선택)
            }

        Returns:
            {
                'exam_id': 123,
                'questions': [...],
                'total_count': 20,
                'time_limit': 600,
                'exam_type': 'multiple_choice'
            }
        """
        try:
            exam_type = config.get('exam_type', 'multiple_choice')
            word_range = config.get('word_range', 'all')
            question_count = config.get('question_count', 20)
            time_limit = config.get('time_limit', 600)

            # 1. 출제 범위에 따라 단어 선택
            words = self._select_words(word_range, question_count)

            if not words:
                _logger.error("출제할 단어가 없습니다")
                raise ValueError("출제할 단어가 없습니다")

            # 2. 시험 생성
            exam_id = self.exam_model.create_exam(exam_type, len(words))

            # 3. 문제 생성
            questions = self.exam_model.generate_questions(words, exam_type)

            # 4. 현재 시험 정보 저장
            self.current_exam = {
                'exam_id': exam_id,
                'exam_type': exam_type,
                'time_limit': time_limit,
                'total_count': len(questions)
            }
            self.current_questions = questions
            self.user_answers = {}
            self.start_time = time.time()

            _logger.info(
                f"시험 시작: exam_id={exam_id}, type={exam_type}, "
                f"questions={len(questions)}, time_limit={time_limit}초"
            )

            return {
                'exam_id': exam_id,
                'questions': questions,
                'total_count': len(questions),
                'time_limit': time_limit,
                'exam_type': exam_type
            }

        except Exception as e:
            _logger.error(f"시험 시작 실패: {e}", exc_info=True)
            raise

    def _select_words(self, word_range: str, count: int) -> List[dict]:
        """
        출제 범위에 따라 단어 선택

        Args:
            word_range: 'all' | 'favorites' | 'weak' | 'recent'
            count: 선택할 단어 개수

        Returns:
            단어 리스트
        """
        if word_range == 'all':
            words = self.word_model.get_all_words()
        elif word_range == 'favorites':
            words = self.word_model.get_favorite_words()
        elif word_range == 'weak':
            words = self.word_model.get_weak_words(limit=count)
        elif word_range == 'recent':
            words = self.word_model.get_recently_learned_words(limit=count)
        else:
            _logger.warning(f"알 수 없는 출제 범위: {word_range}, 전체 단어 사용")
            words = self.word_model.get_all_words()

        # 요청 개수만큼 랜덤 선택
        import random
        if len(words) > count:
            words = random.sample(words, count)

        return words

    def submit_answer(self, question_number: int, answer: str) -> None:
        """
        답변 제출 (임시 저장)

        Args:
            question_number: 문제 번호 (1부터 시작)
            answer: 사용자 답변
        """
        self.user_answers[question_number] = answer
        _logger.debug(f"답변 제출: Q{question_number} = {answer}")

    def finish_exam(self) -> dict:
        """
        시험 종료 및 채점

        Returns:
            {
                'exam_id': 123,
                'total': 20,
                'correct': 17,
                'wrong': 3,
                'score': 85.0,
                'time_taken': 543,
                'results': [...],  # 문제별 결과
                'wrong_questions': [...]  # 틀린 문제 리스트
            }
        """
        try:
            if not self.current_exam:
                raise ValueError("진행 중인 시험이 없습니다")

            # 1. 소요 시간 계산
            time_taken = int(time.time() - self.start_time)

            # 2. 채점
            results = self._grade_exam()

            # 3. 시험 결과 저장
            success = self.exam_model.save_exam_result(
                self.current_exam['exam_id'],
                results,
                time_taken
            )

            if not success:
                _logger.warning("시험 결과 저장 실패")

            # 4. 결과 요약
            correct_count = sum(1 for r in results if r['is_correct'])
            wrong_count = len(results) - correct_count
            score = (correct_count / len(results) * 100) if results else 0

            # 틀린 문제 리스트 생성
            wrong_questions = [
                {
                    'question_number': r['question_number'],
                    'word_id': r['word_id'],
                    'correct_answer': r['correct_answer'],
                    'user_answer': r['user_answer']
                }
                for r in results if not r['is_correct']
            ]

            result_summary = {
                'exam_id': self.current_exam['exam_id'],
                'total': len(results),
                'correct': correct_count,
                'wrong': wrong_count,
                'score': round(score, 2),
                'time_taken': time_taken,
                'results': results,
                'wrong_questions': wrong_questions
            }

            _logger.info(
                f"시험 완료: exam_id={self.current_exam['exam_id']}, "
                f"score={score:.1f}%, time={time_taken}초"
            )

            # 5. 현재 시험 정보 초기화
            self.current_exam = None
            self.current_questions = []
            self.user_answers = {}
            self.start_time = None

            return result_summary

        except Exception as e:
            _logger.error(f"시험 종료 실패: {e}", exc_info=True)
            raise

    def _grade_exam(self) -> List[dict]:
        """
        채점 로직

        Returns:
            문제별 채점 결과 리스트
        """
        results = []

        for question in self.current_questions:
            question_number = question['question_number']
            correct_answer = question['correct_answer'].strip().lower()
            user_answer = self.user_answers.get(question_number, '').strip().lower()

            # 정답 비교 (대소문자 구분 없음)
            is_correct = (user_answer == correct_answer)

            result = {
                'word_id': question['word_id'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'question_number': question_number
            }
            results.append(result)

        return results

    def get_exam_history(self, limit: int = 10) -> List[dict]:
        """
        시험 이력 조회

        Args:
            limit: 조회할 최대 개수

        Returns:
            시험 이력 리스트
        """
        return self.exam_model.get_exam_history(limit)

    def get_exam_details(self, exam_id: int) -> dict:
        """
        시험 상세 결과 조회

        Args:
            exam_id: 시험 ID

        Returns:
            시험 상세 정보 (시험 정보 + 문제별 결과)
        """
        # 시험 기본 정보
        exam_info = self.exam_model.find_by_id(exam_id, 'exam_id')
        if not exam_info:
            _logger.warning(f"시험 정보 없음: exam_id={exam_id}")
            return None

        # 문제별 상세 결과
        details = self.exam_model.get_exam_details(exam_id)

        return {
            'exam_info': exam_info,
            'details': details
        }


# ==============================================================================
# 테스트 코드
# ==============================================================================

if __name__ == '__main__':
    import config

    print("=== ExamController 테스트 ===\n")

    # 환경 설정
    config.ensure_directories()

    # 컨트롤러 생성
    controller = ExamController()

    # 테스트 1: 시험 시작
    print("테스트 1: 시험 시작")
    exam_config = {
        'exam_type': 'short_answer',
        'word_range': 'all',
        'question_count': 5,
        'time_limit': 300
    }

    try:
        exam_data = controller.start_exam(exam_config)
        print(f"  시험 ID: {exam_data['exam_id']}")
        print(f"  문제 수: {exam_data['total_count']}개")
        print(f"  시험 유형: {exam_data['exam_type']}\n")

        # 테스트 2: 답변 제출
        print("테스트 2: 답변 제출")
        for idx, q in enumerate(exam_data['questions'], start=1):
            # 홀수 문제만 정답 제출
            answer = q['correct_answer'] if idx % 2 == 1 else 'wrong_answer'
            controller.submit_answer(idx, answer)
            print(f"  Q{idx}: 제출 완료")

        # 테스트 3: 시험 종료
        print("\n테스트 3: 시험 종료 및 채점")
        result = controller.finish_exam()
        print(f"  총 문제: {result['total']}개")
        print(f"  정답: {result['correct']}개")
        print(f"  오답: {result['wrong']}개")
        print(f"  점수: {result['score']}점")
        print(f"  소요 시간: {result['time_taken']}초")

        # 테스트 4: 시험 이력 조회
        print("\n테스트 4: 시험 이력 조회")
        history = controller.get_exam_history(3)
        for exam in history:
            score = (exam['correct_count'] / exam['total_words'] * 100) if exam['total_words'] > 0 else 0
            print(f"  ID={exam['exam_id']}, Type={exam['exam_type']}, Score={score:.1f}%")

        print("\n=== 테스트 완료 ===")

    except Exception as e:
        print(f"[ERROR] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
