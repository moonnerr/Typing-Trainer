import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QHBoxLayout, QLabel, QTextBrowser, QMainWindow, QLineEdit
)
import sqlite3


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def load_text(self, level):
        connection = sqlite3.connect("typing_trainer.db")
        cursor = connection.cursor()

        cursor.execute("SELECT content FROM texts WHERE level = ? ORDER BY RANDOM() LIMIT 1",(level,))

        result = cursor.fetchone()

        self.result = result[0]
        self.text_label.setText(self.result)

        connection.close()

    def initUI(self):
        self.setWindowTitle("TypingTrainer")

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
        main_layout.addWidget(sidebar, 1)
        main_layout.addWidget(training_panel, 3)
        main_layout.addWidget(stats_panel, 1)

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

        self.text_label = QLabel()
        training_panel.layout().addWidget(self.text_label)

        # Здесь будут:
        # Таймер
        # Скорость печати
        # Текст для набора
        # Поле ввода

        # ==================================================
        # ПРАВАЯ ПАНЕЛЬ — СТАТИСТИКА
        # ==================================================

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
