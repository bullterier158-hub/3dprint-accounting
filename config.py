import sys
import os
from pathlib import Path

APP_TITLE = "Учёт 3D-печати (v3.0)"
APP_GEOMETRY = "1200x800"

# 1. Определяем, запущено ли приложение как .exe
if getattr(sys, 'frozen', False):
    # Папка, куда PyInstaller распаковал ресурсы (сюда мы зашили schema.sql)
    BUNDLE_DIR = Path(sys._MEIPASS)
    
    # Папка, где физически лежит .exe файл.
    EXE_DIR = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
else:
    # Режим разработки (запуск через python main.py)
    BUNDLE_DIR = Path(__file__).parent
    EXE_DIR = BUNDLE_DIR

# 2. Пути к SQL-файлам (они всегда лежат в BUNDLE_DIR)
SCHEMA_PATH = BUNDLE_DIR / "db" / "schema.sql"
SEED_TEST_PATH = BUNDLE_DIR / "db" / "seed_test.sql"

# 3. Путь к рабочей БД. 
# ВАЖНО: Мы явно указываем папку EXE_DIR, чтобы база создавалась РЯДОМ с .exe, 
# а не во временной папке PyInstaller.
DB_DIR = EXE_DIR / "db"
DB_PATH = DB_DIR / "db.db"

# 4. Принудительно создаем папку db рядом с exe (если её нет)
if not DB_DIR.exists():
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Создана папка для БД: {DB_DIR}")
    except PermissionError:
        import tkinter.messagebox as mb
        mb.showerror("Ошибка доступа", f"Не удалось создать папку для базы данных:\n{DB_DIR}\n\nПеренесите программу в другую папку (например, на Рабочий стол).")
        sys.exit(1) 