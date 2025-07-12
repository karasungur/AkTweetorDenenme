
import sys
import os

# PyQt5 import denemesi
try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QSplashScreen
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QPixmap, QFont
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    print("⚠️ PyQt5 yüklenemedi, web arayüzü başlatılacak...")

if PYQT5_AVAILABLE:
    # Mevcut PyQt5 arayüzü
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

else:
    # Web arayüzü fallback
    import flask
    from flask import Flask, render_template_string, request, jsonify
    
    app = Flask(__name__)
    
    WEB_TEMPLATE = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AkTweetor - Web Arayüzü</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .menu { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
            .menu-item { padding: 20px; background: #007bff; color: white; text-decoration: none; border-radius: 8px; text-align: center; transition: background 0.3s; }
            .menu-item:hover { background: #0056b3; }
            .stats { margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🐦 AkTweetor</h1>
                <p>Twitter Hesap Yönetim Sistemi - Web Arayüzü</p>
            </div>
            
            <div class="menu">
                <a href="/users" class="menu-item">
                    <h3>👥 Kullanıcı Yönetimi</h3>
                    <p>Hesapları yönetin</p>
                </a>
                <a href="/targets" class="menu-item">
                    <h3>🎯 Hedef Hesaplar</h3>
                    <p>Takip edilecek hesapları yönetin</p>
                </a>
                <a href="/categories" class="menu-item">
                    <h3>🏷️ Kategori Yönetimi</h3>
                    <p>Hesaplara kategori atayın</p>
                </a>
                <a href="/stats" class="menu-item">
                    <h3>📊 İstatistikler</h3>
                    <p>Kategori dağılımlarını görüntüleyin</p>
                </a>
            </div>
            
            <div class="stats">
                <h3>📈 Hızlı İstatistikler</h3>
                <div id="stats-content">Yükleniyor...</div>
            </div>
        </div>
        
        <script>
            // Basit istatistikler yükleme
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('stats-content').innerHTML = 
                        `<p>Toplam Kullanıcı: ${data.users || 0}</p>
                         <p>Hedef Hesap: ${data.targets || 0}</p>
                         <p>Kategori: ${data.categories || 0}</p>`;
                })
                .catch(error => {
                    document.getElementById('stats-content').innerHTML = 'İstatistikler yüklenemedi';
                });
        </script>
    </body>
    </html>
    '''
    
    @app.route('/')
    def index():
        return render_template_string(WEB_TEMPLATE)
    
    @app.route('/api/stats')
    def api_stats():
        try:
            from database.mysql import mysql_manager
            from database.user_manager import user_manager
            
            users = user_manager.get_all_users()
            targets = mysql_manager.get_all_targets()
            categories = mysql_manager.get_categories()
            
            return jsonify({
                'users': len(users),
                'targets': len(targets),
                'categories': len(set([(cat['kategori_turu'], cat['ana_kategori']) for cat in categories]))
            })
        except Exception as e:
            return jsonify({'error': str(e)})
    
    @app.route('/users')
    def users():
        return "<h1>Kullanıcı Yönetimi</h1><p>Bu özellik PyQt5 arayüzünde mevcuttur.</p>"
    
    @app.route('/targets')
    def targets():
        return "<h1>Hedef Hesaplar</h1><p>Bu özellik PyQt5 arayüzünde mevcuttur.</p>"
    
    @app.route('/categories')
    def categories():
        return "<h1>Kategori Yönetimi</h1><p>Bu özellik PyQt5 arayüzünde mevcuttur.</p>"
    
    @app.route('/stats')
    def stats():
        return "<h1>İstatistikler</h1><p>Bu özellik PyQt5 arayüzünde mevcuttur.</p>"
    
    def main():
        print("🌐 Web arayüzü başlatılıyor...")
        print("📱 Tarayıcınızda şu adrese gidin: http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()
