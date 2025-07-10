import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap

# UI dosyalarını yükle
from ui.main_window import MainWindow
from ui.splash_screen import SplashScreen

class AkTweetor:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.setup_app()
        self.create_directories()  # Klasörleri oluştur

        # Modern splash screen'i oluştur ve göster
        self.splash = SplashScreen()
        self.splash.show()

        # Ana pencere splash screen'den açılacak

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
                print(f"⚠️ Klasör oluşturma hatası: {e}")

        # MySQL bağlantısını test et
        try:
            from database.mysql import mysql_manager
            if mysql_manager.test_connection():
                print("✅ MySQL bağlantısı başarılı")
            else:
                print("⚠️ MySQL bağlantısı başarısız - Lütfen veritabanı ayarlarını kontrol edin")
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
            return 1

        return self.app.exec_()

if __name__ == "__main__":
    try:
        print("🚀 AkTweetor başlatılıyor...")
        aktweetor = AkTweetor()
        sys.exit(aktweetor.run())
    except Exception as e:
        print(f"❌ Kritik hata: {e}")
        sys.exit(1)