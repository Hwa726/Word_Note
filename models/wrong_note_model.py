# 2025-11-03 - 스마트 단어장 - 오답노트 데이터 모델
# 파일 위치: models/wrong_note_model.py

from typing import List, Dict, Optional
from datetime import datetime

from common.base_model import BaseModel
from common.logger import get_logger

_logger = get_logger(__name__)


class WrongNoteModel(BaseModel):
    """
    오답노트 데이터 모델

    담당 테이블:
    - wrong_note: 오답 단어 관리
    """

    def __init__(self):
        super().__init__('wrong_note')
        _logger.info("WrongNoteModel 초기화")

    def add_wrong_word(self, word_id: int, exam_id: int = None) -> int:
        """
        오답 단어 추가

        Args:
            word_id: 단어 ID
            exam_id: 시험 ID (사용 안 함, 하위 호환성 유지)

        Returns:
            note_id: 생성된 오답노트 ID
        """
        try:
            # 중복 체크
            if self.exists('word_id = ?', (word_id,)):
                _logger.debug(f"이미 오답노트에 존재: word_id={word_id}")
                # 이미 존재하는 경우 기존 note_id 반환
                result = self.db.execute_query(
                    'SELECT note_id FROM wrong_note WHERE word_id = ?',
                    (word_id,)
                )
                return result[0]['note_id'] if result else 0

            # 새로운 오답 추가
            note_data = {
                'word_id': word_id,
                'added_date': self.get_current_datetime(),
                'last_review_date': None,
                'review_count': 0
            }

            note_id = self.insert(note_data)
            _logger.info(f"오답 단어 추가: note_id={note_id}, word_id={word_id}")
            return note_id

        except Exception as e:
            _logger.error(f"오답 단어 추가 실패: {e}", exc_info=True)
            raise

    def get_wrong_words(self, filter_type: str = 'all') -> List[dict]:
        """
        오답 단어 조회

        Args:
            filter_type: 'all' (사용 안 함, 하위 호환성 유지)

        Returns:
            오답 단어 리스트 (단어 정보 + 오답률 + 복습 횟수)
        """
        try:
            # 기본 쿼리
            sql = """
                SELECT
                    wn.note_id,
                    wn.word_id,
                    wn.added_date,
                    wn.last_review_date,
                    wn.review_count,
                    w.english,
                    w.korean,
                    w.memo,
                    ws.total_attempts,
                    ws.correct_count,
                    ws.wrong_count,
                    ws.last_study_date
                FROM wrong_note wn
                JOIN words w ON wn.word_id = w.word_id
                LEFT JOIN word_statistics ws ON wn.word_id = ws.word_id
                ORDER BY wn.added_date DESC
            """

            results = self.db.execute_query(sql)

            # 오답률 계산 추가
            for result in results:
                total = result.get('total_attempts') or 0
                wrong = result.get('wrong_count') or 0
                if total > 0:
                    result['wrong_rate'] = round(wrong / total * 100, 1)
                else:
                    result['wrong_rate'] = 0.0

            _logger.debug(f"오답 단어 조회: {len(results)}개, filter={filter_type}")
            return results

        except Exception as e:
            _logger.error(f"오답 단어 조회 실패: {e}", exc_info=True)
            return []

    def update_review(self, note_id: int) -> bool:
        """
        복습 정보 업데이트

        Args:
            note_id: 오답노트 ID

        Returns:
            성공 여부
        """
        try:
            # 현재 정보 조회
            note = self.find_by_id(note_id, 'note_id')
            if not note:
                return False

            # 복습 카운트 증가
            review_count = note.get('review_count', 0) + 1

            success = self.update(
                'note_id',
                note_id,
                {
                    'last_review_date': self.get_current_datetime(),
                    'review_count': review_count
                }
            )

            if success:
                _logger.info(f"복습 정보 업데이트: note_id={note_id}, review_count={review_count}")

            return success

        except Exception as e:
            _logger.error(f"복습 정보 업데이트 오류: {e}", exc_info=True)
            return False

    def delete_note(self, note_id: int) -> bool:
        """
        오답노트 항목 삭제

        Args:
            note_id: 오답노트 ID

        Returns:
            성공 여부
        """
        try:
            success = self.delete('note_id', note_id)

            if success:
                _logger.info(f"오답노트 항목 삭제: note_id={note_id}")
            else:
                _logger.warning(f"오답노트 항목 삭제 실패: note_id={note_id}")

            return success

        except Exception as e:
            _logger.error(f"오답노트 항목 삭제 오류: {e}", exc_info=True)
            return False

    def auto_add_from_exam(self, exam_id: int) -> int:
        """
        시험에서 틀린 문제 자동 추가

        Args:
            exam_id: 시험 ID

        Returns:
            추가된 항목 수
        """
        try:
            # exam_details에서 틀린 문제 조회
            sql = """
                SELECT DISTINCT word_id
                FROM exam_details
                WHERE exam_id = ? AND is_correct = 0
            """
            wrong_words = self.db.execute_query(sql, (exam_id,))

            added_count = 0
            for word in wrong_words:
                note_id = self.add_wrong_word(word['word_id'], exam_id)
                if note_id > 0:
                    added_count += 1

            _logger.info(
                f"시험 오답 자동 추가: exam_id={exam_id}, "
                f"추가={added_count}개"
            )

            return added_count

        except Exception as e:
            _logger.error(f"시험 오답 자동 추가 실패: {e}", exc_info=True)
            return 0

    def get_count(self) -> int:
        """
        오답 단어 개수 조회

        Returns:
            오답 단어 개수
        """
        return self.count()


# ==============================================================================
# 테스트 코드
# ==============================================================================

if __name__ == '__main__':
    from common.db_connection import get_db_connection
    import config

    print("=== WrongNoteModel 테스트 ===\n")

    # 환경 설정
    config.ensure_directories()

    # DB 연결
    db = get_db_connection()
    model = WrongNoteModel()

    # 테스트용 단어 ID (실제 DB에 있는 단어 ID 사용)
    sql = "SELECT word_id FROM words LIMIT 3"
    test_words = db.execute_query(sql)

    if not test_words:
        print("[!] 단어 데이터가 없습니다.")
    else:
        print(f"[OK] 테스트용 단어: {len(test_words)}개\n")

        # 테스트 1: 오답 단어 추가
        print("테스트 1: 오답 단어 추가")
        note_id1 = model.add_wrong_word(test_words[0]['word_id'])
        note_id2 = model.add_wrong_word(test_words[1]['word_id'], exam_id=1)
        print(f"  추가된 note_id: {note_id1}, {note_id2}\n")

        # 테스트 2: 오답 단어 조회
        print("테스트 2: 오답 단어 조회")
        all_notes = model.get_wrong_words()
        print(f"  전체 오답: {len(all_notes)}개")
        for note in all_notes[:3]:
            print(f"    ID={note['note_id']}, Word={note['english']}, "
                  f"ReviewCount={note['review_count']}")

        # 테스트 3: 복습 정보 업데이트
        print("\n테스트 3: 복습 정보 업데이트")
        if all_notes:
            success = model.update_review(all_notes[0]['note_id'])
            print(f"  복습 업데이트 성공: {success}\n")

        # 테스트 4: 개수 조회
        print("테스트 4: 개수 조회")
        total = model.get_count()
        print(f"  전체 오답: {total}개")

        print("\n=== 테스트 완료 ===")
