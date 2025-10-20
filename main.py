# 2025-10-21 - 스마트 단어장 - 메인 진입점
# 파일 위치: main.py

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
import config 

# ==============================================================================
# 인프라 및 핵심 컴포넌트 임포트
# ==============================================================================
# common/db_connection에서 get_db_connection을 가져옴
from common.db_connection import get_db_connection 
# common/logger에서 필요한 함수를 가져옴
from common.logger import get_logger, configure_logging 
# common/settings에서 get_settings_manager를 가져옴
from common.settings import get_settings_manager 

# Controller 임포트 (MainApp 실행에 필요)
# 프로젝트 아키텍처에 따라 경로가 controllers/word_controller.py일 수 있습니다.
# 현재 단계에서는 main.py와 동일한 레벨이거나, 별도의 컨트롤러 폴더가 없다고 가정합니다.
from controllers.word_controller import WordController 
from controllers.learning_controller import LearningController 

# View 임포트
from views.main_window import MainWindow

# ==============================================================================
# 로깅 및 환경 설정
# ==============================================================================
# 로깅 설정 (앱 실행 전)
configure_logging()
_logger = get_logger('main')

# ==============================================================================
# 1. 초기화 함수: 환경 설정 (디렉토리 생성)
# ==============================================================================

def setup_environment() -> bool:
    """
    애플리케이션 실행에 필요한 환경 (디렉토리)을 설정합니다.
    """
    try:
        # config.py에 정의된 디렉토리 생성 함수 호출
        config.ensure_directories() 
        _logger.info("환경 설정 완료: 필수 디렉토리 확인")
        return True
    except Exception as e:
        _logger.critical(f"FATAL ERROR: 환경 설정 실패 - {e}", exc_info=True)
        return False

# ==============================================================================
# 2. 초기화 함수: 데이터베이스 설정 및 스키마 초기화
# ==============================================================================

def setup_database():
    """
    데이터베이스 연결을 설정하고 필요한 경우 스키마를 초기화하고 설정을 로드합니다.
    """
    _logger.info("데이터베이스 설정 시작...")
    
    # 1. 데이터베이스 연결 및 스키마 초기화
    db = get_db_connection() 
    try:
        # db_connection.py에 initialize_database 메소드가 추가되어 있어야 합니다.
        db.initialize_database(config.SCHEMA_PATH) 
        _logger.info(f"데이터베이스 스키마 초기화 성공: {config.DB_PATH}")
    except Exception as e:
        # 스키마 초기화 실패는 치명적이므로 프로그램 종료
        _logger.critical(f"데이터베이스 스키마 초기화 실패: {e}", exc_info=True)
        return False
    
    # 2. SettingsManager에서 설정 로드
    settings = get_settings_manager()
    try:
        # common/settings.py에 load_settings_from_db 메소드가 정의되어 있어야 합니다.
        settings.load_settings_from_db() 
        _logger.info("애플리케이션 설정 로드 완료.")
    except Exception as e:
        _logger.warning(f"데이터베이스 설정 로드 중 오류 발생. 기본 설정값 사용: {e}")
        # 설정 로드 실패는 치명적이지 않으므로 앱은 계속 진행합니다.
    
    return True


# ==============================================================================
# 3. 메인 실행 함수
# ==============================================================================

def main():
    """
    애플리케이션을 실행하는 메인 함수입니다.
    """
    
    # 0. 환경 설정 (디렉토리 생성)
    if not setup_environment():
        sys.exit(1)
    
    _logger.info("=======================================")
    _logger.info(f"🚀 스마트 단어장 애플리케이션 시작 (v{config.APP_VERSION})")
    _logger.info("=======================================")

    # 1. PyQt 애플리케이션 객체 생성
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    
    # 2. 데이터베이스 설정 및 초기화 검증
    if not setup_database():
        # DB 초기화 실패 시 사용자에게 알리고 앱 종료
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Critical)
        error_msg.setText("❌ 데이터베이스 초기화에 실패했습니다.")
        error_msg.setInformativeText("프로그램을 종료합니다. 로그 파일(logs/app_YYYYMMDD.log)을 확인해주세요.")
        error_msg.setWindowTitle("심각한 오류")
        error_msg.exec_()
        sys.exit(1)

    # 3. 컨트롤러 인스턴스 생성 및 메인 윈도우 주입
    try:
        word_controller = WordController()
        learning_controller = LearningController()
        
        # MainWindow.__init__에 모든 컨트롤러를 전달한다고 가정
        main_window = MainWindow(
            word_controller=word_controller, 
            learning_controller=learning_controller
        )
        
        # 4. 윈도우 표시 및 앱 실행
        main_window.show()
        _logger.info("메인 윈도우 표시 완료. 이벤트 루프 진입.")
        sys.exit(app.exec_())

    except Exception as e:
        # 앱 실행 중 발생하는 모든 예외를 최종적으로 여기서 처리
        _logger.critical(f"FATAL ERROR: 애플리케이션 실행 중 치명적인 오류 발생: {e}", exc_info=True)
        
        # 사용자에게 오류를 알림
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Critical)
        error_msg.setText("❌ 애플리케이션 실행 중 치명적인 오류가 발생했습니다.")
        error_msg.setInformativeText("프로그램을 종료합니다. 로그 파일을 확인해주세요.")
        error_msg.setWindowTitle("치명적인 오류")
        error_msg.exec_()
        sys.exit(1)

# ==============================================================================
# 메인 진입점
# ==============================================================================

if __name__ == '__main__':
    main()