# db/settings_repository.py
from typing import List, Optional
from db.connection import DatabaseConnection

class SettingsRepository:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    # ==================== ВИДЫ ПЛАСТИКА ====================
    def get_all_plastics(self) -> List:
        return self.db.fetch_all('SELECT * FROM "sys_Виды пластика" ORDER BY "Основа", "Модификатор"')

    def add_plastic(self, base: str, mod: str, coeff: float, notes: str) -> bool:
        return self.db.execute(
            'INSERT INTO "sys_Виды пластика" ("Основа", "Модификатор", "Коэф. трудности", "Примечание") VALUES (?, ?, ?, ?)',
            (base.strip(), mod.strip(), coeff, notes)
        )

    def update_plastic(self, p_id: int, base: str, mod: str, coeff: float, notes: str) -> bool:
        return self.db.execute(
            'UPDATE "sys_Виды пластика" SET "Основа"=?, "Модификатор"=?, "Коэф. трудности"=?, "Примечание"=? WHERE "id"=?',
            (base.strip(), mod.strip(), coeff, notes, p_id)
        )

    def delete_plastic(self, p_id: int) -> bool:
        return self.db.execute('DELETE FROM "sys_Виды пластика" WHERE "id"=?', (p_id,))

    # ==================== ТИПЫ СОПЕЛ ====================
    def get_all_nozzle_types(self) -> List:
        return self.db.fetch_all('SELECT * FROM "sys_Типы сопел" ORDER BY "Название"')

    def add_nozzle_type(self, name: str, resource: float, notes: str) -> bool:
        return self.db.execute(
            'INSERT INTO "sys_Типы сопел" ("Название", "Ожидаемый ресурс (г)", "Примечание") VALUES (?, ?, ?)',
            (name.strip(), resource, notes)
        )

    def update_nozzle_type(self, n_id: int, name: str, resource: float, notes: str) -> bool:
        return self.db.execute(
            'UPDATE "sys_Типы сопел" SET "Название"=?, "Ожидаемый ресурс (г)"=?, "Примечание"=? WHERE "id"=?',
            (name.strip(), resource, notes, n_id)
        )

    def delete_nozzle_type(self, n_id: int) -> bool:
        return self.db.execute('DELETE FROM "sys_Типы сопел" WHERE "id"=?', (n_id,))

    # ==================== ТАРИФЫ И НАЛОГИ ====================
    def get_tariffs(self):
        return self.db.fetch_one('''
            SELECT t.*, n."Название" AS "tax_name" 
            FROM "sys_Тарифы" t
            LEFT JOIN "sys_Налоговые режимы" n ON t."Налоговый режим id" = n."id"
            WHERE t."id"=1
        ''')

    def get_all_tax_regimes(self):
        return self.db.fetch_all('SELECT * FROM "sys_Налоговые режимы" ORDER BY "id"')

    def update_tariffs(self, t_type: str, day_price: float, night_price: Optional[float], defect: float, tax_id: int) -> bool:
        if t_type == "фикс":
            night_price = None
        return self.db.execute('''
            UPDATE "sys_Тарифы" SET 
                "Тип тарифа на электричество"=?, "Цена 1кВт (руб)"=?, "Цена 1кВт ночь (руб)"=?, 
                "% Брака"=?, "Налоговый режим id"=?
            WHERE "id"=1
        ''', (t_type, day_price, night_price, defect, tax_id))

    # ==================== КОЭФФИЦИЕНТЫ ИЗНОСА ====================
    def get_wear_matrix(self):
        return self.db.fetch_all('''
            SELECT v."id" AS p_id, v."Основа" AS p_base, v."Модификатор" AS p_mod,
                   t."id" AS n_id, t."Название" AS n_name,
                   COALESCE(c."Коэффициент", 1.0) AS coeff
            FROM "sys_Виды пластика" v
            CROSS JOIN "sys_Типы сопел" t
            LEFT JOIN "sys_Коэффициенты износа сопла от вида пластика" c
                   ON c."id Пластика" = v."id" AND c."id Сопла" = t."id"
            ORDER BY v."Основа", v."Модификатор", t."Название"
        ''')

    def set_wear_coefficient(self, p_id: int, n_id: int, coeff: float) -> bool:
        return self.db.execute('''
            INSERT INTO "sys_Коэффициенты износа сопла от вида пластика" ("id Пластика", "id Сопла", "Коэффициент")
            VALUES (?, ?, ?)
            ON CONFLICT("id Пластика", "id Сопла") DO UPDATE SET "Коэффициент"=excluded."Коэффициент"
        ''', (p_id, n_id, coeff))

    # ==================== ЦВЕТА ====================
    def get_all_colors(self):
        return self.db.fetch_all('''
            SELECT * FROM "sys_Цвета" 
            ORDER BY "Группа", "Порядок", "Название"
        ''')

    def add_color(self, name: str, group: str, order: int, hex_code: str, notes: str) -> bool:
        return self.db.execute(
            'INSERT INTO "sys_Цвета" ("Название", "Группа", "Порядок", "HEX", "Примечание") VALUES (?, ?, ?, ?, ?)',
            (name.strip(), group, order, hex_code.strip(), notes)
        )

    def update_color(self, c_id: int, name: str, group: str, order: int, hex_code: str, notes: str) -> bool:
        return self.db.execute(
            'UPDATE "sys_Цвета" SET "Название"=?, "Группа"=?, "Порядок"=?, "HEX"=?, "Примечание"=? WHERE "id"=?',
            (name.strip(), group, order, hex_code.strip(), notes, c_id)
        )

    def delete_color(self, c_id: int) -> bool:
        return self.db.execute('DELETE FROM "sys_Цвета" WHERE "id"=?', (c_id,))