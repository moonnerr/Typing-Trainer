import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel,
                             QTextBrowser, QMainWindow, QLineEdit)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("TypingTrainer")

        # центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # боковая(левая) панель
        sidebar = QWidget()
        sidebar.setLayout(QVBoxLayout())

        # средняя панель(с текстом)
        training_panel = QWidget()
        training_panel.setLayout(QVBoxLayout())

        # боковая(правая) панель
        stats_panel = QWidget()
        stats_panel.setLayout(QVBoxLayout())

        main_layout.addWidget(sidebar, 1)
        main_layout.addWidget(training_panel, 3)
        main_layout.addWidget(stats_panel, 1)

        # кнопки боковой панели
        button_training = QPushButton("Тренировка")
        sidebar.layout().addWidget(button_training)
        button_stats = QPushButton("Статистика")
        sidebar.layout().addWidget(button_stats)
        button_settings = QPushButton("Настройки")
        sidebar.layout().addWidget(button_settings)
        button_about = QPushButton("О программе")
        sidebar.layout().addWidget(button_about)

        # заголовок выбора сложности
        difficulty_label = QLabel("Сложность")
        sidebar.layout().addWidget(difficulty_label)

        # кнопки сложности
        button_light = QPushButton("Лёгкая")
        button_medium = QPushButton("Средняя")
        button_hard = QPushButton("Сложная")

        sidebar.layout().addWidget(button_light)
        sidebar.layout().addWidget(button_medium)
        sidebar.layout().addWidget(button_hard)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.showMaximized()
    sys.exit(app.exec())
