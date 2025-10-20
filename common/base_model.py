# 2025-10-21 - 스마트 단어장 - 기본 모델 클래스 (BaseModel)
# 파일 위치: common/base_model.py

"""
프로젝트의 모든 모델(Model) 클래스가 상속받는 기본 클래스.
- DatabaseConnection 인스턴스를 관리
- 테이블 이름(table_name)을 필수로 요구
- 기본적인 CRUD 및 유틸리티 메서드 제공
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import sqlite3

# 인프라 모듈 임포트
from common.db_connection import get_db_connection, DatabaseConnection
from common.logger import get_logger

# 현재 모델에서는 DB에 접근해야 하므로, Model 클래스의 인스턴스마다 로거를 가져옵니다.
logger = get_logger(__name__)


class BaseModel:
    """
    모든 데이터베이스 모델의 기본 클래스.
    """

    def __init__(self, table_name: str):
        """
        초기화 시 이 모델이 담당하는 DB 테이블 이름을 지정해야 합니다.

        Args:
            table_name: 이 모델이 처리할 데이터베이스 테이블 이름 (예: 'words')
        """
        if not table_name:
            raise ValueError("BaseModel은 반드시 table_name을 지정해야 합니다.")
            
        self.table_name = table_name
        # 싱글톤으로 관리되는 DB 연결 객체 가져오기
        self.db: DatabaseConnection = get_db_connection() 
        logger.debug(f"BaseModel 초기화 완료: Table={self.table_name}")

    # ==========================================================================
    # 기본 CRUD 메서드 (모든 테이블에 공통적으로 필요)
    # ==========================================================================

    def find_all(self, columns: str = '*') -> List[Dict[str, Any]]:
        """
        테이블의 모든 레코드를 조회합니다.
        """
        sql = f"SELECT {columns} FROM {self.table_name}"
        return self.db.execute_query(sql)

    def find_by_id(self, item_id: int, id_column: str = None, columns: str = '*') -> Optional[Dict[str, Any]]:
        """
        기본 키를 기준으로 하나의 레코드를 조회합니다.
        """
        if id_column is None:
            # 기본 키가 'word_id'일 수도 'setting_key'일 수도 있으므로 유연하게 처리
            id_column = f"{self.table_name.rstrip('s')}_id" # 예: words -> word_id
        
        sql = f"SELECT {columns} FROM {self.table_name} WHERE {id_column} = ?"
        result = self.db.execute_query(sql, (item_id,))
        return result[0] if result else None
    
    def exists(self, where_clause: str, params: Optional[Tuple[Any, ...]] = None) -> bool:
        """
        특정 조건의 레코드가 존재하는지 확인합니다.
        """
        sql = f"SELECT 1 FROM {self.table_name} WHERE {where_clause} LIMIT 1"
        return bool(self.db.execute_query(sql, params))

    # ==========================================================================
    # 유틸리티 메서드
    # ==========================================================================
    
    @staticmethod
    def _get_current_datetime() -> str:
        """현재 시각을 DB 저장 형식(TEXT)으로 반환합니다."""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _validate_data(self, data: Dict[str, Any]):
        """
        데이터 유효성을 검사합니다. (하위 클래스에서 오버라이드 예정)
        """
        # 기본적으로 모든 키가 None이 아닌지 확인
        for key, value in data.items():
            if value is None:
                raise ValueError(f"필수 필드 '{key}'가 누락되었습니다.")