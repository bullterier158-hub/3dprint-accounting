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
    
        # ==================== Типы сопел ====================
    def get_all_nozzle_types(self):
        return self.execute_query(
            'SELECT * FROM "Типы сопел" ORDER BY "Название"'
        )

    def get_nozzle_type_info(self, type_id):
        rows = self.execute_query(
            'SELECT * FROM "Типы сопел" WHERE "id" = ?', (type_id,)
        )
        return rows[0] if rows else None

    def add_nozzle_type(self, name, material, diameter, resource,
                        coeff_pla=1.0, coeff_pla_plus=1.0,
                        coeff_pla_cf=5.0, coeff_pla_gf=5.0,
                        coeff_petg=1.0, coeff_petg_plus=1.0,
                        coeff_petg_cf=5.0, coeff_petg_gf=5.0,
                        coeff_abs=1.2, coeff_abs_cf=6.0, coeff_abs_gf=6.0,
                        coeff_asa=1.3, coeff_asa_cf=6.0,
                        coeff_tpu_95a=0.8, coeff_tpu_98a=0.8,
                        coeff_tpu_85a=0.7, coeff_tpu_75d=0.9,
                        notes=""):
        return self.execute_commit(
            '''INSERT INTO "Типы сопел"
               ("Название", "Материал", "Диаметр (мм)", "Ресурс (г)",
                "Коэф. износа PLA", "Коэф. износа PLA+",
                "Коэф. износа PLA-CF", "Коэф. износа PLA-GF",
                "Коэф. износа PETG", "Коэф. износа PETG+",
                "Коэф. износа PETG-CF", "Коэф. износа PETG-GF",
                "Коэф. износа ABS", "Коэф. износа ABS-CF", "Коэф. износа ABS-GF",
                "Коэф. износа ASA", "Коэф. износа ASA-CF",
                "Коэф. износа TPU 95A", "Коэф. износа TPU 98A",
                "Коэф. износа TPU 85A", "Коэф. износа TPU 75D",
                "Заметки")
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                       ?, ?, ?, ?, ?)''',
            (name, material, diameter, resource,
             coeff_pla, coeff_pla_plus, coeff_pla_cf, coeff_pla_gf,
             coeff_petg, coeff_petg_plus, coeff_petg_cf, coeff_petg_gf,
             coeff_abs, coeff_abs_cf, coeff_abs_gf,
             coeff_asa, coeff_asa_cf,
             coeff_tpu_95a, coeff_tpu_98a, coeff_tpu_85a, coeff_tpu_75d,
             notes)
        )

    def update_nozzle_type(self, type_id, name, material, diameter, resource,
                           coeff_pla, coeff_pla_plus, coeff_pla_cf, coeff_pla_gf,
                           coeff_petg, coeff_petg_plus, coeff_petg_cf, coeff_petg_gf,
                           coeff_abs, coeff_abs_cf, coeff_abs_gf,
                           coeff_asa, coeff_asa_cf,
                           coeff_tpu_95a, coeff_tpu_98a, coeff_tpu_85a, coeff_tpu_75d,
                           notes=""):
        return self.execute_commit(
            '''UPDATE "Типы сопел" SET
               "Название" = ?, "Материал" = ?, "Диаметр (мм)" = ?, "Ресурс (г)" = ?,
               "Коэф. износа PLA" = ?, "Коэф. износа PLA+" = ?,
               "Коэф. износа PLA-CF" = ?, "Коэф. износа PLA-GF" = ?,
               "Коэф. износа PETG" = ?, "Коэф. износа PETG+" = ?,
               "Коэф. износа PETG-CF" = ?, "Коэф. износа PETG-GF" = ?,
               "Коэф. износа ABS" = ?, "Коэф. износа ABS-CF" = ?,
               "Коэф. износа ABS-GF" = ?,
               "Коэф. износа ASA" = ?, "Коэф. износа ASA-CF" = ?,
               "Коэф. износа TPU 95A" = ?, "Коэф. износа TPU 98A" = ?,
               "Коэф. износа TPU 85A" = ?, "Коэф. износа TPU 75D" = ?,
               "Заметки" = ?
               WHERE "id" = ?''',
            (name, material, diameter, resource,
             coeff_pla, coeff_pla_plus, coeff_pla_cf, coeff_pla_gf,
             coeff_petg, coeff_petg_plus, coeff_petg_cf, coeff_petg_gf,
             coeff_abs, coeff_abs_cf, coeff_abs_gf,
             coeff_asa, coeff_asa_cf,
             coeff_tpu_95a, coeff_tpu_98a, coeff_tpu_85a, coeff_tpu_75d,
             notes, type_id)
        )

    def delete_nozzle_type(self, type_id):
        return self.execute_commit(
            'DELETE FROM "Типы сопел" WHERE "id" = ?', (type_id,)
        )

    def get_wear_coefficient(self, nozzle_type_id, plastic_type_id):
        """Возвращает коэффициент износа для пары (тип сопла, вид пластика).
        Если для данного вида пластика нет колонки — возвращает 1.0."""
        nozzle_type = self.get_nozzle_type_info(nozzle_type_id)
        plastic = self.get_plastic_type_info(plastic_type_id)
        if not nozzle_type or not plastic:
            return 1.0

        plastic_name = plastic["Название"]
        # Ищем колонку "Коэф. износа <Название пластика>"
        col_name = f"Коэф. износа {plastic_name}"

        # Проверяем, есть ли такая колонка в схеме
        cols = self.execute_query('PRAGMA table_info("Типы сопел")')
        col_names = [c["name"] for c in cols]
        if col_name not in col_names:
            return 1.0
        return float(nozzle_type[col_name] or 1.0)

    # ==================== Сопла ====================
    def get_all_nozzles(self):
        """Возвращает все сопла с расшифровкой типа, ресурса и остатка."""
        query = '''
            SELECT n.*,
                   t."Название" AS "Тип",
                   t."Материал" AS "Материал",
                   t."Диаметр (мм)" AS "Диаметр",
                   t."Ресурс (г)" AS "Ресурс",
                   (t."Ресурс (г)" - n."Наработка (г)") AS "Остаток"
            FROM "Сопла" n
            JOIN "Типы сопел" t ON n."Тип сопла id" = t."id"
            ORDER BY "Остаток" ASC
        '''
        return self.execute_query(query)

    def get_nozzle_info(self, nozzle_id):
        query = '''
            SELECT n.*,
                   t."Название" AS "Тип",
                   t."Материал" AS "Материал",
                   t."Диаметр (мм)" AS "Диаметр",
                   t."Ресурс (г)" AS "Ресурс",
                   (t."Ресурс (г)" - n."Наработка (г)") AS "Остаток"
            FROM "Сопла" n
            JOIN "Типы сопел" t ON n."Тип сопла id" = t."id"
            WHERE n."id" = ?
        '''
        rows = self.execute_query(query, (nozzle_id,))
        return rows[0] if rows else None

    def add_nozzle(self, type_id, serial, cost, purchase_date=None, notes=""):
        return self.execute_commit(
            '''INSERT INTO "Сопла"
               ("Тип сопла id", "Серийный номер", "Стоимость (руб)",
                "Дата покупки", "Заметки")
               VALUES (?, ?, ?, ?, ?)''',
            (type_id, serial, cost, purchase_date, notes)
        )

    def update_nozzle(self, nozzle_id, type_id, serial, cost,
                      status, notes=""):
        return self.execute_commit(
            '''UPDATE "Сопла" SET
               "Тип сопла id" = ?, "Серийный номер" = ?,
               "Стоимость (руб)" = ?, "Статус" = ?, "Заметки" = ?
               WHERE "id" = ?''',
            (type_id, serial, cost, status, notes, nozzle_id)
        )

    def delete_nozzle(self, nozzle_id):
        return self.execute_commit(
            'DELETE FROM "Сопла" WHERE "id" = ?', (nozzle_id,)
        )

    def add_nozzle_wear(self, nozzle_id, plastic_type_id, grams):
        """Увеличивает наработку сопла на эффективную нагрузку (г × коэф.)."""
        nozzle = self.get_nozzle_info(nozzle_id)
        if not nozzle:
            return False
        coeff = self.get_wear_coefficient(nozzle["Тип сопла id"], plastic_type_id)
        effective = grams * coeff
        new_wear = (nozzle["Наработка (г)"] or 0) + effective
        return self.execute_commit(
            'UPDATE "Сопла" SET "Наработка (г)" = ? WHERE "id" = ?',
            (new_wear, nozzle_id)
        )

    def find_nozzle_for_print(self, plastic_type_id, grams_required):
        """Ищет сопло с минимальным остатком ресурса, которого хватит на печать.
        Возвращает (nozzle_row, effective_load) или (None, effective_load)."""
        coeff = self.get_wear_coefficient_from_plastic(plastic_type_id)
        effective_load = grams_required * coeff

        # Все сопла в статусе "В работе", отсортированы по остатку возрастанию
        query = '''
            SELECT n.*,
                   t."Ресурс (г)" - n."Наработка (г)" AS "Остаток",
                   t."Название" AS "Тип",
                   t."Ресурс (г)" AS "Ресурс"
            FROM "Сопла" n
            JOIN "Типы сопел" t ON n."Тип сопла id" = t."id"
            WHERE n."Статус" = 'В работе'
            ORDER BY "Остаток" ASC
        '''
        nozzles = self.execute_query(query)
        for n in nozzles:
            if n["Остаток"] >= effective_load:
                return n, effective_load
        return None, effective_load

    def get_wear_coefficient_from_plastic(self, plastic_type_id):
        """Возвращает коэффициент износа, используя первое сопло 'В работе'.
        Используется для предварительной оценки нагрузки."""
        nozzles = self.execute_query(
            '''SELECT "Тип сопла id" FROM "Сопла"
               WHERE "Статус" = 'В работе' LIMIT 1'''
        )
        if not nozzles:
            return 1.0
        return self.get_wear_coefficient(nozzles[0]["Тип сопла id"], plastic_type_id)

    def calculate_nozzle_cost(self, nozzle_id, plastic_type_id, grams):
        """Амортизация сопла на конкретную печать."""
        nozzle = self.get_nozzle_info(nozzle_id)
        if not nozzle:
            return 0.0
        resource = nozzle["Ресурс"] or 0
        if resource <= 0:
            return 0.0
        coeff = self.get_wear_coefficient(nozzle["Тип сопла id"], plastic_type_id)
        cost = float(nozzle["Стоимость (руб)"] or 0)
        return (grams * coeff / resource) * cost

    # ==================== Параметры принтера ====================
    def get_printer_cost(self):
        rows = self.execute_query(
            'SELECT "Стоимость принтера (руб)" FROM "Тарифы" LIMIT 1'
        )
        if rows and rows[0][0] is not None:
            return float(rows[0][0])
        return 0.0

    def get_printer_hours_to_overhaul(self):
        rows = self.execute_query(
            'SELECT "Часы до кап. ремонта" FROM "Тарифы" LIMIT 1'
        )
        if rows and rows[0][0] is not None:
            return float(rows[0][0])
        return 5000.0

    def update_printer_params(self, cost, hours):
        return self.execute_commit(
            'UPDATE "Тарифы" SET "Стоимость принтера (руб)" = ?, '
            '"Часы до кап. ремонта" = ?',
            (cost, hours)
        )