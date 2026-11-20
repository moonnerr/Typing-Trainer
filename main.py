import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QHBoxLayout, QLabel, QMainWindow, QSlider, QMessageBox
)
import sqlite3
from PyQt6.QtCore import Qt, QTimer
import time
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, StrMethodFormatter
from pathlib import Path
from styles import LIGHT_THEME, DARK_THEME, get_stylesheet

BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "typing_trainer.db"

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

        self.pending_result = None

        self.settings = self.load_settings()

        self.current_theme = (LIGHT_THEME if self.settings["theme"] == "light" else DARK_THEME)

        self.text_font_size = self.settings["font_size"]

        self.initUI()

    # сохранение пользовательских настроек
    def load_settings(self):
        connection = None

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()

            cursor.execute("SELECT theme, font_size, interface_language, training_language FROM settings WHERE id = 1") # получение настроек

            result = cursor.fetchone()

            if result is None:
                return {"theme": "light", "font_size": 20, "interface_language": "ru", "training_language": "ru"}

            theme, font_size, interface_language, training_language = result

            if theme not in ("light", "dark"):
                theme = "light"

            if not isinstance(font_size, int) or not 12 <= font_size <= 36:
                font_size = 20

            if interface_language not in ("ru", "en"):
                interface_language = "ru"

            if training_language not in ("ru", "en"):
                training_language = "ru"

            return {
                "theme": theme,
                "font_size": font_size,
                "interface_language": interface_language,
                "training_language": training_language
            }

        except sqlite3.Error as error:
            QMessageBox.critical(
                None,
                "Ошибка базы данных",
                f"Не удалось загрузить настройки.\n\n{error}"
            )
            sys.exit(1)

        finally:
            if connection is not None:
                connection.close()

    # загрузка нового текста для тренировки и подготовка программы к его набору
    def load_text(self, level):
        self.level = level  # запоминаем текущую сложность
        self.timer.stop()  # останавливаем таймер
        self.start_time = None  # новая тренировка ещё не началась
        self.elapsed_time = 0  # обнуляет прошедшее время
        self.time_value.setText("00:00")  # обновляет надпись времени на экране
        self.accuracy_value.setText("100,0%")  # обновляет надпись точности на экране
        self.speed_value.setText("0")  # обновляет надпись времени на экране

        self.is_paused = False
        self.pause_started = None
        self.paused_time = 0
        self.pause_button.setText("Пауза")
        self.pause_button.setEnabled(False)
        self.next_button.setEnabled(False)

        self.cpm = 0
        self.result = ""

        connection = None

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()

            cursor.execute("SELECT content FROM texts WHERE level = ? AND language = ? ORDER BY RANDOM() LIMIT 1",
                           (level, self.settings[
                               "training_language"]))  # выбираем рандомный текст из базы данных по языку и уровню

            result = cursor.fetchone()

        except sqlite3.Error as error:
            self.text_label.setText("Не удалось загрузить текст")
            QMessageBox.critical(
                self,
                "Ошибка базы данных",
                f"Не удалось загрузить текст для тренировки.\n\n{error}"
            )
            return

        finally:
            if connection is not None:
                connection.close()

        if result is None:
            self.text_label.setText("Нет текстов для выбранного языка и сложности")
            QMessageBox.warning(self, "Нет текстов", "Нет текстов для выбранного языка и сложности.")
            return

        self.accuracy = 100.0  # точность печати на старте
        self.errors = 0  # количество ошибок
        self.result = result[0]  # строка, которую нужно напечатать
        self.current_index = 0  # текущий номер символа
        self.last_input_correct = None
        self.update_text()

        self.setFocus()  # переключаем клавиатурный фокус на главное окно

    # смена языка тренировочного текста и сохранение выбранного языка в базе данных
    def change_language(self, language):
        connection = None

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()

            cursor.execute("UPDATE settings SET training_language = ? WHERE id = 1", (language,))

            connection.commit()

            self.settings["training_language"] = language
            self.load_text(self.level)

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Ошибка базы данных",
                f"Не удалось изменить язык тренировочного текста.\n\n{error}"
            )

        finally:
            if connection is not None:
                connection.close()

    def change_interface_language(self, language):
        self.settings["interface_language"] = language

        connection = None

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()

            cursor.execute(
                "UPDATE settings SET interface_language = ? WHERE id = 1",
                (language,)
            )

            connection.commit()

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Database error" if language == "en" else "Ошибка базы данных",
                f"Failed to change interface language.\n\n{error}" if language == "en"
                else f"Не удалось изменить язык интерфейса.\n\n{error}"
            )
            return

        finally:
            if connection is not None:
                connection.close()

        if language == "ru":
            self.pause_button.setText("Пауза")
            self.language_label.setText("ЯЗЫК ТЕКСТА")
            self.difficulty_label.setText("СЛОЖНОСТЬ")
            self.button_light.setText("Лёгкая")
            self.button_medium.setText("Средняя")
            self.button_hard.setText("Сложная")
            self.next_button.setText("Следующий текст")
            self.retry_button.setText("Повторить сохранение")
            self.button_theme.setText("Светлая тема" if self.settings["theme"] == "dark" else "Тёмная тема")
            self.text_size_label.setText(f"РАЗМЕР ТЕКСТА {self.text_font_size}")
            self.speed_title.setText("СКОРОСТЬ")
            self.accuracy_title.setText("ТОЧНОСТЬ")
            self.time_title.setText("ВРЕМЯ")
            self.ax.set_title("Мой прогресс")
            self.ax.set_xlabel("Тренировки")
            self.ax.set_ylabel("Скорость (симв./мин)")

        else:
            self.pause_button.setText("Pause")
            self.language_label.setText("TEXT LANGUAGE")
            self.difficulty_label.setText("DIFFICULTY")
            self.button_light.setText("Easy")
            self.button_medium.setText("Medium")
            self.button_hard.setText("Hard")
            self.next_button.setText("Next text")
            self.retry_button.setText("Retry saving")
            self.button_theme.setText("Light theme" if self.settings["theme"] == "dark" else "Dark theme")
            self.text_size_label.setText(f"TEXT SIZE {self.text_font_size}")
            self.speed_title.setText("SPEED")
            self.accuracy_title.setText("ACCURACY")
            self.time_title.setText("TIME")
            self.ax.set_title("My progress")
            self.ax.set_xlabel("Trainings")
            self.ax.set_ylabel("Speed (chars/min)")

        self.canvas.draw()

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

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute("UPDATE settings SET font_size = ? WHERE id = 1",(size,))

        connection.commit()
        connection.close()

        self.text_size_label.setText(f"РАЗМЕР ТЕКСТА {size}" if self.settings["interface_language"] == "ru" else f"TEXT SIZE {size}")
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

        # меняем отображаемые данные по времени и скорости печати
        if self.settings["interface_language"] == "ru":
            self.time_value.setText(f"Время: {minutes:02d}:{seconds:02d}")
            self.speed_value.setText(f"Скорость: {self.cpm:.0f} симв./мин")
        else:
            self.time_value.setText(f"Time: {minutes:02d}:{seconds:02d}")
            self.speed_value.setText(f"Speed: {self.cpm:.0f} chars/min")

    # обновление графика прогресса
    def update_graph(self):
        connection = None

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()

            # Получаем номер тренировки и скорость печати
            cursor.execute("""SELECT training_number, speed FROM results ORDER BY training_number""")

            results = cursor.fetchall()

        except sqlite3.Error as error:
            self.ax.clear()
            self.ax.set_title("Не удалось загрузить статистику")
            self.canvas.draw()

            QMessageBox.warning(
                self,
                "Ошибка базы данных",
                f"Не удалось загрузить статистику.\n\n{error}"
            )
            return

        finally:
            if connection is not None:
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

        if self.settings["interface_language"] == "ru":
            self.ax.set_title("Мой прогресс", color=theme["text"])
            self.ax.set_xlabel("Тренировки", color=theme["secondary_text"])
            self.ax.set_ylabel("Скорость (симв./мин)", color=theme["secondary_text"])
        else:
            self.ax.set_title("My progress", color=theme["text"])
            self.ax.set_xlabel("Trainings", color=theme["secondary_text"])
            self.ax.set_ylabel("Speed (chars/min)", color=theme["secondary_text"])

        self.ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.ax.yaxis.set_major_locator(MaxNLocator(nbins=5, min_n_ticks=3))
        self.ax.yaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))
        self.ax.set_ylim(bottom=0)

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
        new_theme = "dark" if self.settings["theme"] == "light" else "light"

        connection = None

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()

            cursor.execute("UPDATE settings SET theme = ? WHERE id = 1", (new_theme,))

            connection.commit()

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Ошибка базы данных",
                f"Не удалось сохранить тему оформления.\n\n{error}"
            )
            return

        finally:
            if connection is not None:
                connection.close()

        self.settings["theme"] = new_theme

        if new_theme == "dark":
            self.current_theme = DARK_THEME
            self.button_theme.setText(
                "Светлая тема" if self.settings["interface_language"] == "ru" else "Light theme"
            )
        else:
            self.current_theme = LIGHT_THEME
            self.button_theme.setText(
                "Тёмная тема" if self.settings["interface_language"] == "ru" else "Dark theme"
            )

        self.setStyleSheet(get_stylesheet(self.current_theme))

        self.update_graph()
        self.update_text()

    # приостановка тренировки и её продолжение
    def toggle_pause(self):
        language = self.settings["interface_language"]

        if not self.is_paused:
            self.is_paused = True
            self.pause_started = time.monotonic()
            self.timer.stop()
            self.pause_button.setText("Продолжить" if language == "ru" else "Resume")
        else:
            self.paused_time += time.monotonic() - self.pause_started
            self.pause_started = None
            self.is_paused = False
            self.timer.start(100)
            self.pause_button.setText("Пауза" if language == "ru" else "Pause")
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

        # меняем отображаемые данные по времени и скорости печати
        if self.settings["interface_language"] == "ru":
            self.time_value.setText(f"Время: {minutes:02d}:{seconds:02d}")
            self.speed_value.setText(f"Скорость: {self.cpm:.0f} симв./мин")
        else:
            self.time_value.setText(f"Time: {minutes:02d}:{seconds:02d}")
            self.speed_value.setText(f"Speed: {self.cpm:.0f} chars/min")

        self.pending_result = (
            self.cpm,
            self.accuracy,
            self.errors,
            self.elapsed_time,
            self.level
        )

        self.save_result()

        self.pause_button.setEnabled(False)

        self.pause_button.setText("Пауза" if self.settings["interface_language"] == "ru" else "Pause")

    # сохранение результата тренировки
    def save_result(self):
        connection = None

        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()

            cursor.execute("SELECT MAX(training_number) FROM results")
            last_number = cursor.fetchone()[0]

            if last_number is None:
                training_number = 1
            else:
                training_number = last_number + 1

            cursor.execute(
                """INSERT INTO results (speed, accuracy, errors, duration, level, training_number) VALUES (?, ?, ?, ?, ?, ?)""",
                (*self.pending_result, training_number)
            )

            connection.commit()

            self.pending_result = None
            self.retry_button.setEnabled(False)
            self.next_button.setEnabled(True)
            self.update_graph()

        except sqlite3.Error as error:
            QMessageBox.warning(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить результат тренировки.\n\n{error}\n\nРезультат остался в памяти. Попробуйте сохранить его повторно."
            )

            self.retry_button.setEnabled(True)

        finally:
            if connection is not None:
                connection.close()

    # повторное сохранение результата
    def retry_save_result(self):
        if self.pending_result is not None:
            self.save_result()


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

        interface_buttons_layout = QHBoxLayout()

        self.interface_button_en = QPushButton("EN")
        self.interface_button_ru = QPushButton("RU")

        self.interface_button_en.setFixedSize(65, 40)
        self.interface_button_ru.setFixedSize(65, 40)

        self.interface_button_en.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.interface_button_ru.setStyleSheet("font-size: 16px; font-weight: bold;")

        interface_buttons_layout.addWidget(self.interface_button_en)
        interface_buttons_layout.addWidget(self.interface_button_ru)
        interface_buttons_layout.addStretch()

        sidebar.layout().addLayout(interface_buttons_layout)

        self.interface_button_en.clicked.connect(lambda: self.change_interface_language("en"))
        self.interface_button_ru.clicked.connect(lambda: self.change_interface_language("ru"))

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
        self.button_theme.setFocusPolicy(Qt.FocusPolicy.NoFocus) # запрещаем кнопке получать фокус клавиатуры
        sidebar.layout().addWidget(self.button_theme)

        if self.settings["theme"] == "dark":
            self.button_theme.setText("Светлая тема")
        else:
            self.button_theme.setText("Тёмная тема")

        self.button_theme.clicked.connect(self.toggle_theme)

        self.language_label = QLabel("ЯЗЫК ТЕКСТА")
        self.language_label.setObjectName("sectionTitle")
        sidebar.layout().addWidget(self.language_label)

        button_ru = QPushButton("Русский")
        button_en = QPushButton("English")

        sidebar.layout().addWidget(button_ru)
        sidebar.layout().addWidget(button_en)

        button_ru.clicked.connect(lambda: self.change_language("ru"))
        button_en.clicked.connect(lambda: self.change_language("en"))

        # Выбор сложности
        self.difficulty_label = QLabel("СЛОЖНОСТЬ")
        self.difficulty_label.setObjectName("sectionTitle")
        sidebar.layout().addWidget(self.difficulty_label)

        self.button_light = QPushButton("Лёгкая")
        self.button_medium = QPushButton("Средняя")
        self.button_hard = QPushButton("Сложная")

        sidebar.layout().addWidget(self.button_light)
        sidebar.layout().addWidget(self.button_medium)
        sidebar.layout().addWidget(self.button_hard)

        self.button_light.clicked.connect(lambda: self.load_text("light"))
        self.button_medium.clicked.connect(lambda: self.load_text("medium"))
        self.button_hard.clicked.connect(lambda: self.load_text("hard"))
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
        self.text_label.setStyleSheet(f"font-size: {self.text_font_size}px;")

        # ==================================================
        # ПРАВАЯ ПАНЕЛЬ — СТАТИСТИКА
        # ==================================================

        self.pause_button = QPushButton("Пауза")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.toggle_pause)
        stats_panel.layout().addWidget(self.pause_button)

        self.next_button = QPushButton("Следующий текст")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.next_training)
        stats_panel.layout().addWidget(self.next_button)

        self.retry_button = QPushButton("Повторить сохранение")
        self.retry_button.clicked.connect(self.retry_save_result)
        self.retry_button.setEnabled(False)
        stats_panel.layout().addWidget(self.retry_button)

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

        self.change_interface_language(self.settings["interface_language"])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.showMaximized()
    sys.exit(app.exec())
