import sys
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

from ui.main_window import MainWindow
from ui.splash_screen import SplashScreen
from config.settings import settings
from utils.logger import logger
from database.mysql import mysql_manager
from database.user_manager import user_manager

def main():
    """Ana uygulama fonksiyonu"""
    app = QApplication(sys.argv)

    # Uygulama bilgileri
    app.setApplicationName("AkTweetor")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("AkTweetor")

    # Splash screen
    splash = SplashScreen()
    splash.show()

    # Ana pencere
    main_window = MainWindow()

    # Splash screen'i kapat ve ana pencereyi göster
    QTimer.singleShot(3000, splash.close)
    QTimer.singleShot(3000, main_window.show)

    return app.exec_()

if __name__ == "__main__":
    main()