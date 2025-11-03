# 2025-11-03 - 스마트 단어장 - 학습 개인화 알고리즘
# 파일 위치: common/personalization.py

import random
from typing import List, Dict
from common.logger import get_logger

_logger = get_logger(__name__)


class PersonalizationEngine:
    """
    학습 개인화 알고리즘 엔진

    주요 기능:
    - 오답률 기반 가중치 계산
    - 가중치 기반 단어 선택 (오답률 높은 단어 자주 출제)
    - Ease Factor 업데이트 (간격 반복 학습 알고리즘)
    """

    def __init__(self, db_connection):
        """
        개인화 엔진 초기화

        Args:
            db_connection: 데이터베이스 연결 객체
        """
        self.db = db_connection
        _logger.info("PersonalizationEngine 초기화")

    def calculate_weights(self, words: List[dict]) -> Dict[int, float]:
        """
        단어별 가중치 계산

        가중치 공식:
        weight = 1.0 + (wrong_count / total_attempts) * 2.0

        - 신규 단어 (학습 이력 없음): weight = 1.5
        - 오답률 0%: weight = 1.0
        - 오답률 50%: weight = 2.0
        - 오답률 100%: weight = 3.0

        Args:
            words: 단어 정보 리스트
                   각 단어는 {'word_id', 'total_attempts', 'wrong_count'} 포함

        Returns:
            {word_id: weight} 딕셔너리
        """
        weights = {}

        for word in words:
            word_id = word['word_id']
            total_attempts = word.get('total_attempts', 0)
            wrong_count = word.get('wrong_count', 0)

            if total_attempts == 0:
                # 신규 단어: 중간 가중치
                weight = 1.5
            else:
                # 오답률 기반 가중치
                wrong_rate = wrong_count / total_attempts
                weight = 1.0 + (wrong_rate * 2.0)

            weights[word_id] = weight

        _logger.debug(f"가중치 계산 완료: {len(weights)}개 단어")
        return weights

    def get_weighted_words(self, words: List[dict], count: int) -> List[dict]:
        """
        가중치 기반 단어 선택

        알고리즘:
        1. 모든 단어의 가중치 계산
        2. 가중치 기반 확률 분포 생성
        3. 가중치에 비례하여 단어 선택 (중복 없이)

        Args:
            words: 단어 리스트
            count: 선택할 단어 개수

        Returns:
            선택된 단어 리스트 (오답률 높은 단어가 더 많이 포함됨)
        """
        if not words:
            _logger.warning("선택할 단어가 없습니다")
            return []

        # 요청 개수가 전체 단어 개수보다 많으면 전체 반환
        if count >= len(words):
            _logger.info(f"요청 개수({count})가 전체 단어 수({len(words)})보다 많음 - 전체 반환")
            return words

        # 가중치 계산
        weights = self.calculate_weights(words)

        # 가중치 리스트 생성
        weight_list = [weights.get(word['word_id'], 1.0) for word in words]

        # 가중치 기반 랜덤 선택 (중복 없이)
        try:
            selected_words = random.choices(
                words,
                weights=weight_list,
                k=count
            )

            # 중복 제거 (혹시 모를 경우 대비)
            seen_ids = set()
            unique_words = []
            for word in selected_words:
                if word['word_id'] not in seen_ids:
                    unique_words.append(word)
                    seen_ids.add(word['word_id'])

            _logger.info(f"가중치 기반 단어 선택 완료: {len(unique_words)}개")
            return unique_words

        except Exception as e:
            _logger.error(f"가중치 기반 선택 실패: {e} - 랜덤 선택으로 대체")
            # 실패 시 일반 랜덤 선택
            return random.sample(words, count)

    def update_ease_factor(self, word_id: int, is_correct: bool) -> None:
        """
        Ease Factor 업데이트 (간격 반복 학습 알고리즘)

        SuperMemo SM-2 알고리즘 간소화 버전:
        - 정답: ease_factor += 0.1 (최대 2.5)
        - 오답: ease_factor -= 0.2 (최소 1.3)
        - interval_days = interval_days * ease_factor

        Args:
            word_id: 단어 ID
            is_correct: 정답 여부
        """
        try:
            # 현재 통계 조회
            query = """
                SELECT ease_factor, interval_days
                FROM word_statistics
                WHERE word_id = ?
            """
            result = self.db.execute_query(query, (word_id,))

            if not result:
                # 통계가 없으면 초기화
                ease_factor = 2.5
                interval_days = 1
            else:
                ease_factor = result[0].get('ease_factor', 2.5)
                interval_days = result[0].get('interval_days', 1)

            # Ease Factor 업데이트
            if is_correct:
                ease_factor = min(ease_factor + 0.1, 2.5)
                interval_days = int(interval_days * ease_factor)
            else:
                ease_factor = max(ease_factor - 0.2, 1.3)
                interval_days = max(1, int(interval_days * 0.5))

            # 데이터베이스 업데이트
            update_query = """
                UPDATE word_statistics
                SET ease_factor = ?, interval_days = ?
                WHERE word_id = ?
            """
            self.db.execute_update(update_query, (ease_factor, interval_days, word_id))

            _logger.debug(
                f"Ease Factor 업데이트: word_id={word_id}, "
                f"correct={is_correct}, ease_factor={ease_factor:.2f}, "
                f"interval_days={interval_days}"
            )

        except Exception as e:
            _logger.error(f"Ease Factor 업데이트 실패: {e}", exc_info=True)

    def calculate_next_review_date(self, word_id: int) -> str:
        """
        다음 복습 날짜 계산

        Args:
            word_id: 단어 ID

        Returns:
            다음 복습 날짜 (YYYY-MM-DD 형식)
        """
        try:
            from datetime import datetime, timedelta

            # 현재 통계 조회
            query = """
                SELECT interval_days, last_study_date
                FROM word_statistics
                WHERE word_id = ?
            """
            result = self.db.execute_query(query, (word_id,))

            if not result:
                # 통계가 없으면 내일
                next_date = datetime.now() + timedelta(days=1)
            else:
                interval_days = result[0].get('interval_days', 1)
                last_study_date = result[0].get('last_study_date')

                if last_study_date:
                    last_date = datetime.strptime(last_study_date, '%Y-%m-%d %H:%M:%S')
                    next_date = last_date + timedelta(days=interval_days)
                else:
                    next_date = datetime.now() + timedelta(days=interval_days)

            return next_date.strftime('%Y-%m-%d')

        except Exception as e:
            _logger.error(f"다음 복습 날짜 계산 실패: {e}", exc_info=True)
            from datetime import datetime, timedelta
            return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')


# ==============================================================================
# 테스트 코드
# ==============================================================================

if __name__ == '__main__':
    print("=== PersonalizationEngine 테스트 ===\n")

    # Mock DB connection (간단한 테스트용)
    class MockDB:
        def execute_query(self, query, params):
            # 테스트용 더미 데이터
            return [{'ease_factor': 2.5, 'interval_days': 3, 'last_study_date': '2025-11-01 12:00:00'}]

        def execute_update(self, query, params):
            return True

    # 엔진 생성
    engine = PersonalizationEngine(MockDB())

    # 테스트 1: 가중치 계산
    print("테스트 1: 가중치 계산")
    test_words = [
        {'word_id': 1, 'english': 'computer', 'total_attempts': 10, 'wrong_count': 8},  # 오답률 80%
        {'word_id': 2, 'english': 'apple', 'total_attempts': 10, 'wrong_count': 2},     # 오답률 20%
        {'word_id': 3, 'english': 'test', 'total_attempts': 10, 'wrong_count': 5},      # 오답률 50%
        {'word_id': 4, 'english': 'new', 'total_attempts': 0, 'wrong_count': 0},        # 신규
    ]

    weights = engine.calculate_weights(test_words)
    for word in test_words:
        wid = word['word_id']
        print(f"  word_id={wid}, english={word['english']}, weight={weights[wid]:.2f}")

    # 테스트 2: 가중치 기반 선택
    print("\n테스트 2: 가중치 기반 선택 (10개 선택, 100회 반복)")
    selection_count = {1: 0, 2: 0, 3: 0, 4: 0}

    for _ in range(100):
        selected = engine.get_weighted_words(test_words, 2)
        for word in selected:
            selection_count[word['word_id']] += 1

    print("  선택 횟수 (오답률 높을수록 많이 선택되어야 함):")
    for wid in sorted(selection_count.keys()):
        print(f"    word_id={wid}: {selection_count[wid]}회")

    # 테스트 3: Ease Factor 업데이트
    print("\n테스트 3: Ease Factor 업데이트")
    print("  정답 처리...")
    engine.update_ease_factor(1, is_correct=True)
    print("  오답 처리...")
    engine.update_ease_factor(1, is_correct=False)

    # 테스트 4: 다음 복습 날짜 계산
    print("\n테스트 4: 다음 복습 날짜 계산")
    next_date = engine.calculate_next_review_date(1)
    print(f"  다음 복습 날짜: {next_date}")

    print("\n=== 테스트 완료 ===")
