# main.py
# Версия: v1.0 (baseline)
# Дата: финальная версия после серии правок (выравнивание заголовков,
#        обработка невалидных позиций, двойные кавычки в SQL, убрана Марка
#        из калькулятора и "Наша стоимость" из справочника пластиков).
import tkinter as tk
from tkinter import ttk, messagebox
from db_manager import DatabaseManager

DB_PATH = r"JobData.db"  # ЗАМЕНИ на свой путь


class PrintCostApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет 3D-печати и калькулятор себестоимости (v1.0)")
        self.root.geometry("1180x780")

        try:
            self.db = DatabaseManager(DB_PATH)
        except Exception as e:
            messagebox.showerror("Ошибка БД", f"Не удалось открыть базу:\n{e}")
            root.destroy()
            return

        self.plastic_types = {}       # {Название: id}
        self.plastic_type_names = []
        self.calc_rows = []           # строки калькулятора
        self.calc_rows_start_row = 1  # 0-я строка в grid занята заголовками

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_calc = ttk.Frame(self.notebook)
        self.tab_stock = ttk.Frame(self.notebook)
        self.tab_projects = ttk.Frame(self.notebook)
        self.tab_types = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_calc, text="🧮 Калькулятор")
        self.notebook.add(self.tab_stock, text="📦 Склад")
        self.notebook.add(self.tab_projects, text="📋 Проекты")
        self.notebook.add(self.tab_types, text="🎨 Виды пластика")

        self.build_calc_tab()
        self.build_stock_tab()
        self.build_projects_tab()
        self.build_types_tab()

        self.refresh_all()

    # ============================================================
    # Общие методы
    # ============================================================
    def refresh_all(self):
        self.load_plastic_types()
        self.load_stock_data()
        self.load_projects()
        self.load_types_data()

    def load_plastic_types(self):
        types = self.db.get_all_plastic_types()
        self.plastic_types = {row["Название"]: row["id"] for row in types}
        self.plastic_type_names = list(self.plastic_types.keys())

        for row in self.calc_rows:
            row["type"].configure(values=self.plastic_type_names)
            if row["type"].get() not in self.plastic_type_names:
                if self.plastic_type_names:
                    row["type"].current(0)
                else:
                    row["type"].set("")

    # ============================================================
    # ВКЛАДКА 1: КАЛЬКУЛЯТОР
    # ============================================================
    def build_calc_tab(self):
        # --- Параметры печати ---
        frm_params = ttk.LabelFrame(self.tab_calc, text="Параметры печати", padding=10)
        frm_params.pack(fill="x", padx=10, pady=5)

        ttk.Label(frm_params, text="Мощность принтера (Вт):").grid(row=0, column=0, sticky="w")
        self.entry_watts = ttk.Entry(frm_params, width=10)
        self.entry_watts.grid(row=0, column=1, padx=5)
        self.entry_watts.insert(0, "120")

        ttk.Label(frm_params, text="Время печати (ч):").grid(row=0, column=2, sticky="w", padx=(20, 0))
        self.entry_hours = ttk.Entry(frm_params, width=10)
        self.entry_hours.grid(row=0, column=3, padx=5)

        ttk.Label(frm_params, text="Тариф эл-ва (руб./кВт):").grid(row=0, column=4, sticky="w", padx=(20, 0))
        self.entry_tariff = ttk.Entry(frm_params, width=10)
        self.entry_tariff.grid(row=0, column=5, padx=5)
        self.entry_tariff.insert(0, f"{self.db.get_electricity_tariff():.2f}")

        ttk.Button(frm_params, text="💾 Сохранить тариф", command=self.save_tariff).grid(row=0, column=6, padx=10)

        # --- Таблица позиций ---
        frm_table = ttk.LabelFrame(self.tab_calc, text="Необходимый пластик", padding=10)
        frm_table.pack(fill="both", expand=True, padx=10, pady=5)

        # Один общий фрейм для заголовков И строк — grid выровняет колонки
        self.calc_grid = ttk.Frame(frm_table)
        self.calc_grid.pack(fill="x", anchor="nw")

        # Фиксированная ширина колонок
        self.calc_grid.columnconfigure(0, minsize=180)  # Вид пластика
        self.calc_grid.columnconfigure(1, minsize=180)  # Цвет
        self.calc_grid.columnconfigure(2, minsize=100)  # Вес
        self.calc_grid.columnconfigure(3, minsize=60)   # Кнопка

        headers = ["Вид пластика", "Цвет", "Вес (г)", "Действие"]
        for col, text in enumerate(headers):
            ttk.Label(self.calc_grid, text=text, font=("", 9, "bold")).grid(
                row=0, column=col, padx=5, pady=(0, 8), sticky="w"
            )

        # Кнопки строк
        frm_btns = ttk.Frame(frm_table)
        frm_btns.pack(fill="x", pady=(10, 0), anchor="w")
        ttk.Button(frm_btns, text="➕ Добавить позицию", command=self.add_calc_row).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🗑 Очистить", command=self.clear_calc_rows).pack(side="left", padx=5)

        # --- Кнопка расчёта ---
        ttk.Button(self.tab_calc, text="🧮 РАССЧИТАТЬ СЕБЕСТОИМОСТЬ",
                   command=self.calculate).pack(pady=10)

        # --- Результат ---
        frm_res = ttk.LabelFrame(self.tab_calc, text="Результат", padding=10)
        frm_res.pack(fill="both", expand=True, padx=10, pady=5)
        self.text_result = tk.Text(frm_res, height=12, bg="#f5f5f5",
                                   font=("Consolas", 10), wrap="word")
        self.text_result.pack(fill="both", expand=True)

        self.add_calc_row()

    def save_tariff(self):
        try:
            val = float(self.entry_tariff.get().replace(",", "."))
            if self.db.update_electricity_tariff(val):
                messagebox.showinfo("OK", "Тариф сохранён.")
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить.")
        except ValueError:
            messagebox.showerror("Ошибка", "Тариф должен быть числом.")

    def add_calc_row(self):
        row_idx = self.calc_rows_start_row + len(self.calc_rows)

        combo_type = ttk.Combobox(self.calc_grid, values=self.plastic_type_names,
                                  width=20, state="readonly")
        combo_type.grid(row=row_idx, column=0, padx=5, pady=2, sticky="w")
        if self.plastic_type_names:
            combo_type.current(0)

        entry_color = ttk.Entry(self.calc_grid, width=22)
        entry_color.grid(row=row_idx, column=1, padx=5, pady=2, sticky="w")

        entry_weight = ttk.Entry(self.calc_grid, width=12)
        entry_weight.grid(row=row_idx, column=2, padx=5, pady=2, sticky="w")

        btn_del = ttk.Button(self.calc_grid, text="✖", width=3,
                             command=lambda cw=combo_type: self.remove_calc_row(cw))
        btn_del.grid(row=row_idx, column=3, padx=5, pady=2, sticky="w")

        self.calc_rows.append({
            "type": combo_type,
            "color": entry_color,
            "weight": entry_weight,
            "btn": btn_del,
        })

    def remove_calc_row(self, combo_widget):
        if len(self.calc_rows) <= 1:
            messagebox.showinfo("Инфо", "Должна остаться хотя бы одна позиция.")
            return

        target = None
        for r in self.calc_rows:
            if r["type"] is combo_widget:
                target = r
                break
        if target is None:
            return

        for key in ("type", "color", "weight", "btn"):
            target[key].destroy()
        self.calc_rows.remove(target)

        # Перенумеровываем оставшиеся строки, чтобы не было дырок в grid
        for idx, r in enumerate(self.calc_rows):
            new_row = self.calc_rows_start_row + idx
            r["type"].grid_configure(row=new_row)
            r["color"].grid_configure(row=new_row)
            r["weight"].grid_configure(row=new_row)
            r["btn"].grid_configure(row=new_row)

    def clear_calc_rows(self):
        for r in self.calc_rows:
            for key in ("type", "color", "weight", "btn"):
                r[key].destroy()
        self.calc_rows = []
        self.add_calc_row()

    def calculate(self):
        try:
            watts = float(self.entry_watts.get().replace(",", "."))
            hours = float(self.entry_hours.get().replace(",", "."))
            tariff = float(self.entry_tariff.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Ошибка", "Мощность, время и тариф — числа.")
            return

        cost_electricity = (watts / 1000.0) * hours * tariff

        self.text_result.delete("1.0", tk.END)
        self.text_result.insert(tk.END, "=== РАСЧЁТ СЕБЕСТОИМОСТИ ===\n\n")

        total_plastic_cost = 0.0
        total_market_cost = 0.0
        problems = []

        for i, row in enumerate(self.calc_rows, 1):
            type_name = row["type"].get().strip()
            color = row["color"].get().strip()
            w_str = row["weight"].get().strip().replace(",", ".")

            if not type_name or not w_str:
                continue
            try:
                need_grams = float(w_str)
            except ValueError:
                self.text_result.insert(tk.END, f"[{i}] {type_name}: ❌ неверный вес\n\n")
                problems.append(f"[{i}] {type_name} / {color}: неверный вес")
                continue

            self.text_result.insert(
                tk.END, f"[{i}] {type_name} / {color or '—'} / {need_grams} г\n"
            )

            plastic_id = self.plastic_types.get(type_name)
            if not plastic_id:
                self.text_result.insert(tk.END, "    ❌ Вид пластика не найден в справочнике\n\n")
                problems.append(f"[{i}] {type_name}: вид пластика отсутствует в БД")
                continue

            # --- Поиск на складе ---
            spools = self.db.find_spools_by_type_color(plastic_id, color)
            remaining = need_grams
            cost_row = 0.0
            found_something = False

            for spool in spools:
                if remaining <= 0:
                    break
                stock = spool["Приблизительный остаток (г)"] or 0
                if stock <= 0:
                    continue
                take = min(remaining, stock)
                ppg = spool["Себестоимость 1г пластика (руб.)"] or 0.0
                part = take * ppg
                cost_row += part
                remaining -= take
                found_something = True

                spool_label = f"ID #{spool['Внутренний ID']}"
                spool_desc = f"{spool['Марка'] or '—'} / {spool['Цвет']}"
                self.text_result.insert(
                    tk.END,
                    f"    ✅ Со склада ({spool_label}, {spool_desc}): "
                    f"{take:.1f} г × {ppg:.4f} ₽/г = {part:.2f} ₽\n",
                )

            # --- Добор у поставщиков ---
            if remaining > 0:
                self.text_result.insert(
                    tk.END, f"    ⚠️ Не хватает {remaining:.1f} г на складе. Ищу у поставщиков...\n"
                )
                suppliers = self.db.find_supplier_prices(plastic_id, color)

                total_suppliers = len(suppliers)
                with_weight = []
                for s in suppliers:
                    weight = float(s["Вес катушки"] or 0)
                    if weight > 0:
                        with_weight.append(s)

                if total_suppliers == 0:
                    self.text_result.insert(
                        tk.END, "    ❌ У поставщиков тоже нет такой позиции.\n"
                    )
                    problems.append(
                        f"[{i}] {type_name} / {color}: нет ни на складе, ни у поставщиков"
                    )
                    self.text_result.insert(tk.END, "\n")
                    continue

                if not with_weight:
                    self.text_result.insert(
                        tk.END,
                        f"    ❌ У поставщиков {total_suppliers} записей, но ни у одной "
                        f"не указан вес катушки — расчёт невозможен.\n"
                    )
                    problems.append(
                        f"[{i}] {type_name} / {color}: у поставщиков нет данных о весе катушки"
                    )
                    self.text_result.insert(tk.END, "\n")
                    continue

                best = None
                for s in with_weight:
                    price = float(s["Цена"] or 0)
                    weight = float(s["Вес катушки"] or 0)
                    ppg = price / weight
                    if best is None or ppg < best["ppg"]:
                        best = {
                            "ppg": ppg,
                            "price": price,
                            "weight": weight,
                            "link": s["Ссылка"] or "—",
                            "brand": s["Марка"] or "—",
                        }

                part = remaining * best["ppg"]
                cost_row += part
                found_something = True
                self.text_result.insert(
                    tk.END,
                    f"    🛒 У поставщика ({best['brand']}): {remaining:.1f} г × "
                    f"{best['ppg']:.4f} ₽/г = {part:.2f} ₽\n"
                    f"       (катушка {best['weight']:.0f} г за {best['price']:.2f} ₽, "
                    f"ссылка: {best['link']})\n",
                )

            if not found_something:
                self.text_result.insert(tk.END, "\n")
                continue

            # --- Рыночная стоимость для сравнения (только для рассчитанных позиций) ---
            type_info = self.db.get_plastic_type_info(plastic_id)
            market_ppg = float(type_info["Рыночная стоимость (руб./г)"] or 0) if type_info else 0.0
            if market_ppg > 0:
                market_row = market_ppg * need_grams
                total_market_cost += market_row
                self.text_result.insert(
                    tk.END,
                    f"    📊 Рыночная стоимость: {market_row:.2f} ₽ "
                    f"({market_ppg:.2f} ₽/г), твоя себестоимость по пластику: {cost_row:.2f} ₽ "
                    f"(разница: {market_row - cost_row:+.2f} ₽)\n",
                )

            total_plastic_cost += cost_row
            self.text_result.insert(tk.END, "\n")

        # ==================== ИТОГ ====================
        total = cost_electricity + total_plastic_cost
        self.text_result.insert(tk.END, "=" * 60 + "\n")
        self.text_result.insert(tk.END, f"Электричество:             {cost_electricity:>8.2f} ₽\n")
        self.text_result.insert(tk.END, f"Пластик (себестоимость):   {total_plastic_cost:>8.2f} ₽\n")
        self.text_result.insert(tk.END, "-" * 60 + "\n")

        if problems:
            self.text_result.insert(
                tk.END, f"ИТОГО (неполно):           {total:>8.2f} ₽\n"
            )
            self.text_result.insert(tk.END, "\n")
            self.text_result.insert(
                tk.END,
                "⚠️ ВНИМАНИЕ: не все позиции удалось рассчитать.\n"
                "Итог неполный, потому что:\n",
            )
            for p in problems:
                self.text_result.insert(tk.END, f"   • {p}\n")
        else:
            self.text_result.insert(tk.END, f"ИТОГО СЕБЕСТОИМОСТЬ:       {total:>8.2f} ₽\n")
            if total_market_cost > 0:
                self.text_result.insert(
                    tk.END,
                    f"Рыночная стоимость печати: {total_market_cost:>8.2f} ₽\n"
                    f"Разница (рынок − себест.): {total_market_cost - total:>+8.2f} ₽\n",
                )

        if problems:
            messagebox.showwarning(
                "Неполный расчёт",
                "Некоторые позиции не удалось рассчитать.\n"
                "Подробности — в окне результата.",
            )

    # ============================================================
    # ВКЛАДКА 2: СКЛАД
    # ============================================================
    def build_stock_tab(self):
        columns = ("ID", "Вид", "Марка", "Цвет", "Цена катушки", "Вес", "Остаток", "Себест/г")
        self.tree_stock = ttk.Treeview(self.tab_stock, columns=columns, show="headings", height=18)
        widths = (50, 90, 110, 100, 100, 80, 90, 90)
        for col, w in zip(columns, widths):
            self.tree_stock.heading(col, text=col)
            self.tree_stock.column(col, width=w, anchor="center")
        self.tree_stock.pack(fill="both", expand=True, padx=10, pady=10)

        frm_btns = ttk.Frame(self.tab_stock)
        frm_btns.pack(fill="x", padx=10, pady=5)
        ttk.Button(frm_btns, text="➕ Добавить катушку", command=self.add_spool_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="✏ Изменить остаток", command=self.edit_stock_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🗑 Удалить", command=self.delete_selected_spool).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🔄 Обновить", command=self.load_stock_data).pack(side="left", padx=5)

    def load_stock_data(self):
        for i in self.tree_stock.get_children():
            self.tree_stock.delete(i)
        for s in self.db.get_all_spools():
            self.tree_stock.insert("", "end", iid=str(s["Внутренний ID"]), values=(
                s["Внутренний ID"],
                s["Вид пластика"],
                s["Марка"] or "",
                s["Цвет"],
                f"{s['Стоимость катушки (RUB)']:.2f}",
                f"{s['Заявленный вес пластика (г)']:.0f}",
                f"{s['Приблизительный остаток (г)'] or 0:.1f}",
                f"{s['Себестоимость 1г пластика (руб.)']:.4f}",
            ))

    def add_spool_dialog(self):
        if not self.plastic_type_names:
            messagebox.showerror("Ошибка", "Сначала добавь хотя бы один вид пластика.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить катушку")
        dialog.geometry("360x400")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Вид пластика:").pack(pady=(10, 2))
        combo_type = ttk.Combobox(dialog, values=self.plastic_type_names, state="readonly")
        combo_type.pack()
        combo_type.current(0)

        ttk.Label(dialog, text="Марка (производитель):").pack(pady=(10, 2))
        entry_brand = ttk.Entry(dialog)
        entry_brand.pack()

        ttk.Label(dialog, text="Цвет:").pack(pady=(10, 2))
        entry_color = ttk.Entry(dialog)
        entry_color.pack()

        ttk.Label(dialog, text="Стоимость катушки (руб.):").pack(pady=(10, 2))
        entry_cost = ttk.Entry(dialog)
        entry_cost.pack()

        ttk.Label(dialog, text="Заявленный вес (г):").pack(pady=(10, 2))
        entry_weight = ttk.Entry(dialog)
        entry_weight.pack()

        def save():
            try:
                type_id = self.plastic_types[combo_type.get()]
                brand = entry_brand.get().strip()
                color = entry_color.get().strip()
                cost = float(entry_cost.get().replace(",", "."))
                weight = float(entry_weight.get().replace(",", "."))
                if not color:
                    messagebox.showerror("Ошибка", "Цвет обязателен.")
                    return
                if self.db.add_spool(type_id, brand, color, cost, weight):
                    messagebox.showinfo("OK", "Катушка добавлена.")
                    dialog.destroy()
                    self.load_stock_data()
                else:
                    messagebox.showerror("Ошибка", "Не удалось добавить.")
            except ValueError:
                messagebox.showerror("Ошибка", "Проверь числа.")
            except KeyError:
                messagebox.showerror("Ошибка", "Выбери вид пластика.")

        ttk.Button(dialog, text="💾 Сохранить", command=save).pack(pady=20)

    def edit_stock_dialog(self):
        sel = self.tree_stock.selection()
        if not sel:
            messagebox.showinfo("Инфо", "Выбери катушку в таблице.")
            return
        spool_id = int(sel[0])

        current = None
        for s in self.db.get_all_spools():
            if s["Внутренний ID"] == spool_id:
                current = s
                break
        if not current:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Катушка #{spool_id}")
        dialog.geometry("320x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Новый остаток (г):").pack(pady=(15, 5))
        entry = ttk.Entry(dialog)
        entry.pack()
        entry.insert(0, f"{current['Приблизительный остаток (г)'] or 0:.1f}")

        def save():
            try:
                val = float(entry.get().replace(",", "."))
                if self.db.update_spool_stock(spool_id, val):
                    dialog.destroy()
                    self.load_stock_data()
            except ValueError:
                messagebox.showerror("Ошибка", "Число, пожалуйста.")

        ttk.Button(dialog, text="💾 Сохранить", command=save).pack(pady=20)

    def delete_selected_spool(self):
        sel = self.tree_stock.selection()
        if not sel:
            return
        spool_id = int(sel[0])
        if not messagebox.askyesno("Удалить?", f"Удалить катушку #{spool_id}?"):
            return
        if self.db.delete_spool(spool_id):
            self.load_stock_data()
        else:
            messagebox.showerror("Ошибка", "Возможно, катушка используется в истории печати.")

    # ============================================================
    # ВКЛАДКА 3: ПРОЕКТЫ
    # ============================================================
    def build_projects_tab(self):
        columns = ("ID", "Название", "Заказчик", "Статус", "Цена", "Дата")
        self.tree_projects = ttk.Treeview(self.tab_projects, columns=columns, show="headings", height=18)
        widths = (50, 250, 150, 100, 100, 140)
        for col, w in zip(columns, widths):
            self.tree_projects.heading(col, text=col)
            self.tree_projects.column(col, width=w, anchor="center")
        self.tree_projects.pack(fill="both", expand=True, padx=10, pady=10)

        frm_btns = ttk.Frame(self.tab_projects)
        frm_btns.pack(fill="x", padx=10, pady=5)
        ttk.Button(frm_btns, text="➕ Новый проект", command=self.add_project_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="💰 Задать цену", command=self.set_project_price_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="📜 История печати", command=self.show_project_history).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🔄 Обновить", command=self.load_projects).pack(side="left", padx=5)

    def load_projects(self):
        for i in self.tree_projects.get_children():
            self.tree_projects.delete(i)
        for p in self.db.get_all_projects():
            self.tree_projects.insert("", "end", iid=str(p["id"]), values=(
                p["id"],
                p["Название"],
                p["Заказчик"] or "",
                p["Статус"] or "",
                f"{p['Цена']:.2f}" if p["Цена"] is not None else "",
                p["Дата создания"] or "",
            ))

    def add_project_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Новый проект")
        dialog.geometry("340x260")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Название:").pack(pady=(10, 2))
        entry_name = ttk.Entry(dialog)
        entry_name.pack(fill="x", padx=20)

        ttk.Label(dialog, text="Заказчик:").pack(pady=(10, 2))
        entry_customer = ttk.Entry(dialog)
        entry_customer.pack(fill="x", padx=20)

        ttk.Label(dialog, text="Статус:").pack(pady=(10, 2))
        combo_status = ttk.Combobox(dialog, values=["В работе", "Завершён", "Отменён", "Черновик"])
        combo_status.pack(fill="x", padx=20)
        combo_status.current(0)

        def save():
            name = entry_name.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Название обязательно.")
                return
            if self.db.add_project(name, entry_customer.get().strip(), combo_status.get()):
                dialog.destroy()
                self.load_projects()
            else:
                messagebox.showerror("Ошибка", "Не удалось создать проект.")

        ttk.Button(dialog, text="💾 Сохранить", command=save).pack(pady=15)

    def set_project_price_dialog(self):
        sel = self.tree_projects.selection()
        if not sel:
            messagebox.showinfo("Инфо", "Выбери проект.")
            return
        project_id = int(sel[0])
        project = self.db.get_project(project_id)
        if not project:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Цена проекта #{project_id}")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Цена (руб.):").pack(pady=(15, 5))
        entry = ttk.Entry(dialog)
        entry.pack()
        if project["Цена"] is not None:
            entry.insert(0, f"{project['Цена']:.2f}")

        def save():
            try:
                val = float(entry.get().replace(",", "."))
                if self.db.update_project_price(project_id, val):
                    dialog.destroy()
                    self.load_projects()
            except ValueError:
                messagebox.showerror("Ошибка", "Число, пожалуйста.")

        ttk.Button(dialog, text="💾 Сохранить", command=save).pack(pady=15)

    def show_project_history(self):
        sel = self.tree_projects.selection()
        if not sel:
            messagebox.showinfo("Инфо", "Выбери проект.")
            return
        project_id = int(sel[0])

        dialog = tk.Toplevel(self.root)
        dialog.title(f"История печати проекта #{project_id}")
        dialog.geometry("900x400")
        dialog.transient(self.root)

        columns = ("Дата", "Вид", "Марка", "Цвет", "Катушка", "Грамм", "Факт", "Результат")
        tree = ttk.Treeview(dialog, columns=columns, show="headings", height=15)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for h in self.db.get_project_history(project_id):
            tree.insert("", "end", values=(
                h["Дата события"],
                h["Вид пластика"],
                h["Марка"] or "",
                h["Цвет"] or "",
                f"#{h['id катушки']}",
                f"{h['Количество (г)']:.1f}",
                f"{h['Фактический расход (г)']:.1f}" if h["Фактический расход (г)"] is not None else "",
                h["Результат"] or "",
            ))

    # ============================================================
    # ВКЛАДКА 4: ВИДЫ ПЛАСТИКА
    # ============================================================
    def build_types_tab(self):
        columns = ("ID", "Название", "Рыночная стоимость (руб./г)", "Заметки")
        self.tree_types = ttk.Treeview(self.tab_types, columns=columns, show="headings", height=18)
        widths = (50, 150, 200, 400)
        for col, w in zip(columns, widths):
            self.tree_types.heading(col, text=col)
            self.tree_types.column(col, width=w, anchor="center")
        self.tree_types.pack(fill="both", expand=True, padx=10, pady=10)

        frm_btns = ttk.Frame(self.tab_types)
        frm_btns.pack(fill="x", padx=10, pady=5)
        ttk.Button(frm_btns, text="➕ Добавить", command=self.add_type_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="✏ Изменить", command=self.edit_type_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🗑 Удалить", command=self.delete_selected_type).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🔄 Обновить", command=self.load_types_data).pack(side="left", padx=5)

    def load_types_data(self):
        for i in self.tree_types.get_children():
            self.tree_types.delete(i)
        for t in self.db.get_all_plastic_types():
            self.tree_types.insert("", "end", iid=str(t["id"]), values=(
                t["id"],
                t["Название"],
                f"{t['Рыночная стоимость (руб./г)']:.4f}" if t["Рыночная стоимость (руб./г)"] is not None else "0",
                t["Заметки"] or "",
            ))

    def add_type_dialog(self):
        self._type_form(None)

    def edit_type_dialog(self):
        sel = self.tree_types.selection()
        if not sel:
            messagebox.showinfo("Инфо", "Выбери вид пластика.")
            return
        self._type_form(int(sel[0]))

    def _type_form(self, type_id):
        dialog = tk.Toplevel(self.root)
        dialog.title("Вид пластика" + (f" #{type_id}" if type_id else ""))
        dialog.geometry("360x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Название (например, PLA):").pack(pady=(15, 2))
        entry_name = ttk.Entry(dialog)
        entry_name.pack(fill="x", padx=20)

        ttk.Label(dialog, text="Рыночная стоимость (руб./г):").pack(pady=(10, 2))
        entry_price = ttk.Entry(dialog)
        entry_price.pack(fill="x", padx=20)

        ttk.Label(dialog, text="Заметки:").pack(pady=(10, 2))
        entry_notes = ttk.Entry(dialog)
        entry_notes.pack(fill="x", padx=20)

        if type_id:
            info = self.db.get_plastic_type_info(type_id)
            if info:
                entry_name.insert(0, info["Название"])
                if info["Рыночная стоимость (руб./г)"] is not None:
                    entry_price.insert(0, f"{info['Рыночная стоимость (руб./г)']:.4f}")
                entry_notes.insert(0, info["Заметки"] or "")

        def save():
            try:
                name = entry_name.get().strip()
                price = float(entry_price.get().replace(",", ".") or 0)
                notes = entry_notes.get().strip()
                if not name:
                    messagebox.showerror("Ошибка", "Название обязательно.")
                    return
                if type_id:
                    ok = self.db.update_plastic_type(type_id, name, price, notes)
                else:
                    ok = self.db.add_plastic_type(name, price, notes)
                if ok:
                    dialog.destroy()
                    self.refresh_all()
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить (возможно, такое название уже есть).")
            except ValueError:
                messagebox.showerror("Ошибка", "Стоимость — число.")

        ttk.Button(dialog, text="💾 Сохранить", command=save).pack(pady=20)

    def delete_selected_type(self):
        sel = self.tree_types.selection()
        if not sel:
            return
        type_id = int(sel[0])
        if not messagebox.askyesno("Удалить?", "Удалить вид пластика?\n"
                                                  "Если он используется — удаление не сработает."):
            return
        if self.db.delete_plastic_type(type_id):
            self.refresh_all()
        else:
            messagebox.showerror("Ошибка", "Вид пластика используется в других таблицах.")


if __name__ == "__main__":
    root = tk.Tk()
    app = PrintCostApp(root)
    root.mainloop()