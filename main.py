import sys
import os
import traceback

# Qt'yi headless modda çalıştırmak için environment variable'ları ayarla
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['DISPLAY'] = ':99'

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

def main():
    """Ana program giriş noktası"""
    try:
        # Minimal backend ile uygulama oluştur
        app = QApplication(sys.argv)
        app.setApplicationName("AkTweetor")
        
        # OpenGL gerektirmeyen backend kullan
        try:
            app.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
        except:
            pass

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