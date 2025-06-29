from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QMessageBox, QStackedWidget)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QPalette, QColor
from .login_window import LoginWindow
from .validation_window import ValidationWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.colors = {
            'primary': '#ED8B00',      # Sarı
            'secondary': '#0072CE',     # Mavi
            'primary_hover': '#C57A00', # Sarı hover
            'secondary_hover': '#005BB5', # Mavi hover
            'text_primary': '#231F20',  # Koyu gri
            'text_secondary': '#666666', # Açık gri
            'background': '#FFFFFF',    # Beyaz
            'background_alt': '#F5F5F5', # Açık gri
            'success': '#388E3C',       # Yeşil
            'error': '#D32F2F',         # Kırmızı
            'card_bg': '#FAFAFA',       # Kart arka planı
            'border': '#E5E5E7'         # Kenarlık
        }
        
        self.init_ui()
        self.setup_style()
        
    def init_ui(self):
        """UI'yi başlat"""
        self.setWindowTitle("AkTweetor - Twitter Otomasyon Aracı")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(800, 600)
        
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Stacked widget - sayfa geçişleri için
        self.stacked_widget = QStackedWidget()
        
        # Ana menü sayfası
        self.main_page = self.create_main_page()
        self.stacked_widget.addWidget(self.main_page)
        
        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(main_layout)
        
    def create_main_page(self):
        """Ana menü sayfasını oluştur"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Başlık bölümü
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout()
        
        # Ana başlık
        title_label = QLabel("AkTweetor")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Alt başlık
        subtitle_label = QLabel("Twitter Otomasyon Aracı")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        header_layout.setSpacing(10)
        header_frame.setLayout(header_layout)
        
        # Menü butonları bölümü
        menu_frame = QFrame()
        menu_frame.setObjectName("menuFrame")
        menu_layout = QVBoxLayout()
        menu_layout.setSpacing(15)
        menu_layout.setContentsMargins(50, 30, 50, 30)
        
        # Menü butonları
        menu_buttons = [
            ("📥 Giriş Yapıcı", self.open_login_menu),
            ("🔍 Giriş Doğrulama/Silme", self.open_validation_menu),
            ("🍪 Çerez Kasıcı/Çerez Çıkarıcı", self.coming_soon),
            ("📋 RT'lenecek Hesapları Ekle", self.coming_soon),
            ("📅 Yıl Ayırıcı", self.coming_soon),
            ("📂 Hesapları Kategorilere Ayır", self.coming_soon),
            ("💰 Hesap Doldurucu", self.coming_soon),
            ("❤️ Beğeni/Retweet/Yorum/Hesap İşlemleri", self.coming_soon),
            ("⚙️ Ayarlar", self.coming_soon)
        ]
        
        self.menu_buttons = []
        for text, callback in menu_buttons:
            btn = QPushButton(text)
            btn.setObjectName("menuButton")
            btn.clicked.connect(callback)
            btn.setCursor(Qt.PointingHandCursor)
            menu_layout.addWidget(btn)
            self.menu_buttons.append(btn)
        
        menu_frame.setLayout(menu_layout)
        
        # Ana layout'a ekle
        layout.addWidget(header_frame)
        layout.addWidget(menu_frame, 1)  # Stretch factor
        layout.setContentsMargins(0, 0, 0, 0)
        
        page.setLayout(layout)
        return page
    
    def setup_style(self):
        """Stil ayarlarını uygula"""
        style = f"""
        QMainWindow {{
            background-color: {self.colors['background']};
        }}
        
        #headerFrame {{
            background-color: {self.colors['background']};
            padding: 40px 0px;
        }}
        
        #titleLabel {{
            font-size: 42px;
            font-weight: 700;
            color: {self.colors['text_primary']};
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
            margin-bottom: 10px;
        }}
        
        #subtitleLabel {{
            font-size: 18px;
            font-weight: 400;
            color: {self.colors['text_secondary']};
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
        }}
        
        #menuFrame {{
            background-color: {self.colors['background']};
        }}
        
        #menuButton {{
            background-color: {self.colors['primary']};
            color: white;
            border: none;
            border-radius: 12px;
            padding: 18px 24px;
            font-size: 16px;
            font-weight: 600;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
            text-align: left;
            min-height: 20px;
        }}
        
        #menuButton:hover {{
            background-color: {self.colors['primary_hover']};
            transform: translateY(-2px);
        }}
        
        #menuButton:pressed {{
            background-color: {self.colors['primary_hover']};
            transform: translateY(0px);
        }}
        
        #backButton {{
            background-color: {self.colors['text_secondary']};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 600;
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
        }}
        
        #backButton:hover {{
            background-color: #555555;
        }}
        """
        
        self.setStyleSheet(style)
    
    def open_login_menu(self):
        """Giriş Yapıcı menüsünü aç"""
        try:
            login_window = LoginWindow(self.colors, self.return_to_main)
            self.stacked_widget.addWidget(login_window)
            self.stacked_widget.setCurrentWidget(login_window)
        except Exception as e:
            self.show_error(f"Giriş Yapıcı açılırken hata: {str(e)}")
    
    def open_validation_menu(self):
        """Giriş Doğrulama/Silme menüsünü aç"""
        try:
            validation_window = ValidationWindow(self.colors, self.return_to_main)
            self.stacked_widget.addWidget(validation_window)
            self.stacked_widget.setCurrentWidget(validation_window)
        except Exception as e:
            self.show_error(f"Giriş Doğrulama açılırken hata: {str(e)}")
    
    def return_to_main(self):
        """Ana menüye dön"""
        # Mevcut widget'ı kaldır (ana menü hariç)
        current_widget = self.stacked_widget.currentWidget()
        if current_widget != self.main_page:
            self.stacked_widget.removeWidget(current_widget)
            current_widget.deleteLater()
        
        # Ana menüye dön
        self.stacked_widget.setCurrentWidget(self.main_page)
    
    def coming_soon(self):
        """Yakında gelecek özellikler için mesaj"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Bilgi")
        msg.setText("Bu özellik yakında eklenecek!")
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {self.colors['background']};
                color: {self.colors['text_primary']};
            }}
            QMessageBox QPushButton {{
                background-color: {self.colors['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {self.colors['primary_hover']};
            }}
        """)
        msg.exec_()
    
    def show_error(self, message):
        """Hata mesajı göster"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Hata")
        msg.setText(message)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {self.colors['background']};
                color: {self.colors['text_primary']};
            }}
            QMessageBox QPushButton {{
                background-color: {self.colors['error']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QMessageBox QPushButton:hover {{
                background-color: #B71C1C;
            }}
        """)
        msg.exec_()
