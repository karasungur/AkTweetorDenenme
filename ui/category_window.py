
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QMessageBox, QListWidget, QListWidgetItem,
                             QComboBox, QLineEdit, QTextEdit, QGroupBox, QSplitter,
                             QTreeWidget, QTreeWidgetItem, QFileDialog, QProgressBar,
                             QTabWidget, QGridLayout, QScrollArea, QButtonGroup, QRadioButton,
                             QCheckBox)
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
        self.import_type = import_type
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
        self.selected_account_type = 'giris_yapilan'  # Varsayılan
        self.accounts = []
        self.categories = []
        self.selected_accounts = set()

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

        # İmport/Export butonları
        import_export_layout = QHBoxLayout()
        
        import_categories_btn = QPushButton("📁 Kategori Dosyası İçe Aktar")
        import_categories_btn.setObjectName("importButton")
        import_categories_btn.clicked.connect(self.import_categories_file)
        import_categories_btn.setCursor(Qt.PointingHandCursor)
        
        import_account_categories_btn = QPushButton("📁 Hesap Kategorileri İçe Aktar")
        import_account_categories_btn.setObjectName("importButton")
        import_account_categories_btn.clicked.connect(self.import_account_categories_file)
        import_account_categories_btn.setCursor(Qt.PointingHandCursor)

        import_export_layout.addWidget(import_categories_btn)
        import_export_layout.addWidget(import_account_categories_btn)
        import_export_layout.addStretch()

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

        main_splitter.setSizes([400, 600])

        # Layout'a ekle
        layout.addLayout(header_layout)
        layout.addLayout(import_export_layout)
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

        # Soru etiketi
        question_label = QLabel("Hangi hesaplara işlem yapmak istiyorsunuz?")
        question_label.setObjectName("questionLabel")

        # Radio butonlar
        self.account_type_group = QButtonGroup()

        login_radio = QRadioButton("🔐 Giriş Yapılan Hesaplar")
        login_radio.setObjectName("accountTypeRadio")
        login_radio.setChecked(True)
        self.account_type_group.addButton(login_radio, 0)

        target_radio = QRadioButton("🎯 Hedef Hesaplar")
        target_radio.setObjectName("accountTypeRadio")
        self.account_type_group.addButton(target_radio, 1)

        # Signal bağlantısı
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

        # Üst kontroller
        controls_layout = QHBoxLayout()

        # Tümünü seç checkbox
        self.select_all_checkbox = QCheckBox("Tümünü Seç")
        self.select_all_checkbox.setObjectName("selectAllCheckbox")
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)

        # Hesap sayısı
        self.account_count_label = QLabel("0 hesap")
        self.account_count_label.setObjectName("countLabel")

        # Yenile butonu
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.clicked.connect(self.load_accounts)
        refresh_btn.setCursor(Qt.PointingHandCursor)

        controls_layout.addWidget(self.select_all_checkbox)
        controls_layout.addWidget(self.account_count_label)
        controls_layout.addStretch()
        controls_layout.addWidget(refresh_btn)

        # Hesap listesi
        self.accounts_list = QListWidget()
        self.accounts_list.setObjectName("accountsList")
        self.accounts_list.itemClicked.connect(self.on_account_clicked)
        self.accounts_list.itemChanged.connect(self.on_account_item_changed)

        layout.addLayout(controls_layout)
        layout.addWidget(self.accounts_list, 1)

        panel.setLayout(layout)
        return panel

    def create_categories_panel(self):
        """Kategori atama paneli"""
        panel = QGroupBox("🏷️ Kategori Atama")
        panel.setObjectName("categoriesPanel")
        layout = QVBoxLayout()

        # Seçili hesap bilgisi
        self.selected_info_label = QLabel("Hesap seçilmedi")
        self.selected_info_label.setObjectName("selectedInfoLabel")

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setObjectName("categoryScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Kategori widget
        category_widget = QWidget()
        self.category_layout = QVBoxLayout()
        self.category_layout.setSpacing(15)

        # Kategori gruplarını oluştur
        self.create_category_groups()

        category_widget.setLayout(self.category_layout)
        scroll_area.setWidget(category_widget)

        # Alt kontroller
        controls_layout = QHBoxLayout()

        # Temizle butonu
        clear_btn = QPushButton("🗑️ Seçimleri Temizle")
        clear_btn.setObjectName("clearButton")
        clear_btn.clicked.connect(self.clear_selections)
        clear_btn.setCursor(Qt.PointingHandCursor)

        # Kaydet butonu
        save_btn = QPushButton("💾 Kategorileri Kaydet")
        save_btn.setObjectName("saveButton")
        save_btn.clicked.connect(self.save_categories)
        save_btn.setCursor(Qt.PointingHandCursor)

        controls_layout.addWidget(clear_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(save_btn)

        # Layout'a ekle
        layout.addWidget(self.selected_info_label)
        layout.addWidget(scroll_area, 1)
        layout.addLayout(controls_layout)

        panel.setLayout(layout)
        return panel

    def create_category_groups(self):
        """Kategori gruplarını oluştur"""
        # Önceki widget'ları temizle
        for i in reversed(range(self.category_layout.count())):
            child = self.category_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Profil kategorileri (Radio Button)
        profile_group = self.create_profile_categories()
        self.category_layout.addWidget(profile_group)

        # İçerik kategorileri (Checkbox)
        content_group = self.create_content_categories()
        self.category_layout.addWidget(content_group)

        # Boş alan
        self.category_layout.addStretch()

    def create_profile_categories(self):
        """Profil kategorileri grubu (Radio Button)"""
        group = QGroupBox("👤 Profil Kategorileri")
        group.setObjectName("profileCategoriesGroup")
        layout = QVBoxLayout()

        # Yaş grubu
        age_frame = QFrame()
        age_frame.setObjectName("categoryFrame")
        age_layout = QVBoxLayout()
        age_layout.setContentsMargins(15, 10, 15, 10)

        age_label = QLabel("🧓 Yaş Grubu")
        age_label.setObjectName("categoryLabel")
        age_layout.addWidget(age_label)

        self.age_group = QButtonGroup()
        age_options = [
            ("young", "Genç (18-30)"),
            ("middle", "Orta yaş (31-50)"),
            ("old", "Yaşlı (50+)")
        ]

        for value, text in age_options:
            radio = QRadioButton(text)
            radio.setObjectName("categoryRadio")
            self.age_group.addButton(radio)
            radio.value = value
            age_layout.addWidget(radio)

        age_frame.setLayout(age_layout)
        layout.addWidget(age_frame)

        # Cinsiyet
        gender_frame = QFrame()
        gender_frame.setObjectName("categoryFrame")
        gender_layout = QVBoxLayout()
        gender_layout.setContentsMargins(15, 10, 15, 10)

        gender_label = QLabel("🚻 Cinsiyet")
        gender_label.setObjectName("categoryLabel")
        gender_layout.addWidget(gender_label)

        self.gender_group = QButtonGroup()
        gender_options = [
            ("male", "Erkek"),
            ("female", "Kadın"),
            ("other", "Belirtmeyen / Diğer")
        ]

        for value, text in gender_options:
            radio = QRadioButton(text)
            radio.setObjectName("categoryRadio")
            self.gender_group.addButton(radio)
            radio.value = value
            gender_layout.addWidget(radio)

        gender_frame.setLayout(gender_layout)
        layout.addWidget(gender_frame)

        # Profil fotoğrafı
        photo_frame = QFrame()
        photo_frame.setObjectName("categoryFrame")
        photo_layout = QVBoxLayout()
        photo_layout.setContentsMargins(15, 10, 15, 10)

        photo_label = QLabel("📸 Profil Fotoğrafı")
        photo_label.setObjectName("categoryLabel")
        photo_layout.addWidget(photo_label)

        self.photo_group = QButtonGroup()
        self.photo_yes = QRadioButton("Fotoğraf var")
        self.photo_no = QRadioButton("Fotoğraf yok")
        self.photo_yes.setObjectName("categoryRadio")
        self.photo_no.setObjectName("categoryRadio")

        self.photo_group.addButton(self.photo_yes)
        self.photo_group.addButton(self.photo_no)

        # Fotoğraf içeriği (koşullu gösterim)
        self.photo_content_frame = QFrame()
        self.photo_content_frame.setObjectName("subCategoryFrame")
        self.photo_content_frame.setVisible(False)
        photo_content_layout = QVBoxLayout()
        photo_content_layout.setContentsMargins(20, 10, 10, 10)

        photo_content_label = QLabel("🖼️ Fotoğrafın İçeriği")
        photo_content_label.setObjectName("subCategoryLabel")
        photo_content_layout.addWidget(photo_content_label)

        self.photo_content_group = QButtonGroup()
        photo_content_options = [
            ("self", "Kendi Fotoğrafı"),
            ("erdogan", "Erdoğan Fotoğrafı"),
            ("flag", "Bayrak"),
            ("landscape", "Manzara"),
            ("other", "Diğer")
        ]

        for value, text in photo_content_options:
            radio = QRadioButton(text)
            radio.setObjectName("subCategoryRadio")
            self.photo_content_group.addButton(radio)
            radio.value = value
            photo_content_layout.addWidget(radio)

        self.photo_content_frame.setLayout(photo_content_layout)

        # Fotoğraf var/yok kontrolü
        self.photo_yes.toggled.connect(self.on_photo_option_changed)

        photo_layout.addWidget(self.photo_yes)
        photo_layout.addWidget(self.photo_no)
        photo_layout.addWidget(self.photo_content_frame)

        photo_frame.setLayout(photo_layout)
        layout.addWidget(photo_frame)

        group.setLayout(layout)
        return group

    def create_content_categories(self):
        """İçerik kategorileri grubu (Checkbox)"""
        group = QGroupBox("📝 Profil İçerik Kategorileri")
        group.setObjectName("contentCategoriesGroup")
        layout = QVBoxLayout()

        content_frame = QFrame()
        content_frame.setObjectName("categoryFrame")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(15, 10, 15, 10)

        content_label = QLabel("📂 İçerik Türleri (Birden fazla seçilebilir)")
        content_label.setObjectName("categoryLabel")
        content_layout.addWidget(content_label)

        # İçerik kategorileri
        self.content_checkboxes = {}
        content_options = [
            ("religious", "Dini İçerik"),
            ("political", "Siyasi İçerik"),
            ("humor", "Mizah"),
            ("sports", "Spor"),
            ("news", "Haber"),
            ("entertainment", "Eğlence"),
            ("education", "Eğitim"),
            ("technology", "Teknoloji"),
            ("art", "Sanat"),
            ("lifestyle", "Yaşam Tarzı")
        ]

        for value, text in content_options:
            checkbox = QCheckBox(text)
            checkbox.setObjectName("categoryCheckbox")
            checkbox.value = value
            self.content_checkboxes[value] = checkbox
            content_layout.addWidget(checkbox)

        content_frame.setLayout(content_layout)
        layout.addWidget(content_frame)

        group.setLayout(layout)
        return group

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

            # Listeye ekle
            for account in self.accounts:
                item = QListWidgetItem(account)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.accounts_list.addItem(item)

            self.account_count_label.setText(f"{len(self.accounts)} hesap")

        except Exception as e:
            self.show_error(f"Hesaplar yüklenirken hata: {str(e)}")

    def on_select_all_changed(self, state):
        """Tümünü seç değiştiğinde"""
        check_state = Qt.Checked if state == Qt.Checked else Qt.Unchecked

        for i in range(self.accounts_list.count()):
            item = self.accounts_list.item(i)
            item.setCheckState(check_state)

    def on_account_clicked(self, item):
        """Hesaba tıklandığında"""
        # Sadece tek hesap seçimi için kategorileri yükle
        account = item.text()
        self.load_account_categories(account)
        self.selected_info_label.setText(f"🎯 Görüntülenen: {account}")

    def on_account_item_changed(self, item):
        """Hesap item'ı değiştiğinde (checkbox)"""
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

        if selected_count == 0:
            self.selected_info_label.setText("Hesap seçilmedi")
        elif selected_count == 1:
            account = list(self.selected_accounts)[0]
            self.selected_info_label.setText(f"🎯 Seçili: {account}")
            self.load_account_categories(account)
        else:
            self.selected_info_label.setText(f"🎯 {selected_count} hesap seçili")

    def on_photo_option_changed(self, checked):
        """Fotoğraf seçeneği değiştiğinde"""
        self.photo_content_frame.setVisible(checked)

    def load_categories(self):
        """Kategorileri yükle"""
        try:
            self.categories = mysql_manager.get_categories()
        except Exception as e:
            self.show_error(f"Kategoriler yüklenirken hata: {str(e)}")

    def load_account_categories(self, account):
        """Hesabın kategorilerini yükle"""
        try:
            account_categories = mysql_manager.get_account_categories(account, self.selected_account_type)

            # Kategori seçimlerini temizle
            self.clear_category_selections()

            # Hesabın kategorilerini işaretle
            for cat in account_categories:
                # Profil kategorilerini işaretle
                if cat['ana_kategori'] == 'Yaş Grubu':
                    for button in self.age_group.buttons():
                        if hasattr(button, 'value') and button.value == cat['kategori_degeri']:
                            button.setChecked(True)
                            break

                elif cat['ana_kategori'] == 'Cinsiyet':
                    for button in self.gender_group.buttons():
                        if hasattr(button, 'value') and button.value == cat['kategori_degeri']:
                            button.setChecked(True)
                            break

                elif cat['ana_kategori'] == 'Profil Fotoğrafı':
                    if cat['kategori_degeri'] == 'var':
                        self.photo_yes.setChecked(True)
                    else:
                        self.photo_no.setChecked(True)

                elif cat['ana_kategori'] == 'Fotoğraf İçeriği':
                    for button in self.photo_content_group.buttons():
                        if hasattr(button, 'value') and button.value == cat['kategori_degeri']:
                            button.setChecked(True)
                            break

                # İçerik kategorilerini işaretle
                elif cat['kategori_degeri'] in self.content_checkboxes:
                    self.content_checkboxes[cat['kategori_degeri']].setChecked(True)

        except Exception as e:
            self.show_error(f"Hesap kategorileri yüklenirken hata: {str(e)}")

    def clear_category_selections(self):
        """Kategori seçimlerini temizle"""
        # Radio button gruplarını temizle
        for group in [self.age_group, self.gender_group, self.photo_group, self.photo_content_group]:
            checked = group.checkedButton()
            if checked:
                checked.setChecked(False)

        # Checkbox'ları temizle
        for checkbox in self.content_checkboxes.values():
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
            self.show_warning("Önce hesap seçin!")
            return

        try:
            saved_count = 0

            for account in self.selected_accounts:
                # Önce hesabın kategorilerini sil
                mysql_manager.delete_account_categories(account, self.selected_account_type)

                # Kategori ID'lerini al
                category_mappings = self.get_category_id_mappings()

                # Profil kategorilerini kaydet
                # Yaş grubu
                age_checked = self.age_group.checkedButton()
                if age_checked and hasattr(age_checked, 'value'):
                    age_cat_id = category_mappings.get(('Yaş Grubu', None))
                    if age_cat_id:
                        mysql_manager.assign_category_to_account(account, self.selected_account_type, age_cat_id, age_checked.value)

                # Cinsiyet
                gender_checked = self.gender_group.checkedButton()
                if gender_checked and hasattr(gender_checked, 'value'):
                    gender_cat_id = category_mappings.get(('Cinsiyet', None))
                    if gender_cat_id:
                        mysql_manager.assign_category_to_account(account, self.selected_account_type, gender_cat_id, gender_checked.value)

                # Profil fotoğrafı
                photo_checked = self.photo_group.checkedButton()
                if photo_checked:
                    photo_value = 'var' if photo_checked == self.photo_yes else 'yok'
                    photo_cat_id = category_mappings.get(('Profil Fotoğrafı', None))
                    if photo_cat_id:
                        mysql_manager.assign_category_to_account(account, self.selected_account_type, photo_cat_id, photo_value)

                    # Fotoğraf içeriği
                    if photo_checked == self.photo_yes:
                        photo_content_checked = self.photo_content_group.checkedButton()
                        if photo_content_checked and hasattr(photo_content_checked, 'value'):
                            content_cat_id = category_mappings.get(('Fotoğraf İçeriği', None))
                            if content_cat_id:
                                mysql_manager.assign_category_to_account(account, self.selected_account_type, content_cat_id, photo_content_checked.value)

                # İçerik kategorilerini kaydet
                for value, checkbox in self.content_checkboxes.items():
                    if checkbox.isChecked():
                        content_cat_id = category_mappings.get(('İçerik Türü', None))
                        if content_cat_id:
                            mysql_manager.assign_category_to_account(account, self.selected_account_type, content_cat_id, value)

                saved_count += 1

            self.show_info(f"✅ {saved_count} hesap için kategoriler kaydedildi!")

        except Exception as e:
            self.show_error(f"Kategoriler kaydedilirken hata: {str(e)}")

    def get_category_id_mappings(self):
        """Kategori ID eşlemelerini al"""
        mappings = {}
        categories = mysql_manager.get_categories()
        
        for cat in categories:
            key = (cat['ana_kategori'], cat['alt_kategori'])
            mappings[key] = cat['id']
        
        return mappings

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
                self.create_category_groups()
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
                # Seçili hesap varsa kategorilerini yenile
                if self.selected_accounts:
                    account = list(self.selected_accounts)[0]
                    self.load_account_categories(account)
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

        #backButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5A6268, stop:1 #495057);
        }}

        #importButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #17A2B8, stop:1 #138496);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 12px;
            font-weight: 600;
            margin: 5px;
        }}

        #importButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #138496, stop:1 #117A8B);
        }}

        #questionLabel {{
            font-size: 16px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            padding: 10px;
        }}

        #accountTypeRadio {{
            font-size: 15px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            spacing: 8px;
        }}

        #accountTypeRadio::indicator {{
            width: 20px;
            height: 20px;
            border-radius: 10px;
            border: 2px solid {self.colors['border']};
            background: {self.colors['background']};
        }}

        #accountTypeRadio::indicator:checked {{
            background: {self.colors['primary']};
            border: 2px solid {self.colors['primary']};
        }}

        #selectAllCheckbox {{
            font-size: 14px;
            font-weight: 600;
            color: {self.colors['text_primary']};
        }}

        #countLabel {{
            font-size: 12px;
            color: {self.colors['text_secondary']};
            padding: 5px;
        }}

        #refreshButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary']}, stop:1 {self.colors['primary_end']});
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
        }}

        #selectedInfoLabel {{
            font-size: 16px;
            font-weight: 600;
            color: {self.colors['primary']};
            padding: 15px;
            background: {self.colors['background_alt']};
            border-radius: 8px;
            border: 1px solid {self.colors['border']};
        }}

        #categoryLabel {{
            font-size: 15px;
            font-weight: 700;
            color: {self.colors['text_primary']};
            padding: 8px 0px;
        }}

        #subCategoryLabel {{
            font-size: 14px;
            font-weight: 600;
            color: {self.colors['text_secondary']};
            padding: 5px 0px;
        }}

        #categoryRadio {{
            font-size: 14px;
            font-weight: 500;
            color: {self.colors['text_primary']};
            spacing: 8px;
            padding: 5px;
        }}

        #subCategoryRadio {{
            font-size: 13px;
            font-weight: 500;
            color: {self.colors['text_secondary']};
            spacing: 8px;
            padding: 3px;
        }}

        #categoryCheckbox {{
            font-size: 14px;
            font-weight: 500;
            color: {self.colors['text_primary']};
            spacing: 8px;
            padding: 5px;
        }}

        #categoryCheckbox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 2px solid {self.colors['border']};
            background: {self.colors['background']};
        }}

        #categoryCheckbox::indicator:checked {{
            background: {self.colors['primary']};
            border: 2px solid {self.colors['primary']};
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

        QGroupBox {{
            font-weight: 600;
            font-size: 14px;
            color: {self.colors['text_primary']};
            border: 2px solid {self.colors['border']};
            border-radius: 8px;
            margin: 5px;
            padding-top: 15px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px;
            background: {self.colors['background']};
        }}

        #categoryFrame {{
            background: {self.colors['background']};
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            margin: 5px 0px;
        }}

        #subCategoryFrame {{
            background: {self.colors['background_alt']};
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            margin: 10px 0px;
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

        QScrollArea {{
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            background: {self.colors['background']};
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
