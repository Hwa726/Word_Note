# 2025-10-21 - 스마트 단어장 - 플래시카드 학습 화면 (View)
# 파일 위치: views/flashcard_view.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QStackedWidget, QFrame, QSizePolicy, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QGraphicsOpacityEffect # 애니메이션을 위한 임포트 추가

# 새로운 아키텍처 경로에 따라 Controller 임포트
from controllers.learning_controller import LearningController
# 1. Logger 클래스 대신 get_logger 함수 임포트
from common.logger import get_logger 
# common/settings.py에 정의된 설정을 활용한다고 가정
from common.settings import get_settings_manager 

# 1. _logger 초기화 방식 변경
_logger = get_logger('flashcard_view')

class FlashcardView(QWidget):
    """
    플래시카드 학습을 위한 핵심 UI 화면.
    카드를 앞/뒷면으로 플립하고, SM-2 평가 버튼(Quality 0~5)을 통해 
    학습 결과를 LearningController에 전달합니다.
    """
    
    # 학습이 완료되었을 때 메인 윈도우에 알리는 신호 (예: 통계 탭으로 전환 요청)
    learning_finished_signal = pyqtSignal()
    
    # LearningSettingsTab으로 돌아가기 위한 신호
    return_to_settings_signal = pyqtSignal()
    
    def __init__(self, controller: LearningController):
        super().__init__()
        self.controller = controller
        self.settings = get_settings_manager() # 사용자 설정 접근 (예: 테마)
        self.is_flipped = False
        self.current_word_data = None
        self.animation_running = False
        
        self.init_ui()

    # ======================================================================
    # UI 초기화
    # ======================================================================

    def init_ui(self):
        # 기본 폰트 설정
        font_style = QFont("Nanum Gothic", 18)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        
        # 1. 상단 진행 표시줄
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # 2. 플래시카드 위젯 (중앙)
        self.card_stacked_widget = QStackedWidget()
        self.card_stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.card_stacked_widget.setMinimumSize(400, 300)
        
        self.card_front = self._create_card_face("질문", "카드 앞면")
        self.card_back = self._create_card_face("정답", "카드 뒷면")
        
        self.card_stacked_widget.addWidget(self.card_front)
        self.card_stacked_widget.addWidget(self.card_back)
        
        # 2. main_layout.addWidget 완성
        main_layout.addWidget(self.card_stacked_widget)
        
        # 3. 플립 버튼 (질문 -> 정답 보기)
        self.flip_button = QPushButton("정답 보기 (Space)")
        self.flip_button.setFont(QFont("Nanum Gothic", 12, QFont.Bold))
        self.flip_button.setFixedHeight(40)
        self.flip_button.clicked.connect(self.flip_card_action)
        self.flip_button.setEnabled(False) # 초기에는 비활성화
        main_layout.addWidget(self.flip_button)
        
        # 4. 평가 버튼 그룹 (정답 확인 후 활성화)
        self.evaluation_group = self._create_evaluation_group()
        self.evaluation_group.setHidden(True) # 초기에는 숨김
        main_layout.addWidget(self.evaluation_group)
        
        # 5. 하단 버튼 (설정으로 돌아가기 등)
        bottom_layout = QHBoxLayout()
        self.return_button = QPushButton("학습 설정으로 돌아가기")
        self.return_button.clicked.connect(lambda: self.return_to_settings_signal.emit())
        bottom_layout.addWidget(self.return_button)
        main_layout.addLayout(bottom_layout)

    def _create_card_face(self, title: str, default_text: str) -> QFrame:
        """카드 앞면/뒷면 공통 프레임을 생성합니다."""
        frame = QFrame()
        # 스타일 시트 적용 (배경색, 테두리 등)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 제목 라벨
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Nanum Gothic", 10, QFont.Bold))
        title_label.setStyleSheet("color: #777;")
        layout.addWidget(title_label)
        
        # 내용 라벨
        content_label = QLabel(default_text)
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setFont(QFont("Nanum Gothic", 30, QFont.Bold))
        content_label.setWordWrap(True)
        content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(content_label)
        
        # 메모/통계 라벨 (뒷면에 주로 사용)
        memo_label = QLabel("")
        memo_label.setAlignment(Qt.AlignCenter)
        memo_label.setFont(QFont("Nanum Gothic", 12))
        memo_label.setStyleSheet("color: #333;")
        layout.addWidget(memo_label)
        
        # 각 카드에 고유한 속성 추가
        setattr(frame, 'content_label', content_label)
        setattr(frame, 'memo_label', memo_label)
        
        return frame

    def _create_evaluation_group(self) -> QFrame:
        """SM-2 평가 버튼 그룹을 생성합니다."""
        group = QFrame()
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Quality: 0~5 버튼 생성
        buttons_data = [
            (0, "0. 전혀 모름"), 
            (2, "2. 오답/재학습"),
            (4, "4. 애매/보통"), 
            (5, "5. 완벽 정답") # Quality 1, 3은 생략하고 주요 피드백만 제공
        ]
        
        for quality, text in buttons_data:
            btn = QPushButton(text)
            btn.setProperty('quality', quality) # 사용자 속성 저장
            btn.setFont(QFont("Nanum Gothic", 10))
            btn.clicked.connect(lambda checked, q=quality: self.submit_evaluation(q))
            
            # 스타일 설정
            if quality <= 2:
                btn.setStyleSheet("background-color: #FF3B30; color: white;") # 빨강
            elif quality <= 4:
                btn.setStyleSheet("background-color: #FF9500; color: white;") # 주황
            else:
                btn.setStyleSheet("background-color: #4CD964; color: white;") # 녹색
                
            layout.addWidget(btn)
            
        return group
    
    # ======================================================================
    # 애니메이션 및 카드 동작
    # ======================================================================

    def flip_card_action(self):
        """정답 보기 버튼 클릭 시 호출됩니다."""
        if self.animation_running:
            return
            
        if not self.is_flipped:
            # 3. 플립 애니메이션 시작
            self.flip_card_animation()
            self.is_flipped = True
            
            # 버튼 상태 변경
            self.flip_button.setHidden(True)
            QTimer.singleShot(500, lambda: self.evaluation_group.setHidden(False)) # 애니메이션 후 평가 버튼 표시
        else:
            # 이미 플립된 상태에서 다시 누를 수 없도록 버튼 비활성화
            pass

    def flip_card_animation(self):
        """카드 플립 애니메이션 (3D 회전 시뮬레이션)"""
        self.animation_running = True
        
        # 현재 활성화된 카드(앞면 또는 뒷면)를 가져옴
        current_widget = self.card_stacked_widget.currentWidget()
        
        # Opacity Effect를 사용하여 Fade Out/In 효과
        opacity_effect = QGraphicsOpacityEffect(current_widget)
        current_widget.setGraphicsEffect(opacity_effect)
        
        # 4. 애니메이션 로직
        anim = QPropertyAnimation(opacity_effect, b"opacity")
        anim.setDuration(250)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Fade Out 완료 후 카드 전환 및 Fade In 시작
        def on_fade_out_finished():
            # 카드 전환
            next_index = 1 if self.card_stacked_widget.currentIndex() == 0 else 0
            self.card_stacked_widget.setCurrentIndex(next_index)
            
            # Fade In 애니메이션
            next_widget = self.card_stacked_widget.currentWidget()
            opacity_effect_in = QGraphicsOpacityEffect(next_widget)
            next_widget.setGraphicsEffect(opacity_effect_in)
            
            anim_in = QPropertyAnimation(opacity_effect_in, b"opacity")
            anim_in.setDuration(250)
            anim_in.setStartValue(0.0)
            anim_in.setEndValue(1.0)
            anim_in.setEasingCurve(QEasingCurve.InCubic)
            anim_in.start()
            
            anim_in.finished.connect(lambda: self._on_animation_complete(current_widget, next_widget))

        anim.finished.connect(on_fade_out_finished)
        anim.start()

    def _on_animation_complete(self, old_widget, new_widget):
        """애니메이션 완료 후 정리"""
        self.animation_running = False
        # 이전 위젯의 그래픽 효과 제거
        old_widget.setGraphicsEffect(None)
        # 새 위젯의 그래픽 효과 제거
        new_widget.setGraphicsEffect(None)
        
    # ======================================================================
    # 학습 세션 관리
    # ======================================================================

    def start_learning(self, mode: str):
        """
        LearningSettingsTab에서 호출되어 학습을 시작합니다.
        """
        self.card_stacked_widget.setCurrentIndex(0) # 항상 앞면(질문)부터 시작
        self.is_flipped = False
        self.flip_button.setEnabled(True)
        self.evaluation_group.setHidden(True)
        
        if self.controller.start_learning_session(mode):
            self.load_new_word()
        else:
            QMessageBox.information(self, "정보", "오늘 학습할 단어가 없거나 단어장에 단어가 없습니다.")
            self.return_to_settings_signal.emit() # 설정 화면으로 돌아가기

    def load_new_word(self):
        """
        컨트롤러에서 다음 단어를 가져와 UI에 표시합니다.
        """
        if self.controller.is_session_finished():
            self.show_completion_message()
            return
            
        # 1. 단어 데이터 로드
        self.current_word_data = self.controller.get_current_word()
        
        if self.current_word_data:
            # 2. UI 업데이트
            front_text = self.controller.get_next_word_prompt()
            back_text = self.controller.get_current_word_answer()
            memo = self.current_word_data.get('memo', '')
            
            # 앞면 업데이트
            self.card_front.content_label.setText(front_text)
            self.card_front.memo_label.setText("메모: " + memo if memo else "")
            
            # 뒷면 업데이트 (통계 정보 포함)
            self.card_back.content_label.setText(back_text)
            
            stats_info = f"메모: {memo}\n"
            total = self.current_word_data.get('total_attempts', 0)
            wrong_rate = self.current_word_data.get('wrong_rate')
            
            if total > 0:
                rate_str = f"{wrong_rate:.1f}%" if wrong_rate is not None else "0%"
                stats_info += f"총 학습: {total}회, 오답률: {rate_str}"
            else:
                stats_info += "신규 단어"
                
            self.card_back.memo_label.setText(stats_info)
            
            # 3. 진행 표시줄 업데이트
            self.update_progress()
            
            self.flip_button.setEnabled(True) # 새 단어 로드 후 플립 가능
        else:
            _logger.error("컨트롤러에서 단어를 가져오지 못했습니다.")
            self.show_completion_message()

    def update_progress(self):
        """진행 표시줄 값을 업데이트합니다."""
        progress = self.controller.get_progress_info()
        total = progress['total']
        current = progress['current']
        
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(f"진행: {current} / {total}")
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("진행: 0 / 0")

    def submit_evaluation(self, quality: int):
        """
        SM-2 평가 버튼 클릭 시 호출되며, 결과를 컨트롤러에 제출합니다.
        """
        if not self.current_word_data:
            return
            
        # 1. 컨트롤러에 결과 제출
        success = self.controller.process_review_result(quality)
        
        if success:
            _logger.info(f"단어 {self.current_word_data['word_id']} 평가 제출 완료. Quality: {quality}")
            
            # 2. UI 상태 초기화 및 다음 단어 로드
            self.flip_button.setHidden(False)
            self.flip_button.setEnabled(False)
            self.evaluation_group.setHidden(True)
            self.is_flipped = False
            self.card_stacked_widget.setCurrentIndex(0) # 카드를 앞면으로 다시 전환
            
            # 지연 없이 바로 다음 단어 로드
            self.load_new_word()
        else:
            QMessageBox.critical(self, "오류", "학습 결과 반영 중 오류가 발생했습니다. 로그를 확인하세요.")

    def show_completion_message(self):
        """학습 세션 완료 시 메시지를 표시합니다."""
        self.flip_button.setEnabled(False)
        self.evaluation_group.setHidden(True)
        self.card_front.content_label.setText("🎉 학습 완료! 🎉")
        self.card_front.memo_label.setText("오늘 목표를 달성했습니다. 통계를 확인하세요.")
        self.card_back.content_label.setText("오늘 학습 통계 탭으로 이동합니다.")
        self.card_back.memo_label.setText("")
        
        QMessageBox.information(self, "완료", "오늘의 학습 목표를 모두 달성했습니다!")
        self.learning_finished_signal.emit() # 메인 윈도우에 완료 신호 전송

    def keyPressEvent(self, event):
        """키보드 단축키 처리"""
        # 학습 중일 때만 단축키 처리
        if not self.controller.session_started or self.controller.is_session_finished():
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key_Space:
            # 스페이스바: 정답 보기 (플립)
            self.flip_card_action()
            event.accept()
        elif self.is_flipped:
            # 플립된 상태에서만 숫자 키 입력 처리
            if event.key() == Qt.Key_5 or event.key() == Qt.Key_E:
                self.submit_evaluation(5)
            elif event.key() == Qt.Key_4 or event.key() == Qt.Key_W:
                self.submit_evaluation(4)
            elif event.key() == Qt.Key_2 or event.key() == Qt.Key_S:
                self.submit_evaluation(2)
            elif event.key() == Qt.Key_0 or event.key() == Qt.Key_Q:
                self.submit_evaluation(0)
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)


# ======================================================================
# 테스트 코드는 생략합니다.
# ======================================================================