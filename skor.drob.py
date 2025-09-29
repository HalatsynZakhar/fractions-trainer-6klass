import tkinter as tk
from tkinter import ttk, font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import math
import random


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
                    left, right = parts[0].strip(), parts[1].strip()
                    frac_frame = ttk.Frame(frame)
                    frac_frame.pack(anchor="w", pady=10)
                    self.draw_single_fraction(frac_frame, left)
                    ttk.Label(frac_frame, text="  ->  ", font=self.font_frac).pack(side=tk.LEFT, padx=10)
                    self.draw_single_fraction(frac_frame, right)
                else:
                    line_label = ttk.Label(frame, text=line, font=self.font_explanation, wraplength=700)
                    line_label.pack(anchor="w", pady=2)
                    frame.bind("<Configure>", lambda e, lbl=line_label: lbl.config(wraplength=e.width - 40))

    def draw_single_fraction(self, parent, frac_str):
        try:
            n_str, d_str = map(str.strip, frac_str.replace('(', '').replace(')', '').split('/'))
        except ValueError:
            ttk.Label(parent, text=frac_str, font=self.font_frac).pack(side=tk.LEFT)
            return

        canvas = tk.Canvas(parent, height=60, bg=self.cget('bg'), highlightthickness=0)
        canvas.pack(side=tk.LEFT)
        n_w, d_w = self.font_frac.measure(n_str), self.font_frac.measure(d_str)
        max_w = max(n_w, d_w) + 10
        canvas.config(width=max_w)
        canvas.create_text(max_w / 2, 15, text=n_str, font=self.font_frac, anchor="center")
        canvas.create_line(2, 30, max_w - 2, 30, width=3)
        canvas.create_text(max_w / 2, 45, text=d_str, font=self.font_frac, anchor="center")


class FractionReductionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Тренажер скорочення дробів")
        try:
            self.state('zoomed')
        except tk.TclError:
            self.attributes('-zoomed', True)

        self.MAX_DENOMINATOR = 100
        self.color1, self.color2, self.empty_color = 'mediumseagreen', 'salmon', '#E0E0E0'
        self.task_n, self.task_d = 0, 1
        self.correct_n, self.correct_d = 0, 1

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

        self.num_var, self.den_var = tk.IntVar(), tk.IntVar()
        self.success_var = tk.StringVar()

        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        controls_main_frame = ttk.Frame(main_pane, padding=20)
        main_pane.add(controls_main_frame, weight=2)

        task_frame = ttk.Frame(controls_main_frame)
        task_frame.pack(fill="x", pady=(0, 20))
        self.task_canvas = tk.Canvas(task_frame, height=60)
        self.task_canvas.pack(fill=tk.X, expand=True)

        toolbar_frame = ttk.Frame(controls_main_frame)
        toolbar_frame.pack(fill="x", pady=20)
        self.success_label = ttk.Label(toolbar_frame, textvariable=self.success_var, style="Success.TLabel")
        self.success_label.pack(side=tk.LEFT, expand=True)
        ttk.Button(toolbar_frame, text="Нове завдання", command=self._generate_new_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Показати рішення", command=self._open_solution_window).pack(side=tk.LEFT,
                                                                                                    padx=5)

        self.controls = self._create_fraction_controls(controls_main_frame, "Ваша відповідь", self.num_var,
                                                       self.den_var)
        self.controls['frame'].pack(fill="x", expand=True, pady=20)

        plot_frame = ttk.Frame(main_pane)
        main_pane.add(plot_frame, weight=5)

        self.figure = plt.figure(figsize=(12, 6), dpi=90)
        self.canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._generate_new_task()

    def _create_fraction_controls(self, parent, title, num_var, den_var):
        frame = ttk.Frame(parent, padding=10)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=title, style="Title.TLabel").pack(pady=(0, 20))
        num_widgets = self._create_slider_unit(frame, "Чисельник:", num_var)
        num_widgets['frame'].pack(pady=5, fill="x", expand=True)
        ttk.Separator(frame, orient="horizontal").pack(pady=20, fill="x", expand=True)
        den_widgets = self._create_slider_unit(frame, "Знаменник:", den_var)
        den_widgets['frame'].pack(pady=5, fill="x", expand=True)
        return {'frame': frame, 'num': num_widgets, 'den': den_widgets}

    def _create_slider_unit(self, parent, label_text, var):
        frame = ttk.Frame(parent)
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

    def _update_task_display(self, n, d):
        self.task_canvas.delete("all")
        self.task_canvas.bind("<Configure>", lambda e: self._draw_task_fraction(n, d), add="+")
        self.update_idletasks()
        self._draw_task_fraction(n, d)

    def _draw_task_fraction(self, n, d):
        self.task_canvas.delete("all")
        canvas_w, canvas_h = self.task_canvas.winfo_width(), self.task_canvas.winfo_height()
        if canvas_w < 50: return
        task_font = font.Font(family="Helvetica", size=24, weight="bold")
        prefix_text = "Завдання: скоротити "
        prefix_len = font.Font(font=self.font_body).measure(prefix_text)
        self.task_canvas.create_text(10, canvas_h / 2, text=prefix_text, font=self.font_body, anchor="w", fill="navy")
        x_pos = prefix_len + 15

        n_w, d_w = task_font.measure(str(n)), task_font.measure(str(d))
        max_w = max(n_w, d_w) + 10
        self.task_canvas.create_text(x_pos + max_w / 2, canvas_h / 2 - 16, text=str(n), font=task_font, anchor="center")
        self.task_canvas.create_line(x_pos, canvas_h / 2, x_pos + max_w, canvas_h / 2, width=3)
        self.task_canvas.create_text(x_pos + max_w / 2, canvas_h / 2 + 16, text=str(d), font=task_font, anchor="center")

    def _adjust_value(self, var, delta):
        var.set(var.get() + delta)
        self._on_slider_change()

    def _on_slider_change(self, value=None, var=None):
        if var is not None and value is not None: var.set(int(float(value)))
        if self.den_var.get() < 1: self.den_var.set(1)
        if self.num_var.get() < 0: self.num_var.set(0)
        self.controls['num']['scale'].config(to=self.den_var.get())
        if self.num_var.get() > self.den_var.get(): self.num_var.set(self.den_var.get())
        self.visualize()

    def _open_solution_window(self):
        self._build_solution_for_task()
        SolutionWindow(self, self.solution_steps)

    def _set_controls_state(self, state):
        for part in ['num', 'den']:
            self.controls[part]['scale'].config(state=state)
            self.controls[part]['plus'].config(state=state)
            self.controls[part]['minus'].config(state=state)

    def _generate_new_task(self):
        while True:
            d_corr = random.randint(3, 12)
            n_corr = random.randint(1, d_corr - 1)
            if math.gcd(n_corr, d_corr) == 1:
                break

        multiplier = random.randint(2, 8)
        n_task = n_corr * multiplier
        d_task = d_corr * multiplier

        if d_task > self.MAX_DENOMINATOR:
            self._generate_new_task()
            return

        self._load_state((n_task, d_task, n_corr, d_corr))

    def _load_state(self, state):
        self._set_controls_state(tk.NORMAL)
        self.success_var.set("")
        n_task, d_task, n_corr, d_corr = state
        self.task_n, self.task_d = n_task, d_task
        self.correct_n, self.correct_d = n_corr, d_corr

        self.num_var.set(n_task)
        self.den_var.set(d_task)
        self.controls['den']['scale'].config(to=self.MAX_DENOMINATOR)

        self._update_task_display(n_task, d_task)
        self._on_slider_change()

    def get_prime_factorization(self, n):
        factors, d = [], 2
        while d * d <= n:
            while (n % d) == 0: factors.append(d); n //= d
            d += 1
        if n > 1: factors.append(n)
        return factors

    def _build_solution_for_task(self):
        n, d = self.task_n, self.task_d
        gcd = math.gcd(n, d)

        n_factors_str = ' * '.join(map(str, self.get_prime_factorization(n)))
        d_factors_str = ' * '.join(map(str, self.get_prime_factorization(d)))

        self.solution_steps = [
            ("bold", "--- КРОК 1: ПОШУК НАЙБІЛЬШОГО СПІЛЬНОГО ДІЛЬНИКА (НСД) ---"),
            ("normal",
             f"Щоб скоротити дріб, потрібно знайти найбільше число, на яке ділиться і чисельник ({n}), і знаменник ({d})."),
            ("normal", f"1. Розкладемо числа на прості множники:\n   {n} = {n_factors_str}\n   {d} = {d_factors_str}"),
            ("normal", "2. Знайдемо спільні множники в обох розкладах і перемножимо їх. Це і буде НСД."),
            ("normal", f"   НСД({n}, {d}) = {gcd}"),
            ("bold", "--- КРОК 2: СКОРОЧЕННЯ ДРОБУ ---"),
            ("normal", f"Тепер поділимо чисельник і знаменник на їх НСД, тобто на {gcd}."),
            ("normal", f"Чисельник: {n} ÷ {gcd} = {self.correct_n}\nЗнаменник: {d} ÷ {gcd} = {self.correct_d}"),
            ("normal", f"({n}/{d}) -> ({self.correct_n}/{self.correct_d})"),
            ("bold", "--- РЕЗУЛЬТАТ ---"),
            ("normal", f"Скорочений дріб: {self.correct_n}/{self.correct_d}")
        ]

    def visualize(self):
        self.figure.clear()
        user_n, user_d = self.num_var.get(), self.den_var.get()

        is_correct = (user_n == self.correct_n and user_d == self.correct_d)

        if is_correct:
            self.success_var.set("✔ ПРАВИЛЬНО!")
            self._set_controls_state(tk.DISABLED)
        else:
            self.success_var.set("")

        ax1 = self.figure.add_subplot(1, 2, 1)
        ax2 = self.figure.add_subplot(1, 2, 2)

        # Малюємо початковий дріб (завдання)
        self.draw_fraction_pie(ax1, self.task_n, self.color1, self.task_d,
                               f"Початковий дріб\n$\\frac{{{self.task_n}}}{{{self.task_d}}}$")

        # **ВИПРАВЛЕНО:** Завжди малюємо дріб користувача для візуального порівняння
        # Використовуємо інший колір для наочності
        self.draw_fraction_pie(ax2, user_n, self.color2, user_d, f"Ваш дріб\n$\\frac{{{user_n}}}{{{user_d}}}$")

        self.figure.tight_layout(pad=3.0)
        self.canvas.draw()

    def draw_fraction_pie(self, ax, numerator, color, denominator, title):
        ax.set_title(title, pad=20, fontsize=24)
        ax.axis('equal')

        if numerator > 0 and denominator > 0:
            val = numerator / denominator
            # --- ЗМІНЕНО ТУТ ---
            # Використовуємо ":.3g" замість ":.3f", щоб видалити зайві нулі
            ax.text(0, -1.3, f"(= {val:.3g})", ha='center', va='center', fontsize=18, color='gray')

        sizes, colors = [], []
        if numerator > 0:
            sizes.append(numerator)
            colors.append(color)
        if denominator - numerator > 0:
            sizes.append(denominator - numerator)
            colors.append(self.empty_color)

        # Запобігаємо помилці, якщо дріб 0/0 (хоча логіка це не допускає)
        if not sizes:
            sizes, colors = [1], [self.empty_color]

        ax.pie(sizes, colors=colors, startangle=90, counterclock=False,
               wedgeprops={'edgecolor': 'black', 'linewidth': 1})

        # Малюємо розділювачі для наочності
        if denominator <= 40:
            for i in range(denominator):
                angle = np.deg2rad(90 - i * (360.0 / denominator))
                ax.plot([0, np.cos(angle)], [0, np.sin(angle)], color='black', lw=0.7, alpha=0.6)


if __name__ == "__main__":
    app = FractionReductionApp()
    app.mainloop()