
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QMessageBox, QDialog, QDialogButtonBox,
                             QTabWidget, QScrollArea, QGroupBox, QGridLayout,
                             QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                             QProgressBar, QComboBox, QCheckBox, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QBrush
import io
import base64

# Matplotlib import'unu try-except ile koruyalım
try:
    import matplotlib
    matplotlib.use('Agg')  # Backend'i Agg olarak ayarla (GUI olmayan)
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ Matplotlib bulunamadı. Grafikler devre dışı.")
except Exception as e:
    MATPLOTLIB_AVAILABLE = False
    print(f"⚠️ Matplotlib yükleme hatası: {e}")
from database.mysql import mysql_manager
from database.user_manager import user_manager
import json
from collections import Counter, defaultdict

class CategoryStatsDialog(QDialog):
    """Kategori istatistikleri dialog'u"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Kategori İstatistikleri ve Analiz")
        self.setModal(True)
        self.resize(1200, 800)
        
        self.setup_ui()
        self.load_statistics()
        
    def setup_ui(self):
        """UI'yi ayarla"""
        layout = QVBoxLayout()
        
        # Başlık
        title_label = QLabel("📊 Kategori İstatistikleri ve Analiz")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 15px;
        """)
        layout.addWidget(title_label)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Genel istatistikler
        self.general_tab = self.create_general_stats_tab()
        self.tabs.addTab(self.general_tab, "📈 Genel İstatistikler")
        
        # Kategori dağılımı
        self.distribution_tab = self.create_distribution_tab()
        self.tabs.addTab(self.distribution_tab, "🥧 Kategori Dağılımı")
        
        # Detaylı analiz
        self.detailed_tab = self.create_detailed_analysis_tab()
        self.tabs.addTab(self.detailed_tab, "🔍 Detaylı Analiz")
        
        # Grafik görüntüleme
        self.charts_tab = self.create_charts_tab()
        self.tabs.addTab(self.charts_tab, "📊 Grafiksel Görünüm")
        
        layout.addWidget(self.tabs)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.load_statistics)
        
        export_btn = QPushButton("📤 İstatistikleri Dışa Aktar")
        export_btn.clicked.connect(self.export_statistics)
        
        close_btn = QPushButton("✅ Kapat")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def create_general_stats_tab(self):
        """Genel istatistikler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Özet kartları
        summary_frame = QFrame()
        summary_layout = QGridLayout()
        
        self.total_categories_label = QLabel("0")
        self.total_accounts_label = QLabel("0") 
        self.categorized_accounts_label = QLabel("0")
        self.uncategorized_accounts_label = QLabel("0")
        
        summary_layout.addWidget(self.create_stat_card("📋", "Toplam Kategori", self.total_categories_label), 0, 0)
        summary_layout.addWidget(self.create_stat_card("👥", "Toplam Hesap", self.total_accounts_label), 0, 1)
        summary_layout.addWidget(self.create_stat_card("✅", "Kategorili Hesap", self.categorized_accounts_label), 1, 0)
        summary_layout.addWidget(self.create_stat_card("❌", "Kategorisiz Hesap", self.uncategorized_accounts_label), 1, 1)
        
        summary_frame.setLayout(summary_layout)
        layout.addWidget(summary_frame)
        
        # Kategori tablosu
        self.general_table = QTableWidget()
        self.general_table.setColumnCount(4)
        self.general_table.setHorizontalHeaderLabels(["Ana Kategori", "Alt Kategori Sayısı", "Hesap Sayısı", "Kullanım %"])
        self.general_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.general_table)
        
        widget.setLayout(layout)
        return widget
        
    def create_distribution_tab(self):
        """Dağılım sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Hesap türü seçimi
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Hesap Türü:"))
        
        self.account_type_combo = QComboBox()
        self.account_type_combo.addItems(["Giriş Yapılan Hesaplar", "Hedef Hesaplar", "Tümü"])
        self.account_type_combo.currentTextChanged.connect(self.update_distribution)
        type_layout.addWidget(self.account_type_combo)
        type_layout.addStretch()
        
        layout.addLayout(type_layout)
        
        # Dağılım tablosu
        self.distribution_table = QTableWidget()
        self.distribution_table.setColumnCount(3)
        self.distribution_table.setHorizontalHeaderLabels(["Kategori", "Hesap Sayısı", "Yüzde"])
        layout.addWidget(self.distribution_table)
        
        widget.setLayout(layout)
        return widget
        
    def create_detailed_analysis_tab(self):
        """Detaylı analiz sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Analiz seçenekleri
        options_frame = QFrame()
        options_layout = QHBoxLayout()
        
        self.show_empty_categories = QCheckBox("Boş kategorileri göster")
        self.show_empty_categories.setChecked(True)
        self.show_empty_categories.stateChanged.connect(self.update_detailed_analysis)
        
        self.min_count_combo = QComboBox()
        self.min_count_combo.addItems(["Tümü", "En az 1", "En az 5", "En az 10", "En az 20"])
        self.min_count_combo.currentTextChanged.connect(self.update_detailed_analysis)
        
        options_layout.addWidget(QLabel("Filtreler:"))
        options_layout.addWidget(self.show_empty_categories)
        options_layout.addWidget(QLabel("Minimum hesap sayısı:"))
        options_layout.addWidget(self.min_count_combo)
        options_layout.addStretch()
        
        options_frame.setLayout(options_layout)
        layout.addWidget(options_frame)
        
        # Detaylı tablo
        self.detailed_table = QTableWidget()
        self.detailed_table.setColumnCount(6)
        self.detailed_table.setHorizontalHeaderLabels([
            "Ana Kategori", "Alt Kategori", "Hesap Sayısı", 
            "Giriş Yapılan", "Hedef", "Toplam %"
        ])
        layout.addWidget(self.detailed_table)
        
        widget.setLayout(layout)
        return widget
        
    def create_charts_tab(self):
        """Grafikler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Grafik türü seçimi
        chart_controls = QHBoxLayout()
        chart_controls.addWidget(QLabel("Grafik Türü:"))
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Pasta Grafik", "Bar Grafik", "Yatay Bar Grafik"])
        self.chart_type_combo.currentTextChanged.connect(self.update_chart)
        chart_controls.addWidget(self.chart_type_combo)
        
        self.chart_data_combo = QComboBox()
        self.chart_data_combo.addItems(["Ana Kategoriler", "Tüm Kategoriler", "En Popüler 10"])
        self.chart_data_combo.currentTextChanged.connect(self.update_chart)
        chart_controls.addWidget(self.chart_data_combo)
        
        chart_controls.addStretch()
        layout.addLayout(chart_controls)
        
        # Grafik alanı
        self.chart_frame = QFrame()
        self.chart_frame.setMinimumHeight(500)
        self.chart_frame.setStyleSheet("border: 1px solid #ddd; background: white;")
        layout.addWidget(self.chart_frame)
        
        widget.setLayout(layout)
        return widget
        
    def create_stat_card(self, icon, title, value_label):
        """İstatistik kartı oluştur"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 20px;
                margin: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 600; color: #64748b;")
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        value_label.setStyleSheet("font-size: 28px; font-weight: 700; color: #1e293b; margin-top: 10px;")
        
        layout.addLayout(header_layout)
        layout.addWidget(value_label)
        layout.setContentsMargins(15, 15, 15, 15)
        
        card.setLayout(layout)
        return card
        
    def load_statistics(self):
        """İstatistikleri yükle"""
        try:
            # Genel istatistikler
            categories = mysql_manager.get_categories('icerik')
            login_accounts = user_manager.get_all_users()
            target_accounts = mysql_manager.get_all_targets()
            
            total_categories = len(set(cat.get('ana_kategori', '') for cat in categories))
            total_login_accounts = len(login_accounts)
            total_target_accounts = len(target_accounts)
            total_accounts = total_login_accounts + total_target_accounts
            
            # Kategorili hesap sayısı
            categorized_login = len([acc for acc in login_accounts 
                                   if mysql_manager.get_account_categories(acc['kullanici_adi'], 'giris_yapilan')])
            categorized_target = len([acc for acc in target_accounts 
                                    if mysql_manager.get_account_categories(acc['kullanici_adi'], 'hedef')])
            categorized_total = categorized_login + categorized_target
            uncategorized_total = total_accounts - categorized_total
            
            # Özet güncellemesi
            self.total_categories_label.setText(str(total_categories))
            self.total_accounts_label.setText(str(total_accounts))
            self.categorized_accounts_label.setText(str(categorized_total))
            self.uncategorized_accounts_label.setText(str(uncategorized_total))
            
            self.update_general_table()
            self.update_distribution()
            self.update_detailed_analysis()
            self.update_chart()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"İstatistikler yüklenirken hata: {str(e)}")
            
    def update_general_table(self):
        """Genel istatistik tablosunu güncelle"""
        try:
            categories = mysql_manager.get_categories('icerik')
            
            # Ana kategorileri grupla
            main_categories = defaultdict(lambda: {'sub_count': 0, 'account_count': 0})
            
            for cat in categories:
                ana_kategori = cat.get('ana_kategori', '')
                if ana_kategori:
                    if cat.get('alt_kategori'):
                        main_categories[ana_kategori]['sub_count'] += 1
                    
                    # Hesap sayısını hesapla
                    login_count = len([acc for acc in user_manager.get_all_users() 
                                     if any(c.get('ana_kategori') == ana_kategori 
                                           for c in mysql_manager.get_account_categories(acc['kullanici_adi'], 'giris_yapilan'))])
                    target_count = len([acc for acc in mysql_manager.get_all_targets() 
                                      if any(c.get('ana_kategori') == ana_kategori 
                                            for c in mysql_manager.get_account_categories(acc['kullanici_adi'], 'hedef'))])
                    main_categories[ana_kategori]['account_count'] = login_count + target_count
            
            # Tabloyu doldur
            self.general_table.setRowCount(len(main_categories))
            total_accounts = len(user_manager.get_all_users()) + len(mysql_manager.get_all_targets())
            
            for row, (ana_kategori, data) in enumerate(main_categories.items()):
                self.general_table.setItem(row, 0, QTableWidgetItem(ana_kategori))
                self.general_table.setItem(row, 1, QTableWidgetItem(str(data['sub_count'])))
                self.general_table.setItem(row, 2, QTableWidgetItem(str(data['account_count'])))
                
                percentage = (data['account_count'] / total_accounts * 100) if total_accounts > 0 else 0
                self.general_table.setItem(row, 3, QTableWidgetItem(f"{percentage:.1f}%"))
                
        except Exception as e:
            print(f"Genel tablo güncelleme hatası: {e}")
            
    def update_distribution(self):
        """Dağılım tablosunu güncelle"""
        try:
            account_type = self.account_type_combo.currentText()
            
            # Hesap türüne göre veri topla
            if account_type == "Giriş Yapılan Hesaplar":
                accounts = [(acc['kullanici_adi'], 'giris_yapilan') for acc in user_manager.get_all_users()]
            elif account_type == "Hedef Hesaplar":
                accounts = [(acc['kullanici_adi'], 'hedef') for acc in mysql_manager.get_all_targets()]
            else:  # Tümü
                accounts = ([(acc['kullanici_adi'], 'giris_yapilan') for acc in user_manager.get_all_users()] +
                          [(acc['kullanici_adi'], 'hedef') for acc in mysql_manager.get_all_targets()])
            
            # Kategori sayımı
            category_counts = Counter()
            
            for username, acc_type in accounts:
                categories = mysql_manager.get_account_categories(username, acc_type)
                for cat in categories:
                    ana_kategori = cat.get('ana_kategori', '')
                    alt_kategori = cat.get('alt_kategori', '')
                    
                    if alt_kategori:
                        category_counts[f"{ana_kategori} → {alt_kategori}"] += 1
                    else:
                        category_counts[ana_kategori] += 1
            
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
                ana_kategori = cat.get('ana_kategori', '')
                alt_kategori = cat.get('alt_kategori', '')
                
                # Hesap sayılarını hesapla
                login_count = len([acc for acc in user_manager.get_all_users() 
                                 if any((c.get('ana_kategori') == ana_kategori and 
                                        (not alt_kategori or c.get('alt_kategori') == alt_kategori))
                                       for c in mysql_manager.get_account_categories(acc['kullanici_adi'], 'giris_yapilan'))])
                
                target_count = len([acc for acc in mysql_manager.get_all_targets() 
                                  if any((c.get('ana_kategori') == ana_kategori and 
                                         (not alt_kategori or c.get('alt_kategori') == alt_kategori))
                                        for c in mysql_manager.get_account_categories(acc['kullanici_adi'], 'hedef'))])
                
                total_count = login_count + target_count
                
                # Filtreleme
                if not show_empty and total_count == 0:
                    continue
                if total_count < min_count:
                    continue
                
                detailed_data.append({
                    'ana_kategori': ana_kategori,
                    'alt_kategori': alt_kategori or '-',
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
                self.show_empty_chart("Grafik modülü bulunamadı. Matplotlib yüklü değil.")
                return
                
            chart_type = self.chart_type_combo.currentText()
            data_type = self.chart_data_combo.currentText()
            
            # Veri toplama
            categories = mysql_manager.get_categories('icerik')
            category_counts = Counter()
            
            all_accounts = ([(acc['kullanici_adi'], 'giris_yapilan') for acc in user_manager.get_all_users()] +
                          [(acc['kullanici_adi'], 'hedef') for acc in mysql_manager.get_all_targets()])
            
            for username, acc_type in all_accounts:
                account_categories = mysql_manager.get_account_categories(username, acc_type)
                for cat in account_categories:
                    ana_kategori = cat.get('ana_kategori', '')
                    alt_kategori = cat.get('alt_kategori', '')
                    
                    if data_type == "Ana Kategoriler":
                        if ana_kategori:
                            category_counts[ana_kategori] += 1
                    else:  # Tüm kategoriler veya En popüler 10
                        if alt_kategori:
                            category_counts[f"{ana_kategori} → {alt_kategori}"] += 1
                        elif ana_kategori:
                            category_counts[ana_kategori] += 1
            
            # En popüler 10 için filtreleme
            if data_type == "En Popüler 10":
                category_counts = dict(category_counts.most_common(10))
            
            if not category_counts:
                self.show_empty_chart("Gösterilecek veri bulunamadı")
                return
            
            # Grafik oluşturma
            self.create_chart(chart_type, category_counts)
            
        except Exception as e:
            print(f"Grafik güncelleme hatası: {e}")
            self.show_empty_chart(f"Grafik oluşturulamadı: {str(e)}")
            
    def create_chart(self, chart_type, data):
        """Grafik oluştur"""
        if not MATPLOTLIB_AVAILABLE:
            self.show_empty_chart("Grafik oluşturulamadı: Matplotlib kütüphanesi bulunamadı")
            return
            
        try:
            # Matplotlib kullanarak grafik oluştur
            plt.ioff()  # Interactive mode kapalı
            fig, ax = plt.subplots(figsize=(10, 6))
            
            labels = list(data.keys())
            values = list(data.values())
            
            # Güvenli renk paleti
            colors = plt.cm.tab10(range(len(labels) % 10))
            
            if chart_type == "Pasta Grafik":
                wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                                                 colors=colors, startangle=90)
                ax.set_title("Kategori Dağılımı", fontsize=14, fontweight='bold')
                
            elif chart_type == "Bar Grafik":
                bars = ax.bar(range(len(labels)), values, color=colors)
                ax.set_xlabel("Kategoriler", fontsize=12)
                ax.set_ylabel("Hesap Sayısı", fontsize=12)
                ax.set_title("Kategori Kullanım İstatistikleri", fontsize=14, fontweight='bold')
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
                
                # Bar'ların üzerine değer yazma
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{int(height)}', ha='center', va='bottom', fontsize=9)
                           
            elif chart_type == "Yatay Bar Grafik":
                bars = ax.barh(range(len(labels)), values, color=colors)
                ax.set_ylabel("Kategoriler", fontsize=12)
                ax.set_xlabel("Hesap Sayısı", fontsize=12)
                ax.set_title("Kategori Kullanım İstatistikleri", fontsize=14, fontweight='bold')
                ax.set_yticks(range(len(labels)))
                ax.set_yticklabels(labels, fontsize=10)
                
                # Bar'ların sonuna değer yazma
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    if width > 0:
                        ax.text(width, bar.get_y() + bar.get_height()/2.,
                               f'{int(width)}', ha='left', va='center', fontsize=9)
            
            plt.tight_layout()
            
            # Grafik PNG olarak kaydet ve göster
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            
            pixmap = QPixmap()
            success = pixmap.loadFromData(buffer.getvalue())
            
            if success:
                # Chart frame'e grafik ekle
                self.show_chart_image(pixmap)
            else:
                self.show_empty_chart("Grafik gösterilemedi")
            
            # Bellek temizliği
            plt.close(fig)
            plt.clf()
            buffer.close()
            
        except Exception as e:
            print(f"Grafik oluşturma hatası: {e}")
            self.show_empty_chart(f"Grafik oluşturulamadı: {str(e)}")
            
    def show_chart_image(self, pixmap):
        """Grafik resmini göster"""
        # Önceki widget'ları temizle
        for child in self.chart_frame.findChildren(QLabel):
            child.deleteLater()
        
        label = QLabel()
        label.setPixmap(pixmap.scaled(self.chart_frame.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        label.setAlignment(Qt.AlignCenter)
        
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.chart_frame.setLayout(layout)
        
    def show_empty_chart(self, message):
        """Boş grafik mesajı göster"""
        for child in self.chart_frame.findChildren(QLabel):
            child.deleteLater()
        
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #64748b; font-size: 16px;")
        
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.chart_frame.setLayout(layout)
        
    def export_statistics(self):
        """İstatistikleri dışa aktar"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import json
            from datetime import datetime
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "İstatistikleri Kaydet", 
                f"kategori_istatistikleri_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Dosyaları (*.json);;Metin Dosyaları (*.txt)"
            )
            
            if file_path:
                stats_data = {
                    'export_date': datetime.now().isoformat(),
                    'total_categories': self.total_categories_label.text(),
                    'total_accounts': self.total_accounts_label.text(),
                    'categorized_accounts': self.categorized_accounts_label.text(),
                    'uncategorized_accounts': self.uncategorized_accounts_label.text(),
                    'detailed_data': self.get_detailed_export_data()
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(stats_data, f, ensure_ascii=False, indent=2)
                    
                QMessageBox.information(self, "Başarılı", f"İstatistikler başarıyla kaydedildi:\n{file_path}")
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"İstatistikler kaydedilirken hata: {str(e)}")
            
    def get_detailed_export_data(self):
        """Detaylı dışa aktarma verisi hazırla"""
        try:
            categories = mysql_manager.get_categories('icerik')
            all_accounts = ([(acc['kullanici_adi'], 'giris_yapilan') for acc in user_manager.get_all_users()] +
                          [(acc['kullanici_adi'], 'hedef') for acc in mysql_manager.get_all_targets()])
            
            detailed_data = []
            
            for cat in categories:
                ana_kategori = cat.get('ana_kategori', '')
                alt_kategori = cat.get('alt_kategori', '')
                
                login_accounts = []
                target_accounts = []
                
                for username, acc_type in all_accounts:
                    account_categories = mysql_manager.get_account_categories(username, acc_type)
                    for acc_cat in account_categories:
                        if (acc_cat.get('ana_kategori') == ana_kategori and 
                            (not alt_kategori or acc_cat.get('alt_kategori') == alt_kategori)):
                            if acc_type == 'giris_yapilan':
                                login_accounts.append(username)
                            else:
                                target_accounts.append(username)
                
                if login_accounts or target_accounts:
                    detailed_data.append({
                        'ana_kategori': ana_kategori,
                        'alt_kategori': alt_kategori,
                        'login_accounts': login_accounts,
                        'target_accounts': target_accounts,
                        'login_count': len(login_accounts),
                        'target_count': len(target_accounts),
                        'total_count': len(login_accounts) + len(target_accounts)
                    })
            
            return detailed_data
            
        except Exception as e:
            print(f"Detaylı veri hazırlama hatası: {e}")
            return []
    
    def closeEvent(self, event):
        """Dialog kapandığında bellek temizliği"""
        try:
            if MATPLOTLIB_AVAILABLE:
                plt.close('all')  # Tüm matplotlib figureleri kapat
                plt.clf()         # Cache temizle
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
