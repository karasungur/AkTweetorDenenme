import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

def main():
    """Ana program giriş noktası"""
    try:
        # Uygulama oluştur
        app = QApplication(sys.argv)
        app.setApplicationName("AkTweetor")

        # High DPI desteği
        try:
            app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        except:
            pass

        # Splash ekranını göster
        try:
            from ui.splash_screen import SplashScreen
            splash = SplashScreen()
            splash.show()
        except Exception as e:
            print(f"❌ Splash ekranı yüklenemedi: {str(e)}")
            # Direkt ana pencereyi aç
            from ui.main_window import MainWindow
            window = MainWindow()
            window.show()

        # Uygulamayı çalıştır
        sys.exit(app.exec_())

    except ImportError as e:
        print(f"❌ Modül import hatası: {str(e)}")
        print("💡 Lütfen PyQt5'i yükleyin: pip install PyQt5")

    except Exception as e:
        print(f"❌ Beklenmeyen hata: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()