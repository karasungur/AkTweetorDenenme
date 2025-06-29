"""
IP Service - Tüm IP işlemlerini merkezi olarak yönetir
"""

import threading
import time
import requests
from PyQt5.QtCore import QTimer, QObject, pyqtSignal


class IPService(QObject):
    """IP adres yönetimi için merkezi servis"""
    
    # Signals
    normal_ip_updated = pyqtSignal(str)
    browser_ip_updated = pyqtSignal(str)
    ip_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.normal_ip = "Alınıyor..."
        self.browser_ip = "Tarayıcı açılmadı"
        
    def get_normal_ip(self, callback=None):
        """Bilgisayarın normal IP adresini al"""
        def get_ip_thread():
            try:
                print("🌐 Normal IP adresi alınıyor...")
                response = requests.get("https://api.ipify.org", timeout=15)
                ip = response.text.strip()
                
                self.normal_ip = ip
                self.normal_ip_updated.emit(ip)
                
                if callback:
                    QTimer.singleShot(0, lambda: callback(ip))
                    
                print(f"✅ Normal IP adresi alındı: {ip}")
                
            except Exception as e:
                error_msg = f"❌ Normal IP alma hatası: {str(e)}"
                print(error_msg)
                
                self.normal_ip = "Bağlantı hatası"
                self.ip_error.emit(error_msg)
                
                if callback:
                    QTimer.singleShot(0, lambda: callback("Bağlantı hatası"))
        
        thread = threading.Thread(target=get_ip_thread, daemon=True)
        thread.start()
    
    def get_browser_ip(self, driver, callback=None):
        """Tarayıcının IP adresini al"""
        def browser_ip_thread():
            try:
                print("🌐 Tarayıcı IP adresi kontrol ediliyor...")
                
                # Mevcut pencereyi kaydet
                original_window = driver.current_window_handle
                
                # Yeni sekme aç
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                
                # IP kontrol sitesine git
                driver.get("https://api.ipify.org")
                time.sleep(3)
                
                # IP adresini al
                browser_ip = driver.find_element("tag name", "body").text.strip()
                
                # Sekmeyi kapat ve geri dön
                driver.close()
                driver.switch_to.window(original_window)
                
                self.browser_ip = browser_ip
                self.browser_ip_updated.emit(browser_ip)
                
                if callback:
                    QTimer.singleShot(0, lambda: callback(browser_ip))
                    
                print(f"✅ Tarayıcı IP adresi: {browser_ip}")
                
            except Exception as e:
                error_msg = f"❌ Tarayıcı IP kontrol hatası: {str(e)}"
                print(error_msg)
                
                self.browser_ip = "IP alınamadı"
                self.ip_error.emit(error_msg)
                
                if callback:
                    QTimer.singleShot(0, lambda: callback("IP alınamadı"))
        
        thread = threading.Thread(target=browser_ip_thread, daemon=True)
        thread.start()
    
    def reset_ip_via_url(self, driver, reset_url, callback=None):
        """Belirtilen URL ile IP'yi sıfırla"""
        def reset_thread():
            try:
                print(f"🔄 IP sıfırlanıyor: {reset_url}")
                
                # Mevcut pencereyi kaydet
                original_window = driver.current_window_handle
                
                # Yeni sekme aç
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                
                # Reset URL'sine git
                driver.get(reset_url)
                time.sleep(5)
                
                # IP'yi tekrar kontrol et
                self.get_browser_ip(driver, callback)
                
                print("✅ IP sıfırlama tamamlandı")
                
            except Exception as e:
                error_msg = f"❌ IP sıfırlama hatası: {str(e)}"
                print(error_msg)
                self.ip_error.emit(error_msg)
        
        thread = threading.Thread(target=reset_thread, daemon=True)
        thread.start()


# Global IP service instance
ip_service = IPService()
