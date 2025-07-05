from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QMessageBox, QListWidget, QLineEdit,
                             QCheckBox, QGroupBox, QSpinBox, QTextEdit, QListWidgetItem,
                             QSplitter, QFileDialog, QInputDialog, QComboBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import os
from database.mysql import mysql_manager

class TargetWindow(QWidget):
    def __init__(self, colors, return_callback):
        super().__init__()
        self.colors = colors
        self.return_callback = return_callback
        self.targets = []

        self.init_ui()
        self.setup_style()
        self.load_targets()

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
        title_label = QLabel("🧭 Hedef Hesaplar")
        title_label.setObjectName("pageTitle")

        # İstatistik labels
        self.stats_label = QLabel("📊 Yükleniyor...")
        self.stats_label.setObjectName("statsLabel")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.stats_label)

        # Kontrol paneli
        control_panel = self.create_control_panel()

        # Ana içerik - Tablo
        content_panel = self.create_content_panel()

        # Layout'a ekle
        layout.addLayout(header_layout)
        layout.addWidget(control_panel)
        layout.addWidget(content_panel, 1)

        self.setLayout(layout)

    def create_control_panel(self):
        """Kontrol panelini oluştur"""
        panel = QFrame()
        panel.setObjectName("controlPanel")
        layout = QHBoxLayout()

        # Sol grup - Ekleme işlemleri
        add_group = QGroupBox("➕ Hesap Ekleme")
        add_group.setObjectName("settingsGroup")
        add_layout = QHBoxLayout()

        # Manuel ekleme
        self.username_entry = QLineEdit()
        self.username_entry.setObjectName("inputField")
        self.username_entry.setPlaceholderText("Kullanıcı adı giriniz...")

        self.year_spin = QSpinBox()
        self.year_spin.setObjectName("inputField")
        self.year_spin.setRange(2020, 2030)
        self.year_spin.setValue(2024)
        self.year_spin.setSpecialValueText("Yıl seç")
        self.year_spin.setMinimum(0)

        self.month_spin = QSpinBox()
        self.month_spin.setObjectName("inputField")
        self.month_spin.setRange(1, 12)
        self.month_spin.setValue(1)
        self.month_spin.setSpecialValueText("Ay seç")
        self.month_spin.setMinimum(0)

        add_btn = QPushButton("Ekle")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self.add_single_target)
        add_btn.setCursor(Qt.PointingHandCursor)

        add_layout.addWidget(QLabel("Kullanıcı Adı:"))
        add_layout.addWidget(self.username_entry)
        add_layout.addWidget(QLabel("Yıl:"))
        add_layout.addWidget(self.year_spin)
        add_layout.addWidget(QLabel("Ay:"))
        add_layout.addWidget(self.month_spin)
        add_layout.addWidget(add_btn)
        add_group.setLayout(add_layout)

        # Orta grup - Dosya işlemleri
        file_group = QGroupBox("📁 Dosya İşlemleri")
        file_group.setObjectName("settingsGroup")
        file_layout = QVBoxLayout()

        import_btn = QPushButton("📥 .txt Dosyasından İçe Aktar")
        import_btn.setObjectName("secondaryButton")
        import_btn.clicked.connect(self.import_from_file)
        import_btn.setCursor(Qt.PointingHandCursor)

        export_btn = QPushButton("📤 .txt Dosyasına Aktar")
        export_btn.setObjectName("accentButton")
        export_btn.clicked.connect(self.export_to_file)
        export_btn.setCursor(Qt.PointingHandCursor)

        file_layout.addWidget(import_btn)
        file_layout.addWidget(export_btn)
        file_group.setLayout(file_layout)

        # Sağ grup - Toplu işlemler
        bulk_group = QGroupBox("🔧 Toplu İşlemler")
        bulk_group.setObjectName("settingsGroup")
        bulk_layout = QVBoxLayout()

        select_all_btn = QPushButton("☑️ Tümünü Seç")
        select_all_btn.setObjectName("warningButton")
        select_all_btn.clicked.connect(self.select_all)
        select_all_btn.setCursor(Qt.PointingHandCursor)

        delete_selected_btn = QPushButton("🗑️ Seçilenleri Sil")
        delete_selected_btn.setObjectName("errorButton")
        delete_selected_btn.clicked.connect(self.delete_selected)
        delete_selected_btn.setCursor(Qt.PointingHandCursor)

        bulk_layout.addWidget(select_all_btn)
        bulk_layout.addWidget(delete_selected_btn)
        bulk_group.setLayout(bulk_layout)

        # Layout'a ekle
        layout.addWidget(add_group)
        layout.addWidget(file_group)
        layout.addWidget(bulk_group)
        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def create_content_panel(self):
        """İçerik panelini oluştur"""
        panel = QFrame()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout()

        # Tablo
        self.table = QTableWidget()
        self.table.setObjectName("dataTable")
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "☑️", "👤 Kullanıcı Adı", "📅 Yıl", "🗓️ Ay", "📝 Notlar", "🕒 Eklenme Tarihi"
        ])

        # Tablo ayarları
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        # Kolon genişlikleri
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Kullanıcı adı
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Yıl
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # Ay
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Notlar

        self.table.setColumnWidth(0, 50)   # Checkbox
        self.table.setColumnWidth(2, 80)   # Yıl
        self.table.setColumnWidth(3, 60)   # Ay

        # Sağ tık menüsü
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.table)
        panel.setLayout(layout)
        return panel

    def load_targets(self):
        """Hedef hesapları yükle"""
        self.targets = mysql_manager.get_all_targets()
        self.update_table()
        self.update_stats()

    def update_table(self):
        """Tabloyu güncelle"""
        self.table.setRowCount(len(self.targets))

        for row, target in enumerate(self.targets):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setObjectName("tableCheckbox")
            self.table.setCellWidget(row, 0, checkbox)

            # Kullanıcı adı
            username_item = QTableWidgetItem(target.get('kullanici_adi', ''))
            username_item.setFlags(username_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, username_item)

            # Yıl
            year_text = str(target.get('yil', '')) if target.get('yil') else '-'
            year_item = QTableWidgetItem(year_text)
            self.table.setItem(row, 2, year_item)

            # Ay
            month_text = str(target.get('ay', '')) if target.get('ay') else '-'
            month_item = QTableWidgetItem(month_text)
            self.table.setItem(row, 3, month_item)

            # Notlar
            notes_text = target.get('notlar', '') or ''
            notes_item = QTableWidgetItem(notes_text)
            self.table.setItem(row, 4, notes_item)

            # Eklenme tarihi
            date_text = target.get('olusturma_tarihi', '').strftime('%d.%m.%Y %H:%M') if target.get('olusturma_tarihi') else ''
            date_item = QTableWidgetItem(date_text)
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 5, date_item)

        # Tablo güncelleme sinyali
        self.table.cellChanged.connect(self.on_cell_changed)

    def update_stats(self):
        """İstatistikleri güncelle"""
        stats = mysql_manager.get_target_stats()
        stats_text = f"📊 Toplam: {stats.get('toplam', 0)} | 🟢 Aktif: {stats.get('aktif', 0)} | 📅 Tarihli: {stats.get('tarihli', 0)}"
        self.stats_label.setText(stats_text)

    def add_single_target(self):
        """Tek hedef hesap ekle"""
        username = self.username_entry.text().strip()
        if not username:
            self.show_warning("Kullanıcı adı boş olamaz!")
            return

        year = self.year_spin.value() if self.year_spin.value() > 0 else None
        month = self.month_spin.value() if self.month_spin.value() > 0 else None

        if mysql_manager.add_target(username, year, month):
            self.show_info(f"✅ {username} hedef hesaplara eklendi!")
            self.username_entry.clear()
            self.load_targets()
        else:
            self.show_error("Hedef hesap eklenirken hata oluştu!")

    def import_from_file(self):
        """Dosyadan içe aktar"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Hedef Hesapları İçe Aktar",
            "",
            "Text files (*.txt);;All files (*.*)"
        )

        if file_path:
            imported_count = mysql_manager.import_targets_from_file(file_path)
            if imported_count > 0:
                self.show_info(f"✅ {imported_count} hedef hesap içe aktarıldı!")
                self.load_targets()
            else:
                self.show_error("Hiçbir hedef hesap içe aktarılamadı!")

    def export_to_file(self):
        """Dosyaya aktar"""
        if not self.targets:
            self.show_warning("Aktarılacak hedef hesap bulunamadı!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Hedef Hesapları Dışa Aktar",
            "hedef_hesaplar.txt",
            "Text files (*.txt);;All files (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for target in self.targets:
                        username = target.get('kullanici_adi', '')
                        year = target.get('yil', '')
                        month = target.get('ay', '')

                        if year and month:
                            f.write(f"{username}:{year}:{month}\n")
                        else:
                            f.write(f"{username}\n")

                self.show_info(f"✅ {len(self.targets)} hedef hesap dışa aktarıldı!")

            except Exception as e:
                self.show_error(f"Dışa aktarma hatası: {str(e)}")

    def select_all(self):
        """Tümünü seç/seçimi kaldır"""
        # İlk checkbox'un durumunu kontrol et
        first_checkbox = self.table.cellWidget(0, 0)
        if first_checkbox:
            new_state = not first_checkbox.isChecked()

            # Tüm checkbox'ları aynı duruma getir
            for row in range(self.table.rowCount()):
                checkbox = self.table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(new_state)

    def delete_selected(self):
        """Seçili hedef hesapları sil"""
        selected_usernames = []

        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                username_item = self.table.item(row, 1)
                if username_item:
                    selected_usernames.append(username_item.text())

        if not selected_usernames:
            self.show_warning("Silinecek hedef hesap seçiniz!")
            return

        # Onay iste
        reply = QMessageBox.question(
            self,
            "Onay",
            f"{len(selected_usernames)} hedef hesap silinecek. Emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            deleted_count = 0
            for username in selected_usernames:
                if mysql_manager.delete_target(username):
                    deleted_count += 1

            self.show_info(f"✅ {deleted_count} hedef hesap silindi!")
            self.load_targets()

    def on_cell_changed(self, row, column):
        """Hücre değiştiğinde güncelle"""
        if column in [2, 3, 4]:  # Yıl, Ay, Notlar
            username_item = self.table.item(row, 1)
            if not username_item:
                return

            username = username_item.text()

            # Yeni değerleri al
            year_item = self.table.item(row, 2)
            month_item = self.table.item(row, 3)
            notes_item = self.table.item(row, 4)

            year = None
            month = None
            notes = None

            if year_item and year_item.text() and year_item.text() != '-':
                try:
                    year = int(year_item.text())
                except ValueError:
                    pass

            if month_item and month_item.text() and month_item.text() != '-':
                try:
                    month = int(month_item.text())
                    if month < 1 or month > 12:
                        month = None
                except ValueError:
                    pass

            if notes_item:
                notes = notes_item.text()

            # Güncelle
            mysql_manager.add_target(username, year, month, notes)

    def show_context_menu(self, position):
        """Sağ tık menüsünü göster"""
        # Basit bir sağ tık menüsü için şimdilik pas geç
        pass

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

        #statsLabel {{
            font-size: 14px;
            font-weight: 600;
            color: {self.colors['text_secondary']};
            background: {self.colors['background_alt']};
            padding: 8px 16px;
            border-radius: 20px;
        }}

        #controlPanel {{
            background: {self.colors['card_bg']};
            border: 1px solid {self.colors['border']};
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0px;
        }}

        #contentPanel {{
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

        #primaryButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary']}, 
                stop:1 {self.colors['primary_end']});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
        }}

        #primaryButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['primary_hover']}, 
                stop:1 {self.colors['primary']});
        }}

        #secondaryButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['secondary']}, 
                stop:1 {self.colors['secondary_hover']});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
        }}

        #secondaryButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['secondary_hover']}, 
                stop:1 {self.colors['secondary']});
        }}

        #accentButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['accent']}, 
                stop:1 {self.colors['accent_hover']});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
        }}

        #accentButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['accent_hover']}, 
                stop:1 {self.colors['accent']});
        }}

        #warningButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['warning']}, 
                stop:1 {self.colors['warning_hover']});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
        }}

        #warningButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['warning_hover']}, 
                stop:1 {self.colors['warning']});
        }}

        #errorButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['error']}, 
                stop:1 {self.colors['error_hover']});
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
        }}

        #errorButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['error_hover']}, 
                stop:1 {self.colors['error']});
        }}

        #dataTable {{
            background: {self.colors['background']};
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            gridline-color: {self.colors['border']};
            selection-background-color: {self.colors['primary']};
            selection-color: white;
            font-size: 13px;
        }}

        #dataTable::item {{
            padding: 8px;
            border: none;
        }}

        #dataTable::item:alternate {{
            background: {self.colors['background_alt']};
        }}

        #dataTable::item:selected {{
            background: {self.colors['primary']};
            color: white;
        }}

        #dataTable QHeaderView::section {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['gradient_start']}, 
                stop:1 {self.colors['gradient_end']});
            color: white;
            padding: 10px;
            border: none;
            font-weight: 600;
            font-size: 13px;
        }}

        #tableCheckbox {{
            margin: 5px;
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
        """

        self.setStyleSheet(style)

    def return_to_main(self):
        """Ana menüye dön"""
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