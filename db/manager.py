# db/manager.py
from db.connection import DatabaseConnection
from db.settings_repository import SettingsRepository
from db.inventory_repository import InventoryRepository
from config import SCHEMA_PATH, SEED_TEST_PATH

class DatabaseManager(DatabaseConnection):
    def __init__(self, db_path: str):
        super().__init__(db_path)
        self._ensure_schema()
        
        # Подключаем репозитории
        self.settings = SettingsRepository(self)
        self.inventory = InventoryRepository(self)

    def _ensure_schema(self):
        # 1. Применяем основную схему (справочники создаются всегда)
        if SCHEMA_PATH.exists():
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                self.executescript(f.read())
        
        self.execute('INSERT OR IGNORE INTO "sys_Тарифы" ("id") VALUES (1)')

        # 2. Проверяем, есть ли вообще принтеры в базе.
        # Если таблица пуста, значит это первый запуск — заливаем тестовые данные.
        has_printers = self.fetch_scalar('SELECT COUNT(*) FROM "inv_Принтеры"')
        
        if has_printers == 0:
            if SEED_TEST_PATH.exists():
                with open(SEED_TEST_PATH, "r", encoding="utf-8") as f:
                    self.executescript(f.read())
                print("[DB] Загружены тестовые данные (seed_test.sql)")