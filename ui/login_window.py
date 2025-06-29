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

        ip_label = QLabel("🌐 Şu anki IP:")
        ip_label.setObjectName("ipLabel")

        self.ip_display = QLabel(self.current_ip)
        self.ip_display.setObjectName("ipDisplay")

        layout.addWidget(ip_label)
        layout.addWidget(self.ip_display)
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
            background-color: {self.colors['primary_hover']};
        }}

        #secondaryButton {{
            background-color: {self.colors['secondary']};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 14px;
            font-weight: 600;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
        }}

        #secondaryButton:hover {{
            background-color: {self.colors['secondary_hover']};
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

        #settingsCheckbox {{
            font-size: 13px;
            color: {self.colors['text_primary']};
            spacing: 8px;
        }}

        #settingsCheckbox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 9px;
            border: 2px solid {self.colors['border']};
            background-color: white;
        }}

        #settingsCheckbox::indicator:checked {{
            background-color: {self.colors['primary']};
            border-color: {self.colors['primary']};
        }}

        #settingsInput {{
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            background-color: white;
            color: {self.colors['text_primary']};
        }}

        #settingsInput:focus {{
            border-color: {self.colors['primary']};
            outline: none;
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

        #ipDisplay {{
            font-size: 14px;
            color: {self.colors['secondary']};
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
                        parts = line.split(':')
                        if len(parts) >= 2:
                            username = parts[0]
                            password = parts[1]
                            proxy = None
                            proxy_port = None

                            if len(parts) >= 4:
                                proxy = parts[2]
                                proxy_port = parts[3]

                            user_data = {
                                'username': username,
                                'password': password,
                                'proxy': proxy,
                                'proxy_port': proxy_port,
                                'original_line': line
                            }

                            self.users.append(user_data)

                            # Display text'i düzelt
                            if proxy and proxy_port:
                                display_text = f"{username} (Proxy: {proxy}:{proxy_port})"
                            else:
                                display_text = f"{username} (Proxy: Yok)"

                            self.user_list.addItem(display_text)

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

                # Giriş işlemi
                success = self.perform_login(driver, user)

                if success:
                    self.log_message(f"✅ {user['username']} başarıyla giriş yaptı.")
                    self.simulate_scroll(driver)

                    if self.proxy_enabled.isChecked() and self.reset_url_entry.text():
                        self.reset_ip(driver)

                    self.save_profile_permanently(user['username'], driver)
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

            if not self.browser_visible.isChecked():
                options.add_argument("--headless=new")

            # Proxy ayarı
            proxy_to_use = None
            if user['proxy'] and user['proxy_port']:
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
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.log_message(f"🔄 {user['username']} için {attempt + 1}. deneme...")

                driver.get("https://x.com/i/flow/login?lang=tr")
                time.sleep(2)

                # Kullanıcı adı girişi
                if not self.wait_and_type(driver, "//*[@autocomplete='username']", user['username']):
                    raise Exception("Kullanıcı adı alanı bulunamadı")

                # İleri butonuna tıkla
                if not self.wait_and_click(driver, "//button[.//span[text()='İleri']]"):
                    raise Exception("İleri butonu bulunamadı")

                # Şifre girişi
                if not self.wait_and_type(driver, "//*[@autocomplete='current-password']", user['password']):
                    raise Exception("Şifre alanı bulunamadı")

                # Giriş yap butonuna tıkla
                if not self.wait_and_click(driver, "//button[.//span[text()='Giriş yap']]"):
                    raise Exception("Giriş yap butonu bulunamadı")

                # Giriş sonucunu kontrol et
                time.sleep(5)
                current_url = driver.current_url.lower()

                if "home" in current_url or "x.com" in current_url and "login" not in current_url:
                    return True
                elif "challenge" in current_url:
                    self.log_message(f"⚠️ {user['username']} güvenlik doğrulaması gerekiyor")
                    return False
                elif "suspended" in current_url:
                    self.log_message(f"❌ {user['username']} hesabı askıya alınmış")
                    return False
                elif "locked" in current_url:
                    self.log_message(f"❌ {user['username']} hesabı kilitlenmiş")
                    return False
                else:
                    raise Exception(f"Beklenmeyen sayfa: {current_url}")

            except Exception as e:
                error_msg = str(e)
                if attempt == max_retries - 1:
                    self.log_message(f"❌ {user['username']} giriş başarısız (son deneme): {error_msg}")
                    return False
                else:
                    self.log_message(f"⚠️ {user['username']} giriş hatası: {error_msg}")
                    time.sleep(3)  # Tekrar denemeden önce bekle

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

    def reset_ip(self, driver):
        """IP sıfırlama"""
        try:
            reset_url = self.reset_url_entry.text()
            self.log_message(f"🔄 IP sıfırlanıyor: {reset_url}")
            driver.get(reset_url)
            time.sleep(10)
        except Exception as e:
            self.log_message(f"❌ IP sıfırlama hatası: {str(e)}")

    def save_profile_permanently(self, username, driver):
        """Profili kalıcı klasöre kaydet"""
        temp_profile = None
        try:
            # ÖNEMLİ: Driver kapatılmadan ÖNCE cookies al!
            cookies = None
            try:
                cookies = driver.get_cookies()  # Driver açıkken cookie'leri al
                self.log_message(f"🍪 {username} için {len(cookies)} cookie alındı.")
            except Exception as e:
                self.log_message(f"⚠️ Cookie alma hatası: {str(e)}")

            # Driver bilgilerini al
            temp_profile = driver.capabilities['chrome']['userDataDir']
            permanent_profile = f"./Profiller/{username}"

            # Driver'ı güvenli şekilde kapat
            self.safe_quit_driver(driver, username)
            if hasattr(self, 'active_driver') and self.active_driver == driver:
                self.active_driver = None

            # Geçici profili kalıcı konuma kopyala
            if os.path.exists(temp_profile) and not os.path.exists(permanent_profile):
                import shutil
                try:
                    shutil.copytree(temp_profile, permanent_profile, ignore_dangling_symlinks=True)
                    self.log_message(f"💾 {username} profili kalıcı olarak kaydedildi.")

                    # Geçici profili temizle
                    try:
                        shutil.rmtree(temp_profile)
                        self.log_message(f"🧹 {username} geçici profili temizlendi.")
                    except:
                        pass

                except Exception as copy_error:
                    self.log_message(f"⚠️ Profil kopyalama hatası: {str(copy_error)}")
                    # Alternatif yöntem: sadece önemli dosyaları kopyala
                    self.copy_important_files(temp_profile, permanent_profile, username)

            # MySQL'e kullanıcıyı kaydet (cookies ile)
            try:
                password = next((u['password'] for u in self.users if u['username'] == username), '')
                success = user_manager.save_user(username, password, cookies)
                if success:
                    self.log_message(f"💾 {username} MySQL veritabanına kaydedildi.")
                else:
                    self.log_message(f"⚠️ {username} MySQL kaydı başarısız.")
            except Exception as e:
                self.log_message(f"⚠️ MySQL kayıt hatası: {str(e)}")

        except Exception as e:
            self.log_message(f"⚠️ Profil kaydetme hatası: {str(e)}")
            try:
                response = requests.get("https://api.ipify.org", timeout=5)
                return response.text.strip()
            except:
                return "Bağlantı hatası"

        # Thread'de IP al ama UI güncellemesini ana thread'de yap
        def get_ip_threaded():
            try:
                ip = get_ip()
                # Thread-safe UI güncelleme için QTimer kullan
                QTimer.singleShot(0, lambda: self.set_ip(ip))
            except Exception as e:
                QTimer.singleShot(0, lambda: self.set_ip("Bağlantı hatası"))

        thread = threading.Thread(target=get_ip_threaded, daemon=True)
        thread.start()

    def set_ip(self, ip):
        """IP'yi set et (Ana thread'de çalışır)"""
        self.current_ip = ip
        if hasattr(self, 'ip_display'):
            self.ip_display.setText(self.current_ip)

    def safe_quit_driver(self, driver, username):
        """Driver'ı güvenli şekilde kapat ve zombie process'leri temizle"""
        try:
            # Önce normal quit dene
            driver.quit()
            time.sleep(2)

            # Zombie process'leri kontrol et ve temizle
            try:
                import psutil
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                            if proc.info['cmdline']:
                                cmdline = ' '.join(proc.info['cmdline'])
                                if username in cmdline:
                                    proc.terminate()
                                    try:
                                        proc.wait(timeout=3)
                                        self.log_message(f"🧹 {username} zombie process temizlendi")
                                    except psutil.TimeoutExpired:
                                        proc.kill()
                                        self.log_message(f"🔥 {username} zorla kapatıldı")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except ImportError:
                # psutil yoksa sadece bekle
                time.sleep(1)
            except Exception as e:
                self.log_message(f"⚠️ Process temizleme hatası: {str(e)}")

        except Exception as e:
            self.log_message(f"❌ Driver kapatma hatası: {str(e)}")

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
