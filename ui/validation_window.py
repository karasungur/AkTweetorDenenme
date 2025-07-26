from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QMessageBox, QListWidget, QLineEdit,
                             QCheckBox, QGroupBox, QSplitter, QScrollArea, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import threading
import time
import requests
import os
import shutil
import random
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from database.user_manager import user_manager

class ValidationWindow(QWidget):
    def __init__(self, colors, return_callback):
        super().__init__()
        self.colors = colors
        self.return_callback = return_callback
        self.profiles = []
        self.filtered_profiles = []
        self.current_ip = "Kontrol ediliyor..."
        self.ip_thread_running = True
        self.drivers = []

        # Android cihaz listesini JSON dosyasından yükle
        self.android_devices = self.load_devices_from_file()

        # IP monitoring timer
        self.ip_timer = QTimer()
        self.ip_timer.timeout.connect(self.update_ip)

        self.init_ui()
        self.setup_style()
        self.load_profiles()
        self.start_ip_monitoring()

    def load_devices_from_file(self):
        """JSON dosyasından cihaz listesini yükle - Güvenli hata yönetimi ile"""
        import os
        import json

        # Varsayılan cihaz listesi (JSON dosyası yoksa veya hatalıysa)
        default_devices = [
            {
                'name': 'Samsung Galaxy S24',
                'user_agent': 'Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36',
                'device_metrics': {
                    'width': 360,
                    'height': 780,
                    'device_scale_factor': 3,
                    'mobile': True
                },
                'client_hints': {
                    'platform': 'Android',
                    'mobile': True
                }
            },
            {
                'name': 'Oppo Reno11 FS',
                'user_agent': 'Mozilla/5.0 (Linux; Android 13; CPH2363) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
                'device_metrics': {
                    'width': 412,
                    'height': 915,
                    'device_scale_factor': 2.625,
                    'mobile': True
                },
                'client_hints': {
                    'platform': 'Android',
                    'mobile': True
                }
            },
            {
                'name': 'Xiaomi Redmi Note 12',
                'user_agent': 'Mozilla/5.0 (Linux; Android 12; Redmi Note 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'device_metrics': {
                    'width': 393,
                    'height': 851,
                    'device_scale_factor': 2.75,
                    'mobile': True
                },
                'client_hints': {
                    'platform': 'Android',
                    'mobile': True
                }
            }
        ]

        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            devices_file = os.path.join(BASE_DIR, "config", "android_devices.json")

            # Config klasörünün izinlerini ayarla
            config_dir = os.path.dirname(devices_file)
            try:
                os.makedirs(config_dir, mode=0o777, exist_ok=True)
                os.chmod(config_dir, 0o777)
            except Exception as perm_error:
                print(f"⚠️ Config klasör izin hatası: {perm_error}")

            if os.path.exists(devices_file):
                try:
                    # Dosya izinlerini ayarla
                    os.chmod(devices_file, 0o666)

                    with open(devices_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # JSON yapısını kontrol et
                    if isinstance(data, dict) and 'devices' in data:
                        devices = data['devices']
                        if isinstance(devices, list) and len(devices) > 0:
                            # Her cihazın gerekli alanlarını kontrol et
                            valid_devices = []
                            for device in devices:
                                if (isinstance(device, dict) and 
                                    'name' in device and 
                                    'user_agent' in device and 
                                    'device_metrics' in device):
                                    valid_devices.append(device)

                            if valid_devices:
                                print(f"✅ {len(valid_devices)} geçerli cihaz JSON dosyasından yüklendi")
                                return valid_devices

                    print("⚠️ JSON dosyası geçersiz format içeriyor, varsayılan liste kullanılacak")

                except (json.JSONDecodeError, UnicodeDecodeError) as json_error:
                    print(f"⚠️ JSON okuma hatası: {json_error}, varsayılan liste kullanılacak")
                except Exception as file_error:
                    print(f"⚠️ Dosya okuma hatası: {file_error}, varsayılan liste kullanılacak")

            # Dosya yoksa veya hatalıysa yeni dosya oluştur
            try:
                device_data = {"devices": default_devices}
                with open(devices_file, 'w', encoding='utf-8') as f:
                    json.dump(device_data, f, indent=2, ensure_ascii=False)
                os.chmod(devices_file, 0o666)
                print(f"ℹ️ Yeni cihaz dosyası oluşturuldu: {devices_file}")
            except Exception as create_error:
                print(f"⚠️ Dosya oluşturma hatası: {create_error}")

            return default_devices

        except Exception as e:
            print(f"❌ Kritik cihaz dosyası hatası: {e}, varsayılan liste kullanılıyor")
            return default_devices

    def create_driver(self, profile_name):
        """Android cihaz özellikleri ile Chrome driver oluştur"""
        try:
            options = Options()

            # Profil yolu - Replit uyumlu izinlerle
            profile_path = os.path.abspath(f"./Profiller/{profile_name}")
            if not os.path.exists(profile_path):
                return None

            # Profil dizini izinlerini en üst düzeye çıkar
            try:
                os.chmod(profile_path, 0o777)
                # Alt dizinlerin izinlerini de en üst düzeye çıkar
                for root, dirs, files in os.walk(profile_path):
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        try:
                            os.chmod(dir_path, 0o777)
                        except Exception:
                            pass
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        try:
                            os.chmod(file_path, 0o666)
                        except Exception:
                            pass
            except Exception as perm_error:
                print(f"⚠️ Profil dizini izin ayarlama hatası: {perm_error}")

            # Kapsamlı temp dosya izin ayarları
            temp_dirs = [
                '/tmp', '/var/tmp', './temp', './Profiller/.temp', 
                './cache', './logs', './downloads', './uploads',
                os.path.expanduser('~/tmp'), os.path.expanduser('~/.cache'),
                os.environ.get('TMPDIR', '/tmp'), os.environ.get('TEMP', '/tmp')
            ]

            for temp_dir in temp_dirs:
                if temp_dir:
                    try:
                        # Klasör yoksa oluştur
                        os.makedirs(temp_dir, mode=0o777, exist_ok=True)
                        # İzinleri ayarla
                        os.chmod(temp_dir, 0o777)

                        # İçindeki dosyaların izinlerini de ayarla
                        if os.path.exists(temp_dir):
                            for root, dirs, files in os.walk(temp_dir):
                                for dir_name in dirs:
                                    try:
                                        os.chmod(os.path.join(root, dir_name), 0o777)
                                    except Exception:
                                        pass
                                for file_name in files:
                                    try:
                                        os.chmod(os.path.join(root, file_name), 0o666)
                                    except Exception:
                                        pass
                    except Exception as temp_error:
                        print(f"⚠️ Temp dizin izin ayarlama hatası {temp_dir}: {temp_error}")

            # Chrome cache ve data klasörleri için özel izinler
            chrome_cache_dirs = [
                os.path.join(profile_path, 'Default', 'Cache'),
                os.path.join(profile_path, 'Default', 'Code Cache'),
                os.path.join(profile_path, 'Default', 'GPUCache'),
                os.path.join(profile_path, 'ShaderCache'),
                os.path.join(profile_path, 'Default', 'IndexedDB'),
                os.path.join(profile_path, 'Default', 'Local Storage'),
                os.path.join(profile_path, 'Default', 'Session Storage')
            ]

            for cache_dir in chrome_cache_dirs:
                try:
                    os.makedirs(cache_dir, mode=0o777, exist_ok=True)
                    os.chmod(cache_dir, 0o777)
                except Exception:
                    pass

            options.add_argument(f"--user-data-dir={profile_path}")

            # Cihaz özelliklerini MySQL'den al
            device_specs = user_manager.get_device_specs(profile_name)
            user_agent = user_manager.get_user_agent(profile_name)

            if device_specs and user_agent:
                # Mevcut cihaz özelliklerini kullan
                selected_device = {
                    'name': device_specs['device_name'],
                    'user_agent': user_agent,
                    'screen_width': device_specs['screen_width'],
                    'screen_height': device_specs['screen_height'],
                    'device_pixel_ratio': device_specs['device_pixel_ratio']
                }

                # Mobil cihaz simülasyonu
                mobile_emulation = {
                    "deviceMetrics": {
                        "width": device_specs['screen_width'],
                        "height": device_specs['screen_height'],
                        "pixelRatio": device_specs['device_pixel_ratio'],
                        "mobile": True,
                        "fitWindow": False,
                        "textAutosizing": False
                    },
                    "userAgent": user_agent
                }
                options.add_experimental_option("mobileEmulation", mobile_emulation)

                # Chrome pencere boyutunu mobil emülasyon boyutuyla eşitle
                options.add_argument(f"--window-size={device_specs['screen_width']},{device_specs['screen_height']}")

                self.log_message(f"📱 {profile_name} için mevcut cihaz kullanılıyor: {device_specs['device_name']}")
                self.log_message(f"🔧 Ekran: {device_specs['screen_width']}x{device_specs['screen_height']}, DPR: {device_specs['device_pixel_ratio']}")

                selected_device = {
                    'user_agent': user_agent,
                    'screen_width': device_specs['screen_width'],
                    'screen_height': device_specs['screen_height']
                }
            else:
                # Yeni cihaz seç ve kaydet
                selected_device = random.choice(self.android_devices)
                user_manager.update_user_agent(profile_name, selected_device['user_agent'])
                user_manager.update_device_specs(profile_name, selected_device)

                # Mobil cihaz simülasyonu
                mobile_emulation = {
                    "deviceMetrics": {
                        "width": selected_device['device_metrics']['width'],
                        "height": selected_device['device_metrics']['height'],
                        "pixelRatio": selected_device['device_metrics']['device_scale_factor'],
                        "mobile": True,
                        "fitWindow": False,
                        "textAutosizing": False
                    },
                    "userAgent": selected_device['user_agent']
                }
                options.add_experimental_option("mobileEmulation", mobile_emulation)

                # Chrome pencere boyutunu mobil emülasyon boyutuyla eşitle
                options.add_argument(f"--window-size={selected_device['device_metrics']['width']},{selected_device['device_metrics']['height']}")

                self.log_message(f"📱 {profile_name} için yeni cihaz atandı: {selected_device['name']}")
                self.log_message(f"🔧 Ekran: {selected_device['device_metrics']['width']}x{selected_device['device_metrics']['height']}, DPR: {selected_device['device_metrics']['device_scale_factor']}")

                options.add_argument(f"--user-agent={selected_device['user_agent']}")

                # 🔒 Anti-Bot Gelişmiş Ayarlar
                options.add_argument("--lang=tr-TR,tr")
                options.add_argument("--accept-lang=tr-TR,tr;q=0.9,en;q=0.8")

                # Zaman dilimi ayarı
                options.add_argument("--timezone=Europe/Istanbul")

                # Canvas fingerprint koruması
                options.add_argument("--disable-canvas-aa")
                options.add_argument("--disable-2d-canvas-clip-aa")

                # WebGL fingerprint koruması  
                options.add_argument("--disable-gl-drawing-for-tests")
                options.add_argument("--disable-accelerated-2d-canvas")

            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            # Resimleri etkinleştir (X.com için gerekli)
            options.add_argument("--enable-javascript")
            options.add_argument("--enable-features=NetworkService")
            options.add_argument("--disable-site-isolation-trials")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            service = Service("chromedriver.exe")
            service.hide_command_prompt_window = True

            driver = webdriver.Chrome(service=service, options=options)

            # 🔒 Minimal Anti-Bot (Sayfa yüklenmesini engellemeyecek)
            minimal_script = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            """

            driver.execute_script(minimal_script)

            return driver

        except Exception as e:
            print(f"❌ Driver oluşturma hatası: {str(e)}")
            return None

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
        title_label = QLabel("🔍 Giriş Doğrulama/Silme")
        title_label.setObjectName("pageTitle")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Arama ve kontrol paneli
        control_panel = self.create_control_panel()

        # Ana içerik
        content_panel = self.create_content_panel()

        # Alt panel - IP ve proxy ayarları
        bottom_panel = self.create_bottom_panel()

        # Ana layout'a ekle
        layout.addLayout(header_layout)
        layout.addWidget(control_panel)
        layout.addWidget(content_panel, 1)
        layout.addWidget(bottom_panel)

        self.setLayout(layout)

    def create_control_panel(self):
        """Kontrol panelini oluştur"""
        panel = QFrame()
        panel.setObjectName("controlPanel")
        layout = QVBoxLayout()

        # Arama kutusu
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Arama:")
        search_label.setObjectName("searchLabel")

        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Profil adı ara...")
        self.search_entry.setObjectName("searchInput")
        self.search_entry.textChanged.connect(self.filter_profiles)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_entry)
        search_layout.addStretch()

        # Kontrol butonları
        button_layout = QHBoxLayout()

        select_all_btn = QPushButton("✅ Tümünü Seç")
        select_all_btn.setObjectName("controlButton")
        select_all_btn.clicked.connect(self.select_all)
        select_all_btn.setCursor(Qt.PointingHandCursor)

        deselect_all_btn = QPushButton("❌ Seçimi Kaldır")
        deselect_all_btn.setObjectName("controlButton")
        deselect_all_btn.clicked.connect(self.deselect_all)
        deselect_all_btn.setCursor(Qt.PointingHandCursor)

        delete_btn = QPushButton("🗑️ Sil")
        delete_btn.setObjectName("deleteButton")
        delete_btn.clicked.connect(self.delete_selected)
        delete_btn.setCursor(Qt.PointingHandCursor)

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setObjectName("primaryButton")
        refresh_btn.clicked.connect(self.load_profiles)
        refresh_btn.setCursor(Qt.PointingHandCursor)

        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(deselect_all_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)

        layout.addLayout(search_layout)
        layout.addLayout(button_layout)

        panel.setLayout(layout)
        return panel

    def create_content_panel(self):
        """İçerik panelini oluştur"""
        panel = QFrame()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout()

        # Profil listesi
        profiles_group = QGroupBox("📁 Profil Listesi")
        profiles_group.setObjectName("profilesGroup")
        profiles_layout = QVBoxLayout()

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("profileScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Profil container
        self.profile_container = QWidget()
        self.profile_layout = QVBoxLayout()
        self.profile_layout.setSpacing(5)
        self.profile_container.setLayout(self.profile_layout)

        self.scroll_area.setWidget(self.profile_container)

        profiles_layout.addWidget(self.scroll_area)
        profiles_group.setLayout(profiles_layout)

        layout.addWidget(profiles_group)
        panel.setLayout(layout)
        return panel

    def create_bottom_panel(self):
        """Alt paneli oluştur"""
        panel = QFrame()
        panel.setObjectName("bottomPanel")
        layout = QHBoxLayout()

        # Proxy ayarları
        proxy_group = QGroupBox("🌐 Proxy Ayarları")
        proxy_group.setObjectName("proxyGroup")
        proxy_layout = QVBoxLayout()

        self.proxy_enabled = QCheckBox("Proxy kullanılsın mı?")
        self.proxy_enabled.setObjectName("settingsCheckbox")
        self.proxy_enabled.toggled.connect(self.toggle_proxy_fields)

        self.proxy_entry = QLineEdit()
        self.proxy_entry.setPlaceholderText("IP:Port")
        self.proxy_entry.setObjectName("settingsInput")
        self.proxy_entry.setEnabled(False)

        reset_url_label = QLabel("IP Reset URL:")
        reset_url_label.setObjectName("settingsLabel")

        self.reset_url_entry = QLineEdit()
        self.reset_url_entry.setPlaceholderText("http://example.com/reset")
        self.reset_url_entry.setObjectName("settingsInput")
        self.reset_url_entry.setEnabled(False)

        proxy_layout.addWidget(self.proxy_enabled)
        proxy_layout.addWidget(self.proxy_entry)
        proxy_layout.addWidget(reset_url_label)
        proxy_layout.addWidget(self.reset_url_entry)
        proxy_group.setLayout(proxy_layout)

        # IP bilgisi
        ip_group = QGroupBox("🌐 IP Bilgisi")
        ip_group.setObjectName("ipGroup")
        ip_layout = QVBoxLayout()

        # Bilgisayar IP'si
        computer_ip_layout = QHBoxLayout()
        computer_ip_label = QLabel("💻 Bilgisayar IP:")
        computer_ip_label.setObjectName("ipLabel")

        self.computer_ip_display = QLabel(self.current_ip)
        self.computer_ip_display.setObjectName("computerIpDisplay")

        computer_ip_layout.addWidget(computer_ip_label)
        computer_ip_layout.addWidget(self.computer_ip_display)
        computer_ip_layout.addStretch()

        # Tarayıcı IP'si
        browser_ip_layout = QHBoxLayout()
        browser_ip_label = QLabel("🌐 Tarayıcı IP:")
        browser_ip_label.setObjectName("ipLabel")

        self.browser_ip_display = QLabel("Henüz kontrol edilmedi")
        self.browser_ip_display.setObjectName("browserIpDisplay")

        browser_ip_layout.addWidget(browser_ip_label)
        browser_ip_layout.addWidget(self.browser_ip_display)
        browser_ip_layout.addStretch()

        # IP değiştir butonu
        ip_change_btn = QPushButton("🔄 IP Değiştir")
        ip_change_btn.setObjectName("secondaryButton")
        ip_change_btn.clicked.connect(self.change_ip)
        ip_change_btn.setCursor(Qt.PointingHandCursor)

        ip_layout.addLayout(computer_ip_layout)
        ip_layout.addLayout(browser_ip_layout)
        ip_layout.addWidget(ip_change_btn)
        ip_group.setLayout(ip_layout)

        layout.addWidget(proxy_group)
        layout.addWidget(ip_group)

        panel.setLayout(layout)
        return panel

    def setup_style(self):
        """Stil ayarlarını uygula"""
        style = f"""
        #controlPanel {{
            background-color: {self.colors['card_bg']};
            border: 1px solid {self.colors['border']};
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
        }}

        #contentPanel {{
            background-color: {self.colors['background']};
        }}

        #bottomPanel {{
            background-color: {self.colors['background']};
            padding: 10px 0px;
            border-top: 1px solid {self.colors['border']};
        }}

        #pageTitle {{
            font-size: 24px;
            font-weight: 700;
            color: {self.colors['text_primary']};
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
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

        #searchLabel {{
            font-size: 14px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            margin-right: 10px;
        }}

        #searchInput {{
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
            background-color: white;
            color: {self.colors['text_primary']};
            min-width: 250px;
        }}

        #searchInput:focus {{
            border-color: {self.colors['primary']};
            outline: none;
        }}

        #controlButton {{
            background-color: {self.colors['secondary']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
            margin-right: 10px;
        }}

        #controlButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['secondary_hover']}, 
                stop:1 #2E689F);
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
        }}

        #deleteButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['error']}, 
                stop:1 #D32F2F);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 600;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
            margin-right: 10px;
        }}

        #deleteButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['error_hover']}, 
                stop:1 #A93226);
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(231, 76, 60, 0.4);
        }}

        #primaryButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary']}, 
                stop:1 {self.colors['primary_end']});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 600;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
        }}

        #primaryButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary_hover']}, 
                stop:1 #E67E22);
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(255, 107, 53, 0.4);
        }}

        #secondaryButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['secondary']}, 
                stop:1 #357ABD);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 12px;
            font-weight: 600;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
        }}

        #secondaryButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['secondary_hover']}, 
                stop:1 #2E689F);
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
        }}

        #profileScrollArea {{
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            background-color: white;
        }}

        #profileItem {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, 
                stop:1 #F8FAFC);
            border: 2px solid {self.colors['border']};
            border-radius: 12px;
            padding: 15px;
            margin: 5px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }}

        #profileItem:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, 
                stop:1 #EDF2F7);
            border-color: {self.colors['primary']};
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
        }}

        #profileCheckbox {{
            font-size: 14px;
            color: {self.colors['text_primary']};
            font-weight: 500;
        }}

        #profileCheckbox::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 8px;
            border: 2px solid {self.colors['border']};
            background-color: white;
        }}

        #profileCheckbox::indicator:checked {{
            background-color: {self.colors['primary']};
            border-color: {self.colors['primary']};
        }}

        #openButton {{
            background-color: {self.colors['secondary']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 600;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
        }}

        #openButton:hover {{
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
            background-color: {self.colors['background']};
        }}

        #settingsCheckbox {{
            font-size: 13px;
            color: {self.colors['text_primary']};
            spacing: 8px;
        }}

        #settingsCheckbox::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 8px;
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

        ```python
        #settingsInput:focus {{
            border-color: {self.colors['primary']};
            outline: none;
        }}

        #settingsInput:disabled {{
            background-color: {self.colors['background_alt']};
            color: {self.colors['text_secondary']};
        }}

        #settingsLabel {{
            font-size: 12px;
            color: {self.colors['text_secondary']};
            margin-top: 8px;
        }}

        #ipLabel {{
            font-size: 13px;
            font-weight: 600;
            color: {self.colors['text_primary']};
        }}

        #computerIpDisplay {{
            font-size: 13px;
            color: {self.colors['secondary']};
            font-weight: 500;
            margin-left: 10px;
        }}

        #browserIpDisplay {{
            font-size: 13px;
            color: {self.colors['primary']};
            font-weight: 500;
            margin-left: 10px;
        }}
        """

        self.setStyleSheet(style)

    def load_profiles(self):
        """Profilleri yükle"""
        self.profiles = []
        profiles_dir = "./Profiller"

        # Profiller klasörü yoksa oluştur ve izinleri ayarla
        if not os.path.exists(profiles_dir):
            try:
                os.makedirs(profiles_dir, mode=0o777, exist_ok=True)
                os.chmod(profiles_dir, 0o777)
                print(f"✅ Profiller klasörü oluşturuldu: {profiles_dir}")
            except Exception as e:
                self.show_error(f"Profiller klasörü oluşturulamadı: {str(e)}")
                return

        # Tüm proje klasörlerinin izinlerini ayarla
        project_dirs = [
            './config', './database', './ui', './utils', './assets',
            './logs', './cache', './temp', './downloads', './uploads'
        ]

        for project_dir in project_dirs:
            try:
                os.makedirs(project_dir, mode=0o777, exist_ok=True)
                os.chmod(project_dir, 0o777)

                # İçindeki dosyaların izinlerini de ayarla
                if os.path.exists(project_dir):
                    for root, dirs, files in os.walk(project_dir):
                        for dir_name in dirs:
                            try:
                                os.chmod(os.path.join(root, dir_name), 0o777)
                            except Exception:
                                pass
                        for file_name in files:
                            try:
                                os.chmod(os.path.join(root, file_name), 0o666)
                            except Exception:
                                pass
            except Exception as project_error:
                print(f"⚠️ Proje klasör izin hatası {project_dir}: {project_error}")

        # Ana dosyaların izinlerini ayarla
        main_files = [
            'main.py', 'requirements.txt', 'kategoriler.json',
            '.replit', 'replit.nix'
        ]

        for main_file in main_files:
            try:
                if os.path.exists(main_file):
                    os.chmod(main_file, 0o666)
            except Exception:
                pass

        if os.path.exists(profiles_dir):
            try:
                # Klasör izinlerini ayarla
                os.chmod(profiles_dir, 0o777)

                for item in os.listdir(profiles_dir):
                    item_path = os.path.join(profiles_dir, item)
                    if os.path.isdir(item_path):
                        self.profiles.append(item)
                        # Her profil klasörünün izinlerini ayarla
                        try:
                            os.chmod(item_path, 0o777)
                        except Exception:
                            pass
            except Exception as e:
                self.show_error(f"Profiller yüklenirken hata: {str(e)}")

        self.profiles.sort()
        self.filtered_profiles = self.profiles.copy()
        self.update_profile_display()

    def filter_profiles(self):
        """Profilleri filtrele"""
        search_text = self.search_entry.text().lower()
        if search_text:
            self.filtered_profiles = [p for p in self.profiles if search_text in p.lower()]
        else:
            self.filtered_profiles = self.profiles.copy()

        self.update_profile_display()

    def update_profile_display(self):
        """Profil görünümünü güncelle"""
        # Mevcut widget'ları temizle
        for i in reversed(range(self.profile_layout.count())):
            child = self.profile_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        self.profile_checkboxes = {}

        if not self.filtered_profiles:
            no_profile_label = QLabel("Profil bulunamadı")
            no_profile_label.setAlignment(Qt.AlignCenter)
            no_profile_label.setStyleSheet(f"""
                font-size: 16px;
                color: {self.colors['text_secondary']};
                padding: 40px;
            """)
            self.profile_layout.addWidget(no_profile_label)
            return

        for profile in self.filtered_profiles:
            profile_frame = QFrame()
            profile_frame.setObjectName("profileItem")
            profile_layout = QVBoxLayout()  # Dikey layout kullan

            # Üst kısım - Checkbox ve buton
            top_layout = QHBoxLayout()

            # Checkbox
            checkbox = QCheckBox(f"👤 {profile}")
            checkbox.setObjectName("profileCheckbox")
            self.profile_checkboxes[profile] = checkbox

            # Tarayıcı aç butonu
            open_btn = QPushButton("🌐 Aç")
            open_btn.setObjectName("openButton")
            open_btn.clicked.connect(lambda checked, p=profile: self.open_browser(p))
            open_btn.setCursor(Qt.PointingHandCursor)

            top_layout.addWidget(checkbox)
            top_layout.addStretch()
            top_layout.addWidget(open_btn)

            # Alt kısım - MySQL bilgileri
            mysql_info_layout = QHBoxLayout()

            # MySQL'den kullanıcı bilgilerini al
            user_data = user_manager.get_user(profile)
            if user_data:
                # MySQL'de var
                status_color = "#388E3C" if user_data.get('durum') == 'aktif' else "#FF9800"
                mysql_status = QLabel(f"💾 MySQL: {user_data.get('durum', 'Bilinmiyor')}")
                mysql_status.setStyleSheet(f"color: {status_color}; font-size: 11px; font-weight: 500;")

                last_login = user_data.get('son_giris')
                if last_login:
                    login_info = QLabel(f"🕒 Son giriş: {last_login.strftime('%d.%m.%Y %H:%M') if last_login else 'Bilinmiyor'}")
                    login_info.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 11px;")
                else:
                    login_info = QLabel("🕒 Son giriş: Bilinmiyor")
                    login_info.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 11px;")

                mysql_info_layout.addWidget(mysql_status)
                mysql_info_layout.addWidget(login_info)
            else:
                # MySQL'de yok
                mysql_status = QLabel("⚠️ MySQL: Kayıt yok")
                mysql_status.setStyleSheet(f"color: {self.colors['error']}; font-size: 11px; font-weight: 500;")
                mysql_info_layout.addWidget(mysql_status)

            mysql_info_layout.addStretch()

            # Layout'ları birleştir
            profile_layout.addLayout(top_layout)
            profile_layout.addLayout(mysql_info_layout)
            profile_layout.setSpacing(5)

            profile_frame.setLayout(profile_layout)
            self.profile_layout.addWidget(profile_frame)

        # Stretch ekle
        self.profile_layout.addStretch()

    def select_all(self):
        """Tümünü seç"""
        for checkbox in self.profile_checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all(self):
        """Seçimi kaldır"""
        for checkbox in self.profile_checkboxes.values():
            checkbox.setChecked(False)

    def delete_selected(self):
        """Seçili profilleri sil"""
        selected_profiles = [profile for profile, checkbox in self.profile_checkboxes.items() 
                           if checkbox.isChecked()]

        if not selected_profiles:
            self.show_warning("Silinecek profil seçilmedi!")
            return

        # Onay iste
        reply = QMessageBox.question(
            self,
            "Onay",
            f"{len(selected_profiles)} profil silinecek. Emin misiniz?\n\n" +
            "⚠️ Bu işlem hem profil klasörünü hem de MySQL veritabanındaki kayıtları silecek!\n\n" +
            "\n".join(selected_profiles[:5]) +
            ("..." if len(selected_profiles) > 5 else ""),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            deleted_count = 0
            mysql_deleted_count = 0

            for profile in selected_profiles:
                try:
                    # 1. Profil klasörünü sil
                    profile_path = os.path.join("./Profiller", profile)
                    if os.path.exists(profile_path):
                        shutil.rmtree(profile_path)
                        deleted_count += 1
                        print(f"✅ Profil klasörü silindi: {profile}")

                    # 2. MySQL'den kullanıcıyı sil
                    if user_manager.delete_user(profile):
                        mysql_deleted_count += 1
                        print(f"✅ MySQL kaydı silindi: {profile}")
                    else:
                        print(f"⚠️ MySQL kaydı bulunamadı veya silinemedi: {profile}")
                except Exception as e:
                    self.show_error(f"{profile} silinirken hata: {str(e)}")

            # Sonuç mesajı
            result_message = f"✅ {deleted_count} profil klasörü silindi.\n"
            result_message += f"✅ {mysql_deleted_count} MySQL kaydı silindi."

            if deleted_count != mysql_deleted_count:
                result_message += f"\n⚠️ Bazı MySQL kayıtları silinemedi."

            self.show_info(result_message)
            self.load_profiles()

    def open_browser(self, profile):
        """Tarayıcı aç"""
        try:
            # MySQL'den kullanıcı bilgilerini kontrol et
            user_data = user_manager.get_user(profile)
            if user_data:
                self.show_info(f"📊 {profile} MySQL'de kayıtlı\n"
                          f"🕒 Son giriş: {user_data.get('son_giris', 'Bilinmiyor')}\n"
                          f"📊 Durum: {user_data.get('durum', 'Bilinmiyor')}")

            self.close_existing_chrome_processes(profile)

            options = Options()

            # Kalıcı profil kullan
            original_profile_path = os.path.abspath(f"./Profiller/{profile}")

            if not os.path.exists(original_profile_path):
                self.show_warning(f"{profile} profili bulunamadı!")
                return

            options.add_argument(f"--user-data-dir={original_profile_path}")

            # User-Agent ayarı (MySQL'den al)
            user_agent = user_manager.get_user_agent(profile)
            if user_agent:
                options.add_argument(f"--user-agent={user_agent}")
                print(f"🔧 {profile} için user-agent kullanılıyor")
            else:
                print(f"⚠️ {profile} için user-agent bulunamadı, varsayılan kullanılacak")

            # Proxy ayarı - format kontrolü ile
            if self.proxy_enabled.isChecked() and self.proxy_entry.text():
                proxy = self.proxy_entry.text()
                if self.validate_proxy_format(proxy):
                    options.add_argument(f"--proxy-server={proxy}")
                else:
                    self.show_error(f"Geçersiz proxy formatı: {proxy}")
                    return None

            # Display ve GPU ayarları
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--remote-debugging-port=9222")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")

            # Chrome başlatma ayarları
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-default-apps")

            # Anti-bot ayarları
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            service = Service("chromedriver.exe")
            service.hide_command_prompt_window = True

            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # İlk olarak IP kontrolü yap
            browser_ip = self.check_browser_ip_initial(driver)
            if not browser_ip:
                self.show_error(f"{profile} için tarayıcı IP'si alınamadı.")
                driver.quit()
                return

            # Proxy kontrolü yap
            if not self.validate_proxy(browser_ip):
                driver.quit()
                return

            # MySQL'den kaydedilmiş çerezleri önce uygula
            self.apply_saved_cookies_to_browser(driver, profile)

            # Twitter'a git
            driver.get("https://x.com/")

            # Sayfanın tam yüklenmesini bekle
            self.wait_for_page_load(driver)

            # Giriş durumunu kontrol et
            current_url = driver.current_url
            if "logout" in current_url or "login" in current_url:
                self.show_warning(f"{profile} profilinde oturum kaybı tespit edildi!\nÇerezler geçersiz olabilir.")

            # Çerezleri güncelle (x.com tam yüklendikten sonra)
            self.update_cookies_in_mysql(driver, profile)

            # Driver'ı listeye ekle
            self.drivers.append({
                'driver': driver,
                'profile': profile,
                'temp_path': None
            })

            # MySQL'de son giriş zamanını güncelle
            if user_data:
                user_manager.update_user(profile)

            self.show_info(f"{profile} profili için tarayıcı açıldı.\n✅ Uzantılar ve ayarlar kalıcı olarak korunacak!")

        except Exception as e:
            self.show_error(f"Tarayıcı açılırken hata: {str(e)}")

    def close_existing_chrome_processes(self, profile):
        """Mevcut Chrome process'lerini kapat"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        if proc.info['cmdline']:
                            cmdline = ' '.join(proc.info['cmdline'])
                            if profile in cmdline and 'user-data-dir' in cmdline:
                                proc.terminate()
                                proc.wait(timeout=3)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
        except ImportError:
            pass
        except Exception as e:
            print(f"Process kapatma hatası: {str(e)}")

    def toggle_proxy_fields(self):
        """Proxy alanlarını etkinleştir/devre dışı bırak"""
        enabled = self.proxy_enabled.isChecked()
        self.proxy_entry.setEnabled(enabled)
        self.reset_url_entry.setEnabled(enabled)

    def change_ip(self):
        """IP değiştir"""
        if not self.proxy_enabled.isChecked() or not self.proxy_entry.text():
            self.show_warning("Önce proxy ayarlarını yapın!")
            return

        if not self.reset_url_entry.text():
            self.show_warning("IP Reset URL'sini girin!")
            return

        if self.drivers:
            for driver_info in self.drivers:
                try:
                    driver = driver_info['driver']
                    reset_url = self.reset_url_entry.text()

                    # Yeni sekme aç
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[-1])

                    # Reset URL'sine git
                    driver.get(reset_url)
                    time.sleep(5)

                    # IP'yi tekrar kontrol et
                    self.check_browser_ip(driver)

                    self.show_info(f"{driver_info['profile']} için IP sıfırlandı.")

                except Exception as e:
                    self.show_error(f"IP sıfırlama hatası: {str(e)}")
        else:
            self.show_info("Açık tarayıcı bulunamadı.")

    def start_ip_monitoring(self):
        """IP takibini başlat        """
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

    def check_browser_ip_initial(self, driver):
        """Tarayıcının IP adresini kontrol et (geçici sekme ile)"""
        try:
            print("🔍 Tarayıcı IP adresi kontrol ediliyor...")

            # Yeni sekme aç
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])

            # IP kontrol sitesine git
            driver.get("https://api.ipify.org")
            time.sleep(3)

            # IP adresini al
            browser_ip = driver.find_element("tag name", "body").text.strip()

            print(f"🌐 Tarayıcı IP adresi: {browser_ip}")
            self.set_browser_ip(browser_ip)

            # Sekmeyi kapat ve ana sekmeye dön
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

            return browser_ip

        except Exception as e:
            print(f"❌ Tarayıcı IP kontrol hatası: {str(e)}")
            self.set_browser_ip("Kontrol edilemedi")
            return None

    def check_browser_ip(self, driver):
        """Tarayıcının IP adresini kontrol et (geçici sekme ile)"""
        try:
            # Yeni sekme aç
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])

            # IP kontrol sitesine git
            driver.get("https://api.ipify.org")
            time.sleep(2)

            # IP adresini al
            browser_ip = driver.find_element("tag name", "body").text.strip()

            # IP label'ını güncelle
            self.set_browser_ip(browser_ip)

            # Sekmeyi kapat ve ana sekmeye dön
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        except Exception as e:
            print(f"IP kontrol hatası: {str(e)}")

    def wait_for_page_load(self, driver):
        """X.com sayfasının tam yüklenmesini bekle"""
        try:
            print("⏳ X.com sayfasının yüklenmesi bekleniyor...")

            # İlk olarak temel yükleme süresi
            time.sleep(5)

            # Sayfa başlığının yüklenmesini bekle
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By

            wait = WebDriverWait(driver, 15)

            # X.com'un ana elementlerinden birinin yüklenmesini bekle
            try:
                # Ana navigasyon veya header elementini bekle
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "nav")))
                print("✅ X.com navigasyon elementi yüklendi")
            except:
                try:
                    # Alternatif olarak header bekle
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "header")))
                    print("✅ X.com header elementi yüklendi")
                except:
                    print("⚠️ X.com elementleri bulunamadı, süre ile devam ediliyor")

            # Çerezlerin oluşması için ek bekleme
            time.sleep(1)
            print("✅ X.com sayfası tam yüklendi")

        except Exception as e:
            print(f"⚠️ Sayfa yükleme bekleme hatası: {str(e)}")
            # Hata durumunda minimum bekleme
            time.sleep(8)

    def apply_saved_cookies_to_browser(self, driver, profile):
        """MySQL'den kaydedilmiş çerezleri tarayıcıya uygula"""
        try:
            print(f"🍪 {profile} için kaydedilmiş çerezler tarayıcıya uygulanıyor...")

            # MySQL'den çerezleri al
            saved_cookies = user_manager.get_user_cookies(profile)
            if not saved_cookies:
                print(f"⚠️ {profile} için kaydedilmiş çerez bulunamadı")
                return False

            # X.com'a git
            driver.get("https://x.com")
            time.sleep(2)

            # Kaydedilmiş çerezleri tarayıcıya ekle
            cookies_added = 0
            for cookie_name, cookie_value in saved_cookies.items():
                if cookie_value:  # Boş değilse
                    try:
                        driver.add_cookie({
                            'name': cookie_name,
                            'value': cookie_value,
                            'domain': '.x.com',
                            'path': '/'
                        })
                        cookies_added += 1
                    except Exception as cookie_error:
                        print(f"⚠️ {cookie_name} çerezi eklenemedi: {cookie_error}")

            if cookies_added > 0:
                print(f"✅ {profile} için {cookies_added} çerez tarayıcıya eklendi")
                # Sayfayı yenile
                driver.refresh()
                time.sleep(3)
                return True
            else:
                print(f"⚠️ {profile} için hiç çerez eklenemedi")
                return False

        except Exception as e:
            print(f"❌ {profile} çerez uygulama hatası: {str(e)}")
            return False

    def update_cookies_in_mysql(self, driver, profile):
        """X.com çerezlerini MySQL'de güncelle"""
        try:
            print(f"🍪 {profile} için çerezler güncelleniyor...")

            # X.com'da olduğundan emin ol
            current_url = driver.current_url
            if "x.com" not in current_url:
                driver.get("https://x.com")
                time.sleep(3)

            # Güncel çerezleri al
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

            # MySQL'de güncelle
            if cookie_dict:
                success = user_manager.update_user_cookies(profile, cookie_dict)
                if success:
                    print(f"✅ {profile} çerezleri MySQL'de güncellendi ({len(cookie_dict)} çerez)")
                else:
                    print(f"⚠️ {profile} çerezleri MySQL'de güncellenemedi")
            else:
                print(f"⚠️ {profile} için güncel çerez bulunamadı")

        except Exception as e:
            print(f"❌ {profile} çerez güncelleme hatası: {str(e)}")

    def validate_proxy_format(self, proxy):
        """Proxy formatını doğrula"""
        try:
            import re
            pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):\d+$|^[a-zA-Z0-9.-]+:\d+$'
            return bool(re.match(pattern, proxy))
        except:
            return False

    def validate_proxy(self, browser_ip):
        """Proxy kontrolü yap - gelişmiş kontrol ile"""
        try:
            # Proxy etkin değilse kontrol yapma
            if not self.proxy_enabled.isChecked():
                return True

            # Bilgisayar IP'si ile karşılaştır
            computer_ip = self.current_ip

            if browser_ip == computer_ip:
                # Alternatif IP servisi kontrol et
                try:
                    alt_ip = self.check_alternative_ip_service()
                    if alt_ip and alt_ip != computer_ip:
                        print("✅ Alternatif IP servisi IP değişikliğini onayladı")
                        return True
                except:
                    pass
                
                self.show_warning("IP adresi değişmemiş!\n\nProxy ayarlarınızı kontrol edin.\nTarayıcı kapatıldı.")
                return False

            print("✅ Proxy doğrulama başarılı - IP değişmiş")
            return True

        except Exception as e:
            print(f"❌ Proxy doğrulama hatası: {str(e)}")
            return True  # Hata durumunda devam et
    
    def check_alternative_ip_service(self):
        """Alternatif IP servisini kontrol et"""
        try:
            import requests
            response = requests.get("https://httpbin.org/ip", timeout=5)
            if response.status_code == 200:
                return response.json().get('origin', '').split(',')[0].strip()
        except:
            pass
        return None

    def return_to_main(self):
        """Ana menüye dön"""
        self.ip_thread_running = False
        self.ip_timer.stop()

        # Açık driver'ları kapat
        for driver_info in self.drivers:
            try:
                driver_info['driver'].quit()
            except:
                pass

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

    def process_profile(self, profile):
            """Tek profil işleme"""
            driver = None
            try:
                self.log_message(f"🔍 {profile} profili işleniyor...")

                # Kullanıcının giriş türünü kontrol et
                login_type = user_manager.get_user_login_type(profile)
                self.log_message(f"📋 {profile} giriş türü: {login_type}")

                # Tarayıcı oluştur
                driver = self.create_driver(profile)
                if not driver:
                    return False

                # Giriş türüne göre işlem yap
                if login_type == 'cerezli':
                    # Çerezli giriş - MySQL'den çerezleri al ve uygula
                    self.log_message(f"🍪 {profile} için çerezli giriş yapılıyor...")
                    cookies_data = user_manager.get_user_cookies(profile)

                    if not cookies_data:
                        self.log_message(f"❌ {profile} için çerezler bulunamadı!")
                        return False

                    # X.com'a git ve çerezleri uygula
                    driver.get("https://x.com/")
                    time.sleep(3)

                    # MySQL'den gelen çerezleri tarayıcıya ekle
                    for cookie_name, cookie_value in cookies_data.items():
                        if cookie_value:  # Boş değilse
                            try:
                                driver.add_cookie({
                                    'name': cookie_name,
                                    'value': cookie_value,
                                    'domain': '.x.com'
                                })
                            except Exception as e:
                                self.log_message(f"⚠️ {profile} çerez ekleme hatası {cookie_name}: {e}")

                    # Sayfayı yenile
                    driver.refresh()
                    time.sleep(5)

                else:
                    # Normal giriş - profil klasörünü kontrol et
                    profile_path = f"./Profiller/{profile}"
                    if not os.path.exists(profile_path):
                        self.log_message(f"❌ {profile} profil klasörü bulunamadı!")
                        return False

                    self.log_message(f"🔑 {profile} için normal profil giriş yapılıyor...")

                    # Twitter'a git
                    driver.get("https://x.com/")

                # Sayfanın tam yüklenmesini bekle
                self.wait_for_page_load(driver)

                # Giriş durumunu kontrol et
                current_url = driver.current_url
                if "logout" in current_url or "login" in current_url:
                    self.log_message(f"⚠️ {profile} profilinde oturum kaybı tespit edildi!")
                    if login_type == 'cerezli':
                        self.log_message(f"🔄 {profile} çerezli giriş başarısız, normal giriş türüne çevriliyor...")
                        user_manager.update_user_login_type(profile, 'normal')
                    return False

                # Başarılı giriş - çerezleri güncelle
                self.update_cookies_in_mysql(driver, profile)

                # Driver'ı listeye ekle
                self.drivers.append({
                    'driver': driver,
                    'profile': profile,
                    'temp_path': None
                })

                # MySQL'de son giriş zamanını güncelle
                user_data = user_manager.get_user(profile)
                if user_data:
                    user_manager.update_user(profile)

                self.log_message(f"✅ {profile} profili başarıyla işlendi!")
                return True

            except Exception as e:
                self.log_message(f"❌ {profile} profil işlenirken hata: {str(e)}")
                return False

            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass

    def log_message(self, message):
        """Log mesajını yazdır"""
        print(message)