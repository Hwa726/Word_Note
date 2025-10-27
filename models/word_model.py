# 2025-10-20 - 스마트 단어장 - 단어 모델
# 파일 위치: word_model.py

"""
단어 모델

단어 데이터베이스 접근 및 관리를 담당한다.
CRUD 작업, 검색, 필터링 기능을 제공한다.
"""

from typing import List, Dict, Any, Optional

from common.base_model import BaseModel
from common.logger import get_logger

logger = get_logger(__name__)


class WordModel(BaseModel):
    """
    단어 모델 클래스
    
    words 테이블에 대한 모든 데이터베이스 작업을 담당한다.
    """
    
    def __init__(self):
        # 💡 수정: 상위 클래스인 BaseModel에 테이블 이름 'words'를 전달해야 합니다.
        super().__init__(table_name='words') 
        logger.debug("WordModel 초기화")
    
    def add_word(self, english: str, korean: str, memo: str = "", is_favorite: int = 0) -> int:
        """
        새 단어를 추가한다.
        
        Args:
            english: 영어 단어
            korean: 한국어 뜻
            memo: 메모 (선택)
            is_favorite: 즐겨찾기 여부 (0 또는 1, 기본값 0)
        
        Returns:
            int: 추가된 단어의 ID
        
        Raises:
            ValueError: 유효성 검사 실패
        """
        # 유효성 검사
        self._validate_word(english, korean)
        
        # 중복 검사
        if self.exists('english = ?', (english,)):
            logger.warning(f"중복 단어 추가 시도: {english}")
            raise ValueError(f"이미 존재하는 단어입니다: {english}")
        
        # 데이터 삽입
        data = {
            'english': english.strip(),
            'korean': korean.strip(),
            'memo': memo.strip() if memo else '',
            'is_favorite': is_favorite,
            'created_date': self.get_current_datetime()
        }
        
        word_id = self.insert(data)
        logger.info(f"단어 추가 성공: {english} (ID: {word_id})")
        
        # 통계 테이블 초기화
        self._initialize_word_statistics(word_id)
        
        return word_id
    
    def update_word(self, word_id: int, english: str = None, 
                    korean: str = None, memo: str = None) -> bool:
        """
        단어를 수정한다.
        
        Args:
            word_id: 단어 ID
            english: 영어 단어 (None이면 변경 안 함)
            korean: 한국어 뜻 (None이면 변경 안 함)
            memo: 메모 (None이면 변경 안 함)
        
        Returns:
            bool: 수정 성공 여부
        """
        # 단어 존재 확인
        if not self.find_by_id(word_id):
            logger.warning(f"존재하지 않는 단어 수정 시도: ID {word_id}")
            raise ValueError(f"단어를 찾을 수 없습니다: ID {word_id}")
        
        # 수정할 데이터 구성
        data = {'modified_date': self.get_current_datetime()}
        
        if english is not None:
            data['english'] = english.strip()
        if korean is not None:
            data['korean'] = korean.strip()
        if memo is not None:
            data['memo'] = memo.strip()
        
        # 수정
        updated = self.update('word_id', word_id, data)
        
        if updated > 0:
            logger.info(f"단어 수정 성공: ID {word_id}")
            return True
        else:
            logger.warning(f"단어 수정 실패: ID {word_id}")
            return False
    
    def delete_word(self, word_id: int) -> bool:
        """
        단어를 삭제한다.
        
        Args:
            word_id: 단어 ID
        
        Returns:
            bool: 삭제 성공 여부
        """
        deleted = self.delete('word_id', word_id)
        
        if deleted > 0:
            logger.info(f"단어 삭제 성공: ID {word_id}")
            return True
        else:
            logger.warning(f"단어 삭제 실패: ID {word_id}")
            return False
    
    def get_word(self, word_id: int) -> Optional[Dict[str, Any]]:
        """
        단어 ID로 단어를 조회한다.
        
        Args:
            word_id: 단어 ID
        
        Returns:
            Optional[Dict]: 단어 정보 (없으면 None)
        """
        word = self.find_by_id(word_id)
        
        if word:
            # 통계 정보 추가
            word = self._enrich_word_with_stats(word)
        
        return word
    
    def get_all_words(self, offset: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        모든 단어를 조회한다.
        
        Args:
            offset: 시작 위치
            limit: 최대 개수
        
        Returns:
            List[Dict]: 단어 목록
        """
        words = self.find_all('words', order_by='created_date DESC', limit=limit, offset=offset)
        
        # 각 단어에 통계 정보 추가
        enriched_words = [self._enrich_word_with_stats(word) for word in words]
        
        logger.debug(f"단어 조회: {len(enriched_words)}개")
        return enriched_words
    
    def search_words(self, keyword: str) -> List[Dict[str, Any]]:
        """
        키워드로 단어를 검색한다.
        
        Args:
            keyword: 검색 키워드
        
        Returns:
            List[Dict]: 검색 결과
        """
        query = """
            SELECT * FROM words 
            WHERE english LIKE ? OR korean LIKE ? OR memo LIKE ?
            ORDER BY english ASC
        """
        
        search_pattern = f"%{keyword}%"
        results = self._execute_query(query, (search_pattern, search_pattern, search_pattern))
        
        enriched_results = [self._enrich_word_with_stats(word) for word in results]
        
        logger.info(f"단어 검색: '{keyword}' -> {len(enriched_results)}개")
        return enriched_results
    
    def get_word_count(self) -> int:
        """
        전체 단어 개수를 조회한다.
        
        Returns:
            int: 단어 개수
        """
        return self.count()
    
    def toggle_favorite(self, word_id: int) -> bool:
        """
        즐겨찾기 상태를 토글한다.
        
        Args:
            word_id: 단어 ID
        
        Returns:
            bool: 새로운 즐겨찾기 상태
        """
        word = self.find_by_id(word_id)
        if not word:
            return False
        
        new_favorite = 0 if word['is_favorite'] == 1 else 1
        self.update('word_id', word_id, {
            'is_favorite': new_favorite,
            'modified_date': self.get_current_datetime()
        })
        
        logger.info(f"즐겨찾기 토글: ID {word_id} -> {new_favorite}")
        return new_favorite == 1
    
    def _validate_word(self, english: str, korean: str):
        """단어 유효성 검사"""
        if not english or not english.strip():
            raise ValueError("영어 단어를 입력해주세요")
        
        if not korean or not korean.strip():
            raise ValueError("한국어 뜻을 입력해주세요")
        
        if len(english) > 100:
            raise ValueError("영어 단어는 100자를 초과할 수 없습니다")
        
        if len(korean) > 500:
            raise ValueError("한국어 뜻은 500자를 초과할 수 없습니다")
    
    def _initialize_word_statistics(self, word_id: int):
        """단어 통계 테이블 초기화"""
        try:
            data = {
                'word_id': word_id,
                'total_attempts': 0,
                'correct_count': 0,
                'wrong_count': 0,
                'ease_factor': 2.5,
                'interval_days': 0
            }
            # 다른 테이블에 삽입하므로 직접 SQL 사용
            sql = """
                INSERT INTO word_statistics (word_id, total_attempts, correct_count, wrong_count, ease_factor, interval_days)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db.execute_non_query(sql, (word_id, 0, 0, 0, 2.5, 0))
            logger.debug(f"단어 통계 초기화: ID {word_id}")
        except Exception as e:
            logger.error(f"단어 통계 초기화 실패: ID {word_id} - {e}")
    
    def _enrich_word_with_stats(self, word: Dict[str, Any]) -> Dict[str, Any]:
        """단어에 통계 정보 추가"""
        word_id = word['word_id']
        
        # 다른 테이블 조회이므로 직접 SQL 사용
        sql = "SELECT * FROM word_statistics WHERE word_id = ?"
        result = self.db.execute_query(sql, (word_id,))
        stats = result[0] if result else None
        
        if stats:
            if stats['total_attempts'] > 0:
                wrong_rate = (stats['wrong_count'] / stats['total_attempts']) * 100
            else:
                wrong_rate = None
            
            word['total_attempts'] = stats['total_attempts']
            word['wrong_rate'] = wrong_rate
            word['last_study_date'] = stats.get('last_study_date')
        else:
            word['total_attempts'] = 0
            word['wrong_rate'] = None
            word['last_study_date'] = None
        
        return word


if __name__ == '__main__':
    # 테스트
    from common.db_connection import get_db_connection
    
    db = get_db_connection()
    db.initialize_database()
    
    model = WordModel()
    
    # 단어 추가
    word_id = model.add_word("test", "테스트", "테스트용")
    print(f"✓ 단어 추가: ID {word_id}")
    
    # 조회
    word = model.get_word(word_id)
    print(f"✓ 단어 조회: {word['english']} = {word['korean']}")
    
    # 전체 조회
    words = model.get_all_words()
    print(f"✓ 전체 단어: {len(words)}개")
    
    # 삭제
    model.delete_word(word_id)
    print(f"✓ 단어 삭제 완료")