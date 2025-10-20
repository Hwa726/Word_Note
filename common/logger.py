# 2025-10-21 - 스마트 단어장 - 중앙 집중식 로깅 시스템
# 파일 위치: common/logger.py

import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

# config.py에서 로깅 관련 설정을 가져옴 
import config

class Logger:
    """
    애플리케이션 전반에 걸쳐 사용되는 정적 로깅 클래스입니다.
    - 파일 로깅 (RotatingFileHandler 사용)
    - 콘솔 로깅 (StreamHandler 사용)
    """
    
    _configured = False
    
    @staticmethod
    def configure_logging():
        """
        로거를 설정하고 핸들러를 추가합니다. 프로그램 시작 시 단 한 번만 호출되어야 합니다.
        """
        if Logger._configured:
            return

        # 1. 루트 로거 설정
        root_logger = logging.getLogger()
        # config.LOG_LEVEL (예: 'INFO', 'DEBUG')를 대문자로 변환하여 레벨 설정
        root_logger.setLevel(config.LOG_LEVEL.upper()) 

        # 2. 로깅 포맷 정의
        formatter = logging.Formatter(
            fmt=config.LOG_FORMAT, 
            datefmt=config.LOG_DATE_FORMAT
        )
        
        # 3. 파일 핸들러 (RotatingFileHandler)
        try:
            # 파일 로깅 경로 확인 및 생성
            log_path = Path(config.LOG_FILE)
            
            # RotatingFileHandler: 5MB(1024*1024*5 bytes)마다 최대 5개 파일로 순환
            file_handler = RotatingFileHandler(
                log_path, 
                maxBytes=1024*1024*5, 
                backupCount=5, 
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            # 파일 로깅 실패 시 콘솔에만 기록
            print(f"로그 파일 생성/접근 오류. 콘솔에만 로깅합니다: {e}")

        # 4. 콘솔 핸들러 (StreamHandler)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        Logger._configured = True
        
        # 설정 후 초기 메시지 기록
        root_logger.info("로깅 시스템 초기화 완료.")

    @staticmethod
    def get_logger(name: str):
        """
        지정된 이름의 로거 인스턴스를 반환합니다.
        
        Args:
            name: 로거 이름 (일반적으로 __name__을 사용)
        
        Returns:
            logging.Logger: 로거 객체
        """
        if not Logger._configured:
            Logger.configure_logging()
        return logging.getLogger(name)

# ==============================================================================
# 모듈 레벨 함수 (외부 임포트용) - ImportError 해결을 위해 추가됨
# ==============================================================================

def configure_logging():
    """
    로거 설정을 시작합니다.
    다른 모듈에서 from common.logger import configure_logging 형태로 사용
    """
    Logger.configure_logging()
    
def get_logger(name: str):
    """
    지정된 이름의 로거 인스턴스를 반환합니다.
    다른 모듈에서 from common.logger import get_logger 형태로 사용
    """
    return Logger.get_logger(name)

# ==============================================================================
# 테스트 코드
# ==============================================================================
if __name__ == '__main__':
    # config.py의 ensure_directories가 실행되었다고 가정
    
    # 1. 로거 설정
    configure_logging() # 모듈 레벨 함수 사용
    
    # 2. 다양한 모듈에서 로거 사용 시뮬레이션
    main_logger = get_logger('main') # 모듈 레벨 함수 사용
    db_logger = get_logger('db_connection')
    ui_logger = get_logger('flashcard_view')
    
    print("\n--- 로깅 테스트 시작 ---")
    
    main_logger.info("애플리케이션 시작 준비 완료.")
    db_logger.warning("데이터베이스 연결 지연...")
    ui_logger.error("UI 초기화 중 심각한 오류 발생", exc_info=True)