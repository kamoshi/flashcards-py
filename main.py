import sys
from PySide2.QtWidgets import QApplication
from controller.controller import Controller


if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = Controller()
    sys.exit(app.exec_())