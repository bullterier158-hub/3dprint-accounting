# ui/main_window.py
import tkinter as tk
from tkinter import ttk
from config import APP_TITLE, APP_GEOMETRY

from ui.tabs.settings_tab import SettingsTab
from ui.tabs.inventory_tab import InventoryTab  # <-- Импортируем новую вкладку

class MainWindow:
    def __init__(self, root: tk.Tk, db):
        self.root = root
        self.db = db
        
        self.root.title(APP_TITLE)
        self.root.geometry(APP_GEOMETRY)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tabs = {}
        self._init_tabs()
        self.refresh_all()

    def _init_tabs(self):
        self.add_tab(SettingsTab)
        self.add_tab(InventoryTab) # <-- Добавляем вкладку Склад

    def add_tab(self, tab_cls):
        tab = tab_cls(self.notebook, self.db, self)
        text = f"{tab.icon} {tab.title}".strip()
        self.notebook.add(tab, text=text)
        self.tabs[tab_cls.__name__] = tab
        return tab

    def refresh_all(self):
        for name, tab in self.tabs.items():
            try:
                tab.refresh()
            except Exception as e:
                print(f"[refresh] Ошибка в {name}: {e}")