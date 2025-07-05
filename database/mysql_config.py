
import mysql.connector
from mysql.connector import Error
import os
from config.settings import settings
from utils.logger import logger
from utils.exceptions import DatabaseException, handle_exception

class MySQLConfig:
    def __init__(self):
        # Settings'den MySQL bağlantı bilgilerini al
        self.host = settings.get('database.host', 'localhost')
        self.database = settings.get('database.database', 'aktweetor')
        self.username = settings.get('database.username', 'root')
        self.password = settings.get('database.password', '')
        self.port = settings.get('database.port', 3306)
        self.pool_size = settings.get('database.pool_size', 5)
        
        # Bağlantı havuzu
        self.connection_pool = None
        self.init_connection_pool()
    
    @handle_exception
    def init_connection_pool(self):
        """Bağlantı havuzunu başlat"""
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="aktweetor_pool",
                pool_size=self.pool_size,
                pool_reset_session=True,
                host=self.host,
                database=self.database,
                user=self.username,
                password=self.password,
                port=self.port,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=False,
                sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'
            )
            logger.info("✅ MySQL bağlantı havuzu oluşturuldu")
            
            # Tabloları oluştur
            self.create_tables()
            
        except Error as e:
            logger.error(f"❌ MySQL bağlantı havuzu hatası: {e}")
            self.connection_pool = None
            raise DatabaseException(f"MySQL bağlantı havuzu hatası: {e}")
    
    @handle_exception
    def get_connection(self):
        """Bağlantı havuzundan bağlantı al"""
        try:
            if self.connection_pool:
                connection = self.connection_pool.get_connection()
                logger.debug("Bağlantı havuzundan bağlantı alındı")
                return connection
            else:
                # Havuz yoksa direkt bağlantı oluştur
                connection = mysql.connector.connect(
                    host=self.host,
                    database=self.database,
                    user=self.username,
                    password=self.password,
                    port=self.port,
                    charset='utf8mb4',
                    collation='utf8mb4_unicode_ci',
                    autocommit=False
                )
                logger.debug("Direkt MySQL bağlantısı oluşturuldu")
                return connection
        except Error as e:
            logger.error(f"❌ MySQL bağlantı hatası: {e}")
            raise DatabaseException(f"MySQL bağlantı hatası: {e}")
    
    @handle_exception
    def create_tables(self):
        """Gerekli tabloları oluştur"""
        connection = self.get_connection()
        if not connection:
            raise DatabaseException("Bağlantı alınamadı")
        
        try:
            cursor = connection.cursor()
            
            # kullanicilar tablosu
            create_users_table = """
            CREATE TABLE IF NOT EXISTS kullanicilar (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kullanici_adi VARCHAR(255) NOT NULL UNIQUE,
                sifre VARCHAR(255) NOT NULL,
                auth_token TEXT,
                gt TEXT,
                guest_id TEXT,
                twid TEXT,
                lang VARCHAR(10),
                __cf_bm TEXT,
                att TEXT,
                ct0 TEXT,
                d_prefs TEXT,
                dnt VARCHAR(10),
                guest_id_ads TEXT,
                guest_id_marketing TEXT,
                kdt TEXT,
                personalization_id TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                durum ENUM('aktif', 'pasif', 'banli') DEFAULT 'aktif',
                son_giris TIMESTAMP NULL,
                giris_sayisi INT DEFAULT 0,
                basarili_islem_sayisi INT DEFAULT 0,
                basarisiz_islem_sayisi INT DEFAULT 0,
                son_ip VARCHAR(45),
                proxy_bilgisi TEXT,
                notlar TEXT,
                INDEX idx_kullanici_adi (kullanici_adi),
                INDEX idx_durum (durum),
                INDEX idx_son_giris (son_giris),
                INDEX idx_olusturma_tarihi (olusturma_tarihi)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_users_table)
            
            # hesap_kategorileri tablosu
            create_categories_table = """
            CREATE TABLE IF NOT EXISTS hesap_kategorileri (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kategori_adi VARCHAR(255) NOT NULL UNIQUE,
                aciklama TEXT,
                renk VARCHAR(7) DEFAULT '#007bff',
                sira_no INT DEFAULT 0,
                aktif BOOLEAN DEFAULT TRUE,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_kategori_adi (kategori_adi),
                INDEX idx_sira_no (sira_no)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_categories_table)
            
            # kullanici_kategorileri tablosu
            create_user_categories_table = """
            CREATE TABLE IF NOT EXISTS kullanici_kategorileri (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kullanici_id INT,
                kategori_id INT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id) ON DELETE CASCADE,
                FOREIGN KEY (kategori_id) REFERENCES hesap_kategorileri(id) ON DELETE CASCADE,
                UNIQUE KEY unique_user_category (kullanici_id, kategori_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_user_categories_table)
            
            # islem_logları tablosu
            create_logs_table = """
            CREATE TABLE IF NOT EXISTS islem_logları (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kullanici_id INT,
                islem_tipi ENUM('giris', 'cerez_alma', 'begeni', 'retweet', 'yorum', 'takip', 'takip_birak', 'profil_guncellemesi') NOT NULL,
                islem_detayi TEXT,
                durum ENUM('basarili', 'basarisiz', 'beklemede') DEFAULT 'beklemede',
                hata_mesaji TEXT,
                ip_adresi VARCHAR(45),
                user_agent TEXT,
                proxy_bilgisi TEXT,
                islem_süresi DECIMAL(10,3),
                islem_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id) ON DELETE CASCADE,
                INDEX idx_kullanici_islem (kullanici_id, islem_tipi),
                INDEX idx_islem_tarihi (islem_tarihi),
                INDEX idx_durum (durum),
                INDEX idx_islem_tipi (islem_tipi)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_logs_table)
            
            # sistem_ayarları tablosu
            create_settings_table = """
            CREATE TABLE IF NOT EXISTS sistem_ayarları (
                id INT AUTO_INCREMENT PRIMARY KEY,
                anahtar VARCHAR(255) NOT NULL UNIQUE,
                deger TEXT,
                aciklama TEXT,
                veri_tipi ENUM('string', 'integer', 'boolean', 'json') DEFAULT 'string',
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_anahtar (anahtar)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_settings_table)
            
            connection.commit()
            logger.info("✅ MySQL tabloları oluşturuldu/kontrol edildi")
            
        except Error as e:
            logger.error(f"❌ Tablo oluşturma hatası: {e}")
            connection.rollback()
            raise DatabaseException(f"Tablo oluşturma hatası: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def test_connection(self):
        """Bağlantıyı test et"""
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                logger.info("✅ MySQL bağlantısı başarılı")
                return True
            except Error as e:
                logger.error(f"❌ MySQL bağlantı testi başarısız: {e}")
                raise DatabaseException(f"MySQL bağlantı testi başarısız: {e}")
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        return False
    
    def get_connection_info(self):
        """Bağlantı bilgilerini al"""
        return {
            'host': self.host,
            'database': self.database,
            'username': self.username,
            'port': self.port,
            'pool_size': self.pool_size
        }

# Global MySQL yapılandırması
mysql_config = MySQLConfig()
