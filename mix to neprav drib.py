import tkinter as tk
from tkinter import ttk, font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import math
import random


class SolutionWindow(tk.Toplevel):
    """Окреме, повністю функціональне вікно для показу рішення"""

    def __init__(self, parent, solution_steps, task_type):
        super().__init__(parent)
        self.title("Рішення завдання")
        self.geometry("800x600")

        self.font_explanation = font.Font(family="Helvetica", size=16)
        self.font_title = font.Font(family="Helvetica", size=18, weight="bold")
        self.font_frac = font.Font(family="Helvetica", size=20, weight="bold")
        self.font_mixed = font.Font(family="Helvetica", size=24, weight="bold")

        self.task_type = task_type  # Зберігаємо тип завдання для коректного відображення

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

                    # Логіка відображення в залежності від типу завдання та сторони "->"
                    if self.task_type == "mixed_to_improper":
                        # Зліва мішане, справа неправильне
                        if ' ' in left and '/' in left:
                            whole_str, fraction_str = left.split(' ', 1)
                            self.draw_mixed_number(frac_frame, whole_str, fraction_str)
                        else:
                            self.draw_single_fraction(frac_frame, left)  # На випадок проміжного кроку з дробом

                        ttk.Label(frac_frame, text="  ->  ", font=self.font_frac).pack(side=tk.LEFT, padx=10)
                        self.draw_single_fraction(frac_frame, right)  # Результат завжди неправильний дріб

                    elif self.task_type == "improper_to_mixed":
                        # Зліва неправильне, справа мішане
                        self.draw_single_fraction(frac_frame, left)  # Завжди неправильний дріб зліва

                        ttk.Label(frac_frame, text="  ->  ", font=self.font_frac).pack(side=tk.LEFT, padx=10)
                        if ' ' in right and '/' in right:
                            whole_str, fraction_str = right.split(' ', 1)
                            self.draw_mixed_number(frac_frame, whole_str, fraction_str)
                        else:
                            self.draw_single_fraction(frac_frame, right)  # На випадок проміжного кроку з дробом


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

    def draw_mixed_number(self, parent, whole_str, frac_str):
        try:
            n_str, d_str = map(str.strip, frac_str.replace('(', '').replace(')', '').split('/'))
        except ValueError:
            ttk.Label(parent, text=f"{whole_str} {frac_str}", font=self.font_mixed).pack(side=tk.LEFT)
            return

        whole_w = self.font_mixed.measure(whole_str)
        n_w, d_w = self.font_frac.measure(n_str), self.font_frac.measure(d_str)
        frac_max_w = max(n_w, d_w) + 10

        canvas = tk.Canvas(parent, height=60, width=whole_w + frac_max_w + 5, bg=self.cget('bg'), highlightthickness=0)
        canvas.pack(side=tk.LEFT)

        canvas.create_text(whole_w / 2, 30, text=whole_str, font=self.font_mixed, anchor="center")

        # Малюємо дробову частину
        frac_x_offset = whole_w + 5
        canvas.create_text(frac_x_offset + frac_max_w / 2, 15, text=n_str, font=self.font_frac, anchor="center")
        canvas.create_line(frac_x_offset, 30, frac_x_offset + frac_max_w, 30, width=3)
        canvas.create_text(frac_x_offset + frac_max_w / 2, 45, text=d_str, font=self.font_frac, anchor="center")


class FractionConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Тренажер: Перетворення дробів")
        try:
            self.state('zoomed')
        except tk.TclError:
            self.attributes('-zoomed', True)

        self.MAX_DENOMINATOR = 10  # Обмежуємо для візуалізації
        self.MAX_WHOLE_PART = 5  # Максимальна ціла частина для візуалізації
        self.MAX_IMPROPER_NUMERATOR = self.MAX_DENOMINATOR * self.MAX_WHOLE_PART + self.MAX_DENOMINATOR - 1

        self.color_filled = 'mediumseagreen'
        self.color_empty = '#E0E0E0'

        # Змінні для завдання
        self.task_type = None  # "mixed_to_improper" або "improper_to_mixed"
        self.mixed_whole, self.mixed_num, self.mixed_den = 0, 0, 1  # Мішане число для завдання
        self.improper_num, self.improper_den = 0, 1  # Неправильний дріб для завдання

        # Змінні для відповіді користувача
        self.user_whole_var = tk.IntVar(value=0)
        self.user_num_var = tk.IntVar(value=0)
        self.user_den_var = tk.IntVar(value=1)

        self.success_var = tk.StringVar()

        # Шрифти
        self.font_body = font.Font(family="Helvetica", size=16)
        self.font_title = font.Font(family="Helvetica", size=18, weight="bold")
        self.font_slider_value = font.Font(family="Helvetica", size=17, weight="bold")
        self.font_success = font.Font(family="Helvetica", size=18, weight="bold")
        self.font_task_display = font.Font(family="Helvetica", size=30, weight="bold")

        # Стилі
        self.style = ttk.Style(self)
        self.style.configure("TLabel", font=self.font_body)
        self.style.configure("TButton", font=self.font_body, padding=10)
        self.style.configure("TScale", length=300)
        self.style.configure("Title.TLabel", font=self.font_title)
        self.style.configure("Success.TLabel", font=self.font_success, foreground="green")

        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Ліва панель (контроли)
        controls_main_frame = ttk.Frame(main_pane, padding=20)
        main_pane.add(controls_main_frame, weight=2)

        # Рамка завдання
        task_label_frame = ttk.LabelFrame(controls_main_frame, text="Завдання", padding=10)
        task_label_frame.pack(fill="x", pady=(0, 20))
        self.task_canvas = tk.Canvas(task_label_frame, height=80, bg='white')
        self.task_canvas.pack(fill=tk.X, expand=True)

        # Рамка для кнопок та повідомлення про успіх
        toolbar_frame = ttk.Frame(controls_main_frame)
        toolbar_frame.pack(fill="x", pady=20)
        self.success_label = ttk.Label(toolbar_frame, textvariable=self.success_var, style="Success.TLabel")
        self.success_label.pack(side=tk.LEFT, expand=True)
        ttk.Button(toolbar_frame, text="Нове завдання", command=self._generate_new_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="Показати рішення", command=self._open_solution_window).pack(side=tk.LEFT,
                                                                                                    padx=5)

        # Елементи управління для введення відповіді
        self.user_whole_controls = self._create_slider_unit(controls_main_frame, "Ціла частина:", self.user_whole_var)
        self.user_whole_controls['frame'].pack(fill="x", pady=5)
        self.user_num_controls = self._create_slider_unit(controls_main_frame, "Чисельник:", self.user_num_var)
        self.user_num_controls['frame'].pack(fill="x", pady=5)
        self.user_den_controls = self._create_slider_unit(controls_main_frame, "Знаменник:", self.user_den_var)
        self.user_den_controls['frame'].pack(fill="x", pady=5)

        # Права панель (візуалізація)
        plot_frame = ttk.Frame(main_pane)
        main_pane.add(plot_frame, weight=5)

        self.figure = plt.figure(figsize=(12, 6), dpi=90)
        self.canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._generate_new_task()  # Генеруємо перше завдання
        self._on_slider_change()  # Оновлюємо відображення

    def _create_slider_unit(self, parent, label_text, var):
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text=label_text).grid(row=0, column=0, columnspan=4, sticky="w")
        btn_minus = ttk.Button(frame, text="-", command=lambda v=var: self._adjust_value(v, -1))
        btn_minus.grid(row=1, column=0, padx=(0, 5))
        scale = ttk.Scale(frame, from_=0, to=self.MAX_IMPROPER_NUMERATOR, variable=var,  # Max для чисельника
                          command=lambda val, v=var: self._on_slider_change(val, v), orient="horizontal")
        scale.grid(row=1, column=1, sticky="ew")
        btn_plus = ttk.Button(frame, text="+", command=lambda v=var: self._adjust_value(v, 1))
        btn_plus.grid(row=1, column=2, padx=5)
        ttk.Label(frame, textvariable=var, font=self.font_slider_value, width=4).grid(row=1, column=3, padx=(10, 0))
        return {'frame': frame, 'scale': scale, 'plus': btn_plus, 'minus': btn_minus}

    def _adjust_value(self, var, delta):
        var.set(var.get() + delta)
        self._on_slider_change()

    def _on_slider_change(self, value=None, var=None):
        if var is not None and value is not None: var.set(int(float(value)))

        # Обмеження для значень
        if self.user_den_var.get() < 1: self.user_den_var.set(1)
        if self.user_whole_var.get() < 0: self.user_whole_var.set(0)
        if self.user_num_var.get() < 0: self.user_num_var.set(0)

        # Чисельник дробової частини не може бути більшим або рівним знаменнику
        if self.task_type == "improper_to_mixed":  # Тільки якщо вводимо мішане число
            if self.user_num_var.get() >= self.user_den_var.get() and self.user_den_var.get() > 0:
                self.user_num_var.set(self.user_den_var.get() - 1 if self.user_den_var.get() > 1 else 0)

        # Оновлення діапазонів слайдерів
        # Ціла частина може бути великою, якщо неправильний дріб має великий чисельник
        self.user_whole_controls['scale'].config(to=self.MAX_WHOLE_PART + self.MAX_IMPROPER_NUMERATOR // (
            self.user_den_var.get() if self.user_den_var.get() > 0 else 1))
        self.user_den_controls['scale'].config(to=self.MAX_DENOMINATOR)

        if self.task_type == "improper_to_mixed":
            self.user_num_controls['scale'].config(to=self.user_den_var.get() - 1 if self.user_den_var.get() > 1 else 0)
        else:  # mixed_to_improper
            self.user_num_controls['scale'].config(to=self.MAX_IMPROPER_NUMERATOR)

        self._check_answer()
        self._visualize_fractions()

    def _update_task_display(self):
        self.task_canvas.delete("all")
        self.task_canvas.bind("<Configure>", self._draw_task_content, add="+")
        self.update_idletasks()  # Оновлюємо вікно, щоб отримати коректні розміри canvas
        self._draw_task_content()

    def _draw_task_content(self, event=None):
        self.task_canvas.delete("all")
        canvas_w, canvas_h = self.task_canvas.winfo_width(), self.task_canvas.winfo_height()
        if canvas_w < 50: return

        prefix_text = "Завдання: "
        prefix_len = font.Font(font=self.font_body).measure(prefix_text)
        self.task_canvas.create_text(10, canvas_h / 2, text=prefix_text, font=self.font_body, anchor="w", fill="navy")
        x_pos = prefix_len + 15

        if self.task_type == "mixed_to_improper":
            whole_str = str(self.mixed_whole)
            whole_w = self.font_task_display.measure(whole_str)
            self.task_canvas.create_text(x_pos + whole_w / 2, canvas_h / 2, text=whole_str, font=self.font_task_display,
                                         anchor="center")

            frac_x_offset = x_pos + whole_w + 5
            num_str, den_str = str(self.mixed_num), str(self.mixed_den)
            num_w, den_w = self.font_task_display.measure(num_str), self.font_task_display.measure(den_str)
            max_frac_w = max(num_w, den_w) + 10

            self.task_canvas.create_text(frac_x_offset + max_frac_w / 2, canvas_h / 2 - 20, text=num_str,
                                         font=self.font_task_display, anchor="center")
            self.task_canvas.create_line(frac_x_offset, canvas_h / 2, frac_x_offset + max_frac_w, canvas_h / 2, width=3)
            self.task_canvas.create_text(frac_x_offset + max_frac_w / 2, canvas_h / 2 + 20, text=den_str,
                                         font=self.font_task_display, anchor="center")

        elif self.task_type == "improper_to_mixed":
            num_str, den_str = str(self.improper_num), str(self.improper_den)
            num_w, den_w = self.font_task_display.measure(num_str), self.font_task_display.measure(den_str)
            max_w = max(num_w, den_w) + 10

            self.task_canvas.create_text(x_pos + max_w / 2, canvas_h / 2 - 20, text=num_str,
                                         font=self.font_task_display, anchor="center")
            self.task_canvas.create_line(x_pos, canvas_h / 2, x_pos + max_w, canvas_h / 2, width=3)
            self.task_canvas.create_text(x_pos + max_w / 2, canvas_h / 2 + 20, text=den_str,
                                         font=self.font_task_display, anchor="center")

    def _open_solution_window(self):
        self._build_solution_for_task()
        SolutionWindow(self, self.solution_steps, self.task_type)

    def _set_controls_state(self, state):
        for controls in [self.user_whole_controls, self.user_num_controls, self.user_den_controls]:
            controls['scale'].config(state=state)
            controls['plus'].config(state=state)
            controls['minus'].config(state=state)

    def _generate_new_task(self):
        self._set_controls_state(tk.NORMAL)
        self.success_var.set("")

        self.task_type = random.choice(["mixed_to_improper", "improper_to_mixed"])

        # Генеруємо базові значення
        den = random.randint(2, self.MAX_DENOMINATOR)
        num_frac = random.randint(1, den - 1)  # Чисельник дробової частини мішаного числа
        whole_part = random.randint(1, self.MAX_WHOLE_PART)

        if self.task_type == "mixed_to_improper":
            self.mixed_whole = whole_part
            self.mixed_num = num_frac
            self.mixed_den = den

            # Правильна відповідь
            self.improper_num = self.mixed_whole * self.mixed_den + self.mixed_num
            self.improper_den = self.mixed_den

            # Скидаємо поля вводу до нуля або завдання
            self.user_whole_var.set(0)  # Користувач вводить неправильний дріб, ціла частина не потрібна
            self.user_num_var.set(0)
            self.user_den_var.set(1)

            # Активуємо/деактивуємо елементи управління
            self._set_control_visibility(whole_part=False, improper_fraction_input=True)

        else:  # improper_to_mixed
            # Генеруємо неправильний дріб
            self.improper_den = den
            self.improper_num = random.randint(self.improper_den + 1,
                                               self.MAX_IMPROPER_NUMERATOR)  # Чисельник має бути більшим за знаменник

            # Правильна відповідь
            self.mixed_whole = self.improper_num // self.improper_den
            self.mixed_num = self.improper_num % self.improper_den
            # Якщо чисельник виявився 0 (ідеально ділиться), то спробуємо ще раз
            if self.mixed_num == 0:
                self._generate_new_task()
                return
            self.mixed_den = self.improper_den

            # Скидаємо поля вводу до нуля або завдання
            self.user_whole_var.set(0)
            self.user_num_var.set(0)
            self.user_den_var.set(1)

            # Активуємо/деактивуємо елементи управління
            self._set_control_visibility(whole_part=True, improper_fraction_input=False)

        self._update_task_display()
        self._on_slider_change()  # Оновлюємо візуалізацію та перевірку

    def _set_control_visibility(self, whole_part, improper_fraction_input):
        # whole_part = True означає, що користувач вводить цілу частину (для мішаного числа)
        # improper_fraction_input = True означає, що користувач вводить чисельник і знаменник для неправильного дробу

        # Ціла частина
        state_whole_ctrl = tk.NORMAL if whole_part else tk.DISABLED
        self.user_whole_controls['scale'].config(state=state_whole_ctrl)
        self.user_whole_controls['plus'].config(state=state_whole_ctrl)
        self.user_whole_controls['minus'].config(state=state_whole_ctrl)

        # Чисельник та знаменник
        state_frac_ctrl = tk.NORMAL
        self.user_num_controls['scale'].config(state=state_frac_ctrl)
        self.user_num_controls['plus'].config(state=state_frac_ctrl)
        self.user_num_controls['minus'].config(state=state_frac_ctrl)
        self.user_den_controls['scale'].config(state=state_frac_ctrl)
        self.user_den_controls['plus'].config(state=state_frac_ctrl)
        self.user_den_controls['minus'].config(state=state_frac_ctrl)

        # Оновити max для слайдерів
        self.user_den_controls['scale'].config(to=self.MAX_DENOMINATOR)

        if whole_part:  # Якщо користувач вводить мішане число
            self.user_num_controls['scale'].config(to=self.user_den_var.get() - 1 if self.user_den_var.get() > 1 else 0)
            self.user_whole_controls['scale'].config(to=self.MAX_WHOLE_PART + self.MAX_IMPROPER_NUMERATOR // (
                self.user_den_var.get() if self.user_den_var.get() > 0 else 1))
        else:  # Якщо користувач вводить неправильний дріб
            self.user_num_controls['scale'].config(to=self.MAX_IMPROPER_NUMERATOR)

    def _check_answer(self):
        user_w = self.user_whole_var.get()
        user_n = self.user_num_var.get()
        user_d = self.user_den_var.get()

        if user_d == 0:  # Уникаємо ділення на нуль
            self.success_var.set("")
            return

        is_correct = False

        if self.task_type == "mixed_to_improper":
            # Користувач має ввести неправильний дріб (тому ціла частина має бути 0)
            if user_w != 0:
                self.success_var.set("")  # Якщо введена ціла частина, це не неправильний дріб
                return

            # Перевіряємо еквівалентність дробів
            gcd_user = math.gcd(user_n, user_d)
            simplified_user_n = user_n // gcd_user
            simplified_user_d = user_d // gcd_user

            gcd_correct = math.gcd(self.improper_num, self.improper_den)
            simplified_correct_n = self.improper_num // gcd_correct
            simplified_correct_d = self.improper_den // gcd_correct

            if (simplified_user_n == simplified_correct_n and
                    simplified_user_d == simplified_correct_d):
                is_correct = True

        else:  # improper_to_mixed
            # Користувач має ввести мішане число
            # Чисельник дробової частини не може бути більшим або рівним знаменнику
            if user_n >= user_d and user_d > 0:
                self.success_var.set("")  # Якщо введений дріб є неправильним, то це не мішане число
                return

            # Перевіряємо, чи збігаються цілі частини та дробові частини (враховуючи скорочення)
            if user_w == self.mixed_whole:
                gcd_user_frac = math.gcd(user_n, user_d)
                gcd_correct_frac = math.gcd(self.mixed_num, self.mixed_den)
                if (user_n // gcd_user_frac == self.mixed_num // gcd_correct_frac and
                        user_d // gcd_user_frac == self.mixed_den // gcd_correct_frac):
                    is_correct = True

        if is_correct:
            self.success_var.set("✔ ПРАВИЛЬНО!")
            self._set_controls_state(tk.DISABLED)
        else:
            self.success_var.set("")

    def _build_solution_for_task(self):
        if self.task_type == "mixed_to_improper":
            w, n, d = self.mixed_whole, self.mixed_num, self.mixed_den
            step1_res = w * d
            final_num = step1_res + n

            self.solution_steps = [
                ("bold", f"--- Перетворення мішаного числа {w} {n}/{d} в неправильний дріб ---"),
                ("bold", "--- КРОК 1: Множимо цілу частину на знаменник ---"),
                ("normal",
                 f"Щоб перетворити мішане число, спочатку помножте цілу частину ({w}) на знаменник ({d})."),
                ("normal",
                 f"{w} × {d} = {step1_res}"),
                ("bold", "--- КРОК 2: Додаємо чисельник до результату ---"),
                ("normal",
                 f"Додайте отриманий результат ({step1_res}) до чисельника ({n}) мішаного числа. Це буде новий чисельник неправильного дробу."),
                ("normal",
                 f"{step1_res} + {n} = {final_num}"),
                ("bold", "--- КРОК 3: Формуємо неправильний дріб ---"),
                ("normal",
                 f"Новий чисельник - {final_num}, а знаменник залишається таким же, як і в початкового мішаного числа ({d})."),
                ("normal",
                 f"{w} {n}/{d} -> {final_num}/{d}"),
                ("bold", "--- РЕЗУЛЬТАТ ---"),
                ("normal", f"Мішане число {w} {n}/{d} перетворюється в неправильний дріб: {final_num}/{d}")
            ]
        else:  # improper_to_mixed
            num_imp, den_imp = self.improper_num, self.improper_den

            # Крок 1: Ділення чисельника на знаменник
            whole_res = num_imp // den_imp
            remainder_res = num_imp % den_imp

            # Крок 2: Формування мішаного числа
            simplified_num, simplified_den = remainder_res, den_imp
            # Якщо є можливість скоротити дробову частину
            if remainder_res != 0:
                gcd_frac = math.gcd(remainder_res, den_imp)
                simplified_num = remainder_res // gcd_frac
                simplified_den = den_imp // gcd_frac

            self.solution_steps = [
                ("bold", f"--- Перетворення неправильного дробу {num_imp}/{den_imp} в мішане число ---"),
                ("bold", "--- КРОК 1: Ділимо чисельник на знаменник ---"),
                ("normal",
                 f"Щоб перетворити неправильний дріб, поділіть чисельник ({num_imp}) на знаменник ({den_imp})."),
                ("normal",
                 f"{num_imp} ÷ {den_imp} = {whole_res} (ціла частина) з залишком {remainder_res} (новий чисельник)."),
                ("bold", "--- КРОК 2: Формуємо мішане число ---"),
                ("normal",
                 f"Ціла частина дробу стає цілою частиною мішаного числа ({whole_res})."),
                ("normal",
                 f"Залишок від ділення ({remainder_res}) стає чисельником дробової частини."),
                ("normal",
                 f"Знаменник залишається без змін ({den_imp})."),
                ("normal",
                 f"({num_imp}/{den_imp}) -> {whole_res} {remainder_res}/{den_imp}"),
                ("normal",
                 f"Скорочуємо дробову частину, якщо можливо: {remainder_res}/{den_imp} -> {simplified_num}/{simplified_den}"),
                ("bold", "--- РЕЗУЛЬТАТ ---"),
                ("normal",
                 f"Неправильний дріб {num_imp}/{den_imp} перетворюється в мішане число: {whole_res} {simplified_num}/{simplified_den}")
            ]

    def _visualize_fractions(self):
        self.figure.clear()

        # Визначення, що візуалізуємо в секції "Завдання"
        task_num_for_pie = 0
        task_den_for_pie = 1
        task_title_text = ""

        if self.task_type == "mixed_to_improper":
            task_num_for_pie = self.mixed_whole * self.mixed_den + self.mixed_num
            task_den_for_pie = self.mixed_den
            task_title_text = f"Завдання: {self.mixed_whole} $\\frac{{{self.mixed_num}}}{{{self.mixed_den}}}$"
        elif self.task_type == "improper_to_mixed":
            task_num_for_pie = self.improper_num
            task_den_for_pie = self.improper_den
            task_title_text = f"Завдання: $\\frac{{{self.improper_num}}}{{{self.improper_den}}}$"

        # Визначення, що візуалізуємо в секції "Ваша відповідь"
        user_num_for_pie = 0
        user_den_for_pie = 1
        user_title_text = ""

        # Перевіряємо, чи знаменник не нуль, перед тим як рахувати
        if self.user_den_var.get() > 0:
            user_num_for_pie = self.user_whole_var.get() * self.user_den_var.get() + self.user_num_var.get()
            user_den_for_pie = self.user_den_var.get()

        # Формуємо заголовок для відповіді користувача в залежності від типу завдання
        if self.task_type == "improper_to_mixed":
            # Відповідь має бути мішаним числом
            user_title_text = f"Ваша відповідь: {self.user_whole_var.get()} $\\frac{{{self.user_num_var.get()}}}{{{self.user_den_var.get()}}}$"
        else:  # mixed_to_improper
            # Відповідь має бути неправильним дробом
            user_title_text = f"Ваша відповідь: $\\frac{{{self.user_num_var.get()}}}{{{self.user_den_var.get()}}}$"

        # Створюємо два subplot'а для порівняння
        ax1 = self.figure.add_subplot(1, 2, 1)
        ax2 = self.figure.add_subplot(1, 2, 2)

        # Малюємо візуалізацію для завдання та відповіді
        self.draw_fraction_pie(ax1, task_num_for_pie, task_den_for_pie, task_title_text, self.color_filled)
        self.draw_fraction_pie(ax2, user_num_for_pie, user_den_for_pie, user_title_text, 'salmon')

        self.figure.tight_layout(pad=3.0)
        self.canvas.draw()

    def draw_fraction_pie(self, ax, numerator, denominator, title, color):
        ax.clear()
        ax.set_title(title, fontsize=20, pad=20)
        ax.set_aspect('equal')
        ax.axis('off')

        if denominator <= 0:
            return

        # Розраховуємо кількість повних кіл та залишок
        whole_part = numerator // denominator
        fractional_numerator = numerator % denominator

        # Визначаємо, скільки всього кіл потрібно намалювати
        pies_to_draw = []
        for _ in range(whole_part):
            pies_to_draw.append(denominator)  # Повне коло

        if fractional_numerator > 0:
            pies_to_draw.append(fractional_numerator)

        # Якщо результат 0, все одно малюємо одне пусте коло
        if not pies_to_draw and numerator == 0:
            pies_to_draw.append(0)

        num_pies = len(pies_to_draw)
        if num_pies == 0: return

        # Розташовуємо кола в один ряд
        pie_radius = 0.9 / (2 * num_pies)  # Радіус залежить від кількості кіл

        for i, num in enumerate(pies_to_draw):
            # Розраховуємо центр кожного кола
            x_center = (2 * i + 1) / (2 * num_pies)
            y_center = 0.5

            # Визначаємо, які частини малювати
            if num > 0:
                sizes = [num, denominator - num] if denominator - num > 0 else [num]
                colors = [color, self.color_empty] if denominator - num > 0 else [color]
            else:  # Для випадку 0/D
                sizes = [1]
                colors = [self.color_empty]

            # Малюємо саме коло (pie chart)
            ax.pie(sizes, colors=colors, startangle=90, counterclock=False,
                   radius=pie_radius, center=(x_center, y_center),
                   wedgeprops={'edgecolor': 'black', 'linewidth': 1})

            # Малюємо розділювачі для наочності
            if denominator <= 20:  # Обмеження, щоб не було занадто багато ліній
                for j in range(denominator):
                    angle = np.deg2rad(90 - j * (360.0 / denominator))
                    x1 = x_center
                    y1 = y_center
                    x2 = x_center + pie_radius * np.cos(angle)
                    y2 = y_center + pie_radius * np.sin(angle)
                    ax.plot([x1, x2], [y1, y2], color='black', lw=0.7, alpha=0.6)

        ax.set_ylim(0, 1)
        ax.set_xlim(0, 1)

if __name__ == "__main__":
    app = FractionConverterApp()
    app.mainloop()