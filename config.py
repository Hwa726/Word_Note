# 2025-10-27 - 스마트 단어장 - 전역 설정 및 상수 (완성본)
# 파일 위치: config.py (프로젝트 루트: C:\dev\word\config.py)

import os
from pathlib import Path
from datetime import datetime
import logging

# ==============================================================================
# 1. 애플리케이션 정보
# ==============================================================================

APP_NAME = "Smart Vocabulary Builder"
APP_VERSION = "1.0.0"

# ==============================================================================
# 2. 프로젝트 경로 설정
# ==============================================================================

# 프로젝트 루트 경로 (config.py가 위치한 C:\dev\word)
BASE_DIR = Path(__file__).resolve().parent

# 데이터 폴더
DATA_DIR = BASE_DIR / 'data'
BACKUP_DIR = DATA_DIR / 'backups'

# 로그 폴더
LOG_DIR = BASE_DIR / 'logs'

# 리소스 폴더
ASSETS_DIR = BASE_DIR / 'assets'
ICONS_DIR = ASSETS_DIR / 'icons'
STYLES_DIR = ASSETS_DIR / 'styles'

# 데이터베이스 경로
DB_PATH = DATA_DIR / 'vocabulary.db'
SCHEMA_PATH = BASE_DIR / 'schema.sql'

# 로그 파일 경로
LOG_FILE = LOG_DIR / 'app.log'

# ==============================================================================
# 3. 로깅 설정
# ==============================================================================

LOG_LEVEL = 'DEBUG'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ==============================================================================
# 4. 학습 설정 및 상수 (SM-2, 숙련도)
# ==============================================================================

# SuperMemo-2 (SM-2) 알고리즘 상수
SM2_INITIAL_EASE_FACTOR = 2.5
SM2_MIN_EASE_FACTOR = 1.3
DEFAULT_DAILY_GOAL = 50

# 숙련도 레벨 (오답률 기준)
MASTERY_LEVELS = {
    'new': {'threshold': 100.0, 'label': '신규', 'color': '#AAAAAA'}, 
    'weak': {'threshold': 70.0, 'label': '취약', 'color': '#FF3B30'},   
    'moderate': {'threshold': 30.0, 'label': '보통', 'color': '#FFCC00'},
    'strong': {'threshold': 0.0, 'label': '숙련', 'color': '#34C759'}, 
}

def get_mastery_level(wrong_rate: float) -> dict:
    """오답률을 기반으로 숙지도 레벨을 반환한다."""
    if wrong_rate is None:
        return {
            'label': MASTERY_LEVELS['new']['label'],
            'color': MASTERY_LEVELS['new']['color']
        }
    
    if wrong_rate >= MASTERY_LEVELS['weak']['threshold']:
        return MASTERY_LEVELS['weak']
    elif wrong_rate >= MASTERY_LEVELS['moderate']['threshold']:
        return MASTERY_LEVELS['moderate']
    else:
        return MASTERY_LEVELS['strong']

# ==============================================================================
# 5. UI 레이아웃 상수 (추가됨)
# ==============================================================================

# 간격 설정 (픽셀)
SPACING = {
    'section': 20,      # 큰 섹션 간 간격 (툴바 <-> 테이블 <-> 정보바)
    'group': 15,        # 그룹 내 요소 간 간격
    'item': 10,         # 작은 요소 간 간격
    'compact': 5        # 촘촘한 간격
}

# 버튼 크기 (width, height)
BUTTON_SIZES = {
    'small': (80, 30),      # 작은 버튼 (확인, 취소)
    'medium': (120, 35),    # 중간 버튼 (단어 추가, CSV)
    'large': (200, 45),     # 큰 버튼 (학습 시작)
    'icon': (35, 35)        # 아이콘 버튼 (새로고침 🔄)
}

# 색상 팔레트
COLORS = {
    'primary': '#007AFF',       # 주요 액션 (학습 시작)
    'success': '#34C759',       # 성공 (정답, 숙련)
    'warning': '#FFCC00',       # 경고 (보통)
    'danger': '#FF3B30',        # 위험 (오답, 취약)
    'info': '#5AC8FA',          # 정보
    'background': '#F5F5F5',    # 배경
    'text': '#000000',          # 기본 텍스트
    'text_secondary': '#666666', # 보조 텍스트
    'border': '#DDDDDD'         # 테두리
}

# 폰트 설정
FONTS = {
    'family': 'Nanum Gothic',   # 기본 폰트
    'size_small': 10,           # 작은 텍스트 (설명, 주석)
    'size_normal': 12,          # 일반 텍스트
    'size_subtitle': 14,        # 소제목
    'size_title': 18,           # 제목
    'size_large': 24            # 큰 텍스트 (플래시카드)
}

# 테이블 컬럼 너비 (단어 관리 뷰)
TABLE_COLUMN_WIDTHS = {
    'id': 50,
    'favorite': 40,
    'english': 150,
    'korean': 150,
    'memo': 200,
    'attempts': 60,
    'wrong_rate': 80,
    'last_date': 100
}

# ==============================================================================
# 6. 폴더 자동 생성
# ==============================================================================

def ensure_directories():
    """필요한 디렉토리가 없으면 자동으로 생성한다."""
    directories = [
        DATA_DIR, 
        BACKUP_DIR, 
        LOG_DIR, 
        ASSETS_DIR,
        ICONS_DIR,
        STYLES_DIR
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


if __name__ == '__main__':
    # 테스트 코드
    ensure_directories()
    print(f"프로젝트: {APP_NAME} v{APP_VERSION}")
    print(f"루트 경로: {BASE_DIR}")
    print(f"로그 레벨: {LOG_LEVEL}")
    
    print("\n숙련도 테스트:")
    print(f"오답률 80%: {get_mastery_level(80.0)['label']}")
    
    print("\nUI 설정 테스트:")
    print(f"섹션 간격: {SPACING['section']}px")
    print(f"중간 버튼 크기: {BUTTON_SIZES['medium']}")
    print(f"주요 색상: {COLORS['primary']}")
