import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QHBoxLayout, QLabel, QMainWindow, QSlider
)
import sqlite3
from PyQt6.QtCore import Qt, QTimer
import time
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from styles import LIGHT_THEME, DARK_THEME, get_stylesheet


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_index = 0 # номер символа в строке

        self.last_input_correct = None

        # блок для подсчёта времени
        self.start_time = None # время начала тренировки
        self.elapsed_time = 0 # прошедшее время
        self.timer = QTimer() # сам таймер
        self.timer.timeout.connect(self.update_timer)

        self.is_paused = False
        self.pause_started = None
        self.paused_time = 0

        self.settings = self.load_settings()

        self.current_theme = (
            LIGHT_THEME if self.settings["theme"] == "light" else DARK_THEME
        )

        self.text_font_size = self.settings["font_size"]

        self.initUI()

    # сохранение пользовательских настроек
    def load_settings(self):
        connection = sqlite3.connect("typing_trainer.db")
        cursor = connection.cursor()

        cursor.execute("SELECT theme, font_size, interface_language, training_language FROM settings WHERE id = 1")

        result = cursor.fetchone()
        connection.close()

        if result is None:
            return {"theme": "light", "font_size": 20, "interface_language": "ru", "training_language": "ru"}

        return {"theme": result[0], "font_size": result[1], "interface_language": result[2], "training_language": result[3]}


    # загрузка нового текста для тренировки и подготовка программы к его набору
    def load_text(self, level):
        self.level = level  # запоминаем текущую сложность
        self.timer.stop() # останавливаем таймер
        self.start_time = None # новая тренировка ещё не началась
        self.elapsed_time = 0 # обнуляет прошедшее время
        self.time_value.setText("00:00") # обновляет надпись времени на экране
        self.accuracy_value.setText("100,0%") # обновляет надпись точности на экране
        self.speed_value.setText("0") # обновляет надпись времени на экране

        self.is_paused = False
        self.pause_started = None
        self.paused_time = 0
        self.pause_button.setText("Пауза")
        self.pause_button.setEnabled(False)

        self.cpm = 0

        connection = sqlite3.connect("typing_trainer.db")
        cursor = connection.cursor()

        cursor.execute("SELECT MAX(training_number) FROM results")

        cursor.execute("SELECT content FROM texts WHERE level = ? AND language = ? ORDER BY RANDOM() LIMIT 1", (level, self.settings["training_language"])) # выбираем рандомный текст из базы данных по языку и уровню

        result = cursor.fetchone()

        self.accuracy = 100.0  # точность печати на старте
        self.errors = 0 # количество ошибок
        self.result = result[0] # строка, которую нужно напечатать
        self.current_index = 0 # текущий номер символа
        self.last_input_correct = None
        self.update_text()

        connection.close()

        self.setFocus() # переключаем клавиатурный фокус на главное окно

    # смена языка тренировочного текста и сохранение выбранного языка в базе данных
    def change_language(self, language):
        self.settings["training_language"] = language

        connection = sqlite3.connect("typing_trainer.db")
        cursor = connection.cursor()

        cursor.execute("UPDATE settings SET training_language = ? WHERE id = 1", (language,))

        connection.commit()
        connection.close()

        self.load_text(self.level) # передаём сложность текста

    # проверка правильности ввода
    def keyPressEvent(self, event):
        if self.is_paused:
            return

        if self.current_index >= len(self.result):
            return

        current_symbol = self.result[self.current_index]
        pressed_symbol = event.text()

        if not pressed_symbol: # если клавиша не вводит символ, то нажатие не считается ошибочным
            return

        # счёт времени
        if self.start_time is None: # проверяем, запускался ли таймер раньше
            self.start_time = time.monotonic() # получаем текущее время
            self.timer.start(100) # запускаем таймер с интервалом в 100 миллисекунд (0.1 секунду)
            self.pause_button.setEnabled(True)

        if pressed_symbol == current_symbol:
            self.current_index += 1
            self.last_input_correct = True
        else:
            self.last_input_correct = False
            self.errors += 1

        self.accuracy = self.current_index / (self.current_index + self.errors) * 100
        self.accuracy_value.setText(f"{self.accuracy:.1f}%")

        self.update_text()

        if self.current_index == len(self.result):
            self.finish_training()

    # изменение размера тренировочного текста на экране
    def change_font_size(self, size):
        self.text_font_size = size
        self.text_size_label.setText(f"РАЗМЕР ТЕКСТА {size}")
        self.text_label.setStyleSheet(f"font-size: {size}px;")

    # смена цвета символа
    def update_text(self):
        html = ""

        theme = self.current_theme

        for i, symbol in enumerate(self.result):  # перебор текста с получением символа и номера
            if i < self.current_index:  # проверка правильности ввода
                color = "green"

            elif i == self.current_index:  # если символ - текущий, то он белый
                color = theme["text"]

                if self.last_input_correct == False:
                    frame_color = "red"
                else:
                    frame_color = "green"

            else:
                color = theme["text"]

            # Добавляем символ с нужным цветом
            if i == self.current_index:  # проверяем, что символ текущий
                html += f'<span style="color: {color}; background-color: {frame_color}; padding: 4px; border-radius: 5px;">{symbol}</span>'  # задаём каждому символу своё оформление
            else:
                html += f'<span style="color: {color};">{symbol}</span>'
        self.text_label.setText(html)

    # счётчик времени
    def update_timer(self): # обновляем таймер
        self.elapsed_time = int(time.monotonic() - self.start_time - self.paused_time) # считаем, сколько ЦЕЛЫХ секунд прошло с начала тренировки

        elapsed_seconds = time.monotonic() - self.start_time - self.paused_time # считаем, сколько секунд прошло с начала тренировки (не обязательно целых)

        if elapsed_seconds > 0: # если количество напечатанных символов больше 0
            self.cpm = self.current_index / elapsed_seconds * 60 # считаем скорость печати в символах в минуту
        else: # если количество напечатанных символов = 0
            self.cpm = 0 # тогда скорость печати = 0

        minutes = self.elapsed_time // 60 # сколько минут прошло
        seconds = self.elapsed_time % 60 # сколько секунд осталось после выделения минут

        self.time_value.setText(f"Время: {minutes:02d}:{seconds:02d}") # меняем отображаемые данные по времени
        self.speed_value.setText(f"Скорость: {self.cpm:.0f} симв./мин") # меняем отображаемые данные по скорости печати

    # обновление графика прогресса
    def update_graph(self):
        # Подключаемся к базе данных
        connection = sqlite3.connect("typing_trainer.db")
        cursor = connection.cursor()

        # Получаем номер тренировки и скорость печати
        cursor.execute("""SELECT training_number, speed FROM results ORDER BY training_number""")

        results = cursor.fetchall()
        connection.close()

        # Разделяем данные на два списка
        trainings = [row[0] for row in results]
        speeds = [row[1] for row in results]

        # Очищаем график перед обновлением
        self.ax.clear()

        theme = self.current_theme

        # Оформление графика для светлой темы
        self.figure.set_facecolor(theme["panel"])
        self.ax.set_facecolor(theme["panel"])

        self.ax.plot(
            trainings,
            speeds,
            color=theme["accent"], # цвет графика
            linewidth=2.5, # толщина линии
            marker="o", # форма точки
            markersize=5 # толщина точки
        )

        self.ax.set_title("Мой прогресс", color=theme["text"])
        self.ax.set_xlabel("Тренировки", color=theme["secondary_text"])
        self.ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.ax.set_ylabel("Скорость (симв./мин)", color=theme["secondary_text"])

        self.ax.tick_params(colors=theme["secondary_text"])
        self.ax.grid(color=theme["panel_border"], linestyle="--", alpha=0.8)

        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_color(theme["panel_border"])
        self.ax.spines["bottom"].set_color(theme["panel_border"])

        self.figure.tight_layout()
        self.canvas.draw()

    # переключение оформления программы между светлой и тёмной темами
    def toggle_theme(self):
        # Переключаем тему
        if self.settings["theme"] == "light":
            self.settings["theme"] = "dark"
            self.current_theme = DARK_THEME
            self.button_theme.setText("Светлая тема")
        else:
            self.settings["theme"] = "light"
            self.current_theme = LIGHT_THEME
            self.button_theme.setText("Тёмная тема")

        # Применяем новое оформление
        self.setStyleSheet(get_stylesheet(self.current_theme))

        # Сохраняем выбранную тему в базе данных
        connection = sqlite3.connect("typing_trainer.db")
        cursor = connection.cursor()

        cursor.execute("UPDATE settings SET theme = ? WHERE id = 1", (self.settings["theme"],))

        connection.commit()
        connection.close()

        # Обновляем график
        self.update_graph()
        # обновляем текст
        self.update_text()

    # приостановку тренировки и её продолжение
    def toggle_pause(self):
        if not self.is_paused:
            self.is_paused = True
            self.pause_started = time.monotonic()
            self.timer.stop()
            self.pause_button.setText("Продолжить")
        else:
            self.paused_time += time.monotonic() - self.pause_started
            self.pause_started = None
            self.is_paused = False
            self.timer.start(100)
            self.pause_button.setText("Пауза")
            self.setFocus()

    # переход к следующей тренировке
    def next_training(self):
        self.load_text(self.level)

    # сохранение результатов тренировки в базу данных
    def finish_training(self):
        self.timer.stop() # останавливаем таймер
        elapsed_seconds = time.monotonic() - self.start_time - self.paused_time # вычисляем, сколько секунд длилась тренировка
        self.elapsed_time = int(elapsed_seconds) # сохраняем время тренировки в целых секундах

        # рассчитываем итоговую скорость печати
        if elapsed_seconds > 0:
            self.cpm = self.current_index / elapsed_seconds * 60
        else:
            self.cpm = 0
        minutes = self.elapsed_time // 60 # сколько минут прошло

        seconds = self.elapsed_time % 60 # сколько секунд осталось после выделения минут

        self.time_value.setText(f"Время: {minutes:02d}:{seconds:02d}") # меняем отображаемые данные по времени
        self.speed_value.setText(f"Скорость: {self.cpm:.0f} симв./мин") # меняем отображаемые данные по скорости печати

        connection = sqlite3.connect("typing_trainer.db")
        cursor = connection.cursor()

        cursor.execute("SELECT MAX(training_number) FROM results")
        last_number = cursor.fetchone()[0]

        if last_number is None:
            training_number = 1
        else:
            training_number = last_number + 1

        cursor.execute("""INSERT INTO results (speed, accuracy, errors, duration, level, training_number) VALUES (?, ?, ?, ?, ?, ?)""",(self.cpm, self.accuracy, self.errors, self.elapsed_time, self.level, training_number))

        connection.commit()  # подтверждаем и сохраняем изменения в базе данных
        connection.close()  # закрываем соединение с базой данных

        self.update_graph() # обновляем график

        self.next_button.setEnabled(True)
        self.pause_button.setEnabled(False)


    def initUI(self):
        self.setStyleSheet(get_stylesheet(self.current_theme)) # задаём тему

        self.setWindowTitle("TypingTrainer")

        # разрешаем окну получать фокус клавиатуры
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # ==================================================
        # ОБЩАЯ СТРУКТУРА ОКНА
        # ==================================================

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # ==================================================
        # СОЗДАНИЕ ТРЁХ ПАНЕЛЕЙ
        # ==================================================

        # Левая панель
        sidebar = QWidget()
        sidebar.setLayout(QVBoxLayout())

        # Средняя панель
        training_panel = QWidget()
        training_panel.setLayout(QVBoxLayout())

        # Правая панель
        stats_panel = QWidget()
        stats_panel.setLayout(QVBoxLayout())

        # Добавление панелей в главное окно
        main_layout.addWidget(sidebar, 2)
        main_layout.addWidget(training_panel, 6)
        main_layout.addWidget(stats_panel, 2)

        central_widget.setObjectName("mainContainer")
        sidebar.setObjectName("sidebar")
        training_panel.setObjectName("trainingPanel")
        stats_panel.setObjectName("statsPanel")

        # ==================================================
        # ЛЕВАЯ ПАНЕЛЬ — НАВИГАЦИЯ И СЛОЖНОСТЬ
        # ==================================================

        self.pause_button = QPushButton("Пауза")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.toggle_pause)
        stats_panel.layout().addWidget(self.pause_button)

        self.next_button = QPushButton("Следующий текст")
        self.next_button.clicked.connect(self.next_training)
        stats_panel.layout().addWidget(self.next_button)

        # Название приложения
        title_label = QLabel("TypingTrainer")
        title_label.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            color: #A77BFF;
            padding: 15px 0px;
        """)
        sidebar.layout().addWidget(title_label)

        # кнопка смены темы
        self.button_theme = QPushButton()
        sidebar.layout().addWidget(self.button_theme)

        if self.settings["theme"] == "dark":
            self.button_theme.setText("Светлая тема")
        else:
            self.button_theme.setText("Тёмная тема")

        self.button_theme.clicked.connect(self.toggle_theme)

        language_label = QLabel("ЯЗЫК ТЕКСТА")
        language_label.setObjectName("sectionTitle")
        sidebar.layout().addWidget(language_label)

        button_ru = QPushButton("Русский")
        button_en = QPushButton("English")

        sidebar.layout().addWidget(button_ru)
        sidebar.layout().addWidget(button_en)

        button_ru.clicked.connect(lambda: self.change_language("ru"))
        button_en.clicked.connect(lambda: self.change_language("en"))

        # Выбор сложности
        difficulty_label = QLabel("СЛОЖНОСТЬ")
        difficulty_label.setObjectName("sectionTitle")
        sidebar.layout().addWidget(difficulty_label)

        button_light = QPushButton("Лёгкая")
        button_medium = QPushButton("Средняя")
        button_hard = QPushButton("Сложная")

        sidebar.layout().addWidget(button_light)
        sidebar.layout().addWidget(button_medium)
        sidebar.layout().addWidget(button_hard)

        # Подключение кнопок к выбору сложности
        button_light.clicked.connect(lambda: self.load_text("light"))
        button_medium.clicked.connect(lambda: self.load_text("medium"))
        button_hard.clicked.connect(lambda: self.load_text("hard"))

        # ==================================================
        # СРЕДНЯЯ ПАНЕЛЬ — ТРЕНИРОВКА
        # ==================================================

        # Текст для набора
        self.text_label = QLabel()
        self.text_label.setTextFormat(Qt.TextFormat.RichText)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        training_panel.layout().addWidget(self.text_label, 1)

        # ==================================================
        # ПРАВАЯ ПАНЕЛЬ — СТАТИСТИКА
        # ==================================================

        self.text_size_label = QLabel(f"РАЗМЕР ТЕКСТА {self.text_font_size}")
        self.text_size_label.setObjectName("sectionTitle")
        stats_panel.layout().addWidget(self.text_size_label)

        self.font_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_slider.setRange(12, 36)
        self.font_slider.setValue(self.text_font_size)
        stats_panel.layout().addWidget(self.font_slider)

        self.font_slider.valueChanged.connect(self.change_font_size)

        # Скорость печати, точность и время
        self.speed_value = QLabel("0")
        self.accuracy_value = QLabel("100,0%")
        self.time_value = QLabel("00:00")

        self.speed_title = QLabel("СКОРОСТЬ")
        self.accuracy_title = QLabel("ТОЧНОСТЬ")
        self.time_title = QLabel("ВРЕМЯ")

        for title in (self.speed_title, self.accuracy_title, self.time_title):
            title.setObjectName("statTitle")

        for value in (self.speed_value, self.accuracy_value, self.time_value):
            value.setObjectName("statValue")

        for title, value in (
            (self.speed_title, self.speed_value),
            (self.accuracy_title, self.accuracy_value),
            (self.time_title, self.time_value)
        ):
            card = QWidget()
            card.setObjectName("statCard")

            card_layout = QVBoxLayout()
            card_layout.setContentsMargins(14, 10, 14, 10)
            card_layout.setSpacing(4)

            card.setLayout(card_layout)

            card_layout.addWidget(title)
            card_layout.addWidget(value)

            stats_panel.layout().addWidget(card)

        # блок для графика
        self.figure = Figure()
        self.figure.set_facecolor(self.current_theme["panel"])

        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvas(self.figure)
        stats_panel.layout().addWidget(self.canvas)

        self.update_graph()

        self.load_text("light")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.showMaximized()
    sys.exit(app.exec())
