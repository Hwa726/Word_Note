# 2025-10-27 - 스마트 단어장 - 학습 설정 뷰 (수정본)
# 파일 위치: views/learning_settings_tab.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QLabel, QSpinBox, QComboBox, QPushButton, 
    QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from common.logger import get_logger
from common.settings import get_settings_manager
from controllers.learning_controller import LearningController

_logger = get_logger('learning_settings_tab')


class LearningSettingsTab(QWidget):
    """
    학습 목표와 모드를 설정하는 뷰.
    설정이 완료되면 start_learning_signal을 통해 MainWindow에 학습 시작을 알립니다.
    """
    
    # MainWindow에서 뷰 전환을 트리거하는 시그널 (모드만 전달)
    start_learning_signal = pyqtSignal(str) 

    def __init__(self, controller: LearningController):
        super().__init__()
        self.controller = controller
        self.settings = get_settings_manager()
        
        self.total_words_count = 0
        
        self._setup_ui()
        self._load_initial_data()
        _logger.debug("LearningSettingsTab 초기화 완료")

    def _setup_ui(self):
        """UI 컴포넌트 구성"""
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        main_layout.setSpacing(20)
        
        # 1. 상태 요약 그룹 (현재 단어 수 등)
        self.status_group = self._create_status_group()
        main_layout.addWidget(self.status_group)
        
        # 2. 학습 설정 그룹 (목표, 모드)
        self.settings_group = self._create_settings_group()
        main_layout.addWidget(self.settings_group)
        
        # 3. 학습 시작 버튼
        self.start_button = QPushButton("🚀 학습 시작 (Ctrl+S)")
        self.start_button.setMinimumSize(250, 50)
        self.start_button.clicked.connect(self._start_learning_clicked)
        main_layout.addWidget(self.start_button)
        
        main_layout.addStretch()

    def _create_status_group(self) -> QGroupBox:
        """현재 단어장 상태를 표시하는 그룹 위젯"""
        group = QGroupBox("현재 단어장 상태")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        self.total_words_label = QLabel("총 등록 단어: 로딩 중...")
        self.review_words_label = QLabel("오늘 복습할 단어: 로딩 중...")
        
        layout.addWidget(self.total_words_label)
        layout.addWidget(self.review_words_label)
        
        return group
        
    def _create_settings_group(self) -> QGroupBox:
        """학습 목표와 모드를 설정하는 그룹 위젯"""
        group = QGroupBox("학습 목표 설정")
        layout = QVBoxLayout(group)
        
        # 1. 학습 목표 (단어 수)
        goal_layout = QHBoxLayout()
        goal_layout.addWidget(QLabel("오늘의 학습 목표 단어 수:"))
        
        self.goal_spinbox = QSpinBox()
        self.goal_spinbox.setRange(1, 500)
        # ✅ 수정: get_setting 호출 시 타입 힌트 제거 (default만 사용)
        self.goal_spinbox.setValue(self.settings.get_setting('daily_word_goal', 50))
        self.goal_spinbox.setSuffix("개")
        # ✅ 추가: 값이 변경될 때마다 DB에 저장
        self.goal_spinbox.valueChanged.connect(self._on_goal_changed)
        goal_layout.addWidget(self.goal_spinbox)
        goal_layout.addStretch()
        layout.addLayout(goal_layout)
        
        # 2. 학습 모드
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("학습 모드 선택:"))
        
        self.mode_combobox = QComboBox()
        self.mode_combobox.addItem("영어 -> 한국어 (EN_TO_KR)", 'EN_TO_KR')
        self.mode_combobox.addItem("한국어 -> 영어 (KR_TO_EN)", 'KR_TO_EN')
        self.mode_combobox.addItem("양방향 혼합 (MIXED)", 'MIXED')
        
        # 저장된 모드 로드
        current_mode = self.settings.get_setting('learning_mode', 'EN_TO_KR')
        index = self.mode_combobox.findData(current_mode)
        if index != -1:
            self.mode_combobox.setCurrentIndex(index)
            
        mode_layout.addWidget(self.mode_combobox)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        return group

    def _on_goal_changed(self, value: int):
        """목표 단어 수가 변경될 때 DB에 저장"""
        self.settings.set_setting('daily_word_goal', value)
        _logger.debug(f"목표 단어 수 변경: {value}개")

    def _load_initial_data(self):
        """초기 단어 수와 복습 단어 수를 로드하여 UI에 표시합니다."""
        try:
            # TODO: WordModel을 통해 실제 단어 수 가져오기
            # from models.word_model import WordModel
            # word_model = WordModel()
            # self.total_words_count = word_model.get_word_count()
            
            # 임시로 0으로 설정
            self.total_words_count = 0
            self.review_words_count = 0
            
            self.total_words_label.setText(f"총 등록 단어: {self.total_words_count}개")
            self.review_words_label.setText(f"오늘 복습할 단어: {self.review_words_count}개")

        except Exception as e:
            _logger.error(f"초기 데이터 로드 실패: {e}")
            self.total_words_label.setText("총 등록 단어: 로드 실패")

    def _start_learning_clicked(self):
        """학습 시작 버튼 클릭 시 처리"""
        selected_goal = self.goal_spinbox.value()
        selected_mode = self.mode_combobox.currentData()
        
        if self.total_words_count == 0:
            QMessageBox.warning(
                self, 
                "경고", 
                "단어장에 등록된 단어가 없습니다.\n단어 관리 탭에서 단어를 추가해주세요."
            )
            return

        # ✅ 수정: Controller에 mode만 전달, 반환값은 bool
        try:
            # 목표 단어 수를 DB에 저장 (Controller가 읽어감)
            self.settings.set_setting('daily_word_goal', selected_goal)
            self.settings.set_setting('learning_mode', selected_mode)
            
            # Controller에 세션 시작 요청 (mode만 전달)
            success = self.controller.start_learning_session(mode=selected_mode)
            
            if not success:
                QMessageBox.information(
                    self, 
                    "정보", 
                    "학습할 단어를 찾지 못했습니다.\n설정된 목표를 줄이거나 단어 목록을 확인하세요."
                )
                return
            
            _logger.info(f"학습 세션 시작 성공: 목표={selected_goal}, 모드={selected_mode}")
            
            # ✅ 수정: MainWindow에 모드만 전달
            self.start_learning_signal.emit(selected_mode)

        except Exception as e:
            _logger.critical(f"학습 세션 시작 중 치명적인 오류 발생: {e}", exc_info=True)
            QMessageBox.critical(
                self, 
                "오류", 
                f"학습 시작 중 오류가 발생했습니다.\n로그를 확인해주세요:\n{e}"
            )
