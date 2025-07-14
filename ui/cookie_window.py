from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QMessageBox, QListWidget, QLineEdit,
                             QCheckBox, QGroupBox, QSpinBox, QTextEdit, QListWidgetItem,
                             QSplitter, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import threading
import time
import requests
import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from database.user_manager import user_manager

class CookieWorkerThread(QThread):
    """Çerez toplama işlemlerini yapan thread"""
    log_signal = pyqtSignal(str)
    update_last_log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    profile_stats_signal = pyqtSignal(str, dict)
    ip_signal = pyqtSignal(str)
    current_profile_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, profiles, settings):
        super().__init__()
        self.profiles = profiles
        self.settings = settings
        self.is_running = False
        self.profile_stats = {}

    def run(self):
        """Ana işlem döngüsü - SONSUZ DÖNGÜ"""
        self.is_running = True
        total_profiles = len(self.profiles)
        cycle_count = 0

        while self.is_running:
            cycle_count += 1
            self.log_signal.emit(f"\n🔄 DÖNGÜ {cycle_count} BAŞLADI - {total_profiles} profil işlenecek\n")

            for i, profile in enumerate(self.profiles):
                if not self.is_running:
                    break

                self.log_signal.emit(f"📂 {profile} profili işleniyor...")
                self.current_profile_signal.emit(profile)
                self.progress_signal.emit(i + 1, total_profiles)

                try:
                    success = self.process_profile(profile)

                    if success:
                        self.log_signal.emit(f"✅ {profile} başarıyla tamamlandı")
                    else:
                        self.log_signal.emit(f"❌ {profile} işlem başarısız")

                except Exception as e:
                    self.log_signal.emit(f"❌ {profile} hata: {str(e)}")

                # Profiller arası bekleme
                if i < len(self.profiles) - 1:
                    wait_time = random.randint(3, 8)
                    self.log_signal.emit(f"⏱️ Sonraki profil için {wait_time} saniye bekleniyor...")
                    for j in range(wait_time):
                        if not self.is_running:
                            break
                        time.sleep(1)

                if not self.is_running:
                    break

            if self.is_running:
                # Döngü arası bekleme
                cycle_wait = random.randint(10, 20)
                self.log_signal.emit(f"\n🔄 Döngü {cycle_count} tamamlandı. Yeni döngü için {cycle_wait} saniye bekleniyor...\n")
                for j in range(cycle_wait):
                    if not self.is_running:
                        break
                    time.sleep(1)

        self.finished_signal.emit()

    def process_profile(self, profile):
        """Tek profil işlemi"""
        driver = None
        try:
            # Chrome driver oluştur
            driver = self.create_driver(profile)
            if not driver:
                return False

            # İLK ÖNCE IP kontrolü yap (gezinme işlemi başlamadan)
            browser_ip = self.check_browser_ip(driver)
            if not browser_ip:
                self.log_signal.emit(f"⚠️ {profile} IP kontrol edilemedi")
                return False

            # Proxy kontrolü (proxy aktifse)
            if self.settings['proxy_enabled']:
                if not self.validate_proxy(browser_ip):
                    self.log_signal.emit(f"⚠️ {profile} proxy çalışmıyor, atlanıyor")
                    return False

            # X.com'a git
            driver.get("https://x.com/")
            time.sleep(3)

            # Scroll simülasyonu
            scroll_duration = random.randint(
                self.settings['min_duration'], 
                self.settings['max_duration']
            )

            self.simulate_scroll(driver, profile, scroll_duration)



            # Çerezleri kaydet
            self.save_cookies_to_mysql(driver, profile)

            # İstatistik güncelle
            self.update_profile_stats(profile, scroll_duration)

            # IP sıfırlama (opsiyonel)
            if self.settings['ip_reset_enabled'] and self.settings['ip_reset_url']:
                self.reset_ip()
                self.log_signal.emit(f"⏱️ {profile} IP reset sonrası 10 saniye bekleniyor...")
                time.sleep(10)

            return True

        except Exception as e:
            self.log_signal.emit(f"❌ {profile} işlem hatası: {str(e)}")
            return False
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def create_driver(self, profile):
        """Chrome driver oluştur"""
        try:
            options = Options()

            # Profil ayarı
            profile_path = os.path.abspath(f"./Profiller/{profile}")
            if not os.path.exists(profile_path):
                self.log_signal.emit(f"❌ {profile} profil klasörü bulunamadı")
                return None

            options.add_argument(f"--user-data-dir={profile_path}")

            # Proxy ayarı
            if self.settings['proxy_enabled'] and self.settings['proxy_address']:
                options.add_argument(f"--proxy-server={self.settings['proxy_address']}")

            # Görünürlük ayarı
            if not self.settings['browser_visible']:
                options.add_argument("--headless=new")

            # Diğer ayarlar
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            service = Service("chromedriver.exe")
            service.hide_command_prompt_window = True

            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            return driver

        except Exception as e:
            self.log_signal.emit(f"❌ Driver oluşturma hatası: {str(e)}")
            return None

    def check_browser_ip(self, driver):
        """Tarayıcı IP kontrolü"""
        try:
            driver.get("https://api.ipify.org")
            time.sleep(2)

            browser_ip = driver.find_element("tag name", "body").text.strip()
            self.ip_signal.emit(browser_ip)

            return browser_ip

        except Exception as e:
            self.log_signal.emit(f"❌ IP kontrol hatası: {str(e)}")
            return None

    def validate_proxy(self, browser_ip):
        """Proxy doğrulama"""
        try:
            # Normal IP al
            response = requests.get("https://api.ipify.org", timeout=5)
            normal_ip = response.text.strip()

            if browser_ip == normal_ip:
                return False  # Proxy çalışmıyor

            return True  # Proxy çalışıyor

        except:
            return True  # Hata durumunda devam et

    def simulate_scroll(self, driver, profile, duration):
        """Scroll simülasyonu"""
        self.log_signal.emit(f"📜 {profile} scroll simülasyonu başlatıldı ({duration}s)")

        start_time = time.time()
        last_remaining_log = None

        while time.time() - start_time < duration and self.is_running:
            # Rastgele scroll
            scroll_amount = random.randint(300, 800)
            direction = random.choice([1, -1])  # Yukarı veya aşağı

            driver.execute_script(f"window.scrollBy(0, {scroll_amount * direction});")

            # Kalan süre hesapla - tek satırda güncelle
            remaining = duration - (time.time() - start_time)
            remaining_msg = f"⏱️ {profile} kalan: {remaining:.1f}s"

            # Son mesajı güncelle (aynı satırda)
            if last_remaining_log:
                # Önceki kalan süre mesajını güncelle
                self.update_last_log_signal.emit(remaining_msg)
            else:
                self.log_signal.emit(remaining_msg)
            last_remaining_log = remaining_msg

            # Rastgele bekleme
            wait_time = random.randint(500, 1500) / 1000
            time.sleep(wait_time)

    def save_cookies_to_mysql(self, driver, profile):
        """Çerezleri MySQL'e kaydet"""
        try:
            # X.com'a dön
            driver.get("https://x.com/")
            time.sleep(3)

            # Çerezleri al
            cookies = driver.get_cookies()

            target_cookies = [
                'auth_token', 'gt', 'guest_id', 'twid', 'lang', '__cf_bm',
                'att', 'ct0', 'd_prefs', 'dnt', 'guest_id_ads',
                'guest_id_marketing', 'kdt', 'personalization_id'
            ]

            cookie_dict = {}
            for cookie in cookies:
                if cookie['name'] in target_cookies:
                    cookie_dict[cookie['name']] = cookie['value']

            # MySQL'e kaydet
            if cookie_dict:
                success = user_manager.update_user(profile, None, cookie_dict)
                if success:
                    self.log_signal.emit(f"🍪 {profile} çerezler kaydedildi ({len(cookie_dict)} adet)")
                else:
                    self.log_signal.emit(f"⚠️ {profile} çerezler kaydedilemedi")
            else:
                self.log_signal.emit(f"⚠️ {profile} çerez bulunamadı")

        except Exception as e:
            self.log_signal.emit(f"❌ {profile} çerez kaydetme hatası: {str(e)}")

    def update_profile_stats(self, profile, duration):
        """Profil istatistiklerini güncelle"""
        if profile not in self.profile_stats:
            self.profile_stats[profile] = {'count': 0, 'total_time': 0}

        self.profile_stats[profile]['count'] += 1
        self.profile_stats[profile]['total_time'] += duration

        self.profile_stats_signal.emit(profile, self.profile_stats[profile])

    def reset_ip(self):
        """IP sıfırlama"""
        try:
            reset_url = self.settings['ip_reset_url']
            response = requests.get(reset_url, timeout=10)

            if response.status_code == 200:
                self.log_signal.emit("🔄 IP başarıyla sıfırlandı")
            else:
                self.log_signal.emit(f"⚠️ IP sıfırlama yanıtı: {response.status_code}")

        except Exception as e:
            self.log_signal.emit(f"❌ IP sıfırlama hatası: {str(e)}")

    def stop(self):
        """İşlemi durdur"""
        self.is_running = False

class CookieWindow(QWidget):
    def __init__(self, colors, return_callback):
        super().__init__()
        self.colors = colors
        self.return_callback = return_callback
        self.profiles = []
        self.current_ip = "Kontrol ediliyor..."
        self.browser_ip = "Henüz kontrol edilmedi"
        self.worker_thread = None
        self.profile_stats = {}

        # IP monitoring timer
        self.ip_timer = QTimer()
        self.ip_timer.timeout.connect(self.update_ip)

        self.init_ui()
        self.setup_style()
        self.load_profiles()
        self.start_ip_monitoring()

    def init_ui(self):
        """UI'yi başlat"""
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Ana Menüye Dön")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(self.return_to_main)
        back_btn.setCursor(Qt.PointingHandCursor)

        title_label = QLabel("🍪 Çerez Kasıcı/Çerez Çıkarıcı")
        title_label.setObjectName("pageTitle")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Ana içerik - Splitter ile bölünmüş
        main_splitter = QSplitter(Qt.Horizontal)

        # Sol panel - Kontroller
        left_panel = self.create_control_panel()
        main_splitter.addWidget(left_panel)

        # Sağ panel - Log ve İstatistikler
        right_panel = self.create_log_panel()
        main_splitter.addWidget(right_panel)

        # Splitter oranları
        main_splitter.setSizes([400, 500])

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setVisible(False)

        # Ana layout'a ekle
        layout.addLayout(header_layout)
        layout.addWidget(main_splitter, 1)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def create_control_panel(self):
        """Kontrol panelini oluştur"""
        panel = QFrame()
        panel.setObjectName("controlPanel")
        layout = QVBoxLayout()

        # Profil bilgisi
        profiles_group = QGroupBox("📁 Profil Bilgisi")
        profiles_group.setObjectName("profilesGroup")
        profiles_layout = QVBoxLayout()

        # Profil sayısı bilgisi
        self.profile_count_label = QLabel("📊 Yüklenen profil sayısı: 0")
        self.profile_count_label.setObjectName("profileCountLabel")

        # Mevcut profil bilgisi
        self.current_profile_label = QLabel("📂 Şu anda işlenen: Henüz başlamadı")
        self.current_profile_label.setObjectName("currentProfileLabel")

        profiles_layout.addWidget(self.profile_count_label)
        profiles_layout.addWidget(self.current_profile_label)
        profiles_group.setLayout(profiles_layout)

        # Ayarlar grubu
        settings_group = QGroupBox("⚙️ Ayarlar")
        settings_group.setObjectName("settingsGroup")
        settings_layout = QVBoxLayout()

        # Süre ayarları
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Gezinme süresi:"))

        self.min_duration = QSpinBox()
        self.min_duration.setRange(10, 300)
        self.min_duration.setValue(30)
        self.min_duration.setSuffix(" sn")
        self.min_duration.setObjectName("settingsSpinBox")

        duration_layout.addWidget(QLabel("Min:"))
        duration_layout.addWidget(self.min_duration)

        self.max_duration = QSpinBox()
        self.max_duration.setRange(10, 300)
        self.max_duration.setValue(60)
        self.max_duration.setSuffix(" sn")
        self.max_duration.setObjectName("settingsSpinBox")

        duration_layout.addWidget(QLabel("Max:"))
        duration_layout.addWidget(self.max_duration)
        duration_layout.addStretch()

        # Proxy ayarları
        self.proxy_enabled = QCheckBox("Proxy kullan")
        self.proxy_enabled.setObjectName("settingsCheckbox")
        self.proxy_enabled.toggled.connect(self.toggle_proxy)

        self.proxy_entry = QLineEdit()
        self.proxy_entry.setPlaceholderText("IP:Port")
        self.proxy_entry.setObjectName("settingsInput")
        self.proxy_entry.setEnabled(False)

        # IP Reset ayarları
        self.ip_reset_enabled = QCheckBox("IP Reset kullan")
        self.ip_reset_enabled.setObjectName("settingsCheckbox")
        self.ip_reset_enabled.toggled.connect(self.toggle_ip_reset)

        self.ip_reset_entry = QLineEdit()
        self.ip_reset_entry.setPlaceholderText("http://reset-url.com")
        self.ip_reset_entry.setObjectName("settingsInput")
        self.ip_reset_entry.setEnabled(False)



        # Tarayıcı görünürlük
        self.browser_visible = QCheckBox("Tarayıcı görünür olsun")
        self.browser_visible.setObjectName("settingsCheckbox")
        self.browser_visible.setChecked(True)

        settings_layout.addLayout(duration_layout)
        settings_layout.addWidget(self.proxy_enabled)
        settings_layout.addWidget(self.proxy_entry)
        settings_layout.addWidget(self.ip_reset_enabled)
        settings_layout.addWidget(self.ip_reset_entry)
        settings_layout.addWidget(self.browser_visible)

        settings_group.setLayout(settings_layout)

        # IP bilgisi
        ip_group = QGroupBox("🌐 IP Bilgisi")
        ip_group.setObjectName("ipGroup")
        ip_layout = QVBoxLayout()

        computer_ip_layout = QHBoxLayout()
        computer_ip_label = QLabel("💻 Normal IP:")
        self.computer_ip_display = QLabel(self.current_ip)
        self.computer_ip_display.setObjectName("ipDisplay")
        computer_ip_layout.addWidget(computer_ip_label)
        computer_ip_layout.addWidget(self.computer_ip_display)
        computer_ip_layout.addStretch()

        browser_ip_layout = QHBoxLayout()
        browser_ip_label = QLabel("🌐 Tarayıcı IP:")
        self.browser_ip_display = QLabel(self.browser_ip)
        self.browser_ip_display.setObjectName("ipDisplay")
        browser_ip_layout.addWidget(browser_ip_label)
        browser_ip_layout.addWidget(self.browser_ip_display)
        browser_ip_layout.addStretch()

        ip_layout.addLayout(computer_ip_layout)
        ip_layout.addLayout(browser_ip_layout)
        ip_group.setLayout(ip_layout)

        # Başlat butonu
        self.start_btn = QPushButton("🚀 Başlat")
        self.start_btn.setObjectName("startButton")
        self.start_btn.clicked.connect(self.start_process)
        self.start_btn.setCursor(Qt.PointingHandCursor)

        self.stop_btn = QPushButton("⏹️ Durdur")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.clicked.connect(self.stop_process)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setEnabled(False)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)

        # Ana layout'a ekle
        layout.addWidget(profiles_group)
        layout.addWidget(settings_group)
        layout.addWidget(ip_group)
        layout.addLayout(button_layout)
        
        # JSON Çıkarıcı butonu
        self.json_btn = QPushButton("📤 JSON Çıkartıcı")
        self.json_btn.setObjectName("jsonButton")
        self.json_btn.clicked.connect(self.open_json_extractor)
        self.json_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.json_btn)

        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def create_log_panel(self):
        """Log panelini oluştur"""
        panel = QFrame()
        panel.setObjectName("logPanel")
        layout = QVBoxLayout()

        # İstatistikler
        stats_group = QGroupBox("📊 Profil İstatistikleri")
        stats_group.setObjectName("statsGroup")
        stats_layout = QVBoxLayout()

        self.stats_text = QTextEdit()
        self.stats_text.setObjectName("statsText")
        self.stats_text.setMaximumHeight(150)
        self.stats_text.setReadOnly(True)

        stats_layout.addWidget(self.stats_text)
        stats_group.setLayout(stats_layout)

        # Log alanı
        log_group = QGroupBox("📋 İşlem Logları")
        log_group.setObjectName("logGroup")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setObjectName("logText")
        self.log_text.setReadOnly(True)

        # Log temizle butonu
        clear_log_btn = QPushButton("🗑️ Logları Temizle")
        clear_log_btn.setObjectName("secondaryButton")
        clear_log_btn.clicked.connect(self.clear_logs)
        clear_log_btn.setCursor(Qt.PointingHandCursor)

        log_layout.addWidget(self.log_text)
        log_layout.addWidget(clear_log_btn)
        log_group.setLayout(log_layout)

        layout.addWidget(stats_group)
        layout.addWidget(log_group, 1)

        panel.setLayout(layout)
        return panel

    def setup_style(self):
        """Gelişmiş stil ayarlarını uygula"""
        style = f"""
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FAFBFC, 
                stop:1 #F0F2F5);
        }}

        #controlPanel {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, 
                stop:1 #F8FAFC);
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 20px;
            margin: 10px;
        }}

        #logPanel {{
            background: transparent;
            padding: 10px;
        }}

        #pageTitle {{
            font-size: 28px;
            font-weight: 800;
            color: #1A202C;
            font-family: 'SF Pro Display', 'Inter', 'Segoe UI', sans-serif;
            margin: 10px 0px;
            text-shadow: 0px 1px 3px rgba(0, 0, 0, 0.1);
        }}

        #backButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #667eea, 
                stop:1 #764ba2);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 14px 24px;
            font-size: 15px;
            font-weight: 600;
            font-family: 'SF Pro Display', sans-serif;
        }}

        #backButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5a67d8, 
                stop:1 #6b46c1);
            transform: translateY(-1px);
        }}

        QGroupBox {{
            font-size: 15px;
            font-weight: 700;
            color: #2D3748;
            border: 2px solid #E2E8F0;
            border-radius: 12px;
            margin-top: 15px;
            padding-top: 15px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, 
                stop:1 #F7FAFC);
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 10px 0 10px;
            background-color: #FFFFFF;
            border-radius: 6px;
            color: #4A5568;
        }}

        #profileCountLabel, #currentProfileLabel {{
            font-size: 14px;
            font-weight: 600;
            color: #2D3748;
            padding: 15px 20px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #F7FAFC, 
                stop:1 #EDF2F7);
            border-radius: 12px;
            margin: 10px 0;
            border: 2px solid #E2E8F0;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }}

        #profileCountLabel:hover, #currentProfileLabel:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #FFFFFF, 
                stop:1 #F7FAFC);
            border-color: {self.colors['primary']};
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}

        #settingsCheckbox {{
            font-size: 14px;
            color: #2D3748;
            spacing: 10px;
            font-weight: 500;
        }}

        #settingsCheckbox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 9px;
            border: 2px solid #CBD5E0;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, 
                stop:1 #F7FAFC);
        }}

        #settingsCheckbox::indicator:checked {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4299E1, 
                stop:1 #3182CE);
            border-color: #3182CE;
        }}

        #settingsCheckbox::indicator:checked::after {{
            content: "✓";
            color: white;
            font-weight: bold;
        }}

        #settingsInput, #settingsSpinBox {{
            border: 2px solid #E2E8F0;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 14px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, 
                stop:1 #F7FAFC);
            color: #2D3748;
            font-weight: 500;
        }}

        #settingsInput:focus, #settingsSpinBox:focus {{
            border-color: #4299E1;
            outline: none;
            background: #FFFFFF;
        }}

        #settingsInput:disabled, #settingsSpinBox:disabled {{
            background: #F7FAFC;
            color: #A0AEC0;
            border-color: #E2E8F0;
        }}

        #ipDisplay {{
            font-size: 14px;
            color: #4299E1;
            font-weight: 600;
            margin-left: 10px;
            padding: 4px 8px;
            background: #EBF8FF;
            border-radius: 6px;
        }}

        #startButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #48BB78, 
                stop:1 #38A169);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 14px 28px;
            font-size: 15px;
            font-weight: 700;
            font-family: 'SF Pro Display', sans-serif;
        }}

        #startButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['success_hover']}, 
                stop:1 #1E8449);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
        }}

        #startButton:disabled {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #BDC3C7, 
                stop:1 #95A5A6);
            color: #7F8C8D;
            transform: none;
            box-shadow: none;
        }}

        #stopButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['error']}, 
                stop:1 #D32F2F);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 14px 28px;
            font-size: 15px;
            font-weight: 700;
            font-family: 'SF Pro Display', sans-serif;
        }}

        #stopButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['error_hover']}, 
                stop:1 #A93226);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(231, 76, 60, 0.4);
        }}

        #stopButton:disabled {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #BDC3C7, 
                stop:1 #95A5A6);
            color: #7F8C8D;
            transform: none;
            box-shadow: none;
        }}

        #secondaryButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['secondary']}, 
                stop:1 #357ABD);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 20px;
            font-size: 13px;
            font-weight: 600;
            font-family: 'SF Pro Display', sans-serif;
        }}

        #secondaryButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['secondary_hover']}, 
                stop:1 #2E689F);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(74, 144, 226, 0.3);
        }}
        
        #jsonButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #6366F1, 
                stop:1 #4F46E5);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 14px 28px;
            font-size: 15px;
            font-weight: 700;
            font-family: 'SF Pro Display', sans-serif;
        }}

        #jsonButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4F46E5, 
                stop:1 #4338CA);
            transform: translateY(-2px);
            box_shadow: 0 8px 25px rgba(79, 70, 229, 0.4);
        }}

        #statsText, #logText {{
            border: 2px solid #E2E8F0;
            border-radius: 12px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, 
                stop:1 #F7FAFC);
            font-family: 'SF Mono', 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 13px;
            color: #2D3748;
            padding: 12px;
            line-height: 1.5;
        }}

        #progressBar {{
            border: 2px solid #E2E8F0;
            border-radius: 12px;
            text-align: center;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #F7FAFC, 
                stop:1 #EDF2F7);
            color: #4A5568;
            font-weight: 600;
            height: 24px;
        }}

        #progressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #4299E1, 
                stop:1 #63B3ED);
            border-radius: 10px;
            margin: 2px;
        }}
        """

        self.setStyleSheet(style)

    def load_profiles(self):
        """Profilleri yükle"""
        self.profiles = []
        profiles_dir = "./Profiller"

        if os.path.exists(profiles_dir):
            try:
                for item in os.listdir(profiles_dir):
                    item_path = os.path.join(profiles_dir, item)
                    if os.path.isdir(item_path):
                        self.profiles.append(item)
            except Exception as e:
                self.show_error(f"Profiller yüklenirken hata: {str(e)}")

        self.profiles.sort()
        self.update_profile_list()

    def update_profile_list(self):
        """Profil sayısını güncelle"""
        self.profile_count_label.setText(f"📊 Yüklenen profil sayısı: {len(self.profiles)}")

    def toggle_proxy(self):
        """Proxy ayarlarını aç/kapat"""
        enabled = self.proxy_enabled.isChecked()
        self.proxy_entry.setEnabled(enabled)

    def toggle_ip_reset(self):
        """IP reset ayarlarını aç/kapat"""
        enabled = self.ip_reset_enabled.isChecked()
        self.ip_reset_entry.setEnabled(enabled)

    def start_process(self):
        """İşlemi başlat"""
        # Tüm profilleri al
        if not self.profiles:
            self.show_warning("Hiç profil bulunamadı!")
            return

        # ChromeDriver kontrol
        if not os.path.exists("chromedriver.exe"):
            self.show_error("chromedriver.exe bulunamadı!\nLütfen chromedriver.exe dosyasını ana dizine koyun.")
            return

        # Ayarları hazırla
        settings = {
            'min_duration': self.min_duration.value(),
            'max_duration': self.max_duration.value(),
            'proxy_enabled': self.proxy_enabled.isChecked(),
            'proxy_address': self.proxy_entry.text(),
            'ip_reset_enabled': self.ip_reset_enabled.isChecked(),
            'ip_reset_url': self.ip_reset_entry.text(),
            'browser_visible': self.browser_visible.isChecked()
        }

        # Worker thread başlat - tüm profilleri gönder
        self.worker_thread = CookieWorkerThread(self.profiles, settings)
        self.worker_thread.log_signal.connect(self.add_log)
        self.worker_thread.update_last_log_signal.connect(self.update_last_log)
        self.worker_thread.progress_signal.connect(self.update_progress)
        self.worker_thread.profile_stats_signal.connect(self.update_profile_stats)
        self.worker_thread.ip_signal.connect(self.set_browser_ip)
        self.worker_thread.current_profile_signal.connect(self.update_current_profile)
        self.worker_thread.finished_signal.connect(self.process_finished)

        # UI güncellemeleri
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.profiles))
        self.progress_bar.setValue(0)

        self.add_log(f"🚀 İşlem başlatıldı - {len(self.profiles)} profil")
        self.worker_thread.start()

    def stop_process(self):
        """İşlemi durdur"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.add_log("⏹️ İşlem durduruldu")

    def process_finished(self):
        """İşlem durduruldu"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.current_profile_label.setText("📂 Şu anda işlenen: Durduruldu")
        self.add_log("⏹️ İşlem durduruldu")

    def update_progress(self, current, total):
        """Progress bar güncelle"""
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"{current}/{total} profil")

    def update_profile_stats(self, profile, stats):
        """Profil istatistiklerini güncelle"""
        self.profile_stats[profile] = stats
        self.refresh_stats_display()

    def update_current_profile(self, profile):
        """Mevcut profili güncelle"""
        self.current_profile_label.setText(f"📂 Şu anda işlenen: {profile}")

    def refresh_stats_display(self):
        """İstatistik ekranını yenile"""
        stats_text = "📊 Profil İstatistikleri:\n\n"

        for profile, stats in self.profile_stats.items():
            stats_text += f"👤 {profile}\n"
            stats_text += f"  📊 Çalışma sayısı: {stats['count']}\n"
            stats_text += f"  ⏱️ Toplam süre: {stats['total_time']:.1f} sn\n\n"

        if not self.profile_stats:
            stats_text += "Henüz istatistik yok."

        self.stats_text.setText(stats_text)

    def add_log(self, message):
        """Log ekle"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        self.log_text.ensureCursorVisible()

    def update_last_log(self, message):
        """Son log satırını güncelle (kalan süre için)"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        # Son satırı güncelle
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        cursor.movePosition(cursor.StartOfLine, cursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(log_entry)
        self.log_text.ensureCursorVisible()

    def clear_logs(self):
        """Logları temizle"""
        self.log_text.clear()

    def start_ip_monitoring(self):
        """IP takibini başlat"""
        self.ip_timer.start(10000)  # 10 saniyede bir
        self.update_ip()

    def update_ip(self):
        """Normal IP'yi güncelle"""
        def get_ip():
            try:
                response = requests.get("https://api.ipify.org", timeout=5)
                return response.text.strip()
            except:
                return "Bağlantı hatası"

        thread = threading.Thread(target=lambda: self.set_computer_ip(get_ip()), daemon=True)
        thread.start()

    def set_computer_ip(self, ip):
        """Normal IP'yi ayarla"""
        self.current_ip = ip
        self.computer_ip_display.setText(self.current_ip)

    def set_browser_ip(self, ip):
        """Tarayıcı IP'sini ayarla"""
        self.browser_ip = ip
        self.browser_ip_display.setText(self.browser_ip)
        
    def open_json_extractor(self):
        """JSON Çıkarıcı penceresini aç"""
        self.json_window = JSONExtractorWindow(self.colors, self)
        self.json_window.show()

    def return_to_main(self):
        """Ana menüye dön"""
        # Worker thread'i durdur
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait()

        # IP timer'ı durdur
        self.ip_timer.stop()

        self.return_callback()

    def show_error(self, message):
        """Hata mesajı göster"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Hata")
        msg.setText(message)
        msg.exec_()

    def show_warning(self, message):
        """Uyarı mesajı göster"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Uyarı")
        msg.setText(message)
        msg.exec_()

    def show_info(self, message):
        """Bilgi mesajı göster"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Bilgi")
        msg.setText(message)
        msg.exec_()

class JSONExtractorWindow(QMessageBox):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.colors = colors
        self.selected_users = set()
        self.all_users = []

        self.setWindowTitle("📤 JSON Çıkartıcı")
        self.setIcon(QMessageBox.NoIcon)
        self.setStandardButtons(QMessageBox.NoButton)

        # Ana widget ve layout
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()

        self.init_ui()
        self.load_users()
        self.setup_style()

        self.main_widget.setLayout(self.main_layout)
        self.layout().addWidget(self.main_widget)

        # Pencere boyutu
        self.resize(600, 500)

    def init_ui(self):
        """UI elemanlarını oluştur"""
        # Başlık
        title_label = QLabel("📤 Kullanıcı Çerezlerini JSON Olarak Çıkart")
        title_label.setObjectName("jsonTitle")
        title_label.setAlignment(Qt.AlignCenter)

        # Arama kutusu
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Kullanıcı Ara:")
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Kullanıcı adı yazın...")
        self.search_input.textChanged.connect(self.filter_users)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)

        # Kontrol butonları
        control_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("✅ Tümünü Seç")
        self.select_all_btn.setObjectName("controlButton")
        self.select_all_btn.clicked.connect(self.select_all)

        self.clear_all_btn = QPushButton("❌ Seçimleri Kaldır")
        self.clear_all_btn.setObjectName("controlButton")
        self.clear_all_btn.clicked.connect(self.clear_all)

        self.selected_count_label = QLabel("Seçili: 0")
        self.selected_count_label.setObjectName("countLabel")

        control_layout.addWidget(self.select_all_btn)
        control_layout.addWidget(self.clear_all_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.selected_count_label)

        # Kullanıcı listesi
        self.user_list = QListWidget()
        self.user_list.setObjectName("userList")
        self.user_list.setMaximumHeight(250)

        # Alt butonlar
        button_layout = QHBoxLayout()

        self.extract_btn = QPushButton("📤 Seçilen Kullanıcıların JSON'unu Çıkart")
        self.extract_btn.setObjectName("extractButton")
        self.extract_btn.clicked.connect(self.extract_json)
        self.extract_btn.setEnabled(False)

        self.close_btn = QPushButton("❌ Kapat")
        self.close_btn.setObjectName("closeButton")
        self.close_btn.clicked.connect(self.close)

        button_layout.addWidget(self.extract_btn)
        button_layout.addWidget(self.close_btn)

        # Layout'a ekle
        self.main_layout.addWidget(title_label)
        self.main_layout.addLayout(search_layout)
        self.main_layout.addLayout(control_layout)
        self.main_layout.addWidget(self.user_list)
        self.main_layout.addLayout(button_layout)

    def setup_style(self):
        """Stilleri uygula"""
        style = f"""
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FAFBFC, 
                stop:1 #F0F2F5);
        }}

        #jsonTitle {{
            font-size: 20px;
            font-weight: 800;
            color: #1A202C;
            margin: 15px 0;
            padding: 10px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #8B5CF6, 
                stop:1 #7C3AED);
            color: white;
            border-radius: 12px;
        }}

        #searchInput {{
            border: 2px solid #E2E8F0;
            border-radius: 10px;
            padding: 8px 12px;
            font-size: 14px;
            background: white;
            color: #2D3748;
        }}

        #searchInput:focus {{
            border-color: #8B5CF6;
            outline: none;
        }}

        #controlButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4A90E2, 
                stop:1 #357ABD);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
            margin: 2px;
        }}

        #controlButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #357ABD, 
                stop:1 #2E689F);
        }}

        #countLabel {{
            font-size: 14px;
            font-weight: 600;
            color: #8B5CF6;
            padding: 8px 12px;
            background: #EDF2F7;
            border-radius: 8px;
        }}

        #userList {{
            border: 2px solid #E2E8F0;
            border-radius: 12px;
            background: white;
            alternate-background-color: #F7FAFC;
        }}

        #userList::item {{
            padding: 10px;
            border-bottom: 1px solid #E2E8F0;
        }}

        #userList::item:hover {{
            background: #EBF8FF;
        }}

        #userList::item:selected {{
            background: #E6FFFA;
        }}

        #extractButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #48BB78, 
                stop:1 #38A169);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 700;
        }}

        #extractButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #38A169, 
                stop:1 #2F855A);
        }}

        #extractButton:disabled {{
            background: #BDC3C7;
            color: #7F8C8D;
        }}

        #closeButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #E53E3E, 
                stop:1 #C53030);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 700;
        }}

        #closeButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #C53030, 
                stop:1 #9C2525);
        }}
        """

        self.setStyleSheet(style)

    def load_users(self):
        """Kullanıcıları yükle"""
        try:
            users = user_manager.get_all_users()
            self.all_users = [(user['kullanici_adi'], user.get('cerezler')) for user in users if user.get('cerezler')]
            self.refresh_user_list()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Kullanıcılar yüklenirken hata: {str(e)}")

    def refresh_user_list(self):
        """Kullanıcı listesini yenile"""
        self.user_list.clear()

        search_text = self.search_input.text().lower()

        for username, cookies in self.all_users:
            if search_text in username.lower():
                # Checkbox widget oluştur
                item = QListWidgetItem()
                checkbox = QCheckBox(f"👤 {username}")
                checkbox.setObjectName("userCheckbox")

                # Çerez sayısını göster
                if cookies:
                    import json
                    try:
                        cookie_dict = json.loads(cookies)
                        cookie_count = len(cookie_dict)
                        checkbox.setText(f"👤 {username} ({cookie_count} çerez)")
                    except:
                        checkbox.setText(f"👤 {username} (çerez formatı hatalı)")
                else:
                    checkbox.setText(f"👤 {username} (çerez yok)")

                # Checkbox durumunu kontrol et
                if username in self.selected_users:
                    checkbox.setChecked(True)

                # Checkbox değişikliğini dinle
                checkbox.stateChanged.connect(lambda state, user=username: self.on_user_selection_changed(user, state))

                self.user_list.addItem(item)
                self.user_list.setItemWidget(item, checkbox)

        self.update_selection_count()

    def filter_users(self):
        """Kullanıcıları filtrele"""
        self.refresh_user_list()

    def on_user_selection_changed(self, username, state):
        """Kullanıcı seçimi değiştiğinde"""
        if state == Qt.Checked:
            self.selected_users.add(username)
        else:
            self.selected_users.discard(username)

        self.update_selection_count()

    def select_all(self):
        """Tümünü seç"""
        search_text = self.search_input.text().lower()

        for username, _ in self.all_users:
            if search_text in username.lower():
                self.selected_users.add(username)

        self.refresh_user_list()

    def clear_all(self):
        """Seçimleri kaldır"""
        self.selected_users.clear()
        self.refresh_user_list()

    def update_selection_count(self):
        """Seçim sayısını güncelle"""
        count = len(self.selected_users)
        self.selected_count_label.setText(f"Seçili: {count}")
        self.extract_btn.setEnabled(count > 0)

    def extract_json(self):
        """Seçilen kullanıcıların JSON'larını çıkart"""
        if not self.selected_users:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir kullanıcı seçin!")
            return

        try:
            import json
            import os

            success_count = 0
            error_count = 0

            for username, cookies in self.all_users:
                if username in self.selected_users and cookies:
                    try:
                        # Çerezleri parse et
                        cookie_dict = json.loads(cookies)

                        # Dosya adını oluştur
                        filename = f"{username}.json"
                        filepath = os.path.join(".", filename)

                        # JSON dosyasını kaydet
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(cookie_dict, f, indent=2, ensure_ascii=False)

                        success_count += 1

                    except Exception as e:
                        print(f"❌ {username} JSON çıkartma hatası: {str(e)}")
                        error_count += 1

            # Sonuç mesajı
            if success_count > 0:
                message = f"✅ {success_count} kullanıcının JSON'u başarıyla çıkartıldı!"
                if error_count > 0:
                    message += f"\n⚠️ {error_count} kullanıcıda hata oluştu."
                QMessageBox.information(self, "Başarılı", message)
                self.close()
            else:
                QMessageBox.warning(self, "Hata", "Hiçbir JSON dosyası oluşturulamadı!")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"JSON çıkartma işleminde hata: {str(e)}")

    def close(self):
        """Pencereyi kapat"""
        self.accept()