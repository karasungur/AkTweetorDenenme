
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

        layout = QVBoxLayout()

        # Tab widget
        self.tabs = QTabWidget()

        # Profil içerik kategorileri
        profile_content_tab = self.create_profile_content_tab()
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

    def create_profile_content_tab(self):
        """Profil içerik kategorileri sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Açıklama
        info_label = QLabel("📂 Profil içerik kategorileri: Hesabın paylaştığı içerik türleri")
        info_label.setObjectName("infoLabel")
        layout.addWidget(info_label)

        # Ekleme formu
        form_frame = QFrame()
        form_frame.setObjectName("addForm")
        form_layout = QHBoxLayout()

        self.profile_content_input = QLineEdit()
        self.profile_content_input.setPlaceholderText("Kategori adı girin (ör: Siyasi Eğilim, Dini Paylaşımlar)")

        add_profile_btn = QPushButton("➕ Ekle")
        add_profile_btn.setObjectName("addButton")
        add_profile_btn.clicked.connect(self.add_profile_content_category)

        form_layout.addWidget(self.profile_content_input)
        form_layout.addWidget(add_profile_btn)
        form_frame.setLayout(form_layout)

        # Liste
        self.profile_content_list = QListWidget()
        self.profile_content_list.setObjectName("categoryList")

        # Sil butonu
        delete_profile_btn = QPushButton("🗑️ Seçileni Sil")
        delete_profile_btn.setObjectName("deleteButton")
        delete_profile_btn.clicked.connect(self.delete_profile_content_category)

        layout.addWidget(form_frame)
        layout.addWidget(self.profile_content_list, 1)
        layout.addWidget(delete_profile_btn)

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

        # Sil butonu
        delete_photo_btn = QPushButton("🗑️ Seçileni Sil")
        delete_photo_btn.setObjectName("deleteButton")
        delete_photo_btn.clicked.connect(self.delete_photo_content_category)

        layout.addWidget(form_frame)
        layout.addWidget(self.photo_content_list, 1)
        layout.addWidget(delete_photo_btn)

        widget.setLayout(layout)
        return widget

    def load_categories(self):
        """Kategorileri yükle"""
        # Profil içerik kategorileri
        self.profile_content_list.clear()
        profile_categories = mysql_manager.get_categories('icerik')
        for cat in profile_categories:
            if cat.get('ana_kategori') != 'Fotoğraf İçeriği':
                item = QListWidgetItem(cat.get('ana_kategori', ''))
                item.setData(Qt.UserRole, cat)
                self.profile_content_list.addItem(item)

        # Fotoğraf içeriği kategorileri
        self.photo_content_list.clear()
        photo_categories = [cat for cat in profile_categories if cat.get('ana_kategori') == 'Fotoğraf İçeriği']
        for cat in photo_categories:
            item = QListWidgetItem(cat.get('alt_kategori', ''))
            item.setData(Qt.UserRole, cat)
            self.photo_content_list.addItem(item)

    def add_profile_content_category(self):
        """Profil içerik kategorisi ekle"""
        name = self.profile_content_input.text().strip()
        if name:
            if mysql_manager.add_hierarchical_category('icerik', name, None, 'Profil içerik kategorisi'):
                self.profile_content_input.clear()
                self.load_categories()
                self.show_info(f"✅ Kategori eklendi: {name}")
            else:
                self.show_warning("Bu kategori zaten mevcut!")

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

    def delete_profile_content_category(self):
        """Profil içerik kategorisi sil"""
        current = self.profile_content_list.currentItem()
        if current:
            # Bu işlev için veritabanında silme fonksiyonu eklenmelidir
            self.show_info("Silme işlevi henüz aktif değil")

    def delete_photo_content_category(self):
        """Fotoğraf içerik kategorisi sil"""
        current = self.photo_content_list.currentItem()
        if current:
            # Bu işlev için veritabanında silme fonksiyonu eklenmelidir
            self.show_info("Silme işlevi henüz aktif değil")

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

        # Kategorileri yükle
        categories = mysql_manager.get_categories('icerik')
        photo_categories = [cat for cat in categories if cat.get('ana_kategori') == 'Fotoğraf İçeriği']

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
        """Profil içerik kategorilerini yükle"""
        # Temizle
        for i in reversed(range(self.profile_content_layout.count())):
            child = self.profile_content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        self.profile_content_checkboxes.clear()

        # Kategorileri yükle
        categories = mysql_manager.get_categories('icerik')
        profile_categories = [cat for cat in categories if cat.get('ana_kategori') != 'Fotoğraf İçeriği']

        for cat in profile_categories:
            ana_kategori = cat.get('ana_kategori', '')
            if ana_kategori:
                checkbox = QCheckBox(ana_kategori)
                checkbox.setObjectName("contentCheckbox")
                self.profile_content_checkboxes[ana_kategori] = {
                    'checkbox': checkbox,
                    'data': cat
                }
                self.profile_content_layout.addWidget(checkbox)

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
        dialog.exec_()
        # Kategorileri yeniden yükle
        self.load_photo_content_categories()
        self.load_profile_content_categories()

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
                for ana_kategori, checkbox_data in self.profile_content_checkboxes.items():
                    if checkbox_data['checkbox'].isChecked():
                        mysql_manager.assign_hierarchical_category_to_account(
                            account, self.selected_account_type, ana_kategori, None, "Seçili"
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
