# 2025-10-27 - 스마트 단어장 - 학습 모델 (SM-2 알고리즘 기반) - 수정본
# 파일 위치: models/learning_model.py

import datetime
from typing import List, Dict, Any, Optional

from common.db_connection import get_db_connection 
from common.base_model import BaseModel
from common.logger import get_logger 

# 학습 관련 상수 정의
SM2_INITIAL_EASE_FACTOR = 2.5
SM2_MIN_EASE_FACTOR = 1.3
DEFAULT_DAILY_GOAL = 50

_logger = get_logger('learning_model')

class LearningModel(BaseModel):
    """
    SuperMemo-2 (SM-2) 알고리즘을 기반으로 단어 학습을 관리하는 모델 클래스.
    - 학습할 단어 목록 선정
    - 학습 결과에 따른 통계 및 SM-2 파라미터(Ease Factor, Interval) 업데이트
    """
    
    TABLE_NAME = "words"

    def __init__(self):
        super().__init__(self.TABLE_NAME)
        
    def _calculate_sm2_params(self, old_ef: float, interval: int, quality: int) -> tuple[float, int]:
        """SM-2 알고리즘 파라미터를 계산합니다."""
        if quality < 3:
            # 오답 (0, 1, 2)
            new_ef = old_ef
            next_interval = 0
        else:
            # 정답 (3, 4, 5)
            new_ef = old_ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            # EF 최소값 제한
            if new_ef < SM2_MIN_EASE_FACTOR:
                new_ef = SM2_MIN_EASE_FACTOR
            
            if interval == 0:
                # 첫 번째 정답
                next_interval = 1
            elif interval == 1:
                # 두 번째 정답
                next_interval = 6
            else:
                # 세 번째 이후 정답
                next_interval = round(interval * new_ef)
        
        # 간격은 최소 1일 보장
        if next_interval < 1 and quality >= 3:
            next_interval = 1

        return new_ef, next_interval

    def update_word_after_learning(self, word_id: int, quality: int) -> bool:
        """
        단어 학습 결과(Quality 0~5)를 DB에 반영하고 SM-2 파라미터를 업데이트합니다.
        """
        try:
            current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            is_correct = 1 if quality >= 3 else 0
            
            # 1. 학습 이력 기록
            self.db.execute_non_query(
                """
                INSERT INTO learning_history (word_id, study_date, is_correct, response_time, study_type)
                VALUES (?, ?, ?, ?, 'flashcard')
                """,
                (word_id, current_date, is_correct, 0)
            )
            
            # 2. 통계 업데이트 (total_attempts, correct_count, wrong_count)
            # 먼저 통계 레코드가 있는지 확인
            stats_check = self.db.execute_query(
                "SELECT word_id FROM word_statistics WHERE word_id = ?",
                (word_id,)
            )
            
            if not stats_check:
                # 통계 레코드가 없으면 생성
                self.db.execute_non_query(
                    """
                    INSERT INTO word_statistics (word_id, total_attempts, correct_count, wrong_count, ease_factor, interval_days)
                    VALUES (?, 1, ?, ?, ?, 0)
                    """,
                    (word_id, is_correct, 1 - is_correct, SM2_INITIAL_EASE_FACTOR)
                )
            else:
                # 통계 레코드가 있으면 업데이트
                self.db.execute_non_query(
                    """
                    UPDATE word_statistics SET
                        total_attempts = total_attempts + 1,
                        correct_count = correct_count + ?,
                        wrong_count = wrong_count + ?
                    WHERE word_id = ?
                    """,
                    (is_correct, 1 - is_correct, word_id)
                )

            # 3. SM-2 파라미터 계산 및 업데이트
            stats = self.db.execute_query(
                "SELECT ease_factor, interval_days FROM word_statistics WHERE word_id = ?",
                (word_id,)
            )
            
            if stats and len(stats) > 0:
                old_ef = stats[0].get('ease_factor', SM2_INITIAL_EASE_FACTOR)
                interval = stats[0].get('interval_days', 0)
            else:
                old_ef = SM2_INITIAL_EASE_FACTOR
                interval = 0
            
            new_ef, next_interval = self._calculate_sm2_params(old_ef, interval, quality)
            
            next_study_date = (datetime.datetime.now() + datetime.timedelta(days=next_interval)).strftime("%Y-%m-%d 00:00:00")
            
            self.db.execute_non_query(
                """
                UPDATE word_statistics SET 
                    ease_factor = ?, 
                    interval_days = ?, 
                    next_study_date = ?,
                    last_study_date = ?
                WHERE word_id = ?
                """,
                (new_ef, next_interval, next_study_date, current_date, word_id)
            )
            
            _logger.info(f"단어 {word_id} 학습 결과 반영 완료: Q={quality}, EF={new_ef:.2f}, Next Interval={next_interval}일")
            return True

        except Exception as e:
            _logger.error(f"단어 {word_id} 학습 결과 반영 실패: {e}", exc_info=True)
            return False

    def get_learning_words(self, limit: int, learning_mode: str) -> List[Dict[str, Any]]:
        """
        학습할 단어 목록을 선정하여 반환합니다. (개인화 알고리즘 적용)
        
        Args:
            limit: 최대 단어 수
            learning_mode: 학습 모드 ('EN_TO_KR', 'KR_TO_EN', 'MIXED')
            
        Returns:
            학습할 단어 목록 (딕셔너리 리스트)
        """
        # 1. 복습이 필요한 단어 (next_study_date가 현재 날짜 이전인 단어)
        review_date_condition = "T1.next_study_date IS NULL OR T1.next_study_date <= date('now')"
        
        # 2. 전체 학습 시도 횟수가 0인 단어 (신규 단어)
        new_word_condition = "T1.total_attempts IS NULL OR T1.total_attempts = 0"

        # 3. 통계가 있는 단어와 없는 단어를 합쳐 오늘 학습할 단어를 선정
        # next_study_date가 가장 오래된 단어(즉, 복습 시기가 가장 오래된 단어)부터 가져옴
        query = f"""
            SELECT T0.*, 
                   COALESCE(T1.total_attempts, 0) AS total_attempts,
                   COALESCE(T1.correct_count, 0) AS correct_count,
                   COALESCE(T1.wrong_count, 0) AS wrong_count,
                   T1.next_study_date,
                   T1.ease_factor,
                   T1.last_study_date,
                   CASE 
                       WHEN T1.total_attempts > 0 THEN 
                           ROUND((T1.wrong_count * 100.0 / T1.total_attempts), 1)
                       ELSE NULL 
                   END AS wrong_rate
            FROM words AS T0
            LEFT JOIN word_statistics AS T1 ON T0.word_id = T1.word_id
            WHERE {review_date_condition} OR {new_word_condition}
            ORDER BY T1.next_study_date ASC, T0.word_id ASC
            LIMIT ?
        """
        
        words = self.db.execute_query(query, (limit,))
        _logger.info(f"학습할 단어 {len(words)}개 선정 완료. 목표: {limit}개, 모드: {learning_mode}")
        return words
