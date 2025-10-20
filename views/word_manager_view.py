# 2025-10-20 - 스마트 단어장 - 단어 관리 뷰
# 파일 위치: word_manager_view.py

"""
단어 관리 뷰

단어 목록, 검색, 추가/수정/삭제 UI를 제공한다.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QLineEdit, 
                              QLabel, QMessageBox, QHeaderView, QFileDialog,
                              QComboBox, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

import config
from common.logger import get_logger
from word_controller import WordController
from add_edit_word_dialog import AddEditWordDialog

logger = get_logger(__name__)


class WordManagerView(QWidget):
    """
    단어 관리 뷰 클래스
    
    단어 목록 조회, 추가, 수정, 삭제, 검색 기능을 제공한다.
    """
    
    # 시그널 정의
    word_count_changed = pyqtSignal(int)  # 단어 개수 변경 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.controller = WordController()
        self.current_words = []
        
        self.setup_ui()
        self.refresh_word_list()
        
        logger.info("WordManagerView 초기화 완료")
    
    def setup_ui(self):
        """UI 설정"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(config.SPACING['section'])
        
        # 상단 툴바
        toolbar = self.create_toolbar()
        main_layout.addLayout(toolbar)
        
        # 단어 목록 테이블
        self.word_table = self.create_word_table()
        main_layout.addWidget(self.word_table)
        
        # 하단 정보바
        info_bar = self.create_info_bar()
        main_layout.addLayout(info_bar)
        
        self.setLayout(main_layout)
    
    def create_toolbar(self):
        """상단 툴바 생성"""
        toolbar = QHBoxLayout()
        
        # 단어 추가 버튼
        add_btn = QPushButton("➕ 단어 추가")
        add_btn.setFixedSize(*config.BUTTON_SIZES['medium'])
        add_btn.clicked.connect(self.on_add_word)
        toolbar.addWidget(add_btn)
        
        # CSV 가져오기 버튼
        import_btn = QPushButton("📥 CSV 가져오기")
        import_btn.setFixedSize(*config.BUTTON_SIZES['medium'])
        import_btn.clicked.connect(self.on_import_csv)
        toolbar.addWidget(import_btn)
        
        # CSV 내보내기 버튼
        export_btn = QPushButton("📤 CSV 내보내기")
        export_btn.setFixedSize(*config.BUTTON_SIZES['medium'])
        export_btn.clicked.connect(self.on_export_csv)
        toolbar.addWidget(export_btn)
        
        toolbar.addStretch()
        
        # 정렬 선택
        sort_label = QLabel("정렬:")
        toolbar.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['최근 추가순', '영어 가나다순', '학습 많은순', '오답률 높은순'])
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        toolbar.addWidget(self.sort_combo)
        
        # 검색 입력
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 단어 검색...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self.on_search_changed)
        toolbar.addWidget(self.search_input)
        
        # 새로고침 버튼
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(*config.BUTTON_SIZES['icon'])
        refresh_btn.clicked.connect(self.refresh_word_list)
        toolbar.addWidget(refresh_btn)
        
        return toolbar
    
    def create_word_table(self):
        """단어 목록 테이블 생성"""
        table = QTableWidget()
        
        # 컬럼 설정
        columns = ['ID', '⭐', '영어', '한국어', '메모', '학습', '오답률', '최종학습일']
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # 컬럼 너비 설정
        table.setColumnWidth(0, 50)   # ID
        table.setColumnWidth(1, 40)   # 즐겨찾기
        table.setColumnWidth(2, 150)  # 영어
        table.setColumnWidth(3, 150)  # 한국어
        table.setColumnWidth(4, 200)  # 메모
        table.setColumnWidth(5, 60)   # 학습
        table.setColumnWidth(6, 80)   # 오답률