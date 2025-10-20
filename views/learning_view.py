# 2025-10-21 - 스마트 단어장 - 학습 메인 뷰 (컨테이너)
# 파일 위치: views/learning_view.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QGroupBox, QRadioButton, 
    QSpinBox, QPushButton, QHBoxLayout, QGridLayout, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal

# Phase 3에서 작성된 View 및 Controller 임포트
from controllers.learning_controller import LearningController
from views.flashcard_view import FlashcardView
from common.logger import get_logger
from common.settings import get_settings_manager

_logger = get_logger('learning_view')

# ======================================================================
# 1. 학습 설정 탭 (LearningSettingsTab)
# ======================================================================

class LearningSettingsTab(QWidget):
    """
    학습 모드와 목표 단어 수 등 설정을 보여주고, 
    사용자가 학습을 시작할 수 있도록 하는 화면.
    """
    
    # 학습 시작 신호: 모드('EN_TO_KR'/'KR_TO_EN')를 인자로 전달
    start_learning_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings_manager()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(30)
        
        # 1. 학습 목표 설정 (Setting Manager 값 반영)
        goal_group = QGroupBox("1. 일일 목표 단어 수 설정")
        goal_layout = QHBoxLayout(goal_group)
        
        self.goal_spinbox = QSpinBox()
        self.goal_spinbox.setRange(10, 500)
        
        # config/settings.py에 정의된 값 로드 및 설정
        initial_goal = self.settings.get_setting('daily_word_goal', 50) 
        self.goal_spinbox.setValue(initial_goal)
        
        self.goal_spinbox.valueChanged.connect(self._update_goal_setting)
        
        goal_layout.addWidget(self.goal_spinbox)
        goal_layout.addWidget(QLabel("개"))
        goal_layout.addStretch(1)
        main_layout.addWidget(goal_group)

        # 2. 학습 모드 선택
        mode_group = QGroupBox("2. 학습 모드 선택")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_en_kr = QRadioButton("영어 → 한국어 (영단어 보고 뜻 맞추기)")
        self.mode_kr_en = QRadioButton("한국어 → 영어 (뜻 보고 영단어 철자 맞추기)")
        
        # 기본값 설정
        self.mode_en_kr.setChecked(True)
        
        mode_layout.addWidget(self.mode_en_kr)
        mode_layout.addWidget(self.mode_kr_en)
        main_layout.addWidget(mode_group)
        
        # 3. 학습 시작 버튼
        self.start_button = QPushButton("🚀 학습 시작하기")
        self.start_button.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                padding: 15px;
                background-color: #007AFF; 
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #005BB5;
            }
        """)
        self.start_button.clicked.connect(self._start_session)
        
        main_layout.addStretch(1)
        main_layout.addWidget(self.start_button)

    def _update_goal_setting(self, value: int):
        """SpinBox 값이 변경될 때마다 DB에 목표 단어 수를 저장합니다."""
        self.settings.set_setting('daily_word_goal', value)
        _logger.info(f"일일 목표 단어 수를 {value}개로 업데이트했습니다.")

    def _start_session(self):
        """
        선택된 모드를 확인하고 start_learning_signal을 보냅니다.
        """
        mode = 'EN_TO_KR'
        if self.mode_kr_en.isChecked():
            mode = 'KR_TO_EN'
        
        # 학습 시작 신호 전송
        self.start_learning_signal.emit(mode)


# ======================================================================
# 2. 학습 메인 뷰 (LearningView) - QStackedWidget 기반
# ======================================================================

class LearningView(QWidget):
    """
    학습 설정 탭과 플래시카드 뷰를 전환하는 컨테이너 위젯.
    메인 윈도우의 '학습' 탭에 삽입됩니다.
    """
    
    # 메인 윈도우의 탭 전환을 요청하는 신호
    switch_to_tab_signal = pyqtSignal(str) 

    def __init__(self, controller: LearningController):
        super().__init__()
        self.controller = controller
        
        # QStackedWidget을 사용하여 화면 전환 구현
        self.stacked_widget = QStackedWidget()
        
        # 1. 학습 설정 화면
        self.settings_tab = LearningSettingsTab()
        self.settings_tab.start_learning_signal.connect(self.start_flashcard_view)
        
        # 2. 플래시카드 학습 화면
        self.flashcard_view = FlashcardView(self.controller)
        # 플래시카드 완료/종료 신호 연결
        self.flashcard_view.learning_finished_signal.connect(lambda: self.switch_to_tab_signal.emit('Dashboard')) # 완료 시 대시보드 탭으로 전환 요청
        self.flashcard_view.return_to_settings_signal.connect(self.return_to_settings)
        
        # Stacked Widget에 뷰 추가
        self.stacked_widget.addWidget(self.settings_tab)  # Index 0
        self.stacked_widget.addWidget(self.flashcard_view) # Index 1
        
        # 레이아웃 설정
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.stacked_widget)

        # 초기 화면 설정
        self.stacked_widget.setCurrentIndex(0)

    def start_flashcard_view(self, mode: str):
        """
        학습 설정 화면에서 시작 버튼을 누르면 호출됩니다.
        플래시카드 뷰를 활성화하고 학습을 시작합니다.
        """
        _logger.info(f"학습 시작 요청: 모드={mode}")
        self.flashcard_view.start_learning(mode)
        self.stacked_widget.setCurrentIndex(1) # 플래시카드 뷰로 전환
        self.flashcard_view.setFocus() # 단축키 사용을 위해 포커스 설정

    def return_to_settings(self):
        """
        플래시카드 뷰에서 설정 화면으로 돌아갈 때 호출됩니다.
        """
        self.controller.end_learning_session()
        self.stacked_widget.setCurrentIndex(0) # 설정 화면으로 전환
        _logger.info("학습 설정 화면으로 돌아감.")

    def enter_tab(self):
        """메인 윈도우에서 이 탭을 선택할 때 호출될 수 있는 메소드"""
        # 학습 완료 후 다시 탭으로 돌아올 때 설정 화면으로 보여주기
        if not self.controller.session_started:
            self.stacked_widget.setCurrentIndex(0)