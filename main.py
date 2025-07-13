
import sys
import os
import traceback

def main():
    """Ana program giriş noktası"""
    try:
        # Replit GUI ayarları
        os.environ['DISPLAY'] = ':0'
        os.environ['QT_QPA_PLATFORM'] = 'xcb'
        
        from PyQt5.QtWidgets import QApplication, QMessageBox
        from PyQt5.QtCore import Qt
        
        # Uygulama oluştur
        app = QApplication(sys.argv)
        app.setApplicationName("AkTweetor")
        
        # High DPI desteği
        try:
            app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        except:
            pass

        # Ana pencereyi göster
        from ui.main_window import MainWindow
        window = MainWindow()
        window.show()

        print("🚀 AkTweetor başlatıldı!")
        print("📱 GUI penceresi açıldı")
        
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
