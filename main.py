
import sys
import os
import traceback

def main():
    """Ana program giriş noktası"""
    try:
        # Ortam tespiti (Replit vs PyCharm)
        if 'REPL_ID' in os.environ:
            # Replit ortamı
            os.environ['DISPLAY'] = ':0'
            os.environ['QT_QPA_PLATFORM'] = 'xcb'
        else:
            # PyCharm/Local ortam - Qt platformu ayarlama
            if sys.platform == "win32":
                os.environ['QT_QPA_PLATFORM'] = 'windows'
            elif sys.platform == "darwin":
                os.environ['QT_QPA_PLATFORM'] = 'cocoa'
            else:
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

        # Splash ekranını göster
        try:
            from ui.splash_screen import SplashScreen
            splash = SplashScreen()
            splash.show()
            app.processEvents()  # Splash ekranını göster
            
            # Ana pencereyi yükle
            from ui.main_window import MainWindow
            window = MainWindow()
            
            # Splash'ı kapat ve ana pencereyi göster
            splash.close()
            window.show()
            
            print("🚀 AkTweetor başlatıldı!")
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
