import mysql.connector
from mysql.connector import Error
import os

class MySQLConfig:
    def __init__(self):
        # MySQL bağlantı bilgileri
        self.host = "localhost"
        self.database = "aktweetor"
        self.username = "root"
        self.password = ""
        self.port = 3306

        # Bağlantı havuzu
        self.connection_pool = None
        self.init_connection_pool()

    def init_connection_pool(self):
        """Bağlantı havuzunu başlat"""
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="aktweetor_pool",
                pool_size=5,
                pool_reset_session=True,
                host=self.host,
                database=self.database,
                user=self.username,
                password=self.password,
                port=self.port,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            print("✅ MySQL bağlantı havuzu oluşturuldu")

            # Tabloları oluştur
            self.create_tables()

        except Error as e:
            print(f"❌ MySQL bağlantı havuzu hatası: {e}")
            self.connection_pool = None

    def get_connection(self):
        """Bağlantı havuzundan bağlantı al"""
        try:
            if self.connection_pool:
                connection = self.connection_pool.get_connection()
                if connection and connection.is_connected():
                    return connection
                else:
                    print("⚠️ Bağlantı havuzundan geçersiz bağlantı alındı, yeniden deneniyor...")

            # Havuz yoksa veya bağlantı geçersizse direkt bağlantı oluştur
            connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.username,
                password=self.password,
                port=self.port,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=False,
                connection_timeout=10
            )
            return connection

        except Error as e:
            print(f"❌ MySQL bağlantı hatası: {e}")
            print("📝 MySQL servisi çalışıyor mu kontrol edin!")
            return None
        except Exception as e:
            print(f"❌ Beklenmeyen bağlantı hatası: {e}")
            return None

    def is_mysql_available(self):
        """MySQL'in kullanılabilir olup olmadığını kontrol et"""
        connection = self.get_connection()
        if connection:
            try:
                connection.close()
                return True
            except:
                pass
        return False

    def create_tables(self):
        """Gerekli tabloları oluştur"""
        connection = self.get_connection()
        if not connection:
            return

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
                INDEX idx_kullanici_adi (kullanici_adi),
                INDEX idx_durum (durum),
                INDEX idx_son_giris (son_giris)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """

            cursor.execute(create_users_table)

            # hesap_kategorileri tablosu (gelecek özellikler için)
            create_categories_table = """
            CREATE TABLE IF NOT EXISTS hesap_kategorileri (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kategori_adi VARCHAR(255) NOT NULL,
                aciklama TEXT,
                renk VARCHAR(7) DEFAULT '#007bff',
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """

            cursor.execute(create_categories_table)

            # kullanici_kategorileri tablosu (many-to-many ilişki)
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
                islem_tipi ENUM('giris', 'cerez_alma', 'beğeni', 'retweet', 'yorum', 'takip', 'takip_birak') NOT NULL,
                islem_detayi TEXT,
                durum ENUM('basarili', 'basarisiz', 'beklemede') DEFAULT 'beklemede',
                hata_mesaji TEXT,
                islem_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id) ON DELETE CASCADE,
                INDEX idx_kullanici_islem (kullanici_id, islem_tipi),
                INDEX idx_islem_tarihi (islem_tarihi),
                INDEX idx_durum (durum)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """

            cursor.execute(create_logs_table)

            connection.commit()
            print("✅ MySQL tabloları oluşturuldu/kontrol edildi")

        except Error as e:
            print(f"❌ Tablo oluşturma hatası: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def test_connection(self):
        """Bağlantıyı test et"""
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                print("✅ MySQL bağlantısı başarılı")
                return True
            except Error as e:
                print(f"❌ MySQL bağlantı testi başarısız: {e}")
                return False
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        return False

# Global MySQL yapılandırması
mysql_config = MySQLConfig()
