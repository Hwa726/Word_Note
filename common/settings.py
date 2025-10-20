# 파일 위치: common/settings.py

from typing import Dict, Any, Optional
import json
import config
from common.db_connection import get_db_connection
from common.logger import get_logger

logger = get_logger('common.settings')

# ----------------------------------------------------------------------
# 1. 기본 설정값 정의 (DB에 저장되지 않는 설정값 포함)
# ----------------------------------------------------------------------
DEFAULT_SETTINGS: Dict[str, Any] = {
    'daily_word_goal': 50,
    'daily_time_goal': 30, # 분
    'theme': 'light',
    'font_size': 'medium',
    'flashcard_time_limit': 10, # 초
    'exam_time_limit': 600, # 초
    'language': 'ko',
    'LOG_LEVEL': config.LOG_LEVEL # config.py에서 로깅 레벨을 가져와 설정 객체에 포함
}

# ----------------------------------------------------------------------
# 2. SettingsManager 클래스 (싱글톤)
# ----------------------------------------------------------------------
class SettingsManager:
    """
    애플리케이션 설정을 관리하는 싱글톤 클래스.
    """
    
    _instance = None
    _settings: Dict[str, Any] = DEFAULT_SETTINGS.copy() # 기본 설정으로 초기화
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.db = get_db_connection()
            logger.debug("SettingsManager 인스턴스 생성")
        return cls._instance

    # 💡 누락된 메소드: 데이터베이스에서 설정을 메모리로 로드
    def load_settings_from_db(self) -> None:
        """
        데이터베이스(user_settings 테이블)에서 설정을 로드하여 현재 설정값에 반영합니다.
        """
        # DB 연결 확인 (초기화 단계에서 호출되므로 연결이 되어 있어야 함)
        if not self.db.is_connected:
            logger.warning("DB 연결 끊김. 설정 로드 불가. 기본 설정값 사용.")
            return

        try:
            # user_settings 테이블에서 모든 키/값 쌍을 가져옴
            db_settings_list = self.db.execute_query("SELECT setting_key, setting_value FROM user_settings")
            
            # DB 데이터를 딕셔너리로 변환
            db_settings = {
                item['setting_key']: self._convert_value(item['setting_key'], item['setting_value']) 
                for item in db_settings_list
            }

            # 기본 설정에 DB 설정을 덮어씌움 (DB 값이 우선순위 높음)
            self._settings.update(db_settings)

            logger.info("DB에서 설정 로드 성공 및 적용 완료.")
            
        except Exception as e:
            # 이 오류는 무시해도 괜찮은 Warning 레벨입니다.
            logger.warning(f"DB에서 설정 로드 실패. 기본 설정값 사용. 오류: {e}")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """특정 설정값을 조회합니다."""
        return self._settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> bool:
        """특정 설정값을 메모리와 DB에 저장합니다."""
        # 구현은 생략하고 로직만 포함 (DB에 저장하는 부분)
        str_value = str(value) 
        try:
            self.db.execute_non_query(
                "INSERT OR REPLACE INTO user_settings (setting_key, setting_value, updated_at) VALUES (?, ?, datetime('now'))",
                (key, str_value)
            )
            self._settings[key] = value
            return True
        except Exception as e:
            logger.error(f"설정 저장 실패: {key}, 오류: {e}")
            return False

    def _convert_value(self, key: str, value: str) -> Any:
        """DB에서 로드한 문자열 값을 적절한 파이썬 타입으로 변환"""
        int_keys = ['daily_word_goal', 'daily_time_goal', 'flashcard_time_limit', 'exam_time_limit']
        if key in int_keys:
            try:
                return int(value)
            except ValueError:
                return DEFAULT_SETTINGS.get(key, value)
        return value

# ----------------------------------------------------------------------
# 3. 전역 접근 함수
# ----------------------------------------------------------------------
_settings_manager_instance: Optional[SettingsManager] = None

def get_settings_manager() -> SettingsManager:
    """SettingsManager 싱글톤 인스턴스를 반환합니다."""
    global _settings_manager_instance
    if _settings_manager_instance is None:
        _settings_manager_instance = SettingsManager()
    return _settings_manager_instance