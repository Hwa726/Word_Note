# 2025-10-27 - 스마트 단어장 - 메인 윈도우 (수정본: 시그널 연결 완료)
# 파일 위치: views/main_window.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, 
    QStackedWidget, QMessageBox, QLabel, QStatusBar
)
from PyQt5.QtCore import Qt, QSize
from common.logger import get_logger
from common.settings import get_settings_manager
import config

# 컨트롤러 및 뷰 임포트
from controllers.word_controller import WordController 
from controllers.learning_controller import LearningController 
from views.flashcard_view import FlashcardView 
from views.learning_settings_tab import LearningSettingsTab
from views.word_manager_view import WordManagerView  # ✅ 추가

# 로거 정의
_logger = get_logger('main_window')

# ==============================================================================
# 임시 Placeholder
# ==============================================================================
class PlaceholderTab(QWidget):
    def __init__(self, name):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel(f"🚧 {name} 탭 (구현 예정 🚧)")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

# ==============================================================================
# 메인 윈도우 클래스
# ==============================================================================
class MainWindow(QMainWindow):
    """
    애플리케이션의 메인 윈도우 쉘. 탭 기반 구조를 관리하고, 
    Learning 탭 내부의 뷰 전환 로직을 담당합니다.
    """
    
    def __init__(self, word_controller: WordController, learning_controller: LearningController):
        super().__init__()
        _logger.debug("MainWindow 초기화 시작")
        
        # 컨트롤러 저장
        self.word_controller = word_controller
        self.learning_controller = learning_controller
        self.settings = get_settings_manager()

        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.resize(1000, 700)
        
        self._setup_ui()
        _logger.info("MainWindow UI 설정 완료")
        
    def _setup_ui(self):
        """메인 UI 구성 요소들을 설정합니다."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        self.tab_widget.setIconSize(QSize(18, 18))
        self.main_layout.addWidget(self.tab_widget)
        
        # 탭 추가
        self._add_tabs()
        
        # 상태 표시줄
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("스마트 단어장 준비 완료", 3000)

    def _add_tabs(self):
        """설계서에 정의된 탭들을 추가합니다."""
        
        # 1. 대시보드 탭
        self.dashboard_tab = PlaceholderTab("대시보드")
        self.tab_widget.addTab(self.dashboard_tab, "📊 대시보드")
        
        # 2. 단어 관리 탭 (WordManagerView 사용)
        self.word_manager_tab = WordManagerView(self)
        self.tab_widget.addTab(self.word_manager_tab, "📚 단어 관리")
        
        # 3. 학습 탭 (Learning Settings + Flashcard View 통합)
        self.learning_tab = self._create_learning_tab()
        self.tab_widget.addTab(self.learning_tab, "🧠 학습 시작")
        
        # 4. 시험 탭
        self.exam_tab = PlaceholderTab("시험")
        self.tab_widget.addTab(self.exam_tab, "📝 시험")
        
        # 5. 통계 탭
        self.statistics_tab = PlaceholderTab("통계")
        self.tab_widget.addTab(self.statistics_tab, "📈 통계")
        
        # 6. 설정 탭
        self.settings_tab = PlaceholderTab("설정")
        self.tab_widget.addTab(self.settings_tab, "⚙️ 설정")

    def _create_learning_tab(self) -> QWidget:
        """학습 탭 내부의 QStackedWidget (설정 <-> 플래시카드 뷰 전환)을 설정합니다."""
        self.learning_stacked_widget = QStackedWidget()
        
        # 1. 학습 설정 뷰 (Index 0)
        self.settings_view = LearningSettingsTab(self.learning_controller)
        
        # 2. 플래시카드 뷰 (Index 1)
        self.flashcard_view = FlashcardView(self.learning_controller)
        
        self.learning_stacked_widget.addWidget(self.settings_view)
        self.learning_stacked_widget.addWidget(self.flashcard_view)
        self.learning_stacked_widget.setCurrentWidget(self.settings_view)

        # ✅ 수정: 시그널 연결 활성화
        self.settings_view.start_learning_signal.connect(self.switch_to_flashcard_view)
        self.flashcard_view.return_to_settings_signal.connect(self.switch_to_settings_view)
        self.flashcard_view.learning_finished_signal.connect(self.on_learning_finished)

        return self.learning_stacked_widget

    # ===================================================================
    # 학습 뷰 전환 로직
    # ===================================================================
    
    def switch_to_flashcard_view(self, mode: str):
        """
        LearningSettingsTab에서 학습 시작 신호가 오면 FlashcardView로 전환합니다.
        
        Args:
            mode: 학습 모드 ('EN_TO_KR', 'KR_TO_EN', 'MIXED')
        """
        _logger.info(f"플래시카드 뷰로 전환: 모드={mode}")
        self.learning_stacked_widget.setCurrentWidget(self.flashcard_view)
        
        # ✅ 수정: 첫 단어 로드 활성화
        self.flashcard_view.load_new_word()
        
        self.statusBar().showMessage(f"학습 세션이 시작되었습니다. (모드: {mode})", 5000)

    def switch_to_settings_view(self):
        """FlashcardView에서 설정 화면으로 돌아갈 때 호출됩니다."""
        _logger.info("학습 설정 화면으로 돌아가기")
        self.learning_stacked_widget.setCurrentWidget(self.settings_view)
        self.statusBar().showMessage("학습 세션이 종료되었습니다. 새로운 목표를 설정하세요.", 5000)

    def on_learning_finished(self):
        """
        FlashcardView에서 학습 완료 신호를 받으면 통계 탭으로 전환합니다.
        """
        _logger.info("학습 완료 - 통계 탭으로 전환")
        # TODO: 통계 탭이 구현되면 해당 탭으로 전환
        # self.tab_widget.setCurrentWidget(self.statistics_tab)
        
        # 임시로 설정 화면으로 돌아가기
        self.switch_to_settings_view()
        self.statusBar().showMessage("🎉 학습 완료! 수고하셨습니다.", 10000)
