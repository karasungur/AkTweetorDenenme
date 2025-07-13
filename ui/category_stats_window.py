
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QMessageBox, QDialog, QDialogButtonBox,
                             QTabWidget, QScrollArea, QGroupBox, QGridLayout,
                             QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                             QProgressBar, QComboBox, QCheckBox, QSplitter, QSpacerItem,
                             QSizePolicy, QApplication)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QBrush, QLinearGradient
import io
import base64

# Matplotlib import'unu try-except ile koruyalım
try:
    import matplotlib
    matplotlib.use('Agg')  # Backend'i Agg olarak ayarla (GUI olmayan)
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    plt.style.use('seaborn-v0_8')  # Modern stil
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ Matplotlib bulunamadı. Grafikler devre dışı.")
except Exception as e:
    MATPLOTLIB_AVAILABLE = False
    print(f"⚠️ Matplotlib yükleme hatası: {e}")

# Database imports'ını güvenli hale getirelim
try:
    from database.mysql import mysql_manager
    from database.user_manager import user_manager
except ImportError as e:
    print(f"⚠️ Database modül import hatası: {e}")
    mysql_manager = None
    user_manager = None

import json
from collections import Counter, defaultdict
from datetime import datetime

class ModernStatsCard(QFrame):
    """Modern istatistik kartı"""
    def __init__(self, icon, title, value, color="#3b82f6"):
        super().__init__()
        self.setObjectName("statsCard")
        self.value_text = value
        self.setup_ui(icon, title, color)
        
    def setup_ui(self, icon, title, color):
        """Kart UI'yi ayarla"""
        self.setStyleSheet(f"""
            QFrame#statsCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}, stop:1 {self.darken_color(color)});
                border: none;
                border-radius: 16px;
                padding: 20px;
                margin: 8px;
                min-height: 120px;
            }}
            QLabel {{
                color: white;
                background: transparent;
                border: none;
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Üst kısım - icon ve title
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(50, 50)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: 600; opacity: 0.9;")
        title_label.setWordWrap(True)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Değer
        self.value_label = QLabel(self.value_text)
        self.value_label.setStyleSheet("font-size: 36px; font-weight: 800; margin-top: 10px;")
        self.value_label.setAlignment(Qt.AlignCenter)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.value_label)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def darken_color(self, color):
        """Rengi koyulaştır"""
        color_map = {
            "#3b82f6": "#2563eb",
            "#10b981": "#059669", 
            "#f59e0b": "#d97706",
            "#ef4444": "#dc2626",
            "#8b5cf6": "#7c3aed",
            "#06b6d4": "#0891b2"
        }
        return color_map.get(color, "#1f2937")
    
    def update_value(self, new_value):
        """Değeri güncelle"""
        self.value_label.setText(str(new_value))

class CategoryStatsDialog(QDialog):
    """Kategori istatistikleri dialog'u - Modern tasarım"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Kategori İstatistikleri ve Analiz")
        self.setModal(True)
        self.resize(1400, 900)
        
        # Modern stil
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                border: none;
                border-radius: 0px;
            }
            QTabWidget::pane {
                border: none;
                background: white;
                border-radius: 16px;
                margin-top: 10px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f1f5f9, stop:1 #e2e8f0);
                padding: 14px 24px;
                margin-right: 4px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border: none;
                font-weight: 600;
                font-size: 14px;
                color: #64748b;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e2e8f0, stop:1 #cbd5e1);
            }
            QTableWidget {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                gridline-color: #f1f5f9;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f1f5f9;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #f1f5f9);
                padding: 12px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: 600;
                color: #374151;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb, stop:1 #1d4ed8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1d4ed8, stop:1 #1e40af);
            }
            QComboBox {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                min-width: 120px;
            }
            QComboBox:focus {
                border-color: #3b82f6;
            }
            QCheckBox {
                font-size: 13px;
                color: #374151;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #d1d5db;
                border-radius: 4px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #3b82f6;
                border-color: #3b82f6;
            }
        """)
        
        self.setup_ui()
        self.load_statistics()
        
    def setup_ui(self):
        """UI'yi ayarla"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Modern başlık
        header_frame = QFrame()
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📊 Kategori İstatistikleri")
        title_label.setStyleSheet("""
            font-size: 32px;
            font-weight: 800;
            color: #1e293b;
            margin-bottom: 8px;
        """)
        
        subtitle_label = QLabel("Detaylı analiz ve görselleştirmeler")
        subtitle_label.setStyleSheet("""
            font-size: 16px;
            color: #64748b;
            font-weight: 500;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(subtitle_label)
        
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Sekmeleri oluştur
        self.dashboard_tab = self.create_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "📈 Dashboard")
        
        self.distribution_tab = self.create_distribution_tab()
        self.tabs.addTab(self.distribution_tab, "🥧 Dağılım")
        
        self.detailed_tab = self.create_detailed_analysis_tab()
        self.tabs.addTab(self.detailed_tab, "🔍 Detaylı Analiz")
        
        self.charts_tab = self.create_charts_tab()
        self.tabs.addTab(self.charts_tab, "📊 Grafikler")
        
        layout.addWidget(self.tabs, 1)
        
        # Alt butonlar
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.load_statistics)
        
        export_btn = QPushButton("📤 Dışa Aktar")
        export_btn.clicked.connect(self.export_statistics)
        
        close_btn = QPushButton("✅ Kapat")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def create_dashboard_tab(self):
        """Dashboard sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Üst kısım - İstatistik kartları
        cards_frame = QFrame()
        cards_layout = QGridLayout()
        cards_layout.setSpacing(15)
        
        # Kartları oluştur
        self.total_categories_card = ModernStatsCard("📋", "Toplam Kategori", "0", "#3b82f6")
        self.total_accounts_card = ModernStatsCard("👥", "Toplam Hesap", "0", "#10b981")
        self.categorized_card = ModernStatsCard("✅", "Kategorili", "0", "#f59e0b")
        self.uncategorized_card = ModernStatsCard("❌", "Kategorisiz", "0", "#ef4444")
        
        cards_layout.addWidget(self.total_categories_card, 0, 0)
        cards_layout.addWidget(self.total_accounts_card, 0, 1)
        cards_layout.addWidget(self.categorized_card, 0, 2)
        cards_layout.addWidget(self.uncategorized_card, 0, 3)
        
        cards_frame.setLayout(cards_layout)
        layout.addWidget(cards_frame)
        
        # Alt kısım - Özet tablosu
        table_frame = QGroupBox("📊 Kategori Özeti")
        table_frame.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #374151;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 8px;
                background: white;
            }
        """)
        
        table_layout = QVBoxLayout()
        
        self.general_table = QTableWidget()
        self.general_table.setColumnCount(4)
        self.general_table.setHorizontalHeaderLabels(["Ana Kategori", "Alt Kategori", "Hesap Sayısı", "Kullanım %"])
        self.general_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.general_table.setAlternatingRowColors(True)
        
        table_layout.addWidget(self.general_table)
        table_frame.setLayout(table_layout)
        
        layout.addWidget(table_frame, 1)
        
        widget.setLayout(layout)
        return widget
        
    def create_distribution_tab(self):
        """Dağılım sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Kontrol paneli
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        control_layout = QHBoxLayout()
        
        type_label = QLabel("📊 Hesap Türü:")
        type_label.setStyleSheet("font-weight: 600; color: #374151;")
        
        self.account_type_combo = QComboBox()
        self.account_type_combo.addItems(["Giriş Yapılan", "Hedef Hesaplar", "Tümü"])
        self.account_type_combo.currentTextChanged.connect(self.update_distribution)
        
        control_layout.addWidget(type_label)
        control_layout.addWidget(self.account_type_combo)
        control_layout.addStretch()
        
        control_frame.setLayout(control_layout)
        layout.addWidget(control_frame)
        
        # Dağılım tablosu
        self.distribution_table = QTableWidget()
        self.distribution_table.setColumnCount(3)
        self.distribution_table.setHorizontalHeaderLabels(["Kategori", "Hesap Sayısı", "Yüzde"])
        self.distribution_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.distribution_table, 1)
        
        widget.setLayout(layout)
        return widget
        
    def create_detailed_analysis_tab(self):
        """Detaylı analiz sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Filtre paneli
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel("🔍 Filtreler:")
        filter_label.setStyleSheet("font-weight: 600; color: #374151;")
        
        self.show_empty_categories = QCheckBox("Boş kategoriler")
        self.show_empty_categories.setChecked(True)
        self.show_empty_categories.stateChanged.connect(self.update_detailed_analysis)
        
        min_label = QLabel("Minimum:")
        self.min_count_combo = QComboBox()
        self.min_count_combo.addItems(["Tümü", "En az 1", "En az 5", "En az 10"])
        self.min_count_combo.currentTextChanged.connect(self.update_detailed_analysis)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.show_empty_categories)
        filter_layout.addWidget(min_label)
        filter_layout.addWidget(self.min_count_combo)
        filter_layout.addStretch()
        
        filter_frame.setLayout(filter_layout)
        layout.addWidget(filter_frame)
        
        # Detaylı tablo
        self.detailed_table = QTableWidget()
        self.detailed_table.setColumnCount(6)
        self.detailed_table.setHorizontalHeaderLabels([
            "Ana Kategori", "Alt Kategori", "Toplam", 
            "Giriş Yapılan", "Hedef", "Yüzde"
        ])
        self.detailed_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.detailed_table, 1)
        
        widget.setLayout(layout)
        return widget
        
    def create_charts_tab(self):
        """Grafikler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Grafik kontrolleri
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        control_layout = QHBoxLayout()
        
        type_label = QLabel("📊 Grafik Türü:")
        type_label.setStyleSheet("font-weight: 600; color: #374151;")
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Pasta", "Çubuk", "Yatay Çubuk"])
        self.chart_type_combo.currentTextChanged.connect(self.update_chart)
        
        data_label = QLabel("📋 Veri:")
        self.chart_data_combo = QComboBox()
        self.chart_data_combo.addItems(["Ana Kategoriler", "Tümü", "En Popüler 10"])
        self.chart_data_combo.currentTextChanged.connect(self.update_chart)
        
        control_layout.addWidget(type_label)
        control_layout.addWidget(self.chart_type_combo)
        control_layout.addWidget(data_label)
        control_layout.addWidget(self.chart_data_combo)
        control_layout.addStretch()
        
        control_frame.setLayout(control_layout)
        layout.addWidget(control_frame)
        
        # Grafik alanı
        self.chart_frame = QFrame()
        self.chart_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                min-height: 500px;
            }
        """)
        
        layout.addWidget(self.chart_frame, 1)
        
        widget.setLayout(layout)
        return widget
        
    def load_statistics(self):
        """İstatistikleri yükle"""
        try:
            if not mysql_manager or not user_manager:
                self.show_error("Veritabanı bağlantısı bulunamadı!")
                return
            
            # Kategorileri al
            categories = mysql_manager.get_categories('icerik')
            
            # Hesapları al
            login_accounts = user_manager.get_all_users()
            target_accounts = mysql_manager.get_all_targets()
            
            # Ana kategorileri say
            main_categories = set()
            for cat in categories:
                ana_kat = cat.get('ana_kategori', '')
                if ana_kat:
                    main_categories.add(ana_kat)
            
            total_categories = len(main_categories)
            total_login = len(login_accounts)
            total_target = len(target_accounts)
            total_accounts = total_login + total_target
            
            # Kategorili hesapları say
            categorized_login = 0
            categorized_target = 0
            
            for acc in login_accounts:
                if mysql_manager.get_account_categories(acc['kullanici_adi'], 'giris_yapilan'):
                    categorized_login += 1
                    
            for acc in target_accounts:
                if mysql_manager.get_account_categories(acc['kullanici_adi'], 'hedef'):
                    categorized_target += 1
            
            categorized_total = categorized_login + categorized_target
            uncategorized_total = total_accounts - categorized_total
            
            # Kartları güncelle
            self.total_categories_card.update_value(total_categories)
            self.total_accounts_card.update_value(total_accounts)
            self.categorized_card.update_value(categorized_total)
            self.uncategorized_card.update_value(uncategorized_total)
            
            # Tabloları güncelle
            self.update_general_table()
            self.update_distribution()
            self.update_detailed_analysis()
            self.update_chart()
            
        except Exception as e:
            self.show_error(f"İstatistikler yüklenirken hata: {str(e)}")
            
    def update_general_table(self):
        """Genel tabloyu güncelle"""
        try:
            categories = mysql_manager.get_categories('icerik')
            
            # Kategorileri grupla
            category_stats = {}
            
            for cat in categories:
                ana_kat = cat.get('ana_kategori', '')
                alt_kat = cat.get('alt_kategori', '')
                
                if ana_kat not in category_stats:
                    category_stats[ana_kat] = {
                        'sub_count': 0,
                        'account_count': 0
                    }
                
                if alt_kat:
                    category_stats[ana_kat]['sub_count'] += 1
                
                # Hesap sayısını hesapla
                login_count = 0
                target_count = 0
                
                for acc in user_manager.get_all_users():
                    acc_cats = mysql_manager.get_account_categories(acc['kullanici_adi'], 'giris_yapilan')
                    for acc_cat in acc_cats:
                        if acc_cat.get('ana_kategori') == ana_kat:
                            login_count += 1
                            break
                
                for acc in mysql_manager.get_all_targets():
                    acc_cats = mysql_manager.get_account_categories(acc['kullanici_adi'], 'hedef')
                    for acc_cat in acc_cats:
                        if acc_cat.get('ana_kategori') == ana_kat:
                            target_count += 1
                            break
                
                category_stats[ana_kat]['account_count'] = login_count + target_count
            
            # Tabloyu doldur
            self.general_table.setRowCount(len(category_stats))
            total_accounts = len(user_manager.get_all_users()) + len(mysql_manager.get_all_targets())
            
            for row, (ana_kat, stats) in enumerate(category_stats.items()):
                self.general_table.setItem(row, 0, QTableWidgetItem(ana_kat))
                self.general_table.setItem(row, 1, QTableWidgetItem(str(stats['sub_count'])))
                self.general_table.setItem(row, 2, QTableWidgetItem(str(stats['account_count'])))
                
                percentage = (stats['account_count'] / total_accounts * 100) if total_accounts > 0 else 0
                self.general_table.setItem(row, 3, QTableWidgetItem(f"{percentage:.1f}%"))
                
        except Exception as e:
            print(f"Genel tablo güncelleme hatası: {e}")
            
    def update_distribution(self):
        """Dağılım tablosunu güncelle"""
        try:
            account_type = self.account_type_combo.currentText()
            
            # Hesapları al
            if account_type == "Giriş Yapılan":
                accounts = [(acc['kullanici_adi'], 'giris_yapilan') for acc in user_manager.get_all_users()]
            elif account_type == "Hedef Hesaplar":
                accounts = [(acc['kullanici_adi'], 'hedef') for acc in mysql_manager.get_all_targets()]
            else:
                accounts = ([(acc['kullanici_adi'], 'giris_yapilan') for acc in user_manager.get_all_users()] +
                          [(acc['kullanici_adi'], 'hedef') for acc in mysql_manager.get_all_targets()])
            
            # Kategori sayımı
            category_counts = Counter()
            
            for username, acc_type in accounts:
                categories = mysql_manager.get_account_categories(username, acc_type)
                for cat in categories:
                    ana_kat = cat.get('ana_kategori', '')
                    alt_kat = cat.get('alt_kategori', '')
                    
                    if alt_kat:
                        category_counts[f"{ana_kat} → {alt_kat}"] += 1
                    else:
                        category_counts[ana_kat] += 1
            
            # Tabloyu doldur
            self.distribution_table.setRowCount(len(category_counts))
            total_assignments = sum(category_counts.values())
            
            for row, (category, count) in enumerate(category_counts.most_common()):
                self.distribution_table.setItem(row, 0, QTableWidgetItem(category))
                self.distribution_table.setItem(row, 1, QTableWidgetItem(str(count)))
                
                percentage = (count / total_assignments * 100) if total_assignments > 0 else 0
                self.distribution_table.setItem(row, 2, QTableWidgetItem(f"{percentage:.1f}%"))
                
        except Exception as e:
            print(f"Dağılım güncelleme hatası: {e}")
            
    def update_detailed_analysis(self):
        """Detaylı analiz tablosunu güncelle"""
        try:
            show_empty = self.show_empty_categories.isChecked()
            min_count_text = self.min_count_combo.currentText()
            
            if min_count_text == "Tümü":
                min_count = 0
            elif "En az" in min_count_text:
                min_count = int(min_count_text.split()[-1])
            else:
                min_count = 0
            
            categories = mysql_manager.get_categories('icerik')
            detailed_data = []
            
            for cat in categories:
                ana_kat = cat.get('ana_kategori', '')
                alt_kat = cat.get('alt_kategori', '')
                
                # Hesap sayılarını hesapla
                login_count = 0
                target_count = 0
                
                for acc in user_manager.get_all_users():
                    acc_cats = mysql_manager.get_account_categories(acc['kullanici_adi'], 'giris_yapilan')
                    for acc_cat in acc_cats:
                        if (acc_cat.get('ana_kategori') == ana_kat and 
                            (not alt_kat or acc_cat.get('alt_kategori') == alt_kat)):
                            login_count += 1
                            break
                
                for acc in mysql_manager.get_all_targets():
                    acc_cats = mysql_manager.get_account_categories(acc['kullanici_adi'], 'hedef')
                    for acc_cat in acc_cats:
                        if (acc_cat.get('ana_kategori') == ana_kat and 
                            (not alt_kat or acc_cat.get('alt_kategori') == alt_kat)):
                            target_count += 1
                            break
                
                total_count = login_count + target_count
                
                # Filtreleme
                if not show_empty and total_count == 0:
                    continue
                if total_count < min_count:
                    continue
                
                detailed_data.append({
                    'ana_kategori': ana_kat,
                    'alt_kategori': alt_kat or '-',
                    'login_count': login_count,
                    'target_count': target_count,
                    'total_count': total_count
                })
            
            # Tabloyu doldur
            self.detailed_table.setRowCount(len(detailed_data))
            total_accounts = len(user_manager.get_all_users()) + len(mysql_manager.get_all_targets())
            
            for row, data in enumerate(detailed_data):
                self.detailed_table.setItem(row, 0, QTableWidgetItem(data['ana_kategori']))
                self.detailed_table.setItem(row, 1, QTableWidgetItem(data['alt_kategori']))
                self.detailed_table.setItem(row, 2, QTableWidgetItem(str(data['total_count'])))
                self.detailed_table.setItem(row, 3, QTableWidgetItem(str(data['login_count'])))
                self.detailed_table.setItem(row, 4, QTableWidgetItem(str(data['target_count'])))
                
                percentage = (data['total_count'] / total_accounts * 100) if total_accounts > 0 else 0
                self.detailed_table.setItem(row, 5, QTableWidgetItem(f"{percentage:.1f}%"))
                
        except Exception as e:
            print(f"Detaylı analiz güncelleme hatası: {e}")
            
    def update_chart(self):
        """Grafikleri güncelle"""
        try:
            if not MATPLOTLIB_AVAILABLE:
                self.show_empty_chart("📊 Grafik modülü bulunamadı\nMatplotlib yüklü değil")
                return
                
            chart_type = self.chart_type_combo.currentText()
            data_type = self.chart_data_combo.currentText()
            
            # Veri toplama
            category_counts = Counter()
            
            all_accounts = ([(acc['kullanici_adi'], 'giris_yapilan') for acc in user_manager.get_all_users()] +
                          [(acc['kullanici_adi'], 'hedef') for acc in mysql_manager.get_all_targets()])
            
            for username, acc_type in all_accounts:
                account_categories = mysql_manager.get_account_categories(username, acc_type)
                for cat in account_categories:
                    ana_kat = cat.get('ana_kategori', '')
                    alt_kat = cat.get('alt_kategori', '')
                    
                    if data_type == "Ana Kategoriler":
                        if ana_kat:
                            category_counts[ana_kat] += 1
                    else:
                        if alt_kat:
                            category_counts[f"{ana_kat} → {alt_kat}"] += 1
                        elif ana_kat:
                            category_counts[ana_kat] += 1
            
            # En popüler 10 filtreleme
            if data_type == "En Popüler 10":
                category_counts = dict(category_counts.most_common(10))
            
            if not category_counts:
                self.show_empty_chart("📊 Gösterilecek veri bulunamadı")
                return
            
            # Grafik oluştur
            self.create_modern_chart(chart_type, category_counts)
            
        except Exception as e:
            print(f"Grafik güncelleme hatası: {e}")
            self.show_empty_chart(f"📊 Grafik oluşturulamadı\n{str(e)}")
            
    def create_modern_chart(self, chart_type, data):
        """Modern grafik oluştur"""
        if not MATPLOTLIB_AVAILABLE:
            self.show_empty_chart("📊 Grafik oluşturulamadı\nMatplotlib kütüphanesi bulunamadı")
            return
            
        try:
            # Modern renkler
            colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', 
                     '#84cc16', '#f97316', '#ec4899', '#14b8a6']
            
            plt.ioff()
            fig, ax = plt.subplots(figsize=(12, 8))
            fig.patch.set_facecolor('white')
            
            labels = list(data.keys())
            values = list(data.values())
            
            if chart_type == "Pasta":
                wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                                 colors=colors[:len(labels)], startangle=90,
                                                 textprops={'fontsize': 10, 'fontweight': 'bold'})
                ax.set_title("Kategori Dağılımı", fontsize=18, fontweight='bold', pad=20)
                
                # Pasta grafiğini güzelleştir
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                    
            elif chart_type == "Çubuk":
                bars = ax.bar(range(len(labels)), values, 
                            color=colors[:len(labels)], alpha=0.8, edgecolor='white', linewidth=2)
                
                ax.set_xlabel("Kategoriler", fontsize=14, fontweight='bold')
                ax.set_ylabel("Hesap Sayısı", fontsize=14, fontweight='bold')
                ax.set_title("Kategori Kullanım İstatistikleri", fontsize=18, fontweight='bold', pad=20)
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
                
                # Değerleri bars üzerine yaz
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                               f'{int(height)}', ha='center', va='bottom', 
                               fontsize=10, fontweight='bold')
                           
            elif chart_type == "Yatay Çubuk":
                bars = ax.barh(range(len(labels)), values, 
                             color=colors[:len(labels)], alpha=0.8, edgecolor='white', linewidth=2)
                
                ax.set_ylabel("Kategoriler", fontsize=14, fontweight='bold')
                ax.set_xlabel("Hesap Sayısı", fontsize=14, fontweight='bold')
                ax.set_title("Kategori Kullanım İstatistikleri", fontsize=18, fontweight='bold', pad=20)
                ax.set_yticks(range(len(labels)))
                ax.set_yticklabels(labels, fontsize=10)
                
                # Değerleri bars sonuna yaz
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    if width > 0:
                        ax.text(width + 0.5, bar.get_y() + bar.get_height()/2.,
                               f'{int(width)}', ha='left', va='center', 
                               fontsize=10, fontweight='bold')
            
            # Grid ve stil
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.set_facecolor('#f8fafc')
            
            plt.tight_layout()
            
            # PNG olarak kaydet
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            
            # QPixmap'e dönüştür
            pixmap = QPixmap()
            success = pixmap.loadFromData(buffer.getvalue())
            
            if success:
                self.show_chart_image(pixmap)
            else:
                self.show_empty_chart("📊 Grafik gösterilemedi")
            
            # Bellek temizliği
            plt.close(fig)
            buffer.close()
            
        except Exception as e:
            print(f"Grafik oluşturma hatası: {e}")
            self.show_empty_chart(f"📊 Grafik oluşturulamadı\n{str(e)}")
            
    def show_chart_image(self, pixmap):
        """Grafik resmini göster"""
        # Önceki içeriği temizle
        for child in self.chart_frame.findChildren(QLabel):
            child.deleteLater()
        
        # Scroll area ekle
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none; background: white;")
        
        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("background: white; padding: 20px;")
        
        scroll_area.setWidget(label)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)
        
        self.chart_frame.setLayout(layout)
        
    def show_empty_chart(self, message):
        """Boş grafik mesajı göster"""
        for child in self.chart_frame.findChildren(QLabel):
            child.deleteLater()
        
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            color: #64748b; 
            font-size: 18px; 
            font-weight: 600;
            background: white;
            padding: 40px;
        """)
        
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.chart_frame.setLayout(layout)
        
    def export_statistics(self):
        """İstatistikleri dışa aktar"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path, _ = QFileDialog.getSaveFileName(
                self, "İstatistikleri Kaydet", 
                f"kategori_istatistikleri_{timestamp}.json",
                "JSON Dosyaları (*.json);;Metin Dosyaları (*.txt)"
            )
            
            if file_path:
                stats_data = {
                    'export_date': datetime.now().isoformat(),
                    'total_categories': self.total_categories_card.value_text,
                    'total_accounts': self.total_accounts_card.value_text,
                    'categorized_accounts': self.categorized_card.value_text,
                    'uncategorized_accounts': self.uncategorized_card.value_text,
                    'detailed_data': self.get_detailed_export_data()
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(stats_data, f, ensure_ascii=False, indent=2)
                    
                QMessageBox.information(self, "✅ Başarılı", f"İstatistikler başarıyla kaydedildi:\n{file_path}")
                
        except Exception as e:
            QMessageBox.warning(self, "❌ Hata", f"İstatistikler kaydedilirken hata:\n{str(e)}")
            
    def get_detailed_export_data(self):
        """Detaylı dışa aktarma verisi hazırla"""
        try:
            categories = mysql_manager.get_categories('icerik')
            detailed_data = []
            
            for cat in categories:
                ana_kat = cat.get('ana_kategori', '')
                alt_kat = cat.get('alt_kategori', '')
                
                login_accounts = []
                target_accounts = []
                
                for acc in user_manager.get_all_users():
                    acc_cats = mysql_manager.get_account_categories(acc['kullanici_adi'], 'giris_yapilan')
                    for acc_cat in acc_cats:
                        if (acc_cat.get('ana_kategori') == ana_kat and 
                            (not alt_kat or acc_cat.get('alt_kategori') == alt_kat)):
                            login_accounts.append(acc['kullanici_adi'])
                            break
                
                for acc in mysql_manager.get_all_targets():
                    acc_cats = mysql_manager.get_account_categories(acc['kullanici_adi'], 'hedef')
                    for acc_cat in acc_cats:
                        if (acc_cat.get('ana_kategori') == ana_kat and 
                            (not alt_kat or acc_cat.get('alt_kategori') == alt_kat)):
                            target_accounts.append(acc['kullanici_adi'])
                            break
                
                if login_accounts or target_accounts:
                    detailed_data.append({
                        'ana_kategori': ana_kat,
                        'alt_kategori': alt_kat,
                        'login_accounts': login_accounts,
                        'target_accounts': target_accounts,
                        'total_count': len(login_accounts) + len(target_accounts)
                    })
            
            return detailed_data
            
        except Exception as e:
            print(f"Detaylı veri hazırlama hatası: {e}")
            return []
    
    def show_error(self, message):
        """Hata mesajı göster"""
        QMessageBox.critical(self, "❌ Hata", message)
        
    def closeEvent(self, event):
        """Dialog kapandığında bellek temizliği"""
        try:
            if MATPLOTLIB_AVAILABLE:
                plt.close('all')
                plt.clf()
        except:
            pass
        event.accept()
        
    def __del__(self):
        """Destructor - bellek temizliği"""
        try:
            if MATPLOTLIB_AVAILABLE:
                plt.close('all')
        except:
            pass
