import tkinter as tk
from tkinter import ttk, font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.gridspec as gridspec
import numpy as np
import math
import random
from collections import Counter


class SolutionWindow(tk.Toplevel):
    """Окреме, повністю функціональне вікно для показу рішення"""

    def __init__(self, parent, solution_steps):
        super().__init__(parent)
        self.title("Рішення завдання")
        self.geometry("800x600")

        self.font_explanation = font.Font(family="Helvetica", size=18)
        self.font_title = font.Font(family="Helvetica", size=20, weight="bold")
        self.font_frac = font.Font(family="Helvetica", size=22, weight="bold")

        main_canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        row_counter = 0
        for style, text in solution_steps:
            frame = ttk.LabelFrame(scrollable_frame, padding=15)
            frame.grid(row=row_counter, column=0, sticky="ew", pady=10, padx=10)
            scrollable_frame.columnconfigure(0, weight=1)
            row_counter += 1

            lines = text.split('\n')

            title_label = ttk.Label(frame, text=lines[0],
                                    font=self.font_title if style == "bold" else self.font_explanation)
            title_label.pack(anchor="w")

            for line in lines[1:]:
                if "->" in line:
                    parts = line.split("->")
                    frac_frame = ttk.Frame(frame)
                    frac_frame.pack(anchor="w", pady=10)

                    # Обробка кількох стрілок в одному рядку
                    for i, part in enumerate(parts):
                        if i > 0:
                            ttk.Label(frac_frame, text="  ->  ", font=self.font_frac).pack(side=tk.LEFT, padx=10)
                        self.draw_fraction_expression(frac_frame, part.strip())
                else:
                    line_label = ttk.Label(frame, text=line, font=self.font_explanation, wraplength=700)
                    line_label.pack(anchor="w", pady=2)
                    frame.bind("<Configure>", lambda e, lbl=line_label: lbl.config(wraplength=e.width - 40))

    def draw_fraction_expression(self, parent, expression):
        parts = expression.split('+')
        for i, part in enumerate(parts):
            if i > 0: ttk.Label(parent, text=" + ", font=self.font_frac).pack(side=tk.LEFT)
            try:
                n_str, d_str = map(str.strip, part.replace('(', '').replace(')', '').split('/'))
            except ValueError:
                ttk.Label(parent, text=part, font=self.font_frac).pack(side=tk.LEFT)
                continue

            canvas = tk.Canvas(parent, height=60, bg=self.cget('bg'), highlightthickness=0)
            canvas.pack(side=tk.LEFT)
            n_w, d_w = self.font_frac.measure(n_str), self.font_frac.measure(d_str)
            max_w = max(n_w, d_w) + 10
            canvas.config(width=max_w)
            canvas.create_text(max_w / 2, 15, text=n_str, font=self.font_frac, anchor="center")
            canvas.create_line(2, 30, max_w - 2, 30, width=3)
            canvas.create_text(max_w / 2, 45, text=d_str, font=self.font_frac, anchor="center")


class FractionVisualizerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Інтерактивний тренажер дробів")
        try:
            self.state('zoomed')
        except tk.TclError:
            self.attributes('-zoomed', True)

        self.MAX_DENOMINATOR = 100
        self.color1, self.color2, self.empty_color = 'deepskyblue', 'salmon', '#E0E0E0'
        self.task_n1, self.task_d1, self.task_n2, self.task_d2 = 0, 1, 0, 1

        self.font_body = font.Font(family="Helvetica", size=16)
        self.font_title = font.Font(family="Helvetica", size=18, weight="bold")
        self.font_slider_value = font.Font(family="Helvetica", size=17, weight="bold")
        self.font_success = font.Font(family="Helvetica", size=18, weight="bold")

        self.style = ttk.Style(self)
        self.style.configure("TLabel", font=self.font_body)
        self.style.configure("TButton", font=self.font_body, padding=10)
        self.style.configure("TScale", length=300)
        self.style.configure("Title.TLabel", font=self.font_title)
        self.style.configure("Success.TLabel", font=self.font_success, foreground="green")

        self.num1_var, self.den1_var = tk.IntVar(), tk.IntVar()
        self.num2_var, self.den2_var = tk.IntVar(), tk.IntVar()
        self.success_var = tk.StringVar()

        main_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top_pane_frame = ttk.Frame(main_pane)
        top_pane_frame.columnconfigure(0, weight=1);
        top_pane_frame.rowconfigure(1, weight=1)
        main_pane.add(top_pane_frame, weight=4)

        task_frame = ttk.Frame(top_pane_frame)
        task_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.task_canvas = tk.Canvas(task_frame, height=60)
        self.task_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)

        toolbar_frame = ttk.Frame(task_frame)
        toolbar_frame.pack(side=tk.LEFT, padx=20)
        self.success_label = ttk.Label(toolbar_frame, textvariable=self.success_var, style="Success.TLabel")
        self.success_label.pack(side=tk.LEFT, padx=20)
        ttk.Button(toolbar_frame, text="Нове завдання", command=self._generate_new_task).pack(side=tk.LEFT, padx=10)
        ttk.Button(toolbar_frame, text="Показати рішення", command=self._open_solution_window).pack(side=tk.LEFT,
                                                                                                    padx=10)

        controls_frame = ttk.Frame(top_pane_frame)
        controls_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        controls_frame.columnconfigure(0, weight=1);
        controls_frame.columnconfigure(1, weight=1)

        self.controls1 = self._create_fraction_controls(controls_frame, "Перший дріб", self.num1_var, self.den1_var, 0)
        self.controls2 = self._create_fraction_controls(controls_frame, "Другий дріб", self.num2_var, self.den2_var, 1)

        plot_frame = ttk.Frame(main_pane)
        main_pane.add(plot_frame, weight=6)

        self.figure = plt.figure(figsize=(14, 6), dpi=90)
        self.canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._generate_new_task()

    def _create_fraction_controls(self, parent, title, num_var, den_var, col):
        frame = ttk.Frame(parent);
        frame.grid(row=0, column=col, padx=20, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=title, style="Title.TLabel").pack(pady=(0, 20))
        num_widgets = self._create_slider_unit(frame, "Чисельник:", num_var)
        num_widgets['frame'].pack(pady=5, fill="x", expand=True)
        ttk.Separator(frame, orient="horizontal").pack(pady=20, fill="x", expand=True)
        den_widgets = self._create_slider_unit(frame, "Знаменник:", den_var)
        den_widgets['frame'].pack(pady=5, fill="x", expand=True)
        return {'num': num_widgets, 'den': den_widgets}

    def _create_slider_unit(self, parent, label_text, var):
        frame = ttk.Frame(parent);
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text=label_text).grid(row=0, column=0, columnspan=4, sticky="w")
        btn_minus = ttk.Button(frame, text="-", command=lambda v=var: self._adjust_value(v, -1))
        btn_minus.grid(row=1, column=0, padx=(0, 5))
        scale = ttk.Scale(frame, from_=0, to=self.MAX_DENOMINATOR, variable=var,
                          command=lambda val, v=var: self._on_slider_change(val, v), orient="horizontal")
        scale.grid(row=1, column=1, sticky="ew")
        btn_plus = ttk.Button(frame, text="+", command=lambda v=var: self._adjust_value(v, 1))
        btn_plus.grid(row=1, column=2, padx=5)
        ttk.Label(frame, textvariable=var, font=self.font_slider_value, width=4).grid(row=1, column=3, padx=(10, 0))
        return {'frame': frame, 'scale': scale, 'plus': btn_plus, 'minus': btn_minus}

    def _update_task_display(self, n1, d1, n2, d2):
        self.task_canvas.delete("all")
        self.task_canvas.bind("<Configure>", lambda e: self._draw_task_fractions(n1, d1, n2, d2), add="+")
        self.update_idletasks()
        self._draw_task_fractions(n1, d1, n2, d2)

    def _draw_task_fractions(self, n1, d1, n2, d2):
        self.task_canvas.delete("all")
        canvas_w, canvas_h = self.task_canvas.winfo_width(), self.task_canvas.winfo_height()
        if canvas_w < 50: return
        task_font = font.Font(family="Helvetica", size=24, weight="bold")
        prefix_text = "Завдання: "
        prefix_len = font.Font(font=self.font_body).measure(prefix_text)
        self.task_canvas.create_text(10, canvas_h / 2, text=prefix_text, font=self.font_body, anchor="w", fill="navy")
        x_pos = prefix_len + 15

        def draw_frac(n, d, x):
            n_w, d_w = task_font.measure(str(n)), task_font.measure(str(d))
            max_w = max(n_w, d_w) + 10
            self.task_canvas.create_text(x + max_w / 2, canvas_h / 2 - 16, text=str(n), font=task_font, anchor="center")
            self.task_canvas.create_line(x, canvas_h / 2, x + max_w, canvas_h / 2, width=3)
            self.task_canvas.create_text(x + max_w / 2, canvas_h / 2 + 16, text=str(d), font=task_font, anchor="center")
            return x + max_w + 20

        x_pos = draw_frac(n1, d1, x_pos)
        self.task_canvas.create_text(x_pos, canvas_h / 2, text="+", font=task_font, anchor="center")
        x_pos += 40
        draw_frac(n2, d2, x_pos)

    def _adjust_value(self, var, delta):
        var.set(var.get() + delta)
        self._on_slider_change()

    def _on_slider_change(self, value=None, var=None):
        if var is not None and value is not None: var.set(int(float(value)))
        if self.den1_var.get() < 1: self.den1_var.set(1)
        if self.den2_var.get() < 1: self.den2_var.set(1)
        if self.num1_var.get() < 0: self.num1_var.set(0)
        if self.num2_var.get() < 0: self.num2_var.set(0)
        self.controls1['num']['scale'].config(to=self.den1_var.get())
        if self.num1_var.get() > self.den1_var.get(): self.num1_var.set(self.den1_var.get())
        self.controls2['num']['scale'].config(to=self.den2_var.get())
        if self.num2_var.get() > self.den2_var.get(): self.num2_var.set(self.den2_var.get())
        self.visualize()

    def _open_solution_window(self):
        self._build_solution_for_task()
        SolutionWindow(self, self.solution_steps)

    def _set_controls_state(self, state):
        for control_group in [self.controls1, self.controls2]:
            for part in ['num', 'den']:
                control_group[part]['scale'].config(state=state)
                control_group[part]['plus'].config(state=state)
                control_group[part]['minus'].config(state=state)

    def _generate_new_task(self):
        while True:
            d1, d2 = random.randint(4, 15), random.randint(4, 15)
            lcm = (d1 * d2) // math.gcd(d1, d2)
            if d1 != d2 and lcm <= self.MAX_DENOMINATOR:
                break
        n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
        self._load_state((n1, d1, n2, d2))

    def _load_state(self, state):
        self._set_controls_state(tk.NORMAL)
        self.success_var.set("")
        n1, d1, n2, d2 = state
        self.task_n1, self.task_d1, self.task_n2, self.task_d2 = n1, d1, n2, d2
        self.num1_var.set(n1);
        self.den1_var.set(d1)
        self.num2_var.set(n2);
        self.den2_var.set(d2)
        self._update_task_display(n1, d1, n2, d2)
        self._on_slider_change()

    def get_prime_factorization(self, n):
        factors, d = [], 2
        while d * d <= n:
            while (n % d) == 0: factors.append(d); n //= d
            d += 1
        if n > 1: factors.append(n)
        return factors

    def _get_detailed_lcm_explanation(self, d1, d2):
        factors1, factors2 = self.get_prime_factorization(d1), self.get_prime_factorization(d2)
        count1 = Counter(factors1)
        lcm_factors_list, missing_factors = list(factors1), []
        temp_count1 = count1.copy()
        for factor in factors2:
            if temp_count1.get(factor, 0) > 0:
                temp_count1[factor] -= 1
            else:
                lcm_factors_list.append(factor);
                missing_factors.append(str(factor))
        lcm = math.prod(lcm_factors_list)
        return [
            ("bold", "--- КРОК 1: ПОШУК НСК (Найменшого Спільного Кратного) ---"),
            ("normal",
             f"1. Розкладемо знаменники ({d1} і {d2}) на прості множники:\n   {d1} = {' * '.join(map(str, factors1))}\n   {d2} = {' * '.join(map(str, factors2))}"),
            ("normal",
             "2. Щоб знайти НСК, випишемо множники першого числа і доповнимо їх тими, яких не вистачає з другого."),
            ("normal", f"   - Беремо множники від {d1}: {', '.join(map(str, factors1))}"),
            ("normal",
             f"   - З множників {d2} не вистачає: {', '.join(missing_factors) if missing_factors else 'всі множники вже є'}"),
            ("normal",
             f"3. Перемножимо їх:\n   НСК = ({' * '.join(map(str, factors1))}) * {' * '.join(missing_factors) if missing_factors else '1'} = {lcm}"),
            ("bold", "--- КРОК 2: ДОДАТКОВІ МНОЖНИКИ ---"),
            ("normal", f"   - Для першого дробу: {lcm} ÷ {d1} = {lcm // d1}"),
            ("normal", f"   - Для другого дробу: {lcm} ÷ {d2} = {lcm // d2}"),
        ]

    def visualize(self):
        self.figure.clear()
        num1, den1 = self.num1_var.get(), self.den1_var.get()
        num2, den2 = self.num2_var.get(), self.den2_var.get()

        self.success_var.set("")  # Скидаємо повідомлення при кожній зміні

        # --- НОВА ЛОГІКА ПЕРЕВІРКИ ---
        # Перевіряємо відповідь, тільки якщо користувач встановив спільний знаменник
        if den1 > 0 and den1 == den2:
            # Перевіряємо, чи еквівалентний перший дріб користувача першому дробу завдання
            is_frac1_equiv = (num1 * self.task_d1 == self.task_n1 * den1)
            # Перевіряємо, чи еквівалентний другий дріб користувача другому дробу завдання
            is_frac2_equiv = (num2 * self.task_d2 == self.task_n2 * den2)

            # Якщо обидва дроби перетворено правильно
            if is_frac1_equiv and is_frac2_equiv:
                sum_n = num1 + num2
                sum_d = den1

                common_divisor = math.gcd(sum_n, sum_d)

                if common_divisor > 1:
                    # Відповідь правильна, але результат можна скоротити
                    self.success_var.set("✔ Правильно! Результат можна скоротити.")
                else:
                    # Відповідь правильна і результат вже скорочений
                    self.success_var.set("✔ ВІДМІННО! Результат нескоротний.")

                self._set_controls_state(tk.DISABLED)

        # --- Логіка малювання залишається без змін ---
        is_sum_greater_than_one = (den1 == den2 and (num1 + num2) > den1)

        if is_sum_greater_than_one:
            gs = gridspec.GridSpec(2, 3, figure=self.figure)
            ax1, ax2 = self.figure.add_subplot(gs[:, 0]), self.figure.add_subplot(gs[:, 1])
            ax3, ax4 = self.figure.add_subplot(gs[0, 2]), self.figure.add_subplot(gs[1, 2])
        else:
            gs = gridspec.GridSpec(1, 3, figure=self.figure)
            ax1, ax2 = self.figure.add_subplot(gs[0]), self.figure.add_subplot(gs[1])
            ax3 = self.figure.add_subplot(gs[2])
            ax4 = None

        self.draw_fraction_pie(ax1, [num1], [self.color1], den1, f"Перший дріб\n$\\frac{{{num1}}}{{{den1}}}$")
        self.draw_fraction_pie(ax2, [num2], [self.color2], den2, f"Другий дріб\n$\\frac{{{num2}}}{{{den2}}}$")
        ax2.axvline(x=1.6, color='grey', linestyle='--', linewidth=2, ymin=0.05, ymax=0.95)

        if den1 == den2:
            self._display_sum_result(ax3, ax4, num1, num2, den1)
        else:
            self.draw_placeholder(ax3, "Результат")

        self.figure.tight_layout(pad=2.0, h_pad=4.0)
        self.canvas.draw()

    def _display_sum_result(self, ax3, ax4, n1, n2, den):
        sum_num = n1 + n2
        whole, frac = divmod(sum_num, den)
        title = f"$\\frac{{{n1}}}{{{den}}} + \\frac{{{n2}}}{{{den}}} = \\frac{{{sum_num}}}{{{den}}}$"
        if whole > 0: title += f" = {whole}" + (f" $\\frac{{{frac}}}{{{den}}}$" if frac > 0 else "")

        if sum_num <= den:
            self.draw_fraction_pie(ax3, [n1, n2], [self.color1, self.color2], den, title)
        else:
            first_fill = min(n2, den - n1);
            second_rem = n2 - first_fill
            self.draw_fraction_pie(ax3, [n1, first_fill], [self.color1, self.color2], den, title)
            if ax4:
                self.draw_fraction_pie(ax4, [second_rem], [self.color2], den, "")

    def _build_solution_for_task(self):
        n1, d1, n2, d2 = self.task_n1, self.task_d1, self.task_n2, self.task_d2
        self.solution_steps = self._get_detailed_lcm_explanation(d1, d2)
        lcm = (d1 * d2) // math.gcd(d1, d2)
        m1, m2 = lcm // d1, lcm // d2

        sum_n = (n1 * m1) + (n2 * m2)

        sol_text = [
            ("bold", "--- КРОК 3: ДОДАВАННЯ ДРОБІВ ---"),
            ("normal",
             f"1. Домножимо дроби із завдання на їх додаткові множники:\n({n1}/{d1}) + ({n2}/{d2}) -> ({(n1 * m1)}/{lcm}) + ({(n2 * m2)}/{lcm})"),
            ("normal", f"2. Додамо чисельники:\n= ({sum_n}/{lcm})"),
        ]
        self.solution_steps.extend(sol_text)

        # --- НОВИЙ КРОК: СКОРОЧЕННЯ РЕЗУЛЬТАТУ ---
        common_divisor = math.gcd(sum_n, lcm)
        if common_divisor > 1:
            reduced_n = sum_n // common_divisor
            reduced_d = lcm // common_divisor
            reduction_step = [
                ("bold", "--- КРОК 4: СКОРОЧЕННЯ РЕЗУЛЬТАТУ ---"),
                ("normal", f"Отриманий дріб ({sum_n}/{lcm}) можна скоротити."),
                ("normal", f"Знайдемо найбільший спільний дільник (НСД) для {sum_n} і {lcm}. НСД = {common_divisor}."),
                ("normal",
                 f"Поділимо чисельник і знаменник на {common_divisor}:\n({sum_n}/{lcm}) -> ({reduced_n}/{reduced_d})"),
                ("bold", f"Кінцева відповідь: {reduced_n}/{reduced_d}")
            ]
            self.solution_steps.extend(reduction_step)

    def draw_fraction_pie(self, ax, numerators, colors, denominator, title):
        ax.set_title(title, pad=25, fontsize=26)
        ax.axis('equal')
        total_num = sum(numerators)
        if total_num > 0 and denominator > 0:
            val, rounded_val = total_num / denominator, round(total_num / denominator, 3)
            prefix = "≈" if abs(val - rounded_val) > 1e-9 else "="
            ax.text(0, -1.4, f"({prefix} {rounded_val})", ha='center', va='center', fontsize=18, color='gray')

        sizes, final_colors = [], []
        if sum(numerators) > 0:
            sizes.extend(n for n in numerators if n > 0)
            final_colors.extend(colors[:len(sizes)])
        if denominator - sum(numerators) > 0:
            sizes.append(denominator - sum(numerators))
            final_colors.append(self.empty_color)

        if not sizes:
            sizes, final_colors = [1], [self.empty_color]

        ax.pie(sizes, colors=final_colors, startangle=90, counterclock=False,
               wedgeprops={'edgecolor': 'black', 'linewidth': 1})
        if denominator <= 40:
            for i in range(denominator):
                angle = np.deg2rad(90 - i * (360.0 / denominator))
                ax.plot([0, np.cos(angle)], [0, np.sin(angle)], color='black', lw=0.7, alpha=0.6)

    def draw_placeholder(self, ax, text):
        ax.set_title(text, pad=25, fontsize=26)
        ax.axis('equal')
        ax.pie([1], colors=[self.empty_color], wedgeprops={'edgecolor': 'grey', 'linewidth': 1.5, 'linestyle': '--'})
        ax.text(0, 0, "Зведіть до\nспільного\nзнаменника!", ha='center', va='center', fontsize=20, color='grey')


if __name__ == "__main__":
    app = FractionVisualizerApp()
    app.mainloop()