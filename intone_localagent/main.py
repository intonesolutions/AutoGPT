# main.py
from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow
from app.main_window_ui import Ui_MainWindow
app = QApplication([])
window = MainWindow()
win=Ui_MainWindow()
win.setupUi(window)
window.show()
app.exec()
