# db/manager.py
from db.connection import DatabaseConnection
from db.settings_repository import SettingsRepository
from config import SCHEMA_PATH

class DatabaseManager(DatabaseConnection):
    def __init__(self, db_path: str):
        super().__init__(db_path)
        self._ensure_schema()
        
        # Тот самый дочерний класс для редактирования
        self.settings = SettingsRepository(self)

# db/manager.py (фрагмент)
    def _ensure_schema(self):
        if SCHEMA_PATH.exists():
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                sql = f.read()
            self.executescript(sql)
            
        # Обеспечиваем наличие строки тарифов
        self.execute('INSERT OR IGNORE INTO "sys_Тарифы" ("id") VALUES (1)')