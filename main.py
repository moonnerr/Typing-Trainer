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

        self.initUI()

    def load_text(self, level):
        self.timer.stop() # останавливаем таймер
        self.start_time = None # новая тренировка ещё не началась
        self.elapsed_time = 0 # обнуляет прошедшее время
        self.time_label.setText("Время: 00:00") # обновляет надпись времени на экране
        self.accuracy_label.setText("Точность: 100,0%") # обновляет надпись точности на экране


        connection = sqlite3.connect("typing_trainer.db")
        cursor = connection.cursor()

        cursor.execute("SELECT content FROM texts WHERE level = ? ORDER BY RANDOM() LIMIT 1",(level,))

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

    # смена цвета символа
    def update_text(self):
        html = ""

        for i, symbol in enumerate(self.result): # перебор текста с получением символа и номера
            if i < self.current_index: # проверка правильности ввода
                color = "green"

            elif i == self.current_index: # если символ - текущий, то он белый
                color = "white"

                if self.last_input_correct == False:
                    frame_color = "red"
                else:
                    frame_color = "green"

            else:
                color = "black"

            # Добавляем символ с нужным цветом
            if i == self.current_index: # проверяем, что символ текущий
                html += f'<span style="color: {color}; background-color: {frame_color}; padding: 4px; border-radius: 5px;">{symbol}</span>' # задаём каждому символу своё оформление
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

    def initUI(self):
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


        # ==================================================
        # ЛЕВАЯ ПАНЕЛЬ — НАВИГАЦИЯ И СЛОЖНОСТЬ
        # ==================================================

        # Название приложения
        title_label = QLabel("TypingTrainer")
        sidebar.layout().addWidget(title_label)

        # Кнопки навигации
        button_training = QPushButton("Тренировка")
        sidebar.layout().addWidget(button_training)

        button_stats = QPushButton("Статистика")
        sidebar.layout().addWidget(button_stats)

        button_settings = QPushButton("Настройки")
        sidebar.layout().addWidget(button_settings)

        button_about = QPushButton("О программе")
        sidebar.layout().addWidget(button_about)

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

        # Здесь будут:
        # Результаты текущей тренировки
        # График прогресса
        # Дополнительная статистика

        self.load_text("light")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.showMaximized()
    sys.exit(app.exec())
