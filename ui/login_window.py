from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QFileDialog,
    QMessageBox,
    QListWidget,
    QTextEdit,
    QCheckBox,
    QLineEdit,
    QGroupBox,
    QSplitter,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QScrollArea, QListWidget, QListWidgetItem
from PyQt5.QtGui import QFont
import threading
import time
import random
import requests
import os
import uuid
import shutil
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from database.user_manager import user_manager
from config.settings import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_PROFILES_DIR = os.path.join(BASE_DIR, "temp_profiles")

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

        # Cihaz listesini JSON dosyasından yükle (UI elemanları hazır olduktan sonra)
        self.android_devices = self.load_devices_from_file()

        self.start_ip_monitoring()

    def load_devices_from_file(self):
        """JSON dosyasından cihaz listesini yükle"""
        devices_file = os.path.join(BASE_DIR, "config", "android_devices.json")

        # Varsayılan cihaz listesi (dosya yoksa)
        default_devices = [
            {
                "name": "Apple iPhone 15 Pro Max",
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                "device_metrics": {
                    "width": 430,
                    "height": 932,
                    "device_scale_factor": 3,
                    "mobile": True
                },
                "client_hints": {
                    "platform": "iOS",
                    "mobile": True
                }
            },
            {
                "name": "Samsung Galaxy S24 Ultra",
                "user_agent": "Mozilla/5.0 (Linux; Android 14; SM-S928U Build/QL1A.230918.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
                "device_metrics": {
                    "width": 384,
                    "height": 824,
                    "device_scale_factor": 3.75,
                    "mobile": True
                },
                "client_hints": {
                    "platform": "Android",
                    "mobile": True
                }
            },
            {
                "name": "Xiaomi 15 Ultra",
                "user_agent": "Mozilla/5.0 (Linux; Android 14; Mi 13 Pro Build/TKQ1.220716.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
                "device_metrics": {
                    "width": 393,
                    "height": 852,
                    "device_scale_factor": 3,
                    "mobile": True
                },
                "client_hints": {
                    "platform": "Android",
                    "mobile": True
                }
            }
        ]

        try:
            if os.path.exists(devices_file):
                with open(devices_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    devices = data.get('devices', default_devices)
                    self.log_message(f"✅ {len(devices)} cihaz JSON dosyasından yüklendi")
                    return devices
            else:
                # Dosya yoksa oluştur
                os.makedirs(os.path.dirname(devices_file), exist_ok=True)
                with open(devices_file, 'w', encoding='utf-8') as f:
                    json.dump({"devices": default_devices}, f, indent=2, ensure_ascii=False)
                self.log_message(f"ℹ️ Cihaz dosyası oluşturuldu: {devices_file}")
                return default_devices

        except Exception as e:
            self.log_message(f"⚠️ Cihaz dosyası okuma hatası: {e}, varsayılan liste kullanılıyor")
            return default_devices

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

        # Dosya formatı ayarları
        format_group = QGroupBox("📝 Dosya Formatı")
        format_group.setObjectName("settingsGroup")
        format_layout = QVBoxLayout()
        format_layout.setSpacing(8)

        format_info_label = QLabel("Temel format: kullaniciadi:sifre\nEk alanları seçin ve sıralarını belirleyin:")
        format_info_label.setObjectName("settingsLabel")
        format_layout.addWidget(format_info_label)

        # Format alanları için scrollable widget
        from PyQt5.QtWidgets import QScrollArea, QListWidget, QListWidgetItem
        
        # Format sıralama listesi
        order_label = QLabel("Alan Sıralaması (sürükle-bırak):")
        order_label.setObjectName("settingsLabel")
        format_layout.addWidget(order_label)
        
        self.format_order_list = QListWidget()
        self.format_order_list.setObjectName("formatOrderList")
        self.format_order_list.setDragDropMode(QListWidget.InternalMove)
        self.format_order_list.setMaximumHeight(120)
        self.format_order_list.itemChanged.connect(self.update_format_preview)
        
        # Varsayılan format sırası
        self.format_fields = [
            {"key": "auth_token", "name": "auth_token (Twitter çerezi)", "enabled": False},
            {"key": "ct0", "name": "ct0 (Twitter çerezi)", "enabled": False},
            {"key": "proxy_ip", "name": "Proxy IP", "enabled": False},
            {"key": "proxy_port", "name": "Proxy Port", "enabled": False},
            {"key": "phone", "name": "Telefon Numarası", "enabled": False},
            {"key": "email", "name": "E-mail Adresi", "enabled": False}
        ]
        
        # List widget'a öğeleri ekle
        for field in self.format_fields:
            item = QListWidgetItem(field["name"])
            item.setData(Qt.UserRole, field["key"])
            item.setCheckState(Qt.Unchecked)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            self.format_order_list.addItem(item)
        
        format_layout.addWidget(self.format_order_list)

        # Format önizleme
        self.format_preview = QLabel("Önizleme: kullaniciadi:sifre")
        self.format_preview.setObjectName("formatPreview")
        format_layout.addWidget(self.format_preview)

        format_group.setLayout(format_layout)

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

        layout.addWidget(format_group)
        layout.addWidget(proxy_group)
        layout.addWidget(browser_group)
        layout.addStretch()
        layout.addWidget(start_btn)
        
        # Panel genişliğini artır
        panel.setMinimumWidth(320)

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

        #formatPreview {{
            font-size: 12px;
            color: {self.colors['secondary']};
            font-family: 'SF Mono', 'Consolas', monospace;
            background-color: {self.colors['background_alt']};
            padding: 8px;
            border-radius: 6px;
            margin-top: 10px;
        }}

        #formatOrderList {{
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            background-color: white;
            alternate-background-color: {self.colors['card_bg']};
            selection-background-color: {self.colors['primary']};
            font-size: 12px;
            padding: 4px;
        }}

        #formatOrderList::item {{
            padding: 4px 8px;
            border-radius: 4px;
            margin: 1px;
        }}

        #formatOrderList::item:selected {{
            background-color: {self.colors['primary']};
            color: white;
        }}

        #formatOrderList::item:hover {{
            background-color: {self.colors['card_bg']};
        }}
        """

        self.setStyleSheet(style)

    def toggle_proxy_fields(self):
        """Proxy alanlarını etkinleştir/devre dışı bırak"""
        enabled = self.proxy_enabled.isChecked()
        self.proxy_entry.setEnabled(enabled)
        self.reset_url_entry.setEnabled(enabled)

    def update_format_preview(self):
        """Format önizlemesini güncelle"""
        format_parts = ["kullaniciadi", "sifre"]
        
        # Liste sırasına göre aktif alanları ekle
        for i in range(self.format_order_list.count()):
            item = self.format_order_list.item(i)
            if item.checkState() == Qt.Checked:
                field_key = item.data(Qt.UserRole)
                format_parts.append(field_key)
            
        preview_text = f"Önizleme: {':'.join(format_parts)}"
        self.format_preview.setText(preview_text)

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

                # Format sırasını liste widget'tan al
                format_order = ['username', 'password']
                for i in range(self.format_order_list.count()):
                    item = self.format_order_list.item(i)
                    if item.checkState() == Qt.Checked:
                        field_key = item.data(Qt.UserRole)
                        format_order.append(field_key)

                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            parts = line.split(':')
                            if len(parts) >= 2:
                                user_data = {}
                                
                                # Format sırasına göre değerleri ata
                                for i, field in enumerate(format_order):
                                    if i < len(parts):
                                        value = parts[i].strip() if parts[i].strip() else None
                                        user_data[field] = value

                                # Zorunlu alanları kontrol et
                                if not user_data.get('username') or not user_data.get('password'):
                                    continue

                                # Display text'i oluştur
                                display_parts = [user_data['username']]
                                
                                if user_data.get('auth_token') or user_data.get('ct0'):
                                    display_parts.append("(Çerezli Giriş)")
                                elif user_data.get('proxy_ip') and user_data.get('proxy_port'):
                                    display_parts.append(f"(Proxy: {user_data['proxy_ip']}:{user_data['proxy_port']})")
                                else:
                                    display_parts.append("(Normal Giriş)")

                                display_text = " ".join(display_parts)

                                self.users.append(user_data)
                                self.user_list.addItem(display_text)
                                
                        except Exception as e:
                            self.log_message(f"⚠️ Satır işleme hatası: {line} - {e}")

                self.log_message(f"✅ {len(self.users)} kullanıcı yüklendi.")
                self.log_message(f"📝 Kullanılan format: {':'.join(format_order)}")

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
            # Mobil Cihaz User-Agent atama (önce selected_device'i belirle)
            existing_user_agent = user_manager.get_user_agent(user['username'])
            selected_device = None

            if existing_user_agent:
                # Mevcut user-agent'ı kullan ve cihazı bul
                for device in self.android_devices:
                    if device['user_agent'] == existing_user_agent:
                        selected_device = device
                        break

                if selected_device:
                    self.log_message(f"📱 {user['username']} için mevcut cihaz kullanılıyor: {selected_device['name']}")
                else:
                    # Eski user-agent varsa yeni cihaz seç
                    selected_device = random.choice(self.android_devices)
                    self.log_message(f"🔄 {user['username']} için eski user-agent tespit edildi, yeni cihaz atanıyor: {selected_device['name']}")
            else:
                # Rastgele cihaz seç ve kaydet
                selected_device = random.choice(self.android_devices)
                self.log_message(f"📱 {user['username']} için yeni cihaz atandı: {selected_device['name']}")

            # Önce kullanıcıyı MySQL'e kaydet (eğer yoksa)
            user_data = user_manager.get_user(user['username'])
            if not user_data:
                # Kullanıcı yok, önce temel bilgileri kaydet
                basic_save_success = user_manager.save_user(
                    user['username'],
                    user['password'],
                    None,  # cookie_dict
                    user.get('proxy_ip'),
                    user.get('proxy_port'),
                    selected_device['user_agent'],  # user_agent
                    user.get('phone'),
                    user.get('email')
                )
                if basic_save_success:
                    self.log_message(f"✅ {user['username']} temel bilgileri MySQL'e kaydedildi")
                else:
                    self.log_message(f"⚠️ {user['username']} temel bilgileri kaydedilemedi")

            # User-agent'ı güncelle/kaydet
            if not existing_user_agent or existing_user_agent != selected_device['user_agent']:
                user_agent_updated = user_manager.update_user_agent(user['username'], selected_device['user_agent'])
                device_specs_updated = user_manager.update_device_specs(user['username'], selected_device)
                
                if user_agent_updated and device_specs_updated:
                    self.log_message(f"✅ {user['username']} - {selected_device['name']} user-agent ve cihaz özellikleri kaydedildi")
                    self.log_message(f"🔧 Ekran: {selected_device['device_metrics']['width']}x{selected_device['device_metrics']['height']}, DPR: {selected_device['device_metrics']['device_scale_factor']}")
                elif user_agent_updated:
                    self.log_message(f"✅ {user['username']} user-agent kaydedildi")
                    self.log_message(f"⚠️ {user['username']} cihaz özellikleri kaydedilemedi")
                else:
                    self.log_message(f"⚠️ {user['username']} user-agent kaydedilemedi")

            # Chrome options - Replit ortamı için optimize edilmiş
            chrome_options = Options()

            # Temel güvenlik ayarları (Replit uyumlu)
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")

            # Basit profil yolu ayarı
            profile_path = os.path.join(TEMP_PROFILES_DIR, user['username'])
            os.makedirs(profile_path, exist_ok=True)

            # Mobil cihaz simülasyonu - viewport düzeltildi
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
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

            # Chrome pencere boyutunu mobil cihaz boyutundan biraz daha büyük yap
            window_width = max(selected_device['device_metrics']['width'] + 50, 800)
            window_height = max(selected_device['device_metrics']['height'] + 100, 600)
            chrome_options.add_argument(f"--window-size={window_width},{window_height}")

            self.log_message(f"📱 {user['username']} için mobil emülasyon: {selected_device['device_metrics']['width']}x{selected_device['device_metrics']['height']}")
            self.log_message(f"🖥️ Chrome pencere boyutu: {window_width}x{window_height}")

            # Profil yolu
            chrome_options.add_argument(f"--user-data-dir={profile_path}")

            # Basit performans ayarları
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--lang=tr-TR")

            # Headless modu test için kapalı (GUI modda çalıştır)
            # if not self.browser_visible.isChecked():
            #     chrome_options.add_argument("--headless=new")

            # Proxy ayarı
            proxy_to_use = None
            if user.get('proxy_ip') and user.get('proxy_port'):
                proxy_to_use = f"{user['proxy_ip']}:{user['proxy_port']}"
                self.log_message(f"🌐 Özel proxy kullanılıyor: {proxy_to_use}")
            elif self.proxy_enabled.isChecked() and self.proxy_entry.text():
                proxy_to_use = self.proxy_entry.text()
                self.log_message(f"🌐 Genel proxy kullanılıyor: {proxy_to_use}")

            if proxy_to_use:
                if proxy_to_use.count(':') >= 3:
                    self.log_message(f"⚠️ Kimlik doğrulamalı proxy tespit edildi, atlanıyor.")
                    return None
                chrome_options.add_argument(f"--proxy-server={proxy_to_use}")

            # Display ve GPU ayarları
            chrome_options.add_argument("--remote-debugging-port=9222")

            # Chrome başlatma ayarları
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--disable-default-apps")

            # Sadece temel anti-bot ayarları
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0
            })

            # Basit Chrome driver başlatma
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.set_page_load_timeout(60)
                driver.implicitly_wait(15)

                self.log_message(f"✅ Chrome driver başarıyla başlatıldı")

                # Tarayıcı açılır açılmaz kullanıcı bilgilerini ve cihaz özelliklerini kaydet
                if not existing_user_agent or existing_user_agent != selected_device['user_agent']:
                    # User-agent'ı kaydet
                    user_agent_success = user_manager.update_user_agent(user['username'], selected_device['user_agent'])
                    # Cihaz özelliklerini kaydet
                    device_specs_success = user_manager.update_device_specs(user['username'], selected_device)
                    
                    if user_agent_success and device_specs_success:
                        self.log_message(f"✅ {user['username']} tarayıcı açıldıktan sonra user-agent ve cihaz özellikleri kaydedildi")
                    elif user_agent_success:
                        self.log_message(f"✅ {user['username']} user-agent kaydedildi")
                        self.log_message(f"⚠️ {user['username']} cihaz özellikleri kaydedilemedi")
                    else:
                        self.log_message(f"⚠️ {user['username']} user-agent kaydedilemedi")

            except Exception as e:
                self.log_message(f"❌ Chrome driver başlatma hatası: {str(e)}")
                return None

            # Minimal anti-bot koruması (sayfa yüklenmesinden sonra)
            try:
                script = "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                driver.execute_script(script)
                self.log_message(f"🛡️ Anti-bot koruması aktif")
            except Exception as script_error:
                self.log_message(f"⚠️ Anti-bot script hatası: {script_error}")

            return driver

        except Exception as e:
            self.log_message(f"❌ Tarayıcı başlatma hatası: {str(e)}")
            return None

    def login_with_cookies(self, driver, user):
        """Çerezlerle giriş yap"""
        try:
            auth_token = user.get('auth_token')
            ct0 = user.get('ct0')
            
            if not auth_token or not ct0:
                return False
                
            self.log_message(f"🍪 {user['username']} için çerezli giriş deneniyor...")
            
            # Önce X.com'a git
            driver.get("https://x.com")
            time.sleep(3)
            
            # Çerezleri ekle
            cookies_to_add = [
                {'name': 'auth_token', 'value': auth_token, 'domain': '.x.com'},
                {'name': 'ct0', 'value': ct0, 'domain': '.x.com'}
            ]
            
            # Ek çerezler varsa ekle
            if user.get('guest_id'):
                cookies_to_add.append({'name': 'guest_id', 'value': user['guest_id'], 'domain': '.x.com'})
            
            for cookie in cookies_to_add:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    self.log_message(f"⚠️ Çerez ekleme hatası: {e}")
            
            # Sayfayı yenile
            driver.refresh()
            time.sleep(5)
            
            # Giriş kontrolü
            current_url = driver.current_url
            if "login" not in current_url.lower() and ("home" in current_url.lower() or "x.com" in current_url):
                self.log_message(f"✅ {user['username']} çerezli giriş başarılı")
                return True
            else:
                self.log_message(f"❌ {user['username']} çerezli giriş başarısız")
                return False
                
        except Exception as e:
            self.log_message(f"❌ {user['username']} çerezli giriş hatası: {str(e)}")
            return False

    def human_type(self, element, text):
        """İnsan benzeri yazma simülasyonu"""
        element.clear()
        for char in text:
            element.send_keys(char)
            # Her karakter arası rastgele bekleme (50-200ms)
            time.sleep(random.uniform(0.05, 0.2))

    def perform_login(self, driver, user):
        """Girişteki bu işlem birden fazla basamaktan oluşuyor ve her basamakta başarısızlık durumu kontrol edilmelidir"""

        try:
            # Önce çerezli giriş dene
            if user.get('auth_token') and user.get('ct0'):
                if self.login_with_cookies(driver, user):
                    return True
                else:
                    self.log_message(f"🔄 {user['username']} çerezli giriş başarısız, normal giriş deneniyor...")
            
            # X.com'a git
            self.log_message(f"🌐 {user['username']} için X.com'a gidiliyor...")
            driver.get("https://x.com/i/flow/login?lang=tr")

            # Sayfa yüklenme kontrolü - daha uzun bekleme
            time.sleep(5)
            current_url = driver.current_url
            if "login" not in current_url.lower():
                self.log_message(f"✅ {user['username']} zaten giriş yapmış")
                return True

            # Ana sayfa yüklendi
            self.log_message(f"✅ Ana sayfa yüklendi")

            # Sayfa içeriği kontrolü - daha akıllı kontrol
            try:
                # Login form elementlerinin yüklenmesini bekle
                WebDriverWait(driver, 10).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[autocomplete='username']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='text']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
                    )
                )
                self.log_message(f"✅ Login formu yüklendi")
            except:
                self.log_message(f"⚠️ Login formu yüklenmedi, 5 saniye daha bekleniyor...")
                time.sleep(5)

            # Kullanıcı adı alanını bul ve doldur
            try:
                self.log_message(f"👤 {user['username']} kullanıcı adı giriliyor...")

                # Çeşitli selector'ları dene
                username_selectors = [
                    "input[autocomplete='username']",
                    "input[name='text']",
                    "input[data-testid='ocfEnterTextTextInput']",
                    ".r-30o5oe input",
                    "input[type='text']"
                ]

                username_element = None
                for selector in username_selectors:
                    try:
                        username_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        break
                    except:
                        continue

                if not username_element:
                    raise Exception("Kullanıcı adı alanı bulunamadı")

                # İnsan benzeri yazma
                self.human_type(username_element, user['username'])

                # İleri butonunu bul ve tıkla
                self.log_message(f"➡️ İleri butonuna tıklanıyor...")
                time.sleep(random.uniform(1.5, 3.0))  # Rastgele bekleme

                next_button_selectors = [
                    "button[role='button']:has-text('İleri')",
                    "[data-testid='LoginForm_Login_Button']",
                    "button:contains('İleri')",
                    ".r-19u6a5r button"
                ]

                next_button = None
                for selector in next_button_selectors:
                    try:
                        next_button = driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue

                if not next_button:
                    # JavaScript ile buton ara
                    buttons = driver.find_elements(By.TAG_NAME, "button") 
                    for button in buttons:
                        if "İleri" in button.text or "Next" in button.text:
                            next_button = button
                            break

                if next_button:
                    next_button.click()
                else:
                    raise Exception("İleri butonu bulunamadı")

                # Şifre alanının yüklenmesini bekle
                time.sleep(random.uniform(2.0, 4.0))

                # Şifre alanını bul ve doldur
                self.log_message(f"🔑 {user['username']} şifresi giriliyor...")

                password_selectors = [
                    "input[autocomplete='current-password']",
                    "input[name='password']",
                    "input[type='password']",
                    "[data-testid='LoginForm_Password']"
                ]

                password_element = None
                for selector in password_selectors:
                    try:
                        password_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        break
                    except:
                        continue

                if not password_element:
                    raise Exception("Şifre alanı bulunamadı")

                # İnsan benzeri şifre yazma
                self.human_type(password_element, user['password'])

                # Giriş yap butonunu bul ve tıkla
                self.log_message(f"🚪 Giriş yap butonuna tıklanıyor...")
                time.sleep(random.uniform(1.0, 2.5))

                login_button_selectors = [
                    "button[data-testid='LoginForm_Login_Button']",
                    "button:contains('Giriş yap')",
                    "button:contains('Log in')",
                    ".r-19u6a5r button[role='button']"
                ]

                login_button = None
                for selector in login_button_selectors:
                    try:
                        login_button = driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue

                if not login_button:
                    # JavaScript ile buton ara
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        if "Giriş yap" in button.text or "Log in" in button.text:
                            login_button = button
                            break

                if login_button:
                    login_button.click()
                else:
                    raise Exception("Giriş yap butonu bulunamadı")

                # Giriş sonucunu bekle ve kontrol et
                self.log_message(f"⏳ Giriş sonucu bekleniyor...")
                time.sleep(8)  # Daha uzun bekleme

                current_url = driver.current_url
                if "home" in current_url.lower() or ("x.com" in current_url and "login" not in current_url.lower()):
                    self.log_message(f"✅ {user['username']} başarıyla giriş yaptı")
                    return True
                else:
                    self.log_message(f"❌ {user['username']} giriş başarısız - URL: {current_url}")
                    return False

            except Exception as e:
                self.log_message(f"❌ {user['username']} giriş hatası: {str(e)}")
                return False

        except Exception as e:
            self.log_message(f"❌ {user['username']} genel hata: {str(e)}")
            return False

    def wait_and_type(self, driver, xpath, text):
        """Element bekle ve yazı yaz"""
        try:
            wait = WebDriverWait(driver, 15)
            element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            element.clear()
            time.sleep(0.5)
            element.send_keys(text)
            time.sleep(1)
        except TimeoutException:
            self.log_message(f"❌ Element bulunamadı: {xpath}")
            raise

    def wait_and_click(self, driver, xpath):
        """Element bekle ve tıkla"""
        try:
            wait = WebDriverWait(driver, 15)
            element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            time.sleep(0.5)
            element.click()
            time.sleep(1)
        except TimeoutException:
            self.log_message(f"❌ Tıklanabilir element bulunamadı: {xpath}")
            raise

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
                self.log_message(f"🔍 {user['username']} için {len(cookie_dict)} çerez bulundu: {list(cookie_dict.keys())}")

                # Çerezleri ayrı bir fonksiyon ile kaydet
                cookie_success = user_manager.update_user_cookies(user['username'], cookie_dict)
                if cookie_success:
                    self.log_message(f"✅ {user['username']} çerezleri MySQL'e kaydedildi ({len(cookie_dict)} çerez)")
                else:
                    self.log_message(f"⚠️ {user['username']} çerezleri MySQL'e kaydedilemedi")

                    # Alternatif olarak save_user fonksiyonunu dene
                    try:
                        alternative_success = user_manager.save_user(
                            user['username'],
                            user['password'],
                            cookie_dict,
                            user.get('year'),
                            user.get('month'),
                            user.get('proxy'),
                            user.get('proxy_port'),
                            user_manager.get_user_agent(user['username'])
                        )
                        if alternative_success:
                            self.log_message(f"✅ {user['username']} çerezleri alternatif yöntemle kaydedildi")
                        else:
                            self.log_message(f"❌ {user['username']} çerezleri alternatif yöntemle de kaydedilemedi")
                    except Exception as e:
                        self.log_message(f"❌ {user['username']} alternatif kaydetme hatası: {str(e)}")
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

        # Son giriş zamanını güncelle
        try:
            user = next((u for u in self.users if u['username'] == username), None)
            if user:
                # Sadece son giriş zamanını güncelle (kullanıcı zaten kaydedildi)
                user_manager.update_user(username, user['password'], None)
                self.log_message(f"✅ {username} son giriş zamanı güncellendi.")
            else:
                self.log_message(f"⚠️ {username} kullanıcı bilgisi bulunamadı.")
        except Exception as e:
            self.log_message(f"⚠️ Son giriş güncelleme hatası: {str(e)}")

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

        # Thread-safe log ekleme - log_text varsa
        if hasattr(self, 'log_text') and self.log_text is not None:
            self.log_text.append(log_entry)
            self.log_text.ensureCursorVisible()
        else:
            # log_text henüz hazır değilse konsola yazdır
            print(log_entry)

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