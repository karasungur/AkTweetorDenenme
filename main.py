
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
        print("🌐 PyQt5 yüklenemedi, web arayüzü başlatılıyor...")
        
        # Flask web arayüzünü başlat
        try:
            start_web_interface()
        except Exception as web_error:
            print(f"❌ Web arayüzü de başlatılamadı: {str(web_error)}")
            print("💡 Lütfen PyQt5'i yükleyin: pip install PyQt5")
            
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {str(e)}")
        traceback.print_exc()

def start_web_interface():
    """Web arayüzünü başlat (fallback)"""
    try:
        from flask import Flask, render_template, request, jsonify
        from config.settings import load_config
        from database.mysql import mysql_manager
        from database.user_manager import user_manager
        from utils.logger import setup_logger
        
        app = Flask(__name__)
        app.secret_key = 'aktweetor_secret_key_2024'
        
        logger = setup_logger()
        
        @app.route('/')
        def index():
            return render_template('index.html')
            
        @app.route('/categories')
        def categories():
            return render_template('categories.html')
            
        @app.route('/targets')
        def targets():
            return render_template('targets.html')
            
        @app.route('/stats')
        def stats():
            return render_template('stats.html')
            
        print("🌐 Web arayüzü başlatılıyor...")
        print("🔗 http://localhost:5000 adresinde erişilebilir")
        
        # Web sunucusunu başlat
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        print(f"❌ Web arayüzü başlatma hatası: {str(e)}")
        raise

if __name__ == "__main__":
    main()
