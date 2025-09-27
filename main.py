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
    """Окреме вікно для показу рішення"""

    def __init__(self, parent, solution_steps):
        super().__init__(parent)
        self.title("Рішення завдання")
        try:
            self.state('zoomed')
        except tk.TclError:
            self.attributes('-zoomed', True)
        self.transient(parent)

        self.font_explanation = font.Font(family="Helvetica", size=18)
        self.font_title = font.Font(family="Helvetica", size=20, weight="bold")
        self.font_body = font.Font(family="Helvetica", size=16)

        self.steps_labels = []
        self.solution_steps = solution_steps

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        slider_var = tk.IntVar(value=len(solution_steps) - 1)
        self.slider_var = slider_var

        slider_frame = ttk.Frame(main_frame)
        slider_frame.pack(fill="x")
        slider = ttk.Scale(slider_frame, from_=0, to=len(solution_steps) - 1, variable=slider_var,
                           command=self._on_slider_change)
        slider.pack(side=tk.LEFT, fill="x", expand=True)
        self.step_label_var = tk.StringVar()
        ttk.Label(slider_frame, textvariable=self.step_label_var, font=self.font_body).pack(side=tk.LEFT, padx=10)

        self.steps_frame = ttk.Frame(main_frame, padding=10)
        self.steps_frame.pack(fill="both", expand=True)

        self.steps_frame.bind("<Configure>", self._on_configure)
        self._on_slider_change()

    def _on_slider_change(self, value=None):
        current_step = self.slider_var.get()
        max_steps = len(self.solution_steps) - 1
        self.step_label_var.set(f"Крок: {current_step}/{max_steps}")
        for widget in self.steps_frame.winfo_children(): widget.destroy()

        self.steps_labels.clear()
        for i in range(current_step + 1):
            if i < len(self.solution_steps):
                style, text = self.solution_steps[i]
                lbl = ttk.Label(self.steps_frame, text=text,
                                font=self.font_explanation if style == "normal" else self.font_title)
                lbl.pack(anchor="w", pady=5, padx=10)
                self.steps_labels.append(lbl)
        self.update_wraplength()

    def _on_configure(self, event):
        self.update_wraplength()

    def update_wraplength(self):
        width = self.steps_frame.winfo_width()
        for label in self.steps_labels:
            label.config(wraplength=width - 40)


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
        self.history, self.history_index = [], -1
        self.solution_steps = []
        self.task_n1, self.task_d1, self.task_n2, self.task_d2, self.task_lcm = 0, 1, 0, 1, 1

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
        self.history_slider_var = tk.IntVar()
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

        history_frame = ttk.Frame(task_frame)
        history_frame.pack(side=tk.LEFT, padx=20)
        self.success_label = ttk.Label(history_frame, textvariable=self.success_var, style="Success.TLabel")
        self.success_label.pack(side=tk.LEFT, padx=20)
        self.back_button = ttk.Button(history_frame, text="←", command=self._go_back)
        self.back_button.pack(side=tk.LEFT)
        self.history_slider = ttk.Scale(history_frame, from_=0, to=0, variable=self.history_slider_var,
                                        command=self._on_history_slider_change, length=200)
        self.history_slider.pack(side=tk.LEFT, padx=5)
        self.forward_button = ttk.Button(history_frame, text="→", command=self._go_forward)
        self.forward_button.pack(side=tk.LEFT)
        ttk.Button(history_frame, text="Нове завдання", command=self._generate_new_task).pack(side=tk.LEFT, padx=10)
        ttk.Button(history_frame, text="Показати рішення", command=self._open_solution_window).pack(side=tk.LEFT,
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

        self._generate_new_task(is_initial=True)

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
        self.task_canvas.bind("<Configure>", lambda e: self._draw_task_fractions(n1, d1, n2, d2))

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

    def _on_history_slider_change(self, value):
        new_index = int(float(value))
        if new_index != self.history_index:
            self.history_index = new_index
            self._load_state(self.history[self.history_index])

    def _open_solution_window(self):
        self._build_solution_for_task()
        SolutionWindow(self, self.solution_steps)

    def _set_controls_state(self, state):
        for control_group in [self.controls1, self.controls2]:
            for part in ['num', 'den']:
                control_group[part]['scale'].config(state=state)
                control_group[part]['plus'].config(state=state)
                control_group[part]['minus'].config(state=state)

    def _generate_new_task(self, is_initial=False):
        d1, d2 = random.randint(4, 12), random.randint(4, 12)
        while d1 == d2 or math.gcd(d1, d2) > 1: d1, d2 = random.randint(4, 12), random.randint(4, 12)
        n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
        state = (n1, d1, n2, d2)
        if not is_initial:
            if self.history_index < len(self.history) - 1: self.history = self.history[:self.history_index + 1]
            self.history.append(state);
            self.history_index = len(self.history) - 1
        else:
            self.history.append(state); self.history_index = 0
        self.history_slider.config(to=len(self.history) - 1 if len(self.history) > 1 else 0)
        self._load_state(state)

    def _load_state(self, state):
        self._set_controls_state(tk.NORMAL)
        self.success_var.set("")
        n1, d1, n2, d2 = state
        self.task_n1, self.task_d1, self.task_n2, self.task_d2 = n1, d1, n2, d2
        self.task_lcm = (d1 * d2) // math.gcd(d1, d2)
        self.num1_var.set(n1);
        self.den1_var.set(d1)
        self.num2_var.set(n2);
        self.den2_var.set(d2)
        self._update_task_display(n1, d1, n2, d2)
        self._update_history_buttons_state()
        self.history_slider_var.set(self.history_index)
        self._on_slider_change()

    def _go_back(self):
        if self.history_index > 0:
            self.history_index -= 1;
            self._load_state(self.history[self.history_index])

    def _go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1;
            self._load_state(self.history[self.history_index])

    def _update_history_buttons_state(self):
        self.back_button.config(state=tk.NORMAL if self.history_index > 0 else tk.DISABLED)
        self.forward_button.config(state=tk.NORMAL if self.history_index < len(self.history) - 1 else tk.DISABLED)

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
                lcm_factors_list.append(factor); missing_factors.append(str(factor))
        lcm = math.prod(lcm_factors_list)
        return [
            ("bold", "--- КРОК 1: ПОШУК НСК ---"),
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
        sum_num = num1 + num2

        task_new_n1 = self.task_n1 * (self.task_lcm // self.task_d1)
        task_new_n2 = self.task_n2 * (self.task_lcm // self.task_d2)
        is_correct = (den1 == self.task_lcm and den2 == self.task_lcm and num1 == task_new_n1 and num2 == task_new_n2)

        if is_correct:
            self.success_var.set("✔ ПРАВИЛЬНО!")
            self._set_controls_state(tk.DISABLED)
        else:
            self.success_var.set("")

        # --- Динамічне компонування ---
        if den1 == den2 and sum_num >= den1:
            gs = gridspec.GridSpec(2, 3, figure=self.figure)
            ax1, ax2 = self.figure.add_subplot(gs[:, 0]), self.figure.add_subplot(gs[:, 1])
            ax3, ax4 = self.figure.add_subplot(gs[0, 2]), self.figure.add_subplot(gs[1, 2])
        else:
            gs = gridspec.GridSpec(1, 3, figure=self.figure)
            ax1, ax2 = self.figure.add_subplot(gs[0]), self.figure.add_subplot(gs[1])
            ax3 = self.figure.add_subplot(gs[2])
            ax4 = None

        self.draw_fraction_pie(ax1, [num1], [self.color1], den1, f"Перший дріб: $\\frac{{{num1}}}{{{den1}}}$")
        self.draw_fraction_pie(ax2, [num2], [self.color2], den2, f"Другий дріб: $\\frac{{{num2}}}{{{den2}}}$")
        ax2.axvline(x=1.6, color='grey', linestyle='--', linewidth=2, ymin=0.05, ymax=0.95)

        if den1 == den2:
            whole, frac = divmod(sum_num, den1)
            title = f"$\\frac{{{num1}}}{{{den1}}} + \\frac{{{num2}}}{{{den1}}} = \\frac{{{sum_num}}}{{{den1}}}$"
            if whole > 0: title += f" = {whole}" + (f" $\\frac{{{frac}}}{{{den1}}}$" if frac > 0 else "")

            if sum_num < den1:
                self.draw_fraction_pie(ax3, [num1, num2], [self.color1, self.color2], den1, title)
            else:
                first_fill = min(num2, den1 - num1);
                second_rem = num2 - first_fill
                self.draw_fraction_pie(ax3, [num1, first_fill], [self.color1, self.color2], den1, title)
                if ax4:
                    if second_rem > 0 or (frac == 0 and whole > 1):
                        self.draw_fraction_pie(ax4, [second_rem if second_rem > 0 else den1], [self.color2], den1,
                                               "Дробова частина")
        else:
            self.draw_placeholder(ax3, "Результат")

        self.figure.tight_layout(pad=2.0, h_pad=4.0)
        self.canvas.draw()

    def _build_solution_for_task(self):
        n1, d1, n2, d2 = self.task_n1, self.task_d1, self.task_n2, self.task_d2
        self.solution_steps = self._get_detailed_lcm_explanation(d1, d2)
        lcm = self.task_lcm
        m1, m2 = lcm // d1, lcm // d2
        sol_text = [
            ("bold", "--- КРОК 3: ПОВНЕ РІШЕННЯ ЗАВДАННЯ ---"),
            ("normal",
             f"1. Домножимо дроби із ЗАВДАННЯ на їх додаткові множники:\n   ({n1}/{d1}) + ({n2}/{d2}) -> ({(n1 * m1)}/{lcm}) + ({(n2 * m2)}/{lcm})"),
            ("normal", f"2. Додамо чисельники:\n   = {(n1 * m1 + n2 * m2)}/{lcm}"),
            ("bold", f"3. Ваша мета: встановити на повзунках знаменник '{lcm}' та відповідні нові чисельники."),
        ]
        self.solution_steps.extend(sol_text)

    def draw_fraction_pie(self, ax, numerators, colors, denominator, title):
        ax.set_title(title, pad=25, fontsize=26)
        ax.axis('equal')
        total_num = sum(numerators)
        if total_num > 0 and denominator > 0:
            val, rounded_val = total_num / denominator, round(total_num / denominator, 2)
            prefix = "≈" if abs(val - rounded_val) > 1e-9 else "="
            ax.text(0, -1.4, f"({prefix} {rounded_val})", ha='center', va='center', fontsize=18, color='gray')
        sizes, final_colors = [], []
        if sum(numerators) > 0:
            sizes.extend(n for n in numerators if n > 0);
            final_colors.extend(colors[:len(sizes)])
        if denominator - sum(numerators) > 0:
            sizes.append(denominator - sum(numerators));
            final_colors.append(self.empty_color)
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
    SolutionWindow.font_body = font.Font(family="Helvetica", size=16)  # Pass font to the class
    app.mainloop()