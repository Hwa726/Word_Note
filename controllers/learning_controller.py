# 2025-10-27 - 스마트 단어장 - 학습 컨트롤러 (수정본)
# 파일 위치: controllers/learning_controller.py

import random
from typing import List, Dict, Any, Optional
from common.logger import get_logger 
from models.learning_model import LearningModel 
from common.settings import get_settings_manager

_logger = get_logger('learning_controller')

class LearningController:
    """
    학습 세션의 흐름을 관리하고, View(UI)와 Model(SM-2 로직)을 연결하는 컨트롤러.
    
    책임:
    1. 학습 설정(목표, 모드) 적용 및 단어 목록 초기화.
    2. 학습 세션 상태(진행률, 현재 단어) 관리.
    3. 학습 결과(Quality)를 Model에 전달하여 DB 업데이트 트리거.
    4. View에 필요한 현재 단어 정보 및 진행 상황 제공.
    """

    def __init__(self):
        # Model 인스턴스화
        self.model = LearningModel() 
        self.settings = get_settings_manager()
        self.current_session_words: List[Dict[str, Any]] = []
        self.current_word_index: int = -1
        self.session_length: int = 0
        self.session_started: bool = False
        self.learning_mode: str = 'EN_TO_KR'

    def start_learning_session(self, mode: str = 'EN_TO_KR') -> bool:
        """
        학습 세션을 초기화하고, Model에서 학습할 단어 목록을 가져옵니다.
        
        Args:
            mode: 학습 모드 ('EN_TO_KR' 또는 'KR_TO_EN')
            
        Returns:
            bool: 세션 시작 성공 여부
        """
        if self.session_started:
            _logger.warning("진행 중인 학습 세션이 있습니다. 먼저 종료해야 합니다.")
            return False

        self.learning_mode = mode
        
        # ✅ 수정: settings에서 목표 단어 수를 가져와 Model에 전달
        goal = self.settings.get_setting('daily_word_goal', 50)
        words = self.model.get_learning_words(limit=goal, learning_mode=mode)
        
        if not words:
            _logger.info("학습할 단어가 없습니다. 단어장을 추가하거나 복습일을 기다리세요.")
            self.session_started = False
            return False
            
        # 세션 상태 초기화
        self.current_session_words = words
        self.session_length = len(words)
        self.current_word_index = 0
        self.session_started = True

        _logger.info(f"학습 세션 시작: 목표 {goal}개, 실제 {self.session_length}개 단어, 모드: {mode}")
        return True

    def get_current_word(self) -> Optional[Dict[str, Any]]:
        """현재 학습해야 할 단어 정보를 반환합니다."""
        if not self.session_started or not (0 <= self.current_word_index < self.session_length):
            return None
        return self.current_session_words[self.current_word_index]

    def get_next_word_prompt(self) -> Optional[str]:
        """
        현재 단어에 대한 사용자에게 보여줄 질문(Prompt)을 모드에 따라 반환합니다.
        """
        current_word = self.get_current_word()
        if not current_word:
            return None

        if self.learning_mode == 'EN_TO_KR':
            return current_word['english']
        elif self.learning_mode == 'KR_TO_EN':
            return current_word['korean']
        else:
            return current_word.get('english', '단어 로드 오류') 

    def get_current_word_answer(self) -> Optional[str]:
        """
        현재 단어의 정답을 모드에 따라 반환합니다.
        """
        current_word = self.get_current_word()
        if not current_word:
            return None
            
        if self.learning_mode == 'EN_TO_KR':
            return current_word['korean']
        elif self.learning_mode == 'KR_TO_EN':
            return current_word['english']
        else:
            return current_word.get('korean', '정답 로드 오류') 

    def process_review_result(self, quality: int) -> bool:
        """
        사용자의 학습 결과(Quality: 0~5)를 받아 Model을 업데이트하고 다음 단어로 이동합니다.
        """
        current_word = self.get_current_word()
        if not current_word:
            _logger.error("현재 단어가 없습니다. 학습 세션을 확인하세요.")
            return False
        
        word_id = current_word['word_id']
        
        # Model에 결과 반영 (SM-2 알고리즘 실행 및 DB 업데이트)
        success = self.model.update_word_after_learning(word_id, quality)

        # 다음 단어로 인덱스 이동
        self.current_word_index += 1
        
        if self.is_session_finished():
            self.end_learning_session()
            _logger.info("학습 세션 완료.")

        return success

    def is_session_finished(self) -> bool:
        """현재 학습 세션이 완료되었는지 확인합니다."""
        return self.session_started and (self.current_word_index >= self.session_length)

    def end_learning_session(self):
        """학습 세션을 종료하고 상태를 초기화합니다."""
        self.session_started = False
        self.current_session_words = []
        self.current_word_index = -1
        self.session_length = 0
        _logger.info("학습 세션 상태 초기화 완료.")

    def get_progress_info(self) -> Dict[str, int]:
        """현재 진행 상황을 반환합니다."""
        return {
            'current': max(0, self.current_word_index), 
            'total': self.session_length
        }
