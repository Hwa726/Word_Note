# 2025-11-03 - 스마트 단어장 - 시험 데이터 모델
# 파일 위치: models/exam_model.py

import random
from typing import List, Dict, Optional
from datetime import datetime

from common.base_model import BaseModel
from common.logger import get_logger

_logger = get_logger(__name__)


class ExamModel(BaseModel):
    """
    시험 데이터 모델

    담당 테이블:
    - exam_history: 시험 기록
    - exam_details: 시험 문제별 상세 기록
    """

    def __init__(self):
        super().__init__('exam_history')
        _logger.info("ExamModel 초기화")

    def create_exam(self, exam_type: str, word_count: int) -> int:
        """
        시험 생성

        Args:
            exam_type: 'short_answer' 또는 'multiple_choice'
            word_count: 출제할 단어 개수

        Returns:
            exam_id: 생성된 시험 ID
        """
        try:
            exam_data = {
                'exam_date': self.get_current_datetime(),
                'exam_type': exam_type,
                'total_words': word_count,
                'correct_count': 0,           # 초기값
                'time_taken_seconds': 0       # 초기값
            }

            exam_id = self.insert(exam_data)
            _logger.info(f"시험 생성 완료: exam_id={exam_id}, type={exam_type}, questions={word_count}")
            return exam_id

        except Exception as e:
            _logger.error(f"시험 생성 실패: {e}", exc_info=True)
            raise

    def save_exam_result(self, exam_id: int, results: List[dict], time_taken: int) -> bool:
        """
        시험 결과 저장

        Args:
            exam_id: 시험 ID
            results: 문제별 결과 리스트 [
                {
                    'word_id': 1,
                    'user_answer': 'apple',
                    'correct_answer': 'apple',
                    'is_correct': True,
                    'response_time': 5.2,
                    'question_number': 1
                },
                ...
            ]
            time_taken: 총 소요 시간 (초)

        Returns:
            성공 여부
        """
        try:
            # 1. exam_details에 문제별 결과 저장
            for result in results:
                detail_data = {
                    'exam_id': exam_id,
                    'word_id': result['word_id'],
                    'user_answer': result['user_answer'],
                    'is_correct': 1 if result['is_correct'] else 0
                }

                # BaseModel의 insert는 exam_history 테이블에 삽입하므로 직접 SQL 실행
                sql = """
                    INSERT INTO exam_details
                    (exam_id, word_id, user_answer, is_correct)
                    VALUES (?, ?, ?, ?)
                """
                self.db.execute_non_query(sql, (
                    detail_data['exam_id'],
                    detail_data['word_id'],
                    detail_data['user_answer'],
                    detail_data['is_correct']
                ))

            # 2. exam_history 업데이트 (정답 수, 소요 시간)
            correct_count = sum(1 for r in results if r['is_correct'])
            total_questions = len(results)

            update_data = {
                'correct_count': correct_count,
                'time_taken_seconds': time_taken
            }

            success = self.update('exam_id', exam_id, update_data)

            if success:
                score = (correct_count / total_questions * 100) if total_questions > 0 else 0
                _logger.info(
                    f"시험 결과 저장 완료: exam_id={exam_id}, "
                    f"correct={correct_count}/{total_questions}, score={score:.1f}%"
                )
            else:
                _logger.warning(f"시험 결과 업데이트 실패: exam_id={exam_id}")

            return success

        except Exception as e:
            _logger.error(f"시험 결과 저장 실패: {e}", exc_info=True)
            return False

    def get_exam_history(self, limit: int = 10) -> List[dict]:
        """
        시험 이력 조회

        Args:
            limit: 조회할 최대 개수

        Returns:
            시험 이력 리스트 (최신순)
        """
        try:
            sql = f"""
                SELECT *
                FROM exam_history
                ORDER BY exam_date DESC
                LIMIT ?
            """
            results = self.db.execute_query(sql, (limit,))
            _logger.debug(f"시험 이력 조회: {len(results)}개")
            return results

        except Exception as e:
            _logger.error(f"시험 이력 조회 실패: {e}", exc_info=True)
            return []

    def get_exam_details(self, exam_id: int) -> List[dict]:
        """
        시험 상세 결과 조회

        Args:
            exam_id: 시험 ID

        Returns:
            문제별 상세 결과 (단어 정보 포함)
        """
        try:
            sql = """
                SELECT
                    ed.*,
                    w.english,
                    w.korean
                FROM exam_details ed
                JOIN words w ON ed.word_id = w.word_id
                WHERE ed.exam_id = ?
                ORDER BY ed.question_number
            """
            results = self.db.execute_query(sql, (exam_id,))
            _logger.debug(f"시험 상세 조회: exam_id={exam_id}, {len(results)}문제")
            return results

        except Exception as e:
            _logger.error(f"시험 상세 조회 실패: {e}", exc_info=True)
            return []

    def generate_questions(self, words: List[dict], exam_type: str) -> List[dict]:
        """
        문제 생성

        Args:
            words: 단어 리스트 (word_id, english, korean 포함)
            exam_type: 'short_answer' 또는 'multiple_choice'

        Returns:
            문제 리스트 [
                {
                    'word_id': 1,
                    'question_text': '다음 한국어의 영어를 입력하세요: 사과',
                    'correct_answer': 'apple',
                    'choices': ['apple', 'banana', 'orange', 'grape']  # 객관식만
                },
                ...
            ]
        """
        try:
            questions = []

            for idx, word in enumerate(words, start=1):
                question = {
                    'word_id': word['word_id'],
                    'question_number': idx,
                    'correct_answer': word['english']
                }

                if exam_type == 'short_answer':
                    question['question_text'] = f"다음 한국어의 영어를 입력하세요: {word['korean']}"
                    question['choices'] = None

                elif exam_type == 'multiple_choice':
                    question['question_text'] = f"다음 한국어의 영어를 고르세요: {word['korean']}"
                    question['choices'] = self.generate_choices(word, words)

                else:
                    raise ValueError(f"지원하지 않는 시험 유형: {exam_type}")

                questions.append(question)

            _logger.info(f"문제 생성 완료: {len(questions)}문제, type={exam_type}")
            return questions

        except Exception as e:
            _logger.error(f"문제 생성 실패: {e}", exc_info=True)
            raise

    def generate_choices(self, correct_word: dict, all_words: List[dict]) -> List[str]:
        """
        객관식 선지 생성

        알고리즘:
        1. 정답 포함
        2. 정답과 다른 단어 중 랜덤으로 3개 선택
        3. 선지 순서 랜덤 섞기

        Args:
            correct_word: 정답 단어 {'word_id', 'english', 'korean'}
            all_words: 전체 단어 리스트

        Returns:
            4개의 선지 리스트
        """
        try:
            correct_answer = correct_word['english']

            # 정답을 제외한 단어들
            other_words = [w for w in all_words if w['word_id'] != correct_word['word_id']]

            # 선지가 부족한 경우
            if len(other_words) < 3:
                _logger.warning(
                    f"선지 생성 경고: 단어 부족 (필요: 3개, 실제: {len(other_words)}개)"
                )
                # 부족한 만큼만 추가
                wrong_choices = [w['english'] for w in other_words]
            else:
                # 랜덤으로 3개 선택
                selected_words = random.sample(other_words, 3)
                wrong_choices = [w['english'] for w in selected_words]

            # 정답 포함하여 선지 생성
            choices = [correct_answer] + wrong_choices

            # 순서 랜덤 섞기
            random.shuffle(choices)

            return choices

        except Exception as e:
            _logger.error(f"선지 생성 실패: {e}", exc_info=True)
            # 실패 시 정답만 반환
            return [correct_word['english']]


# ==============================================================================
# 테스트 코드
# ==============================================================================

if __name__ == '__main__':
    from common.db_connection import get_db_connection
    import config

    print("=== ExamModel 테스트 ===\n")

    # 환경 설정
    config.ensure_directories()

    # DB 연결
    db = get_db_connection()
    model = ExamModel()

    # 테스트용 단어 데이터 (실제 DB에서 조회한다고 가정)
    test_words = []
    sql = "SELECT word_id, english, korean FROM words LIMIT 10"
    test_words = db.execute_query(sql)

    if not test_words:
        print("[!] 단어 데이터가 없습니다. 먼저 단어를 추가하세요.")
    else:
        print(f"[OK] 테스트용 단어: {len(test_words)}개\n")

        # 테스트 1: 시험 생성
        print("테스트 1: 시험 생성")
        exam_id = model.create_exam('multiple_choice', 5)
        print(f"  생성된 시험 ID: {exam_id}\n")

        # 테스트 2: 문제 생성
        print("테스트 2: 문제 생성")
        questions = model.generate_questions(test_words[:5], 'multiple_choice')
        print(f"  생성된 문제 수: {len(questions)}개")
        for q in questions[:2]:  # 처음 2문제만 출력
            print(f"    Q{q['question_number']}: {q['question_text']}")
            print(f"      선지: {q['choices']}")
            print(f"      정답: {q['correct_answer']}\n")

        # 테스트 3: 시험 결과 저장
        print("테스트 3: 시험 결과 저장")
        test_results = []
        for idx, q in enumerate(questions, start=1):
            result = {
                'word_id': q['word_id'],
                'user_answer': q['correct_answer'] if idx % 2 == 0 else 'wrong',  # 짝수만 정답
                'correct_answer': q['correct_answer'],
                'is_correct': (idx % 2 == 0),
                'response_time': 3.5,
                'question_number': idx
            }
            test_results.append(result)

        success = model.save_exam_result(exam_id, test_results, 120)
        print(f"  저장 성공: {success}\n")

        # 테스트 4: 시험 이력 조회
        print("테스트 4: 시험 이력 조회")
        history = model.get_exam_history(5)
        print(f"  조회된 시험 수: {len(history)}개")
        for exam in history[:3]:  # 최근 3개만 출력
            score = (exam['correct_count'] / exam['total_words'] * 100) if exam['total_words'] > 0 else 0
            print(f"    ID={exam['exam_id']}, Type={exam['exam_type']}, "
                  f"Score={score:.1f}%, Date={exam['exam_date']}")

        print("\n=== 테스트 완료 ===")
