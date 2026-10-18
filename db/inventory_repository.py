# db/inventory_repository.py
from typing import List
from db.connection import DatabaseConnection

class InventoryRepository:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    # ==================== ПРИНТЕРЫ ====================
    def get_all_printers(self) -> List:
        return self.db.fetch_all('SELECT * FROM "inv_Принтеры" ORDER BY "Название"')

    def add_printer(self, name: str, group_id: int, cost: float, resource: float) -> bool:
        return self.db.execute(
            'INSERT INTO "inv_Принтеры" ("Название", "Группа по соплу", "Стоимость (руб)", "Ресурс (ч)") VALUES (?, ?, ?, ?)',
            (name.strip(), group_id, cost, resource)
        )

    def update_printer(self, p_id: int, name: str, group_id: int, cost: float, resource: float) -> bool:
        return self.db.execute(
            'UPDATE "inv_Принтеры" SET "Название"=?, "Группа по соплу"=?, "Стоимость (руб)"=?, "Ресурс (ч)"=? WHERE "id"=?',
            (name.strip(), group_id, cost, resource, p_id)
        )

    def delete_printer(self, p_id: int) -> bool:
        return self.db.execute('DELETE FROM "inv_Принтеры" WHERE "id"=?', (p_id,))

    # ==================== СОПЛА ====================
    def get_all_nozzles(self) -> List:
        return self.db.fetch_all('''
            SELECT n.*, t."Название" AS "Тип" 
            FROM "inv_Сопла" n
            JOIN "sys_Типы сопел" t ON n."id Типа сопла" = t."id"
            ORDER BY t."Название", n."Диаметр (мм)"
        ''')

    def add_nozzle(self, type_id: int, diameter: float, resource: float) -> bool:
        return self.db.execute(
            'INSERT INTO "inv_Сопла" ("id Типа сопла", "Диаметр (мм)", "Ресурс (г)") VALUES (?, ?, ?)',
            (type_id, diameter, resource)
        )

    def update_nozzle(self, n_id: int, type_id: int, diameter: float, resource: float) -> bool:
        return self.db.execute(
            'UPDATE "inv_Сопла" SET "id Типа сопла"=?, "Диаметр (мм)"=?, "Ресурс (г)"=? WHERE "id"=?',
            (type_id, diameter, resource, n_id)
        )

    def delete_nozzle(self, n_id: int) -> bool:
        return self.db.execute('DELETE FROM "inv_Сопла" WHERE "id"=?', (n_id,))

    # ==================== КАТУШКИ ПЛАСТИКА ====================
    def get_all_spools(self) -> List:
        # Сложный запрос: считаем остаток с учетом расхода, списания при сварке и пополнения при сварке
        return self.db.fetch_all('''
            SELECT k.*, 
                   v."Основа" || ' ' || v."Модификатор" AS "Материал",
                   c."Название" AS "Цвет",
                   c."HEX" AS "HEX Цвета",
                   (k."Вес Нетто (г)" 
                    + COALESCE(SUM(CASE WHEN r."Тип действия" = 'Сварка (пополнение)' THEN r."Количество (г)" ELSE 0 END), 0)
                    - COALESCE(SUM(CASE WHEN r."Тип действия" != 'Сварка (пополнение)' THEN r."Количество (г)" ELSE 0 END), 0)
                   ) AS "Остаток (г)"
            FROM "inv_Катушки пластика" k
            JOIN "sys_Виды пластика" v ON k."id Материала" = v."id"
            JOIN "sys_Цвета" c ON k."id Цвета" = c."id"
            LEFT JOIN "biz_Расход пластика" r ON k."id" = r."id Катушки"
            GROUP BY k."id"
            ORDER BY k."Статус", v."Основа", v."Модификатор", c."Группа", c."Порядок"
        ''')

    def add_spool(self, material_id: int, color_id: int, cost: float, weight: float) -> bool:
        return self.db.execute(
            'INSERT INTO "inv_Катушки пластика" ("id Материала", "id Цвета", "Стоимость покупки (руб)", "Вес Нетто (г)") VALUES (?, ?, ?, ?)',
            (material_id, color_id, cost, weight)
        )

    def update_spool(self, s_id: int, material_id: int, color_id: int, cost: float, weight: float) -> bool:
        return self.db.execute(
            'UPDATE "inv_Катушки пластика" SET "id Материала"=?, "id Цвета"=?, "Стоимость покупки (руб)"=?, "Вес Нетто (г)"=? WHERE "id"=?',
            (material_id, color_id, cost, weight, s_id)
        )

    def update_spool_status(self, s_id: int, status: str) -> bool:
        return self.db.execute('UPDATE "inv_Катушки пластика" SET "Статус"=? WHERE "id"=?', (status, s_id))

    def delete_spool(self, s_id: int) -> bool:
        # Удаление катушки автоматически удалит и её историю расходов благодаря ON DELETE CASCADE
        return self.db.execute('DELETE FROM "inv_Катушки пластика" WHERE "id"=?', (s_id,))

    # ==================== РАСХОД ПЛАСТИКА ====================
    def add_consumption(self, spool_id: int, grams: float) -> bool:
        return self.db.execute(
            'INSERT INTO "biz_Расход пластика" ("id Катушки", "Количество (г)", "Тип действия") VALUES (?, ?, ?)',
            (spool_id, grams, 'Расход')
        )

    def get_spool_history(self, spool_id: int) -> List:
        return self.db.fetch_all(
            'SELECT * FROM "biz_Расход пластика" WHERE "id Катушки"=? ORDER BY "Дата события" DESC',
            (spool_id,)
        )

    def weld_spools(self, source_id: int, target_id: int) -> bool:
        """Атомарно сваривает две катушки: перекидывает остаток с source на target и пишет историю."""
        # 1. Вычисляем текущий остаток исходной катушки
        source = self.db.fetch_one('''
            SELECT k."Вес Нетто (г)", 
                   COALESCE(SUM(CASE WHEN r."Тип действия" = 'Сварка (пополнение)' THEN r."Количество (г)" ELSE 0 END), 0) as added,
                   COALESCE(SUM(CASE WHEN r."Тип действия" != 'Сварка (пополнение)' THEN r."Количество (г)" ELSE 0 END), 0) as used
            FROM "inv_Катушки пластика" k
            LEFT JOIN "biz_Расход пластика" r ON k.id = r."id Катушки"
            WHERE k.id = ? GROUP BY k.id
        ''', (source_id,))
        
        if not source: return False
        
        remainder = source["Вес Нетто (г)"] + source["added"] - source["used"]
        
        if remainder <= 0:
            return False # Нечего варить

        try:
            # 1. Списываем остаток с исходной катушки (записываем в историю)
            self.db.cursor.execute(
                'INSERT INTO "biz_Расход пластика" ("id Катушки", "Количество (г)", "Тип действия") VALUES (?, ?, ?)',
                (source_id, remainder, 'Сварка (списание)')
            )
            # 2. Записываем в историю целевой катушки, что ей "пришло" пополнение
            self.db.cursor.execute(
                'INSERT INTO "biz_Расход пластика" ("id Катушки", "Количество (г)", "Тип действия") VALUES (?, ?, ?)',
                (target_id, remainder, 'Сварка (пополнение)')
            )
            # 3. Меняем статус исходной
            self.db.cursor.execute(
                'UPDATE "inv_Катушки пластика" SET "Статус" = ? WHERE "id" = ?',
                ('Приварена', source_id)
            )
            self.db.conn.commit()
            return True
        except Exception as e:
            self.db.conn.rollback()
            print(f"[DB ERROR] Ошибка сварки: {e}")
            return False