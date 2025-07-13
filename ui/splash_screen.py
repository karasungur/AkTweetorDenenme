
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QProgressBar, QApplication, QFrame)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QPixmap, QFont, QPainter, QLinearGradient, QColor, QMovie, QBrush, QPen
import time
import os
from database.mysql import mysql_manager

class PulsingDot(QLabel):
    """Animasyonlu nokta widget'i"""
    def __init__(self, color, delay=0):
        super().__init__()
        self.setFixedSize(12, 12)
        self.color = color
        self.opacity = 0.3
        
        # Animasyon timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(80)
        
        # Gecikme için başlangıç sayacı
        self.delay_counter = delay
        self.direction = 1
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 6px;
                opacity: {self.opacity};
            }}
        """)
    
    def animate(self):
        if self.delay_counter > 0:
            self.delay_counter -= 1
            return
            
        self.opacity += 0.05 * self.direction
        if self.opacity >= 1.0:
            self.direction = -1
        elif self.opacity <= 0.3:
            self.direction = 1
            
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {self.color};
                border-radius: 6px;
                opacity: {self.opacity};
            }}
        """)

class ModernProgressBar(QProgressBar):
    """Modern progress bar widget'i"""
    def __init__(self):
        super().__init__()
        self.setRange(0, 100)
        self.setValue(0)
        self.setTextVisible(False)
        self.setFixedHeight(8)
        
        # Animasyon için değerler
        self.target_value = 0
        self.current_value = 0
        
        # Smooth animasyon timer
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.smooth_update)
        self.anim_timer.start(16)  # 60 FPS
    
    def set_target_value(self, value):
        self.target_value = value
    
    def smooth_update(self):
        if self.current_value != self.target_value:
            diff = self.target_value - self.current_value
            self.current_value += diff * 0.1
            super().setValue(int(self.current_value))

class InitializationWorker(QThread):
    """Arka planda başlatma işlemlerini yapan thread"""
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(bool)
    
    def run(self):
        """Başlatma işlemlerini yap"""
        try:
            import random
            
            print("🔍 InitializationWorker başlatıldı")
            
            # Toplam süre 8-12 saniye arasında rastgele (biraz uzattık)
            total_time = random.uniform(8.0, 12.0)
            print(f"🕐 Toplam yükleme süresi: {total_time:.2f} saniye")
            
            # Adım 1: Dosya sistemi kontrolü
            self.progress_updated.emit(15, "Dosya sistemi hazırlanıyor...")
            time.sleep(total_time * 0.15)
            
            # Adım 2: Konfigürasyon yükleme
            self.progress_updated.emit(30, "Konfigürasyon dosyaları yükleniyor...")
            time.sleep(total_time * 0.12)
            
            # Adım 3: Veritabanı bağlantısı
            self.progress_updated.emit(50, "Veritabanı bağlantısı kuruluyor...")
            time.sleep(total_time * 0.20)
            
            # MySQL bağlantısını test et
            try:
                if mysql_manager.test_connection():
                    self.progress_updated.emit(70, "Veritabanı bağlantısı başarılı ✓")
                    print("✅ MySQL bağlantısı başarılı")
                else:
                    self.progress_updated.emit(70, "Veritabanı bağlantısı başarısız!")
                    print("⚠️ MySQL bağlantısı başarısız")
            except Exception as db_e:
                print(f"⚠️ MySQL test hatası: {str(db_e)}")
                self.progress_updated.emit(70, "Veritabanı bağlantısı atlandı")
            
            time.sleep(total_time * 0.15)
            
            # Adım 4: Tabloları kontrol et/oluştur
            self.progress_updated.emit(85, "Veritabanı yapısı kontrol ediliyor...")
            try:
                mysql_manager.create_tables()
                print("✅ MySQL tabloları kontrol edildi")
            except Exception as table_e:
                print(f"⚠️ MySQL tablo hatası: {str(table_e)}")
            time.sleep(total_time * 0.18)
            
            # Adım 5: UI hazırlığı
            self.progress_updated.emit(95, "Arayüz hazırlanıyor...")
            time.sleep(total_time * 0.12)
            
            # Adım 6: Tamamlandı
            self.progress_updated.emit(100, "Başlatma tamamlandı! ✓")
            time.sleep(total_time * 0.08)
            
            print("✅ InitializationWorker başarıyla tamamlandı")
            self.finished.emit(True)
            
        except Exception as e:
            print(f"❌ InitializationWorker hatası: {str(e)}")
            import traceback
            traceback.print_exc()
            self.progress_updated.emit(100, f"Hata: {str(e)}")
            self.finished.emit(False)

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.colors = {
            'primary': '#667eea',
            'primary_end': '#764ba2',
            'accent': '#FF6B35',
            'accent_end': '#F7931E',
            'text_primary': '#2C3E50',
            'text_secondary': '#5D6D7E',
            'text_light': '#8B9DC3',
            'background': '#FFFFFF',
            'background_alt': '#F8FAFF',
            'card_bg': 'rgba(255, 255, 255, 0.9)',
        }
        
        self.init_ui()
        self.setup_style()
        self.start_initialization()
        
    def init_ui(self):
        """UI'yi başlat"""
        self.setWindowTitle("AkTweetor")
        self.setFixedSize(700, 520)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Ana layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Ana container
        main_container = QFrame()
        main_container.setObjectName("splashContainer")
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(60, 60, 60, 60)
        container_layout.setSpacing(40)
        
        # Logo container
        logo_container = QVBoxLayout()
        logo_container.setAlignment(Qt.AlignCenter)
        
        # Logo (GIF desteği)
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(130, 130)
        
        # Logo.gif dosyasını yükle, yoksa PNG kullan
        if os.path.exists("assets/logo.gif"):
            self.movie = QMovie("assets/logo.gif")
            self.movie.setScaledSize(self.logo_label.size())
            self.logo_label.setMovie(self.movie)
            self.movie.start()
        elif os.path.exists("assets/logo.png"):
            pixmap = QPixmap("assets/logo.png")
            scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
        else:
            # Logo yoksa emoji kullan
            self.logo_label.setText("🐦")
            self.logo_label.setStyleSheet("""
                font-size: 100px;
                color: #667eea;
            """)
        
        logo_container.addWidget(self.logo_label)
        
        # Başlık container
        title_container = QVBoxLayout()
        title_container.setAlignment(Qt.AlignCenter)
        title_container.setSpacing(12)
        
        # Ana başlık
        title_label = QLabel("AkTweetor")
        title_label.setObjectName("splashTitle")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Alt başlık
        subtitle_label = QLabel("Profesyonel Twitter Otomasyon Platformu")
        subtitle_label.setObjectName("splashSubtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        # Versiyon badge
        version_container = QHBoxLayout()
        version_container.setAlignment(Qt.AlignCenter)
        
        version_badge = QLabel("v1.0.0 Pro Edition")
        version_badge.setObjectName("versionBadge")
        version_badge.setAlignment(Qt.AlignCenter)
        
        version_container.addWidget(version_badge)
        
        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)
        title_container.addLayout(version_container)
        
        # Progress container
        progress_container = QVBoxLayout()
        progress_container.setAlignment(Qt.AlignCenter)
        progress_container.setSpacing(25)
        
        # Progress bar
        self.progress_bar = ModernProgressBar()
        self.progress_bar.setObjectName("modernProgress")
        
        # Status container
        status_container = QVBoxLayout()
        status_container.setAlignment(Qt.AlignCenter)
        status_container.setSpacing(15)
        
        # Durum etiketi
        self.status_label = QLabel("Başlatılıyor...")
        self.status_label.setObjectName("splashStatus")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Yükleme animasyon noktaları
        dots_container = QHBoxLayout()
        dots_container.setAlignment(Qt.AlignCenter)
        dots_container.setSpacing(8)
        
        self.dots = []
        for i in range(3):
            dot = PulsingDot(self.colors['primary'], delay=i*5)
            self.dots.append(dot)
            dots_container.addWidget(dot)
        
        status_container.addWidget(self.status_label)
        status_container.addLayout(dots_container)
        
        progress_container.addWidget(self.progress_bar)
        progress_container.addLayout(status_container)
        
        # Ana container'a ekle
        container_layout.addLayout(logo_container)
        container_layout.addLayout(title_container)
        container_layout.addStretch()
        container_layout.addLayout(progress_container)
        
        main_container.setLayout(container_layout)
        main_layout.addWidget(main_container)
        
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
        """Modern stil ayarlarını uygula"""
        style = f"""
        #splashContainer {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self.colors['background']}, 
                stop:1 {self.colors['background_alt']});
            border-radius: 20px;
            border: 2px solid rgba(102, 126, 234, 0.1);
        }}
        
        #splashTitle {{
            font-size: 42px;
            font-weight: 800;
            color: {self.colors['text_primary']};
            font-family: 'SF Pro Display', 'Segoe UI', 'Roboto', sans-serif;
            letter-spacing: -1px;
        }}
        
        #splashSubtitle {{
            font-size: 18px;
            font-weight: 400;
            color: {self.colors['text_secondary']};
            font-family: 'SF Pro Display', 'Segoe UI', 'Roboto', sans-serif;
            letter-spacing: 0.5px;
        }}
        
        #versionBadge {{
            font-size: 12px;
            font-weight: 600;
            color: {self.colors['primary']};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(102, 126, 234, 0.1), 
                stop:1 rgba(118, 75, 162, 0.1));
            padding: 8px 20px;
            border-radius: 25px;
            border: 1px solid rgba(102, 126, 234, 0.2);
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
        }}
        
        #modernProgress {{
            border: none;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 4px;
            min-width: 400px;
        }}
        
        #modernProgress::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self.colors['primary']}, 
                stop:1 {self.colors['primary_end']});
            border-radius: 4px;
        }}
        
        #splashStatus {{
            font-size: 16px;
            font-weight: 500;
            color: {self.colors['text_secondary']};
            font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
            letter-spacing: 0.3px;
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
        self.progress_bar.set_target_value(value)
        self.status_label.setText(status)
    
    def on_initialization_finished(self, success):
        """Başlatma tamamlandığında çağrılır"""
        print(f"🔍 Initialization finished: {success}")
        if success:
            # 1.5 saniye bekle ve ana pencereyi aç (daha uzun süre)
            print("✅ Başlatma başarılı, ana pencere açılıyor...")
            QTimer.singleShot(1500, self.open_main_window)
        else:
            # Hata durumunda 3 saniye bekle
            print("❌ Başlatma başarısız!")
            self.status_label.setText("❌ Başlatma başarısız!")
            QTimer.singleShot(3000, self.close)
    
    def open_main_window(self):
        """Ana pencereyi aç"""
        try:
            print("🔍 Ana pencere yükleniyor...")
            from ui.main_window import MainWindow
            
            print("🔍 MainWindow sınıfı yüklendi, pencere oluşturuluyor...")
            self.main_window = MainWindow()
            print("🔍 Ana pencere oluşturuldu, gösteriliyor...")
            self.main_window.show()
            print("✅ Ana pencere başarıyla açıldı")
            self.close()
        except Exception as e:
            print(f"❌ Ana pencere açma hatası: {str(e)}")
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"❌ Ana pencere açma hatası: {str(e)}")
            QTimer.singleShot(3000, self.close)
    
    def paintEvent(self, event):
        """Özel çizim olayı - modern gradient arka plan"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Ana gradient
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(self.colors['background']))
        gradient.setColorAt(0.5, QColor('#F0F4FF'))
        gradient.setColorAt(1, QColor(self.colors['background_alt']))
        
        painter.fillRect(self.rect(), gradient)
        
        # Dekoratif daireler
        painter.setPen(QPen(QColor(102, 126, 234, 30), 2))
        painter.setBrush(QBrush(QColor(102, 126, 234, 15)))
        
        # Sol üst daire
        painter.drawEllipse(-50, -50, 200, 200)
        
        # Sağ alt daire
        painter.drawEllipse(self.width()-150, self.height()-150, 200, 200)
