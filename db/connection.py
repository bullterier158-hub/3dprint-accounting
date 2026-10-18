# db/connection.py
import sqlite3
from typing import List, Optional, Any

class DatabaseConnection:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.connect()

    def connect(self) -> None:
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        # Важно: включаем поддержку внешних ключей и WAL-режим
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self.cursor.execute("PRAGMA journal_mode = WAL;")
        self.cursor.execute("PRAGMA synchronous = NORMAL;")

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[DB ERROR] {e}\nQuery: {query}\nParams: {params}")
            return []

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        rows = self.fetch_all(query, params)
        return rows[0] if rows else None

    def fetch_scalar(self, query: str, params: tuple = (), default: Any = None) -> Any:
        row = self.fetch_one(query, params)
        if row is None or row[0] is None:
            return default
        return row[0]

    def execute(self, query: str, params: tuple = ()) -> bool:
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[DB ERROR] {e}\nQuery: {query}\nParams: {params}")
            self.conn.rollback()
            return False

    def executescript(self, script: str) -> bool:
        try:
            self.cursor.executescript(script)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[DB ERROR] Script error: {e}")
            self.conn.rollback()
            return False