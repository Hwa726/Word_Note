# 2025-10-27 - 스마트 단어장 - 기본 모델 클래스 (완성본)
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
        
        Args:
            columns: 조회할 컬럼 (기본값: '*')
        
        Returns:
            List[Dict]: 레코드 목록
        """
        sql = f"SELECT {columns} FROM {self.table_name}"
        return self.db.execute_query(sql)

    def find_by_id(self, item_id: int, id_column: str = None, columns: str = '*') -> Optional[Dict[str, Any]]:
        """
        기본 키를 기준으로 하나의 레코드를 조회합니다.
        
        Args:
            item_id: 조회할 ID 값
            id_column: ID 컬럼명 (None이면 자동 추정)
            columns: 조회할 컬럼
        
        Returns:
            Optional[Dict]: 레코드 (없으면 None)
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
        
        Args:
            where_clause: WHERE 조건 (예: 'english = ?')
            params: 파라미터 튜플
        
        Returns:
            bool: 존재 여부
        """
        sql = f"SELECT 1 FROM {self.table_name} WHERE {where_clause} LIMIT 1"
        return bool(self.db.execute_query(sql, params))
    
    def insert(self, data: Dict[str, Any]) -> int:
        """
        새 레코드를 삽입하고 생성된 ID를 반환합니다.
        
        Args:
            data: 삽입할 데이터 딕셔너리 (컬럼명: 값)
        
        Returns:
            int: 생성된 레코드의 ID (lastrowid)
        
        Example:
            word_id = model.insert({'english': 'apple', 'korean': '사과'})
        """
        if not data:
            raise ValueError("삽입할 데이터가 없습니다.")
        
        # 컬럼명과 값 분리
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = tuple(data.values())
        
        sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        # ✅ 수정: lastrowid를 직접 가져오기
        try:
            cursor = self.db._connection.cursor()
            cursor.execute(sql, values)
            last_id = cursor.lastrowid
            self.db._connection.commit()
            
            logger.debug(f"레코드 삽입 성공: Table={self.table_name}, ID={last_id}")
            return last_id
        except Exception as e:
            logger.error(f"레코드 삽입 실패: Table={self.table_name}, Error={e}")
            self.db._connection.rollback()
            raise
    
    def update(self, id_column: str, id_value: Any, data: Dict[str, Any]) -> bool:
        """
        기존 레코드를 수정합니다.
        
        Args:
            id_column: ID 컬럼명 (예: 'word_id')
            id_value: ID 값
            data: 수정할 데이터 딕셔너리
        
        Returns:
            bool: 성공 여부 (1개 이상의 행이 수정되면 True)
        
        Example:
            success = model.update('word_id', 5, {'korean': '사과나무'})
        """
        if not data:
            raise ValueError("수정할 데이터가 없습니다.")
        
        # SET 절 생성
        set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
        values = list(data.values())
        values.append(id_value)  # WHERE 절의 값
        
        sql = f"UPDATE {self.table_name} SET {set_clause} WHERE {id_column} = ?"

        rowcount = self.db.execute_non_query(sql, tuple(values))
        
        logger.debug(f"레코드 수정: Table={self.table_name}, ID={id_value}, 수정 행수={rowcount}")
        return rowcount > 0
    
    def delete(self, id_column: str, id_value: Any) -> bool:
        """
        레코드를 삭제합니다.
        
        Args:
            id_column: ID 컬럼명 (예: 'word_id')
            id_value: ID 값
        
        Returns:
            bool: 성공 여부 (1개 이상의 행이 삭제되면 True)
        
        Example:
            success = model.delete('word_id', 5)
        """
        sql = f"DELETE FROM {self.table_name} WHERE {id_column} = ?"

        rowcount = self.db.execute_non_query(sql, (id_value,))
        
        logger.debug(f"레코드 삭제: Table={self.table_name}, ID={id_value}, 삭제 행수={rowcount}")
        return rowcount > 0
    
    def count(self, where_clause: str = None, params: Optional[Tuple[Any, ...]] = None) -> int:
        """
        레코드 개수를 반환합니다.
        
        Args:
            where_clause: WHERE 조건 (선택, 없으면 전체 개수)
            params: 파라미터 튜플
        
        Returns:
            int: 레코드 개수
        
        Example:
            total = model.count()
            favorites = model.count('is_favorite = ?', (1,))
        """
        if where_clause:
            sql = f"SELECT COUNT(*) as count FROM {self.table_name} WHERE {where_clause}"
        else:
            sql = f"SELECT COUNT(*) as count FROM {self.table_name}"
        
        result = self.db.execute_query(sql, params)
        return result[0]['count'] if result else 0

    # ==========================================================================
    # 유틸리티 메서드
    # ==========================================================================
    
    def get_current_datetime(self) -> str:
        """
        현재 시각을 DB 저장 형식(TEXT)으로 반환합니다.
        
        Returns:
            str: 'YYYY-MM-DD HH:MM:SS' 형식의 문자열
        """
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def _get_current_datetime() -> str:
        """
        현재 시각을 DB 저장 형식(TEXT)으로 반환합니다. (static 버전)
        하위 호환성을 위해 유지합니다.
        
        Returns:
            str: 'YYYY-MM-DD HH:%M:%S' 형식의 문자열
        """
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _validate_data(self, data: Dict[str, Any]):
        """
        데이터 유효성을 검사합니다. (하위 클래스에서 오버라이드 예정)
        
        Args:
            data: 검사할 데이터 딕셔너리
        
        Raises:
            ValueError: 필수 필드 누락 시
        """
        # 기본적으로 모든 키가 None이 아닌지 확인
        for key, value in data.items():
            if value is None:
                raise ValueError(f"필수 필드 '{key}'가 누락되었습니다.")
