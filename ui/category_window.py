from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QMessageBox, QListWidget, QListWidgetItem,
                             QComboBox, QLineEdit, QTextEdit, QGroupBox, QSplitter,
                             QTreeWidget, QTreeWidgetItem, QFileDialog, QProgressBar,
                             QTabWidget, QGridLayout, QScrollArea, QButtonGroup, QRadioButton,
                             QCheckBox, QDialog, QDialogButtonBox, QStackedWidget, QFormLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
from database.mysql import mysql_manager
from database.user_manager import user_manager
import os

class CategoryManagementDialog(QDialog):
    """Kategori yönetimi dialog'u"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛠 Kategori Yönetimi")
        self.setModal(True)
        self.resize(600, 500)

        # Sayfalama değişkenleri
        self.photo_current_page = 1
        self.photo_items_per_page = 20
        self.content_current_page = 1
        self.content_items_per_page = 20

        layout = QVBoxLayout()

        # Tab widget
        self.tabs = QTabWidget()

        # Profil içerik kategorileri
        profile_content_tab = self.create_content_categories_tab()
        self.tabs.addTab(profile_content_tab, "📂 Profil İçerik Kategorileri")

        # Fotoğraf içeriği kategorileri
        photo_content_tab = self.create_photo_content_tab()
        self.tabs.addTab(photo_content_tab, "📸 Fotoğraf İçeriği Kategorileri")

        layout.addWidget(self.tabs)

        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.load_categories()

    def create_content_categories_tab(self):
        """İçerik kategorileri sekmesi - Hiyerarşik yapı"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Açıklama
        info_label = QLabel("📂 <b>İçerik Kategorileri:</b> Hesabın paylaştığı içerik türleri (Ana kategori → Alt kategoriler)")
        info_label.setObjectName("infoLabel")
        layout.addWidget(info_label)

        # Arama çubuğu
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Arama:")
        self.content_search_input = QLineEdit()
        self.content_search_input.setPlaceholderText("Kategori adı veya açıklama arayın...")
        self.content_search_input.textChanged.connect(self.filter_content_categories)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.content_search_input)
        layout.addWidget(QFrame())  # Spacer
        search_frame = QFrame()
        search_frame.setLayout(search_layout)
        layout.addWidget(search_frame)

        # Splitter - sol taraf ana kategoriler, sağ taraf alt kategoriler
        splitter = QSplitter(Qt.Horizontal)

        # Sol panel - Ana kategoriler
        left_panel = QGroupBox("📋 Ana Kategoriler")
        left_layout = QVBoxLayout()

        # Ana kategori ekleme
        main_form = QFrame()
        main_form.setObjectName("addForm")
        main_form_layout = QHBoxLayout()

        self.main_category_input = QLineEdit()
        self.main_category_input.setPlaceholderText("Ana kategori adı (ör: Siyasi Eğilim)")

        add_main_btn = QPushButton("➕ Ana Kategori Ekle")
        add_main_btn.setObjectName("addButton")
        add_main_btn.clicked.connect(self.add_main_category)

        main_form_layout.addWidget(self.main_category_input)
        main_form_layout.addWidget(add_main_btn)
        main_form.setLayout(main_form_layout)

        # Ana kategori listesi
        self.main_categories_list = QListWidget()
        self.main_categories_list.setObjectName("categoryList")
        self.main_categories_list.itemClicked.connect(self.on_main_category_selected)

        # Ana kategori sil butonu
        delete_main_btn = QPushButton("🗑️ Ana Kategori Sil")
        delete_main_btn.setObjectName("deleteButton")
        delete_main_btn.clicked.connect(self.delete_main_category)

        left_layout.addWidget(main_form)
        left_layout.addWidget(self.main_categories_list, 1)
        left_layout.addWidget(delete_main_btn)
        left_panel.setLayout(left_layout)

        # Sağ panel - Alt kategoriler
        right_panel = QGroupBox("📝 Alt Kategoriler")
        right_layout = QVBoxLayout()

        # Seçili ana kategori bilgisi
        self.selected_main_label = QLabel("← Sol taraftan ana kategori seçin")
        self.selected_main_label.setObjectName("selectedMainLabel")
        right_layout.addWidget(self.selected_main_label)

        # Alt kategori ekleme
        sub_form = QFrame()
        sub_form.setObjectName("addForm")
        sub_form_layout = QHBoxLayout()

        self.sub_category_input = QLineEdit()
        self.sub_category_input.setPlaceholderText("Alt kategori adı")
        self.sub_category_input.setEnabled(False)

        add_sub_btn = QPushButton("➕ Alt Kategori Ekle")
        add_sub_btn.setObjectName("addButton")
        add_sub_btn.clicked.connect(self.add_sub_category)
        add_sub_btn.setEnabled(False)
        self.add_sub_btn = add_sub_btn

        sub_form_layout.addWidget(self.sub_category_input)
        sub_form_layout.addWidget(add_sub_btn)
        sub_form.setLayout(sub_form_layout)

        # Alt kategori listesi
        self.sub_categories_list = QListWidget()
        self.sub_categories_list.setObjectName("categoryList")

        # Alt kategori sil butonu
        delete_sub_btn = QPushButton("🗑️ Alt Kategori Sil")
        delete_sub_btn.setObjectName("deleteButton")
        delete_sub_btn.clicked.connect(self.delete_sub_category)
        delete_sub_btn.setEnabled(False)
        self.delete_sub_btn = delete_sub_btn

        right_layout.addWidget(sub_form)
        right_layout.addWidget(self.sub_categories_list, 1)
        right_layout.addWidget(delete_sub_btn)
        right_panel.setLayout(right_layout)

        # Splitter'a ekle
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 400])

        layout.addWidget(splitter, 1)
        widget.setLayout(layout)
        return widget

    def create_photo_content_tab(self):
        """Fotoğraf içeriği kategorileri sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Açıklama
        info_label = QLabel("📸 Fotoğraf içeriği kategorileri: Profil fotoğrafının içeriği")
        info_label.setObjectName("infoLabel")
        layout.addWidget(info_label)

        # Arama çubuğu
        photo_search_layout = QHBoxLayout()
        photo_search_label = QLabel("🔍 Arama:")
        self.photo_search_input = QLineEdit()
        self.photo_search_input.setPlaceholderText("Fotoğraf kategorisi arayın...")
        self.photo_search_input.textChanged.connect(self.filter_photo_categories)

        photo_search_layout.addWidget(photo_search_label)
        photo_search_layout.addWidget(self.photo_search_input)
        photo_search_frame = QFrame()
        photo_search_frame.setLayout(photo_search_layout)
        layout.addWidget(photo_search_frame)

        # Ekleme formu
        form_frame = QFrame()
        form_frame.setObjectName("addForm")
        form_layout = QHBoxLayout()

        self.photo_content_input = QLineEdit()
        self.photo_content_input.setPlaceholderText("Kategori adı girin (ör: Parti Logosu, Dini Sembol, Selfie)")

        add_photo_btn = QPushButton("➕ Ekle")
        add_photo_btn.setObjectName("addButton")
        add_photo_btn.clicked.connect(self.add_photo_content_category)

        form_layout.addWidget(self.photo_content_input)
        form_layout.addWidget(add_photo_btn)
        form_frame.setLayout(form_layout)

        # Liste
        self.photo_content_list = QListWidget()
        self.photo_content_list.setObjectName("categoryList")

        # Sayfalama kontrolleri
        pagination_layout = QHBoxLayout()
        self.photo_prev_btn = QPushButton("◀ Önceki")
        self.photo_prev_btn.clicked.connect(self.photo_prev_page)
        self.photo_next_btn = QPushButton("Sonraki ▶")
        self.photo_next_btn.clicked.connect(self.photo_next_page)
        self.photo_page_label = QLabel("Sayfa 1")

        pagination_layout.addWidget(self.photo_prev_btn)
        pagination_layout.addWidget(self.photo_page_label)
        pagination_layout.addWidget(self.photo_next_btn)
        pagination_layout.addStretch()

        # Sil butonu
        delete_photo_btn = QPushButton("🗑️ Seçileni Sil")
        delete_photo_btn.setObjectName("deleteButton")
        delete_photo_btn.clicked.connect(self.delete_photo_content_category)

        layout.addWidget(form_frame)
        layout.addWidget(self.photo_content_list, 1)
        layout.addLayout(pagination_layout)
        layout.addWidget(delete_photo_btn)

        widget.setLayout(layout)
        return widget

    def load_categories(self):
        """Kategorileri yükle"""
        # Profil içerik kategorileri - sadece ana kategorileri (alt_kategori NULL olanlar)
        self.main_categories_list.clear()
        profile_categories = mysql_manager.get_categories('icerik')
        self.all_profile_categories = [cat for cat in profile_categories 
                                     if cat.get('ana_kategori') != 'Fotoğraf İçeriği' 
                                     and cat.get('alt_kategori') is None]

        # Ana kategorileri tekrarsız şekilde ekle
        added_main_categories = set()
        for cat in self.all_profile_categories:
            ana_kategori = cat.get('ana_kategori', '')
            if ana_kategori and ana_kategori not in added_main_categories:
                item = QListWidgetItem(ana_kategori)
                item.setData(Qt.UserRole, cat)
                self.main_categories_list.addItem(item)
                added_main_categories.add(ana_kategori)

        # Fotoğraf içeriği kategorileri - sadece alt kategorileri
        self.photo_content_list.clear()
        self.all_photo_categories = [cat for cat in profile_categories 
                                   if cat.get('ana_kategori') == 'Fotoğraf İçeriği'
                                   and cat.get('alt_kategori') is not None]

        for cat in self.all_photo_categories:
            item = QListWidgetItem(cat.get('alt_kategori', ''))
            item.setData(Qt.UserRole, cat)
            self.photo_content_list.addItem(item)

    def filter_content_categories(self):
        """İçerik kategorilerini filtrele"""
        search_text = self.content_search_input.text().lower()
        self.main_categories_list.clear()

        # Ana kategorileri tekrarsız şekilde filtrele
        added_categories = set()
        for cat in getattr(self, 'all_profile_categories', []):
            ana_kategori = cat.get('ana_kategori', '')
            aciklama = cat.get('aciklama', '').lower()

            if (search_text in ana_kategori.lower() or search_text in aciklama) and ana_kategori not in added_categories:
                item = QListWidgetItem(ana_kategori)
                item.setData(Qt.UserRole, cat)
                self.main_categories_list.addItem(item)
                added_categories.add(ana_kategori)

    def filter_photo_categories(self):
        """Fotoğraf kategorilerini filtrele"""
        search_text = self.photo_search_input.text().lower()
        self.photo_content_list.clear()

        for cat in getattr(self, 'all_photo_categories', []):
            alt_kategori = cat.get('alt_kategori', '').lower()
            aciklama = cat.get('aciklama', '').lower()

            if search_text in alt_kategori or search_text in aciklama:
                item = QListWidgetItem(cat.get('alt_kategori', ''))
                item.setData(Qt.UserRole, cat)
                self.photo_content_list.addItem(item)

    def add_main_category(self):
        """Ana içerik kategorisi ekle"""
        name = self.main_category_input.text().strip()
        if name:
            if mysql_manager.add_hierarchical_category('icerik', name, None, 'Profil içerik kategorisi'):
                self.main_category_input.clear()
                self.load_categories()
                self.show_info(f"✅ Ana kategori eklendi: {name}")
            else:
                self.show_warning("Bu kategori zaten mevcut!")

    def add_sub_category(self):
        """Alt içerik kategorisi ekle"""
        main_category = self.selected_main_label.text().replace("Seçili ana kategori: ", "")
        name = self.sub_category_input.text().strip()

        # Önce ana kategori seçilmiş mi kontrol et
        if main_category == "← Sol taraftan ana kategori seçin":
            self.show_warning("⚠️ Önce sol taraftan bir ana kategori seçin!")
            return

        # Alt kategori adı boş mu kontrol et
        if not name:
            self.show_warning("⚠️ Alt kategori adı boş olamaz!")
            return

        # Alt kategori ekle
        if mysql_manager.add_hierarchical_category('icerik', main_category, name, 'Profil içerik alt kategorisi'):
            self.sub_category_input.clear()
            self.load_sub_categories(main_category)
            self.show_info(f"✅ Alt kategori eklendi: {name} (Ana kategori: {main_category})")

            # Ana ekrandaki kategorileri de yenile (parent varsa)
            if hasattr(self.parent(), 'load_profile_content_categories'):
                self.parent().load_profile_content_categories()
        else:
            self.show_warning("Bu alt kategori zaten mevcut veya ana kategori bulunamadı!")

    def add_photo_content_category(self):
        """Fotoğraf içerik kategorisi ekle"""
        name = self.photo_content_input.text().strip()
        if name:
            if mysql_manager.add_hierarchical_category('icerik', 'Fotoğraf İçeriği', name, 'Fotoğraf içerik kategorisi'):
                self.photo_content_input.clear()
                self.load_categories()
                self.show_info(f"✅ Fotoğraf kategorisi eklendi: {name}")
            else:
                self.show_warning("Bu kategori zaten mevcut!")

    def delete_main_category(self):
        """Ana içerik kategorisi sil"""
        current = self.main_categories_list.currentItem()
        if current:
            category_data = current.data(Qt.UserRole)
            category_name = category_data.get('ana_kategori')

            # Onay dialog'u
            reply = QMessageBox.question(self, "Kategori Sil", 
                f"'{category_name}' kategorisini ve tüm alt kategorilerini silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                if mysql_manager.delete_category('icerik', category_name, None):
                    self.load_categories()
                    self.show_info(f"✅ Ana kategori silindi: {category_name}")
                    # Seçimi temizle
                    self.selected_main_label.setText("← Sol taraftan ana kategori seçin")
                    self.sub_categories_list.clear()
                    self.sub_category_input.setEnabled(False)
                    self.add_sub_btn.setEnabled(False)
                    self.delete_sub_btn.setEnabled(False)
                else:
                    self.show_warning("Bu kategori silinemedi! Kategori hala kullanımda olabilir.")
        else:
            self.show_warning("Silmek için bir kategori seçin!")

    def delete_sub_category(self):
        """Alt içerik kategorisi sil"""
        current = self.sub_categories_list.currentItem()
        if current:
            category_data = current.data(Qt.UserRole)
            category_name = category_data.get('alt_kategori')
            main_category = self.selected_main_label.text().replace("Seçili ana kategori: ", "")

            # Onay dialog'u
            reply = QMessageBox.question(self, "Alt Kategori Sil", 
                f"'{category_name}' alt kategorisini silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                if mysql_manager.delete_category('icerik', main_category, category_name):
                    self.load_sub_categories(main_category)
                    # Ana kategori listesini güncellemek gerekmez, sadece alt kategoriler değişti
                    self.show_info(f"✅ Alt kategori silindi: {category_name}")
                else:
                    self.show_warning("Bu kategori silinemedi! Kategori hala kullanımda olabilir.")
        else:
            self.show_warning("Silmek için bir alt kategori seçin!")

    def delete_photo_content_category(self):
        """Fotoğraf içerik kategorisi sil"""
        current = self.photo_content_list.currentItem()
        if current:
            category_data = current.data(Qt.UserRole)
            category_name = category_data.get('alt_kategori')

            # Onay dialog'u
            reply = QMessageBox.question(self, "Fotoğraf Kategorisi Sil", 
                f"'{category_name}' fotoğraf kategorisini silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                if mysql_manager.delete_category('icerik', 'Fotoğraf İçeriği', category_name):
                    self.load_categories()
                    self.show_info(f"✅ Fotoğraf kategorisi silindi: {category_name}")
                else:
                    self.show_warning("Bu kategori silinemedi! Kategori hala kullanımda olabilir.")
        else:
            self.show_warning("Silmek için bir fotoğraf kategorisi seçin!")

    def on_main_category_selected(self, item):
        """Ana kategori seçildiğinde"""
        category_data = item.data(Qt.UserRole)
        category_name = category_data.get('ana_kategori')

        self.selected_main_label.setText(f"Seçili ana kategori: {category_name}")
        self.sub_category_input.setEnabled(True)
        self.add_sub_btn.setEnabled(True)
        self.delete_sub_btn.setEnabled(True)

        self.load_sub_categories(category_name)

    def load_sub_categories(self, main_category):
        """Alt kategorileri yükle"""
        self.sub_categories_list.clear()
        categories = mysql_manager.get_categories('icerik')
        sub_categories = [cat for cat in categories if cat.get('ana_kategori') == main_category and cat.get('alt_kategori')]

        for cat in sub_categories:
            item = QListWidgetItem(cat.get('alt_kategori', ''))
            item.setData(Qt.UserRole, cat)
            self.sub_categories_list.addItem(item)

    def photo_prev_page(self):
        """Fotoğraf kategorileri önceki sayfa"""
        if self.photo_current_page > 1:
            self.photo_current_page -= 1
            self.update_photo_pagination()

    def photo_next_page(self):
        """Fotoğraf kategorileri sonraki sayfa"""
        total_items = len(getattr(self, 'all_photo_categories', []))
        max_pages = (total_items + self.photo_items_per_page - 1) // self.photo_items_per_page
        if self.photo_current_page < max_pages:
            self.photo_current_page += 1
            self.update_photo_pagination()

    def update_photo_pagination(self):
        """Fotoğraf kategorileri sayfalama güncelle"""
        self.photo_content_list.clear()

        all_categories = getattr(self, 'all_photo_categories', [])
        total_items = len(all_categories)
        max_pages = (total_items + self.photo_items_per_page - 1) // self.photo_items_per_page if total_items > 0 else 1

        start_idx = (self.photo_current_page - 1) * self.photo_items_per_page
        end_idx = min(start_idx + self.photo_items_per_page, total_items)

        # Sayfadaki öğeleri göster
        for i in range(start_idx, end_idx):
            cat = all_categories[i]
            item = QListWidgetItem(cat.get('alt_kategori', ''))
            item.setData(Qt.UserRole, cat)
            self.photo_content_list.addItem(item)

        # Sayfa bilgisini güncelle
        self.photo_page_label.setText(f"Sayfa {self.photo_current_page}/{max_pages}")
        self.photo_prev_btn.setEnabled(self.photo_current_page > 1)
        self.photo_next_btn.setEnabled(self.photo_current_page < max_pages)

    def show_info(self, message):
        QMessageBox.information(self, "Bilgi", message)

    def show_warning(self, message):
        QMessageBox.warning(self, "Uyarı", message)

class FileImportDialog(QDialog):
    """Dosyadan içe aktarma dialog'u"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📁 Dosyadan Kategori Atama")
        self.setModal(True)
        self.resize(500, 300)

        layout = QVBoxLayout()

        # Açıklama
        info_label = QLabel("""
📁 Dosyadan toplu kategori atama

Dosya formatları:
• Kategori dosyası: kategori_turu:ana_kategori:alt_kategori:aciklama
• Hesap kategorileri: kullanici_adi:ana_kategori:alt_kategori:deger
        """)
        info_label.setObjectName("infoLabel")
        layout.addWidget(info_label)

        # Dosya seçim butonları
        self.import_categories_btn = QPushButton("📁 Kategori Dosyası Seç")
        self.import_categories_btn.clicked.connect(self.import_categories)

        self.import_account_categories_btn = QPushButton("📁 Hesap Kategorileri Dosyası Seç")
        self.import_account_categories_btn.clicked.connect(self.import_account_categories)

        layout.addWidget(self.import_categories_btn)
        layout.addWidget(self.import_account_categories_btn)

        # Log alanı
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)

        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def import_categories(self):
        """Kategori dosyası içe aktar"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Kategori Dosyası Seç", "", "Metin Dosyaları (*.txt)")
        if file_path:
            count = mysql_manager.import_categories_from_file(file_path)
            self.log_text.append(f"✅ {count} kategori içe aktarıldı")

    def import_account_categories(self):
        """Hesap kategorileri dosyası içe aktar"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Hesap Kategorileri Dosyası Seç", "", "Metin Dosyaları (*.txt)")
        if file_path:
            # Hesap türü seçimi gerekli - şimdilik hedef hesap olarak varsayalım
            count = mysql_manager.import_account_categories_from_file(file_path, 'hedef')
            self.log_text.append(f"✅ {count} hesap kategorisi içe aktarıldı")

class CategoryWindow(QWidget):
    def __init__(self, colors, return_callback):
        super().__init__()
        self.colors = colors
        self.return_callback = return_callback
        self.selected_account_type = 'giris_yapilan'
        self.accounts = []
        self.selected_accounts = set()
        self.current_view_account = None
        self.is_edit_mode = False

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

        title_label = QLabel("🏷️ Kategori Yöneticisi")
        title_label.setObjectName("pageTitle")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Araç çubuğu
        toolbar_layout = QHBoxLayout()

        # Kategori yönetimi
        manage_categories_btn = QPushButton("🛠 Kategori Yönetimi")
        manage_categories_btn.setObjectName("manageButton")
        manage_categories_btn.clicked.connect(self.show_category_management)

        # Dosya işlemleri
        file_import_btn = QPushButton("📁 Dosyadan İçe Aktar")
        file_import_btn.setObjectName("importButton")
        file_import_btn.clicked.connect(self.show_file_import)

        toolbar_layout.addWidget(manage_categories_btn)
        toolbar_layout.addWidget(file_import_btn)
        toolbar_layout.addStretch()

        # Hesap türü seçimi
        account_type_frame = self.create_account_type_selection()

        # Ana splitter
        main_splitter = QSplitter(Qt.Horizontal)

        # Sol panel - Hesap listesi
        left_panel = self.create_accounts_panel()
        main_splitter.addWidget(left_panel)

        # Sağ panel - Kategori yönetimi
        right_panel = self.create_categories_panel()
        main_splitter.addWidget(right_panel)

        main_splitter.setSizes([400, 700])

        # Layout'a ekle
        layout.addLayout(header_layout)
        layout.addLayout(toolbar_layout)
        layout.addWidget(account_type_frame)
        layout.addWidget(main_splitter, 1)

        self.setLayout(layout)

        # İlk yükleme
        self.load_accounts()
        self.ensure_default_categories()

    def create_account_type_selection(self):
        """Hesap türü seçimi"""
        frame = QFrame()
        frame.setObjectName("accountTypeFrame")
        layout = QHBoxLayout()

        question_label = QLabel("📊 Hangi hesaplara kategori atayacaksınız?")
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
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)

        self.account_count_label = QLabel("0 hesap")

        refresh_btn = QPushButton("🔄")
        refresh_btn.clicked.connect(self.load_accounts)
        refresh_btn.setToolTip("Hesapları Yenile")

        controls_layout.addWidget(self.select_all_checkbox)
        controls_layout.addWidget(self.account_count_label)
        controls_layout.addStretch()
        controls_layout.addWidget(refresh_btn)

        # Hesap listesi
        self.accounts_list = QListWidget()
        self.accounts_list.itemClicked.connect(self.on_account_clicked)
        self.accounts_list.itemChanged.connect(self.on_account_item_changed)

        layout.addLayout(search_layout)
        layout.addLayout(controls_layout)
        layout.addWidget(self.accounts_list, 1)

        panel.setLayout(layout)
        return panel

    def create_categories_panel(self):
        """Kategori paneli"""
        panel = QGroupBox("🏷️ Kategori Atama")
        layout = QVBoxLayout()

        # Durum etiketi
        self.status_label = QLabel("Hesap seçin ve kategori atayın")
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

        # Mod butonları
        mode_layout = QHBoxLayout()

        self.view_mode_btn = QPushButton("👁️ Görüntüle")
        self.view_mode_btn.setObjectName("modeButton")
        self.view_mode_btn.clicked.connect(self.set_view_mode)

        self.edit_mode_btn = QPushButton("✏️ Düzenle")
        self.edit_mode_btn.setObjectName("modeButtonActive")
        self.edit_mode_btn.clicked.connect(self.set_edit_mode)

        mode_layout.addWidget(self.view_mode_btn)
        mode_layout.addWidget(self.edit_mode_btn)
        mode_layout.addStretch()

        layout.addLayout(mode_layout)

        # Stacked widget
        self.mode_stack = QStackedWidget()

        # Görüntüleme modu
        self.view_widget = self.create_view_mode_widget()
        self.mode_stack.addWidget(self.view_widget)

        # Düzenleme modu  
        self.edit_widget = self.create_edit_mode_widget()
        self.mode_stack.addWidget(self.edit_widget)

        # Varsayılan düzenleme modu
        self.mode_stack.setCurrentIndex(1)

        layout.addWidget(self.mode_stack, 1)

        panel.setLayout(layout)
        return panel

    def create_view_mode_widget(self):
        """Görüntüleme modu"""
        widget = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel("👁️ Hesabın mevcut kategorilerini görüntülüyorsunuz")
        info_label.setObjectName("infoLabel")
        layout.addWidget(info_label)

        self.view_text = QTextEdit()
        self.view_text.setReadOnly(True)
        layout.addWidget(self.view_text)

        widget.setLayout(layout)
        return widget

    def create_edit_mode_widget(self):
        """Düzenleme modu"""
        widget = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel("✏️ Seçili hesaplara kategori atayın")
        info_label.setObjectName("infoLabel")
        layout.addWidget(info_label)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.categories_layout = QVBoxLayout()

        # Profil kategorileri
        self.create_profile_categories()

        scroll_widget.setLayout(self.categories_layout)
        scroll_area.setWidget(scroll_widget)

        layout.addWidget(scroll_area, 1)

        # Kontrol butonları
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

        layout.addLayout(controls_layout)

        widget.setLayout(layout)
        return widget

    def create_profile_categories(self):
        """Sabit profil kategorilerini oluştur"""
        # Temizle
        for i in reversed(range(self.categories_layout.count())):
            child = self.categories_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # 1. Yaş Grubu
        age_frame = self.create_age_group_category()
        self.categories_layout.addWidget(age_frame)

        # 2. Cinsiyet
        gender_frame = self.create_gender_category()
        self.categories_layout.addWidget(gender_frame)

        # 3. Profil Fotoğrafı
        photo_frame = self.create_photo_category()
        self.categories_layout.addWidget(photo_frame)

        # 4. Profil İçerik Kategorileri
        content_frame = self.create_profile_content_categories()
        self.categories_layout.addWidget(content_frame)

        self.categories_layout.addStretch()

    def create_age_group_category(self):
        """Yaş grubu kategorisi"""
        frame = QFrame()
        frame.setObjectName("categoryFrame")
        layout = QVBoxLayout()

        title = QLabel("🧓 Yaş Grubu")
        title.setObjectName("categoryTitle")
        layout.addWidget(title)

        self.age_group = QButtonGroup()

        age_none = QRadioButton("Belirtilmemiş")
        age_none.setChecked(True)
        self.age_group.addButton(age_none, 0)
        layout.addWidget(age_none)

        age_young = QRadioButton("Genç (18-30)")
        self.age_group.addButton(age_young, 1)
        layout.addWidget(age_young)

        age_middle = QRadioButton("Orta yaş (31-50)")
        self.age_group.addButton(age_middle, 2)
        layout.addWidget(age_middle)

        age_old = QRadioButton("Yaşlı (50+)")
        self.age_group.addButton(age_old, 3)
        layout.addWidget(age_old)

        frame.setLayout(layout)
        return frame

    def create_gender_category(self):
        """Cinsiyet kategorisi"""
        frame = QFrame()
        frame.setObjectName("categoryFrame")
        layout = QVBoxLayout()

        title = QLabel("🚻 Cinsiyet")
        title.setObjectName("categoryTitle")
        layout.addWidget(title)

        self.gender_group = QButtonGroup()

        gender_none = QRadioButton("Belirtilmemiş")
        gender_none.setChecked(True)
        self.gender_group.addButton(gender_none, 0)
        layout.addWidget(gender_none)

        gender_male = QRadioButton("Erkek")
        self.gender_group.addButton(gender_male, 1)
        layout.addWidget(gender_male)

        gender_female = QRadioButton("Kadın")
        self.gender_group.addButton(gender_female, 2)
        layout.addWidget(gender_female)

        gender_other = QRadioButton("Belirtmeyen / Diğer")
        self.gender_group.addButton(gender_other, 3)
        layout.addWidget(gender_other)

        frame.setLayout(layout)
        return frame

    def create_photo_category(self):
        """Profil fotoğrafı kategorisi"""
        frame = QFrame()
        frame.setObjectName("categoryFrame")
        layout = QVBoxLayout()

        title = QLabel("📸 Profil Fotoğrafı")
        title.setObjectName("categoryTitle")
        layout.addWidget(title)

        # Fotoğraf varlığı
        photo_title = QLabel("Fotoğraf Varlığı:")
        photo_title.setObjectName("subTitle")
        layout.addWidget(photo_title)

        self.photo_exists_group = QButtonGroup()

        photo_none = QRadioButton("Belirtilmemiş")
        photo_none.setChecked(True)
        self.photo_exists_group.addButton(photo_none, 0)
        layout.addWidget(photo_none)

        photo_yes = QRadioButton("Fotoğraf var")
        self.photo_exists_group.addButton(photo_yes, 1)
        layout.addWidget(photo_yes)

        photo_no = QRadioButton("Fotoğraf yok")
        self.photo_exists_group.addButton(photo_no, 2)
        layout.addWidget(photo_no)

        # Fotoğraf içeriği (dinamik)
        self.photo_content_frame = QFrame()
        self.photo_content_frame.setVisible(False)
        photo_content_layout = QVBoxLayout()

        content_title = QLabel("Fotoğrafın İçeriği:")
        content_title.setObjectName("subTitle")
        photo_content_layout.addWidget(content_title)

        self.photo_content_layout = QVBoxLayout()
        self.photo_content_checkboxes = {}
        self.load_photo_content_categories()

        photo_content_layout.addLayout(self.photo_content_layout)
        self.photo_content_frame.setLayout(photo_content_layout)

        layout.addWidget(self.photo_content_frame)

        # Fotoğraf varlığı değiştiğinde içerik alanını göster/gizle
        self.photo_exists_group.buttonToggled.connect(self.on_photo_exists_changed)

        frame.setLayout(layout)
        return frame

    def create_profile_content_categories(self):
        """Profil içerik kategorileri"""
        frame = QFrame()
        frame.setObjectName("categoryFrame")
        layout = QVBoxLayout()

        title = QLabel("📂 Profil İçerik Kategorileri")
        title.setObjectName("categoryTitle")
        layout.addWidget(title)

        subtitle = QLabel("Hesabın paylaştığı içerik türleri (çoklu seçim)")
        subtitle.setObjectName("subTitle")
        layout.addWidget(subtitle)

        self.profile_content_layout = QVBoxLayout()
        self.profile_content_checkboxes = {}
        self.load_profile_content_categories()

        layout.addLayout(self.profile_content_layout)

        frame.setLayout(layout)
        return frame

    def load_photo_content_categories(self):
        """Fotoğraf içerik kategorilerini yükle"""
        # Temizle
        for i in reversed(range(self.photo_content_layout.count())):
            child = self.photo_content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        self.photo_content_checkboxes.clear()

        # Kategorileri yükle - sadece fotoğraf içeriği alt kategorileri
        categories = mysql_manager.get_categories('icerik')
        photo_categories = [cat for cat in categories 
                          if cat.get('ana_kategori') == 'Fotoğraf İçeriği'
                          and cat.get('alt_kategori') is not None]

        for cat in photo_categories:
            alt_kategori = cat.get('alt_kategori', '')
            if alt_kategori:
                checkbox = QCheckBox(alt_kategori)
                checkbox.setObjectName("contentCheckbox")
                self.photo_content_checkboxes[alt_kategori] = {
                    'checkbox': checkbox,
                    'data': cat
                }
                self.photo_content_layout.addWidget(checkbox)

    def load_profile_content_categories(self):
        """Profil içerik kategorilerini yükle - hem ana hem alt kategorileri dahil et"""
        # Temizle
        for i in reversed(range(self.profile_content_layout.count())):
            child = self.profile_content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        self.profile_content_checkboxes.clear()

        # Tüm içerik kategorilerini yükle (Fotoğraf İçeriği hariç)
        categories = mysql_manager.get_categories('icerik')

        # Ana kategorileri ve alt kategorileri grupla
        category_tree = {}
        for cat in categories:
            ana_kategori = cat.get('ana_kategori', '')
            alt_kategori = cat.get('alt_kategori', '')

            # Fotoğraf İçeriği kategorilerini atla
            if ana_kategori == 'Fotoğraf İçeriği':
                continue

            if ana_kategori not in category_tree:
                category_tree[ana_kategori] = {
                    'main_category': cat,
                    'sub_categories': []
                }

            if alt_kategori:
                category_tree[ana_kategori]['sub_categories'].append(cat)

        # Ana kategorileri ve alt kategorilerini ekle
        for ana_kategori, data in category_tree.items():
            # Ana kategori ekle
            main_checkbox = QCheckBox(f"📋 {ana_kategori}")
            main_checkbox.setObjectName("contentCheckbox")
            main_checkbox.setStyleSheet("font-weight: bold; margin-top: 8px;")
            self.profile_content_checkboxes[ana_kategori] = {
                'checkbox': main_checkbox,
                'data': data['main_category'],
                'type': 'main'
            }
            self.profile_content_layout.addWidget(main_checkbox)

            # Alt kategorileri ekle
            for sub_cat in data['sub_categories']:
                alt_kategori = sub_cat.get('alt_kategori', '')
                sub_checkbox = QCheckBox(f"   └─ {alt_kategori}")
                sub_checkbox.setObjectName("contentCheckbox")
                sub_checkbox.setStyleSheet("margin-left: 20px; color: #666;")

                # Alt kategori için benzersiz anahtar oluştur
                sub_key = f"{ana_kategori}::{alt_kategori}"
                self.profile_content_checkboxes[sub_key] = {
                    'checkbox': sub_checkbox,
                    'data': sub_cat,
                    'type': 'sub',
                    'parent': ana_kategori
                }
                self.profile_content_layout.addWidget(sub_checkbox)

    def on_photo_exists_changed(self, button, checked):
        """Fotoğraf varlığı değiştiğinde"""
        if checked and self.photo_exists_group.id(button) == 1:  # Fotoğraf var
            self.photo_content_frame.setVisible(True)
        else:
            self.photo_content_frame.setVisible(False)
            # Fotoğraf içerik seçimlerini temizle
            for checkbox_data in self.photo_content_checkboxes.values():
                checkbox_data['checkbox'].setChecked(False)

    def set_view_mode(self):
        """Görüntüleme moduna geç"""
        self.is_edit_mode = False
        self.mode_stack.setCurrentIndex(0)
        self.view_mode_btn.setObjectName("modeButtonActive")
        self.edit_mode_btn.setObjectName("modeButton")
        self.update_button_styles()

        if self.current_view_account:
            self.load_account_categories_view(self.current_view_account)

    def set_edit_mode(self):
        """Düzenleme moduna geç"""
        self.is_edit_mode = True
        self.mode_stack.setCurrentIndex(1)
        self.edit_mode_btn.setObjectName("modeButtonActive")
        self.view_mode_btn.setObjectName("modeButton")
        self.update_button_styles()

    def update_button_styles(self):
        """Buton stillerini güncelle"""
        self.view_mode_btn.style().unpolish(self.view_mode_btn)
        self.edit_mode_btn.style().unpolish(self.edit_mode_btn)
        self.view_mode_btn.style().polish(self.view_mode_btn)
        self.edit_mode_btn.style().polish(self.edit_mode_btn)

    def show_category_management(self):
        """Kategori yönetimi dialog'unu göster"""
        dialog = CategoryManagementDialog(self)
        result = dialog.exec_()
        # Kategorileri yeniden yükle
        self.load_photo_content_categories()
        self.load_profile_content_categories()

        # Eğer bir hesap seçilmişse kategorilerini yenile
        if self.current_view_account:
            if self.is_edit_mode:
                self.load_account_categories_edit(self.current_view_account)
            else:
                self.load_account_categories_view(self.current_view_account)

    def show_file_import(self):
        """Dosya içe aktarma dialog'unu göster"""
        dialog = FileImportDialog(self)
        dialog.exec_()

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

        try:
            if self.selected_account_type == 'giris_yapilan':
                users = user_manager.get_all_users()
                self.accounts = [user['kullanici_adi'] for user in users]
            else:
                targets = mysql_manager.get_all_targets()
                self.accounts = [target['kullanici_adi'] for target in targets]

            for account in self.accounts:
                item = QListWidgetItem(account)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.accounts_list.addItem(item)

            self.account_count_label.setText(f"{len(self.accounts)} hesap")

        except Exception as e:
            self.show_error(f"Hesaplar yüklenirken hata: {str(e)}")

    def on_select_all_changed(self, state):
        """Tümünü seç"""
        check_state = Qt.Checked if state == Qt.Checked else Qt.Unchecked
        for i in range(self.accounts_list.count()):
            item = self.accounts_list.item(i)
            if not item.isHidden():
                item.setCheckState(check_state)

    def on_account_clicked(self, item):
        """Hesaba tıklandığında"""
        account = item.text()
        self.current_view_account = account

        if self.is_edit_mode:
            self.load_account_categories_edit(account)
            self.status_label.setText(f"✏️ Düzenlenen: {account}")
        else:
            self.load_account_categories_view(account)
            self.status_label.setText(f"👁️ Görüntülenen: {account}")

    def on_account_item_changed(self, item):
        """Hesap seçimi değiştiğinde"""
        self.update_selected_accounts()

    def update_selected_accounts(self):
        """Seçili hesapları güncelle"""
        self.selected_accounts.clear()
        for i in range(self.accounts_list.count()):
            item = self.accounts_list.item(i)
            if item.checkState() == Qt.Checked:
                self.selected_accounts.add(item.text())

    def load_account_categories_view(self, account):
        """Hesap kategorilerini görüntüleme modunda göster"""
        try:
            account_categories = mysql_manager.get_account_categories(account, self.selected_account_type)

            if not account_categories:
                self.view_text.setHtml(f"""
                <div style='padding: 20px; text-align: center; color: #666;'>
                    <h3>👤 {account}</h3>
                    <p>Bu hesaba henüz kategori atanmamış</p>
                </div>
                """)
                return

            html = f"<h2>👤 {account} - Kategori Bilgileri</h2>"

            # Kategorileri grupla
            categories_by_type = {}
            for cat in account_categories:
                ana = cat.get('ana_kategori', '')
                if ana not in categories_by_type:
                    categories_by_type[ana] = []
                categories_by_type[ana].append(cat)

            for ana_kategori, cats in categories_by_type.items():
                html += f"<h3>📋 {ana_kategori}</h3><ul>"
                for cat in cats:
                    alt = cat.get('alt_kategori', '')
                    deger = cat.get('kategori_degeri', '')
                    display = alt if alt else deger
                    html += f"<li>{display}</li>"
                html += "</ul>"

            self.view_text.setHtml(html)

        except Exception as e:
            self.show_error(f"Kategoriler yüklenirken hata: {str(e)}")

    def load_account_categories_edit(self, account):
        """Hesap kategorilerini düzenleme modunda yükle"""
        try:
            # Önce tüm seçimleri temizle
            self.clear_category_selections()

            account_categories = mysql_manager.get_account_categories(account, self.selected_account_type)

            for cat in account_categories:
                ana_kategori = cat.get('ana_kategori', '')
                alt_kategori = cat.get('alt_kategori', '')
                deger = cat.get('kategori_degeri', '')

                # Yaş grubu
                if ana_kategori == "Yaş Grubu":
                    if "Genç" in deger:
                        self.age_group.button(1).setChecked(True)
                    elif "Orta" in deger:
                        self.age_group.button(2).setChecked(True)
                    elif "Yaşlı" in deger:
                        self.age_group.button(3).setChecked(True)

                # Cinsiyet
                elif ana_kategori == "Cinsiyet":
                    if "Erkek" in deger:
                        self.gender_group.button(1).setChecked(True)
                    elif "Kadın" in deger:
                        self.gender_group.button(2).setChecked(True)
                    elif "Diğer" in deger or "Belirtmeyen" in deger:
                        self.gender_group.button(3).setChecked(True)

                # Profil fotoğrafı
                elif ana_kategori == "Profil Fotoğrafı":
                    if "var" in deger.lower():
                        self.photo_exists_group.button(1).setChecked(True)
                    elif "yok" in deger.lower():
                        self.photo_exists_group.button(2).setChecked(True)

                # Fotoğraf içeriği
                elif ana_kategori == "Fotoğraf İçeriği":
                    if alt_kategori in self.photo_content_checkboxes:
                        self.photo_content_checkboxes[alt_kategori]['checkbox'].setChecked(True)

                # Profil içerik kategorileri
                else:
                    if alt_kategori:
                        # Alt kategori için anahtar oluştur
                        sub_key = f"{ana_kategori}::{alt_kategori}"
                        if sub_key in self.profile_content_checkboxes:
                            self.profile_content_checkboxes[sub_key]['checkbox'].setChecked(True)
                    else:
                        # Ana kategori
                        if ana_kategori in self.profile_content_checkboxes:
                            self.profile_content_checkboxes[ana_kategori]['checkbox'].setChecked(True)

        except Exception as e:
            self.show_error(f"Kategoriler yüklenirken hata: {str(e)}")

    def clear_category_selections(self):
        """Kategori seçimlerini temizle"""
        # Profil kategorilerini temizle
        self.age_group.button(0).setChecked(True)
        self.gender_group.button(0).setChecked(True)
        self.photo_exists_group.button(0).setChecked(True)

        # Checkbox'ları temizle
        for checkbox_data in self.photo_content_checkboxes.values():
            checkbox_data['checkbox'].setChecked(False)

        for checkbox_data in self.profile_content_checkboxes.values():
            checkbox_data['checkbox'].setChecked(False)

    def clear_selections(self):
        """Tüm seçimleri temizle"""
        self.clear_category_selections()
        self.select_all_checkbox.setChecked(False)

    def save_categories(self):
        """Kategorileri kaydet"""
        if not self.selected_accounts:
            self.show_warning("⚠️ En az bir hesap seçin!")
            return

        try:
            saved_count = 0

            for account in self.selected_accounts:
                # Hesabın kategorilerini sil
                mysql_manager.delete_account_categories(account, self.selected_account_type)

                # Yaş grubu
                age_button = self.age_group.checkedButton()
                age_id = self.age_group.id(age_button)
                if age_id > 0:
                    age_values = ["", "Genç (18-30)", "Orta yaş (31-50)", "Yaşlı (50+)"]
                    mysql_manager.assign_hierarchical_category_to_account(
                        account, self.selected_account_type, "Yaş Grubu", None, age_values[age_id]
                    )

                # Cinsiyet
                gender_button = self.gender_group.checkedButton()
                gender_id = self.gender_group.id(gender_button)
                if gender_id > 0:
                    gender_values = ["", "Erkek", "Kadın", "Belirtmeyen / Diğer"]
                    mysql_manager.assign_hierarchical_category_to_account(
                        account, self.selected_account_type, "Cinsiyet", None, gender_values[gender_id]
                    )

                # Profil fotoğrafı
                photo_button = self.photo_exists_group.checkedButton()
                photo_id = self.photo_exists_group.id(photo_button)
                if photo_id > 0:
                    photo_values = ["", "Fotoğraf var", "Fotoğraf yok"]
                    mysql_manager.assign_hierarchical_category_to_account(
                        account, self.selected_account_type, "Profil Fotoğrafı", None, photo_values[photo_id]
                    )

                    # Fotoğraf içeriği (sadece fotoğraf varsa)
                    if photo_id == 1:
                        for alt_kategori, checkbox_data in self.photo_content_checkboxes.items():
                            if checkbox_data['checkbox'].isChecked():
                                mysql_manager.assign_hierarchical_category_to_account(
                                    account, self.selected_account_type, "Fotoğraf İçeriği", alt_kategori, "Seçili"
                                )

                # Profil içerik kategorileri
                for key, checkbox_data in self.profile_content_checkboxes.items():
                    if checkbox_data['checkbox'].isChecked():
                        if checkbox_data['type'] == 'main':
                            # Ana kategori
                            mysql_manager.assign_hierarchical_category_to_account(
                                account, self.selected_account_type, key, None, "Seçili"
                            )
                        elif checkbox_data['type'] == 'sub':
                            # Alt kategori - key formatı: "ana_kategori::alt_kategori"
                            ana_kategori, alt_kategori = key.split('::', 1)
                            mysql_manager.assign_hierarchical_category_to_account(
                                account, self.selected_account_type, ana_kategori, alt_kategori, "Seçili"
                            )

                saved_count += 1

            self.show_info(f"✅ {saved_count} hesap için kategoriler kaydedildi!")

        except Exception as e:
            self.show_error(f"❌ Kaydetme hatası: {str(e)}")

    def ensure_default_categories(self):
        """Varsayılan kategorileri kontrol et ve ekle"""
        # Bu fonksiyon başlangıçta gerekli kategorilerin var olduğundan emin olur
        mysql_manager.add_hierarchical_category('profil', 'Yaş Grubu', None, 'Kullanıcının yaş grubu')
        mysql_manager.add_hierarchical_category('profil', 'Cinsiyet', None, 'Kullanıcının cinsiyeti')
        mysql_manager.add_hierarchical_category('profil', 'Profil Fotoğrafı', None, 'Profil fotoğrafı varlığı')
        mysql_manager.add_hierarchical_category('icerik', 'Fotoğraf İçeriği', 'Parti Logosu', 'Parti veya siyasi logo')
        mysql_manager.add_hierarchical_category('icerik', 'Fotoğraf İçeriği', 'Dini Sembol', 'Dini içerikli görsel')
        mysql_manager.add_hierarchical_category('icerik', 'Fotoğraf İçeriği', 'Selfie', 'Kişisel fotoğraf')
        mysql_manager.add_hierarchical_category('icerik', 'Siyasi Eğilim', None, 'Siyasi görüş ve eğilim')
        mysql_manager.add_hierarchical_category('icerik', 'Dini Paylaşımlar', None, 'Dini içerik paylaşımları')
        mysql_manager.add_hierarchical_category('icerik', 'Mizah', None, 'Komik ve mizahi içerikler')

    def return_to_main(self):
        """Ana menüye dön"""
        self.return_callback()

    def setup_style(self):
        """Geliştirilmiş stil"""
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

        #manageButton, #importButton {{
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

        #accountTypeFrame {{
            background: {self.colors['background_alt']};
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            padding: 10px;
            margin: 5px 0px;
        }}

        #questionLabel {{
            font-size: 14px;
            font-weight: 600;
            color: {self.colors['text_primary']};
        }}

        #accountTypeRadio {{
            font-size: 13px;
            font-weight: 500;
            color: {self.colors['text_primary']};
            padding: 5px;
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

        #modeButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #E9ECEF, stop:1 #DEE2E6);
            color: #495057;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
            margin: 2px;
        }}

        #modeButtonActive {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary']}, stop:1 {self.colors['primary_hover']});
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
            margin: 2px;
        }}

        #infoLabel {{
            font-size: 13px;
            font-weight: 600;
            color: {self.colors['text_secondary']};
            padding: 8px;
            background: #E3F2FD;
            border-radius: 6px;
            border: 1px solid #BBDEFB;
            margin-bottom: 10px;
        }}

        #categoryFrame {{
            background: {self.colors['background_alt']};
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            margin: 8px 0px;
            padding: 15px;
        }}

        #categoryTitle {{
            font-size: 16px;
            font-weight: 700;
            color: {self.colors['text_primary']};
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid {self.colors['primary']};
        }}

        #subTitle {{
            font-size: 13px;
            font-weight: 600;
            color: {self.colors['text_secondary']};
            margin: 8px 0px 5px 0px;
        }}

        QRadioButton {{
            font-size: 13px;
            font-weight: 500;
            color: {self.colors['text_primary']};
            padding: 4px 8px;
            margin: 2px 0px;
        }}

        #contentCheckbox {{
            font-size: 13px;
            font-weight: 500;
            color: {self.colors['text_primary']};
            padding: 4px 8px;
            margin: 2px 0px;
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

        #saveButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['success']}, stop:1 {self.colors['success_hover']});
```python
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

        #addForm {{
            background: {self.colors['background_alt']};
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            padding: 10px;
            margin: 5px 0px;
        }}

        #addButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['success']}, stop:1 {self.colors['success_hover']});
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
        }}

        #deleteButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #DC3545, stop:1 #C82333);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
        }}

        #categoryList {{
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            background: white;
            selection-background-color: {self.colors['primary']};
            selection-color: white;
        }}
        """

        self.setStyleSheet(style)

    def show_info(self, message):
        QMessageBox.information(self, "✅ Bilgi", message)

    def show_warning(self, message):
        QMessageBox.warning(self, "⚠️ Uyarı", message)

    def show_error(self, message):
        QMessageBox.critical(self, "❌ Hata", message)