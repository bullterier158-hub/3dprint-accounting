-- ==============================================================================
-- БАЗА ДАННЫХ: Учёт 3D-печати (v3.0)
-- ==============================================================================

-- ==============================================================================
-- БЛОК 1: КОНСТАНТЫ И ГЛОБАЛЬНЫЕ НАСТРОЙКИ (sys_)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS "sys_Виды пластика" (
	"id"	INTEGER,
	"Основа"	TEXT NOT NULL,
	"Модификатор"	TEXT NOT NULL DEFAULT '',
	"Коэф. трудности"	REAL NOT NULL DEFAULT 1.0 CHECK("Коэф. трудности" >= 0),
	"Примечание"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT),
	UNIQUE("Основа","Модификатор")
);

CREATE TABLE IF NOT EXISTS "sys_Типы сопел" (
	"id"	INTEGER,
	"Название"	TEXT NOT NULL,
	"Ожидаемый ресурс (г)"	REAL CHECK("Ожидаемый ресурс (г)" IS NULL OR "Ожидаемый ресурс (г)" > 0),
	"Примечание"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT),
	UNIQUE("Название")
);

CREATE TABLE IF NOT EXISTS "sys_Коэффициенты износа сопла от вида пластика" (
	"id Пластика"	INTEGER NOT NULL,
	"id Сопла"	INTEGER NOT NULL,
	"Коэффициент"	REAL NOT NULL DEFAULT 1.0 CHECK("Коэффициент" >= 0),
	PRIMARY KEY("id Пластика","id Сопла"),
	FOREIGN KEY("id Пластика") REFERENCES "sys_Виды пластика"("id") ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY("id Сопла") REFERENCES "sys_Типы сопел"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS "sys_Налоговые режимы" (
	"id"	INTEGER,
	"Название"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "sys_Тарифы" (
	"id"	INTEGER DEFAULT 1 CHECK("id" = 1),
	"Тип тарифа на электричество"	TEXT NOT NULL DEFAULT 'фикс' CHECK("Тип тарифа на электричество" IN ('фикс', 'день/ночь')),
	"Цена 1кВт (руб)"	REAL NOT NULL DEFAULT 5.0 CHECK("Цена 1кВт (руб)" >= 0),
	"Цена 1кВт ночь (руб)"	REAL CHECK("Цена 1кВт ночь (руб)" IS NULL OR "Цена 1кВт ночь (руб)" >= 0),
	"% Брака"	REAL NOT NULL DEFAULT 10.0 CHECK("% Брака" >= 0 AND "% Брака" <= 100),
	"Налоговый режим id"	INTEGER,
	PRIMARY KEY("id"),
	FOREIGN KEY("Налоговый режим id") REFERENCES "sys_Налоговые режимы"("id"),
	CHECK(("Тип тарифа на электричество" = 'фикс' AND "Цена 1кВт ночь (руб)" IS NULL) OR ("Тип тарифа на электричество" = 'день/ночь' AND "Цена 1кВт ночь (руб)" IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS "sys_Цвета" (
	"id"	INTEGER,
	"Название"	TEXT NOT NULL UNIQUE,
	"Группа"	TEXT NOT NULL DEFAULT 'Прочее' CHECK("Группа" IN ('Ахроматические', 'Тёплые', 'Холодные', 'Прозрачные', 'Особые', 'Прочее')),
	"Порядок"	INTEGER NOT NULL DEFAULT 100,
	"HEX"	TEXT,
	"Примечание"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);

-- ==============================================================================
-- БЛОК 2: ФИЗИЧЕСКОЕ ИМУЩЕСТВО (inv_)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS "inv_Принтеры" (
	"id"	INTEGER,
	"Название"	TEXT NOT NULL,
	"Группа по соплу"	INTEGER DEFAULT 1,
	"Стоимость (руб)"	REAL NOT NULL DEFAULT 0.0 CHECK("Стоимость (руб)" >= 0),
	"Ресурс (ч)"	REAL NOT NULL DEFAULT 0.0 CHECK("Ресурс (ч)" >= 0), -- ИЗМЕНЕНО: теперь в часах
	"Примечание"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "inv_Сопла" (
	"id"	INTEGER,
	"id Типа сопла"	INTEGER NOT NULL,
	"Группа по соплу"	INTEGER DEFAULT 1, -- НОВОЕ ПОЛЕ
	"Диаметр (мм)"	REAL NOT NULL DEFAULT 0.4 CHECK("Диаметр (мм)" > 0),
	"Ресурс (г)"	REAL NOT NULL DEFAULT 0.0 CHECK("Ресурс (г)" >= 0), 
	"Название"	TEXT, -- НОВОЕ ПОЛЕ
	"Примечание"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("id Типа сопла") REFERENCES "sys_Типы сопел"("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS "inv_Катушки пластика" (
	"id"	INTEGER,
	"id Материала"	INTEGER NOT NULL,
	"id Цвета"	INTEGER NOT NULL,
	"Стоимость покупки (руб)"	REAL NOT NULL DEFAULT 0.0 CHECK("Стоимость покупки (руб)" >= 0),
	"Вес Нетто (г)"	REAL NOT NULL CHECK("Вес Нетто (г)" > 0),
	"Статус"	TEXT NOT NULL DEFAULT 'Активна' CHECK("Статус" IN ('Активна', 'Закончилась', 'Выброшена', 'Приварена')),
	"Примечание"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("id Материала") REFERENCES "sys_Виды пластика"("id") ON DELETE RESTRICT ON UPDATE CASCADE,
	FOREIGN KEY("id Цвета") REFERENCES "sys_Цвета"("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ==============================================================================
-- БЛОК 3: ДЕЯТЕЛЬНОСТЬ (biz_)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS "biz_Расход пластика" (
	"id"	INTEGER,
	"id Катушки"	INTEGER NOT NULL,
	"Количество (г)"	REAL NOT NULL CHECK("Количество (г)" > 0),
	"Тип действия"	TEXT NOT NULL DEFAULT 'Расход' CHECK("Тип действия" IN ('Расход', 'Сварка (списание)', 'Сварка (пополнение)')),
	"Дата события"	TEXT DEFAULT (datetime('now', 'localtime')),
	"Примечание"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("id Катушки") REFERENCES "inv_Катушки пластика"("id") ON DELETE CASCADE
);

-- ==============================================================================
-- ИНДЕКСЫ
-- ==============================================================================
CREATE INDEX IF NOT EXISTS "idx_sys_coeff_nozzle" ON "sys_Коэффициенты износа сопла от вида пластика" ("id Сопла");
CREATE INDEX IF NOT EXISTS "idx_sys_plastic_base" ON "sys_Виды пластика" ("Основа");

CREATE INDEX IF NOT EXISTS "idx_inv_printer_group" ON "inv_Принтеры" ("Группа по соплу");
CREATE INDEX IF NOT EXISTS "idx_inv_nozzle_type" ON "inv_Сопла" ("id Типа сопла");
CREATE INDEX IF NOT EXISTS "idx_inv_spool_material" ON "inv_Катушки пластика" ("id Материала");

CREATE INDEX IF NOT EXISTS "idx_biz_consumption_spool" ON "biz_Расход пластика" ("id Катушки");

-- ==============================================================================
-- НАЧАЛЬНЫЕ ДАННЫЕ (SEED DATA)
-- ==============================================================================

-- 1. Налоговые режимы
INSERT OR IGNORE INTO "sys_Налоговые режимы" ("id", "Название") VALUES 
(1, 'Не учитывается (0%)'),
(2, 'Самозанятость (4% / 6%)'),
(3, 'УСН Доход (6%)'),
(4, 'УСН Доход-Расход (15%)');

-- 2. Тарифы (строка id=1)
INSERT OR IGNORE INTO "sys_Тарифы" ("id", "Налоговый режим id") VALUES (1, 1);

-- 3. Типы сопел
INSERT OR IGNORE INTO "sys_Типы сопел" ("Название", "Ожидаемый ресурс (г)", "Примечание") VALUES
('Латунь', 1000, 'Стандартное, быстро изнашивается на абразивах'),
('Закалённая сталь', 5000, 'Для CF/GF пластиков'),
('Рубин', 8000, 'Высокая стойкость к абразивам'),
('Карбид вольфрама', 10000, 'Максимальная стойкость');

-- 4. Виды пластика (Основы + Модификаторы)
INSERT OR IGNORE INTO "sys_Виды пластика" ("Основа", "Модификатор", "Коэф. трудности", "Примечание") VALUES
('PLA', '', 1.0, 'Эталон. Прост в печати.'),
('PLA', '+', 1.1, 'Прочнее обычного.'),
('PLA', 'CF', 2.0, 'Карбон. Абразивный.'),
('PLA', 'Silk', 1.2, 'Шёлковый. Капризный к скорости.'),
('PETG', '', 1.3, 'Прочный, hygroscopic.'),
('PETG', '+', 1.4, 'Улучшенная адгезия слоёв.'),
('PETG', 'CF', 2.5, 'Абразивный.'),
('ABS', '', 1.5, 'Требует камеры. Усадка.'),
('ABS', 'CF', 2.5, 'Абразивный.'),
('ASA', '', 1.5, 'УФ-стойкий. Требует камеры.'),
('PC', '', 1.8, 'Очень прочный. Высокая температура.'),
('PC', 'CF', 3.0, 'Абразивный, сверхпрочный.'),
('PA', '', 1.6, 'Нейлон. Гигроскопичен.'),
('PA', 'CF', 3.0, 'Абразивный.'),
('PA', 'GF', 3.0, 'Абразивный.'),
('TPU', '95A', 0.8, 'Гибкий, эластичный.'),
('TPU', '85A', 0.7, 'Очень мягкий.');

-- 5. Матрица коэффициентов износа
INSERT OR IGNORE INTO "sys_Коэффициенты износа сопла от вида пластика" ("id Пластика", "id Сопла", "Коэффициент")
SELECT 
    p.id, n.id,
    CASE 
        WHEN n."Название" = 'Латунь' AND (p."Модификатор" IN ('CF', 'GF')) THEN 5.0
        WHEN n."Название" = 'Латунь' THEN 1.0
        WHEN n."Название" = 'Закалённая сталь' AND (p."Модификатор" IN ('CF', 'GF')) THEN 2.0
        WHEN n."Название" = 'Закалённая сталь' THEN 1.0
        WHEN n."Название" = 'Рубин' AND (p."Модификатор" IN ('CF', 'GF')) THEN 1.2
        WHEN n."Название" = 'Рубин' THEN 1.0
        WHEN n."Название" = 'Карбид вольфрама' THEN 1.0
        ELSE 1.0 
    END AS coeff
FROM "sys_Виды пластика" p
CROSS JOIN "sys_Типы сопел" n;

-- 6. Базовые цвета
INSERT OR IGNORE INTO "sys_Цвета" ("Название", "Группа", "Порядок", "HEX") VALUES
('Чёрный', 'Ахроматические', 10, '#000000'),
('Белый', 'Ахроматические', 20, '#FFFFFF'),
('Серый', 'Ахроматические', 30, '#808080'),
('Красный', 'Тёплые', 10, '#FF0000'),
('Оранжевый', 'Тёплые', 20, '#FFA500'),
('Жёлтый', 'Тёплые', 30, '#FFFF00'),
('Зелёный', 'Холодные', 10, '#00FF00'),
('Голубой', 'Холодные', 20, '#00BFFF'),
('Синий', 'Холодные', 30, '#0000FF'),
('Фиолетовый', 'Холодные', 40, '#800080'),
('Розовый', 'Холодные', 50, '#FFC0CB'),
('Прозрачный', 'Прозрачные', 10, NULL),
('Полупрозрачный', 'Прозрачные', 20, NULL),
('Светящийся', 'Особые', 10, NULL),
('Шёлковый', 'Особые', 20, NULL),
('Матовый', 'Особые', 30, NULL),
('С блёстками', 'Особые', 40, NULL);