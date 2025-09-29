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
        self.title("Інтерактивний тренажер: Додавання (Ручне перетворення)")
        try:
            self.state('zoomed')
        except tk.TclError:
            self.attributes('-zoomed', True)

        self.MAX_CIRCLES = 4
        self.MAX_SLIDER_VAL = 100
        self.color1, self.color2, self.empty_color = 'deepskyblue', 'salmon', '#E0E0E0'
        self.task_n1, self.task_d1, self.task_n2, self.task_d2 = 0, 1, 0, 1  # Numerators and Denominators for the task
        self.correct_result_n, self.correct_result_d = 0, 1  # Final correct result

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
        self.style.configure("Error.TLabel", font=self.font_success, foreground="red")

        self.whole1_var = tk.IntVar()
        self.num1_var = tk.IntVar()
        self.den1_var = tk.IntVar()
        self.whole2_var = tk.IntVar()
        self.num2_var = tk.IntVar()
        self.den2_var = tk.IntVar()
        self.success_var = tk.StringVar()
        self.result_status_var = tk.StringVar()  # For displaying specific error/success messages

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
        self.result_status_label = ttk.Label(toolbar_frame, textvariable=self.result_status_var, style="Success.TLabel")
        self.result_status_label.pack(side=tk.LEFT, padx=20)
        ttk.Button(toolbar_frame, text="Нове завдання", command=self._generate_new_task).pack(side=tk.LEFT, padx=10)
        ttk.Button(toolbar_frame, text="Показати рішення", command=self._open_solution_window).pack(side=tk.LEFT,
                                                                                                    padx=10)

        controls_frame = ttk.Frame(top_pane_frame)
        controls_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        controls_frame.columnconfigure(0, weight=1);
        controls_frame.columnconfigure(1, weight=1)

        self.controls1 = self._create_fraction_controls(controls_frame, "Перший доданок", self.whole1_var,
                                                        self.num1_var,
                                                        self.den1_var, 0)
        self.controls2 = self._create_fraction_controls(controls_frame, "Другий доданок", self.whole2_var,
                                                        self.num2_var,
                                                        self.den2_var, 1)

        plot_frame = ttk.Frame(main_pane)
        main_pane.add(plot_frame, weight=7)
        self.figure = plt.figure(figsize=(12, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._generate_new_task()

    def _create_fraction_controls(self, parent, title, whole_var, num_var, den_var, col):
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=col, padx=20, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=title, style="Title.TLabel").pack(pady=(0, 20))

        whole_widgets = self._create_slider_unit(frame, "Ціла частина:", whole_var, is_slider=False)
        whole_widgets['frame'].pack(pady=5, fill="x", expand=True)
        ttk.Separator(frame, orient="horizontal").pack(pady=15, fill="x", expand=True)

        num_widgets = self._create_slider_unit(frame, "Чисельник:", num_var)
        num_widgets['frame'].pack(pady=5, fill="x", expand=True)
        ttk.Separator(frame, orient="horizontal").pack(pady=15, fill="x", expand=True)

        den_widgets = self._create_slider_unit(frame, "Знаменник:", den_var)
        den_widgets['frame'].pack(pady=5, fill="x", expand=True)

        return {'frame': frame, 'whole': whole_widgets, 'num': num_widgets, 'den': den_widgets}

    def _create_slider_unit(self, parent, label_text, var, is_slider=True):
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text=label_text).grid(row=0, column=0, columnspan=4, sticky="w")

        scale = None
        if is_slider:
            scale = ttk.Scale(frame, from_=0, to=self.MAX_SLIDER_VAL, variable=var,
                              command=lambda val, v=var: self._on_slider_change(val, v), orient="horizontal")
            scale.grid(row=1, column=1, sticky="ew")
        else:
            ttk.Frame(frame).grid(row=1, column=1, sticky="ew")  # Placeholder for alignment

        btn_minus = ttk.Button(frame, text="-", command=lambda v=var: self._adjust_value(v, -1))
        btn_minus.grid(row=1, column=0, padx=(0, 5))
        btn_plus = ttk.Button(frame, text="+", command=lambda v=var: self._adjust_value(v, 1))
        btn_plus.grid(row=1, column=2, padx=5)

        val_label = ttk.Label(frame, textvariable=var, font=self.font_slider_value, width=4)
        val_label.grid(row=1, column=3, padx=(10, 0))

        return {'frame': frame, 'scale': scale, 'plus': btn_plus, 'minus': btn_minus}

    def _adjust_value(self, var, delta):
        new_val = var.get() + delta
        # Ensure values don't go below 0 for whole and numerator, below 1 for denominator
        if var == self.den1_var or var == self.den2_var:
            if new_val < 1: new_val = 1
        else:  # whole and numerator
            if new_val < 0: new_val = 0
        var.set(new_val)
        self._on_slider_change()

    def _on_slider_change(self, value=None, var=None):
        if var is not None and value is not None: var.set(int(float(value)))

        # Ensure denominators are at least 1
        if self.den1_var.get() == 0: self.den1_var.set(1)
        if self.den2_var.get() == 0: self.den2_var.set(1)

        # Ensure numerators are not larger than denominators. This is crucial
        # for proper display and interaction. If user sets num > den, it should
        # be automatically converted to mixed fraction, or at least visually
        # clamped for display logic. For this trainer, we'll allow it as an
        # intermediate step for the user to correct, but the _check_user_answer
        # will guide them.
        if self.num1_var.get() < 0: self.num1_var.set(0)
        if self.num2_var.get() < 0: self.num2_var.set(0)
        if self.whole1_var.get() < 0: self.whole1_var.set(0)
        if self.whole2_var.get() < 0: self.whole2_var.set(0)

        self.visualize()
        self._check_user_answer()  # Check the answer on every change

    def _generate_new_task(self):
        # Generate d1, d2 that are different for a real challenge
        while True:
            d1 = random.randint(3, 8)
            d2 = random.randint(3, 8)
            if d1 != d2:  # We want different denominators for this task type
                break

        # Generate whole1 and frac_n1
        whole1 = random.randint(0, 2)  # Can be 0 for a pure fraction
        frac_n1 = random.randint(1, d1 - 1)
        n1 = whole1 * d1 + frac_n1  # Store as improper fraction for internal calculation

        # Generate whole2 and frac_n2
        whole2 = random.randint(0, 2)
        frac_n2 = random.randint(1, d2 - 1)
        n2 = whole2 * d2 + frac_n2  # Store as improper fraction

        self._load_state((n1, d1, n2, d2))
        self._calculate_correct_result(n1, d1, n2, d2)

    def _calculate_correct_result(self, n1_orig, d1_orig, n2_orig, d2_orig):
        """Calculates the final correct simplified result of the task."""
        lcm = (d1_orig * d2_orig) // math.gcd(d1_orig, d2_orig)

        # Convert to improper fractions with common denominator
        common_n1 = n1_orig * (lcm // d1_orig)
        common_n2 = n2_orig * (lcm // d2_orig)

        # Perform addition
        result_n_improper = common_n1 + common_n2
        result_d = lcm

        # Simplify the result
        common_divisor = math.gcd(result_n_improper, result_d)
        self.correct_result_n = result_n_improper // common_divisor
        self.correct_result_d = result_d // common_divisor

    def _load_state(self, state):
        self._set_controls_state(tk.NORMAL)
        self.result_status_var.set("")
        self.success_var.set("")  # Clear success message
        n1, d1, n2, d2 = state
        self.task_n1, self.task_d1, self.task_n2, self.task_d2 = n1, d1, n2, d2

        w1, f_n1 = divmod(n1, d1)
        w2, f_n2 = divmod(n2, d2)

        # Set initial values for user input to the original task fractions
        self.whole1_var.set(w1)
        self.num1_var.set(f_n1)
        self.den1_var.set(d1)
        self.whole2_var.set(w2)
        self.num2_var.set(f_n2)
        self.den2_var.set(d2)

        self._update_task_display(n1, d1, n2, d2)
        self._on_slider_change()  # This will trigger visualize and check_user_answer

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

            if frac_n > 0 or (whole == 0 and n >= 0 and d != 0):  # Display 0/d if whole is 0 and frac_n is 0
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
        self.task_canvas.create_text(x_pos, canvas_h / 2, text="+", font=font_whole, anchor="center")
        x_pos += 30
        x_pos = draw_frac(n2, d2, x_pos)

    def _set_controls_state(self, state):
        for ctrl_group in [self.controls1, self.controls2]:
            for key in ['whole', 'num', 'den']:
                widgets = ctrl_group[key]
                widgets['plus'].config(state=state)
                widgets['minus'].config(state=state)
                if widgets['scale']:
                    widgets['scale'].config(state=state)

    def visualize(self):
        self.figure.clear()
        w1, n1, d1 = self.whole1_var.get(), self.num1_var.get(), self.den1_var.get()
        w2, n2, d2 = self.whole2_var.get(), self.num2_var.get(), self.den2_var.get()

        # Safely handle d=0 before calculating total_n
        total_n1 = w1 * d1 + n1 if d1 != 0 else n1
        total_n2 = w2 * d2 + n2 if d2 != 0 else n2

        gs_main = gridspec.GridSpec(2, 3, figure=self.figure, height_ratios=[1, 9], hspace=0.1)
        ax_title1, ax_title2, ax_title3 = (self.figure.add_subplot(gs_main[0, i], facecolor='none') for i in range(3))
        for ax in [ax_title1, ax_title2, ax_title3]: ax.axis('off')

        ax_title1.set_title(self.format_user_input_title("Перший доданок", w1, n1, d1), fontsize=18)
        ax_title2.set_title(self.format_user_input_title("Другий доданок", w2, n2, d2), fontsize=18)
        ax_title3.set_title("Сума", fontsize=18)  # Default title

        ax1, ax2, ax3 = (self.figure.add_subplot(gs_main[1, i]) for i in range(3))
        self._draw_overlapping_circles(ax1, total_n1, d1, self.color1)
        self._draw_overlapping_circles(ax2, total_n2, d2, self.color2)

        # Draw placeholder for the result initially
        self.draw_placeholder(ax3, "Зведіть до спільного знаменника")

        # --- NEW LOGIC: If denominators are already equal, show the sum in the third plot ---
        if d1 == d2 and d1 != 0:
            sum_n = n1 + n2
            sum_w = w1 + w2

            # Convert any improper fraction part to whole numbers for display
            if sum_n >= d1:
                sum_w += sum_n // d1
                sum_n %= d1

            # Important: Only draw if it's the final correct step for the user's current input
            # This part will be refined in _check_user_answer for final validation.
            # Here, we just *show* the sum if denominators match.
            self._draw_overlapping_circles(ax3, sum_w * d1 + sum_n, d1, 'green')
            ax_title3.set_title(self.format_user_input_title("Сума", sum_w, sum_n, d1), fontsize=18)

        self.figure.tight_layout(pad=2.0)
        self.canvas.draw()

    def _check_user_answer(self):
        self.result_status_var.set("")  # Clear previous status
        self.result_status_label.config(style="Success.TLabel")  # Reset style

        w1_user, n1_user, d1_user = self.whole1_var.get(), self.num1_var.get(), self.den1_var.get()
        w2_user, n2_user, d2_user = self.whole2_var.get(), self.num2_var.get(), self.den2_var.get()

        # Handle division by zero for user input
        if d1_user == 0 or d2_user == 0:
            self.result_status_var.set("Знаменник не може бути нулем!")
            self.result_status_label.config(style="Error.TLabel")
            return

        # Step 1: Check if denominators are equal
        if d1_user != d2_user:
            self.result_status_var.set("Зведіть до спільного знаменника!")
            self.result_status_label.config(style="Error.TLabel")
            return

        # Denominators are equal, proceed with addition
        common_d = d1_user

        # Calculate user's current full sum (improper fraction for comparison)
        user_total_n_improper = (w1_user * common_d + n1_user) + (w2_user * common_d + n2_user)

        # Simplify the user's current calculated sum
        common_divisor_user = math.gcd(user_total_n_improper, common_d)
        simplified_user_n = user_total_n_improper // common_divisor_user
        simplified_user_d = common_d // common_divisor_user

        # Compare with the pre-calculated correct result
        if simplified_user_n == self.correct_result_n and simplified_user_d == self.correct_result_d:
            self.result_status_var.set("✔ ВІДМІННО! Рішення правильне.")
            self.result_status_label.config(style="Success.TLabel")
            self._set_controls_state(tk.DISABLED)

            # Now, visualize the correct result in the third plot definitively
            gs_main = gridspec.GridSpec(2, 3, figure=self.figure, height_ratios=[1, 9], hspace=0.1)
            ax_title3 = self.figure.add_subplot(gs_main[0, 2], facecolor='none')
            ax_title3.axis('off')

            ax3 = self.figure.add_subplot(gs_main[1, 2])
            self._draw_overlapping_circles(ax3, self.correct_result_n, self.correct_result_d, self.color1)

            # Update title to show the final simplified mixed fraction if applicable
            final_w_display, final_n_display = divmod(self.correct_result_n, self.correct_result_d)
            ax_title3.set_title(
                self.format_user_input_title("", final_w_display, final_n_display, self.correct_result_d),
                fontsize=18)

            self.canvas.draw()  # Redraw the result plot specifically
        else:
            # Check if just the common denominator step is done, but not the sum or simplification
            # This is to provide more granular feedback.
            lcm_original = (self.task_d1 * self.task_d2) // math.gcd(self.task_d1, self.task_d2)

            # Calculate the improper form of original fractions with LCM
            current_n1_lcm = (self.whole1_var.get() * self.den1_var.get() + self.num1_var.get())
            current_n2_lcm = (self.whole2_var.get() * self.den2_var.get() + self.num2_var.get())

            if d1_user == d2_user and d1_user == lcm_original:
                # User has correct common denominator. Now check the sum.
                # The correct sum in improper form with the common_d
                correct_sum_n_at_lcm = (self.task_n1 * (lcm_original // self.task_d1)) + \
                                       (self.task_n2 * (lcm_original // self.task_d2))

                # User's sum at common denominator
                user_sum_n_at_lcm = current_n1_lcm + current_n2_lcm

                if user_sum_n_at_lcm != correct_sum_n_at_lcm:
                    self.result_status_var.set("Неправильна сума чисельників!")
                    self.result_status_label.config(style="Error.TLabel")
                elif user_total_n_improper >= common_d:  # After summing, if it's an improper fraction
                    self.result_status_var.set("Виділіть цілу частину та/або скоротіть дріб!")
                    self.result_status_label.config(style="Error.TLabel")
                else:
                    self.result_status_var.set("Рішення невірне. Перевірте обчислення або скорочення!")
                    self.result_status_label.config(style="Error.TLabel")
            else:
                self.result_status_var.set("Рішення невірне. Перевірте обчислення!")
                self.result_status_label.config(style="Error.TLabel")


    def format_user_input_title(self, base_title, w, n, d):
        if d == 0: return base_title  # Avoid division by zero in title rendering

        whole_str = f"${w}$" if w > 0 else ""
        # Only show fractional part if n > 0, or if w is 0 and n is 0 (to represent 0/d)
        frac_str = f"$\\frac{{{n}}}{{{d}}}$" if n > 0 or (w == 0 and n == 0 and d != 0) else ""

        # Special case: if both whole and numerator are 0, just show 0
        if w == 0 and n == 0 and d != 0:
            return f"{base_title}\n$0$"
        # If w is 0 but n > 0, show only the fraction
        elif w == 0 and n > 0 and d != 0:
            return f"{base_title}\n$\\frac{{{n}}}{{{d}}}$"
        # If w > 0 and n is 0, show only the whole number
        elif w > 0 and n == 0 and d != 0:
            return f"{base_title}\n${w}$"

        return f"{base_title}\n{whole_str}{frac_str}"

    def _draw_overlapping_circles(self, ax, n, d, color):
        ax.axis('off');
        ax.set_aspect('equal', adjustable='box')
        if d == 0: return
        whole, frac_n = divmod(n, d)
        total_circles = whole + (1 if frac_n > 0 else 0)
        if total_circles == 0 and n == 0: self.draw_fraction_pie(ax, [0], [color], d, center=(0, 0)); return

        radius = 1.0;
        overlap = 0.65;
        step = 2 * radius * overlap
        actual_width = (total_circles - 1) * step + 2 * radius if total_circles > 0 else 0
        max_width = (self.MAX_CIRCLES - 1) * step + 2 * radius

        start_x = -actual_width / 2 + radius
        for i in range(whole):
            self.draw_fraction_pie(ax, [d], [color], d, center=(start_x + i * step, 0), radius=radius)
        if frac_n > 0:
            self.draw_fraction_pie(ax, [frac_n], [color], d, center=(start_x + whole * step, 0), radius=radius)

        if d > 0:
            val = round(n / d, 3)
            ax.text(0, -radius - 1.0, f"≈ {val}", ha='center', va='top', fontsize=16, color='gray')

        ax.set_xlim(-max_width / 2 - 0.2, max_width / 2 + 0.2);
        ax.set_ylim(-radius - 1.4, radius + 0.2)

    def _build_solution_for_task(self):
        n1, d1, n2, d2 = self.task_n1, self.task_d1, self.task_n2, self.task_d2
        self.solution_steps = []
        w1, f_n1 = divmod(n1, d1);
        w2, f_n2 = divmod(n2, d2)

        self.solution_steps.append(("bold", "--- КРОК 1: ЗВЕДЕННЯ ДО СПІЛЬНОГО ЗНАМЕННИКА ---"))
        lcm = (d1 * d2) // math.gcd(d1, d2)
        new_f_n1, new_f_n2 = f_n1 * (lcm // d1), f_n2 * (lcm // d2)
        self.solution_steps.append(("normal",
                                    f"НСК для {d1} і {d2} є {lcm}.\n{w1} {f_n1}/{d1} + {w2} {f_n2}/{d2} -> {w1} {new_f_n1}/{lcm} + {w2} {new_f_n2}/{lcm}"))

        final_w_initial, final_f_n_initial = w1 + w2, new_f_n1 + new_f_n2
        self.solution_steps.append(("bold", "--- КРОК 2: ДОДАВАННЯ ---"))
        self.solution_steps.append(("normal",
                                    f"1. Цілі частини: {w1} + {w2} = {final_w_initial}\n2. Дробові частини: ({new_f_n1}/{lcm}) + ({new_f_n2}/{lcm}) = ({final_f_n_initial}/{lcm})"))

        # Check if the fractional part is an improper fraction
        if final_f_n_initial >= lcm:
            self.solution_steps.append(("bold", "--- КРОК 3: ПЕРЕТВОРЕННЯ НЕПРАВИЛЬНОГО ДРОБУ ---"))
            carried_w = final_f_n_initial // lcm
            remaining_f_n = final_f_n_initial % lcm
            self.solution_steps.append(("normal",
                                        f"Дробова частина {final_f_n_initial}/{lcm} є неправильним дробом.\nВиділяємо цілу частину: {final_f_n_initial} / {lcm} = {carried_w} (цілих) і {remaining_f_n} (залишок)."))
            final_w_initial += carried_w
            final_f_n_initial = remaining_f_n
            self.solution_steps.append(("normal",
                                        f"Додаємо цілі частини: {final_w_initial - carried_w} + {carried_w} = {final_w_initial}.\nОтримуємо: {final_w_initial} {final_f_n_initial}/{lcm}"))

        final_n = final_w_initial * lcm + final_f_n_initial
        final_d = lcm
        common_divisor = math.gcd(final_n, final_d)
        if common_divisor > 1 and final_n != 0:
            self.solution_steps.append(("bold", "--- КРОК 4: СКОРОЧЕННЯ ---"))
            reduced_n, reduced_d = final_n // common_divisor, final_d // common_divisor
            self.solution_steps.append(("normal",
                                        f"Перетворимо результат {final_w_initial} {final_f_n_initial}/{lcm} на неправильний дріб {final_n}/{lcm} і скоротимо його:\n({final_n}/{lcm}) -> ({reduced_n}/{reduced_d})"))
            final_n, final_d = reduced_n, reduced_d

        if final_n >= final_d and final_d != 0:
            rw, rn = divmod(final_n, final_d)
            self.solution_steps.append(("bold", f"Кінцева відповідь: {rw} {rn}/{final_d}" if rn > 0 else str(rw)))
        else:
            self.solution_steps.append(("bold", f"Кінцева відповідь: {final_n}/{final_d}"))

    def draw_fraction_pie(self, ax, numerators, colors, denominator, center=(0, 0), radius=1.0):
        sizes, final_colors = [], []
        total_num = sum(numerators)
        if total_num > 0:
            sizes.extend([n for n in numerators if n > 0]);
            final_colors.extend(colors[:len(sizes)])
        if denominator - total_num > 0:
            sizes.append(denominator - total_num);
            final_colors.append(self.empty_color)
        if not sizes: sizes, final_colors = [1], [self.empty_color]
        ax.pie(sizes, radius=radius * 2.2, center=center, colors=final_colors, startangle=90, counterclock=False,
               wedgeprops={'edgecolor': 'black', 'linewidth': 0.8})

    def draw_placeholder(self, ax, text):
        ax.axis('off')
        ax.text(0.5, 0.5, text, ha='center', va='center', fontsize=20, color='grey', transform=ax.transAxes, wrap=True)

    def _open_solution_window(self):
        self._build_solution_for_task()
        SolutionWindow(self, self.solution_steps)

if __name__ == "__main__":
    app = FractionVisualizerApp()
    app.mainloop()