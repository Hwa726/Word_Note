# 2025-10-20 - 스마트 단어장 - 데이터베이스 연결 관리
# 파일 위치: common/db_connection.py

"""
데이터베이스 연결 관리

SQLite 데이터베이스 연결을 관리하고 쿼리 실행을 담당한다.
싱글톤 패턴을 사용하여 하나의 연결만 유지한다.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime # datetime 모듈 추가

import config
from common.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnection:
    """
    데이터베이스 연결 관리 클래스
    
    싱글톤 패턴으로 구현되어 프로그램 전체에서 하나의 인스턴스만 사용한다.
    """
    
    _instance = None
    _connection: Optional[sqlite3.Connection] = None
    
    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """초기화 (싱글톤이므로 한 번만 실행됨)"""
        if self._connection is None:
            self.db_path = config.DB_PATH
            self.connect()
    
    @property
    def is_connected(self) -> bool:
        """현재 DB 연결 상태를 반환한다."""
        return self._connection is not None
        
    def connect(self):
        """
        데이터베이스에 연결한다.
        """
        # 데이터 폴더가 존재하는지 확인 (config.ensure_directories에서 처리됨)
        # config.DB_PATH의 부모 디렉토리가 없으면 오류 발생 가능성 있음
        if not self.db_path.parent.exists():
            # 프로그램 시작 시 main.py에서 ensure_directories를 호출해야 함
            logger.warning(f"데이터 디렉토리 {self.db_path.parent}가 없어 자동 생성 시도.")
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
        try:
            # check_same_thread=False는 PyQt 등 멀티스레드 환경에서 필요할 수 있음
            self._connection = sqlite3.connect(
                self.db_path, 
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False
            )
            self._connection.row_factory = self._dict_factory # 결과 dict 형태로 반환하도록 설정
            logger.info(f"DB 연결 성공: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.critical(f"DB 연결 실패: {e}")
            self._connection = None
            return False

    def close(self):
        """데이터베이스 연결을 닫는다."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("DB 연결 종료")

    def _dict_factory(self, cursor: sqlite3.Cursor, row: Tuple[Any, ...]) -> Dict[str, Any]:
        """쿼리 결과를 딕셔너리로 반환하기 위한 팩토리 함수"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
        
    def execute_query(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
        """
        SELECT 쿼리를 실행하고 결과를 딕셔너리 리스트로 반환한다.
        """
        if not self.is_connected:
            logger.error("DB 연결 상태가 아닙니다. 쿼리 실행 실패.")
            return []
            
        try:
            cursor = self._connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"DB 쿼리 오류: {e}\nSQL: {sql}\nParams: {params}")
            return []

    def execute_non_query(self, sql: str, params: Optional[Tuple[Any, ...]] = None, commit: bool = True) -> int:
        """
        INSERT, UPDATE, DELETE 쿼리를 실행하고 변경된 행의 수를 반환한다.
        """
        if not self.is_connected:
            logger.error("DB 연결 상태가 아닙니다. Non-쿼리 실행 실패.")
            return 0
            
        try:
            cursor = self._connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                # 스키마 초기화처럼 긴 스크립트를 실행할 때 executemany 대신 execute를 사용
                cursor.executescript(sql) if len(sql) > 1000 and 'CREATE' in sql else cursor.execute(sql)
            
            rowcount = cursor.rowcount
            if commit:
                self._connection.commit()
            return rowcount
        except sqlite3.Error as e:
            logger.error(f"DB Non-쿼리 오류: {e}\nSQL: {sql}\nParams: {params}")
            if commit:
                self._connection.rollback()
            raise # 오류를 호출자에게 다시 전달 (main.py에서 catch하도록)
        except Exception as e:
            logger.error(f"예상치 못한 DB 오류: {e}\nSQL: {sql}")
            if commit:
                self._connection.rollback()
            raise


    def initialize_database(self, schema_file: Path) -> None:
        """
        데이터베이스 스키마를 초기화합니다 (user_settings 테이블 포함).
        schema.sql 파일을 읽어 SQL 스크립트를 실행합니다.
        """
        if not self.is_connected:
            logger.error("DB 연결 상태가 아닙니다. 초기화 실패.")
            raise ConnectionError("DB 연결 실패")

        if not schema_file.exists():
            logger.critical(f"스키마 파일이 존재하지 않습니다: {schema_file}")
            raise FileNotFoundError(f"스키마 파일 없음: {schema_file}")

        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            # SQL 스크립트 실행 (PRAGMA foreign_keys 및 모든 테이블 생성, 기본 설정값 삽입 포함)
            # execute_non_query 내부에서 executescript()를 사용하도록 처리함.
            self.execute_non_query(sql_script, commit=True) 
            logger.info(f"데이터베이스 스키마 초기화 완료: {schema_file.name}")
            
        except sqlite3.Error as e:
            logger.critical(f"SQLite 오류 발생: {e}")
            raise
        except Exception as e:
            logger.critical(f"데이터베이스 초기화 중 예상치 못한 오류 발생: {e}")
            raise
            
    def check_database_integrity(self) -> bool:
        """
        데이터베이스 무결성을 검사한다.
        """
        if not self.is_connected:
            return False
            
        try:
            result = self.execute_query("PRAGMA integrity_check")
            is_ok = result[0]['integrity_check'] == 'ok' if result and result[0] else False
            
            if is_ok:
                logger.info("데이터베이스 무결성 검사 통과")
            else:
                logger.warning("데이터베이스 무결성 검사 실패")
            
            return is_ok
            
        except Exception as e:
            logger.error(f"무결성 검사 중 오류: {e}")
            return False


# 전역 인스턴스 (싱글톤)
_db_instance: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """
    데이터베이스 연결 인스턴스를 반환한다.
    
    Returns:
        DatabaseConnection: 데이터베이스 연결 객체
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnection()
    return _db_instance


if __name__ == '__main__':
    # 테스트 코드
    print("=" * 60)
    print("데이터베이스 연결 테스트")
    print("=" * 60)
    
    # config.py의 ensure_directories()가 실행되었다고 가정
    
    db = get_db_connection()
    
    # 데이터베이스 초기화 (실제 schema.sql 파일이 있어야 함)
    # try:
    #     # config.py의 SCHEMA_PATH 정의 필요
    #     # db.initialize_database(config.SCHEMA_PATH) 
    #     # print("DB 초기화 완료.")
    # except Exception as e:
    #     print(f"DB 초기화 테스트 실패: {e}")
        
    print(f"연결 상태: {db.is_connected}")
    db.close()
    print(f"종료 후 연결 상태: {db.is_connected}")