from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QMessageBox, QSpinBox, QGroupBox,
                             QRadioButton, QProgressBar, QTextEdit, QButtonGroup,
                             QCheckBox, QLineEdit, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import asyncio
from twikit import Client
import datetime
import pytz
import os
import random
import time
import requests
from database.user_manager import user_manager
from database.mysql import mysql_manager

class YearSeparatorWorker(QThread):
    progress_updated = pyqtSignal(int, int)  # current, total
    log_updated = pyqtSignal(str)
    finished = pyqtSignal(bool)  # success

    def __init__(self, account_type, wait_seconds, use_proxy, proxy_url, reset_url):
        super().__init__()
        self.account_type = account_type  # 'login' veya 'target'
        self.wait_seconds = wait_seconds
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url
        self.reset_url = reset_url
        self.is_running = True

    def run(self):
        try:
            asyncio.run(self.process_accounts())
        except Exception as e:
            self.log_updated.emit(f"❌ Kritik hata: {str(e)}")
            self.finished.emit(False)

    async def process_accounts(self):
        try:
            # Hesapları al
            if self.account_type == 'login':
                accounts = user_manager.get_all_users()
                self.log_updated.emit("📋 Giriş yapılmış hesaplar alındı")
            else:
                accounts = mysql_manager.get_all_targets()
                self.log_updated.emit("📋 Hedef hesaplar alındı")

            if not accounts:
                self.log_updated.emit("⚠️ Hiç hesap bulunamadı!")
                self.finished.emit(False)
                return

            # Giriş yapılmış hesapları al (çerez için)
            logged_users = user_manager.get_all_users()
            if not logged_users:
                self.log_updated.emit("❌ Giriş yapılmış hesap bulunamadı! Çerez için gerekli.")
                self.finished.emit(False)
                return

            total_accounts = len(accounts)
            processed = 0

            self.log_updated.emit(f"🚀 {total_accounts} hesap işlenecek")

            for account in accounts:
                if not self.is_running:
                    break

                username = account.get('kullanici_adi') if self.account_type == 'login' else account.get('kullanici_adi')

                # Tarih kontrolü - zaten kayıtlı mı?
                if self.account_type == 'login':
                    existing_date = user_manager.get_user_twitter_creation_date(username)
                else:
                    existing_date = mysql_manager.get_target_creation_date(username)

                if existing_date:
                    self.log_updated.emit(f"⏭️ {username} - Tarih zaten kayıtlı, atlanıyor")
                    processed += 1
                    self.progress_updated.emit(processed, total_accounts)
                    continue

                # Rastgele giriş yapılmış hesap seç
                random_user = random.choice(logged_users)
                cookies_data = user_manager.get_user_cookies(random_user.get('kullanici_adi'))

                if not cookies_data:
                    self.log_updated.emit(f"⚠️ {random_user.get('kullanici_adi')} çerezleri bulunamadı, atlanıyor")
                    processed += 1
                    self.progress_updated.emit(processed, total_accounts)
                    continue

                # Kullanıcının kendine ait proxysi varsa al
                user_proxy = user_manager.get_user_proxy(username) if self.account_type == 'login' else mysql_manager.get_target_proxy(username)

                # Tarih bilgisini çek
                creation_date = await self.get_account_creation_date(username, cookies_data, user_proxy)

                if creation_date:
                    # Tarihi kaydet
                    if self.account_type == 'login':
                        success = user_manager.update_user_twitter_creation_date(username, creation_date)
                    else:
                        success = mysql_manager.update_target_creation_date(username, creation_date)

                    if success:
                        self.log_updated.emit(f"✅ {username} - Twitter oluşturma tarihi kaydedildi: {creation_date}")
                    else:
                        self.log_updated.emit(f"❌ {username} - Twitter oluşturma tarihi kaydedilemedi")
                else:
                    self.log_updated.emit(f"❌ {username} - Twitter oluşturma tarihi alınamadı")

                # Çerezleri güncelle
                updated_cookies = await self.get_updated_cookies(cookies_data)
                if updated_cookies:
                    user_manager.update_user_cookies(random_user.get('kullanici_adi'), updated_cookies)

                processed += 1
                self.progress_updated.emit(processed, total_accounts)

                # Proxy sıfırlama
                if self.use_proxy and self.reset_url:
                    await self.reset_proxy()
                    await asyncio.sleep(10)  # 10 saniye bekle

                # Bekleme süresi
                if processed < total_accounts:  # Son hesap değilse bekle
                    self.log_updated.emit(f"⏳ {self.wait_seconds} saniye bekleniyor...")
                    await asyncio.sleep(self.wait_seconds)

            self.log_updated.emit("🎉 Tüm işlemler tamamlandı!")
            self.finished.emit(True)

        except Exception as e:
            self.log_updated.emit(f"❌ İşlem hatası: {str(e)}")
            self.finished.emit(False)

    async def get_account_creation_date(self, username, cookies_data, user_proxy=None):
        """Hesap oluşturma tarihini çek"""
        try:
            # Proxy seçimi: Önce hesabın kendi proxy'si, sonra genel proxy
            proxy_to_use = user_proxy if user_proxy else (self.proxy_url if self.use_proxy else None)
            client = Client(language="tr-TR", proxy=proxy_to_use)

            # Çerezleri yükle
            client.set_cookies(cookies_data)

            # Kullanıcı bilgilerini al
            user = await client.get_user_by_screen_name(username)

            if user and user.created_at:
                # Tarihi formatla
                turkey_date = self.format_turkey_time(user.created_at)
                return turkey_date

            return None

        except Exception as e:
            self.log_updated.emit(f"⚠️ {username} tarih alma hatası: {str(e)}")
            return None

    def format_turkey_time(self, utc_time_str):
        """UTC tarihini Türkiye saatine çevir"""
        try:
            # Twitter'ın tarih formatını parse et
            utc_time = datetime.datetime.strptime(utc_time_str, "%a %b %d %H:%M:%S %z %Y")

            # Türkiye saat dilimini ayarla
            turkey_tz = pytz.timezone('Europe/Istanbul')

            # UTC'den Türkiye saatine çevir
            turkey_time = utc_time.astimezone(turkey_tz)

            # İstenilen formatta döndür: YIL:AY:GÜN:SAAT:DAKİKA
            return turkey_time.strftime("%Y:%m:%d:%H:%M")

        except Exception as e:
            return None

    async def get_updated_cookies(self, cookies_data):
        """Güncellenmiş çerezleri al"""
        try:
            proxy_url = self.proxy_url if self.use_proxy else None
            client = Client(language="tr-TR", proxy=proxy_url)
            client.set_cookies(cookies_data)

            # Basit bir işlem yap (çerezleri güncellemek için)
            await client.user()

            # Güncellenmiş çerezleri döndür
            return client.get_cookies()

        except Exception as e:
            return None

    async def reset_proxy(self):
        """Proxy'yi sıfırla"""
        try:
            if self.reset_url:
                response = requests.get(self.reset_url, timeout=10)
                if response.status_code == 200:
                    self.log_updated.emit("🔄 Proxy sıfırlandı")
                else:
                    self.log_updated.emit(f"⚠️ Proxy sıfırlama başarısız: {response.status_code}")
        except Exception as e:
            self.log_updated.emit(f"⚠️ Proxy sıfırlama hatası: {str(e)}")

    def stop(self):
        """İşlemi durdur"""
        self.is_running = False

class YearSeparatorWindow(QWidget):
    def __init__(self, colors, return_callback):
        super().__init__()
        self.colors = colors
        self.return_callback = return_callback
        self.worker = None

        self.init_ui()
        self.setup_style()

    def init_ui(self):
        """UI'yi başlat"""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header_layout = QHBoxLayout()

        # Geri butonu
        back_btn = QPushButton("← Ana Menüye Dön")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(self.return_to_main)
        back_btn.setCursor(Qt.PointingHandCursor)

        # Başlık
        title_label = QLabel("📅 Yıl Ayırıcı")
        title_label.setObjectName("pageTitle")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Ayarlar paneli
        settings_panel = self.create_settings_panel()

        # Hesap listesi paneli
        accounts_panel = self.create_accounts_panel()

        # İşlem paneli
        operation_panel = self.create_operation_panel()

        # Layout'a ekle
        layout.addLayout(header_layout)
        layout.addWidget(settings_panel)
        layout.addWidget(accounts_panel)
        layout.addWidget(operation_panel, 1)

        self.setLayout(layout)

    def create_settings_panel(self):
        """Ayarlar panelini oluştur"""
        panel = QFrame()
        panel.setObjectName("settingsPanel")
        layout = QVBoxLayout()

        # Hesap türü seçimi
        account_group = QGroupBox("👥 Hangi hesaplara işlem yapmak istiyorsunuz?")
        account_group.setObjectName("settingsGroup")
        account_layout = QVBoxLayout()

        self.account_type_group = QButtonGroup()
        self.login_accounts_radio = QRadioButton("Giriş Yapılan Hesaplar")
        self.target_accounts_radio = QRadioButton("Hedef Hesaplar")

        self.login_accounts_radio.setChecked(True)  # Varsayılan seçim

        self.account_type_group.addButton(self.login_accounts_radio)
        self.account_type_group.addButton(self.target_accounts_radio)

        # Hesap türü değişikliğinde listbox'ı güncelle
        self.login_accounts_radio.toggled.connect(self.update_accounts_list)
        self.target_accounts_radio.toggled.connect(self.update_accounts_list)

        account_layout.addWidget(self.login_accounts_radio)
        account_layout.addWidget(self.target_accounts_radio)
        account_group.setLayout(account_layout)

        # Bekleme süresi ayarı
        wait_group = QGroupBox("⏱ Her işlem arasındaki bekleme süresi")
        wait_group.setObjectName("settingsGroup")
        wait_layout = QHBoxLayout()

        wait_label = QLabel("Saniye:")
        self.wait_spin = QSpinBox()
        self.wait_spin.setObjectName("inputField")
        self.wait_spin.setRange(1, 3600)
        self.wait_spin.setValue(5)
        self.wait_spin.setSuffix(" saniye")

        wait_layout.addWidget(wait_label)
        wait_layout.addWidget(self.wait_spin)
        wait_layout.addStretch()
        wait_group.setLayout(wait_layout)

        # Proxy ayarları
        proxy_group = QGroupBox("🌐 Proxy Ayarları")
        proxy_group.setObjectName("settingsGroup")
        proxy_layout = QVBoxLayout()

        self.proxy_enabled = QCheckBox("Proxy kullan")
        self.proxy_enabled.setObjectName("settingsCheckbox")
        self.proxy_enabled.toggled.connect(self.toggle_proxy_fields)

        # Proxy URL container
        proxy_container = QFrame()
        proxy_container_layout = QVBoxLayout()
        proxy_container_layout.setSpacing(5)
        proxy_container_layout.setContentsMargins(0, 0, 0, 0)

        proxy_label = QLabel("Proxy URL:")
        proxy_label.setObjectName("settingsLabel")
        self.proxy_entry = QLineEdit()
        self.proxy_entry.setObjectName("inputField")
        self.proxy_entry.setPlaceholderText("http://proxy:port")
        self.proxy_entry.setEnabled(False)

        proxy_container_layout.addWidget(proxy_label)
        proxy_container_layout.addWidget(self.proxy_entry)
        proxy_container.setLayout(proxy_container_layout)

        # Reset URL container
        reset_container = QFrame()
        reset_container_layout = QVBoxLayout()
        reset_container_layout.setSpacing(5)
        reset_container_layout.setContentsMargins(0, 0, 0, 0)

        reset_label = QLabel("Reset URL:")
        reset_label.setObjectName("settingsLabel")
        self.reset_url_entry = QLineEdit()
        self.reset_url_entry.setObjectName("inputField")
        self.reset_url_entry.setPlaceholderText("http://example.com/reset")
        self.reset_url_entry.setEnabled(False)

        reset_container_layout.addWidget(reset_label)
        reset_container_layout.addWidget(self.reset_url_entry)
        reset_container.setLayout(reset_container_layout)

        proxy_layout.addWidget(self.proxy_enabled)
        proxy_layout.addSpacing(10)
        proxy_layout.addWidget(proxy_container)
        proxy_layout.addSpacing(8)
        proxy_layout.addWidget(reset_container)
        proxy_group.setLayout(proxy_layout)

        # Kontrol butonları
        control_layout = QHBoxLayout()

        self.start_btn = QPushButton("🚀 İşlemi Başlat")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.clicked.connect(self.start_process)
        self.start_btn.setCursor(Qt.PointingHandCursor)

        self.stop_btn = QPushButton("⏹️ İşlemi Durdur")
        self.stop_btn.setObjectName("errorButton")
        self.stop_btn.clicked.connect(self.stop_process)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setEnabled(False)

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()

        # Layout'a ekle
        layout.addWidget(account_group)
        layout.addWidget(wait_group)
        layout.addWidget(proxy_group)
        layout.addLayout(control_layout)

        panel.setLayout(layout)
        return panel

    def create_accounts_panel(self):
        """Hesap listesi panelini oluştur"""
        panel = QFrame()
        panel.setObjectName("accountsPanel")
        layout = QVBoxLayout()

        # Başlık
        title_label = QLabel("📋 Hesap Listesi")
        title_label.setObjectName("sectionLabel")

        # Hesap listesi
        self.accounts_list = QListWidget()
        self.accounts_list.setObjectName("accountsList")
        self.accounts_list.setMaximumHeight(150)

        # Bilgi etiketi
        self.accounts_info_label = QLabel("Hesap türü seçin")
        self.accounts_info_label.setObjectName("infoLabel")

        # Layout'a ekle
        layout.addWidget(title_label)
        layout.addWidget(self.accounts_list)
        layout.addWidget(self.accounts_info_label)

        panel.setLayout(layout)
        return panel

    def create_operation_panel(self):
        """İşlem panelini oluştur"""
        panel = QFrame()
        panel.setObjectName("operationPanel")
        layout = QVBoxLayout()

        # İlerleme çubuğu
        progress_layout = QVBoxLayout()

        progress_label = QLabel("📊 İşlem İlerlemesi")
        progress_label.setObjectName("sectionLabel")

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setValue(0)

        self.progress_text = QLabel("Hazır")
        self.progress_text.setObjectName("progressText")
        self.progress_text.setAlignment(Qt.AlignCenter)

        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_text)

        # Log alanı
        log_label = QLabel("📝 İşlem Kayıtları")
        log_label.setObjectName("sectionLabel")

        self.log_text = QTextEdit()
        self.log_text.setObjectName("logArea")
        self.log_text.setReadOnly(True)

        # Layout'a ekle
        layout.addLayout(progress_layout)
        layout.addWidget(log_label)
        layout.addWidget(self.log_text, 1)

        panel.setLayout(layout)
        return panel

    def toggle_proxy_fields(self):
        """Proxy alanlarını aktif/pasif yap"""
        enabled = self.proxy_enabled.isChecked()
        self.proxy_entry.setEnabled(enabled)
        self.reset_url_entry.setEnabled(enabled)

    def update_accounts_list(self):
        """Hesap listesini güncelle"""
        self.accounts_list.clear()

        if self.login_accounts_radio.isChecked():
            # Giriş yapılan hesapları al
            accounts = user_manager.get_all_users()
            account_type = "giriş yapılan"
        else:
            # Hedef hesapları al
            accounts = mysql_manager.get_all_targets()
            account_type = "hedef"

        if accounts:
            for account in accounts:
                username = account.get('kullanici_adi', '')

                # Twitter oluşturma tarihi kontrolü
                if self.login_accounts_radio.isChecked():
                    twitter_date = user_manager.get_user_twitter_creation_date(username)
                else:
                    twitter_date = mysql_manager.get_target_creation_date(username)

                # Liste öğesi oluştur
                if twitter_date:
                    item_text = f"✅ {username} - Twitter tarihi: {twitter_date}"
                else:
                    item_text = f"❌ {username} - Twitter tarihi: Bilinmiyor"

                item = QListWidgetItem(item_text)

                # Renk ayarla
                if twitter_date:
                    item.setForeground(QColor(self.colors.get('success', '#4CAF50')))
                else:
                    item.setForeground(QColor(self.colors.get('error', '#F44336')))

                self.accounts_list.addItem(item)

            self.accounts_info_label.setText(f"📊 {len(accounts)} {account_type} hesap bulundu")
        else:
            self.accounts_info_label.setText(f"⚠️ Hiç {account_type} hesap bulunamadı")

    def init_ui(self):
        """UI'yi başlat"""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header_layout = QHBoxLayout()

        # Geri butonu
        back_btn = QPushButton("← Ana Menüye Dön")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(self.return_to_main)
        back_btn.setCursor(Qt.PointingHandCursor)

        # Başlık
        title_label = QLabel("📅 Yıl Ayırıcı")
        title_label.setObjectName("pageTitle")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Ayarlar paneli
        settings_panel = self.create_settings_panel()

        # Hesap listesi paneli
        accounts_panel = self.create_accounts_panel()

        # İşlem paneli
        operation_panel = self.create_operation_panel()

        # Layout'a ekle
        layout.addLayout(header_layout)
        layout.addWidget(settings_panel)
        layout.addWidget(accounts_panel)
        layout.addWidget(operation_panel, 1)

        self.setLayout(layout)

        # İlk yükleme
        self.update_accounts_list()

    def start_process(self):
        """İşlemi başlat"""
        # Ayarları al
        account_type = 'login' if self.login_accounts_radio.isChecked() else 'target'
        wait_seconds = self.wait_spin.value()
        use_proxy = self.proxy_enabled.isChecked()
        proxy_url = self.proxy_entry.text().strip() if use_proxy else None
        reset_url = self.reset_url_entry.text().strip() if use_proxy else None

        # Proxy kontrolü
        if use_proxy and not proxy_url:
            self.show_warning("Proxy URL'si boş olamaz!")
            return

        # UI'yi güncelle
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()

        # Worker thread'i başlat
        self.worker = YearSeparatorWorker(account_type, wait_seconds, use_proxy, proxy_url, reset_url)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_updated.connect(self.add_log)
        self.worker.finished.connect(self.process_finished)
        self.worker.start()

        self.add_log("🚀 Yıl Ayırıcı işlemi başlatıldı...")

    def stop_process(self):
        """İşlemi durdur"""
        if self.worker:
            self.worker.stop()
            self.add_log("⏹️ İşlem durdurma talebi gönderildi...")

    def update_progress(self, current, total):
        """İlerlemeyi güncelle"""
        progress = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        self.progress_text.setText(f"{current}/{total} hesap işlendi (%{progress})")

    def add_log(self, message):
        """Log mesajı ekle"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        self.log_text.ensureCursorVisible()

    def process_finished(self, success):
        """İşlem tamamlandı"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if success:
            self.add_log("✅ Tüm işlemler başarıyla tamamlandı!")
            self.show_info("İşlem başarıyla tamamlandı!")
        else:
            self.add_log("❌ İşlem hata ile sonlandı!")

    def setup_style(self):
        """Stil ayarlarını uygula"""
        style = f"""
        QWidget {{
            background: {self.colors['background']};
            color: {self.colors['text_primary']};
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
        }}

        #pageTitle {{
            font-size: 28px;
            font-weight: 700;
            color: {self.colors['text_primary']};
            margin: 10px 0px;
        }}

        #settingsPanel {{
            background: {self.colors['card_bg']};
            border: 1px solid {self.colors['border']};
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0px;
        }}

        #operationPanel {{
            background: {self.colors['card_bg']};
            border: 1px solid {self.colors['border']};
            border-radius: 12px;
            padding: 20px;
        }}

        #settingsGroup {{
            font-size: 14px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            border: 2px solid {self.colors['border']};
            border-radius: 8px;
            margin: 5px;
            padding-top: 15px;
        }}

        #settingsGroup::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0px 8px;
            background: {self.colors['card_bg']};
            color: {self.colors['text_primary']};
        }}

        #inputField {{
            background: {self.colors['background']};
            border: 2px solid {self.colors['border']};
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
            color: {self.colors['text_primary']};
        }}

        #inputField:focus {{
            border-color: {self.colors['primary']};
            background: {self.colors['background']};
        }}

        #settingsCheckbox {{
            font-size: 14px;
            color: {self.colors['text_primary']};
            font-weight: 500;
            margin-bottom: 5px;
        }}

        #settingsLabel {{
            font-size: 12px;
            color: {self.colors['text_secondary']};
            font-weight: 500;
            margin-bottom: 3px;
        }}

        #primaryButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary']}, 
                stop:1 {self.colors['primary_end']});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
        }}

        #primaryButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary_hover']}, 
                stop:1 {self.colors['primary']});
        }}

        #primaryButton:disabled {{
            background: {self.colors['text_light']};
            color: white;
        }}

        #errorButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['error']}, 
                stop:1 {self.colors['error_hover']});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
        }}

        #errorButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['error_hover']}, 
                stop:1 {self.colors['error']});
        }}

        #errorButton:disabled {{
            background: {self.colors['text_light']};
            color: white;
        }}

        #sectionLabel {{
            font-size: 16px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            margin: 10px 0px 5px 0px;
        }}

        #progressBar {{
            background: {self.colors['background_alt']};
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            text-align: center;
            font-size: 12px;
            font-weight: 600;
        }}

        #progressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self.colors['primary']}, 
                stop:1 {self.colors['primary_end']});
            border-radius: 6px;
        }}

        #progressText {{
            font-size: 14px;
            color: {self.colors['text_secondary']};
            font-weight: 500;
            margin: 5px 0px;
        }}

        #logArea {{
            background: {self.colors['background']};
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            color: {self.colors['text_primary']};
            padding: 10px;
        }}

        #accountsPanel {{
            background: {self.colors['card_bg']};
            border: 1px solid {self.colors['border']};
            border-radius: 12px;
            padding: 15px;
            margin: 10px 0px;
        }}

        #accountsList {{
            background: {self.colors['background']};
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            padding: 5px;
            font-size: 12px;
            selection-background-color: {self.colors['primary']};
            selection-color: white;
        }}

        #infoLabel {{
            font-size: 12px;
            color: {self.colors['text_secondary']};
            font-weight: 500;
            margin-top: 5px;
        }}

        #backButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #6C757D, 
                stop:1 #5A6268);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 14px 24px;
            font-size: 15px;
            font-weight: 600;
        }}

        #backButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5A6268, 
                stop:1 #495057);
        }}

        QRadioButton {{
            font-size: 14px;
            color: {self.colors['text_primary']};
            font-weight: 500;
            padding: 5px;
        }}

        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
        }}

        QRadioButton::indicator:unchecked {{
            border: 2px solid {self.colors['border']};
            border-radius: 8px;
            background: {self.colors['background']};
        }}

        QRadioButton::indicator:checked {{
            border: 2px solid {self.colors['primary']};
            border-radius: 8px;
            background: {self.colors['primary']};
        }}
        """

        self.setStyleSheet(style)

    def return_to_main(self):
        """Ana menüye dön"""
        # İşlem devam ediyorsa durdur
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self.return_callback()

    def show_info(self, message):
        """Bilgi mesajı göster"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("✅ Bilgi")
        msg.setText(message)
        msg.exec_()

    def show_warning(self, message):
        """Uyarı mesajı göster"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("⚠️ Uyarı")
        msg.setText(message)
        msg.exec_()

    def show_error(self, message):
        """Hata mesajı göster"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("❌ Hata")
        msg.setText(message)
        msg.exec_()