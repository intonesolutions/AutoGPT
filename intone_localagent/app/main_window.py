# app/main_window.py
from PySide6.QtWidgets import QMainWindow, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My PySide6 App")
        self.setCentralWidget(QLabel("Hello from PySide6"))
