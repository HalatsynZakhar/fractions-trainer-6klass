import tkinter as tk
from tkinter import ttk, font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.gridspec as gridspec
import numpy as np
import math
import random
from collections import Counter


class CollapsiblePane(ttk.Frame):
    """Секція, що згортається"""

    def __init__(self, parent, text="", *args, **options):
        super().__init__(parent, *args, **options)
        self.columnconfigure(0, weight=1)
        self.text = text
        self.is_open = tk.BooleanVar(value=True)
        self.title_frame = ttk.Frame(self)
        self.title_frame.grid(row=0, column=0, sticky="ew")
        self.toggle_button = ttk.Button(self.title_frame, text='▼ ' + text, command=self.toggle, style="Header.TButton")
        self.toggle_button.pack(fill="x", expand=True)
        self.sub_frame = ttk.Frame(self, padding=10)
        self.sub_frame.grid(row=1, column=0, sticky="nsew")

    def toggle(self):
        if self.is_open.get():
            self.sub_frame.grid_remove()
            self.toggle_button.configure(text='▶ ' + self.text)
            self.is_open.set(False)
        else:
            self.sub_frame.grid()
            self.toggle_button.configure(text='▼ ' + self.text)
            self.is_open.set(True)


class FractionVisualizerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Інтерактивний візуалізатор дробів (v. whiteboard final)")
        try:
            self.state('zoomed')
        except tk.TclError:
            self.attributes('-zoomed', True)

        self.MAX_DENOMINATOR = 100
        self.color1, self.color2, self.empty_color = 'deepskyblue', 'salmon', '#E0E0E0'
        self.history, self.history_index = [], -1
        self.solution_steps = []

        self.font_body = font.Font(family="Helvetica", size=16)
        self.font_title = font.Font(family="Helvetica", size=18, weight="bold")
        self.font_explanation = font.Font(family="Helvetica", size=17)
        self.font_slider_value = font.Font(family="Helvetica", size=17, weight="bold")
        self.font_header = font.Font(family="Helvetica", size=16, weight="bold")

        self.style = ttk.Style(self)
        self.style.configure("TLabel", font=self.font_body)
        self.style.configure("TButton", font=self.font_body, padding=10)
        self.style.configure("TScale", length=300)
        self.style.configure("Title.TLabel", font=self.font_title)
        self.style.configure("TCheckbutton", font=self.font_body, padding=8)
        self.style.configure("Header.TButton", font=self.font_header)

        self.num1_var, self.den1_var = tk.IntVar(), tk.IntVar()
        self.num2_var, self.den2_var = tk.IntVar(), tk.IntVar()
        self.show_lcm_var, self.show_full_solution_var = tk.BooleanVar(value=False), tk.BooleanVar(value=False)
        self.history_slider_var = tk.IntVar()
        self.solution_slider_var = tk.IntVar(value=0)
        self.solution_step_label_var = tk.StringVar(value="Крок: 0/0")

        main_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top_pane_frame = ttk.Frame(main_pane)
        top_pane_frame.columnconfigure(0, weight=1)
        main_pane.add(top_pane_frame, weight=5)

        task_frame = ttk.Frame(top_pane_frame)
        task_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.task_canvas = tk.Canvas(task_frame, height=60)
        self.task_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)

        history_frame = ttk.Frame(task_frame)
        history_frame.pack(side=tk.LEFT, padx=20)
        self.back_button = ttk.Button(history_frame, text="←", command=self._go_back)
        self.back_button.pack(side=tk.LEFT)
        self.history_slider = ttk.Scale(history_frame, from_=0, to=0, variable=self.history_slider_var,
                                        command=self._on_history_slider_change, length=200)
        self.history_slider.pack(side=tk.LEFT, padx=5)
        self.forward_button = ttk.Button(history_frame, text="→", command=self._go_forward)
        self.forward_button.pack(side=tk.LEFT)
        ttk.Button(history_frame, text="Нове завдання", command=self._generate_new_task).pack(side=tk.LEFT, padx=10)

        controls_pane = ttk.PanedWindow(top_pane_frame, orient=tk.HORIZONTAL)
        controls_pane.grid(row=1, column=0, sticky="nsew")
        top_pane_frame.rowconfigure(1, weight=1)

        pane1 = CollapsiblePane(controls_pane, text="Перший дріб")
        self.num1_scale, self.den1_scale = self._create_fraction_controls(pane1.sub_frame, self.num1_var, self.den1_var)
        controls_pane.add(pane1, weight=1)

        pane2 = CollapsiblePane(controls_pane, text="Другий дріб")
        self.num2_scale, self.den2_scale = self._create_fraction_controls(pane2.sub_frame, self.num2_var, self.den2_var)
        controls_pane.add(pane2, weight=1)

        bottom_pane_frame = ttk.Frame(main_pane)
        bottom_pane_frame.columnconfigure(0, weight=1)
        bottom_pane_frame.rowconfigure(1, weight=1)
        main_pane.add(bottom_pane_frame, weight=6)

        explanation_pane = CollapsiblePane(bottom_pane_frame, text="Пояснення та рішення")
        explanation_pane.grid(row=0, column=0, sticky="ew")

        solution_toolbar = ttk.Frame(explanation_pane.sub_frame)
        solution_toolbar.pack(fill="x", pady=5)
        ttk.Checkbutton(solution_toolbar, text="Пошук НСК", variable=self.show_lcm_var, command=self.visualize).pack(
            side=tk.LEFT)
        ttk.Checkbutton(solution_toolbar, text="Повне рішення", variable=self.show_full_solution_var,
                        command=self.visualize).pack(side=tk.LEFT, padx=10)

        self.solution_slider_frame = ttk.Frame(explanation_pane.sub_frame)
        self.solution_slider_frame.pack(fill="x", pady=10, padx=5)
        self.solution_slider = ttk.Scale(self.solution_slider_frame, from_=0, to=0, variable=self.solution_slider_var,
                                         command=self._on_solution_slider_change, length=400)
        self.solution_slider.pack(side=tk.LEFT, fill="x", expand=True)
        ttk.Label(self.solution_slider_frame, textvariable=self.solution_step_label_var).pack(side=tk.LEFT, padx=10)

        self.steps_frame = ttk.Frame(explanation_pane.sub_frame)
        self.steps_frame.pack(fill="both", expand=True)

        plot_frame = ttk.Frame(bottom_pane_frame)
        plot_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        self.figure = plt.figure(figsize=(14, 6), dpi=90)
        gs = gridspec.GridSpec(2, 3, figure=self.figure)
        self.ax1, self.ax2 = self.figure.add_subplot(gs[:, 0]), self.figure.add_subplot(gs[:, 1])
        self.ax3, self.ax4 = self.figure.add_subplot(gs[0, 2]), self.figure.add_subplot(gs[1, 2])
        self.canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._generate_new_task(is_initial=True)

    def _create_fraction_controls(self, parent, num_var, den_var):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        frame.columnconfigure(0, weight=1)
        num_frame, num_scale = self._create_slider_unit(frame, "Чисельник:", num_var)
        num_frame.grid(row=0, column=0, sticky="ew")
        ttk.Separator(frame, orient="horizontal").grid(row=1, column=0, sticky="ew", pady=20)
        den_frame, den_scale = self._create_slider_unit(frame, "Знаменник:", den_var)
        den_frame.grid(row=2, column=0, sticky="ew")
        return num_scale, den_scale

    def _create_slider_unit(self, parent, label_text, var):
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text=label_text).grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Button(frame, text="-", command=lambda v=var: self._adjust_value(v, -1)).grid(row=1, column=0, padx=(0, 5))
        scale = ttk.Scale(frame, from_=0, to=self.MAX_DENOMINATOR, variable=var,
                          command=lambda val, v=var: self._on_slider_change(val, v), orient="horizontal")
        scale.grid(row=1, column=1, sticky="ew")
        ttk.Button(frame, text="+", command=lambda v=var: self._adjust_value(v, 1)).grid(row=1, column=2, padx=5)
        ttk.Label(frame, textvariable=var, font=self.font_slider_value, width=4).grid(row=1, column=3, padx=(10, 0))
        return frame, scale

    def _update_task_display(self, n1, d1, n2, d2):
        self.task_canvas.delete("all")
        self.after(100, lambda: self._draw_task_fractions(n1, d1, n2, d2))

    def _draw_task_fractions(self, n1, d1, n2, d2):
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
        self.num1_scale.config(to=self.den1_var.get())
        if self.num1_var.get() > self.den1_var.get(): self.num1_var.set(self.den1_var.get())
        self.num2_scale.config(to=self.den2_var.get())
        if self.num2_var.get() > self.den2_var.get(): self.num2_var.set(self.den2_var.get())
        self.visualize()

    def _on_history_slider_change(self, value):
        new_index = int(float(value))
        if new_index != self.history_index:
            self.history_index = new_index
            self._load_state(self.history[self.history_index])

    def _on_solution_slider_change(self, value=None):
        current_step = self.solution_slider_var.get()
        max_steps = len(self.solution_steps) - 1
        if max_steps < 0: max_steps = 0
        self.solution_step_label_var.set(f"Крок: {current_step}/{max_steps}")
        for widget in self.steps_frame.winfo_children(): widget.destroy()
        for i in range(current_step + 1):
            if i < len(self.solution_steps):
                style, text = self.solution_steps[i]
                lbl = ttk.Label(self.steps_frame, text=text,
                                font=self.font_explanation if style == "normal" else self.font_title,
                                wraplength=self.steps_frame.winfo_width() - 20)
                lbl.pack(anchor="w", pady=2)

    def _generate_new_task(self, is_initial=False):
        d1, d2 = random.randint(4, 12), random.randint(4, 12)
        while d1 == d2 or math.gcd(d1, d2) > 1: d1, d2 = random.randint(4, 12), random.randint(4, 12)
        n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
        state = (n1, d1, n2, d2)
        if not is_initial:
            if self.history_index < len(self.history) - 1: self.history = self.history[:self.history_index + 1]
            self.history.append(state)
            self.history_index = len(self.history) - 1
        else:
            self.history.append(state); self.history_index = 0
        self.history_slider.config(to=len(self.history) - 1 if len(self.history) > 1 else 0)
        self._load_state(state)

    def _load_state(self, state):
        n1, d1, n2, d2 = state
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
            self.history_index -= 1
            self._load_state(self.history[self.history_index])

    def _go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
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
        ], lcm

    def visualize(self):
        num1, den1 = self.num1_var.get(), self.den1_var.get()
        num2, den2 = self.num2_var.get(), self.den2_var.get()
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]: ax.clear()

        self.draw_fraction_pie(self.ax1, [num1], [self.color1], den1, f"$\\frac{{{num1}}}{{{den1}}}$")
        self.draw_fraction_pie(self.ax2, [num2], [self.color2], den2, f"$\\frac{{{num2}}}{{{den2}}}$")
        self.ax2.axvline(x=1.6, color='grey', linestyle='--', linewidth=2, ymin=0.05, ymax=0.95)

        # ВИПРАВЛЕННЯ: `d2` змінено на `den2`
        if den1 == den2:
            self._display_sum_result(num1, num2, den1)
        else:
            self._display_lcm_prompt(num1, den1, num2, den2)

        self.figure.tight_layout(pad=2.0, h_pad=4.0)
        self.canvas.draw()

    def _display_sum_result(self, n1, n2, den):
        self.solution_slider_frame.pack_forget()
        for widget in self.steps_frame.winfo_children(): widget.destroy()

        sum_num = n1 + n2
        whole, frac = divmod(sum_num, den)
        title = f"Результат: $\\frac{{{sum_num}}}{{{den}}}$"
        if whole > 0: title += f" = {whole}" + (f" $\\frac{{{frac}}}{{{den}}}$" if frac > 0 else "")
        lbl = ttk.Label(self.steps_frame,
                        text=f"ЗАВДАННЯ ВИКОНАНО!\nЗнаменники однакові ({den}), додаємо чисельники: {n1} + {n2} = {sum_num}",
                        font=self.font_title)
        lbl.pack(anchor="w", pady=2)

        self.ax3.set_visible(True)
        if sum_num < den:
            self.ax4.set_visible(False)
            self.draw_fraction_pie(self.ax3, [n1, n2], [self.color1, self.color2], den, title)
        else:
            self.ax4.set_visible(True)
            first_pie_fill = min(n2, den - n1)
            second_pie_rem = n2 - first_pie_fill
            self.draw_fraction_pie(self.ax3, [n1, first_pie_fill], [self.color1, self.color2], den, title)
            if second_pie_rem > 0 or (frac == 0 and whole > 1):
                self.draw_fraction_pie(self.ax4, [second_pie_rem if second_pie_rem > 0 else den], [self.color2], den,
                                       "")
            else:
                self.ax4.set_visible(False)

    def _display_lcm_prompt(self, n1, d1, n2, d2):
        self.ax3.set_visible(True);
        self.ax4.set_visible(False)
        self.draw_placeholder(self.ax3, "Зведіть до\nспільного\nзнаменника!")
        for widget in self.steps_frame.winfo_children(): widget.destroy()

        if not (self.show_lcm_var.get() or self.show_full_solution_var.get()):
            self.solution_slider_frame.pack_forget()
            lbl = ttk.Label(self.steps_frame,
                            text="Знаменники різні. Поставте галочку 'Показати пошук НСК', щоб побачити рішення.",
                            font=self.font_explanation)
            lbl.pack(anchor="w", pady=2)
            return

        self.solution_slider_frame.pack(fill="x", pady=10, padx=5)

        self.solution_steps = [
            ("normal", f"Знаменники різні ({d1} ≠ {d2}). Потрібно звести дроби до спільного знаменника.")]
        lcm_explanation, lcm = self._get_detailed_lcm_explanation(d1, d2)
        self.solution_steps.extend(lcm_explanation)

        if self.show_full_solution_var.get():
            m1, m2 = lcm // d1, lcm // d2
            sol_text = [
                ("bold", "--- КРОК 3: ПОВНЕ РІШЕННЯ ---"),
                ("normal",
                 f"1. Домножимо дроби на їх додаткові множники:\n   ({n1}/{d1}) + ({n2}/{d2}) -> ({(n1 * m1)}/{lcm}) + ({(n2 * m2)}/{lcm})"),
                ("normal", f"2. Додамо чисельники:\n   = {(n1 * m1 + n2 * m2)}/{lcm}"),
                ("bold", f"3. Встановіть на повзунках знаменник '{lcm}'."),
            ]
            self.solution_steps.extend(sol_text)

        self.solution_slider.config(to=len(self.solution_steps) - 1 if self.solution_steps else 0)
        self.solution_slider_var.set(0)
        self._on_solution_slider_change()

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
            sizes.extend(n for n in numerators if n > 0)
            final_colors.extend(colors[:len(sizes)])
        if denominator - sum(numerators) > 0:
            sizes.append(denominator - sum(numerators))
            final_colors.append(self.empty_color)
        ax.pie(sizes, colors=final_colors, startangle=90, counterclock=False,
               wedgeprops={'edgecolor': 'black', 'linewidth': 1})
        if denominator <= 40:
            for i in range(denominator):
                angle = np.deg2rad(90 - i * (360.0 / denominator))
                ax.plot([0, np.cos(angle)], [0, np.sin(angle)], color='black', lw=0.7, alpha=0.6)

    def draw_placeholder(self, ax, text):
        ax.set_title("Результат", pad=25, fontsize=26)
        ax.axis('equal')
        ax.pie([1], colors=[self.empty_color], wedgeprops={'edgecolor': 'grey', 'linewidth': 1.5, 'linestyle': '--'})
        ax.text(0, 0, text, ha='center', va='center', fontsize=20, color='grey')


if __name__ == "__main__":
    app = FractionVisualizerApp()
    app.mainloop()