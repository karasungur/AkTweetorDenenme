
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QMessageBox, QListWidget, QListWidgetItem,
                             QComboBox, QLineEdit, QTextEdit, QGroupBox, QSplitter,
                             QTreeWidget, QTreeWidgetItem, QFileDialog, QProgressBar,
                             QTabWidget, QGridLayout, QScrollArea, QButtonGroup, QRadioButton)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
from database.mysql import mysql_manager
from database.user_manager import user_manager
import os

class CategoryImportThread(QThread):
    """Kategori içe aktarma thread'i"""
    progress_signal = pyqtSignal(int, int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)
    
    def __init__(self, file_path, import_type, hesap_turu=None):
        super().__init__()
        self.file_path = file_path
        self.import_type = import_type  # 'categories' or 'account_categories'
        self.hesap_turu = hesap_turu
    
    def run(self):
        try:
            if self.import_type == 'categories':
                count = mysql_manager.import_categories_from_file(self.file_path)
                self.log_signal.emit(f"✅ {count} kategori başarıyla içe aktarıldı")
            elif self.import_type == 'account_categories':
                count = mysql_manager.import_account_categories_from_file(self.file_path, self.hesap_turu)
                self.log_signal.emit(f"✅ {count} hesap kategorisi başarıyla içe aktarıldı")
            
            self.finished_signal.emit(count)
        except Exception as e:
            self.log_signal.emit(f"❌ İçe aktarma hatası: {str(e)}")
            self.finished_signal.emit(0)

class CategoryWindow(QWidget):
    def __init__(self, colors, return_callback):
        super().__init__()
        self.colors = colors
        self.return_callback = return_callback
        self.selected_account_type = None
        self.accounts = []
        self.categories = []
        
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
        
        title_label = QLabel("📂 Kategori Yöneticisi")
        title_label.setObjectName("pageTitle")
        
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Ana tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabWidget")
        
        # 1. Hesap Seçimi Tab'ı
        self.account_selection_tab = self.create_account_selection_tab()
        self.tab_widget.addTab(self.account_selection_tab, "🎯 Hesap Seçimi")
        
        # 2. Kategori Yönetimi Tab'ı
        self.category_management_tab = self.create_category_management_tab()
        self.tab_widget.addTab(self.category_management_tab, "📋 Kategori Yönetimi")
        
        # 3. Hesap Kategorilendirme Tab'ı
        self.account_categorization_tab = self.create_account_categorization_tab()
        self.tab_widget.addTab(self.account_categorization_tab, "🏷️ Hesap Kategorilendirme")
        
        # 4. Dosya İşlemleri Tab'ı
        self.file_operations_tab = self.create_file_operations_tab()
        self.tab_widget.addTab(self.file_operations_tab, "📁 Dosya İşlemleri")
        
        # Layout'a ekle
        layout.addLayout(header_layout)
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)
        
        # İlk yükleme
        self.load_categories()
    
    def create_account_selection_tab(self):
        """Hesap seçimi tab'ını oluştur"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Açıklama
        info_label = QLabel("Hangi hesaplara işlem yapmak istiyorsunuz?")
        info_label.setObjectName("infoLabel")
        info_label.setAlignment(Qt.AlignCenter)
        
        # Seçim butonları
        selection_frame = QFrame()
        selection_frame.setObjectName("selectionFrame")
        selection_layout = QHBoxLayout()
        
        # Button group
        self.account_type_group = QButtonGroup()
        
        # Giriş yapılan hesaplar
        login_radio = QRadioButton("🔐 Giriş Yapılan Hesaplar")
        login_radio.setObjectName("accountTypeRadio")
        login_radio.setChecked(True)
        self.account_type_group.addButton(login_radio, 0)
        
        # Hedef hesaplar
        target_radio = QRadioButton("📋 Hedef Hesaplar")
        target_radio.setObjectName("accountTypeRadio")
        self.account_type_group.addButton(target_radio, 1)
        
        selection_layout.addStretch()
        selection_layout.addWidget(login_radio)
        selection_layout.addSpacing(50)
        selection_layout.addWidget(target_radio)
        selection_layout.addStretch()
        
        selection_frame.setLayout(selection_layout)
        
        # Hesap listesi
        accounts_group = QGroupBox("📱 Hesap Listesi")
        accounts_group.setObjectName("accountsGroup")
        accounts_layout = QVBoxLayout()
        
        # Yenile butonu
        refresh_btn = QPushButton("🔄 Hesapları Yenile")
        refresh_btn.setObjectName("primaryButton")
        refresh_btn.clicked.connect(self.load_accounts)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        
        # Hesap listesi widget
        self.accounts_list = QListWidget()
        self.accounts_list.setObjectName("accountsList")
        
        accounts_layout.addWidget(refresh_btn)
        accounts_layout.addWidget(self.accounts_list)
        accounts_group.setLayout(accounts_layout)
        
        # Devam butonu
        continue_btn = QPushButton("➡️ Kategorilendirmeye Geç")
        continue_btn.setObjectName("primaryButton")
        continue_btn.clicked.connect(self.proceed_to_categorization)
        continue_btn.setCursor(Qt.PointingHandCursor)
        
        # Layout'a ekle
        layout.addWidget(info_label)
        layout.addSpacing(20)
        layout.addWidget(selection_frame)
        layout.addSpacing(20)
        layout.addWidget(accounts_group, 1)
        layout.addWidget(continue_btn)
        
        tab.setLayout(layout)
        
        # Signal bağlantıları
        self.account_type_group.buttonToggled.connect(self.on_account_type_changed)
        
        # İlk yükleme
        self.load_accounts()
        
        return tab
    
    def create_category_management_tab(self):
        """Kategori yönetimi tab'ını oluştur"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Üst panel - Yeni kategori ekleme
        add_panel = QGroupBox("➕ Yeni Kategori Ekle")
        add_panel.setObjectName("addCategoryGroup")
        add_layout = QGridLayout()
        
        # Kategori türü
        add_layout.addWidget(QLabel("Kategori Türü:"), 0, 0)
        self.category_type_combo = QComboBox()
        self.category_type_combo.setObjectName("categoryCombo")
        self.category_type_combo.addItems(["profil", "icerik"])
        add_layout.addWidget(self.category_type_combo, 0, 1)
        
        # Ana kategori
        add_layout.addWidget(QLabel("Ana Kategori:"), 1, 0)
        self.main_category_entry = QLineEdit()
        self.main_category_entry.setObjectName("categoryInput")
        self.main_category_entry.setPlaceholderText("Örn: Yaş Grubu, İçerik Türü")
        add_layout.addWidget(self.main_category_entry, 1, 1)
        
        # Alt kategori
        add_layout.addWidget(QLabel("Alt Kategori:"), 2, 0)
        self.sub_category_entry = QLineEdit()
        self.sub_category_entry.setObjectName("categoryInput")
        self.sub_category_entry.setPlaceholderText("Örn: Genç (18-30), Spor İçeriği")
        add_layout.addWidget(self.sub_category_entry, 2, 1)
        
        # Açıklama
        add_layout.addWidget(QLabel("Açıklama:"), 3, 0)
        self.description_entry = QLineEdit()
        self.description_entry.setObjectName("categoryInput")
        self.description_entry.setPlaceholderText("Kategori açıklaması (opsiyonel)")
        add_layout.addWidget(self.description_entry, 3, 1)
        
        # Ekle butonu
        add_category_btn = QPushButton("➕ Kategori Ekle")
        add_category_btn.setObjectName("successButton")
        add_category_btn.clicked.connect(self.add_new_category)
        add_category_btn.setCursor(Qt.PointingHandCursor)
        add_layout.addWidget(add_category_btn, 4, 0, 1, 2)
        
        add_panel.setLayout(add_layout)
        
        # Alt panel - Mevcut kategoriler
        categories_panel = QGroupBox("📋 Mevcut Kategoriler")
        categories_panel.setObjectName("categoriesGroup")
        categories_layout = QVBoxLayout()
        
        # Filtreleme
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrele:"))
        self.category_filter_combo = QComboBox()
        self.category_filter_combo.setObjectName("categoryCombo")
        self.category_filter_combo.addItems(["Tümü", "profil", "icerik"])
        self.category_filter_combo.currentTextChanged.connect(self.filter_categories)
        filter_layout.addWidget(self.category_filter_combo)
        filter_layout.addStretch()
        
        # Yenile butonu
        refresh_categories_btn = QPushButton("🔄 Yenile")
        refresh_categories_btn.setObjectName("primaryButton")
        refresh_categories_btn.clicked.connect(self.load_categories)
        refresh_categories_btn.setCursor(Qt.PointingHandCursor)
        filter_layout.addWidget(refresh_categories_btn)
        
        # Kategori ağacı
        self.categories_tree = QTreeWidget()
        self.categories_tree.setObjectName("categoriesTree")
        self.categories_tree.setHeaderLabels(["Kategori", "Tür", "Açıklama"])
        self.categories_tree.setRootIsDecorated(True)
        
        categories_layout.addLayout(filter_layout)
        categories_layout.addWidget(self.categories_tree)
        categories_panel.setLayout(categories_layout)
        
        # Layout'a ekle
        layout.addWidget(add_panel)
        layout.addWidget(categories_panel, 1)
        
        tab.setLayout(layout)
        return tab
    
    def create_account_categorization_tab(self):
        """Hesap kategorilendirme tab'ını oluştur"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Bilgi paneli
        info_panel = QFrame()
        info_panel.setObjectName("infoPanel")
        info_layout = QHBoxLayout()
        
        self.selected_accounts_label = QLabel("Seçili hesap türü yok")
        self.selected_accounts_label.setObjectName("infoLabel")
        
        load_selected_btn = QPushButton("📥 Seçili Hesapları Yükle")
        load_selected_btn.setObjectName("primaryButton")
        load_selected_btn.clicked.connect(self.load_selected_accounts)
        load_selected_btn.setCursor(Qt.PointingHandCursor)
        
        info_layout.addWidget(self.selected_accounts_label)
        info_layout.addStretch()
        info_layout.addWidget(load_selected_btn)
        info_panel.setLayout(info_layout)
        
        # Ana içerik - Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Sol panel - Hesaplar
        accounts_panel = QGroupBox("👥 Hesaplar")
        accounts_panel.setObjectName("accountsGroup")
        accounts_panel_layout = QVBoxLayout()
        
        self.categorization_accounts_list = QListWidget()
        self.categorization_accounts_list.setObjectName("accountsList")
        self.categorization_accounts_list.itemSelectionChanged.connect(self.on_account_selected)
        
        accounts_panel_layout.addWidget(self.categorization_accounts_list)
        accounts_panel.setLayout(accounts_panel_layout)
        
        # Sağ panel - Kategori atama
        assignment_panel = QGroupBox("🏷️ Kategori Atama")
        assignment_panel.setObjectName("assignmentGroup")
        assignment_layout = QVBoxLayout()
        
        # Seçili hesap bilgisi
        self.selected_account_label = QLabel("Hesap seçilmedi")
        self.selected_account_label.setObjectName("selectedAccountLabel")
        
        # Kategori seçimi
        category_selection_layout = QGridLayout()
        
        category_selection_layout.addWidget(QLabel("Ana Kategori:"), 0, 0)
        self.assignment_main_combo = QComboBox()
        self.assignment_main_combo.setObjectName("categoryCombo")
        self.assignment_main_combo.currentTextChanged.connect(self.load_sub_categories)
        category_selection_layout.addWidget(self.assignment_main_combo, 0, 1)
        
        category_selection_layout.addWidget(QLabel("Alt Kategori:"), 1, 0)
        self.assignment_sub_combo = QComboBox()
        self.assignment_sub_combo.setObjectName("categoryCombo")
        category_selection_layout.addWidget(self.assignment_sub_combo, 1, 1)
        
        category_selection_layout.addWidget(QLabel("Değer:"), 2, 0)
        self.assignment_value_entry = QLineEdit()
        self.assignment_value_entry.setObjectName("categoryInput")
        self.assignment_value_entry.setPlaceholderText("Kategori değeri girin")
        category_selection_layout.addWidget(self.assignment_value_entry, 2, 1)
        
        # Atama butonu
        assign_btn = QPushButton("✅ Kategori Ata")
        assign_btn.setObjectName("successButton")
        assign_btn.clicked.connect(self.assign_category)
        assign_btn.setCursor(Qt.PointingHandCursor)
        category_selection_layout.addWidget(assign_btn, 3, 0, 1, 2)
        
        # Mevcut kategoriler
        current_categories_label = QLabel("📋 Mevcut Kategoriler:")
        current_categories_label.setObjectName("sectionLabel")
        
        self.current_categories_list = QListWidget()
        self.current_categories_list.setObjectName("currentCategoriesList")
        
        assignment_layout.addWidget(self.selected_account_label)
        assignment_layout.addSpacing(10)
        assignment_layout.addLayout(category_selection_layout)
        assignment_layout.addSpacing(10)
        assignment_layout.addWidget(current_categories_label)
        assignment_layout.addWidget(self.current_categories_list)
        
        assignment_panel.setLayout(assignment_layout)
        
        # Splitter'a ekle
        splitter.addWidget(accounts_panel)
        splitter.addWidget(assignment_panel)
        splitter.setSizes([300, 400])
        
        # Layout'a ekle
        layout.addWidget(info_panel)
        layout.addWidget(splitter, 1)
        
        tab.setLayout(layout)
        return tab
    
    def create_file_operations_tab(self):
        """Dosya işlemleri tab'ını oluştur"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Kategori içe aktarma
        import_categories_group = QGroupBox("📥 Kategori İçe Aktarma")
        import_categories_group.setObjectName("fileGroup")
        import_categories_layout = QVBoxLayout()
        
        # Açıklama
        import_info = QLabel("Format: kategori_turu:ana_kategori:alt_kategori:aciklama")
        import_info.setObjectName("formatLabel")
        
        # Dosya seçimi
        import_file_layout = QHBoxLayout()
        self.import_categories_path = QLineEdit()
        self.import_categories_path.setObjectName("filePathInput")
        self.import_categories_path.setPlaceholderText("Kategori dosyası seçin...")
        
        browse_categories_btn = QPushButton("📁 Dosya Seç")
        browse_categories_btn.setObjectName("primaryButton")
        browse_categories_btn.clicked.connect(self.browse_categories_file)
        browse_categories_btn.setCursor(Qt.PointingHandCursor)
        
        import_categories_btn = QPushButton("📥 Kategorileri İçe Aktar")
        import_categories_btn.setObjectName("successButton")
        import_categories_btn.clicked.connect(self.import_categories)
        import_categories_btn.setCursor(Qt.PointingHandCursor)
        
        import_file_layout.addWidget(self.import_categories_path)
        import_file_layout.addWidget(browse_categories_btn)
        import_file_layout.addWidget(import_categories_btn)
        
        import_categories_layout.addWidget(import_info)
        import_categories_layout.addLayout(import_file_layout)
        import_categories_group.setLayout(import_categories_layout)
        
        # Hesap kategorileri içe aktarma
        import_account_categories_group = QGroupBox("🏷️ Hesap Kategorileri İçe Aktarma")
        import_account_categories_group.setObjectName("fileGroup")
        import_account_layout = QVBoxLayout()
        
        # Açıklama
        import_account_info = QLabel("Format: kullanici_adi:ana_kategori:alt_kategori:deger")
        import_account_info.setObjectName("formatLabel")
        
        # Hesap türü seçimi
        account_type_layout = QHBoxLayout()
        account_type_layout.addWidget(QLabel("Hesap Türü:"))
        self.import_account_type_combo = QComboBox()
        self.import_account_type_combo.setObjectName("categoryCombo")
        self.import_account_type_combo.addItems(["giris_yapilan", "hedef"])
        account_type_layout.addWidget(self.import_account_type_combo)
        account_type_layout.addStretch()
        
        # Dosya seçimi
        import_account_file_layout = QHBoxLayout()
        self.import_account_categories_path = QLineEdit()
        self.import_account_categories_path.setObjectName("filePathInput")
        self.import_account_categories_path.setPlaceholderText("Hesap kategorileri dosyası seçin...")
        
        browse_account_categories_btn = QPushButton("📁 Dosya Seç")
        browse_account_categories_btn.setObjectName("primaryButton")
        browse_account_categories_btn.clicked.connect(self.browse_account_categories_file)
        browse_account_categories_btn.setCursor(Qt.PointingHandCursor)
        
        import_account_categories_btn = QPushButton("🏷️ Hesap Kategorilerini İçe Aktar")
        import_account_categories_btn.setObjectName("successButton")
        import_account_categories_btn.clicked.connect(self.import_account_categories)
        import_account_categories_btn.setCursor(Qt.PointingHandCursor)
        
        import_account_file_layout.addWidget(self.import_account_categories_path)
        import_account_file_layout.addWidget(browse_account_categories_btn)
        import_account_file_layout.addWidget(import_account_categories_btn)
        
        import_account_layout.addWidget(import_account_info)
        import_account_layout.addLayout(account_type_layout)
        import_account_layout.addLayout(import_account_file_layout)
        import_account_categories_group.setLayout(import_account_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setVisible(False)
        
        # Log alanı
        log_group = QGroupBox("📋 İşlem Logları")
        log_group.setObjectName("logGroup")
        log_layout = QVBoxLayout()
        
        self.log_area = QTextEdit()
        self.log_area.setObjectName("logArea")
        self.log_area.setMaximumHeight(150)
        self.log_area.setReadOnly(True)
        
        log_layout.addWidget(self.log_area)
        log_group.setLayout(log_layout)
        
        # Layout'a ekle
        layout.addWidget(import_categories_group)
        layout.addWidget(import_account_categories_group)
        layout.addWidget(self.progress_bar)
        layout.addWidget(log_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
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
        
        #backButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5A6268, stop:1 #495057);
        }}
        
        #primaryButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary']}, stop:1 {self.colors['primary_end']});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
        }}
        
        #primaryButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary_end']}, stop:1 {self.colors['primary']});
        }}
        
        #successButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['success']}, stop:1 {self.colors['success_hover']});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
        }}
        
        #successButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['success_hover']}, stop:1 {self.colors['success']});
        }}
        
        QGroupBox {{
            font-weight: 600;
            font-size: 14px;
            color: {self.colors['text_primary']};
            border: 2px solid {self.colors['border']};
            border-radius: 8px;
            margin: 5px 0px;
            padding-top: 15px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            background: {self.colors['background']};
        }}
        
        QTabWidget::pane {{
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            background: {self.colors['background']};
        }}
        
        QTabBar::tab {{
            background: {self.colors['background_alt']};
            color: {self.colors['text_secondary']};
            border: 1px solid {self.colors['border']};
            padding: 10px 20px;
            margin-right: 2px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }}
        
        QTabBar::tab:selected {{
            background: {self.colors['background']};
            color: {self.colors['primary']};
            border-bottom: 2px solid {self.colors['primary']};
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
        
        QTreeWidget {{
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            background: {self.colors['background']};
            alternate-background-color: {self.colors['background_alt']};
            selection-background-color: {self.colors['primary']};
            selection-color: white;
        }}
        
        QComboBox, QLineEdit {{
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            padding: 8px;
            background: {self.colors['background']};
            font-size: 14px;
        }}
        
        QComboBox:focus, QLineEdit:focus {{
            border: 2px solid {self.colors['primary']};
        }}
        
        QTextEdit {{
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            background: {self.colors['background']};
            font-family: 'Consolas', monospace;
            font-size: 12px;
        }}
        
        QProgressBar {{
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            background: {self.colors['background_alt']};
            text-align: center;
            height: 20px;
        }}
        
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary']}, stop:1 {self.colors['primary_end']});
            border-radius: 6px;
        }}
        
        QRadioButton {{
            font-size: 16px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            spacing: 10px;
        }}
        
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
        }}
        
        QRadioButton::indicator:checked {{
            background: {self.colors['primary']};
            border: 2px solid {self.colors['primary']};
            border-radius: 9px;
        }}
        
        QRadioButton::indicator:unchecked {{
            background: {self.colors['background']};
            border: 2px solid {self.colors['border']};
            border-radius: 9px;
        }}
        
        #infoLabel {{
            font-size: 18px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            padding: 20px;
        }}
        
        #formatLabel {{
            font-size: 12px;
            color: {self.colors['text_secondary']};
            font-style: italic;
            padding: 5px;
        }}
        
        #selectedAccountLabel {{
            font-size: 16px;
            font-weight: 600;
            color: {self.colors['primary']};
            padding: 10px;
            background: {self.colors['background_alt']};
            border-radius: 6px;
        }}
        
        #sectionLabel {{
            font-size: 14px;
            font-weight: 600;
            color: {self.colors['text_primary']};
        }}
        """
        
        self.setStyleSheet(style)
    
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
        
        try:
            if self.selected_account_type == 'giris_yapilan':
                # Giriş yapılan hesapları getir
                users = user_manager.get_all_users()
                self.accounts = [user['kullanici_adi'] for user in users]
                self.selected_accounts_label.setText(f"📱 Giriş Yapılan Hesaplar ({len(self.accounts)} hesap)")
            
            elif self.selected_account_type == 'hedef':
                # Hedef hesapları getir
                targets = mysql_manager.get_all_targets()
                self.accounts = [target['kullanici_adi'] for target in targets]
                self.selected_accounts_label.setText(f"🎯 Hedef Hesaplar ({len(self.accounts)} hesap)")
            
            # Listeye ekle
            for account in self.accounts:
                self.accounts_list.addItem(account)
            
        except Exception as e:
            self.show_error(f"Hesaplar yüklenirken hata: {str(e)}")
    
    def load_categories(self):
        """Kategorileri yükle"""
        try:
            self.categories = mysql_manager.get_categories()
            self.update_categories_tree()
            self.update_assignment_combos()
        except Exception as e:
            self.show_error(f"Kategoriler yüklenirken hata: {str(e)}")
    
    def update_categories_tree(self):
        """Kategori ağacını güncelle"""
        self.categories_tree.clear()
        
        # Kategorileri grupla
        grouped = {}
        for category in self.categories:
            key = (category['kategori_turu'], category['ana_kategori'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(category)
        
        # Ağaca ekle
        for (kategori_turu, ana_kategori), subs in grouped.items():
            main_item = QTreeWidgetItem([ana_kategori, kategori_turu, ""])
            main_item.setExpanded(True)
            
            for sub in subs:
                sub_item = QTreeWidgetItem([
                    sub['alt_kategori'] or "Genel",
                    sub['kategori_turu'],
                    sub['aciklama'] or ""
                ])
                main_item.addChild(sub_item)
            
            self.categories_tree.addTopLevelItem(main_item)
    
    def filter_categories(self):
        """Kategorileri filtrele"""
        filter_type = self.category_filter_combo.currentText()
        
        if filter_type == "Tümü":
            filtered_categories = self.categories
        else:
            filtered_categories = [c for c in self.categories if c['kategori_turu'] == filter_type]
        
        # Ağacı güncelle
        self.categories_tree.clear()
        grouped = {}
        for category in filtered_categories:
            key = (category['kategori_turu'], category['ana_kategori'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(category)
        
        for (kategori_turu, ana_kategori), subs in grouped.items():
            main_item = QTreeWidgetItem([ana_kategori, kategori_turu, ""])
            main_item.setExpanded(True)
            
            for sub in subs:
                sub_item = QTreeWidgetItem([
                    sub['alt_kategori'] or "Genel",
                    sub['kategori_turu'],
                    sub['aciklama'] or ""
                ])
                main_item.addChild(sub_item)
            
            self.categories_tree.addTopLevelItem(main_item)
    
    def add_new_category(self):
        """Yeni kategori ekle"""
        kategori_turu = self.category_type_combo.currentText()
        ana_kategori = self.main_category_entry.text().strip()
        alt_kategori = self.sub_category_entry.text().strip() or None
        aciklama = self.description_entry.text().strip() or None
        
        if not ana_kategori:
            self.show_warning("Ana kategori boş olamaz!")
            return
        
        if mysql_manager.add_category(kategori_turu, ana_kategori, alt_kategori, aciklama):
            self.show_info("✅ Kategori başarıyla eklendi!")
            self.main_category_entry.clear()
            self.sub_category_entry.clear()
            self.description_entry.clear()
            self.load_categories()
        else:
            self.show_warning("Bu kategori zaten mevcut!")
    
    def proceed_to_categorization(self):
        """Kategorilendirme tab'ına geç"""
        if not self.selected_account_type:
            self.show_warning("Önce hesap türü seçin!")
            return
        
        self.tab_widget.setCurrentIndex(2)  # Hesap kategorilendirme tab'ı
        self.load_selected_accounts()
    
    def load_selected_accounts(self):
        """Seçili hesapları kategorilendirme tab'ına yükle"""
        self.categorization_accounts_list.clear()
        
        if self.selected_account_type:
            for account in self.accounts:
                self.categorization_accounts_list.addItem(account)
    
    def update_assignment_combos(self):
        """Atama combobox'larını güncelle"""
        self.assignment_main_combo.clear()
        
        # Ana kategorileri ekle
        main_categories = set()
        for category in self.categories:
            main_categories.add(category['ana_kategori'])
        
        for main_cat in sorted(main_categories):
            self.assignment_main_combo.addItem(main_cat)
    
    def load_sub_categories(self):
        """Alt kategorileri yükle"""
        self.assignment_sub_combo.clear()
        
        main_category = self.assignment_main_combo.currentText()
        if not main_category:
            return
        
        # Bu ana kategoriye ait alt kategorileri bul
        sub_categories = []
        for category in self.categories:
            if category['ana_kategori'] == main_category and category['alt_kategori']:
                sub_categories.append(category['alt_kategori'])
        
        for sub_cat in sorted(set(sub_categories)):
            self.assignment_sub_combo.addItem(sub_cat)
    
    def on_account_selected(self):
        """Hesap seçildiğinde"""
        selected_items = self.categorization_accounts_list.selectedItems()
        if not selected_items:
            self.selected_account_label.setText("Hesap seçilmedi")
            self.current_categories_list.clear()
            return
        
        account = selected_items[0].text()
        self.selected_account_label.setText(f"🎯 Seçili Hesap: {account}")
        
        # Bu hesabın mevcut kategorilerini yükle
        self.load_account_categories(account)
    
    def load_account_categories(self, account):
        """Hesabın kategorilerini yükle"""
        self.current_categories_list.clear()
        
        try:
            categories = mysql_manager.get_account_categories(account, self.selected_account_type)
            
            for category in categories:
                item_text = f"{category['ana_kategori']} > {category['alt_kategori']} = {category['kategori_degeri']}"
                self.current_categories_list.addItem(item_text)
                
        except Exception as e:
            self.show_error(f"Hesap kategorileri yüklenirken hata: {str(e)}")
    
    def assign_category(self):
        """Kategori ata"""
        selected_items = self.categorization_accounts_list.selectedItems()
        if not selected_items:
            self.show_warning("Hesap seçin!")
            return
        
        account = selected_items[0].text()
        main_category = self.assignment_main_combo.currentText()
        sub_category = self.assignment_sub_combo.currentText()
        value = self.assignment_value_entry.text().strip()
        
        if not all([main_category, sub_category, value]):
            self.show_warning("Tüm alanları doldurun!")
            return
        
        # Kategori ID'sini bul
        category_id = None
        for category in self.categories:
            if category['ana_kategori'] == main_category and category['alt_kategori'] == sub_category:
                category_id = category['id']
                break
        
        if not category_id:
            self.show_error("Kategori bulunamadı!")
            return
        
        # Atama yap
        if mysql_manager.assign_category_to_account(account, self.selected_account_type, category_id, value):
            self.show_info("✅ Kategori başarıyla atandı!")
            self.assignment_value_entry.clear()
            self.load_account_categories(account)
        else:
            self.show_error("Kategori atanamadı!")
    
    def browse_categories_file(self):
        """Kategori dosyası seç"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Kategori Dosyası Seç", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.import_categories_path.setText(file_path)
    
    def browse_account_categories_file(self):
        """Hesap kategorileri dosyası seç"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Hesap Kategorileri Dosyası Seç", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.import_account_categories_path.setText(file_path)
    
    def import_categories(self):
        """Kategorileri içe aktar"""
        file_path = self.import_categories_path.text()
        if not file_path or not os.path.exists(file_path):
            self.show_warning("Geçerli dosya seçin!")
            return
        
        self.progress_bar.setVisible(True)
        self.log_area.append("📥 Kategori içe aktarma başlatıldı...")
        
        # Thread'i başlat
        self.import_thread = CategoryImportThread(file_path, 'categories')
        self.import_thread.log_signal.connect(self.log_area.append)
        self.import_thread.finished_signal.connect(self.on_import_finished)
        self.import_thread.start()
    
    def import_account_categories(self):
        """Hesap kategorilerini içe aktar"""
        file_path = self.import_account_categories_path.text()
        hesap_turu = self.import_account_type_combo.currentText()
        
        if not file_path or not os.path.exists(file_path):
            self.show_warning("Geçerli dosya seçin!")
            return
        
        self.progress_bar.setVisible(True)
        self.log_area.append(f"🏷️ Hesap kategorileri içe aktarma başlatıldı ({hesap_turu})...")
        
        # Thread'i başlat
        self.import_thread = CategoryImportThread(file_path, 'account_categories', hesap_turu)
        self.import_thread.log_signal.connect(self.log_area.append)
        self.import_thread.finished_signal.connect(self.on_import_finished)
        self.import_thread.start()
    
    def on_import_finished(self, count):
        """İçe aktarma tamamlandığında"""
        self.progress_bar.setVisible(False)
        self.load_categories()
        
        if count > 0:
            self.show_info(f"✅ {count} öğe başarıyla içe aktarıldı!")
        else:
            self.show_warning("Hiçbir öğe içe aktarılamadı!")
    
    def return_to_main(self):
        """Ana menüye dön"""
        self.return_callback()
    
    def show_info(self, message):
        """Bilgi mesajı göster"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Bilgi")
        msg.setText(message)
        msg.exec_()
    
    def show_warning(self, message):
        """Uyarı mesajı göster"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Uyarı")
        msg.setText(message)
        msg.exec_()
    
    def show_error(self, message):
        """Hata mesajı göster"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Hata")
        msg.setText(message)
        msg.exec_()
