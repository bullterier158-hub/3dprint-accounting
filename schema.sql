BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "Виды пластика" (
	"id"	INTEGER,
	"Название"	TEXT NOT NULL UNIQUE,
	"Рыночная стоимость (руб./г)"	REAL DEFAULT 0,
	"Заметки"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Заказанный пластик" (
	"id"	INTEGER,
	"Вид пластика id"	INTEGER,
	"Марка"	TEXT,
	"Цвет"	TEXT,
	"Количество (шт)"	INTEGER DEFAULT 1,
	"Цена заказа"	REAL,
	"Ссылка"	TEXT,
	"Статус"	TEXT DEFAULT 'В пути',
	"Дата заказа"	TEXT DEFAULT (datetime('now', 'localtime')),
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("Вид пластика id") REFERENCES "Виды пластика"("id")
);
CREATE TABLE IF NOT EXISTS "Очередь печати" (
	"id"	INTEGER,
	"id проекта"	INTEGER,
	"Вид пластика id"	INTEGER,
	"Требуемый вес (г)"	REAL,
	"Статус"	TEXT DEFAULT 'В очереди',
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("id проекта") REFERENCES "Проекты"("id"),
	FOREIGN KEY("Вид пластика id") REFERENCES "Виды пластика"("id")
);
CREATE TABLE IF NOT EXISTS "Проекты" (
	"id"	INTEGER,
	"Название"	TEXT NOT NULL,
	"Статус"	TEXT DEFAULT 'В работе',
	"Заказчик"	TEXT,
	"Цена"	REAL,
	"Дата создания"	TEXT DEFAULT (datetime('now', 'localtime')),
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Расход катушек" (
	"id события"	INTEGER,
	"id катушки"	INTEGER NOT NULL,
	"id проекта"	INTEGER,
	"Количество (г)"	REAL NOT NULL,
	"Фактический расход (г)"	REAL,
	"Результат"	TEXT DEFAULT 'Успех',
	"Дата события"	TEXT DEFAULT (datetime('now', 'localtime')),
	PRIMARY KEY("id события" AUTOINCREMENT),
	FOREIGN KEY("id катушки") REFERENCES "Филамент в наличии"("Внутренний ID"),
	FOREIGN KEY("id проекта") REFERENCES "Проекты"("id")
);
CREATE TABLE IF NOT EXISTS "Сопла" (
	"id"	INTEGER,
	"Тип сопла id"	INTEGER NOT NULL,
	"Серийный номер"	TEXT,
	"Дата установки"	TEXT DEFAULT (datetime('now', 'localtime')),
	"Дата покупки"	TEXT,
	"Стоимость (руб)"	REAL NOT NULL,
	"Наработка (г)"	REAL DEFAULT 0,
	"Статус"	TEXT DEFAULT 'В работе',
	"Заметки"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("Тип сопла id") REFERENCES "Типы сопел"("id")
);
CREATE TABLE IF NOT EXISTS "Тарифы" (
	"id"	INTEGER,
	"Электричество (руб./кВт)"	REAL DEFAULT 5.0,
	"Стоимость принтера (руб)"	REAL DEFAULT 0,
	"Часы до кап. ремонта"	REAL DEFAULT 5000,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Типы сопел" (
	"id"	INTEGER,
	"Название"	TEXT NOT NULL UNIQUE,
	"Материал"	TEXT,
	"Диаметр (мм)"	REAL DEFAULT 0.4,
	"Ресурс (г)"	REAL NOT NULL,
	"Коэф. износа PLA"	REAL DEFAULT 1.0,
	"Коэф. износа PLA+"	REAL DEFAULT 1.0,
	"Коэф. износа PLA-CF"	REAL DEFAULT 5.0,
	"Коэф. износа PLA-GF"	REAL DEFAULT 5.0,
	"Коэф. износа PETG"	REAL DEFAULT 1.0,
	"Коэф. износа PETG+"	REAL DEFAULT 1.0,
	"Коэф. износа PETG-CF"	REAL DEFAULT 5.0,
	"Коэф. износа PETG-GF"	REAL DEFAULT 5.0,
	"Коэф. износа ABS"	REAL DEFAULT 1.2,
	"Коэф. износа ABS-CF"	REAL DEFAULT 6.0,
	"Коэф. износа ABS-GF"	REAL DEFAULT 6.0,
	"Коэф. износа ASA"	REAL DEFAULT 1.3,
	"Коэф. износа ASA-CF"	REAL DEFAULT 6.0,
	"Коэф. износа TPU 95A"	REAL DEFAULT 0.8,
	"Коэф. износа TPU 98A"	REAL DEFAULT 0.8,
	"Коэф. износа TPU 85A"	REAL DEFAULT 0.7,
	"Коэф. износа TPU 75D"	REAL DEFAULT 0.9,
	"Заметки"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Филамент в наличии" (
	"Внутренний ID"	INTEGER,
	"Вид пластика id"	INTEGER NOT NULL,
	"Марка"	TEXT,
	"Цвет"	TEXT NOT NULL,
	"Стоимость катушки (RUB)"	NUMERIC NOT NULL,
	"Заявленный вес пластика (г)"	NUMERIC NOT NULL,
	"Себестоимость 1г пластика (руб.)"	NUMERIC GENERATED ALWAYS AS (ROUND(CAST("Стоимость катушки (RUB)" AS REAL) / "Заявленный вес пластика (г)", 4)) STORED,
	"Приблизительный остаток (г)"	NUMERIC DEFAULT 0,
	"Дата покупки"	TEXT DEFAULT (datetime('now', 'localtime')),
	PRIMARY KEY("Внутренний ID" AUTOINCREMENT),
	FOREIGN KEY("Вид пластика id") REFERENCES "Виды пластика"("id")
);
CREATE TABLE IF NOT EXISTS "Цены на филамент у поставщиков (OZON)" (
	"id"	INTEGER,
	"Вид пластика id"	INTEGER,
	"Марка"	TEXT,
	"Цвет"	TEXT,
	"Вес катушки"	REAL,
	"Цена"	REAL NOT NULL,
	"Ссылка"	TEXT,
	"Дата обновления информации"	TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("Вид пластика id") REFERENCES "Виды пластика"("id")
);
COMMIT;
