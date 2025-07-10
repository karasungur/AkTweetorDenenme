from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QMessageBox, QSpinBox, QGroupBox,
                             QRadioButton, QProgressBar, QTextEdit, QButtonGroup,
                             QCheckBox, QLineEdit, QListWidget, QListWidgetItem,
                             QScrollArea, QGridLayout, QSplitter)
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
                # Çerez verilerini al
                raw_cookies = user_manager.get_user_cookies(random_user.get('kullanici_adi'))

                # MySQL'den gelen çerezleri uygun formata çevir
                cookies_data = None
                if raw_cookies:
                    cookies_data = {}
                    # Çerez isimlerini kontrol et ve değerleri ata
                    target_cookies = [
                        'auth_token', 'gt', 'guest_id', 'twid', 'lang', '__cf_bm',
                        'att', 'ct0', 'd_prefs', 'dnt', 'guest_id_ads', 
                        'guest_id_marketing', 'kdt', 'personalization_id'
                    ]

                    for cookie_name in target_cookies:
                        if cookie_name in raw_cookies and raw_cookies[cookie_name]:
                            cookies_data[cookie_name] = raw_cookies[cookie_name]
                        elif cookie_name in ['d_prefs', 'dnt']:
                            # d_prefs ve dnt null ise "1" değerini ata
                            cookies_data[cookie_name] = "1"

                    # En az bir önemli çerez var mı kontrol et
                    essential_cookies = ['auth_token', 'ct0', 'guest_id']
                    if not any(cookie in cookies_data for cookie in essential_cookies):
                        cookies_data = None

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
        # Ana layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Header
        header_frame = self.create_header()
        main_layout.addWidget(header_frame)

        # Ana splitter - sol ve sağ paneller
        main_splitter = QSplitter(Qt.Horizontal)

        # Sol panel - Ayarlar ve hesap listesi
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)

        # Sağ panel - İşlem ve log
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)

        # Splitter oranları
        main_splitter.setSizes([500, 600])

        main_layout.addWidget(main_splitter, 1)
        self.setLayout(main_layout)

        # İlk yükleme
        self.update_accounts_list()

    def create_header(self):
        """Header panelini oluştur"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setFixedHeight(60)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 10, 15, 10)

        # Geri butonu
        back_btn = QPushButton("← Ana Menü")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(self.return_to_main)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFixedSize(120, 40)

        # Başlık
        title_label = QLabel("📅 Yıl Ayırıcı")
        title_label.setObjectName("pageTitle")
        title_label.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        header_frame.setLayout(header_layout)
        return header_frame

    def create_left_panel(self):
        """Sol paneli oluştur - Ayarlar ve hesap listesi"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Ayarlar paneli
        settings_frame = QFrame()
        settings_frame.setObjectName("settingsFrame")
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(15, 15, 15, 15)
        settings_layout.setSpacing(10)

        # Başlık
        settings_title = QLabel("⚙️ Ayarlar")
        settings_title.setObjectName("sectionTitle")
        settings_layout.addWidget(settings_title)

        # Hesap türü seçimi - Kompakt
        account_frame = QFrame()
        account_frame.setObjectName("compactFrame")
        account_layout = QVBoxLayout()
        account_layout.setContentsMargins(10, 8, 10, 8)

        account_label = QLabel("👥 Hesap Türü:")
        account_label.setObjectName("compactLabel")
        account_layout.addWidget(account_label)

        # Radio butonlar yan yana
        radio_layout = QHBoxLayout()
        self.account_type_group = QButtonGroup()
        self.login_accounts_radio = QRadioButton("Giriş Yapılan")
        self.target_accounts_radio = QRadioButton("Hedef Hesaplar")
        self.login_accounts_radio.setChecked(True)

        self.account_type_group.addButton(self.login_accounts_radio)
        self.account_type_group.addButton(self.target_accounts_radio)

        self.login_accounts_radio.toggled.connect(self.update_accounts_list)
        self.target_accounts_radio.toggled.connect(self.update_accounts_list)

        radio_layout.addWidget(self.login_accounts_radio)
        radio_layout.addWidget(self.target_accounts_radio)
        radio_layout.addStretch()

        account_layout.addLayout(radio_layout)
        account_frame.setLayout(account_layout)
        settings_layout.addWidget(account_frame)

        # Bekleme süresi - Kompakt
        wait_frame = QFrame()
        wait_frame.setObjectName("compactFrame")
        wait_layout = QHBoxLayout()
        wait_layout.setContentsMargins(10, 8, 10, 8)

        wait_label = QLabel("⏱ Bekleme:")
        wait_label.setObjectName("compactLabel")
        self.wait_spin = QSpinBox()
        self.wait_spin.setObjectName("compactInput")
        self.wait_spin.setRange(1, 3600)
        self.wait_spin.setValue(5)
        self.wait_spin.setSuffix(" sn")
        self.wait_spin.setFixedWidth(80)

        wait_layout.addWidget(wait_label)
        wait_layout.addWidget(self.wait_spin)
        wait_layout.addStretch()

        wait_frame.setLayout(wait_layout)
        settings_layout.addWidget(wait_frame)

        # Proxy ayarları - Kompakt
        proxy_frame = QFrame()
        proxy_frame.setObjectName("compactFrame")
        proxy_layout = QVBoxLayout()
        proxy_layout.setContentsMargins(10, 8, 10, 8)

        self.proxy_enabled = QCheckBox("🌐 Proxy Kullan")
        self.proxy_enabled.setObjectName("compactCheckbox")
        self.proxy_enabled.toggled.connect(self.toggle_proxy_fields)
        proxy_layout.addWidget(self.proxy_enabled)

        # Proxy URL
        proxy_url_layout = QHBoxLayout()
        proxy_url_label = QLabel("URL:")
        proxy_url_label.setObjectName("miniLabel")
        self.proxy_entry = QLineEdit()
        self.proxy_entry.setObjectName("compactInput")
        self.proxy_entry.setPlaceholderText("http://proxy:port")
        self.proxy_entry.setEnabled(False)

        proxy_url_layout.addWidget(proxy_url_label)
        proxy_url_layout.addWidget(self.proxy_entry)
        proxy_layout.addLayout(proxy_url_layout)

        # Reset URL
        reset_url_layout = QHBoxLayout()
        reset_url_label = QLabel("Reset:")
        reset_url_label.setObjectName("miniLabel")
        self.reset_url_entry = QLineEdit()
        self.reset_url_entry.setObjectName("compactInput")
        self.reset_url_entry.setPlaceholderText("http://example.com/reset")
        self.reset_url_entry.setEnabled(False)

        reset_url_layout.addWidget(reset_url_label)
        reset_url_layout.addWidget(self.reset_url_entry)
        proxy_layout.addLayout(reset_url_layout)

        proxy_frame.setLayout(proxy_layout)
        settings_layout.addWidget(proxy_frame)

        # Kontrol butonları - Kompakt
        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)

        self.start_btn = QPushButton("🚀 Başlat")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.clicked.connect(self.start_process)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setFixedHeight(35)

        self.stop_btn = QPushButton("⏹️ Durdur")
        self.stop_btn.setObjectName("errorButton")
        self.stop_btn.clicked.connect(self.stop_process)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setFixedHeight(35)

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)

        settings_layout.addLayout(control_layout)
        settings_frame.setLayout(settings_layout)

        # Hesap listesi paneli
        accounts_frame = QFrame()
        accounts_frame.setObjectName("accountsFrame")
        accounts_layout = QVBoxLayout()
        accounts_layout.setContentsMargins(15, 15, 15, 15)

        # Başlık ve istatistik
        accounts_title = QLabel("📋 Hesap Listesi")
        accounts_title.setObjectName("sectionTitle")
        accounts_layout.addWidget(accounts_title)

        self.accounts_info_label = QLabel("Hesap türü seçin")
        self.accounts_info_label.setObjectName("infoLabel")
        accounts_layout.addWidget(self.accounts_info_label)

        # Hesap listesi
        self.accounts_list = QListWidget()
        self.accounts_list.setObjectName("compactList")
        accounts_layout.addWidget(self.accounts_list)

        accounts_frame.setLayout(accounts_layout)

        # Sol panel layout'u
        left_layout.addWidget(settings_frame)
        left_layout.addWidget(accounts_frame, 1)

        left_widget.setLayout(left_layout)
        return left_widget

    def create_right_panel(self):
        """Sağ paneli oluştur - İşlem ve log"""
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # İlerleme paneli
        progress_frame = QFrame()
        progress_frame.setObjectName("progressFrame")
        progress_layout = QVBoxLayout()
        progress_layout.setContentsMargins(15, 15, 15, 15)

        progress_title = QLabel("📊 İşlem İlerlemesi")
        progress_title.setObjectName("sectionTitle")
        progress_layout.addWidget(progress_title)

        # İlerleme çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("modernProgress")
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(25)
        progress_layout.addWidget(self.progress_bar)

        # İlerleme metni
        self.progress_text = QLabel("Hazır")
        self.progress_text.setObjectName("progressText")
        self.progress_text.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_text)

        progress_frame.setLayout(progress_layout)

        # Log paneli
        log_frame = QFrame()
        log_frame.setObjectName("logFrame")
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(15, 15, 15, 15)

        log_title = QLabel("📝 İşlem Kayıtları")
        log_title.setObjectName("sectionTitle")
        log_layout.addWidget(log_title)

        # Log alanı
        self.log_text = QTextEdit()
        self.log_text.setObjectName("modernLog")
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        log_frame.setLayout(log_layout)

        # Sağ panel layout'u
        right_layout.addWidget(progress_frame)
        right_layout.addWidget(log_frame, 1)

        right_widget.setLayout(right_layout)
        return right_widget

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
                    item_text = f"✅ {username} - {twitter_date}"
                else:
                    item_text = f"❌ {username} - Tarih yok"

                item = QListWidgetItem(item_text)

                # Renk ayarla
                if twitter_date:
                    item.setForeground(QColor(self.colors.get('success', '#4CAF50')))
                else:
                    item.setForeground(QColor(self.colors.get('error', '#F44336')))

                self.accounts_list.addItem(item)

            self.accounts_info_label.setText(f"📊 {len(accounts)} {account_type} hesap")
        else:
            self.accounts_info_label.setText(f"⚠️ Hiç {account_type} hesap yok")

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
        self.progress_text.setText(f"{current}/{total} hesap (%{progress})")

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
        """Kompakt ve modern stil"""
        style = f"""
        QWidget {{
            background: {self.colors['background']};
            color: {self.colors['text_primary']};
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
        }}

        #headerFrame {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['card_bg']}, 
                stop:1 {self.colors['background_alt']});
            border-bottom: 1px solid {self.colors['border']};
        }}

        #pageTitle {{
            font-size: 24px;
            font-weight: 700;
            color: {self.colors['text_primary']};
        }}

        #settingsFrame, #accountsFrame, #progressFrame, #logFrame {{
            background: {self.colors['card_bg']};
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
        }}

        #sectionTitle {{
            font-size: 16px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            margin-bottom: 8px;
        }}

        #compactFrame {{
            background: {self.colors['background_alt']};
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            margin: 2px 0px;
        }}

        #compactLabel {{
            font-size: 13px;
            font-weight: 600;
            color: {self.colors['text_primary']};
        }}

        #miniLabel {{
            font-size: 11px;
            color: {self.colors['text_secondary']};
            min-width: 40px;
        }}

        #compactInput {{
            background: {self.colors['background']};
            border: 1px solid {self.colors['border']};
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 12px;
            color: {self.colors['text_primary']};
        }}

        #compactInput:focus {{
            border-color: {self.colors['primary']};
        }}

        #compactCheckbox {{
            font-size: 12px;
            color: {self.colors['text_primary']};
            font-weight: 500;
        }}

        #compactList {{
            background: {self.colors['background']};
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            font-size: 11px;
            selection-background-color: {self.colors['primary']};
            selection-color: white;
        }}

        #modernProgress {{
            background: {self.colors['background_alt']};
            border: 1px solid {self.colors['border']};
            border-radius: 12px;
            text-align: center;
            font-size: 11px;
            font-weight: 600;
        }}

        #modernProgress::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self.colors['primary']}, 
                stop:1 {self.colors['primary_end']});
            border-radius: 10px;
        }}

        #progressText {{
            font-size: 12px;
            color: {self.colors['text_secondary']};
            font-weight: 500;
            margin: 5px 0px;
        }}

        #modernLog {{
            background: {self.colors['background']};
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 11px;
            color: {self.colors['text_primary']};
            padding: 8px;
        }}

        #infoLabel {{
            font-size: 11px;
            color: {self.colors['text_secondary']};
            font-weight: 500;
        }}

        #primaryButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary']}, 
                stop:1 {self.colors['primary_end']});
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
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
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
        }}

        #errorButton:disabled {{
            background: {self.colors['text_light']};
            color: white;
        }}

        #backButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #6C757D, 
                stop:1 #5A6268);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
        }}

        #backButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5A6268, 
                stop:1 #495057);
        }}

        QRadioButton {{
            font-size: 12px;
            color: {self.colors['text_primary']};
            font-weight: 500;
        }}

        QRadioButton::indicator {{
            width: 14px;
            height: 14px;
        }}

        QRadioButton::indicator:unchecked {{
            border: 2px solid {self.colors['border']};
            border-radius: 7px;
            background: {self.colors['background']};
        }}

        QRadioButton::indicator:checked {{
            border: 2px solid {self.colors['primary']};
            border-radius: 7px;
            background: {self.colors['primary']};
        }}

        QSplitter::handle {{
            background: {self.colors['border']};
            width: 2px;
        }}

        QSplitter::handle:hover {{
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