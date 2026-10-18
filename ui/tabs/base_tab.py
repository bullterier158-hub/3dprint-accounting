# ui/tabs/base_tab.py
from tkinter import ttk

class BaseTab(ttk.Frame):
    """
    Базовый класс для всех вкладок (страниц) приложения.
    """
    title = "Вкладка"
    icon = ""

    def __init__(self, parent, db, app):
        super().__init__(parent)
        self.db = db
        self.app = app  # ссылка на MainWindow для вызова refresh_all()
        self.build_ui()

    def build_ui(self) -> None:
        """Метод для построения интерфейса. Обязателен к переопределению."""
        raise NotImplementedError(f"Метод build_ui не реализован в {self.__class__.__name__}")

    def refresh(self) -> None:
        """Метод для обновления данных. Переопределяется при необходимости."""
        pass