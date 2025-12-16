"""
할 일 관리 모듈 (core 패키지)
SQLite를 사용하여 할 일을 저장하고 관리합니다.
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
from .config import Config


class TodoManager:
    """할 일 관리자"""
    
    def __init__(self):
        """할 일 관리자 초기화 및 데이터베이스 설정"""
        # 데이터 디렉토리 생성
        db_dir = os.path.dirname(Config.DB_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        self.db_path = Config.DB_PATH
        self._init_database()
    
    def _init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_todo(self, title: str, description: str = "") -> int:
        """
        할 일 추가
        
        Args:
            title: 할 일 제목
            description: 할 일 설명
            
        Returns:
            생성된 할 일의 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO todos (title, description, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (title, description, now, now))
        
        todo_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return todo_id
    
    def get_todos(self, completed: Optional[bool] = None) -> List[Dict]:
        """
        할 일 목록 조회
        
        Args:
            completed: 완료 여부 필터 (None이면 전체)
            
        Returns:
            할 일 목록
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if completed is None:
            cursor.execute("SELECT * FROM todos ORDER BY created_at DESC")
        else:
            cursor.execute("""
                SELECT * FROM todos 
                WHERE completed = ? 
                ORDER BY created_at DESC
            """, (1 if completed else 0,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_todo(self, todo_id: int, title: str = None, 
                   description: str = None, completed: bool = None) -> bool:
        """
        할 일 수정
        
        Args:
            todo_id: 할 일 ID
            title: 새 제목 (선택적)
            description: 새 설명 (선택적)
            completed: 완료 여부 (선택적)
            
        Returns:
            성공 여부
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if completed is not None:
            updates.append("completed = ?")
            params.append(1 if completed else 0)
        
        if not updates:
            conn.close()
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(todo_id)
        
        cursor.execute(f"""
            UPDATE todos 
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_todo(self, todo_id: int) -> bool:
        """
        할 일 삭제
        
        Args:
            todo_id: 할 일 ID
            
        Returns:
            성공 여부
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success


