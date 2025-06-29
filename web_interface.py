#!/usr/bin/env python3
"""
Web interface for AkTweetor - Twitter Automation Tool
Since the main application is a PyQt5 desktop app that cannot run in web environment,
this provides a simple web interface to show application information and status.
"""

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from datetime import datetime

class AkTweetorWebHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Get application status
            status_info = self.get_app_status()
            
            html_content = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AkTweetor - Twitter Otomasyon Aracı</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            max-width: 800px;
            width: 90%;
            text-align: center;
        }}
        .logo {{
            font-size: 3em;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 1.2em;
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 10px;
            padding: 20px;
            margin: 30px 0;
            color: #856404;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .info-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #3498db;
        }}
        .info-card h3 {{
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .status {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin: 5px;
        }}
        .status.success {{
            background: #d4edda;
            color: #155724;
        }}
        .status.error {{
            background: #f8d7da;
            color: #721c24;
        }}
        .features {{
            text-align: left;
            margin: 30px 0;
        }}
        .features ul {{
            list-style: none;
            padding: 0;
        }}
        .features li {{
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .features li:before {{
            content: "✅ ";
            margin-right: 10px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🐦</div>
        <h1>AkTweetor</h1>
        <div class="subtitle">Twitter Otomasyon Aracı</div>
        
        <div class="warning">
            <h3>⚠️ Desktop Uygulaması</h3>
            <p>Bu uygulama PyQt5 kullanarak geliştirilmiş bir <strong>desktop uygulamasıdır</strong>. 
            Web tarayıcısında çalışmaz ve görsel arayüz için X11/display server gerektirir.</p>
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <h3>📊 Uygulama Durumu</h3>
                <div class="status {'success' if status_info['dependencies_installed'] else 'error'}">
                    Bağımlılıklar: {'Yüklü' if status_info['dependencies_installed'] else 'Eksik'}
                </div>
                <div class="status {'success' if status_info['chromedriver_exists'] else 'error'}">
                    ChromeDriver: {'Mevcut' if status_info['chromedriver_exists'] else 'Eksik'}
                </div>
                <div class="status {'success' if status_info['profiles_dir_exists'] else 'error'}">
                    Profil Klasörü: {'Mevcut' if status_info['profiles_dir_exists'] else 'Eksik'}
                </div>
            </div>
            
            <div class="info-card">
                <h3>📁 Dosya Bilgileri</h3>
                <p><strong>Profil Sayısı:</strong> {status_info['profile_count']}</p>
                <p><strong>Ana Dosyalar:</strong> {len(status_info['main_files'])} dosya</p>
                <p><strong>UI Dosyalar:</strong> {len(status_info['ui_files'])} dosya</p>
            </div>
        </div>
        
        <div class="features">
            <h3>🚀 Özellikler</h3>
            <ul>
                <li>Twitter hesaplarına otomatik giriş</li>
                <li>Profil bazlı oturum yönetimi</li>
                <li>Proxy desteği</li>
                <li>IP adresi takibi</li>
                <li>MySQL veritabanı entegrasyonu</li>
                <li>Kullanıcı doğrulama ve silme</li>
                <li>Güvenli profil kaydetme</li>
            </ul>
        </div>
        
        <div class="info-card">
            <h3>🔧 Nasıl Çalıştırılır</h3>
            <p>Bu uygulamayı çalıştırmak için:</p>
            <ol style="text-align: left; margin-top: 15px;">
                <li>Uygulamayı desktop environment'a indirin</li>
                <li><code>python3 -m venv venv</code> ile virtual environment oluşturun</li>
                <li><code>source venv/bin/activate</code> ile aktive edin</li>
                <li><code>pip install -r requirements.txt</code> ile bağımlılıkları yükleyin</li>
                <li><code>python main.py</code> ile uygulamayı başlatın</li>
            </ol>
        </div>
        
        <div class="footer">
            <p>Güncelleme: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
            <p>Bu web arayüzü sadece bilgilendirme amaçlıdır. Gerçek uygulama desktop ortamında çalışır.</p>
        </div>
    </div>
</body>
</html>
            """
            self.wfile.write(html_content.encode())
        else:
            super().do_GET()
    
    def get_app_status(self):
        """Get application status information"""
        status = {
            'dependencies_installed': False,
            'chromedriver_exists': False,
            'profiles_dir_exists': False,
            'profile_count': 0,
            'main_files': [],
            'ui_files': []
        }
        
        # Check if dependencies are installed
        try:
            import PyQt5
            import selenium
            import mysql.connector
            import requests
            import psutil
            status['dependencies_installed'] = True
        except ImportError:
            pass
        
        # Check if chromedriver exists
        if os.path.exists('chromedriver.exe'):
            status['chromedriver_exists'] = True
        
        # Check profiles directory
        if os.path.exists('./Profiller'):
            status['profiles_dir_exists'] = True
            try:
                profiles = [d for d in os.listdir('./Profiller') if os.path.isdir(os.path.join('./Profiller', d))]
                status['profile_count'] = len(profiles)
            except:
                pass
        
        # Get main files
        main_files = ['main.py', 'requirements.txt', 'README.md']
        status['main_files'] = [f for f in main_files if os.path.exists(f)]
        
        # Get UI files
        if os.path.exists('./ui'):
            try:
                ui_files = [f for f in os.listdir('./ui') if f.endswith('.py')]
                status['ui_files'] = ui_files
            except:
                pass
        
        return status

def main():
    port = int(os.environ.get('PORT', 3000))
    server = HTTPServer(('0.0.0.0', port), AkTweetorWebHandler)
    print(f"🌐 AkTweetor Web Interface başlatıldı: http://localhost:{port}")
    print("📝 Bu desktop uygulamasının web arayüzüdür - sadece bilgi amaçlıdır.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server kapatıldı.")
        server.shutdown()

if __name__ == '__main__':
    main()
