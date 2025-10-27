# 2025-10-20 - 스마트 단어장 - 단어 컨트롤러
# 파일 위치: controllers/word_controller.py

from typing import List, Dict, Any, Optional
import csv
from pathlib import Path
import config # CSV 입출력 시 경로 사용

# 경로 수정 반영 (word_model.py가 models 폴더에 있으므로 명시적 경로 사용)
from models.word_model import WordModel 
from common.logger import get_logger

logger = get_logger(__name__)


class WordController:
    """
    단어 컨트롤러 클래스
    
    단어 CRUD, CSV 입출력, 유효성 검사를 담당한다.
    """
    
    def __init__(self):
        self.model = WordModel()
        logger.debug("WordController 초기화")
    
    def create_word(self, english: str, korean: str, memo: str = "", is_favorite: int = 0) -> Dict[str, Any]:
        """
        새 단어를 추가한다.
        
        Args:
            english: 영어 단어
            korean: 한국어 뜻
            memo: 메모 (선택)
            is_favorite: 즐겨찾기 여부 (0 또는 1)
        
        Returns:
            dict: {'success': bool, 'message': str, 'word_id': int}
        """
        try:
            # 1. 유효성 검사
            validation = self.validate_word_data(english, korean)
            if not validation['valid']:
                return {'success': False, 'message': validation['message'], 'word_id': -1}

            # 2. 모델에 추가
            # 2. 모델에 추가 (is_favorite 전달)
            word_id = self.model.add_word(english, korean, memo, is_favorite)
            logger.info(f"단어 추가 성공: {english} (ID: {word_id}, 즐겨찾기: {is_favorite})")
            return {'success': True, 'message': '단어 추가 완료.', 'word_id': word_id}
        except ValueError as e:
            logger.warning(f"단어 추가 실패 (유효성): {e}")
            return {'success': False, 'message': str(e), 'word_id': -1}
        except Exception as e:
            logger.error(f"단어 추가 실패 (DB 오류): {e}", exc_info=True)
            return {'success': False, 'message': f'데이터베이스 오류: {e}', 'word_id': -1}
            
    # ... (나머지 메소드 생략 - update_word, delete_word, get_word_list 등)
    
    def validate_word_data(self, english: str, korean: str) -> Dict[str, Any]:
        """
        단어 데이터 유효성을 검사한다.
        ... (생략)
        """
        if not english or not english.strip():
            return {'valid': False, 'message': '영어 단어를 입력해주세요.'}
        
        if not korean or not korean.strip():
            return {'valid': False, 'message': '한국어 뜻을 입력해주세요.'}
        
        if len(english) > 100:
            return {'valid': False, 'message': '영어 단어는 100자를 초과할 수 없습니다.'}
        
        if len(korean) > 500:
            return {'valid': False, 'message': '한국어 뜻은 500자를 초과할 수 없습니다.'}
        
        return {'valid': True, 'message': ''}