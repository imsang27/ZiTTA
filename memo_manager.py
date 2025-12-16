"""
메모 관리 모듈
SQLite를 사용하여 메모를 저장하고 관리합니다.
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
from config import Config

class MemoManager:
    """메모 관리자"""
    
    def __init__(self):
        """메모 관리자 초기화 및 데이터베이스 설정"""
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
            CREATE TABLE IF NOT EXISTS memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                tags TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_memo(self, title: str, content: str = "", tags: str = "") -> int:
        """
        메모 추가
        
        Args:
            title: 메모 제목
            content: 메모 내용
            tags: 태그 (쉼표로 구분)
            
        Returns:
            생성된 메모의 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO memos (title, content, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (title, content, tags, now, now))
        
        memo_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return memo_id
    
    def get_memos(self, tag: Optional[str] = None, search_query: Optional[str] = None) -> List[Dict]:
        """
        메모 목록 조회
        
        Args:
            tag: 태그 필터 (선택적)
            search_query: 검색 쿼리 (제목/내용 검색, 선택적)
            
        Returns:
            메모 목록
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM memos WHERE 1=1"
        params = []
        
        if tag:
            query += " AND tags LIKE ?"
            params.append(f"%{tag}%")
        
        if search_query:
            query += " AND (title LIKE ? OR content LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        
        query += " ORDER BY updated_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_memo(self, memo_id: int) -> Optional[Dict]:
        """
        특정 메모 조회
        
        Args:
            memo_id: 메모 ID
            
        Returns:
            메모 딕셔너리 또는 None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM memos WHERE id = ?", (memo_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def update_memo(self, memo_id: int, title: str = None, 
                   content: str = None, tags: str = None) -> bool:
        """
        메모 수정
        
        Args:
            memo_id: 메모 ID
            title: 새 제목 (선택적)
            content: 새 내용 (선택적)
            tags: 새 태그 (선택적)
            
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
        
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        
        if tags is not None:
            updates.append("tags = ?")
            params.append(tags)
        
        if not updates:
            conn.close()
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(memo_id)
        
        cursor.execute(f"""
            UPDATE memos 
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_memo(self, memo_id: int) -> bool:
        """
        메모 삭제
        
        Args:
            memo_id: 메모 ID
            
        Returns:
            성공 여부
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM memos WHERE id = ?", (memo_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success

