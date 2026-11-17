import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QHBoxLayout, QLabel, QTextBrowser, QMainWindow
)
import sqlite3
from PyQt6.QtCore import Qt, QTimer
import time
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

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

    def load_text(self, level):
        self.level = level  # запоминаем текущую сложность
        self.timer.stop() # останавливаем таймер
        self.start_time = None # новая тренировка ещё не началась
        self.elapsed_time = 0 # обнуляет прошедшее время
        self.time_label.setText("Время: 00:00") # обновляет надпись времени на экране
        self.accuracy_label.setText("Точность: 100,0%") # обновляет надпись точности на экране


        connection = sqlite3.connect("typing_trainer.db")
        cursor = connection.cursor()

        cursor.execute("SELECT MAX(training_number) FROM results")
        last_number = cursor.fetchone()[0]

        if last_number is None:
            training_number = 1
        else:
            training_number = last_number + 1

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

    # проверка правильности ввода
    def keyPressEvent(self, event):
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

        if pressed_symbol == current_symbol:
            self.current_index += 1
            self.last_input_correct = True
        else:
            self.last_input_correct = False
            self.errors += 1

        self.accuracy = self.current_index / (self.current_index + self.errors) * 100
        self.accuracy_label.setText(f"Точность: {self.accuracy:.1f}%")

        self.update_text()

        if self.current_index == len(self.result):
            self.finish_training()

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

        self.text_label.setHtml(html)

    # счётчик времени
    def update_timer(self): # обновляем таймер
        self.elapsed_time = int(time.monotonic() - self.start_time) # считаем, сколько ЦЕЛЫХ секунд прошло с начала тренировки

        elapsed_seconds = time.monotonic() - self.start_time # считаем, сколько секунд прошло с начала тренировки (не обязательно целых)

        if elapsed_seconds > 0: # если количество напечатанных символов больше 0
            self.cpm = self.current_index / elapsed_seconds * 60 # считаем скорость печати в символах в минуту
        else: # если количество напечатанных символов = 0
            self.cpm = 0 # тогда скорость печати = 0

        minutes = self.elapsed_time // 60 # сколько минут прошло
        seconds = self.elapsed_time % 60 # сколько секунд осталось после выделения минут

        self.time_label.setText(f"Время: {minutes:02d}:{seconds:02d}") # меняем отображаемые данные по времени
        self.speed_label.setText(f"Скорость: {self.cpm:.0f} симв./мин") # меняем отображаемые данные по скорости печати

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
        self.ax.set_ylabel("Скорость (симв./мин)", color=theme["secondary_text"])

        self.ax.tick_params(colors=theme["secondary_text"])
        self.ax.grid(color=theme["panel_border"], linestyle="--", alpha=0.8)

        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_color(theme["panel_border"])
        self.ax.spines["bottom"].set_color(theme["panel_border"])

        self.figure.tight_layout()
        self.canvas.draw()

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

        cursor.execute(
            "UPDATE settings SET theme = ? WHERE id = 1",
            (self.settings["theme"],)
        )

        connection.commit()
        connection.close()

        # Обновляем график
        self.update_graph()
        # обновляем текст
        self.update_text()

    # сохранение результатов тренировки в базу данных
    def finish_training(self):
        self.timer.stop() # останавливаем таймер
        elapsed_seconds = time.monotonic() - self.start_time # вычисляем, сколько секунд длилась тренировка
        self.elapsed_time = int(elapsed_seconds) # сохраняем время тренировки в целых секундах

        # рассчитываем итоговую скорость печати
        if elapsed_seconds > 0:
            self.cpm = self.current_index / elapsed_seconds * 60
        else:
            self.cpm = 0
        minutes = self.elapsed_time // 60 # сколько минут прошло

        seconds = self.elapsed_time % 60 # сколько секунд осталось после выделения минут

        self.time_label.setText(f"Время: {minutes:02d}:{seconds:02d}") # меняем отображаемые данные по времени
        self.speed_label.setText(f"Скорость: {self.cpm:.0f} симв./мин") # меняем отображаемые данные по скорости печати

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

        # Название приложения
        title_label = QLabel("TypingTrainer")
        sidebar.layout().addWidget(title_label)

        # кнопка смены темы
        self.button_theme = QPushButton()
        sidebar.layout().addWidget(self.button_theme)

        if self.settings["theme"] == "dark":
            self.button_theme.setText("Светлая тема")
        else:
            self.button_theme.setText("Тёмная тема")

        self.button_theme.clicked.connect(self.toggle_theme)

        # Выбор сложности
        difficulty_label = QLabel("Сложность")
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
        self.text_label = QTextBrowser()
        self.text_label.setReadOnly(True)
        self.text_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        training_panel.layout().addWidget(self.text_label)

        # Скорость печати
        self.speed_label = QLabel("Скорость: 0 симв./мин")
        stats_panel.layout().addWidget(self.speed_label)

        # ==================================================
        # ПРАВАЯ ПАНЕЛЬ — СТАТИСТИКА
        # ==================================================

        self.accuracy_label = QLabel("Точность: 100,0%")
        stats_panel.layout().addWidget(self.accuracy_label)

        self.time_label = QLabel("Время: 00:00")
        stats_panel.layout().addWidget(self.time_label)

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
