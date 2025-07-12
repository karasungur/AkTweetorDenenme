
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QMessageBox, QListWidget, QListWidgetItem,
                             QComboBox, QLineEdit, QTextEdit, QGroupBox, QSplitter,
                             QTreeWidget, QTreeWidgetItem, QFileDialog, QProgressBar,
                             QTabWidget, QGridLayout, QScrollArea, QButtonGroup, QRadioButton,
                             QCheckBox, QDialog, QDialogButtonBox, QStackedWidget)
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
        self.resize(450, 350)

        layout = QVBoxLayout()

        # Kategori türü
        layout.addWidget(QLabel("Kategori Türü:"))
        self.category_type_combo = QComboBox()
        self.category_type_combo.addItems(["profil", "icerik"])
        self.category_type_combo.currentTextChanged.connect(self.on_type_changed)
        layout.addWidget(self.category_type_combo)

        # Ana kategori
        layout.addWidget(QLabel("Ana Kategori:"))
        self.main_category_combo = QComboBox()
        self.main_category_combo.setEditable(True)
        layout.addWidget(self.main_category_combo)

        # Alt kategori
        layout.addWidget(QLabel("Alt Kategori (opsiyonel):"))
        self.sub_category_edit = QLineEdit()
        self.sub_category_edit.setPlaceholderText("Alt kategori adını girin...")
        layout.addWidget(self.sub_category_edit)

        # Açıklama
        layout.addWidget(QLabel("Açıklama:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        layout.addWidget(self.description_edit)

        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.load_existing_categories()

    def load_existing_categories(self):
        """Mevcut kategorileri yükle"""
        categories = mysql_manager.get_categories()
        main_categories = set()
        
        for cat in categories:
            if cat.get('ana_kategori'):
                main_categories.add(cat['ana_kategori'])
        
        self.main_category_combo.addItems(sorted(main_categories))

    def on_type_changed(self, category_type):
        """Kategori türü değiştiğinde ana kategorileri filtrele"""
        self.main_category_combo.clear()
        categories = mysql_manager.get_categories(category_type)
        main_categories = set()
        
        for cat in categories:
            if cat.get('ana_kategori'):
                main_categories.add(cat['ana_kategori'])
        
        self.main_category_combo.addItems(sorted(main_categories))

    def get_category_data(self):
        return {
            'kategori_turu': self.category_type_combo.currentText(),
            'ana_kategori': self.main_category_combo.currentText().strip(),
            'alt_kategori': self.sub_category_edit.text().strip() or None,
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
        self.current_view_account = None
        self.is_edit_mode = False  # Görüntüleme/düzenleme modu

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

        title_label = QLabel("🏷️ Kategori Yöneticisi")
        title_label.setObjectName("pageTitle")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Araç çubuğu
        toolbar_layout = QHBoxLayout()

        # Dosya işlemleri
        import_categories_btn = QPushButton("📁 Kategori Dosyası")
        import_categories_btn.setObjectName("importButton")
        import_categories_btn.clicked.connect(self.import_categories_file)

        import_account_categories_btn = QPushButton("📁 Hesap Kategorileri")
        import_account_categories_btn.setObjectName("importButton")
        import_account_categories_btn.clicked.connect(self.import_account_categories_file)

        # Kategori yönetimi
        add_category_btn = QPushButton("➕ Kategori Ekle")
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
        self.load_categories()
        self.load_accounts()

    def create_account_type_selection(self):
        """Hesap türü seçimi"""
        frame = QFrame()
        frame.setObjectName("accountTypeFrame")
        layout = QHBoxLayout()

        question_label = QLabel("📊 Hangi hesaplara işlem yapmak istiyorsunuz?")
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
        """Kategori yönetim paneli"""
        panel = QGroupBox("🏷️ Kategori Yönetimi")
        panel.setObjectName("categoriesPanel")
        layout = QVBoxLayout()

        # Durum ve mod kontrolleri
        mode_layout = QHBoxLayout()
        
        self.status_label = QLabel("Hesap seçin")
        self.status_label.setObjectName("statusLabel")

        # Mod değiştirme butonları
        self.view_mode_btn = QPushButton("👁️ Görüntüle")
        self.view_mode_btn.setObjectName("modeButton")
        self.view_mode_btn.clicked.connect(self.set_view_mode)

        self.edit_mode_btn = QPushButton("✏️ Düzenle")
        self.edit_mode_btn.setObjectName("modeButtonActive")
        self.edit_mode_btn.clicked.connect(self.set_edit_mode)

        mode_layout.addWidget(self.status_label)
        mode_layout.addStretch()
        mode_layout.addWidget(self.view_mode_btn)
        mode_layout.addWidget(self.edit_mode_btn)

        # Stacked widget - mod değişimi için
        self.mode_stack = QStackedWidget()

        # Görüntüleme modu
        self.view_widget = self.create_view_mode_widget()
        self.mode_stack.addWidget(self.view_widget)

        # Düzenleme modu
        self.edit_widget = self.create_edit_mode_widget()
        self.mode_stack.addWidget(self.edit_widget)

        # Varsayılan olarak düzenleme modu
        self.mode_stack.setCurrentIndex(1)

        layout.addLayout(mode_layout)
        layout.addWidget(self.mode_stack, 1)

        panel.setLayout(layout)
        return panel

    def create_view_mode_widget(self):
        """Görüntüleme modu widget'ı"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Bilgi etiketi
        info_label = QLabel("👁️ Hesabın mevcut kategorilerini görüntülüyorsunuz")
        info_label.setObjectName("infoLabel")
        layout.addWidget(info_label)

        # Kategorileri gösterecek alan
        self.view_text = QTextEdit()
        self.view_text.setObjectName("viewText")
        self.view_text.setReadOnly(True)
        layout.addWidget(self.view_text)

        widget.setLayout(layout)
        return widget

    def create_edit_mode_widget(self):
        """Düzenleme modu widget'ı"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Bilgi etiketi
        info_label = QLabel("✏️ Seçili hesaplara kategori atayın")
        info_label.setObjectName("infoLabel")
        layout.addWidget(info_label)

        # Tab widget
        self.category_tabs = QTabWidget()

        # Profil kategorileri
        profile_tab = self.create_profile_categories_tab()
        self.category_tabs.addTab(profile_tab, "👤 Profil")

        # İçerik kategorileri
        content_tab = self.create_content_categories_tab()
        self.category_tabs.addTab(content_tab, "📝 İçerik")

        layout.addWidget(self.category_tabs, 1)

        # Kaydet ve temizle butonları
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

    def create_profile_categories_tab(self):
        """Profil kategorileri - radio button grupları"""
        widget = QWidget()
        layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.profile_layout = QVBoxLayout()

        self.profile_groups = {}
        self.load_profile_categories()

        scroll_widget.setLayout(self.profile_layout)
        scroll_area.setWidget(scroll_widget)

        layout.addWidget(scroll_area)
        widget.setLayout(layout)
        return widget

    def create_content_categories_tab(self):
        """İçerik kategorileri - checkbox listesi"""
        widget = QWidget()
        layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.content_layout = QVBoxLayout()

        self.content_checkboxes = {}
        self.load_content_categories()

        scroll_widget.setLayout(self.content_layout)
        scroll_area.setWidget(scroll_widget)

        layout.addWidget(scroll_area)
        widget.setLayout(layout)
        return widget

    def load_profile_categories(self):
        """Profil kategorilerini hiyerarşik olarak yükle"""
        # Önceki widget'ları temizle
        for i in reversed(range(self.profile_layout.count())):
            child = self.profile_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        self.profile_groups.clear()

        # Kategorileri hiyerarşik yapıda grupla
        categories = mysql_manager.get_categories('profil')
        grouped = {}

        for category in categories:
            ana_kategori = category.get('ana_kategori', 'Genel')
            if ana_kategori not in grouped:
                grouped[ana_kategori] = []
            grouped[ana_kategori].append(category)

        # Her ana kategori için grup oluştur
        for ana_kategori, subs in grouped.items():
            frame = QFrame()
            frame.setObjectName("categoryGroupFrame")
            frame_layout = QVBoxLayout()

            # Ana kategori başlığı
            title_label = QLabel(f"📋 {ana_kategori}")
            title_label.setObjectName("categoryGroupTitle")
            frame_layout.addWidget(title_label)

            # Radio button grubu
            button_group = QButtonGroup()
            
            # "Seçim yok" seçeneği
            none_radio = QRadioButton("Belirtilmemiş")
            none_radio.setObjectName("profileRadio")
            none_radio.setChecked(True)
            button_group.addButton(none_radio, -1)
            frame_layout.addWidget(none_radio)

            # Alt kategoriler için radio butonlar
            for i, sub in enumerate(subs):
                alt_kategori = sub.get('alt_kategori', sub.get('kategori_adi', ''))
                
                radio = QRadioButton(alt_kategori)
                radio.setObjectName("profileRadio")
                button_group.addButton(radio, i)
                frame_layout.addWidget(radio)

            self.profile_groups[ana_kategori] = {
                'group': button_group,
                'categories': subs,
                'none_button': none_radio
            }

            frame.setLayout(frame_layout)
            self.profile_layout.addWidget(frame)

        self.profile_layout.addStretch()

    def load_content_categories(self):
        """İçerik kategorilerini hiyerarşik olarak yükle"""
        # Önceki widget'ları temizle
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        self.content_checkboxes.clear()

        # Kategorileri hiyerarşik yapıda grupla
        categories = mysql_manager.get_categories('icerik')
        grouped = {}

        for category in categories:
            ana_kategori = category.get('ana_kategori', 'Genel')
            if ana_kategori not in grouped:
                grouped[ana_kategori] = []
            grouped[ana_kategori].append(category)

        # Her ana kategori için grup oluştur
        for ana_kategori, subs in grouped.items():
            frame = QFrame()
            frame.setObjectName("categoryGroupFrame")
            frame_layout = QVBoxLayout()

            # Ana kategori başlığı
            title_label = QLabel(f"📂 {ana_kategori}")
            title_label.setObjectName("categoryGroupTitle")
            frame_layout.addWidget(title_label)

            # Alt kategoriler için checkbox'lar
            for sub in subs:
                alt_kategori = sub.get('alt_kategori', sub.get('kategori_adi', ''))
                category_key = f"{ana_kategori}::{alt_kategori}"
                
                checkbox = QCheckBox(alt_kategori)
                checkbox.setObjectName("contentCheckbox")
                self.content_checkboxes[category_key] = {
                    'checkbox': checkbox,
                    'data': sub
                }
                frame_layout.addWidget(checkbox)

            frame.setLayout(frame_layout)
            self.content_layout.addWidget(frame)

        self.content_layout.addStretch()

    def set_view_mode(self):
        """Görüntüleme moduna geç"""
        self.is_edit_mode = False
        self.mode_stack.setCurrentIndex(0)
        self.view_mode_btn.setObjectName("modeButtonActive")
        self.edit_mode_btn.setObjectName("modeButton")
        self.view_mode_btn.style().unpolish(self.view_mode_btn)
        self.edit_mode_btn.style().unpolish(self.edit_mode_btn)
        self.view_mode_btn.style().polish(self.view_mode_btn)
        self.edit_mode_btn.style().polish(self.edit_mode_btn)
        
        if self.current_view_account:
            self.load_account_categories_view(self.current_view_account)

    def set_edit_mode(self):
        """Düzenleme moduna geç"""
        self.is_edit_mode = True
        self.mode_stack.setCurrentIndex(1)
        self.edit_mode_btn.setObjectName("modeButtonActive")
        self.view_mode_btn.setObjectName("modeButton")
        self.view_mode_btn.style().unpolish(self.view_mode_btn)
        self.edit_mode_btn.style().unpolish(self.edit_mode_btn)
        self.view_mode_btn.style().polish(self.view_mode_btn)
        self.edit_mode_btn.style().polish(self.edit_mode_btn)

    def show_add_category_dialog(self):
        """Kategori ekleme dialog'unu göster"""
        dialog = AddCategoryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_category_data()
            if data['ana_kategori']:
                if mysql_manager.add_hierarchical_category(
                    data['kategori_turu'], 
                    data['ana_kategori'], 
                    data['alt_kategori'], 
                    data['aciklama']
                ):
                    self.show_info(f"✅ Kategori eklendi: {data['ana_kategori']}" + 
                                 (f" > {data['alt_kategori']}" if data['alt_kategori'] else ""))
                    self.load_categories()
                    self.load_profile_categories()
                    self.load_content_categories()
                else:
                    self.show_warning("Bu kategori zaten mevcut!")
            else:
                self.show_warning("Ana kategori adı boş olamaz!")

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
            self.status_label.setText("Hesap seçin")

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
            status_text = f"✅ Seçili: {selected_count} hesap"
            if self.current_view_account:
                mode_text = "👁️ Görüntülenen" if not self.is_edit_mode else "✏️ Düzenlenen"
                status_text += f" | {mode_text}: {self.current_view_account}"
            self.status_label.setText(status_text)

    def load_account_categories_view(self, account):
        """Hesabın kategorilerini görüntüleme modunda göster"""
        try:
            account_categories = mysql_manager.get_account_categories(account, self.selected_account_type)
            
            if not account_categories:
                self.view_text.setHtml("""
                <div style='padding: 20px; text-align: center; color: #666;'>
                    <h3>Bu hesaba henüz kategori atanmamış</h3>
                    <p>Düzenleme moduna geçerek kategori atayabilirsiniz.</p>
                </div>
                """)
                return

            # HTML formatında kategorileri göster
            html = f"""
            <div style='font-family: Arial, sans-serif; padding: 15px;'>
                <h2 style='color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 5px;'>
                    👤 {account} - Kategori Bilgileri
                </h2>
            """

            # Profil kategorileri
            profile_cats = [cat for cat in account_categories if cat.get('kategori_turu') == 'profil']
            if profile_cats:
                html += """
                <h3 style='color: #e67e22; margin-top: 20px;'>📋 Profil Kategorileri</h3>
                <ul style='list-style: none; padding: 0;'>
                """
                for cat in profile_cats:
                    ana = cat.get('ana_kategori', '')
                    alt = cat.get('alt_kategori', '')
                    deger = cat.get('kategori_degeri', '')
                    
                    display_name = f"{ana}" + (f" > {alt}" if alt and alt != ana else "")
                    html += f"""
                    <li style='background: #f8f9fa; margin: 5px 0; padding: 10px; border-left: 4px solid #e67e22; border-radius: 4px;'>
                        <strong>{display_name}:</strong> {deger}
                    </li>
                    """
                html += "</ul>"

            # İçerik kategorileri  
            content_cats = [cat for cat in account_categories if cat.get('kategori_turu') == 'icerik']
            if content_cats:
                html += """
                <h3 style='color: #27ae60; margin-top: 20px;'>📂 İçerik Kategorileri</h3>
                <div style='display: flex; flex-wrap: wrap; gap: 10px;'>
                """
                for cat in content_cats:
                    ana = cat.get('ana_kategori', '')
                    alt = cat.get('alt_kategori', '')
                    
                    display_name = f"{ana}" + (f" > {alt}" if alt and alt != ana else "")
                    html += f"""
                    <span style='background: #d5f4e6; color: #27ae60; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold;'>
                        {display_name}
                    </span>
                    """
                html += "</div>"

            html += "</div>"
            self.view_text.setHtml(html)

        except Exception as e:
            self.show_error(f"Kategoriler görüntülenirken hata: {str(e)}")

    def load_account_categories_edit(self, account):
        """Hesabın kategorilerini düzenleme modunda yükle"""
        try:
            # Önce tüm seçimleri temizle
            self.clear_category_selections()

            # Hesabın kategorilerini getir
            account_categories = mysql_manager.get_account_categories(account, self.selected_account_type)

            # Profil kategorilerini ayarla
            for cat in account_categories:
                if cat.get('kategori_turu') == 'profil':
                    ana_kategori = cat.get('ana_kategori', '')
                    alt_kategori = cat.get('alt_kategori', '')
                    
                    if ana_kategori in self.profile_groups:
                        group_data = self.profile_groups[ana_kategori]
                        # Doğru alt kategoriyi bul ve seç
                        for i, sub_cat in enumerate(group_data['categories']):
                            if sub_cat.get('alt_kategori') == alt_kategori:
                                button = group_data['group'].button(i)
                                if button:
                                    button.setChecked(True)
                                break

                # İçerik kategorilerini ayarla
                elif cat.get('kategori_turu') == 'icerik':
                    ana_kategori = cat.get('ana_kategori', '')
                    alt_kategori = cat.get('alt_kategori', '')
                    category_key = f"{ana_kategori}::{alt_kategori}"
                    
                    if category_key in self.content_checkboxes:
                        self.content_checkboxes[category_key]['checkbox'].setChecked(True)

        except Exception as e:
            self.show_error(f"Kategoriler yüklenirken hata: {str(e)}")

    def clear_category_selections(self):
        """Kategori seçimlerini temizle"""
        # Profil kategorilerini temizle
        for group_data in self.profile_groups.values():
            group_data['none_button'].setChecked(True)

        # İçerik kategorilerini temizle
        for checkbox_data in self.content_checkboxes.values():
            checkbox_data['checkbox'].setChecked(False)

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
            self.show_warning("⚠️ Kategori atamak için en az bir hesap seçin!")
            return

        try:
            saved_count = 0

            for account in self.selected_accounts:
                # Önce hesabın kategorilerini sil
                mysql_manager.delete_account_categories(account, self.selected_account_type)

                # Profil kategorilerini kaydet
                for ana_kategori, group_data in self.profile_groups.items():
                    selected_button = group_data['group'].checkedButton()
                    button_id = group_data['group'].id(selected_button)
                    
                    if button_id >= 0:  # -1 = "Belirtilmemiş"
                        selected_category = group_data['categories'][button_id]
                        mysql_manager.assign_hierarchical_category_to_account(
                            account, 
                            self.selected_account_type,
                            selected_category.get('ana_kategori'),
                            selected_category.get('alt_kategori'),
                            selected_category.get('aciklama', 'Seçili')
                        )

                # İçerik kategorilerini kaydet
                for category_key, checkbox_data in self.content_checkboxes.items():
                    if checkbox_data['checkbox'].isChecked():
                        cat_data = checkbox_data['data']
                        mysql_manager.assign_hierarchical_category_to_account(
                            account,
                            self.selected_account_type,
                            cat_data.get('ana_kategori'),
                            cat_data.get('alt_kategori'),
                            'Aktif'
                        )

                saved_count += 1

            self.show_info(f"✅ {saved_count} hesap için kategoriler başarıyla kaydedildi!")

        except Exception as e:
            self.show_error(f"❌ Kategoriler kaydedilirken hata: {str(e)}")

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
                    if self.is_edit_mode:
                        self.load_account_categories_edit(self.current_view_account)
                    else:
                        self.load_account_categories_view(self.current_view_account)
            except Exception as e:
                self.show_error(f"Hesap kategorileri içe aktarma hatası: {str(e)}")

    def return_to_main(self):
        """Ana menüye dön"""
        self.return_callback()

    def setup_style(self):
        """Geliştirilmiş stil ayarları"""
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

        #importButton, #addButton {{
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
        }}

        #categoryGroupFrame {{
            background: {self.colors['background_alt']};
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            margin: 8px 0px;
            padding: 12px;
        }}

        #categoryGroupTitle {{
            font-size: 15px;
            font-weight: 700;
            color: {self.colors['text_primary']};
            margin-bottom: 8px;
            padding-bottom: 5px;
            border-bottom: 2px solid {self.colors['primary']};
        }}

        #profileRadio {{
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

        #viewText {{
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            background: white;
            padding: 10px;
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
        msg.setWindowTitle("✅ Bilgi")
        msg.setText(message)
        msg.exec_()

    def show_warning(self, message):
        """Uyarı mesajı"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("⚠️ Uyarı")
        msg.setText(message)
        msg.exec_()

    def show_error(self, message):
        """Hata mesajı"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("❌ Hata")
        msg.setText(message)
        msg.exec_()
