from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QGroupBox, QTabWidget, QWidget, QFileDialog,
                             QTextEdit, QProgressBar, QMessageBox, QCheckBox,
                             QComboBox, QSpinBox, QFormLayout, QFrame, QSplitter,
                             QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
                             QHeaderView)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from database.mysql import mysql_manager
from database.user_manager import user_manager
import json
import csv
import os
from datetime import datetime
import openpyxl

class AdvancedImportThread(QThread):
    """Gelişmiş içe aktarma thread'i"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    log = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, operation_type, file_paths, options):
        super().__init__()
        self.operation_type = operation_type
        self.file_paths = file_paths
        self.options = options

    def run(self):
        try:
            if self.operation_type == "batch_import":
                self.batch_import_files()
            elif self.operation_type == "excel_import":
                self.import_from_excel()
            elif self.operation_type == "merge_categories":
                self.merge_category_files()
            elif self.operation_type == "validate_data":
                self.validate_import_data()

        except Exception as e:
            self.error.emit(str(e))

    def batch_import_files(self):
        """Toplu dosya içe aktarma"""
        total_files = len(self.file_paths)
        imported_categories = 0
        imported_accounts = 0

        for i, file_path in enumerate(self.file_paths):
            self.status.emit(f"İşleniyor: {os.path.basename(file_path)}")

            try:
                if file_path.endswith('.json'):
                    result = self.import_json_file(file_path)
                elif file_path.endswith('.txt'):
                    result = self.import_txt_file(file_path)
                elif file_path.endswith('.csv'):
                    result = self.import_csv_file(file_path)
                else:
                    self.log.emit(f"❌ Desteklenmeyen dosya formatı: {file_path}")
                    continue

                imported_categories += result.get('categories', 0)
                imported_accounts += result.get('accounts', 0)

                self.log.emit(f"✅ {os.path.basename(file_path)}: {result.get('categories', 0)} kategori, {result.get('accounts', 0)} hesap")

            except Exception as e:
                self.log.emit(f"❌ {os.path.basename(file_path)}: {str(e)}")

            self.progress.emit(int((i + 1) / total_files * 100))

        self.finished.emit(f"Toplu içe aktarma tamamlandı: {imported_categories} kategori, {imported_accounts} hesap")

    def import_json_file(self, file_path):
        """JSON dosyası içe aktarma"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        categories_count = 0
        accounts_count = 0

        # Kategoriler
        if 'categories' in data:
            for cat in data['categories']:
                if mysql_manager.add_hierarchical_category(
                    'icerik', 
                    cat.get('ana_kategori', ''),
                    cat.get('alt_kategori'),
                    cat.get('aciklama', '')
                ):
                    categories_count += 1

        # Hesap kategorileri
        if 'account_categories' in data or 'data' in data:
            account_data = data.get('account_categories', data.get('data', []))
            for acc_cat in account_data:
                if mysql_manager.assign_hierarchical_category_to_account(
                    acc_cat.get('kullanici_adi', ''),
                    acc_cat.get('hesap_turu', 'hedef'),
                    acc_cat.get('ana_kategori', ''),
                    acc_cat.get('alt_kategori'),
                    acc_cat.get('kategori_degeri', 'İçe Aktarıldı')
                ):
                    accounts_count += 1

        return {'categories': categories_count, 'accounts': accounts_count}

    def import_txt_file(self, file_path):
        """TXT dosyası içe aktarma"""
        categories_count = 0
        accounts_count = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split(':')
                if len(parts) >= 3:
                    if parts[0] == 'icerik':  # Kategori
                        if mysql_manager.add_hierarchical_category(
                            'icerik', parts[1], 
                            parts[2] if parts[2] else None,
                            parts[3] if len(parts) > 3 else ''
                        ):
                            categories_count += 1
                    else:  # Hesap kategorisi
                        if len(parts) >= 5:
                            if mysql_manager.assign_hierarchical_category_to_account(
                                parts[0], parts[1], parts[2], 
                                parts[3] if parts[3] else None,
                                parts[4] if len(parts) > 4 else 'İçe Aktarıldı'
                            ):
                                accounts_count += 1

        return {'categories': categories_count, 'accounts': accounts_count}

    def import_csv_file(self, file_path):
        """CSV dosyası içe aktarma"""
        categories_count = 0
        accounts_count = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)

            if not header:
                return {'categories': 0, 'accounts': 0}

            # Kategori dosyası mı hesap dosyası mı kontrol et
            if 'Ana Kategori' in header and 'Kullanıcı Adı' not in header:
                # Kategori dosyası
                for row in reader:
                    if len(row) >= 2:
                        if mysql_manager.add_hierarchical_category(
                            'icerik', row[0], 
                            row[1] if row[1] else None,
                            row[2] if len(row) > 2 else ''
                        ):
                            categories_count += 1

            elif 'Kullanıcı Adı' in header:
                # Hesap kategorisi dosyası
                for row in reader:
                    if len(row) >= 4:
                        if mysql_manager.assign_hierarchical_category_to_account(
                            row[0], row[1], row[2],
                            row[3] if row[3] else None,
                            row[4] if len(row) > 4 else 'İçe Aktarıldı'
                        ):
                            accounts_count += 1

        return {'categories': categories_count, 'accounts': accounts_count}

    def import_from_excel(self):
        """Excel dosyasından içe aktarma"""
        wb = openpyxl.load_workbook(self.file_paths[0])
        imported_categories = 0
        imported_accounts = 0

        # Kategoriler sayfası
        if 'Kategoriler' in wb.sheetnames:
            ws = wb['Kategoriler']
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0]:  # Ana kategori varsa
                    if mysql_manager.add_hierarchical_category(
                        'icerik', row[0], 
                        row[1] if row[1] else None,
                        row[2] if len(row) > 2 and row[2] else ''
                    ):
                        imported_categories += 1

        # Hesap kategorileri sayfası
        if 'Hesap Kategorileri' in wb.sheetnames:
            ws = wb['Hesap Kategorileri']
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0] and row[2]:  # Kullanıcı adı ve ana kategori varsa
                    hesap_turu = 'giris_yapilan' if row[1] == 'Giriş Yapılan' else 'hedef'
                    if mysql_manager.assign_hierarchical_category_to_account(
                        row[0], hesap_turu, row[2],
                        row[3] if len(row) > 3 and row[3] else None,
                        row[4] if len(row) > 4 and row[4] else 'İçe Aktarıldı'
                    ):
                        imported_accounts += 1

        self.finished.emit(f"Excel içe aktarma tamamlandı: {imported_categories} kategori, {imported_accounts} hesap")

    def validate_import_data(self):
        """İçe aktarma verilerini doğrula"""
        validation_results = []

        for file_path in self.file_paths:
            self.status.emit(f"Doğrulanıyor: {os.path.basename(file_path)}")

            try:
                result = self.validate_file(file_path)
                validation_results.append({
                    'file': os.path.basename(file_path),
                    'valid_lines': result['valid'],
                    'invalid_lines': result['invalid'],
                    'errors': result['errors']
                })

            except Exception as e:
                validation_results.append({
                    'file': os.path.basename(file_path),
                    'valid_lines': 0,
                    'invalid_lines': 0,
                    'errors': [str(e)]
                })

        # Sonuçları logla
        for result in validation_results:
            self.log.emit(f"📁 {result['file']}")
            self.log.emit(f"  ✅ Geçerli: {result['valid_lines']}")
            self.log.emit(f"  ❌ Geçersiz: {result['invalid_lines']}")
            for error in result['errors']:
                self.log.emit(f"  🚨 {error}")
            self.log.emit("")

        self.finished.emit("Doğrulama tamamlandı")

    def validate_file(self, file_path):
        """Dosyayı doğrula"""
        valid_count = 0
        invalid_count = 0
        errors = []

        if file_path.endswith('.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                valid_count = 1
            except json.JSONDecodeError as e:
                errors.append(f"JSON formatı geçersiz: {str(e)}")
                invalid_count = 1

        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split(':')
                    if len(parts) < 3:
                        errors.append(f"Satır {line_num}: Eksik alan")
                        invalid_count += 1
                    else:
                        valid_count += 1

        return {'valid': valid_count, 'invalid': invalid_count, 'errors': errors}

class AdvancedFileOperationsDialog(QDialog):
    """Gelişmiş dosya işlemleri dialog'u"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔄 Gelişmiş İçe/Dışa Aktarma İşlemleri")
        self.setModal(True)
        self.resize(900, 700)

        self.worker_thread = None
        self.setup_ui()

    def setup_ui(self):
        """UI'yi ayarla"""
        layout = QVBoxLayout()

        # Başlık
        title_label = QLabel("🔄 Gelişmiş İçe/Dışa Aktarma İşlemleri")
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 15px;
        """)
        layout.addWidget(title_label)

        # Tab widget
        self.tabs = QTabWidget()

        # Toplu içe aktarma
        self.batch_import_tab = self.create_batch_import_tab()
        self.tabs.addTab(self.batch_import_tab, "📥 Toplu İçe Aktarma")

        # Excel işlemleri
        self.excel_tab = self.create_excel_tab()
        self.tabs.addTab(self.excel_tab, "📗 Excel İşlemleri")

        # Veri doğrulama
        self.validation_tab = self.create_validation_tab()
        self.tabs.addTab(self.validation_tab, "✅ Veri Doğrulama")

        # Yedekleme ve geri yükleme
        self.backup_tab = self.create_backup_tab()
        self.tabs.addTab(self.backup_tab, "💾 Yedekleme")

        layout.addWidget(self.tabs)

        # İlerleme ve log alanı
        progress_frame = QFrame()
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        self.status_label = QLabel("Hazır")
        self.status_label.setStyleSheet("color: #64748b; font-size: 13px;")

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setPlaceholderText("İşlem logları burada görünecek...")

        progress_layout.addWidget(QLabel("İşlem Durumu:"))
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(QLabel("İşlem Logları:"))
        progress_layout.addWidget(self.log_text)

        progress_frame.setLayout(progress_layout)
        layout.addWidget(progress_frame)

        # Butonlar
        button_layout = QHBoxLayout()

        self.clear_log_btn = QPushButton("🗑️ Logları Temizle")
        self.clear_log_btn.clicked.connect(self.log_text.clear)

        self.close_btn = QPushButton("❌ Kapat")
        self.close_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.clear_log_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def create_batch_import_tab(self):
        """Toplu içe aktarma sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Açıklama
        info_label = QLabel("""
📥 <b>Toplu İçe Aktarma:</b> Birden fazla dosyayı aynı anda içe aktarın
• JSON, TXT, CSV dosyalarını destekler
• Kategori ve hesap kategori dosyalarını otomatik tanır
• Hata durumunda diğer dosyalar işlenmeye devam eder
        """)
        info_label.setStyleSheet("background: #f0f9ff; padding: 15px; border-radius: 8px; border: 1px solid #bae6fd;")
        layout.addWidget(info_label)

        # Dosya seçimi
        file_frame = QGroupBox("Dosya Seçimi")
        file_layout = QVBoxLayout()

        file_buttons_layout = QHBoxLayout()
        self.select_files_btn = QPushButton("📁 Dosyaları Seç")
        self.select_files_btn.clicked.connect(self.select_batch_files)

        self.clear_files_btn = QPushButton("🗑️ Listeyi Temizle")
        self.clear_files_btn.clicked.connect(self.clear_file_list)

        file_buttons_layout.addWidget(self.select_files_btn)
        file_buttons_layout.addWidget(self.clear_files_btn)
        file_buttons_layout.addStretch()

        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(150)

        file_layout.addLayout(file_buttons_layout)
        file_layout.addWidget(self.file_list)
        file_frame.setLayout(file_layout)

        # Seçenekler
        options_frame = QGroupBox("İçe Aktarma Seçenekleri")
        options_layout = QFormLayout()

        self.skip_duplicates_check = QCheckBox("Mevcut kategorileri atla")
        self.skip_duplicates_check.setChecked(True)

        self.create_backup_check = QCheckBox("İşlem öncesi yedek oluştur")
        self.create_backup_check.setChecked(True)

        options_layout.addRow("Seçenekler:", self.skip_duplicates_check)
        options_layout.addRow("", self.create_backup_check)
        options_frame.setLayout(options_layout)

        # İşlem başlat
        self.start_batch_btn = QPushButton("🚀 Toplu İçe Aktarmayı Başlat")
        self.start_batch_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        self.start_batch_btn.clicked.connect(self.start_batch_import)

        layout.addWidget(file_frame)
        layout.addWidget(options_frame)
        layout.addWidget(self.start_batch_btn)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_excel_tab(self):
        """Excel işlemleri sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Excel içe aktarma
        import_frame = QGroupBox("📗 Excel Dosyasından İçe Aktarma")
        import_layout = QVBoxLayout()

        excel_info = QLabel("""
Excel dosyasında aşağıdaki sayfa adları aranır:
• <b>Kategoriler:</b> Ana Kategori, Alt Kategori, Açıklama
• <b>Hesap Kategorileri:</b> Kullanıcı Adı, Hesap Türü, Ana Kategori, Alt Kategori, Kategori Değeri
        """)
        excel_info.setStyleSheet("background: #f0fdf4; padding: 10px; border-radius: 6px; border: 1px solid #bbf7d0;")

        excel_buttons_layout = QHBoxLayout()
        self.select_excel_btn = QPushButton("📁 Excel Dosyası Seç")
        self.select_excel_btn.clicked.connect(self.select_excel_file)

        self.import_excel_btn = QPushButton("📥 Excel'den İçe Aktar")
        self.import_excel_btn.clicked.connect(self.import_from_excel)
        self.import_excel_btn.setEnabled(False)

        excel_buttons_layout.addWidget(self.select_excel_btn)
        excel_buttons_layout.addWidget(self.import_excel_btn)
        excel_buttons_layout.addStretch()

        self.excel_file_label = QLabel("Dosya seçilmedi")
        self.excel_file_label.setStyleSheet("color: #64748b; font-style: italic;")

        import_layout.addWidget(excel_info)
        import_layout.addLayout(excel_buttons_layout)
        import_layout.addWidget(self.excel_file_label)
        import_frame.setLayout(import_layout)

        # Excel şablonu indirme
        template_frame = QGroupBox("📋 Excel Şablonu")
        template_layout = QVBoxLayout()

        template_info = QLabel("Boş Excel şablonu indirerek kendi verilerinizi hazırlayabilirsiniz.")

        self.download_template_btn = QPushButton("⬇️ Excel Şablonunu İndir")
        self.download_template_btn.clicked.connect(self.download_excel_template)

        template_layout.addWidget(template_info)
        template_layout.addWidget(self.download_template_btn)
        template_frame.setLayout(template_layout)

        layout.addWidget(import_frame)
        layout.addWidget(template_frame)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_validation_tab(self):
        """Veri doğrulama sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Açıklama
        info_label = QLabel("""
✅ <b>Veri Doğrulama:</b> İçe aktarma öncesi dosyalarınızı kontrol edin
• Format hatalarını tespit eder
• Eksik alanları listeler
• İçe aktarma öncesi problemleri çözer
        """)
        info_label.setStyleSheet("background: #fefce8; padding: 15px; border-radius: 8px; border: 1px solid #fde047;")
        layout.addWidget(info_label)

        # Dosya seçimi
        validation_frame = QGroupBox("Doğrulanacak Dosyalar")
        validation_layout = QVBoxLayout()

        validation_buttons_layout = QHBoxLayout()
        self.select_validation_files_btn = QPushButton("📁 Dosyaları Seç")
        self.select_validation_files_btn.clicked.connect(self.select_validation_files)

        self.validate_btn = QPushButton("🔍 Doğrulamayı Başlat")
        self.validate_btn.clicked.connect(self.start_validation)

        validation_buttons_layout.addWidget(self.select_validation_files_btn)
        validation_buttons_layout.addWidget(self.validate_btn)
        validation_buttons_layout.addStretch()

        self.validation_file_list = QListWidget()
        self.validation_file_list.setMaximumHeight(150)

        validation_layout.addLayout(validation_buttons_layout)
        validation_layout.addWidget(self.validation_file_list)
        validation_frame.setLayout(validation_layout)

        layout.addWidget(info_label)
        layout.addWidget(validation_frame)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_backup_tab(self):
        """Yedekleme sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Açıklama
        info_label = QLabel("""
💾 <b>Yedekleme ve Geri Yükleme:</b> Verilerinizi güvenle yedekleyin
• Kategori verilerini yedekle
• Hesap kategorilerini yedekle
• Tam veritabanı yedeği oluştur
        """)
        info_label.setStyleSheet("background: #f0f9ff; padding: 15px; border-radius: 8px; border: 1px solid #0ea5e9;")
        layout.addWidget(info_label)

        # Yedekleme seçenekleri
        backup_frame = QGroupBox("Yedekleme Seçenekleri")
        backup_layout = QVBoxLayout()

        self.backup_categories_btn = QPushButton("💾 Kategorileri Yedekle")
        self.backup_categories_btn.clicked.connect(self.backup_categories)

        self.backup_accounts_btn = QPushButton("💾 Hesap Kategorilerini Yedekle")
        self.backup_accounts_btn.clicked.connect(self.backup_account_categories)

        self.full_backup_btn = QPushButton("💾 Tam Yedek Oluştur")
        self.full_backup_btn.clicked.connect(self.create_full_backup)

        backup_layout.addWidget(self.backup_categories_btn)
        backup_layout.addWidget(self.backup_accounts_btn)
        backup_layout.addWidget(self.full_backup_btn)
        backup_frame.setLayout(backup_layout)

        layout.addWidget(backup_frame)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def backup_categories(self):
        """Kategorileri yedekle"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            from datetime import datetime
            import json

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Kategori Yedeği Kaydet", 
                f"kategori_yedek_{timestamp}.json",
                "JSON Dosyaları (*.json)"
            )

            if file_path:
                if mysql_manager:
                    categories = mysql_manager.get_categories('icerik')
                    backup_data = {
                        'backup_date': datetime.now().isoformat(),
                        'backup_type': 'categories',
                        'categories': categories
                    }

                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(backup_data, f, ensure_ascii=False, indent=2)

                    QMessageBox.information(self, "Başarılı", f"Kategoriler yedeklendi:\n{file_path}")
                else:
                    QMessageBox.warning(self, "Hata", "MySQL bağlantısı bulunamadı")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Yedekleme hatası: {str(e)}")

    def backup_account_categories(self):
        """Hesap kategorilerini yedekle"""
        QMessageBox.information(self, "Bilgi", "Hesap kategorileri yedeklemesi henüz hazırlanıyor...")

    def create_full_backup(self):
        """Tam yedek oluştur"""
        QMessageBox.information(self, "Bilgi", "Tam yedekleme henüz hazırlanıyor...")

    def select_batch_files(self):
        """Toplu içe aktarma için dosyaları seç"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "İçe Aktarılacak Dosyaları Seç",
            "", "Desteklenen Dosyalar (*.json *.txt *.csv);;Tüm Dosyalar (*)"
        )

        if files:
            self.file_list.clear()
            for file_path in files:
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.UserRole, file_path)
                self.file_list.addItem(item)

    def clear_file_list(self):
        """Dosya listesini temizle"""
        self.file_list.clear()

    def select_excel_file(self):
        """Excel dosyası seç"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Excel Dosyası Seç",
            "", "Excel Dosyaları (*.xlsx *.xls)"
        )

        if file_path:
            self.excel_file_path = file_path
            self.excel_file_label.setText(os.path.basename(file_path))
            self.import_excel_btn.setEnabled(True)

    def select_validation_files(self):
        """Doğrulama için dosyaları seç"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Doğrulanacak Dosyaları Seç",
            "", "Desteklenen Dosyalar (*.json *.txt *.csv);;Tüm Dosyalar (*)"
        )

        if files:
            self.validation_file_list.clear()
            for file_path in files:
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.UserRole, file_path)
                self.validation_file_list.addItem(item)

    def select_backup_file(self):
        """Yedek dosyası seç"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Yedek Dosyası Seç",
            "", "JSON Dosyaları (*.json);;Tüm Dosyalar (*)"
        )

        if file_path:
            self.backup_file_path = file_path
            self.backup_file_label.setText(os.path.basename(file_path))
            self.restore_backup_btn.setEnabled(True)

    def start_batch_import(self):
        """Toplu içe aktarmayı başlat"""
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce dosyaları seçin!")
            return

        file_paths = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            file_paths.append(item.data(Qt.UserRole))

        options = {
            'skip_duplicates': self.skip_duplicates_check.isChecked(),
            'create_backup': self.create_backup_check.isChecked()
        }

        self.start_worker("batch_import", file_paths, options)

    def import_from_excel(self):
        """Excel'den içe aktarma"""
        if not hasattr(self, 'excel_file_path'):
            QMessageBox.warning(self, "Uyarı", "Lütfen önce Excel dosyasını seçin!")
            return

        self.start_worker("excel_import", [self.excel_file_path], {})

    def start_validation(self):
        """Doğrulamayı başlat"""
        if self.validation_file_list.count() == 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce dosyaları seçin!")
            return

        file_paths = []
        for i in range(self.validation_file_list.count()):
            item = self.validation_file_list.item(i)
            file_paths.append(item.data(Qt.UserRole))

        self.start_worker("validate_data", file_paths, {})

    def create_full_backup(self):
        """Tam yedek oluştur"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"aktweetor_backup_{timestamp}.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Yedek Dosyasını Kaydet",
            default_name, "JSON Dosyaları (*.json)"
        )

        if file_path:
            try:
                # Tüm kategori verilerini topla
                categories = mysql_manager.get_categories('icerik')

                # Tüm hesap kategorilerini topla
                all_account_categories = []

                # Giriş yapılan hesaplar
                for acc in user_manager.get_all_users():
                    acc_cats = mysql_manager.get_account_categories(acc['kullanici_adi'], 'giris_yapilan')
                    for cat in acc_cats:
                        cat['kullanici_adi'] = acc['kullanici_adi']
                        cat['hesap_turu'] = 'giris_yapilan'
                        all_account_categories.append(cat)

                # Hedef hesaplar
                for acc in mysql_manager.get_all_targets():
                    acc_cats = mysql_manager.get_account_categories(acc['kullanici_adi'], 'hedef')
                    for cat in acc_cats:
                        cat['kullanici_adi'] = acc['kullanici_adi']
                        cat['hesap_turu'] = 'hedef'
                        all_account_categories.append(cat)

                backup_data = {
                    'backup_date': datetime.now().isoformat(),
                    'version': '1.0',
                    'categories': categories,
                    'account_categories': all_account_categories
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)

                self.log_text.append(f"✅ Yedek oluşturuldu: {file_path}")
                QMessageBox.information(self, "Başarılı", "Yedek başarıyla oluşturuldu!")

            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Yedek oluşturulamadı: {str(e)}")

    def restore_backup(self):
        """Yedek geri yükle"""
        reply = QMessageBox.question(
            self, "Onay",
            "Bu işlem mevcut tüm kategori verilerini silecek ve yedekteki verilerle değiştirecektir.\n\nDevam etmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                with open(self.backup_file_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)

                # Mevcut verileri temizle (dikkatli!)
                # Bu kısım gerçek bir veritabanı işlemi olduğu için dikkatli olunmalı

                # Kategorileri geri yükle
                categories = backup_data.get('categories', [])
                for cat in categories:
                    mysql_manager.add_hierarchical_category(
                        'icerik',
                        cat.get('ana_kategori', ''),
                        cat.get('alt_kategori'),
                        cat.get('aciklama', '')
                    )

                # Hesap kategorilerini geri yükle
                account_categories = backup_data.get('account_categories', [])
                for acc_cat in account_categories:
                    mysql_manager.assign_hierarchical_category_to_account(
                        acc_cat.get('kullanici_adi', ''),
                        acc_cat.get('hesap_turu', 'hedef'),
                        acc_cat.get('ana_kategori', ''),
                        acc_cat.get('alt_kategori'),
                        acc_cat.get('kategori_degeri', 'Geri Yüklendi')
                    )

                self.log_text.append(f"✅ Yedek geri yüklendi: {len(categories)} kategori, {len(account_categories)} hesap kategorisi")
                QMessageBox.information(self, "Başarılı", "Yedek başarıyla geri yüklendi!")

            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Yedek geri yüklenemedi: {str(e)}")

    def download_excel_template(self):
        """Excel şablonunu indir"""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Excel Şablonunu Kaydet",
                "aktweetor_template.xlsx", "Excel Dosyaları (*.xlsx)"
            )

            if file_path:
                wb = openpyxl.Workbook()

                # Kategoriler sayfası
                ws_categories = wb.active
                ws_categories.title = "Kategoriler"

                headers = ['Ana Kategori', 'Alt Kategori', 'Açıklama']
                for col, header in enumerate(headers, 1):
                    cell = ws_categories.cell(row=1, column=col, value=header)
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color='DDDDDD', end_color='DDDDDD', fill_type='solid')
                    cell.alignment = Alignment(horizontal='center')

                # Örnek veriler
                example_data = [
                    ['Siyasi Eğilim', 'Muhafazakar', 'Muhafazakar görüşlü içerikler'],
                    ['Siyasi Eğilim', 'Liberal', 'Liberal görüşlü içerikler'],
                    ['Fotoğraf İçeriği', 'Parti Logosu', 'Siyasi parti logoları']
                ]

                for row, data in enumerate(example_data, 2):
                    for col, value in enumerate(data, 1):
                        ws_categories.cell(row=row, column=col, value=value)

                # Hesap kategorileri sayfası
                ws_accounts = wb.create_sheet("Hesap Kategorileri")

                headers = ['Kullanıcı Adı', 'Hesap Türü', 'Ana Kategori', 'Alt Kategori', 'Kategori Değeri']
                for col, header in enumerate(headers, 1):
                    cell = ws_accounts.cell(row=1, column=col, value=header)
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color='DDDDDD', end_color='DDDDDD', fill_type='solid')
                    cell.alignment = Alignment(horizontal='center')

                # Örnek veriler
                example_data = [
                    ['ornekkullanici1', 'Giriş Yapılan', 'Yaş Grubu', '', 'Genç (18-30)'],
                    ['ornekkullanici2', 'Hedef', 'Cinsiyet', '', 'Erkek'],
                    ['ornekkullanici3', 'Hedef', 'Siyasi Eğilim', 'Muhafazakar', 'Seçili']
                ]

                for row, data in enumerate(example_data, 2):
                    for col, value in enumerate(data, 1):
                        ws_accounts.cell(row=row, column=col, value=value)

                # Sütun genişliklerini ayarla
                for ws in wb.worksheets:
                    for column_cells in ws.columns:
                        length = max(len(str(cell.value or '')) for cell in column_cells)
                        ws.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 30)

                wb.save(file_path)

                QMessageBox.information(self, "Başarılı", f"Excel şablonu oluşturuldu:\n{file_path}")

        except ImportError:
            QMessageBox.warning(self, "Uyarı", "Excel şablonu için openpyxl kütüphanesi gerekli.\nLütfen 'pip install openpyxl' çalıştırın.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Şablon oluşturulamadı: {str(e)}")

    def start_worker(self, operation_type, file_paths, options):
        """Worker thread'i başlat"""
        self.worker_thread = AdvancedImportThread(operation_type, file_paths, options)
        self.worker_thread.progress.connect(self.progress_bar.setValue)
        self.worker_thread.status.connect(self.status_label.setText)
        self.worker_thread.log.connect(self.log_text.append)
        self.worker_thread.finished.connect(self.on_operation_finished)
        self.worker_thread.error.connect(self.on_operation_error)

        # UI'yi güncelle
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker_thread.start()

    def on_operation_finished(self, message):
        """İşlem tamamlandığında"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("✅ " + message)
        self.log_text.append("✅ " + message)

        QMessageBox.information(self, "Başarılı", message)

    def on_operation_error(self, error_message):
        """İşlem hatası"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ " + error_message)
        self.log_text.append("❌ " + error_message)

        QMessageBox.critical(self, "Hata", error_message)

    def closeEvent(self, event):
        """Dialog kapatılırken"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
        event.accept()