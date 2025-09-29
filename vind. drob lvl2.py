import tkinter as tk
from tkinter import ttk, font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.gridspec as gridspec
import numpy as np
import math
import random
from collections import Counter
import re


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
                    for i, part in enumerate(parts):
                        if i > 0:
                            ttk.Label(frac_frame, text="  ->  ", font=self.font_frac).pack(side=tk.LEFT, padx=10)
                        self.draw_fraction_expression(frac_frame, part.strip())
                else:
                    line_label = ttk.Label(frame, text=line, font=self.font_explanation, wraplength=700)
                    line_label.pack(anchor="w", pady=2)
                    frame.bind("<Configure>", lambda e, lbl=line_label: lbl.config(wraplength=e.width - 40))

    def draw_fraction_expression(self, parent, expression):
        tokens = re.split(r'(\s[+-]\s|=)', expression)
        for token in tokens:
            token = token.strip()
            if not token: continue
            if "/" in token:
                try:
                    if ' ' in token:
                        whole_part, frac_part = token.split(' ')
                        n_str, d_str = frac_part.split('/')
                        whole_label = ttk.Label(parent, text=f"{whole_part}", font=self.font_frac)
                        whole_label.pack(side=tk.LEFT, padx=(0, 5))
                    else:
                        n_str, d_str = token.replace('(', '').replace(')', '').split('/')
                except ValueError:
                    ttk.Label(parent, text=token, font=self.font_frac).pack(side=tk.LEFT)
                    continue
                canvas = tk.Canvas(parent, height=60, bg=self.cget('bg'), highlightthickness=0)
                canvas.pack(side=tk.LEFT)
                n_w, d_w = self.font_frac.measure(n_str), self.font_frac.measure(str(d_str))
                max_w = max(n_w, d_w) + 10
                canvas.config(width=max_w)
                canvas.create_text(max_w / 2, 15, text=n_str, font=self.font_frac, anchor="center")
                canvas.create_line(2, 30, max_w - 2, 30, width=3)
                canvas.create_text(max_w / 2, 45, text=d_str, font=self.font_frac, anchor="center")
            else:
                ttk.Label(parent, text=f" {token} ", font=self.font_frac).pack(side=tk.LEFT)


class FractionVisualizerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Інтерактивний тренажер: Віднімання мішаних чисел (Раціональний метод)")
        try:
            self.state('zoomed')
        except tk.TclError:
            self.attributes('-zoomed', True)

        self.MAX_CIRCLES = 4
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
        main_pane.add(top_pane_frame, weight=3)

        task_frame = ttk.Frame(top_pane_frame)
        task_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.task_canvas = tk.Canvas(task_frame, height=70)
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
        self.controls1 = self._create_fraction_controls(controls_frame, "Зменшуване", self.num1_var, self.den1_var, 0)
        self.controls2 = self._create_fraction_controls(controls_frame, "Від'ємник", self.num2_var, self.den2_var, 1)

        plot_frame = ttk.Frame(main_pane)
        main_pane.add(plot_frame, weight=7)
        self.figure = plt.figure(figsize=(12, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._generate_new_task()

    def _create_fraction_controls(self, parent, title, num_var, den_var, col):
        frame = ttk.Frame(parent)
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
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text=label_text).grid(row=0, column=0, columnspan=4, sticky="w")
        btn_minus = ttk.Button(frame, text="-", command=lambda v=var: self._adjust_value(v, -1))
        btn_minus.grid(row=1, column=0, padx=(0, 5))
        scale = ttk.Scale(frame, from_=0, to=100, variable=var,
                          command=lambda val, v=var: self._on_slider_change(val, v), orient="horizontal")
        scale.grid(row=1, column=1, sticky="ew")
        btn_plus = ttk.Button(frame, text="+", command=lambda v=var: self._adjust_value(v, 1))
        btn_plus.grid(row=1, column=2, padx=5)
        ttk.Label(frame, textvariable=var, font=self.font_slider_value, width=4).grid(row=1, column=3, padx=(10, 0))
        return {'frame': frame, 'scale': scale}

    def _adjust_value(self, var, delta):
        var.set(var.get() + delta)
        self._on_slider_change()

    def _on_slider_change(self, value=None, var=None):
        if var is not None and value is not None: var.set(int(float(value)))
        if self.den1_var.get() < 1: self.den1_var.set(1)
        if self.den2_var.get() < 1: self.den2_var.set(1)
        if self.num1_var.get() < 0: self.num1_var.set(0)
        if self.num2_var.get() < 0: self.num2_var.set(0)

        self.controls1['num']['scale'].config(to=self.den1_var.get() * self.MAX_CIRCLES)
        self.controls2['num']['scale'].config(to=self.den2_var.get() * self.MAX_CIRCLES)

        self.visualize()

    def _generate_new_task(self):
        while True:
            d1, d2 = random.randint(3, 8), random.randint(3, 8)
            if d1 != d2: break

        # Генеруємо зменшуване (завжди більше 1)
        whole1 = random.randint(1, 3)
        n1 = whole1 * d1 + random.randint(1, d1 - 1)

        # Генеруємо від'ємник (може бути > 1)
        while True:
            whole2 = random.randint(0, whole1)  # Від'ємник не може мати більше цілих
            frac_n2 = random.randint(1, d2 - 1)
            n2 = whole2 * d2 + frac_n2

            # Гарантуємо, що результат буде додатнім
            if n1 * d2 > n2 * d1:
                break

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

    def _update_task_display(self, n1, d1, n2, d2):
        self.task_canvas.delete("all")
        self.task_canvas.bind("<Configure>", lambda e: self._draw_task_fractions(n1, d1, n2, d2), add="+")
        self.update_idletasks()
        self._draw_task_fractions(n1, d1, n2, d2)

    def _draw_task_fractions(self, n1, d1, n2, d2):
        self.task_canvas.delete("all")
        canvas_w, canvas_h = self.task_canvas.winfo_width(), self.task_canvas.winfo_height()
        if canvas_w < 50: return

        font_whole = font.Font(family="Helvetica", size=30, weight="bold")
        font_frac = font.Font(family="Helvetica", size=18, weight="bold")

        prefix_text = "Завдання: "
        prefix_len = font.Font(font=self.font_body).measure(prefix_text)
        self.task_canvas.create_text(10, canvas_h / 2, text=prefix_text, font=self.font_body, anchor="w", fill="navy")
        x_pos = prefix_len + 20

        def draw_frac(n, d, x):
            if d == 0: return x
            whole, frac_n = divmod(n, d)

            if whole > 0:
                whole_str = str(whole)
                whole_w = font_whole.measure(whole_str)
                self.task_canvas.create_text(x + whole_w / 2, canvas_h / 2, text=whole_str, font=font_whole,
                                             anchor="center")
                x += whole_w + 5

            if frac_n > 0 or (whole == 0 and n >= 0):
                n_str, d_str = str(frac_n), str(d)
                n_w, d_w = font_frac.measure(n_str), font_frac.measure(d_str)
                max_w = max(n_w, d_w) + 10

                self.task_canvas.create_text(x + max_w / 2, canvas_h / 2 - 12, text=n_str, font=font_frac,
                                             anchor="center")
                self.task_canvas.create_line(x, canvas_h / 2, x + max_w, canvas_h / 2, width=2.5)
                self.task_canvas.create_text(x + max_w / 2, canvas_h / 2 + 12, text=d_str, font=font_frac,
                                             anchor="center")
                x += max_w

            return x + 30

        x_pos = draw_frac(n1, d1, x_pos)
        self.task_canvas.create_text(x_pos, canvas_h / 2, text="-", font=font_whole, anchor="center")
        x_pos += 30
        x_pos = draw_frac(n2, d2, x_pos)

    def _set_controls_state(self, state):
        for part in ['scale']:
            self.controls1['num'][part].config(state=state)
            self.controls1['den'][part].config(state=state)
            self.controls2['num'][part].config(state=state)
            self.controls2['den'][part].config(state=state)

    def visualize(self):
        self.figure.clear()
        n1, d1 = self.num1_var.get(), self.den1_var.get()
        n2, d2 = self.num2_var.get(), self.den2_var.get()
        self.success_var.set("")

        if d1 > 0 and d1 == d2:
            user_n, user_d = n1 - n2, d1
            correct_n, correct_d = self.task_n1 * self.task_d2 - self.task_n2 * self.task_d1, self.task_d1 * self.task_d2
            if user_n >= 0 and user_n * correct_d == user_d * correct_d:
                if math.gcd(user_n, user_d) > 1:
                    self.success_var.set("✔ Правильно! Спробуйте ще скоротити вашу відповідь.")
                else:
                    self.success_var.set("✔ ВІДМІННО! Правильна відповідь.")
                self._set_controls_state(tk.DISABLED)

        gs_main = gridspec.GridSpec(2, 3, figure=self.figure, height_ratios=[1, 9], hspace=0.1)

        ax_title1 = self.figure.add_subplot(gs_main[0, 0]);
        ax_title1.axis('off')
        ax_title2 = self.figure.add_subplot(gs_main[0, 1]);
        ax_title2.axis('off')
        ax_title3 = self.figure.add_subplot(gs_main[0, 2]);
        ax_title3.axis('off')

        ax_title1.set_title(self.format_fraction_title("Зменшуване", n1, d1), fontsize=18)
        ax_title2.set_title(self.format_fraction_title("Від'ємник", n2, d2), fontsize=18)

        # Створюємо єдину вісь для кожної групи кружечків
        ax1 = self.figure.add_subplot(gs_main[1, 0])
        ax2 = self.figure.add_subplot(gs_main[1, 1])
        ax3 = self.figure.add_subplot(gs_main[1, 2])

        self._draw_overlapping_circles(ax1, n1, d1, self.color1)
        self._draw_overlapping_circles(ax2, n2, d2, self.color2)

        if d1 == d2 and n1 >= n2:
            res_n, res_d = n1 - n2, d1
            ax_title3.set_title(self.format_fraction_title("Різниця", res_n, res_d), fontsize=18)
            self._draw_overlapping_circles(ax3, res_n, res_d, self.color1)
        else:
            ax_title3.set_title("Різниця", fontsize=18)
            self.draw_placeholder(ax3)

        self.figure.tight_layout(pad=2.0)
        self.canvas.draw()

    def _format_fraction_display(self, n, d, for_matplotlib=True):
        if d == 0: return "N/A", "N/A"

        frac_template = "$\\frac{{{n}}}{{{d}}}$" if for_matplotlib else "{n}/{d}"
        mixed_template = "${whole}\\frac{{{n}}}{{{d}}}$" if for_matplotlib else "{whole} {n}/{d}"

        improper = frac_template.format(n=n, d=d)
        if n < d: return improper, improper

        whole, frac_n = divmod(n, d)
        if frac_n == 0:
            mixed = f"${whole}$" if for_matplotlib else str(whole)
        else:
            mixed = mixed_template.format(whole=whole, n=frac_n, d=d)

        return mixed, improper

    def format_fraction_title(self, base_title, n, d):
        if d == 0 or (n == 0 and d == 1): return base_title
        mixed, improper = self._format_fraction_display(n, d)
        return f"{base_title}\n{mixed} = {improper}" if mixed != improper else f"{base_title}\n{improper}"

    def _draw_overlapping_circles(self, ax, n, d, color):
        ax.axis('off')
        ax.set_aspect('equal', adjustable='box')

        if d == 0: return
        whole, frac_n = divmod(n, d)

        total_circles = whole + (1 if frac_n > 0 else 0)
        if total_circles == 0:
            self.draw_fraction_pie(ax, [0], [color], d, center=(0, 0))
            return

        radius = 1.0
        overlap = 0.65  # 1.0 - жодного накладання, 0.5 - сильне
        step = 2 * radius * overlap

        total_width = (total_circles - 1) * step + 2 * radius
        start_x = -total_width / 2 + radius

        for i in range(whole):
            self.draw_fraction_pie(ax, [d], [color], d, center=(start_x + i * step, 0), radius=radius)

        if frac_n > 0:
            self.draw_fraction_pie(ax, [frac_n], [color], d, center=(start_x + whole * step, 0), radius=radius)

        ax.set_xlim(-total_width / 2 - 0.1, total_width / 2 + 0.1)
        ax.set_ylim(-radius - 0.1, radius + 0.1)

    def _build_solution_for_task(self):
        n1, d1, n2, d2 = self.task_n1, self.task_d1, self.task_n2, self.task_d2
        self.solution_steps = []

        w1, f_n1 = divmod(n1, d1)
        w2, f_n2 = divmod(n2, d2)

        self.solution_steps.append(("bold", "--- КРОК 1: ЗВЕДЕННЯ ДРОБОВИХ ЧАСТИН ДО СПІЛЬНОГО ЗНАМЕННИКА ---"))
        lcm = (d1 * d2) // math.gcd(d1, d2)
        m1, m2 = lcm // d1, lcm // d2

        new_f_n1 = f_n1 * m1
        new_f_n2 = f_n2 * m2

        self.solution_steps.append(("normal",
                                    f"НСК для {d1} і {d2} є {lcm}.\nДомножимо дробові частини:\n({f_n1}/{d1}) -> ({new_f_n1}/{lcm})\n({f_n2}/{d2}) -> ({new_f_n2}/{lcm})"))

        if new_f_n1 < new_f_n2:
            self.solution_steps.append(("bold", "--- КРОК 2: ПОЗИЧАННЯ ОДИНИЦІ ---"))
            self.solution_steps.append(("normal",
                                        f"Оскільки {new_f_n1} < {new_f_n2}, ми не можемо відняти дроби.\nПозичаємо 1 від цілої частини ({w1})."))
            w1 -= 1
            new_f_n1 += lcm
            self.solution_steps.append(("normal", f"Отримуємо: {w1} і ({new_f_n1}/{lcm})"))

        final_w = w1 - w2
        final_f_n = new_f_n1 - new_f_n2

        self.solution_steps.append(("bold", "--- КРОК 3: ВІДНІМАННЯ ---"))
        self.solution_steps.append(("normal", f"1. Віднімаємо цілі частини: {w1} - {w2} = {final_w}"))
        self.solution_steps.append(
            ("normal", f"2. Віднімаємо дробові частини: ({new_f_n1}/{lcm}) - ({new_f_n2}/{lcm}) = ({final_f_n}/{lcm})"))

        common_divisor = math.gcd(final_f_n, lcm)
        if common_divisor > 1:
            self.solution_steps.append(("bold", "--- КРОК 4: СКОРОЧЕННЯ ДРОБОВОЇ ЧАСТИНИ ---"))
            reduced_n, reduced_d = final_f_n // common_divisor, lcm // common_divisor
            self.solution_steps.append(("normal", f"({final_f_n}/{lcm}) -> ({reduced_n}/{reduced_d})"))
            final_f_n, lcm = reduced_n, reduced_d

        final_answer = ""
        if final_w > 0:
            final_answer += str(final_w)
            if final_f_n > 0:
                final_answer += f" {final_f_n}/{lcm}"
        elif final_f_n > 0:
            final_answer = f"{final_f_n}/{lcm}"
        else:
            final_answer = "0"

        self.solution_steps.append(("bold", f"Кінцева відповідь: {final_answer}"))

    def draw_fraction_pie(self, ax, numerators, colors, denominator, center=(0, 0), radius=1.0):
        sizes, final_colors = [], []
        total_num = sum(numerators)
        if total_num > 0:
            sizes.extend([n for n in numerators if n > 0])
            final_colors.extend(colors[:len(sizes)])
        if denominator - total_num > 0:
            sizes.append(denominator - total_num)
            final_colors.append(self.empty_color)
        if not sizes: sizes, final_colors = [1], [self.empty_color]

        ax.pie(sizes, radius=radius, center=center, colors=final_colors, startangle=90, counterclock=False,
               wedgeprops={'edgecolor': 'black', 'linewidth': 0.8})

    def draw_placeholder(self, ax):
        ax.axis('off')
        ax.text(0.5, 0.5, "Зведіть до\nспільного\nзнаменника!", ha='center', va='center', fontsize=20, color='grey',
                transform=ax.transAxes, wrap=True)

    def _open_solution_window(self):
        self._build_solution_for_task()
        SolutionWindow(self, self.solution_steps)


if __name__ == "__main__":
    app = FractionVisualizerApp()
    app.mainloop()