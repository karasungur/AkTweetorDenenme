import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap

# UI dosyalarını yükle
from ui.main_window import MainWindow

class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap("ui/logo.png")  # Logo dosyasının yolu
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setEnabled(False)

        self.progress = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.advance)
        self.timer.start(30)  # 30ms aralıklarla advance fonksiyonunu çağır

    def advance(self):
        self.progress += 1
        if self.progress > 100:
            self.timer.stop()
            self.close()  # Splash screen'i kapat
            return
        self.showMessage(f"Yükleniyor... {self.progress}%", Qt.AlignBottom | Qt.AlignCenter, Qt.black)

class AkTweetor:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.setup_app()
        self.create_directories()  # Klasörleri oluştur
        # Splash screen'i oluştur ve göster
        self.splash = SplashScreen()
        self.splash.show()
        QTimer.singleShot(3000, self.show_main_window) # 3 saniye sonra ana pencereyi göster

    def show_main_window(self):
        self.main_window = MainWindow()
        self.main_window.show()

    def setup_app(self):
        """Uygulama ayarlarını yapılandır"""
        self.app.setApplicationName("AkTweetor")
        self.app.setApplicationVersion("1.0")
        self.app.setOrganizationName("AkTweetor")

        # Global font ayarı
        font = QFont("SF Pro Display", 10)  # Apple'ın fontu
        self.app.setFont(font)

        # Global stil
        self.app.setStyleSheet(self.get_global_style())

    def create_directories(self):
        """Gerekli klasörleri oluştur"""
        directories = [
            "./Profiller",
            "./TempProfiller"
        ]

        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"✅ Klasör oluşturuldu/kontrol edildi: {directory}")
            except Exception as e:
                print(f"⚠️ Klasör oluşturma hatası {directory}: {str(e)}")

        # MySQL bağlantısını test et
        try:
            from database.mysql_config import mysql_config
            if mysql_config.test_connection():
                print("✅ MySQL bağlantısı başarılı")
            else:
                print("⚠️ MySQL bağlantısı başarısız - Lütfen database/mysql_config.py dosyasını kontrol edin")
        except Exception as e:
            print(f"⚠️ MySQL modülü yüklenemedi: {str(e)}")

    def get_global_style(self):
        """Global stil tanımları"""
        return """
        QApplication {
            background-color: #FFFFFF;
            color: #231F20;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
        }

        /* Scrollbar Styling */
        QScrollBar:vertical {
            background: #F5F5F7;
            width: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical {
            background: #C7C7CC;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background: #AEAEB2;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }

        /* Horizontal Scrollbar */
        QScrollBar:horizontal {
            background: #F5F5F7;
            height: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:horizontal {
            background: #C7C7CC;
            border-radius: 6px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background: #AEAEB2;
        }

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        """

    def run(self):
        """Uygulamayı başlat"""
        # chromedriver.exe kontrolü
        if not os.path.exists("chromedriver.exe"):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Hata")
            msg.setText("chromedriver.exe dosyası bulunamadı!")
            msg.setInformativeText("Lütfen chromedriver.exe dosyasını uygulama klasörüne koyun.")
            msg.setDetailedText("""
ChromeDriver İndirme Adımları:
1. https://chromedriver.chromium.org/ adresine gidin
2. Chrome sürümünüze uygun driver'ı indirin
3. chromedriver.exe dosyasını bu klasöre koyun
4. Uygulamayı yeniden başlatın
            """)
            msg.exec_()
            sys.exit(1)

        # self.main_window.show() #Ana pencere burada başlatılıyordu, artık splash screen başlatıyor.
        return self.app.exec_()

if __name__ == "__main__":
    app = AkTweetor()
    sys.exit(app.run())