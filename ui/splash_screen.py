
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QProgressBar, QApplication)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QPainter, QLinearGradient, QColor
import time
import os
from database.mysql import mysql_manager

class InitializationWorker(QThread):
    """Arka planda başlatma işlemlerini yapan thread"""
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(bool)
    
    def run(self):
        """Başlatma işlemlerini yap"""
        try:
            # Adım 1: Dosya sistemi kontrolü
            self.progress_updated.emit(20, "Dosya sistemi kontrol ediliyor...")
            time.sleep(0.5)
            
            # Adım 2: Veritabanı bağlantısı
            self.progress_updated.emit(40, "MySQL bağlantısı kuruluyor...")
            time.sleep(0.8)
            
            # MySQL bağlantısını test et
            if mysql_manager.test_connection():
                self.progress_updated.emit(60, "Veritabanı bağlantısı başarılı")
            else:
                self.progress_updated.emit(60, "Veritabanı bağlantısı başarısız!")
                time.sleep(1)
            
            # Adım 3: Tabloları kontrol et/oluştur
            self.progress_updated.emit(80, "Veritabanı yapısı kontrol ediliyor...")
            mysql_manager.create_tables()
            time.sleep(0.7)
            
            # Adım 4: Sistem hazırlığı
            self.progress_updated.emit(95, "Sistem hazırlanıyor...")
            time.sleep(0.5)
            
            # Adım 5: Tamamlandı
            self.progress_updated.emit(100, "Başlatma tamamlandı!")
            time.sleep(0.3)
            
            self.finished.emit(True)
            
        except Exception as e:
            self.progress_updated.emit(100, f"Hata: {str(e)}")
            self.finished.emit(False)

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.colors = {
            'primary': '#FF6B35',
            'primary_end': '#F7931E',
            'text_primary': '#2C3E50',
            'text_secondary': '#5D6D7E',
            'background': '#FFFFFF',
            'background_alt': '#F8F9FA',
        }
        
        self.init_ui()
        self.setup_style()
        self.start_initialization()
        
    def init_ui(self):
        """UI'yi başlat"""
        self.setWindowTitle("AkTweetor")
        self.setFixedSize(500, 350)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Ana layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # Logo container
        logo_container = QVBoxLayout()
        logo_container.setAlignment(Qt.AlignCenter)
        
        # Logo
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(120, 120)
        
        # Logo dosyasını yükle
        if os.path.exists("assets/logo.png"):
            pixmap = QPixmap("assets/logo.png")
            scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
        else:
            # Logo yoksa emoji kullan
            self.logo_label.setText("🐦")
            self.logo_label.setStyleSheet("""
                font-size: 80px;
                color: #FF6B35;
            """)
        
        logo_container.addWidget(self.logo_label)
        
        # Başlık
        title_label = QLabel("AkTweetor")
        title_label.setObjectName("splashTitle")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Alt başlık
        subtitle_label = QLabel("Twitter Otomasyon Platformu")
        subtitle_label.setObjectName("splashSubtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("splashProgress")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        
        # Durum etiketi
        self.status_label = QLabel("Başlatılıyor...")
        self.status_label.setObjectName("splashStatus")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Versiyon bilgisi
        version_label = QLabel("v1.0.0 Pro Edition")
        version_label.setObjectName("splashVersion")
        version_label.setAlignment(Qt.AlignCenter)
        
        # Layout'a ekle
        main_layout.addLayout(logo_container)
        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.status_label)
        main_layout.addStretch()
        main_layout.addWidget(version_label)
        
        self.setLayout(main_layout)
        
        # Ekranı ortala
        self.center_on_screen()
    
    def center_on_screen(self):
        """Ekranı ortala"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def setup_style(self):
        """Stil ayarlarını uygula"""
        style = f"""
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['background']}, 
                stop:1 {self.colors['background_alt']});
            border-radius: 15px;
        }}
        
        #splashTitle {{
            font-size: 32px;
            font-weight: 800;
            color: {self.colors['text_primary']};
            font-family: 'SF Pro Display', 'Segoe UI', 'Roboto', sans-serif;
        }}
        
        #splashSubtitle {{
            font-size: 16px;
            font-weight: 400;
            color: {self.colors['text_secondary']};
            font-family: 'SF Pro Display', 'Segoe UI', 'Roboto', sans-serif;
        }}
        
        #splashProgress {{
            border: 2px solid {self.colors['background_alt']};
            border-radius: 10px;
            background-color: {self.colors['background_alt']};
            height: 20px;
        }}
        
        #splashProgress::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self.colors['primary']}, 
                stop:1 {self.colors['primary_end']});
            border-radius: 8px;
        }}
        
        #splashStatus {{
            font-size: 14px;
            font-weight: 500;
            color: {self.colors['text_secondary']};
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
        }}
        
        #splashVersion {{
            font-size: 12px;
            font-weight: 400;
            color: {self.colors['text_secondary']};
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
        }}
        """
        
        self.setStyleSheet(style)
    
    def start_initialization(self):
        """Başlatma işlemini başlat"""
        self.worker = InitializationWorker()
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self.on_initialization_finished)
        self.worker.start()
    
    def update_progress(self, value, status):
        """Progress bar'ı güncelle"""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
    
    def on_initialization_finished(self, success):
        """Başlatma tamamlandığında çağrılır"""
        if success:
            # 500ms bekle ve ana pencereyi aç
            QTimer.singleShot(500, self.open_main_window)
        else:
            # Hata durumunda 2 saniye bekle
            self.status_label.setText("❌ Başlatma başarısız!")
            QTimer.singleShot(2000, self.close)
    
    def open_main_window(self):
        """Ana pencereyi aç"""
        from ui.main_window import MainWindow
        
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()
    
    def paintEvent(self, event):
        """Özel çizim olayı - gradient arka plan için"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Gradient oluştur
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(self.colors['background']))
        gradient.setColorAt(1, QColor(self.colors['background_alt']))
        
        painter.fillRect(self.rect(), gradient)
