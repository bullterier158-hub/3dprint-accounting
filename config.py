from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
# Теперь БД лежит внутри папки db
DB_PATH = str(BASE_DIR / "db" / "db.db") 
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"

APP_TITLE = "Учет 3D-печати (v3.0)"
APP_GEOMETRY = "1180x780"