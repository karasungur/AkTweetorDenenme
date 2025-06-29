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
        self.normal_ip = "Alınıyor..."
        self.browser_ip = "Tarayıcı açılmadı"
        self.drivers = []

        self.init_ui()
        self.setup_style()
        self.load_profiles()
        self.get_initial_ip()  # Sadece bir kez IP al

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

        # Normal IP
        normal_ip_layout = QHBoxLayout()
        normal_ip_label = QLabel("🖥️ Normal IP:")
        normal_ip_label.setObjectName("ipLabel")

        self.normal_ip_display = QLabel(self.normal_ip)
        self.normal_ip_display.setObjectName("ipDisplay")

        normal_ip_layout.addWidget(normal_ip_label)
        normal_ip_layout.addWidget(self.normal_ip_display)
        normal_ip_layout.addStretch()

        # Tarayıcı IP
        browser_ip_layout = QHBoxLayout()
        browser_ip_label = QLabel("🌐 Tarayıcı IP:")
        browser_ip_label.setObjectName("ipLabel")

        self.browser_ip_display = QLabel(self.browser_ip)
        self.browser_ip_display.setObjectName("browserIpDisplay")

        browser_ip_layout.addWidget(browser_ip_label)
        browser_ip_layout.addWidget(self.browser_ip_display)
        browser_ip_layout.addStretch()

        # IP değiştir butonu
        ip_change_btn = QPushButton("🔄 IP Değiştir")
        ip_change_btn.setObjectName("secondaryButton")
        ip_change_btn.clicked.connect(self.change_ip)
        ip_change_btn.setCursor(Qt.PointingHandCursor)

        ip_layout.addLayout(normal_ip_layout)
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
            background-color: {self.colors['secondary_hover']};
        }}

        #deleteButton {{
            background-color: {self.colors['error']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
            margin-right: 10px;
        }}

        #deleteButton:hover {{
            background-color: #B71C1C;
        }}

        #primaryButton {{
            background-color: {self.colors['primary']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 13px;
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
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 600;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
        }}

        #secondaryButton:hover {{
            background-color: {self.colors['secondary_hover']};
        }}

        #profileScrollArea {{
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            background-color: white;
        }}

        #profileItem {{
            background-color: white;
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            padding: 12px;
            margin: 2px;
        }}

        #profileItem:hover {{
            background-color: {self.colors['card_bg']};
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

        #ipDisplay {{
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

        if os.path.exists(profiles_dir):
            try:
                for item in os.listdir(profiles_dir):
                    item_path = os.path.join(profiles_dir, item)
                    if os.path.isdir(item_path):
                        self.profiles.append(item)
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
                    mysql_success = user_manager.delete_user(profile)
                    if mysql_success:
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

            # Proxy ayarı
            if self.proxy_enabled.isChecked() and self.proxy_entry.text():
                proxy = self.proxy_entry.text()
                options.add_argument(f"--proxy-server={proxy}")

            # Diğer ayarlar
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-default-apps")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            service = Service("chromedriver.exe")
            service.hide_command_prompt_window = True

            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Twitter'a git
            driver.get("https://x.com/")

            # Tarayıcının IP adresini bir kez kontrol et (5 saniye bekle)
            QTimer.singleShot(5000, lambda: self.check_browser_ip_once(driver))

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
                    self.check_browser_ip_once(driver)

                    self.show_info(f"{driver_info['profile']} için IP sıfırlandı.")

                except Exception as e:
                    self.show_error(f"IP sıfırlama hatası: {str(e)}")
        else:
            self.show_info("Açık tarayıcı bulunamadı.")

    def get_initial_ip(self):
        """Bilgisayarın normal IP adresini bir kez al"""
        def get_ip_threaded():
            try:
                print("🌐 Normal IP adresi alınıyor...")
                response = requests.get("https://api.ipify.org", timeout=15)
                ip = response.text.strip()

                # Ana thread'de UI güncelle
                def update_ui():
                    self.set_normal_ip(ip)
                    print(f"✅ Normal IP adresi alındı: {ip}")

                QTimer.singleShot(0, update_ui)

            except Exception as e:
                def update_error():
                    self.set_normal_ip("Bağlantı hatası")
                    print(f"❌ Normal IP alma hatası: {str(e)}")

                QTimer.singleShot(0, update_error)

        thread = threading.Thread(target=get_ip_threaded, daemon=True)
        thread.start()

    def set_normal_ip(self, ip):
        """Normal IP'yi set et (Ana thread'de çalışır)"""
        self.normal_ip = ip
        if hasattr(self, 'normal_ip_display'):
            self.normal_ip_display.setText(self.normal_ip)

    def set_browser_ip(self, ip):
        """Tarayıcı IP'sini set et (Ana thread'de çalışır)"""
        self.browser_ip = ip
        if hasattr(self, 'browser_ip_display'):
            self.browser_ip_display.setText(self.browser_ip)

    def check_browser_ip_once(self, driver):
        """Tarayıcının IP adresini bir kez kontrol et"""
        def ip_check_thread():
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

                # UI'yi güncelle
                def update_browser_ip():
                    self.set_browser_ip(browser_ip)
                    print(f"✅ Tarayıcı IP adresi: {browser_ip}")

                QTimer.singleShot(0, update_browser_ip)

            except Exception as e:
                def update_error():
                    self.set_browser_ip("IP alınamadı")
                    print(f"❌ Tarayıcı IP kontrol hatası: {str(e)}")

                QTimer.singleShot(0, update_error)

        # Ayrı thread'de çalıştır
        thread = threading.Thread(target=ip_check_thread, daemon=True)
        thread.start()

    def return_to_main(self):
        """Ana menüye dön"""
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
