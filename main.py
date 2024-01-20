import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

import windows


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('media/app.ico'))
    app.setApplicationDisplayName("MusicPlayer")

    alert = windows.Alert(Alert_text='Идёт загрузка')

    main_win = windows.MainWindow() # создаём главное окно

    alert.hide()

    sys.exit(app.exec())
