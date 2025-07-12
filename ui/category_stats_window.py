
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGroupBox, QScrollArea, QTabWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from database.mysql import mysql_manager
from database.user_manager import user_manager
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class CategoryStatsWindow(QWidget):
    def __init__(self, colors, return_callback):
        super().__init__()
        self.colors = colors
        self.return_callback = return_callback
        self.init_ui()
        self.setup_style()

    def init_ui(self):
        """UI'yi başlat"""
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Geri")
        back_btn.clicked.connect(self.return_callback)
        
        title_label = QLabel("📊 Kategori İstatistikleri")
        title_label.setObjectName("pageTitle")
        
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)

        # Tab widget
        self.tabs = QTabWidget()
        
        # Genel istatistikler
        general_tab = self.create_general_stats_tab()
        self.tabs.addTab(general_tab, "📈 Genel İstatistikler")
        
        # Kategori dağılımları
        distribution_tab = self.create_distribution_tab()
        self.tabs.addTab(distribution_tab, "📊 Kategori Dağılımları")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        self.load_stats()

    def create_general_stats_tab(self):
        """Genel istatistikler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # İstatistik kartları
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_layout = QHBoxLayout()
        
        self.total_users_card = self.create_stat_card("👥 Toplam Kullanıcı", "0")
        self.categorized_users_card = self.create_stat_card("🏷️ Kategorili Kullanıcı", "0")
        self.total_categories_card = self.create_stat_card("📂 Toplam Kategori", "0")
        
        stats_layout.addWidget(self.total_users_card)
        stats_layout.addWidget(self.categorized_users_card)
        stats_layout.addWidget(self.total_categories_card)
        
        stats_frame.setLayout(stats_layout)
        layout.addWidget(stats_frame)
        
        # Detaylı bilgiler
        details_scroll = QScrollArea()
        details_widget = QWidget()
        self.details_layout = QVBoxLayout()
        
        details_widget.setLayout(self.details_layout)
        details_scroll.setWidget(details_widget)
        details_scroll.setWidgetResizable(True)
        
        layout.addWidget(details_scroll)
        widget.setLayout(layout)
        return widget

    def create_distribution_tab(self):
        """Kategori dağılımları sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Grafik alanı
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        widget.setLayout(layout)
        return widget

    def create_stat_card(self, title, value):
        """İstatistik kartı oluştur"""
        card = QFrame()
        card.setObjectName("statCard")
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        card.setLayout(layout)
        
        return card

    def load_stats(self):
        """İstatistikleri yükle"""
        try:
            # Genel istatistikler
            users = user_manager.get_all_users()
            targets = mysql_manager.get_all_targets()
            categories = mysql_manager.get_categories()
            
            total_users = len(users) + len(targets)
            total_categories = len(set([(cat['kategori_turu'], cat['ana_kategori']) for cat in categories]))
            
            # Kategorili kullanıcı sayısı
            categorized_count = 0
            for user in users:
                user_cats = mysql_manager.get_account_categories(user['kullanici_adi'], 'giris_yapilan')
                if user_cats:
                    categorized_count += 1
            
            for target in targets:
                target_cats = mysql_manager.get_account_categories(target['kullanici_adi'], 'hedef')
                if target_cats:
                    categorized_count += 1
            
            # Kartları güncelle
            self.total_users_card.findChild(QLabel, "statValue").setText(str(total_users))
            self.categorized_users_card.findChild(QLabel, "statValue").setText(str(categorized_count))
            self.total_categories_card.findChild(QLabel, "statValue").setText(str(total_categories))
            
            # Detaylı bilgileri yükle
            self.load_detailed_stats()
            
            # Grafikleri oluştur
            self.create_charts()
            
        except Exception as e:
            print(f"İstatistik yükleme hatası: {e}")

    def load_detailed_stats(self):
        """Detaylı istatistikleri yükle"""
        # Kategori türlerine göre dağılım
        categories = mysql_manager.get_categories()
        
        profil_count = len([cat for cat in categories if cat['kategori_turu'] == 'profil'])
        icerik_count = len([cat for cat in categories if cat['kategori_turu'] == 'icerik'])
        
        profil_frame = QGroupBox("👤 Profil Kategorileri")
        profil_layout = QVBoxLayout()
        profil_layout.addWidget(QLabel(f"Toplam: {profil_count} kategori"))
        profil_frame.setLayout(profil_layout)
        
        icerik_frame = QGroupBox("📝 İçerik Kategorileri")
        icerik_layout = QVBoxLayout()
        icerik_layout.addWidget(QLabel(f"Toplam: {icerik_count} kategori"))
        icerik_frame.setLayout(icerik_layout)
        
        self.details_layout.addWidget(profil_frame)
        self.details_layout.addWidget(icerik_frame)

    def create_charts(self):
        """Grafikleri oluştur"""
        try:
            self.figure.clear()
            
            # Kategori türleri pasta grafiği
            ax1 = self.figure.add_subplot(221)
            categories = mysql_manager.get_categories()
            
            profil_count = len([cat for cat in categories if cat['kategori_turu'] == 'profil'])
            icerik_count = len([cat for cat in categories if cat['kategori_turu'] == 'icerik'])
            
            ax1.pie([profil_count, icerik_count], labels=['Profil', 'İçerik'], autopct='%1.1f%%')
            ax1.set_title('Kategori Türleri Dağılımı')
            
            # En popüler kategoriler
            ax2 = self.figure.add_subplot(222)
            category_usage = {}
            
            all_users = user_manager.get_all_users()
            for user in all_users:
                user_cats = mysql_manager.get_account_categories(user['kullanici_adi'], 'giris_yapilan')
                for cat in user_cats:
                    ana_kat = cat['ana_kategori']
                    category_usage[ana_kat] = category_usage.get(ana_kat, 0) + 1
            
            if category_usage:
                sorted_cats = sorted(category_usage.items(), key=lambda x: x[1], reverse=True)[:5]
                categories_names = [cat[0] for cat in sorted_cats]
                usage_counts = [cat[1] for cat in sorted_cats]
                
                ax2.bar(categories_names, usage_counts)
                ax2.set_title('En Popüler Kategoriler')
                ax2.tick_params(axis='x', rotation=45)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"Grafik oluşturma hatası: {e}")

    def setup_style(self):
        """Stil ayarları"""
        style = f"""
        #pageTitle {{
            font-size: 24px;
            font-weight: bold;
            color: {self.colors['text_primary']};
        }}
        
        #statsFrame {{
            background: {self.colors['background_alt']};
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
        }}
        
        #statCard {{
            background: white;
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            padding: 20px;
            margin: 10px;
            text-align: center;
        }}
        
        #statTitle {{
            font-size: 14px;
            color: {self.colors['text_secondary']};
            font-weight: 600;
        }}
        
        #statValue {{
            font-size: 32px;
            font-weight: bold;
            color: {self.colors['primary']};
        }}
        """
        self.setStyleSheet(style)
