# ui/tabs/inventory_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
from ui.tabs.base_tab import BaseTab
from ui.common import parse_float, fmt_float

class InventoryTab(BaseTab):
    """Вкладка «Склад»: учёт принтеров, физических сопел и катушек пластика."""

    title = "Склад"
    icon = "📦"

    def build_ui(self):
        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.tab_printers = ttk.Frame(self.sub_notebook)
        self.tab_nozzles = ttk.Frame(self.sub_notebook)
        self.tab_spools = ttk.Frame(self.sub_notebook)

        self.sub_notebook.add(self.tab_printers, text="Принтеры")
        self.sub_notebook.add(self.tab_nozzles, text="Сопла")
        self.sub_notebook.add(self.tab_spools, text="Катушки пластика")

        self._build_printers_ui()
        self._build_nozzles_ui()
        self._build_spools_ui()

        # Словарь для хранения картинок цветов (чтобы Tkinter их не удалял)
        self.color_icons = {}

    # =================================================================
    # ПОД-ВКЛАДКА 1: ПРИНТЕРЫ
    # =================================================================
    def _build_printers_ui(self):
        tree_frm = ttk.Frame(self.tab_printers)
        tree_frm.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        cols = ("Название", "Группа по соплу", "Стоимость (руб)", "Ресурс (ч)")
        self.tree_printers = ttk.Treeview(tree_frm, columns=cols, show="headings")
        
        for c in cols:
            self.tree_printers.heading(c, text=c)
            self.tree_printers.column(c, width=150, anchor="center")
        
        scroll = ttk.Scrollbar(tree_frm, orient="vertical", command=self.tree_printers.yview)
        self.tree_printers.configure(yscrollcommand=scroll.set)
        self.tree_printers.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.ctx_menu_printers = tk.Menu(self, tearoff=0)
        self.ctx_menu_printers.add_command(label="✏ Изменить", command=self._edit_printer)
        self.ctx_menu_printers.add_command(label="🗑 Удалить", command=self._delete_printer)
        self.tree_printers.bind("<Button-3>", self._show_printer_context_menu)

        frm_btns = ttk.Frame(self.tab_printers)
        frm_btns.pack(fill="x", padx=10, pady=5)
        ttk.Button(frm_btns, text="➕ Добавить", command=self._add_printer).pack(side="right")

    def _show_printer_context_menu(self, event):
        item = self.tree_printers.identify_row(event.y)
        if item:
            self.tree_printers.selection_set(item)
            self.ctx_menu_printers.post(event.x_root, event.y_root)

    def _refresh_printers(self):
        for i in self.tree_printers.get_children(): 
            self.tree_printers.delete(i)
        for p in self.db.inventory.get_all_printers():
            self.tree_printers.insert("", "end", iid=str(p["id"]), values=(
                p["Название"], 
                p["Группа по соплу"], 
                fmt_float(p["Стоимость (руб)"]), 
                fmt_float(p["Ресурс (ч)"])
            ))

    def _printer_form(self, p_id=None):
        dialog = tk.Toplevel(self)
        dialog.title("Принтер")
        dialog.geometry("350x250")
        dialog.grab_set()

        ttk.Label(dialog, text="Название:").pack(pady=(10,2))
        e_name = ttk.Entry(dialog); e_name.pack(fill="x", padx=20)
        
        ttk.Label(dialog, text="Группа по соплу (число):").pack(pady=(5,2))
        e_group = ttk.Entry(dialog); e_group.pack(fill="x", padx=20); e_group.insert(0, "1")
        
        ttk.Label(dialog, text="Стоимость (руб):").pack(pady=(5,2))
        e_cost = ttk.Entry(dialog); e_cost.pack(fill="x", padx=20)
        
        ttk.Label(dialog, text="Ресурс (ч):").pack(pady=(5,2))
        e_res = ttk.Entry(dialog); e_res.pack(fill="x", padx=20)

        if p_id:
            row = next((x for x in self.db.inventory.get_all_printers() if x["id"] == p_id), None)
            if row:
                e_name.insert(0, row["Название"])
                e_group.delete(0, tk.END); e_group.insert(0, str(row["Группа по соплу"]))
                e_cost.insert(0, fmt_float(row["Стоимость (руб)"]))
                e_res.insert(0, fmt_float(row["Ресурс (ч)"]))

        def save():
            try:
                ok = self.db.inventory.update_printer(p_id, e_name.get(), int(e_group.get()), parse_float(e_cost.get()), parse_float(e_res.get())) if p_id else \
                     self.db.inventory.add_printer(e_name.get(), int(e_group.get()), parse_float(e_cost.get()), parse_float(e_res.get()))
                if ok:
                    dialog.destroy(); self.refresh()
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить.")
            except ValueError:
                messagebox.showerror("Ошибка", "Проверьте числа.")
        ttk.Button(dialog, text="Сохранить", command=save).pack(pady=15)

    def _add_printer(self): self._printer_form()
    def _edit_printer(self):
        sel = self.tree_printers.selection()
        if sel: self._printer_form(int(sel[0]))
    def _delete_printer(self):
        sel = self.tree_printers.selection()
        if sel and messagebox.askyesno("Удалить?", "Точно?"):
            self.db.inventory.delete_printer(int(sel[0])); self.refresh()

    # =================================================================
    # ПОД-ВКЛАДКА 2: СОПЛА
    # =================================================================
    def _build_nozzles_ui(self):
        tree_frm = ttk.Frame(self.tab_nozzles)
        tree_frm.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        # Добавили "Группа" и "Название"
        cols = ("Название", "Группа", "Тип", "Диаметр (мм)", "Ресурс (г)")
        self.tree_nozzles = ttk.Treeview(tree_frm, columns=cols, show="headings")
        
        for c in cols:
            self.tree_nozzles.heading(c, text=c)
            self.tree_nozzles.column(c, width=120, anchor="center")
        
        scroll = ttk.Scrollbar(tree_frm, orient="vertical", command=self.tree_nozzles.yview)
        self.tree_nozzles.configure(yscrollcommand=scroll.set)
        self.tree_nozzles.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.ctx_menu_nozzles = tk.Menu(self, tearoff=0)
        self.ctx_menu_nozzles.add_command(label="✏ Изменить", command=self._edit_nozzle)
        self.ctx_menu_nozzles.add_command(label="🗑 Удалить", command=self._delete_nozzle)
        self.tree_nozzles.bind("<Button-3>", self._show_nozzle_context_menu)

        frm_btns = ttk.Frame(self.tab_nozzles)
        frm_btns.pack(fill="x", padx=10, pady=5)
        ttk.Button(frm_btns, text="➕ Добавить", command=self._add_nozzle).pack(side="right")

    def _show_nozzle_context_menu(self, event):
        item = self.tree_nozzles.identify_row(event.y)
        if item:
            self.tree_nozzles.selection_set(item)
            self.ctx_menu_nozzles.post(event.x_root, event.y_root)

    def _refresh_nozzles(self):
        for i in self.tree_nozzles.get_children(): 
            self.tree_nozzles.delete(i)
        for n in self.db.inventory.get_all_nozzles():
            # Используем "Название" из БД, если оно есть. Если нет - генерируем старое имя
            display_name = n["Название"] or f"Сопло {n['Тип']} {fmt_float(n['Диаметр (мм)'])}мм"
            
            self.tree_nozzles.insert("", "end", iid=str(n["id"]), values=(
                display_name,
                n["Группа по соплу"],
                n["Тип"], 
                fmt_float(n["Диаметр (мм)"]), 
                fmt_float(n["Ресурс (г)"])
            ))

    def _nozzle_form(self, n_id=None):
        dialog = tk.Toplevel(self)
        dialog.title("Физическое сопло")
        dialog.geometry("400x450")
        dialog.grab_set()

        types = self.db.settings.get_all_nozzle_types()
        type_names = [t["Название"] for t in types]

        ttk.Label(dialog, text="Тип сопла:").pack(pady=(10,2))
        combo_type = ttk.Combobox(dialog, values=type_names, state="readonly")
        combo_type.pack(fill="x", padx=20)
        if type_names: combo_type.current(0)

        ttk.Label(dialog, text="Группа по соплу (ID):").pack(pady=(5,2))
        e_group = ttk.Entry(dialog); e_group.pack(fill="x", padx=20); e_group.insert(0, "1")

        ttk.Label(dialog, text="Диаметр (мм):").pack(pady=(5,2))
        e_diam = ttk.Entry(dialog); e_diam.pack(fill="x", padx=20); e_diam.insert(0, "0.4")
        
        ttk.Label(dialog, text="Ресурс (г):").pack(pady=(5,2))
        e_res = ttk.Entry(dialog); e_res.pack(fill="x", padx=20)

        # Поле для названия
        ttk.Label(dialog, text="Название (автогенерация + можно дописать):").pack(pady=(10,2))
        e_name = ttk.Entry(dialog); e_name.pack(fill="x", padx=20)

        def generate_name(event=None):
            """Генерирует базовое название, но не перезаписывает его, если пользователь уже начал вводить свой текст"""
            current = e_name.get()
            base_name = f"Сопло {combo_type.get()} {e_diam.get()}мм"
            
            # Перезаписываем только если поле пустое или совпадает с предыдущей автогенерацией
            # (упрощенный вариант: перезаписываем только если пользователь стер всё)
            if not current.strip():
                e_name.insert(0, base_name)

        # Привязка событий к полям для автообновления (только если поле пустое)
        combo_type.bind("<<ComboboxSelected>>", generate_name)
        e_diam.bind("<FocusOut>", generate_name) 

        # Автозаполнение ресурса при выборе типа
        def on_type_select(event=None):
            selected_name = combo_type.get()
            selected_type = next((t for t in types if t["Название"] == selected_name), None)
            if selected_type and selected_type["Ожидаемый ресурс (г)"] is not None:
                e_res.delete(0, tk.END)
                e_res.insert(0, fmt_float(selected_type["Ожидаемый ресурс (г)"]))
            generate_name()

        combo_type.bind("<<ComboboxSelected>>", on_type_select)

        if not n_id and types:
            on_type_select()
            generate_name()
            # Переместим курсор в конец названия для удобства добавления приписки
            e_name.focus_set()
            e_name.icursor(tk.END)

        if n_id:
            row = next((x for x in self.db.inventory.get_all_nozzles() if x["id"] == n_id), None)
            if row:
                combo_type.set(row["Тип"])
                e_group.delete(0, tk.END); e_group.insert(0, str(row["Группа по соплу"]))
                e_diam.delete(0, tk.END); e_diam.insert(0, fmt_float(row["Диаметр (мм)"]))
                e_res.delete(0, tk.END); e_res.insert(0, fmt_float(row["Ресурс (г)"]))
                
                # Если в БД есть название - ставим его. Если нет - генерируем дефолтное.
                if row["Название"]:
                    e_name.insert(0, row["Название"])
                else:
                    e_name.insert(0, f"Сопло {row['Тип']} {fmt_float(row['Диаметр (мм)'])}мм")

        def save():
            try:
                type_id = next(t["id"] for t in types if t["Название"] == combo_type.get())
                group_id = int(e_group.get())
                
                if n_id:
                    ok = self.db.inventory.update_nozzle(
                        n_id, type_id, group_id, parse_float(e_diam.get()), parse_float(e_res.get()), e_name.get()
                    )
                else:
                    ok = self.db.inventory.add_nozzle(
                        type_id, group_id, parse_float(e_diam.get()), parse_float(e_res.get()), e_name.get()
                    )

                if ok:
                    dialog.destroy(); self.refresh()
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить.")
            except (ValueError, StopIteration):
                messagebox.showerror("Ошибка", "Проверьте числа или выбранный тип.")
                
        ttk.Button(dialog, text="Сохранить", command=save).pack(pady=20)

    def _add_nozzle(self): self._nozzle_form()
    def _edit_nozzle(self):
        sel = self.tree_nozzles.selection()
        if sel: self._nozzle_form(int(sel[0]))
    def _delete_nozzle(self):
        sel = self.tree_nozzles.selection()
        if sel and messagebox.askyesno("Удалить?", "Точно?"):
            self.db.inventory.delete_nozzle(int(sel[0])); self.refresh()

    # =================================================================
    # ПОД-ВКЛАДКА 3: КАТУШКИ ПЛАСТИКА
    # =================================================================
    def _build_spools_ui(self):
        tree_frm = ttk.Frame(self.tab_spools)
        tree_frm.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        # Убрали "Цвет" из этого кортежа
        cols = ("Материал", "Стоимость покупки (руб)", "Вес Нетто (г)", "Остаток (г)", "Статус")
        self.tree_spools = ttk.Treeview(tree_frm, columns=cols)
        
        # Настраиваем первую колонку (#0). Делаем её широкой и даем заголовок "Цвет"
        self.tree_spools.heading("#0", text="Цвет")
        self.tree_spools.column("#0", width=150, anchor="center", stretch=False)
        
        for c in cols:
            self.tree_spools.heading(c, text=c)
            self.tree_spools.column(c, width=120, anchor="center")
        
        scroll = ttk.Scrollbar(tree_frm, orient="vertical", command=self.tree_spools.yview)
        self.tree_spools.configure(yscrollcommand=scroll.set)
        self.tree_spools.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.ctx_menu_spools = tk.Menu(self, tearoff=0)
        self.ctx_menu_spools.add_command(label="✏ Изменить данные", command=self._edit_spool)
        self.ctx_menu_spools.add_command(label="➕ Записать расход", command=self._add_consumption_dialog)
        self.ctx_menu_spools.add_command(label="📜 История катушки", command=self._show_spool_history)
        self.ctx_menu_spools.add_separator()
        self.ctx_menu_spools.add_command(label="🔗 Приварить к...", command=self._weld_spool)
        self.ctx_menu_spools.add_command(label="🗑 Выбросить остаток", command=self._discard_spool)
        
        self.tree_spools.bind("<Button-3>", self._show_spool_context_menu)

        frm_btns = ttk.Frame(self.tab_spools)
        frm_btns.pack(fill="x", padx=10, pady=5)
        ttk.Button(frm_btns, text="➕ Добавить", command=self._add_spool).pack(side="right")

    def _show_spool_context_menu(self, event):
        item = self.tree_spools.identify_row(event.y)
        if item:
            self.tree_spools.selection_set(item)
            self.ctx_menu_spools.post(event.x_root, event.y_root)

    def _refresh_spools(self):
        for i in self.tree_spools.get_children(): 
            self.tree_spools.delete(i)
        self.color_icons.clear()

        for s in self.db.inventory.get_all_spools():
            img = ""
            if s["HEX Цвета"] and s["HEX Цвета"].startswith("#") and len(s["HEX Цвета"]) == 7:
                try:
                    icon = tk.PhotoImage(width=16, height=16)
                    icon.put(s["HEX Цвета"], to=(0, 0, 16, 16))
                    self.color_icons[s["id"]] = icon
                    img = icon
                except tk.TclError:
                    img = ""

            # Картинка и текст передаются в #0 через image= и text=
            self.tree_spools.insert("", "end", iid=str(s["id"]), image=img, text=s["Цвет"], values=(
                s["Материал"], 
                fmt_float(s["Стоимость покупки (руб)"]), 
                fmt_float(s["Вес Нетто (г)"]),
                fmt_float(s["Остаток (г)"]),
                s["Статус"]
            ))

    def _spool_form(self, s_id=None):
        dialog = tk.Toplevel(self)
        dialog.title("Катушка пластика")
        dialog.geometry("350x350")
        dialog.grab_set()

        ttk.Label(dialog, text="Материал:").pack(pady=(10,2))
        mats = self.db.settings.get_all_plastics()
        mat_names = [f"{m['Основа']} {m['Модификатор']}".strip() for m in mats]
        combo_mat = ttk.Combobox(dialog, values=mat_names, state="readonly")
        combo_mat.pack(fill="x", padx=20)
        if mat_names: combo_mat.current(0)

        ttk.Label(dialog, text="Цвет:").pack(pady=(5,2))
        colors = self.db.settings.get_all_colors()
        color_names = [c["Название"] for c in colors]
        combo_color = ttk.Combobox(dialog, values=color_names, state="readonly")
        combo_color.pack(fill="x", padx=20)
        if color_names: combo_color.current(0)

        ttk.Label(dialog, text="Стоимость покупки (руб):").pack(pady=(5,2))
        e_cost = ttk.Entry(dialog); e_cost.pack(fill="x", padx=20)
        
        ttk.Label(dialog, text="Вес Нетто (г):").pack(pady=(5,2))
        e_weight = ttk.Entry(dialog); e_weight.pack(fill="x", padx=20)

        ttk.Label(dialog, text="Статус:").pack(pady=(5,2))
        combo_status = ttk.Combobox(dialog, values=["Активна", "Закончилась", "Выброшена", "Приварена"], state="readonly")
        combo_status.pack(fill="x", padx=20)
        combo_status.current(0)

        if s_id:
            row = next((x for x in self.db.inventory.get_all_spools() if x["id"] == s_id), None)
            if row:
                combo_mat.set(row["Материал"])
                combo_color.set(row["Цвет"])
                e_cost.insert(0, fmt_float(row["Стоимость покупки (руб)"]))
                e_weight.insert(0, fmt_float(row["Вес Нетто (г)"]))
                combo_status.set(row["Статус"])

        def save():
            try:
                mat_id = next(m["id"] for m in mats if f"{m['Основа']} {m['Модификатор']}".strip() == combo_mat.get())
                color_id = next(c["id"] for c in colors if c["Название"] == combo_color.get())
                
                if s_id:
                    ok = self.db.inventory.update_spool(s_id, mat_id, color_id, parse_float(e_cost.get()), parse_float(e_weight.get()))
                    if ok: self.db.inventory.update_spool_status(s_id, combo_status.get())
                else:
                    ok = self.db.inventory.add_spool(mat_id, color_id, parse_float(e_cost.get()), parse_float(e_weight.get()))

                if ok:
                    dialog.destroy(); self.refresh()
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить.")
            except (ValueError, StopIteration):
                messagebox.showerror("Ошибка", "Проверьте числа или выбранные значения.")
        ttk.Button(dialog, text="Сохранить", command=save).pack(pady=15)

    def _add_spool(self): self._spool_form()
    def _edit_spool(self):
        sel = self.tree_spools.selection()
        if sel: self._spool_form(int(sel[0]))
    def _delete_spool(self):
        sel = self.tree_spools.selection()
        if sel and messagebox.askyesno("Удалить?", "Точно?"):
            self.db.inventory.delete_spool(int(sel[0])); self.refresh()

    # --- Действия из контекстного меню ---

    def _add_consumption_dialog(self):
        sel = self.tree_spools.selection()
        if not sel: return
        s_id = int(sel[0])

        dialog = tk.Toplevel(self)
        dialog.title("Записать расход")
        dialog.geometry("300x150")
        dialog.grab_set()

        ttk.Label(dialog, text="Количество (г):").pack(pady=10)
        e_grams = ttk.Entry(dialog)
        e_grams.pack(padx=20, fill="x")
        e_grams.focus_set()

        def save():
            try:
                grams = parse_float(e_grams.get())
                if self.db.inventory.add_consumption(s_id, grams):
                    dialog.destroy()
                    self.refresh()
            except ValueError:
                messagebox.showerror("Ошибка", "Введите число.")

        ttk.Button(dialog, text="Записать", command=save).pack(pady=10)

    def _show_spool_history(self):
        sel = self.tree_spools.selection()
        if not sel: return
        s_id = int(sel[0])

        dialog = tk.Toplevel(self)
        dialog.title(f"История катушки")
        dialog.geometry("500x300")
        dialog.grab_set()

        # Изменили колонки: добавили "Тип действия"
        cols = ("Дата", "Тип", "Количество (г)")
        tree = ttk.Treeview(dialog, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=150, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for r in self.db.inventory.get_spool_history(s_id):
            tree.insert("", "end", values=(
                r["Дата события"], 
                r["Тип действия"], 
                fmt_float(r["Количество (г)"])
            ))

    def _weld_spool(self):
        sel = self.tree_spools.selection()
        if not sel: return
        
        source_id = int(sel[0])
        source_data = next((x for x in self.db.inventory.get_all_spools() if x["id"] == source_id), None)
        if not source_data: return

        dialog = tk.Toplevel(self)
        dialog.title("Сварка остатка")
        dialog.geometry("400x250")
        dialog.grab_set()

        ttk.Label(dialog, text=f"Вы варите катушку: {source_data['Материал']} / {source_data['Цвет']}", font=("", 9, "bold")).pack(pady=(10,2))
        ttk.Label(dialog, text=f"Текущий остаток: {source_data['Остаток (г)']:.1f} г", foreground="gray").pack()
        
        ttk.Label(dialog, text="К какой катушке приварить?").pack(pady=(15,2))
        
        all_spools = self.db.inventory.get_all_spools()
        valid_targets = [s for s in all_spools if s["id"] != source_id and s["Статус"] not in ('Выброшена', 'Приварена')]
        
        display_list = []
        for s in valid_targets:
            display_list.append(f"ID {s['id']} | {s['Материал']} {s['Цвет']} (остаток: {s['Остаток (г)']:.1f} г)")

        combo_target = ttk.Combobox(dialog, values=display_list, state="readonly", width=50)
        combo_target.pack(fill="x", padx=20, pady=5)
        if display_list: combo_target.current(0)

        def save():
            if not combo_target.get():
                messagebox.showerror("Ошибка", "Выберите катушку.")
                return

            target_id = int(combo_target.get().split(" | ")[0].replace("ID ", ""))
            target_data = next((x for x in valid_targets if x["id"] == target_id), None)

            if not target_data: return

            if source_data["Материал"] != target_data["Материал"]:
                if not messagebox.askyesno("Внимание", 
                    f"Вы пытаетесь приварить {source_data['Материал']} к {target_data['Материал']}.\n"
                    "Разные материалы могут по-разному плавиться.\n"
                    "Продолжить?"):
                    return

            # Вызываем атомарную функцию сварки из репозитория
            if self.db.inventory.weld_spools(source_id, target_id):
                messagebox.showinfo("Успех", "Катушки успешно сварены. Масса перераспределена.")
                dialog.destroy()
                self.refresh()
            else:
                messagebox.showerror("Ошибка", "Не удалось выполнить сварку (возможно, остаток уже 0).")

        ttk.Button(dialog, text="Приварить", command=save).pack(pady=15)

    def _discard_spool(self):
        sel = self.tree_spools.selection()
        if not sel: return
        s_id = int(sel[0])
        if messagebox.askyesno("Выбросить", "Вы уверены, что хотите выбросить остаток этой катушки?"):
            self.db.inventory.update_spool_status(s_id, "Выброшена")
            self.refresh()

    # =================================================================
    # ОБНОВЛЕНИЕ
    # =================================================================
    def refresh(self):
        self._refresh_printers()
        self._refresh_nozzles()
        self._refresh_spools()