# 2025-11-03 - 스마트 단어장 - 학습 완료 요약 다이얼로그
# 파일 위치: views/learning_result_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class LearningResultDialog(QDialog):
    """
    학습 완료 요약 다이얼로그

    학습 세션 종료 후 결과를 표시하고 다음 액션을 선택할 수 있게 함
    """

    # 시그널 정의
    review_weak_words_requested = pyqtSignal(list)  # 취약 단어 복습 요청
    view_statistics_requested = pyqtSignal()        # 통계 보기 요청

    def __init__(self, parent, session_result: dict):
        """
        초기화

        Args:
            parent: 부모 위젯
            session_result: {
                'total': 50,              # 총 학습 단어 수
                'correct': 42,            # 정답 수
                'wrong': 8,               # 오답 수
                'time_taken': 923,        # 학습 시간 (초)
                'avg_response_time': 3.2, # 평균 응답 시간 (초)
                'wrong_words': [          # 오답 처리된 단어 리스트
                    {'word_id': 1, 'english': 'computer', 'korean': '컴퓨터'},
                    {'word_id': 2, 'english': 'difficult', 'korean': '어려운'},
                    ...
                ]
            }
        """
        super().__init__(parent)
        self.session_result = session_result
        self.setup_ui()

    def setup_ui(self):
        """UI 구성"""
        self.setWindowTitle("학습 완료")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)

        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 1. 제목 및 축하 메시지
        self._add_title_section(main_layout)

        # 2. 학습 결과 통계
        self._add_statistics_section(main_layout)

        # 3. 취약 단어 리스트
        if self.session_result.get('wrong_words'):
            self._add_weak_words_section(main_layout)

        # 4. 버튼 영역
        self._add_buttons_section(main_layout)

        self.setLayout(main_layout)

    def _add_title_section(self, layout):
        """제목 섹션 추가"""
        title_label = QLabel("축하합니다!")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        subtitle_label = QLabel("학습을 완료하셨습니다")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        layout.addWidget(subtitle_label)

    def _add_statistics_section(self, layout):
        """학습 결과 통계 섹션 추가"""
        # 그룹박스 생성
        stats_group = QGroupBox("학습 결과")
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(10)

        # 결과 데이터 추출
        total = self.session_result.get('total', 0)
        correct = self.session_result.get('correct', 0)
        wrong = self.session_result.get('wrong', 0)
        time_taken = self.session_result.get('time_taken', 0)
        avg_response = self.session_result.get('avg_response_time', 0)

        # 정답률 계산
        accuracy = (correct / total * 100) if total > 0 else 0

        # 시간 포맷팅
        minutes = int(time_taken // 60)
        seconds = int(time_taken % 60)
        time_str = f"{minutes}분 {seconds}초"

        # 통계 정보 표시
        stats_info = [
            f"총 학습 단어: {total}개",
            f"정답: {correct}개 ({accuracy:.1f}%)",
            f"오답: {wrong}개 ({100-accuracy:.1f}%)",
            f"학습 시간: {time_str}",
            f"평균 응답 시간: {avg_response:.1f}초"
        ]

        for info in stats_info:
            label = QLabel(info)
            label.setStyleSheet("padding: 5px; font-size: 14px;")
            stats_layout.addWidget(label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

    def _add_weak_words_section(self, layout):
        """취약 단어 섹션 추가"""
        weak_group = QGroupBox("취약 단어 (오답 처리된 단어)")
        weak_layout = QVBoxLayout()

        # 리스트 위젯 생성
        self.weak_words_list = QListWidget()
        self.weak_words_list.setMaximumHeight(200)

        # 오답 단어 추가
        wrong_words = self.session_result.get('wrong_words', [])
        for word in wrong_words:
            english = word.get('english', '')
            korean = word.get('korean', '')
            item_text = f"• {english} - {korean}"
            item = QListWidgetItem(item_text)
            self.weak_words_list.addItem(item)

        weak_layout.addWidget(self.weak_words_list)
        weak_group.setLayout(weak_layout)
        layout.addWidget(weak_group)

    def _add_buttons_section(self, layout):
        """버튼 섹션 추가"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 취약 단어 복습하기 버튼 (오답이 있을 때만)
        if self.session_result.get('wrong_words'):
            review_button = QPushButton("취약 단어 복습하기")
            review_button.clicked.connect(self.on_review_weak_words)
            review_button.setMinimumHeight(40)
            review_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF9500;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #FF8000;
                }
            """)
            button_layout.addWidget(review_button)

        # 통계 보기 버튼
        stats_button = QPushButton("통계 보기")
        stats_button.clicked.connect(self.on_view_statistics)
        stats_button.setMinimumHeight(40)
        stats_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0066DD;
            }
        """)
        button_layout.addWidget(stats_button)

        # 확인 버튼
        confirm_button = QPushButton("확인")
        confirm_button.clicked.connect(self.accept)
        confirm_button.setMinimumHeight(40)
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2DB54A;
            }
        """)
        button_layout.addWidget(confirm_button)

        layout.addLayout(button_layout)

    def on_review_weak_words(self):
        """취약 단어 복습하기 버튼 클릭"""
        wrong_words = self.session_result.get('wrong_words', [])
        if wrong_words:
            self.review_weak_words_requested.emit(wrong_words)
            self.accept()

    def on_view_statistics(self):
        """통계 보기 버튼 클릭"""
        self.view_statistics_requested.emit()
        self.accept()


# ==============================================================================
# 테스트 코드
# ==============================================================================

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 테스트 데이터
    test_result = {
        'total': 50,
        'correct': 42,
        'wrong': 8,
        'time_taken': 923,  # 15분 23초
        'avg_response_time': 3.2,
        'wrong_words': [
            {'word_id': 1, 'english': 'computer', 'korean': '컴퓨터'},
            {'word_id': 2, 'english': 'difficult', 'korean': '어려운'},
            {'word_id': 3, 'english': 'important', 'korean': '중요한'},
            {'word_id': 4, 'english': 'necessary', 'korean': '필요한'},
            {'word_id': 5, 'english': 'beautiful', 'korean': '아름다운'},
        ]
    }

    # 다이얼로그 표시
    dialog = LearningResultDialog(None, test_result)

    # 시그널 연결 (테스트용)
    def on_review_requested(words):
        print(f"취약 단어 복습 요청: {len(words)}개")
        for word in words:
            print(f"  - {word['english']}: {word['korean']}")

    def on_stats_requested():
        print("통계 보기 요청")

    dialog.review_weak_words_requested.connect(on_review_requested)
    dialog.view_statistics_requested.connect(on_stats_requested)

    dialog.exec_()

    sys.exit(0)
