import sys
from PySide2.QtWidgets import QApplication
from logic.controller import Controller


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = Controller()
    sys.exit(app.exec_())
