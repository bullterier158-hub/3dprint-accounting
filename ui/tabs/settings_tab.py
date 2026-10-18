# ui/tabs/settings_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
from ui.tabs.base_tab import BaseTab
from ui.common import parse_float, fmt_float

class SettingsTab(BaseTab):
    title = "Глобальные настройки"
    icon = "⚙️"

    def build_ui(self):
        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.tab_tariffs = ttk.Frame(self.sub_notebook)
        self.tab_plastics = ttk.Frame(self.sub_notebook)
        self.tab_nozzles = ttk.Frame(self.sub_notebook)
        self.tab_matrix = ttk.Frame(self.sub_notebook)
        self.tab_colors = ttk.Frame(self.sub_notebook)

        self.sub_notebook.add(self.tab_tariffs, text="Тарифы")
        self.sub_notebook.add(self.tab_plastics, text="Виды пластика")
        self.sub_notebook.add(self.tab_nozzles, text="Типы сопел")
        self.sub_notebook.add(self.tab_matrix, text="Коэффициенты износа")
        self.sub_notebook.add(self.tab_colors, text="Цвета")

        self._build_tariffs_ui()
        self._build_plastics_ui()
        self._build_nozzles_ui()
        self._build_matrix_ui()
        self._build_colors_ui()

    # =================================================================
    # ПОД-ВКЛАДКА 1: ТАРИФЫ
    # =================================================================
    def _build_tariffs_ui(self):
        main_frm = ttk.Frame(self.tab_tariffs, padding=20)
        main_frm.pack(fill="both", expand=True)

        frm_elec = ttk.LabelFrame(main_frm, text=" Электричество ", padding=10)
        frm_elec.pack(fill="x", pady=5)

        ttk.Label(frm_elec, text="Тип тарифа:").grid(row=0, column=0, sticky="w", pady=5)
        self.combo_t_type = ttk.Combobox(frm_elec, values=["фикс", "день/ночь"], state="readonly", width=20)
        self.combo_t_type.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        self.combo_t_type.bind("<<ComboboxSelected>>", self._toggle_night_price)

        ttk.Label(frm_elec, text="Цена 1кВт (день/единая):").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_t_day = ttk.Entry(frm_elec, width=15)
        self.entry_t_day.grid(row=1, column=1, sticky="w", pady=5, padx=10)

        ttk.Label(frm_elec, text="Цена 1кВт (ночь):").grid(row=2, column=0, sticky="w", pady=5)
        self.entry_t_night = ttk.Entry(frm_elec, width=15)
        self.entry_t_night.grid(row=2, column=1, sticky="w", pady=5, padx=10)

        frm_defect = ttk.LabelFrame(main_frm, text=" Качество ", padding=10)
        frm_defect.pack(fill="x", pady=10)

        ttk.Label(frm_defect, text="Процент брака (%):").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_defect = ttk.Entry(frm_defect, width=15)
        self.entry_defect.grid(row=0, column=1, sticky="w", pady=5, padx=10)

        frm_tax = ttk.LabelFrame(main_frm, text=" Налогообложение ", padding=10)
        frm_tax.pack(fill="x", pady=5)

        ttk.Label(frm_tax, text="Текущий режим:").grid(row=0, column=0, sticky="w", pady=5)
        self.combo_tax = ttk.Combobox(frm_tax, state="readonly", width=30)
        self.combo_tax.grid(row=0, column=1, sticky="w", pady=5, padx=10)

        ttk.Button(main_frm, text="💾 Сохранить настройки", command=self._save_tariffs).pack(pady=20)

    def _toggle_night_price(self, event=None):
        if self.combo_t_type.get() == "фикс":
            self.entry_t_night.config(state="disabled")
            self.entry_t_night.delete(0, tk.END)
        else:
            self.entry_t_night.config(state="normal")

    def _save_tariffs(self):
        try:
            t_type = self.combo_t_type.get()
            day = parse_float(self.entry_t_day.get())
            night = parse_float(self.entry_t_night.get()) if t_type != "фикс" else None
            defect = parse_float(self.entry_defect.get())
            
            tax_idx = self.combo_tax.current()
            if tax_idx == -1:
                messagebox.showerror("Ошибка", "Выберите налоговый режим.")
                return
            
            taxes = self.db.settings.get_all_tax_regimes()
            tax_id = taxes[tax_idx]["id"]

            if self.db.settings.update_tariffs(t_type, day, night, defect, tax_id):
                messagebox.showinfo("Успех", "Настройки сохранены!")
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить (проверьте числа).")
        except ValueError:
            messagebox.showerror("Ошибка", "Все поля должны быть числами.")

    # =================================================================
    # ПОД-ВКЛАДКА 2: ВИДЫ ПЛАСТИКА
    # =================================================================
    def _build_plastics_ui(self):
        tree_frm = ttk.Frame(self.tab_plastics)
        tree_frm.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        cols = ("Основа", "Модификатор", "Коэф. трудности", "Примечание")
        self.tree_plastics = ttk.Treeview(tree_frm, columns=cols, show="headings")
        
        self.tree_plastics.heading("Основа", text="Основа")
        self.tree_plastics.column("Основа", width=120, anchor="center")
        
        self.tree_plastics.heading("Модификатор", text="Модификатор")
        self.tree_plastics.column("Модификатор", width=120, anchor="center")
        
        self.tree_plastics.heading("Коэф. трудности", text="Коэф. трудности")
        self.tree_plastics.column("Коэф. трудности", width=120, anchor="center")
        
        self.tree_plastics.heading("Примечание", text="Примечание")
        self.tree_plastics.column("Примечание", width=350, anchor="center")
        
        scroll = ttk.Scrollbar(tree_frm, orient="vertical", command=self.tree_plastics.yview)
        self.tree_plastics.configure(yscrollcommand=scroll.set)
        
        self.tree_plastics.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.ctx_menu_plastics = tk.Menu(self, tearoff=0)
        self.ctx_menu_plastics.add_command(label="✏ Изменить", command=self._edit_plastic)
        self.ctx_menu_plastics.add_command(label="🗑 Удалить", command=self._delete_plastic)
        self.tree_plastics.bind("<Button-3>", self._show_plastic_context_menu)

        frm_btns = ttk.Frame(self.tab_plastics)
        frm_btns.pack(fill="x", padx=10, pady=5)
        ttk.Button(frm_btns, text="➕ Добавить", command=self._add_plastic).pack(side="right")

    def _show_plastic_context_menu(self, event):
        item = self.tree_plastics.identify_row(event.y)
        if item:
            self.tree_plastics.selection_set(item)
            self.ctx_menu_plastics.post(event.x_root, event.y_root)

    def _refresh_plastics(self):
        for i in self.tree_plastics.get_children(): self.tree_plastics.delete(i)
        for p in self.db.settings.get_all_plastics():
            self.tree_plastics.insert("", "end", iid=str(p["id"]), values=(
                p["Основа"], p["Модификатор"], 
                fmt_float(p["Коэф. трудности"]), p["Примечание"] or ""
            ))

    def _plastic_form(self, p_id=None):
        dialog = tk.Toplevel(self)
        dialog.title("Пластик")
        dialog.geometry("350x250")
        dialog.grab_set()

        ttk.Label(dialog, text="Основа (напр. PLA):").pack(pady=(10,2))
        e_base = ttk.Entry(dialog); e_base.pack(fill="x", padx=20)
        ttk.Label(dialog, text="Модификатор (напр. +, CF, пусто):").pack(pady=(5,2))
        e_mod = ttk.Entry(dialog); e_mod.pack(fill="x", padx=20)
        ttk.Label(dialog, text="Коэф. трудности:").pack(pady=(5,2))
        e_coeff = ttk.Entry(dialog); e_coeff.pack(fill="x", padx=20); e_coeff.insert(0, "1.0")
        ttk.Label(dialog, text="Примечание:").pack(pady=(5,2))
        e_note = ttk.Entry(dialog); e_note.pack(fill="x", padx=20)

        if p_id:
            row = next((x for x in self.db.settings.get_all_plastics() if x["id"] == p_id), None)
            if row:
                e_base.insert(0, row["Основа"])
                e_mod.insert(0, row["Модификатор"] or "")
                e_coeff.delete(0, tk.END); e_coeff.insert(0, fmt_float(row["Коэф. трудности"]))
                e_note.insert(0, row["Примечание"] or "")

        def save():
            try:
                ok = self.db.settings.update_plastic(p_id, e_base.get(), e_mod.get(), parse_float(e_coeff.get()), e_note.get()) if p_id else \
                     self.db.settings.add_plastic(e_base.get(), e_mod.get(), parse_float(e_coeff.get()), e_note.get())
                if ok:
                    dialog.destroy(); self.refresh()
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить (возможно дубликат).")
            except ValueError:
                messagebox.showerror("Ошибка", "Коэф. должен быть числом.")
        ttk.Button(dialog, text="Сохранить", command=save).pack(pady=15)

    def _add_plastic(self): self._plastic_form()
    def _edit_plastic(self):
        sel = self.tree_plastics.selection()
        if sel: self._plastic_form(int(sel[0]))
    def _delete_plastic(self):
        sel = self.tree_plastics.selection()
        if sel and messagebox.askyesno("Удалить?", "Точно?"):
            self.db.settings.delete_plastic(int(sel[0])); self.refresh()

    # =================================================================
    # ПОД-ВКЛАДКА 3: ТИПЫ СОПЕЛ
    # =================================================================
    def _build_nozzles_ui(self):
        tree_frm = ttk.Frame(self.tab_nozzles)
        tree_frm.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        cols = ("Название", "Ресурс (г)", "Примечание")
        self.tree_nozzles = ttk.Treeview(tree_frm, columns=cols, show="headings")
        
        self.tree_nozzles.heading("Название", text="Название")
        self.tree_nozzles.column("Название", width=180, anchor="center")
        self.tree_nozzles.heading("Ресурс (г)", text="Ожидаемый ресурс (г)")
        self.tree_nozzles.column("Ресурс (г)", width=150, anchor="center")
        self.tree_nozzles.heading("Примечание", text="Примечание")
        self.tree_nozzles.column("Примечание", width=350, anchor="center")
        
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
        for i in self.tree_nozzles.get_children(): self.tree_nozzles.delete(i)
        for n in self.db.settings.get_all_nozzle_types():
            self.tree_nozzles.insert("", "end", iid=str(n["id"]), values=(
                n["Название"], fmt_float(n["Ожидаемый ресурс (г)"]), n["Примечание"] or ""
            ))

    def _nozzle_form(self, n_id=None):
        dialog = tk.Toplevel(self)
        dialog.title("Сопло")
        dialog.geometry("350x200")
        dialog.grab_set()

        ttk.Label(dialog, text="Название:").pack(pady=(10,2))
        e_name = ttk.Entry(dialog); e_name.pack(fill="x", padx=20)
        ttk.Label(dialog, text="Ожидаемый ресурс (г):").pack(pady=(5,2))
        e_res = ttk.Entry(dialog); e_res.pack(fill="x", padx=20)
        ttk.Label(dialog, text="Примечание:").pack(pady=(5,2))
        e_note = ttk.Entry(dialog); e_note.pack(fill="x", padx=20)

        if n_id:
            row = next((x for x in self.db.settings.get_all_nozzle_types() if x["id"] == n_id), None)
            if row:
                e_name.insert(0, row["Название"])
                e_res.insert(0, fmt_float(row["Ожидаемый ресурс (г)"]))
                e_note.insert(0, row["Примечание"] or "")

        def save():
            try:
                ok = self.db.settings.update_nozzle_type(n_id, e_name.get(), parse_float(e_res.get()), e_note.get()) if n_id else \
                     self.db.settings.add_nozzle_type(e_name.get(), parse_float(e_res.get()), e_note.get())
                if ok:
                    dialog.destroy(); self.refresh()
                else:
                    messagebox.showerror("Ошибка", "Не удалось (возможно дубликат).")
            except ValueError:
                messagebox.showerror("Ошибка", "Ресурс должен быть числом.")
        ttk.Button(dialog, text="Сохранить", command=save).pack(pady=15)

    def _add_nozzle(self): self._nozzle_form()
    def _edit_nozzle(self):
        sel = self.tree_nozzles.selection()
        if sel: self._nozzle_form(int(sel[0]))
    def _delete_nozzle(self):
        sel = self.tree_nozzles.selection()
        if sel and messagebox.askyesno("Удалить?", "Точно?"):
            self.db.settings.delete_nozzle_type(int(sel[0])); self.refresh()

    # =================================================================
    # ПОД-ВКЛАДКА 4: МАТРИЦА КОЭФФИЦИЕНТОВ
    # =================================================================
    def _build_matrix_ui(self):
        self.matrix_container = ttk.Frame(self.tab_matrix)
        self.matrix_container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(self.matrix_container, highlightthickness=0)
        self.scroll_y = ttk.Scrollbar(self.matrix_container, orient="vertical", command=self.canvas.yview)
        self.scroll_x = ttk.Scrollbar(self.matrix_container, orient="horizontal", command=self.canvas.xview)
        self.matrix_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.matrix_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.matrix_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.ctx_menu_cell = tk.Menu(self, tearoff=0)
        self.ctx_menu_cell.add_command(label="✏ Редактировать", command=self._edit_matrix_cell)
        self.ctx_menu_cell.add_command(label="📋 Копировать", command=self._copy_matrix_cell)
        self.active_cell_data = None

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._toggle_scrollbars()

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self._toggle_scrollbars()

    def _toggle_scrollbars(self):
        frame_width = self.matrix_frame.winfo_reqwidth()
        canvas_width = self.canvas.winfo_width()
        if frame_width > canvas_width:
            if not self.scroll_x.winfo_ismapped(): self.scroll_x.pack(side="bottom", fill="x")
        else:
            if self.scroll_x.winfo_ismapped(): self.scroll_x.pack_forget()

        frame_height = self.matrix_frame.winfo_reqheight()
        canvas_height = self.canvas.winfo_height()
        if frame_height > canvas_height:
            if not self.scroll_y.winfo_ismapped(): self.scroll_y.pack(side="right", fill="y")
        else:
            if self.scroll_y.winfo_ismapped(): self.scroll_y.pack_forget()

    def _redraw_matrix(self):
        for widget in self.matrix_frame.winfo_children(): widget.destroy()
        data = self.db.settings.get_wear_matrix()
        if not data:
            ttk.Label(self.matrix_frame, text="Нет данных (добавьте пластики и сопла).").grid(row=0, column=0, padx=10, pady=10)
            self._toggle_scrollbars()
            return

        nozzles = {r["n_id"]: r["n_name"] for r in data}
        plastics = {r["p_id"]: f"{r['p_base']} {r['p_mod']}".strip() for r in data}
        
        ttk.Label(self.matrix_frame, text="Пластик \\ Сопло", font=("", 9, "bold")).grid(row=0, column=0, padx=10, pady=5)
        for col, (nid, nname) in enumerate(nozzles.items(), start=1):
            ttk.Label(self.matrix_frame, text=nname, font=("", 9, "bold")).grid(row=0, column=col, padx=5, pady=5)

        for row, (pid, pname) in enumerate(plastics.items(), start=1):
            ttk.Label(self.matrix_frame, text=pname).grid(row=row, column=0, sticky="w", padx=10, pady=2)
            for col, nid in enumerate(nozzles.keys(), start=1):
                val = next((x["coeff"] for x in data if x["p_id"] == pid and x["n_id"] == nid), 1.0)
                lbl = ttk.Label(self.matrix_frame, text=fmt_float(val, 2), relief="flat", padding=4, anchor="center", width=8)
                lbl.grid(row=row, column=col, padx=2, pady=2)
                lbl.bind("<Button-3>", lambda e, p=pid, n=nid, v=val, w=lbl: self._show_cell_context_menu(e, p, n, v, w))
        
        self.canvas.update_idletasks()
        self._on_frame_configure()

    def _show_cell_context_menu(self, event, p_id, n_id, current_val, widget):
        self.active_cell_data = (p_id, n_id, current_val, widget)
        widget.configure(background="#e0e0e0")
        self.ctx_menu_cell.post(event.x_root, event.y_root)

    def _edit_matrix_cell(self):
        if not self.active_cell_data: return
        p_id, n_id, old_val, widget = self.active_cell_data
        widget.configure(background="")
        
        dialog = tk.Toplevel(self)
        dialog.title("Изменить коэффициент")
        dialog.geometry("250x120")
        dialog.grab_set()

        ttk.Label(dialog, text="Новое значение:").pack(pady=10)
        entry = ttk.Entry(dialog)
        entry.pack(padx=20, fill="x")
        entry.insert(0, fmt_float(old_val, 2))
        entry.focus_set()

        def save():
            try:
                new_val = parse_float(entry.get())
                if self.db.settings.set_wear_coefficient(p_id, n_id, new_val):
                    dialog.destroy(); self._redraw_matrix()
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить.")
            except ValueError:
                messagebox.showerror("Ошибка", "Введите число.")

        ttk.Button(dialog, text="Сохранить", command=save).pack(pady=10)

    def _copy_matrix_cell(self):
        if not self.active_cell_data: return
        p_id, n_id, old_val, widget = self.active_cell_data
        widget.configure(background="")
        self.clipboard_clear()
        self.clipboard_append(str(old_val))
        messagebox.showinfo("Скопировано", f"Значение '{old_val}' скопировано в буфер обмена.")

    # =================================================================
    # ПОД-ВКЛАДКА 5: ЦВЕТА
    # =================================================================
    def _build_colors_ui(self):
        tree_frm = ttk.Frame(self.tab_colors)
        tree_frm.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        # Первая колонка (#0) - это колонка дерева, мы спрячем её заголовок, но картинка ляжет именно туда
        cols = ("Название", "Группа", "Порядок", "HEX", "Примечание")
        self.tree_colors = ttk.Treeview(tree_frm, columns=cols) # убрали show="headings"
        
        # Настраиваем первую (скрытую) колонку
        self.tree_colors.heading("#0", text="Превью")
        self.tree_colors.column("#0", width=50, anchor="center", stretch=False)
        
        self.tree_colors.heading("Название", text="Название")
        self.tree_colors.column("Название", width=150, anchor="center")
        
        self.tree_colors.heading("Группа", text="Группа")
        self.tree_colors.column("Группа", width=120, anchor="center")
        
        self.tree_colors.heading("Порядок", text="Порядок")
        self.tree_colors.column("Порядок", width=80, anchor="center")
        
        self.tree_colors.heading("HEX", text="HEX (цвет)")
        self.tree_colors.column("HEX", width=100, anchor="center")
        
        self.tree_colors.heading("Примечание", text="Примечание")
        self.tree_colors.column("Примечание", width=250, anchor="center")
        
        scroll = ttk.Scrollbar(tree_frm, orient="vertical", command=self.tree_colors.yview)
        self.tree_colors.configure(yscrollcommand=scroll.set)
        
        self.tree_colors.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.ctx_menu_colors = tk.Menu(self, tearoff=0)
        self.ctx_menu_colors.add_command(label="✏ Изменить", command=self._edit_color)
        self.ctx_menu_colors.add_command(label="🗑 Удалить", command=self._delete_color)
        self.tree_colors.bind("<Button-3>", self._show_color_context_menu)

        frm_btns = ttk.Frame(self.tab_colors)
        frm_btns.pack(fill="x", padx=10, pady=5)
        ttk.Button(frm_btns, text="➕ Добавить", command=self._add_color).pack(side="right")

        self.color_icons = {}

    def _show_color_context_menu(self, event):
        item = self.tree_colors.identify_row(event.y)
        if item:
            self.tree_colors.selection_set(item)
            self.ctx_menu_colors.post(event.x_root, event.y_root)

    def _refresh_colors(self):
        for i in self.tree_colors.get_children(): 
            self.tree_colors.delete(i)
        self.color_icons.clear()

        for c in self.db.settings.get_all_colors():
            img = ""
            if c["HEX"] and c["HEX"].startswith("#") and len(c["HEX"]) == 7:
                try:
                    icon = tk.PhotoImage(width=16, height=16)
                    icon.put(c["HEX"], to=(0, 0, 16, 16))
                    self.color_icons[c["id"]] = icon
                    img = icon
                except tk.TclError:
                    img = ""

            # Важно: image=img передаётся отдельным аргументом, а не внутри values!
            self.tree_colors.insert("", "end", iid=str(c["id"]), image=img, values=(
                c["Название"], c["Группа"], c["Порядок"], c["HEX"] or "", c["Примечание"] or ""
            ))

    def _color_form(self, c_id=None):
        dialog = tk.Toplevel(self)
        dialog.title("Цвет")
        dialog.geometry("350x300")
        dialog.grab_set()

        ttk.Label(dialog, text="Название:").pack(pady=(10,2))
        e_name = ttk.Entry(dialog); e_name.pack(fill="x", padx=20)

        ttk.Label(dialog, text="Группа:").pack(pady=(5,2))
        combo_group = ttk.Combobox(dialog, values=["Ахроматические", "Тёплые", "Холодные", "Прозрачные", "Особые", "Прочее"], state="readonly")
        combo_group.pack(fill="x", padx=20)
        combo_group.current(5)

        ttk.Label(dialog, text="Порядок (цифра для сортировки):").pack(pady=(5,2))
        e_order = ttk.Entry(dialog); e_order.pack(fill="x", padx=20)
        e_order.insert(0, "100")

        ttk.Label(dialog, text="HEX (например, #FF0000):").pack(pady=(5,2))
        e_hex = ttk.Entry(dialog); e_hex.pack(fill="x", padx=20)

        ttk.Label(dialog, text="Примечание:").pack(pady=(5,2))
        e_note = ttk.Entry(dialog); e_note.pack(fill="x", padx=20)

        if c_id:
            row = next((x for x in self.db.settings.get_all_colors() if x["id"] == c_id), None)
            if row:
                e_name.insert(0, row["Название"])
                combo_group.set(row["Группа"])
                e_order.delete(0, tk.END); e_order.insert(0, str(row["Порядок"]))
                e_hex.insert(0, row["HEX"] or "")
                e_note.insert(0, row["Примечание"] or "")

        def save():
            try:
                order = int(e_order.get())
                hex_val = e_hex.get().strip()
                if hex_val and (not hex_val.startswith("#") or len(hex_val) != 7):
                    messagebox.showerror("Ошибка", "HEX должен быть в формате #RRGGBB (например, #FF0000)")
                    return
                ok = self.db.settings.update_color(c_id, e_name.get(), combo_group.get(), order, hex_val, e_note.get()) if c_id else \
                     self.db.settings.add_color(e_name.get(), combo_group.get(), order, hex_val, e_note.get())
                if ok:
                    dialog.destroy(); self.refresh()
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить (возможно дубликат).")
            except ValueError:
                messagebox.showerror("Ошибка", "Порядок должен быть целым числом.")
        ttk.Button(dialog, text="Сохранить", command=save).pack(pady=15)

    def _add_color(self): self._color_form()
    def _edit_color(self):
        sel = self.tree_colors.selection()
        if sel: self._color_form(int(sel[0]))
    def _delete_color(self):
        sel = self.tree_colors.selection()
        if sel and messagebox.askyesno("Удалить?", "Точно?"):
            self.db.settings.delete_color(int(sel[0])); self.refresh()

    # =================================================================
    # ОБНОВЛЕНИЕ
    # =================================================================
    def refresh(self):
        row = self.db.settings.get_tariffs()
        if row:
            self.combo_t_type.set(row["Тип тарифа на электричество"])
            self.entry_t_day.delete(0, tk.END); self.entry_t_day.insert(0, fmt_float(row["Цена 1кВт (руб)"]))
            self.entry_t_night.delete(0, tk.END)
            if row["Цена 1кВт ночь (руб)"] is not None:
                self.entry_t_night.insert(0, fmt_float(row["Цена 1кВт ночь (руб)"]))
            self.entry_defect.delete(0, tk.END); self.entry_defect.insert(0, fmt_float(row["% Брака"]))
            
            taxes = self.db.settings.get_all_tax_regimes()
            self.combo_tax["values"] = [t["Название"] for t in taxes]
            
            current_tax_id = row["Налоговый режим id"]
            for i, t in enumerate(taxes):
                if t["id"] == current_tax_id:
                    self.combo_tax.current(i)
                    break
            
            self._toggle_night_price()

        self._refresh_plastics()
        self._refresh_nozzles()
        self._redraw_matrix()
        self._refresh_colors()