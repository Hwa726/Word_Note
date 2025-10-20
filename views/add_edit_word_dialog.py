# 2025-10-20 - 스마트 단어장 - 단어 추가/수정 다이얼로그
# 파일 위치: add_edit_word_dialog.py

"""
단어 추가/수정 다이얼로그

단어를 추가하거나 수정하는 모달 다이얼로그를 제공한다.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QLineEdit, QTextEdit, QPushButton, 
                              QCheckBox, QMessageBox)
from PyQt5.QtCore import Qt

import config
from common.logger import get_logger

logger = get_logger(__name__)


class AddEditWordDialog(QDialog):
    """
    단어 추가/수정 다이얼로그 클래스
    """
    
    def __init__(self, parent=None, mode='add', word_data=None):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            mode: 'add' (추가) 또는 'edit' (수정)
            word_data: 수정 모드일 때 기존 단어 데이터
        """
        super().__init__(parent)
        
        self.mode = mode
        self.word_data = word_data or {}
        
        self.setup_ui()
        self.load_data()
        
        logger.debug(f"AddEditWordDialog 생성: mode={mode}")
    
    def setup_ui(self):
        """UI 설정"""
        # 다이얼로그 기본 설정
        title = "단어 추가" if self.mode == 'add' else "단어 수정"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setModal(True)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        
        # 제목
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: {config.FONTS['size_subtitle']}pt; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        form_layout.setSpacing(config.SPACING['group'])
        
        # 영어 단어 입력
        self.english_input = QLineEdit()
        self.english_input.setPlaceholderText("예: apple")
        self.english_input.setMaxLength(100)
        form_layout.addRow("영어 단어: *", self.english_input)
        
        # 한국어 뜻 입력
        self.korean_input = QLineEdit()
        self.korean_input.setPlaceholderText("예: 사과")
        self.korean_input.setMaxLength(500)
        form_layout.addRow("한국어 뜻: *", self.korean_input)
        
        # 메모 입력
        self.memo_input = QTextEdit()
        self.memo_input.setPlaceholderText("예: 과일 이름")
        self.memo_input.setMaximumHeight(100)
        form_layout.addRow("메모:", self.memo_input)
        
        # 즐겨찾기 체크박스
        self.favorite_checkbox = QCheckBox("즐겨찾기에 추가")
        form_layout.addRow("", self.favorite_checkbox)
        
        main_layout.addLayout(form_layout)
        
        # 안내 문구
        hint_label = QLabel("* 필수 항목")
        hint_label.setStyleSheet(f"font-size: {config.FONTS['size_small']}pt; color: gray;")
        main_layout.addWidget(hint_label)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 취소 버튼
        cancel_btn = QPushButton("취소")
        cancel_btn.setFixedSize(*config.BUTTON_SIZES['medium'])
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # 저장 버튼
        save_text = "추가" if self.mode == 'add' else "수정"
        self.save_btn = QPushButton(save_text)
        self.save_btn.setFixedSize(*config.BUTTON_SIZES['medium'])
        self.save_btn.setStyleSheet(f"background-color: {config.COLORS['primary']}; color: white;")
        self.save_btn.clicked.connect(self.on_save)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
        
        # 레이아웃 적용
        self.setLayout(main_layout)
        
        # 엔터키로 저장
        self.english_input.returnPressed.connect(self.korean_input.setFocus)
        self.korean_input.returnPressed.connect(self.on_save)
    
    def load_data(self):
        """기존 데이터 로드 (수정 모드)"""
        if self.mode == 'edit' and self.word_data:
            self.english_input.setText(self.word_data.get('english', ''))
            self.korean_input.setText(self.word_data.get('korean', ''))
            self.memo_input.setPlainText(self.word_data.get('memo', ''))
            
            is_favorite = self.word_data.get('is_favorite', 0) == 1
            self.favorite_checkbox.setChecked(is_favorite)
            
            logger.debug(f"기존 데이터 로드: {self.word_data.get('english')}")
    
    def on_save(self):
        """저장 버튼 클릭"""
        # 입력값 가져오기
        english = self.english_input.text().strip()
        korean = self.korean_input.text().strip()
        memo = self.memo_input.toPlainText().strip()
        is_favorite = self.favorite_checkbox.isChecked()
        
        # 유효성 검사
        validation_result = self.validate_input(english, korean)
        if not validation_result['valid']:
            QMessageBox.warning(self, "입력 오류", validation_result['message'])
            return
        
        # 데이터 저장
        self.result_data = {
            'english': english,
            'korean': korean,
            'memo': memo,
            'is_favorite': 1 if is_favorite else 0
        }
        
        logger.info(f"단어 다이얼로그 저장: {english}")
        self.accept()
    
    def validate_input(self, english: str, korean: str) -> dict:
        """
        입력값 유효성 검사
        
        Args:
            english: 영어 단어
            korean: 한국어 뜻
        
        Returns:
            dict: {'valid': bool, 'message': str}
        """
        if not english:
            return {'valid': False, 'message': '영어 단어를 입력해주세요.'}
        
        if not korean:
            return {'valid': False, 'message': '한국어 뜻을 입력해주세요.'}
        
        if len(english) > 100:
            return {'valid': False, 'message': '영어 단어는 100자를 초과할 수 없습니다.'}
        
        if len(korean) > 500:
            return {'valid': False, 'message': '한국어 뜻은 500자를 초과할 수 없습니다.'}
        
        return {'valid': True, 'message': ''}
    
    def get_data(self):
        """
        입력된 데이터를 반환한다.
        
        Returns:
            dict: {'english': str, 'korean': str, 'memo': str, 'is_favorite': int}
        """
        return getattr(self, 'result_data', None)


if __name__ == '__main__':
    # 테스트
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 추가 모드 테스트
    dialog = AddEditWordDialog(mode='add')
    if dialog.exec_() == QDialog.Accepted:
        data = dialog.get_data()
        print(f"추가 데이터: {data}")
    
    # 수정 모드 테스트
    word_data = {
        'word_id': 1,
        'english': 'apple',
        'korean': '사과',
        'memo': '과일',
        'is_favorite': 1
    }
    dialog = AddEditWordDialog(mode='edit', word_data=word_data)
    if dialog.exec_() == QDialog.Accepted:
        data = dialog.get_data()
        print(f"수정 데이터: {data}")