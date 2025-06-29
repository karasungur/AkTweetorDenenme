"""
Driver Manager - Chrome driver işlemlerini merkezi olarak yönetir
"""

import os
import uuid
import time
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class DriverManager:
    """Chrome driver yönetimi için merkezi servis"""
    
    def __init__(self):
        self.active_drivers = []
    
    def create_driver(self, user_data, proxy_settings=None, headless=False):
        """Chrome driver oluştur"""
        try:
            options = Options()
            
            # Profil ayarları
            unique_id = str(uuid.uuid4())[:8]
            profile_path = os.path.abspath(f"./TempProfiller/{user_data['username']}_{unique_id}")
            
            # Profil dizinini oluştur
            os.makedirs(profile_path, exist_ok=True)
            
            # Mevcut Chrome process'lerini kapat
            self.close_existing_processes(user_data['username'])
            
            # Chrome seçenekleri
            options.add_argument(f"--user-data-dir={profile_path}")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-default-apps")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            
            # Headless mode
            if headless:
                options.add_argument("--headless=new")
            
            # Proxy ayarları
            proxy_to_use = self._get_proxy_setting(user_data, proxy_settings)
            if proxy_to_use:
                # Kimlik doğrulamalı proxy kontrolü
                if proxy_to_use.count(':') >= 3:
                    print(f"⚠️ Kimlik doğrulamalı proxy tespit edildi, atlanıyor.")
                    return None
                    
                options.add_argument(f"--proxy-server={proxy_to_use}")
                print(f"🌐 Proxy kullanılıyor: {proxy_to_use}")
            
            # Anti-detection ayarları
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Chrome service
            service = Service("chromedriver.exe")
            service.hide_command_prompt_window = True
            
            # Driver oluştur
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Driver bilgilerini kaydet
            driver_info = {
                'driver': driver,
                'username': user_data['username'],
                'profile_path': profile_path,
                'created_at': time.time()
            }
            
            self.active_drivers.append(driver_info)
            
            print(f"✅ Driver oluşturuldu: {user_data['username']}")
            return driver
            
        except Exception as e:
            print(f"❌ Driver oluşturma hatası: {str(e)}")
            return None
    
    def _get_proxy_setting(self, user_data, proxy_settings):
        """Proxy ayarını belirle"""
        # Önce kullanıcıya özel proxy'yi kontrol et
        if user_data.get('proxy') and user_data.get('proxy_port'):
            return f"{user_data['proxy']}:{user_data['proxy_port']}"
        
        # Sonra genel proxy ayarını kontrol et
        if proxy_settings and proxy_settings.get('enabled') and proxy_settings.get('address'):
            return proxy_settings['address']
        
        return None
    
    def close_existing_processes(self, username):
        """Kullanıcıya ait mevcut Chrome process'lerini kapat"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        if proc.info['cmdline']:
                            cmdline = ' '.join(proc.info['cmdline'])
                            if username in cmdline and 'user-data-dir' in cmdline:
                                proc.terminate()
                                proc.wait(timeout=3)
                                print(f"🔄 {username} için mevcut Chrome process kapatıldı")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
        except Exception as e:
            print(f"⚠️ Process kapatma hatası: {str(e)}")
    
    def safe_quit_driver(self, driver, username):
        """Driver'ı güvenli şekilde kapat"""
        try:
            # Driver listesinden çıkar
            self.active_drivers = [d for d in self.active_drivers if d['driver'] != driver]
            
            # Driver'ı kapat
            driver.quit()
            time.sleep(2)
            
            # Zombie process'leri temizle
            self.cleanup_zombie_processes(username)
            
            print(f"✅ Driver güvenli şekilde kapatıldı: {username}")
            
        except Exception as e:
            print(f"❌ Driver kapatma hatası: {str(e)}")
    
    def cleanup_zombie_processes(self, username):
        """Zombie process'leri temizle"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        if proc.info['cmdline']:
                            cmdline = ' '.join(proc.info['cmdline'])
                            if username in cmdline:
                                proc.terminate()
                                try:
                                    proc.wait(timeout=3)
                                    print(f"🧹 {username} zombie process temizlendi")
                                except psutil.TimeoutExpired:
                                    proc.kill()
                                    print(f"🔥 {username} zorla kapatıldı")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"⚠️ Zombie process temizleme hatası: {str(e)}")
    
    def get_active_drivers(self):
        """Aktif driver'ları getir"""
        return self.active_drivers
    
    def close_all_drivers(self):
        """Tüm aktif driver'ları kapat"""
        for driver_info in self.active_drivers[:]:  # Copy list to avoid modification during iteration
            try:
                self.safe_quit_driver(driver_info['driver'], driver_info['username'])
            except:
                pass
        
        self.active_drivers.clear()
        print("✅ Tüm driver'lar kapatıldı")


# Global driver manager instance
driver_manager = DriverManager()
