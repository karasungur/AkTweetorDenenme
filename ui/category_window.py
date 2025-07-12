from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QMessageBox, QListWidget, QListWidgetItem,
                             QComboBox, QLineEdit, QTextEdit, QGroupBox, QSplitter,
                             QTreeWidget, QTreeWidgetItem, QFileDialog, QProgressBar,
                             QTabWidget, QGridLayout, QScrollArea, QButtonGroup, QRadioButton,
                             QCheckBox, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
from database.mysql import mysql_manager
from database.user_manager import user_manager
import os

class AddCategoryDialog(QDialog):
    """Kategori ekleme dialog'u"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Kategori Ekle")
        self.setModal(True)
        self.resize(400, 200)

        layout = QVBoxLayout()

        # Kategori adı
        layout.addWidget(QLabel("Kategori Adı:"))
        self.category_name_edit = QLineEdit()
        layout.addWidget(self.category_name_edit)

        # Kategori türü
        layout.addWidget(QLabel("Kategori Türü:"))
        self.category_type_combo = QComboBox()
        self.category_type_combo.addItems(["profil", "icerik"])
        layout.addWidget(self.category_type_combo)

        # Açıklama
        layout.addWidget(QLabel("Açıklama (opsiyonel):"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        layout.addWidget(self.description_edit)

        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_category_data(self):
        return {
            'kategori_adi': self.category_name_edit.text().strip(),
            'kategori_turu': self.category_type_combo.currentText(),
            'aciklama': self.description_edit.toPlainText().strip() or None
        }

class CategoryWindow(QWidget):
    def __init__(self, colors, return_callback):
        super().__init__()
        self.colors = colors
        self.return_callback = return_callback
        self.selected_account_type = 'giris_yapilan'
        self.accounts = []
        self.categories = []
        self.selected_accounts = set()
        self.current_view_account = None  # Kategorileri görüntülenen hesap

        self.init_ui()
        self.setup_style()

    def init_ui(self):
        """UI'yi başlat"""
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Ana Menüye Dön")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(self.return_to_main)
        back_btn.setCursor(Qt.PointingHandCursor)

        title_label = QLabel("🧩 Kategori Yöneticisi")
        title_label.setObjectName("pageTitle")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Üst araç çubuğu
        toolbar_layout = QHBoxLayout()

        # İçe aktar butonları
        import_categories_btn = QPushButton("📁 Kategori Dosyası İçe Aktar")
        import_categories_btn.setObjectName("importButton")
        import_categories_btn.clicked.connect(self.import_categories_file)

        import_account_categories_btn = QPushButton("📁 Hesap Kategorileri İçe Aktar")
        import_account_categories_btn.setObjectName("importButton")
        import_account_categories_btn.clicked.connect(self.import_account_categories_file)

        # Kategori yönetimi
        add_category_btn = QPushButton("➕ Yeni Kategori Ekle")
        add_category_btn.setObjectName("addButton")
        add_category_btn.clicked.connect(self.show_add_category_dialog)

        toolbar_layout.addWidget(import_categories_btn)
        toolbar_layout.addWidget(import_account_categories_btn)
        toolbar_layout.addWidget(add_category_btn)
        toolbar_layout.addStretch()

        # Hesap türü seçimi
        account_type_frame = self.create_account_type_selection()

        # Ana splitter
        main_splitter = QSplitter(Qt.Horizontal)

        # Sol panel - Hesap listesi
        left_panel = self.create_accounts_panel()
        main_splitter.addWidget(left_panel)

        # Sağ panel - Kategori atama
        right_panel = self.create_categories_panel()
        main_splitter.addWidget(right_panel)

        main_splitter.setSizes([450, 650])

        # Layout'a ekle
        layout.addLayout(header_layout)
        layout.addLayout(toolbar_layout)
        layout.addWidget(account_type_frame)
        layout.addWidget(main_splitter, 1)

        self.setLayout(layout)

        # İlk yükleme
        self.load_categories()
        self.load_accounts()

    def create_account_type_selection(self):
        """Hesap türü seçimi paneli"""
        frame = QFrame()
        frame.setObjectName("accountTypeFrame")
        layout = QHBoxLayout()

        question_label = QLabel("Hangi hesaplara işlem yapmak istiyorsunuz?")
        question_label.setObjectName("questionLabel")

        self.account_type_group = QButtonGroup()

        login_radio = QRadioButton("🔐 Giriş Yapılan Hesaplar")
        login_radio.setObjectName("accountTypeRadio")
        login_radio.setChecked(True)
        self.account_type_group.addButton(login_radio, 0)

        target_radio = QRadioButton("🎯 Hedef Hesaplar")
        target_radio.setObjectName("accountTypeRadio")
        self.account_type_group.addButton(target_radio, 1)

        self.account_type_group.buttonToggled.connect(self.on_account_type_changed)

        layout.addWidget(question_label)
        layout.addStretch()
        layout.addWidget(login_radio)
        layout.addSpacing(20)
        layout.addWidget(target_radio)
        layout.addStretch()

        frame.setLayout(layout)
        return frame

    def create_accounts_panel(self):
        """Hesap listesi paneli"""
        panel = QGroupBox("👥 Hesap Listesi")
        panel.setObjectName("accountsPanel")
        layout = QVBoxLayout()

        # Arama çubuğu
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Hesap adı arayın...")
        self.search_edit.textChanged.connect(self.filter_accounts)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)

        # Kontroller
        controls_layout = QHBoxLayout()

        self.select_all_checkbox = QCheckBox("Tümünü Seç")
        self.select_all_checkbox.setObjectName("selectAllCheckbox")
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)

        self.account_count_label = QLabel("0 hesap")
        self.account_count_label.setObjectName("countLabel")

        refresh_btn = QPushButton("🔄")
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.clicked.connect(self.load_accounts)
        refresh_btn.setToolTip("Hesapları Yenile")

        controls_layout.addWidget(self.select_all_checkbox)
        controls_layout.addWidget(self.account_count_label)
        controls_layout.addStretch()
        controls_layout.addWidget(refresh_btn)

        # Hesap listesi
        self.accounts_list = QListWidget()
        self.accounts_list.setObjectName("accountsList")
        self.accounts_list.itemClicked.connect(self.on_account_clicked)
        self.accounts_list.itemChanged.connect(self.on_account_item_changed)

        layout.addLayout(search_layout)
        layout.addLayout(controls_layout)
        layout.addWidget(self.accounts_list, 1)

        panel.setLayout(layout)
        return panel

    def create_categories_panel(self):
        """Kategori atama paneli"""
        panel = QGroupBox("🏷️ Kategori Yönetimi")
        panel.setObjectName("categoriesPanel")
        layout = QVBoxLayout()

        # Durum bilgisi
        self.status_label = QLabel("Hesap seçilmedi")
        self.status_label.setObjectName("statusLabel")

        # Tab widget
        self.category_tabs = QTabWidget()

        # Profil kategorileri tab'ı
        profile_tab = self.create_profile_categories_tab()
        self.category_tabs.addTab(profile_tab, "👤 Profil")

        # İçerik kategorileri tab'ı
        content_tab = self.create_content_categories_tab()
        self.category_tabs.addTab(content_tab, "📝 İçerik")

        # Alt kontroller
        controls_layout = QHBoxLayout()

        clear_btn = QPushButton("🗑️ Temizle")
        clear_btn.setObjectName("clearButton")
        clear_btn.clicked.connect(self.clear_selections)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.setObjectName("saveButton")
        save_btn.clicked.connect(self.save_categories)

        controls_layout.addWidget(clear_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(save_btn)

        layout.addWidget(self.status_label)
        layout.addWidget(self.category_tabs, 1)
        layout.addLayout(controls_layout)

        panel.setLayout(layout)
        return panel

    def create_profile_categories_tab(self):
        """Profil kategorileri tab'ı"""
        widget = QWidget()
        layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.profile_layout = QVBoxLayout()

        self.profile_categories = {}
        self.load_profile_categories()

        scroll_widget.setLayout(self.profile_layout)
        scroll_area.setWidget(scroll_widget)

        layout.addWidget(scroll_area)
        widget.setLayout(layout)
        return widget

    def create_content_categories_tab(self):
        """İçerik kategorileri tab'ı"""
        widget = QWidget()
        layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.content_layout = QVBoxLayout()

        self.content_categories = {}
        self.load_content_categories()

        scroll_widget.setLayout(self.content_layout)
        scroll_area.setWidget(scroll_widget)

        layout.addWidget(scroll_area)
        widget.setLayout(layout)
        return widget

    def load_profile_categories(self):
        """Profil kategorilerini yükle"""
        # Önceki widget'ları temizle
        for i in reversed(range(self.profile_layout.count())):
            child = self.profile_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        self.profile_categories.clear()

        # Kategorileri getir
        categories = mysql_manager.get_categories('profil')

        for category in categories:
            kategori_adi = category['kategori_adi']

            # Kategori frame'i oluştur
            frame = QFrame()
            frame.setObjectName("categoryFrame")
            frame_layout = QVBoxLayout()

            # Kategori başlığı
            label = QLabel(f"📋 {kategori_adi}")
            label.setObjectName("categoryLabel")
            frame_layout.addWidget(label)

            # Değer girişi
            if kategori_adi in ['Yaş Grubu', 'Cinsiyet']:
                # Dropdown
                combo = QComboBox()
                if kategori_adi == 'Yaş Grubu':
                    combo.addItems(['', 'Genç (18-30)', 'Orta yaş (31-50)', 'Yaşlı (50+)'])
                elif kategori_adi == 'Cinsiyet':
                    combo.addItems(['', 'Erkek', 'Kadın', 'Belirtmeyen'])
                self.profile_categories[kategori_adi] = combo
                frame_layout.addWidget(combo)
            else:
                # Text input
                line_edit = QLineEdit()
                line_edit.setPlaceholderText(f"{kategori_adi} değerini girin...")
                self.profile_categories[kategori_adi] = line_edit
                frame_layout.addWidget(line_edit)

            frame.setLayout(frame_layout)
            self.profile_layout.addWidget(frame)

        self.profile_layout.addStretch()

    def load_content_categories(self):
        """İçerik kategorilerini yükle"""
        # Önceki widget'ları temizle
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        self.content_categories.clear()

        # Kategorileri getir
        categories = mysql_manager.get_categories('icerik')

        for category in categories:
            kategori_adi = category['kategori_adi']

            # Checkbox oluştur
            checkbox = QCheckBox(f"📂 {kategori_adi}")
            checkbox.setObjectName("contentCheckbox")
            self.content_categories[kategori_adi] = checkbox
            self.content_layout.addWidget(checkbox)

        self.content_layout.addStretch()

    def show_add_category_dialog(self):
        """Kategori ekleme dialog'unu göster"""
        dialog = AddCategoryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_category_data()
            if data['kategori_adi']:
                if mysql_manager.add_category(data['kategori_adi'], data['kategori_turu'], data['aciklama']):
                    self.show_info(f"✅ '{data['kategori_adi']}' kategorisi eklendi!")
                    self.load_categories()
                    self.load_profile_categories()
                    self.load_content_categories()
                else:
                    self.show_warning("Bu kategori zaten mevcut!")
            else:
                self.show_warning("Kategori adı boş olamaz!")

    def filter_accounts(self):
        """Hesapları filtrele"""
        search_text = self.search_edit.text().lower()

        for i in range(self.accounts_list.count()):
            item = self.accounts_list.item(i)
            account_name = item.text().lower()
            item.setHidden(search_text not in account_name)

    def on_account_type_changed(self, button, checked):
        """Hesap türü değiştiğinde"""
        if checked:
            if self.account_type_group.id(button) == 0:
                self.selected_account_type = 'giris_yapilan'
            else:
                self.selected_account_type = 'hedef'

            self.load_accounts()

    def load_accounts(self):
        """Hesapları yükle"""
        self.accounts_list.clear()
        self.accounts = []
        self.selected_accounts.clear()
        self.current_view_account = None

        try:
            if self.selected_account_type == 'giris_yapilan':
                users = user_manager.get_all_users()
                self.accounts = [user['kullanici_adi'] for user in users]
            else:
                targets = mysql_manager.get_all_targets()
                self.accounts = [target['kullanici_adi'] for target in targets]

            # Listeye ekle
            for account in self.accounts:
                item = QListWidgetItem(account)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.accounts_list.addItem(item)

            self.account_count_label.setText(f"{len(self.accounts)} hesap")
            self.status_label.setText("Hesap seçilmedi")

        except Exception as e:
            self.show_error(f"Hesaplar yüklenirken hata: {str(e)}")

    def on_select_all_changed(self, state):
        """Tümünü seç değiştiğinde"""
        check_state = Qt.Checked if state == Qt.Checked else Qt.Unchecked

        for i in range(self.accounts_list.count()):
            item = self.accounts_list.item(i)
            if not item.isHidden():
                item.setCheckState(check_state)

    def on_account_clicked(self, item):
        """Hesaba tıklandığında - kategorileri görüntüle"""
        account = item.text()
        self.current_view_account = account
        self.load_account_categories(account)
        self.status_label.setText(f"👁️ Görüntülenen: {account}")

    def on_account_item_changed(self, item):
        """Hesap checkbox'ı değiştiğinde"""
        self.update_selected_accounts()

    def update_selected_accounts(self):
        """Seçili hesapları güncelle"""
        selected_count = 0
        self.selected_accounts.clear()

        for i in range(self.accounts_list.count()):
            item = self.accounts_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_count += 1
                self.selected_accounts.add(item.text())

        if selected_count > 0:
            status_text = f"✅ Atama için seçili: {selected_count} hesap"
            if self.current_view_account:
                status_text += f" | 👁️ Görüntülenen: {self.current_view_account}"
            self.status_label.setText(status_text)

    def load_account_categories(self, account):
        """Hesabın kategorilerini yükle ve göster"""
        try:
            # Önce tüm seçimleri temizle
            self.clear_category_selections()

            # Hesabın kategorilerini getir
            account_categories = mysql_manager.get_account_categories(account, self.selected_account_type)

            # Profil kategorilerini işaretle
            for cat in account_categories:
                kategori_adi = cat['kategori_adi']
                kategori_degeri = cat['kategori_degeri']

                if kategori_adi in self.profile_categories:
                    widget = self.profile_categories[kategori_adi]
                    if isinstance(widget, QComboBox):
                        index = widget.findText(kategori_degeri)
                        if index >= 0:
                            widget.setCurrentIndex(index)
                    elif isinstance(widget, QLineEdit):
                        widget.setText(kategori_degeri)

                # İçerik kategorilerini işaretle
                if kategori_adi in self.content_categories:
                    self.content_categories[kategori_adi].setChecked(True)

        except Exception as e:
            self.show_error(f"Hesap kategorileri yüklenirken hata: {str(e)}")

    def clear_category_selections(self):
        """Kategori seçimlerini temizle"""
        # Profil kategorilerini temizle
        for widget in self.profile_categories.values():
            if isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, QLineEdit):
                widget.clear()

        # İçerik kategorilerini temizle
        for checkbox in self.content_categories.values():
            checkbox.setChecked(False)

    def clear_selections(self):
        """Tüm seçimleri temizle"""
        self.clear_category_selections()

        # Hesap seçimlerini temizle
        self.select_all_checkbox.setChecked(False)
        for i in range(self.accounts_list.count()):
            item = self.accounts_list.item(i)
            item.setCheckState(Qt.Unchecked)

    def save_categories(self):
        """Kategorileri kaydet"""
        if not self.selected_accounts:
            self.show_warning("Kategori atamak için hesap seçin!")
            return

        try:
            saved_count = 0

            for account in self.selected_accounts:
                # Önce hesabın kategorilerini sil
                mysql_manager.delete_account_categories(account, self.selected_account_type)

                # Profil kategorilerini kaydet
                for kategori_adi, widget in self.profile_categories.items():
                    value = None
                    if isinstance(widget, QComboBox):
                        if widget.currentIndex() > 0:
                            value = widget.currentText()
                    elif isinstance(widget, QLineEdit):
                        if widget.text().strip():
                            value = widget.text().strip()

                    if value:
                        mysql_manager.assign_category_to_account(account, self.selected_account_type, kategori_adi, value)

                # İçerik kategorilerini kaydet
                for kategori_adi, checkbox in self.content_categories.items():
                    if checkbox.isChecked():
                        mysql_manager.assign_category_to_account(account, self.selected_account_type, kategori_adi, "aktif")

                saved_count += 1

            self.show_info(f"✅ {saved_count} hesap için kategoriler kaydedildi!")

        except Exception as e:
            self.show_error(f"Kategoriler kaydedilirken hata: {str(e)}")

    def load_categories(self):
        """Kategorileri yükle"""
        try:
            self.categories = mysql_manager.get_categories()
        except Exception as e:
            self.show_error(f"Kategoriler yüklenirken hata: {str(e)}")

    def import_categories_file(self):
        """Kategori dosyası içe aktar"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Kategori Dosyası Seç",
            "",
            "Metin Dosyaları (*.txt);;Tüm Dosyalar (*)"
        )

        if file_path:
            try:
                count = mysql_manager.import_categories_from_file(file_path)
                self.show_info(f"✅ {count} kategori başarıyla içe aktarıldı!")
                self.load_categories()
                self.load_profile_categories()
                self.load_content_categories()
            except Exception as e:
                self.show_error(f"Kategori içe aktarma hatası: {str(e)}")

    def import_account_categories_file(self):
        """Hesap kategorileri dosyası içe aktar"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Hesap Kategorileri Dosyası Seç",
            "",
            "Metin Dosyaları (*.txt);;Tüm Dosyalar (*)"
        )

        if file_path:
            try:
                count = mysql_manager.import_account_categories_from_file(file_path, self.selected_account_type)
                self.show_info(f"✅ {count} hesap kategorisi başarıyla içe aktarıldı!")
                if self.current_view_account:
                    self.load_account_categories(self.current_view_account)
            except Exception as e:
                self.show_error(f"Hesap kategorileri içe aktarma hatası: {str(e)}")

    def return_to_main(self):
        """Ana menüye dön"""
        self.return_callback()

    def setup_style(self):
        """Stil ayarlarını uygula"""
        style = f"""
        QWidget {{
            background: {self.colors['background']};
            color: {self.colors['text_primary']};
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
        }}

        #pageTitle {{
            font-size: 24px;
            font-weight: 700;
            color: {self.colors['text_primary']};
            margin: 10px 0px;
        }}

        #backButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #6C757D, stop:1 #5A6268);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
        }}

        #importButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #17A2B8, stop:1 #138496);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
            margin: 2px;
        }}

        #addButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['success']}, stop:1 {self.colors['success_hover']});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
            margin: 2px;
        }}

        #statusLabel {{
            font-size: 14px;
            font-weight: 600;
            color: {self.colors['primary']};
            padding: 10px;
            background: {self.colors['background_alt']};
            border-radius: 8px;
            border: 1px solid {self.colors['border']};
        }}

        #categoryLabel {{
            font-size: 14px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            padding: 5px 0px;
        }}

        #categoryFrame {{
            background: {self.colors['background_alt']};
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            margin: 5px 0px;
            padding: 10px;
        }}

        #contentCheckbox {{
            font-size: 13px;
            font-weight: 500;
            color: {self.colors['text_primary']};
            padding: 5px;
        }}

        QListWidget {{
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            background: {self.colors['background']};
            alternate-background-color: {self.colors['background_alt']};
            selection-background-color: {self.colors['primary']};
            selection-color: white;
            padding: 5px;
        }}

        QComboBox, QLineEdit {{
            border: 1px solid {self.colors['border']};
            border-radius: 4px;
            padding: 5px;
            background: {self.colors['background']};
            font-size: 12px;
        }}

        #saveButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['success']}, stop:1 {self.colors['success_hover']});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
        }}

        #clearButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #DC3545, stop:1 #C82333);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
        }}
        """

        self.setStyleSheet(style)

    def show_info(self, message):
        """Bilgi mesajı"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Bilgi")
        msg.setText(message)
        msg.exec_()

    def show_warning(self, message):
        """Uyarı mesajı"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Uyarı")
        msg.setText(message)
        msg.exec_()

    def show_error(self, message):
        """Hata mesajı"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Hata")
        msg.setText(message)
        msg.exec_()