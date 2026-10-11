# db_manager.py
# Версия: v1.0 (baseline)
import sqlite3
from typing import List, Optional


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")

    def close(self):
        if self.conn:
            self.conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[DB ERROR] {e}\nQuery: {query}\nParams: {params}")
            return []

    def execute_commit(self, query: str, params: tuple = ()) -> bool:
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[DB ERROR] {e}\nQuery: {query}\nParams: {params}")
            self.conn.rollback()
            return False

    # ==================== Виды пластика ====================
    def get_all_plastic_types(self):
        return self.execute_query('SELECT * FROM "Виды пластика" ORDER BY "Название"')

    def get_plastic_type_info(self, plastic_type_id) -> Optional[sqlite3.Row]:
        rows = self.execute_query(
            'SELECT * FROM "Виды пластика" WHERE "id" = ?', (plastic_type_id,)
        )
        return rows[0] if rows else None

    def add_plastic_type(self, name, market_price_per_gram=0.0, notes=""):
        return self.execute_commit(
            'INSERT INTO "Виды пластика" ("Название", "Рыночная стоимость (руб./г)", "Заметки") '
            'VALUES (?, ?, ?)',
            (name, market_price_per_gram, notes),
        )

    def update_plastic_type(self, plastic_type_id, name, market_price_per_gram, notes=""):
        return self.execute_commit(
            'UPDATE "Виды пластика" SET "Название" = ?, "Рыночная стоимость (руб./г)" = ?, '
            '"Заметки" = ? WHERE "id" = ?',
            (name, market_price_per_gram, notes, plastic_type_id),
        )

    def delete_plastic_type(self, plastic_type_id):
        return self.execute_commit(
            'DELETE FROM "Виды пластика" WHERE "id" = ?', (plastic_type_id,)
        )

    # ==================== Тарифы ====================
    def get_electricity_tariff(self) -> float:
        rows = self.execute_query(
            'SELECT "Электричество (руб./кВт)" FROM "Тарифы" LIMIT 1'
        )
        if rows and rows[0][0] is not None:
            return float(rows[0][0])
        return 5.0

    def update_electricity_tariff(self, value: float):
        return self.execute_commit(
            'UPDATE "Тарифы" SET "Электричество (руб./кВт)" = ?', (value,)
        )

    # ==================== Филамент в наличии ====================
    def get_all_spools(self):
        query = '''
            SELECT f.*, v."Название" AS "Вид пластика"
            FROM "Филамент в наличии" f
            JOIN "Виды пластика" v ON f."Вид пластика id" = v."id"
            ORDER BY f."Внутренний ID" DESC
        '''
        return self.execute_query(query)

    def add_spool(self, plastic_type_id, brand, color, cost, weight, stock=None):
        if stock is None:
            stock = weight
        return self.execute_commit(
            '''INSERT INTO "Филамент в наличии"
               ("Вид пластика id", "Марка", "Цвет",
                "Стоимость катушки (RUB)", "Заявленный вес пластика (г)",
                "Приблизительный остаток (г)")
               VALUES (?, ?, ?, ?, ?, ?)''',
            (plastic_type_id, brand, color, cost, weight, stock),
        )

    def update_spool_stock(self, spool_id, new_stock):
        return self.execute_commit(
            'UPDATE "Филамент в наличии" SET "Приблизительный остаток (г)" = ? '
            'WHERE "Внутренний ID" = ?',
            (new_stock, spool_id),
        )

    def delete_spool(self, spool_id):
        return self.execute_commit(
            'DELETE FROM "Филамент в наличии" WHERE "Внутренний ID" = ?',
            (spool_id,),
        )

    def find_spools_by_type_color(self, plastic_type_id, color):
        query = '''
            SELECT * FROM "Филамент в наличии"
            WHERE "Вид пластика id" = ? AND "Цвет" LIKE ?
            ORDER BY "Приблизительный остаток (г)" DESC
        '''
        return self.execute_query(query, (plastic_type_id, f"%{color}%"))

    def get_all_brands(self):
        rows = self.execute_query(
            'SELECT DISTINCT "Марка" FROM "Филамент в наличии" '
            'WHERE "Марка" IS NOT NULL AND "Марка" != \'\' ORDER BY "Марка"'
        )
        return [r[0] for r in rows]

    def get_all_colors(self):
        rows = self.execute_query(
            'SELECT DISTINCT "Цвет" FROM "Филамент в наличии" '
            'WHERE "Цвет" IS NOT NULL AND "Цвет" != \'\' ORDER BY "Цвет"'
        )
        return [r[0] for r in rows]

    # ==================== Поставщики ====================
    def find_supplier_prices(self, plastic_type_id, color):
        query = '''
            SELECT * FROM "Цены на филамент у поставщиков (OZON)"
            WHERE "Вид пластика id" = ? AND "Цвет" LIKE ?
            ORDER BY "Цена" ASC
        '''
        return self.execute_query(query, (plastic_type_id, f"%{color}%"))

    def add_supplier_price(self, plastic_type_id, brand, color, weight, price, link=""):
        return self.execute_commit(
            '''INSERT INTO "Цены на филамент у поставщиков (OZON)"
               ("Вид пластика id", "Марка", "Цвет", "Вес катушки", "Цена", "Ссылка")
               VALUES (?, ?, ?, ?, ?, ?)''',
            (plastic_type_id, brand, color, weight, price, link),
        )

    # ==================== Проекты ====================
    def get_all_projects(self):
        return self.execute_query('SELECT * FROM "Проекты" ORDER BY "id" DESC')

    def get_project(self, project_id) -> Optional[sqlite3.Row]:
        rows = self.execute_query('SELECT * FROM "Проекты" WHERE "id" = ?', (project_id,))
        return rows[0] if rows else None

    def add_project(self, name, customer="", status="В работе", price=None):
        return self.execute_commit(
            'INSERT INTO "Проекты" ("Название", "Заказчик", "Статус", "Цена") VALUES (?, ?, ?, ?)',
            (name, customer, status, price),
        )

    def update_project_price(self, project_id, price):
        return self.execute_commit(
            'UPDATE "Проекты" SET "Цена" = ? WHERE "id" = ?', (price, project_id)
        )

    # ==================== Расход катушек ====================
    def add_consumption(self, spool_id, project_id, grams, actual_grams=None, result="Успех"):
        spool = self.execute_query(
            'SELECT "Приблизительный остаток (г)" FROM "Филамент в наличии" '
            'WHERE "Внутренний ID" = ?',
            (spool_id,),
        )
        if spool:
            current = spool[0][0] or 0
            used = actual_grams if actual_grams is not None else grams
            new_stock = max(0, current - used)
            self.update_spool_stock(spool_id, new_stock)

        return self.execute_commit(
            '''INSERT INTO "Расход катушек"
               ("id катушки", "id проекта", "Количество (г)", "Фактический расход (г)", "Результат")
               VALUES (?, ?, ?, ?, ?)''',
            (spool_id, project_id, grams, actual_grams, result),
        )

    def get_project_history(self, project_id):
        query = '''
            SELECT r.*, f."Марка", f."Цвет", v."Название" AS "Вид пластика"
            FROM "Расход катушек" r
            JOIN "Филамент в наличии" f ON r."id катушки" = f."Внутренний ID"
            JOIN "Виды пластика" v ON f."Вид пластика id" = v."id"
            WHERE r."id проекта" = ?
            ORDER BY r."Дата события" DESC
        '''
        return self.execute_query(query, (project_id,))