from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QFileDialog, QMessageBox, QListWidget,
                             QTextEdit, QCheckBox, QLineEdit, QGroupBox, QSplitter)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import threading
import time
import random
import requests
import os
import uuid
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from database.user_manager import user_manager

class LoginWindow(QWidget):
    def __init__(self, colors, return_callback):
        super().__init__()
        self.colors = colors
        self.return_callback = return_callback
        self.users = []
        self.current_ip = "Kontrol ediliyor..."
        self.ip_thread_running = True

        # iPhone User-Agent listesi
        self.iphone_user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_11 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.7 Mobile/15E148 Safari/604.1",  # iPhone 8/8 Plus
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_11 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.7 Mobile/15E148 Safari/604.1",  # iPhone X
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",  # iPhone XR/XS/XS Max
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",  # iPhone 11 series
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",  # iPhone 12 series
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",  # iPhone 13 series
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",  # iPhone 14 series
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"   # iPhone 15 series
        ]

        # IP monitoring timer
        self.ip_timer = QTimer()
        self.ip_timer.timeout.connect(self.update_ip)

        self.init_ui()
        self.setup_style()
        self.start_ip_monitoring()

    def init_ui(self):
        """UI'yi başlat"""
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()

        # Geri butonu
        back_btn = QPushButton("← Ana Menüye Dön")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(self.return_to_main)
        back_btn.setCursor(Qt.PointingHandCursor)

        # Başlık
        title_label = QLabel("📥 Giriş Yapıcı")
        title_label.setObjectName("pageTitle")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Ana içerik - Splitter ile böl
        splitter = QSplitter(Qt.Horizontal)

        # Sol panel - Ayarlar
        left_panel = self.create_settings_panel()
        splitter.addWidget(left_panel)

        # Sağ panel - Kullanıcı listesi ve loglar
        right_panel = self.create_user_panel()
        splitter.addWidget(right_panel)

        # Splitter oranları
        splitter.setSizes([300, 600])

        # Alt panel - IP bilgisi
        bottom_panel = self.create_bottom_panel()

        # Ana layout'a ekle
        layout.addLayout(header_layout)
        layout.addWidget(splitter, 1)
        layout.addWidget(bottom_panel)

        self.setLayout(layout)

    def create_settings_panel(self):
        """Ayarlar panelini oluştur"""
        panel = QFrame()
        panel.setObjectName("settingsPanel")
        layout = QVBoxLayout()

        # Başlık
        title = QLabel("⚙️ Ayarlar")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Proxy ayarları
        proxy_group = QGroupBox("🌐 Proxy Ayarları")
        proxy_group.setObjectName("settingsGroup")
        proxy_layout = QVBoxLayout()

        self.proxy_enabled = QCheckBox("Proxy Kullanılsın mı?")
        self.proxy_enabled.setObjectName("settingsCheckbox")
        self.proxy_enabled.toggled.connect(self.toggle_proxy_fields)

        self.proxy_entry = QLineEdit()
        self.proxy_entry.setPlaceholderText("IP:Port (örn: 127.0.0.1:8080)")
        self.proxy_entry.setObjectName("settingsInput")
        self.proxy_entry.setEnabled(False)

        proxy_url_label = QLabel("IP Reset URL:")
        proxy_url_label.setObjectName("settingsLabel")

        self.reset_url_entry = QLineEdit()
        self.reset_url_entry.setPlaceholderText("http://example.com/reset")
        self.reset_url_entry.setObjectName("settingsInput")
        self.reset_url_entry.setEnabled(False)

        proxy_layout.addWidget(self.proxy_enabled)
        proxy_layout.addWidget(QLabel("Proxy IP:Port:"))
        proxy_layout.addWidget(self.proxy_entry)
        proxy_layout.addWidget(proxy_url_label)
        proxy_layout.addWidget(self.reset_url_entry)
        proxy_group.setLayout(proxy_layout)

        # Tarayıcı ayarları
        browser_group = QGroupBox("👀 Tarayıcı Ayarları")
        browser_group.setObjectName("settingsGroup")
        browser_layout = QVBoxLayout()

        self.browser_visible = QCheckBox("Tarayıcı Görünsün mü?")
        self.browser_visible.setObjectName("settingsCheckbox")
        self.browser_visible.setChecked(True)

        browser_layout.addWidget(self.browser_visible)
        browser_group.setLayout(browser_layout)

        # Başlat butonu
        start_btn = QPushButton("🚀 Giriş İşlemini Başlat")
        start_btn.setObjectName("primaryButton")
        start_btn.clicked.connect(self.start_login_process)
        start_btn.setCursor(Qt.PointingHandCursor)

        layout.addWidget(proxy_group)
        layout.addWidget(browser_group)
        layout.addStretch()
        layout.addWidget(start_btn)

        panel.setLayout(layout)
        return panel

    def create_user_panel(self):
        """Kullanıcı panelini oluştur"""
        panel = QFrame()
        panel.setObjectName("userPanel")
        layout = QVBoxLayout()

        # Kullanıcı listesi
        user_group = QGroupBox("📥 Kullanıcı Listesi")
        user_group.setObjectName("userGroup")
        user_layout = QVBoxLayout()

        # Liste yükle butonu
        load_btn = QPushButton("📁 Liste Yükle")
        load_btn.setObjectName("secondaryButton")
        load_btn.clicked.connect(self.load_user_list)
        load_btn.setCursor(Qt.PointingHandCursor)

        # Kullanıcı listesi
        self.user_list = QListWidget()
        self.user_list.setObjectName("userList")

        user_layout.addWidget(load_btn)
        user_layout.addWidget(self.user_list)
        user_group.setLayout(user_layout)

        # Log alanı
        log_group = QGroupBox("📝 İşlem Logları")
        log_group.setObjectName("logGroup")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setObjectName("logText")
        self.log_text.setReadOnly(True)

        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)

        # Splitter ile böl
        content_splitter = QSplitter(Qt.Vertical)
        content_splitter.addWidget(user_group)
        content_splitter.addWidget(log_group)
        content_splitter.setSizes([300, 200])

        layout.addWidget(content_splitter)
        panel.setLayout(layout)
        return panel

    def create_bottom_panel(self):
        """Alt paneli oluştur"""
        panel = QFrame()
        panel.setObjectName("bottomPanel")
        layout = QHBoxLayout()

        # Bilgisayar IP'si
        computer_ip_label = QLabel("💻 Bilgisayar IP:")
        computer_ip_label.setObjectName("ipLabel")

        self.computer_ip_display = QLabel(self.current_ip)
        self.computer_ip_display.setObjectName("computerIpDisplay")

        # Tarayıcı IP'si
        browser_ip_label = QLabel("🌐 Tarayıcı IP:")
        browser_ip_label.setObjectName("ipLabel")

        self.browser_ip_display = QLabel("Henüz kontrol edilmedi")
        self.browser_ip_display.setObjectName("browserIpDisplay")

        layout.addWidget(computer_ip_label)
        layout.addWidget(self.computer_ip_display)
        layout.addWidget(QLabel("  |  "))
        layout.addWidget(browser_ip_label)
        layout.addWidget(self.browser_ip_display)
        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def setup_style(self):
        """Stil ayarlarını uygula"""
        style = f"""
        #settingsPanel {{
            background-color: {self.colors['card_bg']};
            border: 1px solid {self.colors['border']};
            border-radius: 12px;
            margin: 5px;
            padding: 15px;
        }}

        #userPanel {{
            background-color: {self.colors['background']};
            margin: 5px;
        }}

        #bottomPanel {{
            background-color: {self.colors['background']};
            padding: 10px;
            border-top: 1px solid {self.colors['border']};
        }}

        #pageTitle {{
            font-size: 24px;
            font-weight: 700;
            color: {self.colors['text_primary']};
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
        }}

        #sectionTitle {{
            font-size: 18px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
            margin-bottom: 15px;
        }}

        #backButton {{
            background-color: {self.colors['text_secondary']};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 600;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
        }}

        #backButton:hover {{
            background-color: #555555;
        }}

        #primaryButton {{
            background-color: {self.colors['primary']};
            color: white;
            border: none;
            border-radius: 10px;
            padding: 15px 20px;
            font-size: 16px;
            font-weight: 600;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
        }}

        #primaryButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary_hover']}, 
                stop:1 #D14A1F);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(255, 107, 53, 0.4);
        }}

        #secondaryButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['secondary']}, 
                stop:1 #357ABD);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 600;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
        }}

        #secondaryButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['secondary_hover']}, 
                stop:1 #2E689F);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(74, 144, 226, 0.3);
        }}

        QGroupBox {{
            font-size: 14px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            background-color: {self.colors['card_bg']};
        }}

        #settingsCheckbox::indicator {{
            width: 20px;
            height: 20px;
            border-radius: 10px;
            border: 3px solid {self.colors['border']};
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, 
                stop:1 #F7FAFC);
        }}

        #settingsCheckbox::indicator:checked {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary']}, 
                stop:1 {self.colors['primary_end']});
            border-color: {self.colors['primary']};
            box-shadow: 0 0 10px rgba(255, 107, 53, 0.3);
        }}

        #settingsCheckbox::indicator:hover {{
            border-color: {self.colors['primary_hover']};
            box-shadow: 0 0 5px rgba(255, 107, 53, 0.2);
        }}

        #settingsInput {{
            border: 2px solid {self.colors['border']};
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 14px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, 
                stop:1 #F7FAFC);
            color: {self.colors['text_primary']};
            font-weight: 500;
        }}

        #settingsInput:focus {{
            border-color: {self.colors['primary']};
            outline: none;
            background: #FFFFFF;
            box-shadow: 0 0 15px rgba(255, 107, 53, 0.2);
        }}

        #settingsInput:hover {{
            border-color: {self.colors['border_hover']};
        }}

        #settingsInput:disabled {{
            background-color: {self.colors['background_alt']};
            color: {self.colors['text_secondary']};
        }}

        #settingsLabel {{
            font-size: 13px;
            color: {self.colors['text_secondary']};
            margin-top: 10px;
        }}

        #userList {{
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            background-color: white;
            alternate-background-color: {self.colors['card_bg']};
            selection-background-color: {self.colors['primary']};
            font-size: 13px;
            padding: 5px;
        }}

        #logText {{
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            background-color: {self.colors['card_bg']};
            font-family: 'SF Mono', 'Consolas', monospace;
            font-size: 12px;
            color: {self.colors['text_primary']};
            padding: 10px;
        }}

        #ipLabel {{
            font-size: 14px;
            font-weight: 600;
            color: {self.colors['text_primary']};
        }}

        #computerIpDisplay {{
            font-size: 14px;
            color: {self.colors['secondary']};
            font-weight: 500;
            margin-left: 10px;
        }}

        #browserIpDisplay {{
            font-size: 14px;
            color: {self.colors['primary']};
            font-weight: 500;
            margin-left: 10px;
        }}
        """

        self.setStyleSheet(style)

    def toggle_proxy_fields(self):
        """Proxy alanlarını etkinleştir/devre dışı bırak"""
        enabled = self.proxy_enabled.isChecked()
        self.proxy_entry.setEnabled(enabled)
        self.reset_url_entry.setEnabled(enabled)

    def load_user_list(self):
        """Kullanıcı listesini yükle"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Kullanıcı Listesi Seç",
            "",
            "Text files (*.txt);;All files (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()

                self.users = []
                self.user_list.clear()

                for line in lines:
                    line = line.strip()
                    if line:
                        try:
                            parts = line.strip().split(':')
                            if len(parts) >= 2:
                                user_data = {
                                    'username': parts[0],
                                    'password': parts[1]
                                }

                            # Format: kullaniciadi:sifre:yil:ay:proxy:port
                            if len(parts) >= 4:
                                try:
                                    user_data['year'] = int(parts[2]) if parts[2] else None
                                    user_data['month'] = int(parts[3]) if parts[3] else None
                                except ValueError:
                                    user_data['year'] = None
                                    user_data['month'] = None

                            if len(parts) >= 6:
                                user_data['proxy'] = parts[4] if parts[4] else None
                                try:
                                    user_data['proxy_port'] = int(parts[5]) if parts[5] else None
                                except ValueError:
                                    user_data['proxy_port'] = None

                            # Display text'i düzelt
                            if user_data.get('proxy') and user_data.get('proxy_port'):
                                display_text = f"{user_data['username']} (Proxy: {user_data['proxy']}:{user_data['proxy_port']})"
                            else:
                                display_text = f"{user_data['username']} (Proxy: Yok)"

                            self.users.append(user_data)
                            self.user_list.addItem(display_text)
                        except Exception as e:
                            print(f"Error processing line: {line} - {e}")

                self.log_message(f"✅ {len(self.users)} kullanıcı yüklendi.")

            except Exception as e:
                self.show_error(f"Dosya okuma hatası: {str(e)}")

    def start_login_process(self):
        """Giriş işlemini başlat"""
        if not self.users:
            self.show_warning("Önce kullanıcı listesi yükleyin!")
            return

        # Thread'de çalıştır
        thread = threading.Thread(target=self.login_process_thread, daemon=True)
        thread.start()

    def login_process_thread(self):
        """Giriş işlemi thread'i"""
        self.log_message("🚀 Giriş işlemi başlatılıyor...")

        for i, user in enumerate(self.users, 1):
            try:
                self.log_message(f"\n[{i}/{len(self.users)}] {user['username']} işleniyor...")

                # Profil kontrolü
                base_profile_path = f"./Profiller/{user['username']}"
                if os.path.exists(base_profile_path):
                    try:
                        files = os.listdir(base_profile_path)
                        important_files = [f for f in files if f in ['Default', 'Local State', 'Preferences']]
                        if len(important_files) >= 2:
                            self.log_message(f"⏭️ {user['username']} zaten giriş yapmış, atlanıyor.")
                            continue
                    except:
                        pass

                # Tarayıcı başlat
                driver = self.create_driver(user)
                if not driver:
                    continue

                # IP kontrolü yap
                browser_ip = self.check_browser_ip(driver)
                if not browser_ip:
                    self.log_message(f"❌ {user['username']} için tarayıcı IP'si alınamadı.")
                    driver.quit()
                    continue

                # Proxy kontrolü yap
                if not self.validate_proxy(browser_ip):
                    self.log_message(f"❌ {user['username']} için IP değişmemiş, işlem durduruldu.")
                    driver.quit()
                    continue

                # Giriş işlemi
                success = self.perform_login(driver, user)

                if success:
                    self.log_message(f"✅ {user['username']} başarıyla giriş yaptı.")

                    # Scroll simülasyonu
                    self.simulate_scroll(driver)

                    # Çerezleri MySQL'e kaydet (tarayıcı kapanmadan önce)
                    self.save_cookies_to_mysql(driver, user)

                    # Profili kalıcı olarak kaydet
                    self.save_profile_permanently(user['username'], driver)

                    # IP sıfırlama (eğer etkinse)
                    if self.proxy_enabled.isChecked() and self.reset_url_entry.text():
                        self.reset_ip()
                else:
                    self.log_message(f"❌ {user['username']} giriş başarısız.")
                    driver.quit()

                # Kullanıcılar arası bekleme
                if i < len(self.users):
                    wait_time = random.randint(3, 8)
                    self.log_message(f"⏳ Sonraki kullanıcı için {wait_time} saniye bekleniyor...")
                    time.sleep(wait_time)

            except Exception as e:
                self.log_message(f"❌ {user['username']} işlenirken hata: {str(e)}")

        self.log_message("\n🎉 Tüm kullanıcılar işlendi!")

    def create_driver(self, user):
        """Chrome driver oluştur"""
        try:
            options = Options()

            unique_id = str(uuid.uuid4())[:8]
            profile_path = os.path.abspath(f"./TempProfiller/{user['username']}_{unique_id}")

            os.makedirs(profile_path, exist_ok=True)

            options.add_argument(f"--user-data-dir={profile_path}")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-default-apps")

            # iPhone User-Agent atama
            existing_user_agent = user_manager.get_user_agent(user['username'])
            if existing_user_agent:
                # Mevcut user-agent'ı kullan
                selected_user_agent = existing_user_agent
                self.log_message(f"📱 {user['username']} için mevcut iPhone user-agent kullanılıyor")
            else:
                # Rastgele iPhone user-agent seç ve kaydet
                selected_user_agent = random.choice(self.iphone_user_agents)
                user_manager.update_user_agent(user['username'], selected_user_agent)
                self.log_message(f"📱 {user['username']} için yeni iPhone user-agent atandı ve kaydedildi")

            options.add_argument(f"--user-agent={selected_user_agent}")

            if not self.browser_visible.isChecked():
                options.add_argument("--headless=new")

            # Proxy ayarı
            proxy_to_use = None
            if user.get('proxy') and user.get('proxy_port'):
                proxy_to_use = f"{user['proxy']}:{user['proxy_port']}"
                self.log_message(f"🌐 Özel proxy kullanılıyor: {proxy_to_use}")
            elif self.proxy_enabled.isChecked() and self.proxy_entry.text():
                proxy_to_use = self.proxy_entry.text()
                self.log_message(f"🌐 Genel proxy kullanılıyor: {proxy_to_use}")

            if proxy_to_use:
                if proxy_to_use.count(':') >= 3:
                    self.log_message(f"⚠️ Kimlik doğrulamalı proxy tespit edildi, atlanıyor.")
                    return None
                options.add_argument(f"--proxy-server={proxy_to_use}")

            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            service = Service("chromedriver.exe")
            service.hide_command_prompt_window = True

            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            return driver

        except Exception as e:
            self.log_message(f"❌ Tarayıcı başlatma hatası: {str(e)}")
            return None

    def perform_login(self, driver, user):
        """Giriş işlemini gerçekleştir"""
        try:
            driver.get("https://x.com/i/flow/login?lang=tr")

            self.wait_and_type(driver, "//*[@autocomplete='username']", user['username'])
            self.wait_and_click(driver, "//button[.//span[text()='İleri']]")
            self.wait_and_type(driver, "//*[@autocomplete='current-password']", user['password'])
            self.wait_and_click(driver, "//button[.//span[text()='Giriş yap']]")

            time.sleep(5)
            if "home" in driver.current_url.lower() or "x.com" in driver.current_url:
                # Çerezleri almak için driver'ı geçici olarak sakla
                return True

            return False

        except Exception as e:
            self.log_message(f"❌ Giriş hatası: {str(e)}")
            return False

    def wait_and_type(self, driver, xpath, text):
        """Element bekle ve yazı yaz"""
        wait_time = random.randint(800, 3000) / 1000
        time.sleep(wait_time)

        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            element.clear()

            for char in text:
                element.send_keys(char)
                time.sleep(random.randint(50, 150) / 1000)

        except TimeoutException:
            element = driver.find_element(By.CSS_SELECTOR, "input")
            element.clear()
            element.send_keys(text)

    def wait_and_click(self, driver, xpath):
        """Element bekle ve tıkla"""
        wait_time = random.randint(1000, 3000) / 1000
        time.sleep(wait_time)

        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            element.click()
        except TimeoutException:
            element = driver.find_element(By.CSS_SELECTOR, "button[type='button']")
            element.click()

    def simulate_scroll(self, driver):
        """Organik scroll simülasyonu"""
        scroll_duration = random.randint(10, 20)
        self.log_message(f"📜 {scroll_duration} saniye scroll simülasyonu yapılıyor...")

        start_time = time.time()
        while time.time() - start_time < scroll_duration:
            scroll_amount = random.randint(300, 600)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.randint(1000, 3000) / 1000)

    def check_browser_ip(self, driver):
        """Tarayıcının IP adresini kontrol et"""
        try:
            self.log_message("🔍 Tarayıcı IP adresi kontrol ediliyor...")

            # IP kontrol sitesine git
            driver.get("https://api.ipify.org")
            time.sleep(3)

            # IP adresini al
            browser_ip = driver.find_element("tag name", "body").text.strip()

            self.log_message(f"🌐 Tarayıcı IP adresi: {browser_ip}")
            self.set_browser_ip(browser_ip)

            return browser_ip

        except Exception as e:
            self.log_message(f"❌ Tarayıcı IP kontrol hatası: {str(e)}")
            self.set_browser_ip("Kontrol edilemedi")
            return None

    def validate_proxy(self, browser_ip):
        """Proxy kontrolü yap"""
        try:
            # Proxy etkin değilse kontrol yapma
            if not self.proxy_enabled.isChecked():
                return True

            # Bilgisayar IP'si ile karşılaştır
            computer_ip = self.current_ip

            if browser_ip == computer_ip:
                self.log_message("⚠️ UYARI: Proxy etkin ama IP değişmemiş!")
                self.show_warning("IP adresi değişmemiş!\n\nProxy ayarlarınızı kontrol edin.\nİşlem durduruldu.")
                return False

            self.log_message("✅ Proxy doğrulama başarılı - IP değişmiş")
            return True

        except Exception as e:
            self.log_message(f"❌ Proxy doğrulama hatası: {str(e)}")
            return True  # Hata durumunda devam et

    def save_cookies_to_mysql(self, driver, user):
        """X.com çerezlerini MySQL'e kaydet"""
        try:
            self.log_message(f"🍪 {user['username']} için çerezler kaydediliyor...")

            # x.com'a git (eğer başka sayfadaysa)
            current_url = driver.current_url
            if "x.com" not in current_url:
                driver.get("https://x.com/")
                time.sleep(3)

            # Tüm çerezleri al
            cookies = driver.get_cookies()

            # İstenen çerezleri filtrele
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
                # Çerezleri ayrı bir fonksiyon ile kaydet
                cookie_success = user_manager.update_user_cookies(user['username'], cookie_dict)
                if cookie_success:
                    self.log_message(f"✅ {user['username']} çerezleri MySQL'e kaydedildi ({len(cookie_dict)} çerez)")
                else:
                    self.log_message(f"⚠️ {user['username']} çerezleri MySQL'e kaydedilemedi")
            else:
                self.log_message(f"⚠️ {user['username']} için çerez bulunamadı")

        except Exception as e:
            self.log_message(f"❌ {user['username']} çerez kaydetme hatası: {str(e)}")

    def reset_ip(self):
        """IP sıfırlama - HTTP isteği ile"""
        try:
            reset_url = self.reset_url_entry.text()
            if not reset_url:
                return

            self.log_message(f"🔄 IP sıfırlanıyor: {reset_url}")

            # HTTP isteği gönder
            response = requests.get(reset_url, timeout=10)

            if response.status_code == 200:
                self.log_message(f"✅ IP başarıyla sıfırlandı")
            else:
                self.log_message(f"⚠️ IP sıfırlama yanıtı: {response.status_code}")

            # IP'nin değişmesi için kısa bir bekleme
            time.sleep(3)

        except Exception as e:
            self.log_message(f"❌ IP sıfırlama hatası: {str(e)}")

    def save_profile_permanently(self, username, driver):
        """Profili kalıcı klasöre kaydet"""
        try:
            temp_profile = driver.capabilities['chrome']['userDataDir']
            permanent_profile = f"./Profiller/{username}"

            driver.quit()
            time.sleep(3)

            if os.path.exists(temp_profile) and not os.path.exists(permanent_profile):
                try:
                    shutil.copytree(temp_profile, permanent_profile, ignore_dangling_symlinks=True)
                    self.log_message(f"💾 {username} profili kalıcı olarak kaydedildi.")

                    try:
                        shutil.rmtree(temp_profile)
                        self.log_message(f"🧹 {username} geçici profili temizlendi.")
                    except:
                        pass

                except Exception as copy_error:
                    self.log_message(f"⚠️ Profil kopyalama hatası: {str(copy_error)}")

        except Exception as e:
            self.log_message(f"⚠️ Profil kaydetme hatası: {str(e)}")

        # MySQL'e kullanıcıyı kaydet
        try:
            user = next((u for u in self.users if u['username'] == username), None)
            if not user:
                self.log_message(f"⚠️ {username} kullanıcı bilgisi bulunamadı.")
                return

            existing_user_agent = user_manager.get_user_agent(username)
            success = user_manager.save_user(
                username,
                user['password'],
                None,  # cookie_dict yok
                user.get('year'),
                user.get('month'),
                user.get('proxy'),
                user.get('proxy_port'),
                existing_user_agent
            )

            if success:
                self.log_message(f"💾 {username} MySQL veritabanına kaydedildi.")

                # Hedef hesaplara da ekle (yıl ay bilgisi varsa)
                if user.get('year') or user.get('month'):
                    target_manager.add_target(username, user.get('year'), user.get('month'))
                    self.log_message(f"✅ {username} hedef hesaplara da eklendi")

            else:
                self.log_message(f"⚠️ {username} MySQL kaydı başarısız.")
        except Exception as e:
            self.log_message(f"⚠️ MySQL kayıt hatası: {str(e)}")

    def start_ip_monitoring(self):
        """IP takibini başlat"""
        self.ip_timer.start(10000)  # 10 saniyede bir
        self.update_ip()  # İlk güncelleme

    def update_ip(self):
        """IP'yi güncelle (QTimer ile thread-safe)"""
        def get_ip():
            try:
                response = requests.get("https://api.ipify.org", timeout=5)
                return response.text.strip()
            except:
                return "Bağlantı hatası"

        # Thread'de IP al
        thread = threading.Thread(target=lambda: self.set_ip(get_ip()), daemon=True)
        thread.start()

    def set_ip(self, ip):
        """Bilgisayar IP'sini set et"""
        self.current_ip = ip
        self.computer_ip_display.setText(self.current_ip)

    def set_browser_ip(self, ip):
        """Tarayıcı IP'sini set et"""
        self.browser_ip_display.setText(ip)

    def log_message(self, message):
        """Log mesajı ekle"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        # Thread-safe log ekleme
        self.log_text.append(log_entry)
        self.log_text.ensureCursorVisible()

    def return_to_main(self):
        """Ana menüye dön"""
        self.ip_thread_running = False
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