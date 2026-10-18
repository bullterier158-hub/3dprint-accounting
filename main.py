# main.py
import tkinter as tk
from tkinter import messagebox

from config import DB_PATH
from db.manager import DatabaseManager
from ui.main_window import MainWindow

def main():
    root = tk.Tk()
    try:
        # Подключаемся к базе и применяем схему
        db = DatabaseManager(DB_PATH)
    except Exception as e:
        messagebox.showerror("Ошибка БД", f"Не удалось открыть базу:\n{e}")
        root.destroy()
        return

    try:
        # Запускаем главное окно
        MainWindow(root, db)
        root.mainloop()
    finally:
        db.close()

if __name__ == "__main__":
    main()