# main.py
# Версия: v1.1 — добавлена вкладка "Типы сопел"
import tkinter as tk
from tkinter import ttk, messagebox
from db_manager import DatabaseManager

DB_PATH = r"JobData.db"


class PrintCostApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет 3D-печати и калькулятор себестоимости (v1.1)")
        self.root.geometry("1180x780")

        try:
            self.db = DatabaseManager(DB_PATH)
        except Exception as e:
            messagebox.showerror("Ошибка БД", f"Не удалось открыть базу:\n{e}")
            root.destroy()
            return

        self.plastic_types = {}
        self.plastic_type_names = []
        self.calc_rows = []
        self.calc_rows_start_row = 1

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        # ==== Вкладки ====
        self.tab_calc = ttk.Frame(self.notebook)
        self.tab_stock = ttk.Frame(self.notebook)
        self.tab_projects = ttk.Frame(self.notebook)
        self.tab_types = ttk.Frame(self.notebook)
        self.tab_nozzle_types = ttk.Frame(self.notebook)
        self.tab_nozzles = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_calc, text="🧮 Калькулятор")
        self.notebook.add(self.tab_stock, text="📦 Склад")
        self.notebook.add(self.tab_projects, text="📋 Проекты")
        self.notebook.add(self.tab_types, text="🎨 Виды пластика")
        self.notebook.add(self.tab_nozzle_types, text="🔧 Типы сопел")
        self.notebook.add(self.tab_nozzles, text="🔩 Сопла")

        # ==== Построение UI вкладок ====
        self.build_calc_tab()
        self.build_stock_tab()
        self.build_projects_tab()
        self.build_types_tab()
        self.build_nozzle_types_tab()
        self.build_nozzles_tab()

        # ==== Первичная загрузка данных ====
        self.refresh_all()

    # ============================================================
    # Общие методы
    # ============================================================
    def refresh_all(self):
        self.load_plastic_types()
        self.load_stock_data()
        self.load_projects()
        self.load_types_data()
        self.load_nozzle_types_data()
        self.load_nozzles_data()

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
        self.load_nozzles_into_combo()

    def load_nozzles_into_combo(self):
        """Заполняет выпадающий список сопел в калькуляторе."""
        nozzles = self.db.get_all_nozzles()
        self.nozzle_list = [n for n in nozzles if n["Статус"] == "В работе"]
        # Формируем отображаемые строки: "ID #N — Тип (остаток г)"
        display = []
        for n in self.nozzle_list:
            остаток = n["Остаток"] or 0
            display.append(f"#{n['id']} — {n['Тип']} (остаток {остаток:.0f} г)")
        self.combo_nozzle["values"] = display

        if display:
            # По умолчанию первое (с минимальным остатком, они уже отсортированы)
            self.combo_nozzle.current(0)
        else:
            self.combo_nozzle.set("")

    # ============================================================
    # ВКЛАДКА 1: КАЛЬКУЛЯТОР
    # ============================================================
    def build_calc_tab(self):
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

        ttk.Button(frm_params, text="💾 Сохранить тариф",
                command=self.save_tariff).grid(row=0, column=6, padx=10)

        # ==== Вторая строка параметров ====
        ttk.Label(frm_params, text="Стоимость принтера (руб):").grid(
            row=1, column=0, sticky="w", pady=(8, 0))
        self.entry_printer_cost = ttk.Entry(frm_params, width=10)
        self.entry_printer_cost.grid(row=1, column=1, padx=5, pady=(8, 0))
        self.entry_printer_cost.insert(0, f"{self.db.get_printer_cost():.2f}")

        ttk.Label(frm_params, text="Часы до кап. ремонта:").grid(
            row=1, column=2, sticky="w", padx=(20, 0), pady=(8, 0))
        self.entry_printer_hours = ttk.Entry(frm_params, width=10)
        self.entry_printer_hours.grid(row=1, column=3, padx=5, pady=(8, 0))
        self.entry_printer_hours.insert(0, f"{self.db.get_printer_hours_to_overhaul():.0f}")

        ttk.Button(frm_params, text="💾 Сохранить",
                command=self.save_printer_params).grid(row=1, column=4, padx=10, pady=(8, 0))

        # ==== Третья строка: сопло и брак ====
        ttk.Label(frm_params, text="Активное сопло:").grid(
            row=2, column=0, sticky="w", pady=(8, 0))
        self.combo_nozzle = ttk.Combobox(frm_params, width=30, state="readonly")
        self.combo_nozzle.grid(row=2, column=1, columnspan=2, padx=5, pady=(8, 0), sticky="w")

        ttk.Label(frm_params, text="Брак (%):").grid(
            row=2, column=3, sticky="w", padx=(20, 0), pady=(8, 0))
        self.entry_defect = ttk.Entry(frm_params, width=10)
        self.entry_defect.grid(row=2, column=4, padx=5, pady=(8, 0), sticky="w")
        self.entry_defect.insert(0, "10")

        frm_table = ttk.LabelFrame(self.tab_calc, text="Необходимый пластик", padding=10)
        frm_table.pack(fill="both", expand=True, padx=10, pady=5)

        self.calc_grid = ttk.Frame(frm_table)
        self.calc_grid.pack(fill="x", anchor="nw")

        self.calc_grid.columnconfigure(0, minsize=180)
        self.calc_grid.columnconfigure(1, minsize=180)
        self.calc_grid.columnconfigure(2, minsize=100)
        self.calc_grid.columnconfigure(3, minsize=60)

        headers = ["Вид пластика", "Цвет", "Вес (г)", "Действие"]
        for col, text in enumerate(headers):
            ttk.Label(self.calc_grid, text=text, font=("", 9, "bold")).grid(
                row=0, column=col, padx=5, pady=(0, 8), sticky="w"
            )

        frm_btns = ttk.Frame(frm_table)
        frm_btns.pack(fill="x", pady=(10, 0), anchor="w")
        ttk.Button(frm_btns, text="➕ Добавить позицию",
                   command=self.add_calc_row).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🗑 Очистить",
                   command=self.clear_calc_rows).pack(side="left", padx=5)

        ttk.Button(self.tab_calc, text="🧮 РАССЧИТАТЬ СЕБЕСТОИМОСТЬ",
                   command=self.calculate).pack(pady=10)

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

    def save_printer_params(self):
        try:
            cost = float(self.entry_printer_cost.get().replace(",", "."))
            hours = float(self.entry_printer_hours.get().replace(",", "."))
            if self.db.update_printer_params(cost, hours):
                messagebox.showinfo("OK", "Параметры принтера сохранены.")
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить.")
        except ValueError:
            messagebox.showerror("Ошибка", "Стоимость и часы — числа.")

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
        # ==== Читаем параметры ====
        try:
            watts = float(self.entry_watts.get().replace(",", "."))
            hours = float(self.entry_hours.get().replace(",", "."))
            tariff = float(self.entry_tariff.get().replace(",", "."))
            printer_cost = float(self.entry_printer_cost.get().replace(",", "."))
            printer_hours = float(self.entry_printer_hours.get().replace(",", "."))
            defect_pct = float(self.entry_defect.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Ошибка", "Проверь числа в параметрах.")
            return

        # ==== Электричество ====
        cost_electricity = (watts / 1000.0) * hours * tariff

        # ==== Принтер ====
        if printer_hours > 0:
            cost_printer = hours * (printer_cost / printer_hours)
        else:
            cost_printer = 0.0

        # ==== Какое сопло используем ====
        nozzle_id = None
        nozzle_label = "—"
        if self.combo_nozzle.get() and self.nozzle_list:
            try:
                idx = self.combo_nozzle.current()
                if idx >= 0:
                    nozzle_id = self.nozzle_list[idx]["id"]
                    nozzle_label = f"#{nozzle_id} ({self.nozzle_list[idx]['Тип']})"
            except Exception:
                pass

        self.text_result.delete("1.0", tk.END)
        self.text_result.insert(tk.END, "=== РАСЧЁТ СЕБЕСТОИМОСТИ ===\n\n")

        total_plastic_cost = 0.0
        total_nozzle_cost = 0.0
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

            # ==== Пластик ====
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

            # ==== Поставщики (если не хватает) ====
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

            # ==== Амортизация сопла (для этой позиции) ====
            if nozzle_id:
                nozzle_cost = self.db.calculate_nozzle_cost(
                    nozzle_id, plastic_id, need_grams
                )
                if nozzle_cost > 0:
                    total_nozzle_cost += nozzle_cost
                    self.text_result.insert(
                        tk.END,
                        f"    🔩 Амортизация сопла: {nozzle_cost:.2f} ₽\n"
                    )

            # ==== Рыночная стоимость ====
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

        # ==== Подытог ====
        subtotal = (total_plastic_cost + cost_electricity
                    + total_nozzle_cost + cost_printer)
        # ==== Накрутка на брак ====
        defect_multiplier = 1.0 + (defect_pct / 100.0)
        total = subtotal * defect_multiplier
        cost_defect = total - subtotal

        # ==== Вывод ====
        self.text_result.insert(tk.END, "=" * 60 + "\n")
        self.text_result.insert(tk.END, f"Пластик (себестоимость):   {total_plastic_cost:>8.2f} ₽\n")
        self.text_result.insert(tk.END, f"Электричество:             {cost_electricity:>8.2f} ₽\n")
        if nozzle_id:
            self.text_result.insert(tk.END, f"Амортизация сопла:         {total_nozzle_cost:>8.2f} ₽   (сопло {nozzle_label})\n")
        if cost_printer > 0:
            self.text_result.insert(tk.END, f"Амортизация принтера:      {cost_printer:>8.2f} ₽\n")
        self.text_result.insert(tk.END, "-" * 60 + "\n")
        self.text_result.insert(tk.END, f"Подытог:                   {subtotal:>8.2f} ₽\n")
        self.text_result.insert(
            tk.END,
            f"Брак ({defect_pct:.1f}%):              +{cost_defect:>7.2f} ₽\n"
        )
        self.text_result.insert(tk.END, "=" * 60 + "\n")

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
        ttk.Button(frm_btns, text="➕ Добавить катушку",
                   command=self.add_spool_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="✏ Изменить остаток",
                   command=self.edit_stock_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🗑 Удалить",
                   command=self.delete_selected_spool).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🔄 Обновить",
                   command=self.load_stock_data).pack(side="left", padx=5)

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
        ttk.Button(frm_btns, text="➕ Новый проект",
                   command=self.add_project_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="💰 Задать цену",
                   command=self.set_project_price_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="📜 История печати",
                   command=self.show_project_history).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🔄 Обновить",
                   command=self.load_projects).pack(side="left", padx=5)

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
        ttk.Button(frm_btns, text="➕ Добавить",
                   command=self.add_type_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="✏ Изменить",
                   command=self.edit_type_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🗑 Удалить",
                   command=self.delete_selected_type).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🔄 Обновить",
                   command=self.load_types_data).pack(side="left", padx=5)

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

    # ============================================================
    # ВКЛАДКА 5: ТИПЫ СОПЕЛ
    # ============================================================
    def build_nozzle_types_tab(self):
        columns = ("ID", "Название", "Материал", "Ø (мм)", "Ресурс (г)",
                   "PLA", "PLA+", "PLA-CF", "PLA-GF",
                   "PETG", "PETG+", "PETG-CF", "PETG-GF",
                   "ABS", "ABS-CF", "ABS-GF",
                   "ASA", "ASA-CF",
                   "TPU 95A", "TPU 98A", "TPU 85A", "TPU 75D")
        self.tree_nozzle_types = ttk.Treeview(
            self.tab_nozzle_types, columns=columns, show="headings", height=18
        )
        widths = (40, 130, 90, 60, 80,
                  45, 50, 55, 55,
                  50, 55, 60, 60,
                  45, 55, 55,
                  45, 55,
                  60, 60, 60, 60)
        for col, w in zip(columns, widths):
            self.tree_nozzle_types.heading(col, text=col)
            self.tree_nozzle_types.column(col, width=w, anchor="center")

        h_scroll = ttk.Scrollbar(self.tab_nozzle_types, orient="horizontal",
                                 command=self.tree_nozzle_types.xview)
        self.tree_nozzle_types.configure(xscrollcommand=h_scroll.set)

        self.tree_nozzle_types.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        h_scroll.pack(fill="x", padx=10)

        frm_btns = ttk.Frame(self.tab_nozzle_types)
        frm_btns.pack(fill="x", padx=10, pady=5)
        ttk.Button(frm_btns, text="➕ Добавить тип",
                   command=self.add_nozzle_type_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="✏ Изменить",
                   command=self.edit_nozzle_type_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🗑 Удалить",
                   command=self.delete_selected_nozzle_type).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🔄 Обновить",
                   command=self.load_nozzle_types_data).pack(side="left", padx=5)

    def load_nozzle_types_data(self):
        for i in self.tree_nozzle_types.get_children():
            self.tree_nozzle_types.delete(i)
        for t in self.db.get_all_nozzle_types():
            self.tree_nozzle_types.insert("", "end", iid=str(t["id"]), values=(
                t["id"],
                t["Название"],
                t["Материал"] or "",
                f"{t['Диаметр (мм)']:.2f}" if t["Диаметр (мм)"] is not None else "",
                f"{t['Ресурс (г)']:.0f}" if t["Ресурс (г)"] is not None else "",
                f"{t['Коэф. износа PLA']:.2f}",
                f"{t['Коэф. износа PLA+']:.2f}",
                f"{t['Коэф. износа PLA-CF']:.2f}",
                f"{t['Коэф. износа PLA-GF']:.2f}",
                f"{t['Коэф. износа PETG']:.2f}",
                f"{t['Коэф. износа PETG+']:.2f}",
                f"{t['Коэф. износа PETG-CF']:.2f}",
                f"{t['Коэф. износа PETG-GF']:.2f}",
                f"{t['Коэф. износа ABS']:.2f}",
                f"{t['Коэф. износа ABS-CF']:.2f}",
                f"{t['Коэф. износа ABS-GF']:.2f}",
                f"{t['Коэф. износа ASA']:.2f}",
                f"{t['Коэф. износа ASA-CF']:.2f}",
                f"{t['Коэф. износа TPU 95A']:.2f}",
                f"{t['Коэф. износа TPU 98A']:.2f}",
                f"{t['Коэф. износа TPU 85A']:.2f}",
                f"{t['Коэф. износа TPU 75D']:.2f}",
            ))

    def add_nozzle_type_dialog(self):
        self._nozzle_type_form(None)

    def edit_nozzle_type_dialog(self):
        sel = self.tree_nozzle_types.selection()
        if not sel:
            messagebox.showinfo("Инфо", "Выбери тип сопла.")
            return
        self._nozzle_type_form(int(sel[0]))

    def _nozzle_type_form(self, type_id):
        dialog = tk.Toplevel(self.root)
        dialog.title("Тип сопла" + (f" #{type_id}" if type_id else ""))
        dialog.geometry("500x700")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Название:").pack(pady=(10, 2))
        entry_name = ttk.Entry(dialog, width=40)
        entry_name.pack()

        ttk.Label(dialog, text="Материал:").pack(pady=(8, 2))
        combo_material = ttk.Combobox(dialog, values=[
            "Латунь", "Закалённая сталь", "Рубин", "Карбид", "Медь", "Другое"
        ], width=38)
        combo_material.pack()

        ttk.Label(dialog, text="Диаметр (мм):").pack(pady=(8, 2))
        entry_diameter = ttk.Entry(dialog, width=40)
        entry_diameter.pack()

        ttk.Label(dialog, text="Ресурс (г, для PLA):").pack(pady=(8, 2))
        entry_resource = ttk.Entry(dialog, width=40)
        entry_resource.pack()

        ttk.Separator(dialog, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(dialog, text="Коэффициенты износа:",
                  font=("", 10, "bold")).pack(pady=(0, 8))

        coeff_frame = ttk.Frame(dialog)
        coeff_frame.pack(fill="x", padx=20)

        coeff_labels = [
            "PLA", "PLA+", "PLA-CF", "PLA-GF",
            "PETG", "PETG+", "PETG-CF", "PETG-GF",
            "ABS", "ABS-CF", "ABS-GF",
            "ASA", "ASA-CF",
            "TPU 95A", "TPU 98A", "TPU 85A", "TPU 75D",
        ]
        coeff_defaults = [1.0, 1.0, 5.0, 5.0, 1.0, 1.0, 5.0, 5.0,
                          1.2, 6.0, 6.0, 1.3, 6.0, 0.8, 0.8, 0.7, 0.9]
        coeff_entries = {}

        for idx, (label, default) in enumerate(zip(coeff_labels, coeff_defaults)):
            row = idx // 2
            col = (idx % 2) * 2
            ttk.Label(coeff_frame, text=label + ":").grid(
                row=row, column=col, sticky="w", padx=5, pady=2
            )
            entry = ttk.Entry(coeff_frame, width=10)
            entry.grid(row=row, column=col + 1, padx=5, pady=2)
            entry.insert(0, str(default))
            coeff_entries[label] = entry

        if type_id:
            info = self.db.get_nozzle_type_info(type_id)
            if info:
                entry_name.insert(0, info["Название"])
                combo_material.set(info["Материал"] or "Латунь")
                entry_diameter.insert(0, f"{info['Диаметр (мм)']:.2f}")
                entry_resource.insert(0, f"{info['Ресурс (г)']:.0f}")
                for label in coeff_labels:
                    key = f"Коэф. износа {label}"
                    coeff_entries[label].delete(0, tk.END)
                    coeff_entries[label].insert(0, f"{info[key]:.2f}")

        def save():
            try:
                name = entry_name.get().strip()
                material = combo_material.get().strip()
                diameter = float(entry_diameter.get().replace(",", ".") or 0.4)
                resource = float(entry_resource.get().replace(",", "."))
                if not name:
                    messagebox.showerror("Ошибка", "Название обязательно.")
                    return
                if resource <= 0:
                    messagebox.showerror("Ошибка", "Ресурс должен быть > 0.")
                    return

                coeffs = []
                for label in coeff_labels:
                    val = float(coeff_entries[label].get().replace(",", "."))
                    coeffs.append(val)

                if type_id:
                    ok = self.db.update_nozzle_type(
                        type_id, name, material, diameter, resource, *coeffs
                    )
                else:
                    ok = self.db.add_nozzle_type(
                        name, material, diameter, resource, *coeffs
                    )

                if ok:
                    dialog.destroy()
                    self.refresh_all()
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить (возможно, дубликат названия).")
            except ValueError:
                messagebox.showerror("Ошибка", "Проверь числа.")

        ttk.Button(dialog, text="💾 Сохранить", command=save).pack(pady=15)

    def delete_selected_nozzle_type(self):
        sel = self.tree_nozzle_types.selection()
        if not sel:
            return
        type_id = int(sel[0])
        if not messagebox.askyesno("Удалить?",
                "Удалить тип сопла?\nЕсли есть сопла этого типа — удаление не сработает."):
            return
        if self.db.delete_nozzle_type(type_id):
            self.refresh_all()
        else:
            messagebox.showerror("Ошибка", "Тип используется в таблице Сопла.")

    # ============================================================
    # ВКЛАДКА 6: СОПЛА
    # ============================================================
    def build_nozzles_tab(self):
        columns = ("ID", "Тип", "Материал", "Ø (мм)", "Серийный",
                   "Стоимость", "Наработка (г)", "Ресурс (г)",
                   "Остаток (г)", "Износ %", "Статус")
        self.tree_nozzles = ttk.Treeview(
            self.tab_nozzles, columns=columns, show="headings", height=18
        )
        widths = (40, 130, 90, 55, 110, 80, 100, 80, 90, 70, 90)
        for col, w in zip(columns, widths):
            self.tree_nozzles.heading(col, text=col)
            self.tree_nozzles.column(col, width=w, anchor="center")

        h_scroll = ttk.Scrollbar(self.tab_nozzles, orient="horizontal",
                                 command=self.tree_nozzles.xview)
        self.tree_nozzles.configure(xscrollcommand=h_scroll.set)

        self.tree_nozzles.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        h_scroll.pack(fill="x", padx=10)

        frm_btns = ttk.Frame(self.tab_nozzles)
        frm_btns.pack(fill="x", padx=10, pady=5)
        ttk.Button(frm_btns, text="➕ Добавить сопло",
                   command=self.add_nozzle_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="✏ Изменить",
                   command=self.edit_nozzle_dialog).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🗑 Удалить",
                   command=self.delete_selected_nozzle).pack(side="left", padx=5)
        ttk.Button(frm_btns, text="🔄 Обновить",
                   command=self.load_nozzles_data).pack(side="left", padx=5)

    def load_nozzles_data(self):
        for i in self.tree_nozzles.get_children():
            self.tree_nozzles.delete(i)
        for n in self.db.get_all_nozzles():
            resource = n["Ресурс"] or 0
            wear = n["Наработка (г)"] or 0
            остаток = n["Остаток"] or 0
            if resource > 0:
                wear_pct = (wear / resource) * 100
            else:
                wear_pct = 0.0
            self.tree_nozzles.insert("", "end", iid=str(n["id"]), values=(
                n["id"],
                n["Тип"],
                n["Материал"] or "",
                f"{n['Диаметр']:.2f}" if n["Диаметр"] is not None else "",
                n["Серийный номер"] or "",
                f"{n['Стоимость (руб)']:.2f}",
                f"{wear:.1f}",
                f"{resource:.0f}",
                f"{остаток:.1f}",
                f"{wear_pct:.1f}%",
                n["Статус"] or "",
            ))

    def add_nozzle_dialog(self):
        # Проверяем, есть ли вообще типы сопел
        types = self.db.get_all_nozzle_types()
        if not types:
            messagebox.showerror(
                "Ошибка",
                "Сначала добавь хотя бы один тип сопла (вкладка «🔧 Типы сопел»)."
            )
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить сопло")
        dialog.geometry("400x420")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Тип сопла:").pack(pady=(10, 2))
        type_names = [t["Название"] for t in types]
        combo_type = ttk.Combobox(dialog, values=type_names, state="readonly", width=35)
        combo_type.pack()
        combo_type.current(0)

        ttk.Label(dialog, text="Серийный номер (опционально):").pack(pady=(10, 2))
        entry_serial = ttk.Entry(dialog, width=38)
        entry_serial.pack()

        ttk.Label(dialog, text="Стоимость сопла (руб.):").pack(pady=(10, 2))
        entry_cost = ttk.Entry(dialog, width=38)
        entry_cost.pack()

        ttk.Label(dialog, text="Дата покупки (ГГГГ-ММ-ДД, опционально):").pack(pady=(10, 2))
        entry_date = ttk.Entry(dialog, width=38)
        entry_date.pack()

        ttk.Label(dialog, text="Заметки:").pack(pady=(10, 2))
        entry_notes = ttk.Entry(dialog, width=38)
        entry_notes.pack()

        def save():
            try:
                type_name = combo_type.get()
                type_id = next(t["id"] for t in types if t["Название"] == type_name)
                serial = entry_serial.get().strip()
                cost = float(entry_cost.get().replace(",", "."))
                purchase_date = entry_date.get().strip() or None
                notes = entry_notes.get().strip()

                if self.db.add_nozzle(type_id, serial, cost, purchase_date, notes):
                    messagebox.showinfo("OK", "Сопло добавлено.")
                    dialog.destroy()
                    self.load_nozzles_data()
                else:
                    messagebox.showerror("Ошибка", "Не удалось добавить.")
            except ValueError:
                messagebox.showerror("Ошибка", "Стоимость — число.")
            except StopIteration:
                messagebox.showerror("Ошибка", "Выбери тип сопла.")

        ttk.Button(dialog, text="💾 Сохранить", command=save).pack(pady=20)

    def edit_nozzle_dialog(self):
        sel = self.tree_nozzles.selection()
        if not sel:
            messagebox.showinfo("Инфо", "Выбери сопло в таблице.")
            return
        nozzle_id = int(sel[0])

        current = self.db.get_nozzle_info(nozzle_id)
        if not current:
            return

        types = self.db.get_all_nozzle_types()
        if not types:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Сопло #{nozzle_id}")
        dialog.geometry("400x480")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Тип сопла:").pack(pady=(10, 2))
        type_names = [t["Название"] for t in types]
        combo_type = ttk.Combobox(dialog, values=type_names, state="readonly", width=35)
        combo_type.pack()
        # Устанавливаем текущий тип
        current_type_name = current["Тип"]
        if current_type_name in type_names:
            combo_type.set(current_type_name)

        ttk.Label(dialog, text="Серийный номер:").pack(pady=(10, 2))
        entry_serial = ttk.Entry(dialog, width=38)
        entry_serial.pack()
        entry_serial.insert(0, current["Серийный номер"] or "")

        ttk.Label(dialog, text="Стоимость сопла (руб.):").pack(pady=(10, 2))
        entry_cost = ttk.Entry(dialog, width=38)
        entry_cost.pack()
        entry_cost.insert(0, f"{current['Стоимость (руб)']:.2f}")

        ttk.Label(dialog, text="Статус:").pack(pady=(10, 2))
        combo_status = ttk.Combobox(
            dialog, values=["В работе", "В запасе", "Изношено", "Сломано"],
            state="readonly", width=35
        )
        combo_status.pack()
        combo_status.set(current["Статус"] or "В работе")

        ttk.Label(dialog, text="Наработка (г, эффективная):").pack(pady=(10, 2))
        entry_wear = ttk.Entry(dialog, width=38)
        entry_wear.pack()
        entry_wear.insert(0, f"{current['Наработка (г)'] or 0:.1f}")

        ttk.Label(dialog, text="Заметки:").pack(pady=(10, 2))
        entry_notes = ttk.Entry(dialog, width=38)
        entry_notes.pack()
        entry_notes.insert(0, current["Заметки"] or "")

        def save():
            try:
                type_name = combo_type.get()
                type_id = next(t["id"] for t in types if t["Название"] == type_name)
                serial = entry_serial.get().strip()
                cost = float(entry_cost.get().replace(",", "."))
                status = combo_status.get()
                wear = float(entry_wear.get().replace(",", "."))
                notes = entry_notes.get().strip()

                # Обновляем через update_nozzle (тип, серийник, стоимость, статус)
                ok1 = self.db.update_nozzle(
                    nozzle_id, type_id, serial, cost, status, notes
                )
                # Наработку обновляем отдельно (чтобы не терять другое)
                ok2 = self.db.execute_commit(
                    'UPDATE "Сопла" SET "Наработка (г)" = ? WHERE "id" = ?',
                    (wear, nozzle_id)
                )

                if ok1 and ok2:
                    dialog.destroy()
                    self.load_nozzles_data()
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить.")
            except ValueError:
                messagebox.showerror("Ошибка", "Стоимость и наработка — числа.")
            except StopIteration:
                messagebox.showerror("Ошибка", "Выбери тип сопла.")

        ttk.Button(dialog, text="💾 Сохранить", command=save).pack(pady=20)

    def delete_selected_nozzle(self):
        sel = self.tree_nozzles.selection()
        if not sel:
            return
        nozzle_id = int(sel[0])
        if not messagebox.askyesno("Удалить?", f"Удалить сопло #{nozzle_id}?"):
            return
        if self.db.delete_nozzle(nozzle_id):
            self.load_nozzles_data()
        else:
            messagebox.showerror("Ошибка", "Возможно, сопло используется в истории печати.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PrintCostApp(root)
    root.mainloop()