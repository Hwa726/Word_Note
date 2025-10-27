# 2025-10-27 - 스마트 단어장 - 단어 관리 뷰 (Phase 1 완성본)
# 파일 위치: views/word_manager_view.py

"""
단어 관리 뷰

단어 목록, 검색, 추가/수정/삭제 UI를 제공한다.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QLineEdit, 
                              QLabel, QMessageBox, QHeaderView, QFileDialog,
                              QComboBox, QAbstractItemView, QDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

import config
from common.logger import get_logger
from controllers.word_controller import WordController
from views.add_edit_word_dialog import AddEditWordDialog

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
        
        # ===== Phase 1: 컬럼 너비 설정 (config 사용) =====
        table.setColumnWidth(0, config.TABLE_COLUMN_WIDTHS['id'])
        table.setColumnWidth(1, config.TABLE_COLUMN_WIDTHS['favorite'])
        table.setColumnWidth(2, config.TABLE_COLUMN_WIDTHS['english'])
        table.setColumnWidth(3, config.TABLE_COLUMN_WIDTHS['korean'])
        table.setColumnWidth(4, config.TABLE_COLUMN_WIDTHS['memo'])
        table.setColumnWidth(5, config.TABLE_COLUMN_WIDTHS['attempts'])
        table.setColumnWidth(6, config.TABLE_COLUMN_WIDTHS['wrong_rate'])
        table.setColumnWidth(7, config.TABLE_COLUMN_WIDTHS['last_date'])
        
        # ===== Phase 1: 테이블 속성 설정 =====
        # 선택 동작: 행 단위 선택
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # 선택 모드: 단일 선택
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # 편집 금지
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 교차 색상 (가독성)
        table.setAlternatingRowColors(True)
        
        # 정렬 활성화
        table.setSortingEnabled(True)
        
        # 마지막 컬럼 늘리기
        table.horizontalHeader().setStretchLastSection(True)
        
        # ===== Phase 1: 이벤트 연결 (Phase 2에서 구현) =====
        # table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        # table.cellClicked.connect(self.on_cell_clicked)
        # table.setContextMenuPolicy(Qt.CustomContextMenu)
        # table.customContextMenuRequested.connect(self.show_context_menu)
        
        return table
    
    def create_info_bar(self):
        """하단 정보바 생성"""
        info_bar = QHBoxLayout()
        
        # 총 단어 수 라벨
        self.total_label = QLabel("총 단어: 0개")
        info_bar.addWidget(self.total_label)
        
        # 늘어나는 공간 (좌우 정렬 효과)
        info_bar.addStretch()
        
        # 선택된 단어 라벨
        self.selected_label = QLabel("선택: 0개")
        info_bar.addWidget(self.selected_label)
        
        return info_bar
    
    def refresh_word_list(self):
        """
        Controller에서 단어 목록을 가져와 테이블에 표시합니다.
        Phase 1의 핵심 메서드!
        """
        logger.debug("단어 목록 새로고침 시작")
        
        try:
            # ===== Step 1: Controller에서 데이터 가져오기 =====
            # 검색어와 정렬 기준을 Controller에 전달
            search_keyword = self.search_input.text().strip()
            sort_order = self.sort_combo.currentText()
            
            # ✅ 수정: 직접 SQL 쿼리로 단어 목록 가져오기 (동적 정렬 적용)
            try:
                # 정렬 기준 매핑
                sort_mapping = {
                    '최근 추가순': 'w.created_date DESC',
                    '영어 가나다순': 'w.english ASC',
                    '학습 많은순': 'ws.total_attempts DESC',
                    '오답률 높은순': 'wrong_rate DESC'
                }
                
                # 현재 선택된 정렬 기준
                current_sort = self.sort_combo.currentText()
                order_by_clause = sort_mapping.get(current_sort, 'w.created_date DESC')
                
                query = f"""
                    SELECT 
                        w.*,
                        COALESCE(ws.total_attempts, 0) AS total_attempts,
                        COALESCE(ws.correct_count, 0) AS correct_count,
                        COALESCE(ws.wrong_count, 0) AS wrong_count,
                        ws.last_study_date,
                        CASE 
                            WHEN ws.total_attempts > 0 THEN 
                                ROUND((ws.wrong_count * 100.0 / ws.total_attempts), 1)
                            ELSE NULL 
                        END AS wrong_rate
                    FROM words w
                    LEFT JOIN word_statistics ws ON w.word_id = ws.word_id
                    ORDER BY {order_by_clause}
                """
                words = self.controller.model.db.execute_query(query)
                result = {'success': True, 'words': words}
            except Exception as e:
                logger.error(f"단어 목록 조회 실패: {e}")
                QMessageBox.warning(self, "오류", f"단어 목록을 불러올 수 없습니다:\n{e}")
                return
            
            # ===== Step 2: 테이블 초기화 =====
            self.word_table.setRowCount(0)
            self.current_words = result.get('words', [])
            
            # ===== Step 3: 각 단어마다 행 추가 =====
            for row_idx, word in enumerate(self.current_words):
                self.word_table.insertRow(row_idx)
                
                # 컬럼 0: ID (가운데 정렬)
                id_item = QTableWidgetItem(str(word['word_id']))
                id_item.setTextAlignment(Qt.AlignCenter)
                self.word_table.setItem(row_idx, 0, id_item)
                
                # 컬럼 1: 즐겨찾기 (⭐ or 빈 칸)
                star = "⭐" if word.get('is_favorite') == 1 else ""
                star_item = QTableWidgetItem(star)
                star_item.setTextAlignment(Qt.AlignCenter)
                self.word_table.setItem(row_idx, 1, star_item)
                
                # 컬럼 2: 영어
                self.word_table.setItem(row_idx, 2, QTableWidgetItem(word['english']))
                
                # 컬럼 3: 한국어
                self.word_table.setItem(row_idx, 3, QTableWidgetItem(word['korean']))
                
                # 컬럼 4: 메모
                memo = word.get('memo', '') or ''  # None 처리
                self.word_table.setItem(row_idx, 4, QTableWidgetItem(memo))
                
                # 컬럼 5: 학습 횟수 (가운데 정렬)
                attempts = str(word.get('total_attempts', 0)) + "회"
                attempts_item = QTableWidgetItem(attempts)
                attempts_item.setTextAlignment(Qt.AlignCenter)
                self.word_table.setItem(row_idx, 5, attempts_item)
                
                # 컬럼 6: 오답률 (색상 표시, 가운데 정렬)
                wrong_rate = word.get('wrong_rate')
                rate_item = QTableWidgetItem()
                rate_item.setTextAlignment(Qt.AlignCenter)
                
                if wrong_rate is not None:
                    rate_item.setText(f"{wrong_rate:.1f}%")
                    
                    # 오답률에 따라 배경색 변경
                    if wrong_rate >= 70:
                        rate_item.setBackground(QColor('#FFE5E5'))  # 연한 빨강 (취약)
                    elif wrong_rate >= 30:
                        rate_item.setBackground(QColor('#FFF4E5'))  # 연한 주황 (보통)
                    else:
                        rate_item.setBackground(QColor('#E5F5E5'))  # 연한 녹색 (숙련)
                else:
                    rate_item.setText("-")  # 신규 단어
                    
                self.word_table.setItem(row_idx, 6, rate_item)
                
                # 컬럼 7: 최종학습일 (가운데 정렬)
                last_date = word.get('last_study_date', '-')
                if last_date and last_date != '-':
                    # "2025-10-25 14:30:00" → "2025-10-25"로 변환
                    last_date = last_date.split(' ')[0]
                    
                date_item = QTableWidgetItem(last_date)
                date_item.setTextAlignment(Qt.AlignCenter)
                self.word_table.setItem(row_idx, 7, date_item)
            
            # ===== Step 4: 정보바 업데이트 =====
            self.total_label.setText(f"총 단어: {len(self.current_words)}개")
            
            # ===== Step 5: 시그널 발생 =====
            self.word_count_changed.emit(len(self.current_words))
            
            logger.info(f"단어 목록 표시 완료: {len(self.current_words)}개")
            
        except Exception as e:
            logger.error(f"단어 목록 새로고침 중 오류 발생: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"단어 목록을 표시하는 중 오류가 발생했습니다:\n{e}")
    
    def on_add_word(self):
        """단어 추가 버튼 클릭 핸들러"""
        logger.debug("단어 추가 다이얼로그 열기")
        
        # 1. 다이얼로그 생성 (추가 모드)
        dialog = AddEditWordDialog(self, mode='add')
        
        # 2. 다이얼로그 표시 및 결과 대기
        if dialog.exec_() == QDialog.Accepted:
            # 3. 입력된 데이터 가져오기
            data = dialog.get_data()
            
            if not data:
                logger.warning("다이얼로그에서 데이터를 가져오지 못함")
                return
            
            # 4. Controller에 요청 (is_favorite 전달)
            result = self.controller.create_word(
                english=data['english'],
                korean=data['korean'],
                memo=data.get('memo', ''),
                is_favorite=data.get('is_favorite', 0)
            )
            
            # 5. 결과 처리
            if result['success']:
                logger.info(f"단어 추가 성공: {data['english']}")
                QMessageBox.information(self, "성공", "단어가 추가되었습니다.")
                self.refresh_word_list()  # 테이블 새로고침
            else:
                logger.error(f"단어 추가 실패: {result['message']}")
                QMessageBox.warning(self, "오류", result['message'])
    
    # ===== Phase 2에서 구현할 메서드들 (임시 스텁) =====
    
    def on_import_csv(self):
        """CSV 가져오기 (Phase 3에서 구현)"""
        QMessageBox.information(self, "준비 중", "CSV 가져오기 기능은 Phase 3에서 구현됩니다.")
    
    def on_export_csv(self):
        """CSV 내보내기 (Phase 3에서 구현)"""
        QMessageBox.information(self, "준비 중", "CSV 내보내기 기능은 Phase 3에서 구현됩니다.")
    
    def on_sort_changed(self, index):
        """정렬 기준 변경"""
        logger.debug(f"정렬 기준 변경: {self.sort_combo.currentText()}")
        self.refresh_word_list()  # 정렬 기준에 따라 목록 새로고침
    
    def on_search_changed(self, text):
        """검색어 변경 (Phase 3에서 구현)"""
        logger.debug(f"검색어 변경: {text}")
        # TODO: 검색 로직 구현
