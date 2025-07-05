
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QMessageBox, QStackedWidget,
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QLinearGradient, QPainter, QPainterPath
from .login_window import LoginWindow
from .validation_window import ValidationWindow
from .cookie_window import CookieWindow
from .target_window import TargetWindow

class GradientFrame(QFrame):
    """Gradient arka plan efekti için özel frame"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Gradient oluştur
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#FAFBFC"))
        gradient.setColorAt(1, QColor("#F0F2F5"))
        
        painter.fillRect(self.rect(), gradient)

class AnimatedButton(QPushButton):
    """Animasyonlu buton sınıfı"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        self.shadow.setOffset(0, 3)
        self.setGraphicsEffect(self.shadow)
        
        # Animasyon timer'ı
        self.hover_timer = QTimer()
        self.hover_timer.timeout.connect(self.update_shadow)
        self.hover_timer.start(16)  # 60 FPS
        
        self.target_blur = 15
        self.target_offset = 3
        
    def enterEvent(self, event):
        super().enterEvent(event)
        self.target_blur = 25
        self.target_offset = 6
        
    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.target_blur = 15
        self.target_offset = 3
        
    def update_shadow(self):
        current_blur = self.shadow.blurRadius()
        current_offset = self.shadow.yOffset()
        
        # Smooth interpolation
        new_blur = current_blur + (self.target_blur - current_blur) * 0.15
        new_offset = current_offset + (self.target_offset - current_offset) * 0.15
        
        self.shadow.setBlurRadius(new_blur)
        self.shadow.setOffset(0, new_offset)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.colors = {
            'primary': '#FF6B35',       # Turuncu-kırmızı gradient başlangıç
            'primary_end': '#F7931E',   # Turuncu gradient bitiş
            'primary_hover': '#E85A2B', # Primary hover rengi
            'secondary': '#4A90E2',     # Mavi
            'secondary_hover': '#3A7BC8', # Secondary hover rengi
            'accent': '#7B68EE',        # Mor-mavi
            'accent_hover': '#6B58DE',  # Accent hover rengi
            'success': '#27AE60',       # Yeşil
            'success_hover': '#219A52', # Success hover rengi
            'warning': '#F39C12',       # Turuncu
            'warning_hover': '#E67E22', # Warning hover rengi
            'error': '#E74C3C',         # Kırmızı
            'error_hover': '#C0392B',   # Error hover rengi
            'text_primary': '#2C3E50',  # Koyu lacivert
            'text_secondary': '#5D6D7E', # Orta gri
            'text_light': '#85929E',    # Açık gri
            'background': '#FFFFFF',    # Beyaz
            'background_alt': '#F8F9FA', # Çok açık gri
            'card_bg': '#FFFFFF',       # Kart arka planı
            'border': '#E8EAED',        # Açık kenarlık
            'border_hover': '#CBD5E0',  # Hover kenarlık
            'shadow': 'rgba(0, 0, 0, 0.08)', # Gölge
            'shadow_hover': 'rgba(0, 0, 0, 0.15)', # Hover gölge
            'gradient_start': '#667eea', # Gradient başlangıç
            'gradient_end': '#764ba2'    # Gradient bitiş
        }
        
        self.init_ui()
        self.setup_style()
        
    def init_ui(self):
        """UI'yi başlat"""
        self.setWindowTitle("AkTweetor - Twitter Otomasyon Aracı")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
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
        
        # Ana container
        main_container = GradientFrame()
        main_container.setObjectName("mainContainer")
        container_layout = QVBoxLayout()
        
        # Başlık bölümü
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout()
        
        # Logo/İkon alanı
        logo_frame = QFrame()
        logo_frame.setObjectName("logoFrame")
        logo_layout = QVBoxLayout()
        
        # Logo resmi
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedSize(100, 100)
        
        # Logo dosyasını yükle
        import os
        if os.path.exists("assets/logo.png"):
            from PyQt5.QtGui import QPixmap
            pixmap = QPixmap("assets/logo.png")
            scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            # Logo yoksa emoji kullan
            logo_label.setText("🐦")
            logo_label.setStyleSheet("font-size: 60px; color: white;")
        
        logo_layout.addWidget(logo_label)
        logo_layout.setContentsMargins(0, 20, 0, 20)
        logo_frame.setLayout(logo_layout)
        logo_frame.setFixedHeight(120)
        
        # Ana başlık
        title_label = QLabel("🐦 AkTweetor")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Alt başlık
        subtitle_label = QLabel("Profesyonel Twitter Otomasyon Platformu")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        # Versiyon bilgisi
        version_label = QLabel("v1.0.0 Pro Edition")
        version_label.setObjectName("versionLabel")
        version_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(logo_frame)
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        header_layout.addWidget(version_label)
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 40, 0, 40)
        header_frame.setLayout(header_layout)
        
        # Menü butonları bölümü - Grid Layout
        menu_frame = QFrame()
        menu_frame.setObjectName("menuFrame")
        menu_layout = QVBoxLayout()
        
        # İlk satır butonları
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(20)
        
        # İkinci satır butonları
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(20)
        
        # Üçüncü satır butonları
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(20)
        
        # Menü butonları
        menu_buttons_data = [
            # Satır 1 - Ana işlemler
            [
                ("🔐", "Giriş Yapıcı", "Hesap giriş işlemlerini yönetin", self.open_login_menu, "primary"),
                ("🔍", "Giriş Doğrulama", "Hesap durumlarını kontrol edin", self.open_validation_menu, "secondary"),
                ("🍪", "Çerez Yöneticisi", "Çerez toplama ve yönetimi", self.open_cookie_menu, "accent"),
            ],
            # Satır 2 - Gelişmiş özellikler
            [
                ("📋", "Hedef Hesaplar", "RT'lenecek hesapları yönetin", self.open_target_menu, "success"),
                ("📂", "Kategori Yöneticisi", "Hesapları kategorilere ayırın", self.coming_soon, "secondary"),
                ("📅", "Tarih Ayırıcı", "Hesapları tarihlere göre ayırın", self.coming_soon, "warning"),
            ],
            # Satır 3 - Otomasyon ve ayarlar
            [
                ("💰", "Hesap Doldurucu", "Hesap bilgilerini tamamlayın", self.coming_soon, "primary"),
                ("❤️", "Etkileşim Merkezi", "Beğeni, RT ve yorum işlemleri", self.coming_soon, "accent"),
                ("⚙️", "Sistem Ayarları", "Uygulama yapılandırması", self.coming_soon, "text_secondary"),
            ]
        ]
        
        self.menu_buttons = []
        
        # Butonları oluştur ve yerleştir
        for row_idx, row_data in enumerate(menu_buttons_data):
            current_layout = [row1_layout, row2_layout, row3_layout][row_idx]
            
            for icon, title, description, callback, color_key in row_data:
                btn_container = self.create_menu_button(icon, title, description, callback, color_key)
                current_layout.addWidget(btn_container)
                self.menu_buttons.append(btn_container)
            
            # Layout'a boşluk ekle
            current_layout.addStretch()
        
        # Alt bilgi paneli
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_layout = QHBoxLayout()
        
        # Durum bilgileri
        status_label = QLabel("🟢 Sistem Hazır")
        status_label.setObjectName("statusLabel")
        
        # Kullanıcı sayısı
        user_count_label = QLabel("👥 0 Aktif Kullanıcı")
        user_count_label.setObjectName("userCountLabel")
        
        # Versiyon ve telif hakkı
        copyright_label = QLabel("© 2024 AkTweetor - Tüm hakları saklıdır")
        copyright_label.setObjectName("copyrightLabel")
        
        info_layout.addWidget(status_label)
        info_layout.addStretch()
        info_layout.addWidget(user_count_label)
        info_layout.addStretch()
        info_layout.addWidget(copyright_label)
        info_frame.setLayout(info_layout)
        
        # Ana layout'a ekle
        menu_layout.addLayout(row1_layout)
        menu_layout.addSpacing(25)
        menu_layout.addLayout(row2_layout)
        menu_layout.addSpacing(25)
        menu_layout.addLayout(row3_layout)
        menu_layout.setContentsMargins(60, 30, 60, 30)
        menu_frame.setLayout(menu_layout)
        
        # Container layout'a ekle
        container_layout.addWidget(header_frame)
        container_layout.addWidget(menu_frame, 1)
        container_layout.addWidget(info_frame)
        container_layout.setContentsMargins(0, 0, 0, 0)
        main_container.setLayout(container_layout)
        
        # Ana layout'a ekle
        layout.addWidget(main_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        page.setLayout(layout)
        return page
    
    def create_menu_button(self, icon, title, description, callback, color_key):
        """Modern menü butonu oluştur"""
        container = QFrame()
        container.setObjectName("menuButtonContainer")
        container.setFixedSize(380, 140)
        container.setCursor(Qt.PointingHandCursor)
        
        # Gölge efekti
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout()
        
        # Üst kısım - İkon ve başlık
        top_layout = QHBoxLayout()
        
        # İkon
        icon_label = QLabel(icon)
        icon_label.setObjectName("menuButtonIcon")
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        
        # Başlık ve açıklama
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setObjectName("menuButtonTitle")
        
        desc_label = QLabel(description)
        desc_label.setObjectName("menuButtonDesc")
        desc_label.setWordWrap(True)
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)
        text_layout.addStretch()
        
        top_layout.addWidget(icon_label)
        top_layout.addSpacing(15)
        top_layout.addLayout(text_layout, 1)
        
        # Alt kısım - Durum göstergesi
        status_layout = QHBoxLayout()
        status_dot = QLabel("●")
        status_dot.setObjectName(f"statusDot_{color_key}")
        status_text = QLabel("Hazır")
        status_text.setObjectName("statusText")
        
        status_layout.addWidget(status_dot)
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        
        layout.addLayout(top_layout)
        layout.addLayout(status_layout)
        layout.setContentsMargins(20, 15, 20, 15)
        container.setLayout(layout)
        
        # Click event
        def mouse_press_event(event):
            if event.button() == Qt.LeftButton:
                callback()
        
        container.mousePressEvent = mouse_press_event
        
        return container
    
    def setup_style(self):
        """Gelişmiş stil ayarlarını uygula"""
        style = f"""
        QMainWindow {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['background']}, 
                stop:1 {self.colors['background_alt']});
        }}
        
        #mainContainer {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FAFBFC, 
                stop:1 #F0F2F5);
            border-radius: 0px;
        }}
        
        #headerFrame {{
            background: transparent;
            border: none;
        }}
        
        #logoFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self.colors['gradient_start']}, 
                stop:1 {self.colors['gradient_end']});
            border-radius: 60px;
            margin: 0px 450px;
        }}
        
        #titleLabel {{
            font-size: 48px;
            font-weight: 800;
            color: {self.colors['text_primary']};
            font-family: 'SF Pro Display', 'Segoe UI', 'Roboto', sans-serif;
            margin: 0px;
            text-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        #subtitleLabel {{
            font-size: 18px;
            font-weight: 400;
            color: {self.colors['text_secondary']};
            font-family: 'SF Pro Display', 'Segoe UI', 'Roboto', sans-serif;
            margin: 8px 0px;
        }}
        
        #versionLabel {{
            font-size: 14px;
            font-weight: 500;
            color: {self.colors['text_light']};
            font-family: 'SF Pro Display', 'Segoe UI', 'Roboto', sans-serif;
            background: {self.colors['background_alt']};
            padding: 6px 16px;
            border-radius: 20px;
            margin: 0px 450px;
        }}
        
        #menuFrame {{
            background: transparent;
            border: none;
        }}
        
        #menuButtonContainer {{
            background: {self.colors['card_bg']};
            border: 1px solid {self.colors['border']};
            border-radius: 18px;
            margin: 8px;
        }}
        
        #menuButtonContainer:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, 
                stop:1 #F8FAFC);
            border: 1px solid {self.colors['primary']};
            transform: translateY(-2px);
        }}
        
        #menuButtonIcon {{
            font-size: 24px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {self.colors['primary']}, 
                stop:1 {self.colors['primary_end']});
            border-radius: 20px;
            color: white;
        }}
        
        #menuButtonTitle {{
            font-size: 16px;
            font-weight: 700;
            color: {self.colors['text_primary']};
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
        }}
        
        #menuButtonDesc {{
            font-size: 13px;
            font-weight: 400;
            color: {self.colors['text_secondary']};
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
            line-height: 1.4;
        }}
        
        #statusDot_primary {{
            color: {self.colors['primary']};
            font-size: 12px;
        }}
        
        #statusDot_secondary {{
            color: {self.colors['secondary']};
            font-size: 12px;
        }}
        
        #statusDot_accent {{
            color: {self.colors['accent']};
            font-size: 12px;
        }}
        
        #statusDot_success {{
            color: {self.colors['success']};
            font-size: 12px;
        }}
        
        #statusDot_warning {{
            color: {self.colors['warning']};
            font-size: 12px;
        }}
        
        #statusDot_text_secondary {{
            color: {self.colors['text_secondary']};
            font-size: 12px;
        }}
        
        #statusText {{
            font-size: 11px;
            font-weight: 500;
            color: {self.colors['text_light']};
            margin-left: 4px;
        }}
        
        #infoFrame {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['card_bg']}, 
                stop:1 {self.colors['background_alt']});
            border-top: 1px solid {self.colors['border']};
            padding: 15px 30px;
        }}
        
        #statusLabel {{
            font-size: 14px;
            font-weight: 600;
            color: {self.colors['success']};
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
        }}
        
        #userCountLabel {{
            font-size: 14px;
            font-weight: 500;
            color: {self.colors['text_secondary']};
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
        }}
        
        #copyrightLabel {{
            font-size: 12px;
            font-weight: 400;
            color: {self.colors['text_light']};
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
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
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
        }}
        
        #backButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5A6268, 
                stop:1 #495057);
            transform: translateY(-1px);
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
    
    def open_cookie_menu(self):
        """Çerez Kasıcı/Çerez Çıkarıcı menüsünü aç"""
        try:
            cookie_window = CookieWindow(self.colors, self.return_to_main)
            self.stacked_widget.addWidget(cookie_window)
            self.stacked_widget.setCurrentWidget(cookie_window)
        except Exception as e:
            self.show_error(f"Çerez Kasıcı açılırken hata: {str(e)}")
    
    def open_target_menu(self):
        """Hedef Hesaplar menüsünü aç"""
        try:
            target_window = TargetWindow(self.colors, self.return_to_main)
            self.stacked_widget.addWidget(target_window)
            self.stacked_widget.setCurrentWidget(target_window)
        except Exception as e:
            self.show_error(f"Hedef Hesaplar açılırken hata: {str(e)}")
    
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
        """Yakında gelecek özellikler için gelişmiş mesaj"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("🚀 Yakında Geliyor")
        msg.setText("Bu özellik şu anda geliştirme aşamasında!\n\nÇok yakında kullanıma sunulacak. Güncellemeler için takipte kalın.")
        msg.setStyleSheet(f"""
            QMessageBox {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.colors['background']}, 
                    stop:1 {self.colors['background_alt']});
                color: {self.colors['text_primary']};
                border-radius: 12px;
            }}
            QMessageBox QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.colors['primary']}, 
                    stop:1 {self.colors['primary_end']});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }}
            QMessageBox QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.colors['primary_end']}, 
                    stop:1 {self.colors['primary']});
            }}
        """)
        msg.exec_()
    
    def show_error(self, message):
        """Gelişmiş hata mesajı göster"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("❌ Hata")
        msg.setText(message)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.colors['background']}, 
                    stop:1 {self.colors['background_alt']});
                color: {self.colors['text_primary']};
                border-radius: 12px;
            }}
            QMessageBox QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.colors['error']}, 
                    stop:1 #C0392B);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }}
            QMessageBox QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #C0392B, 
                    stop:1 {self.colors['error']});
            }}
        """)
        msg.exec_()
