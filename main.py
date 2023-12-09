import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

import windows


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('src/app.ico'))
    app.setApplicationDisplayName("MusicPlayer")

    main_win = windows.MainWindow()

    sys.exit(app.exec())
