
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
from config.settings import settings
from utils.logger import logger
from utils.exceptions import DatabaseException, handle_exception

class MySQLManager:
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
            
        except Exception as e:
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
            
            # Önce eski tabloları sil
            old_tables = ['kullanici_kategorileri', 'islem_logları', 'sistem_ayarları']
            for table in old_tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    print(f"🗑️ Eski tablo silindi: {table}")
                except:
                    pass
            
            print("✅ Eski tablolar temizlendi")
            
            # kullanicilar tablosu
            create_users_table = """
            CREATE TABLE IF NOT EXISTS kullanicilar (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kullanici_adi VARCHAR(255) NOT NULL UNIQUE,
                sifre VARCHAR(255),
                email VARCHAR(255),
                telefon VARCHAR(20),
                durum ENUM('aktif', 'pasif', 'banli') DEFAULT 'aktif',
                profil_klasoru VARCHAR(255),
                twitter_olusturma_tarihi DATETIME,
                proxy_ip VARCHAR(255),
                proxy_port INT,
                cerezler TEXT,
                son_giris TIMESTAMP NULL,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_kullanici_adi (kullanici_adi),
                INDEX idx_durum (durum)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_users_table)
            
            # hedef_hesaplar tablosu
            create_targets_table = """
            CREATE TABLE IF NOT EXISTS hedef_hesaplar (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kullanici_adi VARCHAR(255) NOT NULL,
                yil INT,
                ay INT,
                twitter_olusturma_tarihi DATETIME,
                proxy_ip VARCHAR(255),
                proxy_port INT,
                durum ENUM('aktif', 'pasif') DEFAULT 'aktif',
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_kullanici_adi (kullanici_adi),
                INDEX idx_yil_ay (yil, ay),
                INDEX idx_durum (durum)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_targets_table)
            
            connection.commit()
            print("✅ Yeni tablo yapısı oluşturuldu")
            logger.info("✅ MySQL tabloları oluşturuldu/kontrol edildi")
            
            # Eksik sütunları ekle
            self.add_missing_columns()
            
        except Error as e:
            logger.error(f"❌ Tablo oluşturma hatası: {e}")
            connection.rollback()
            raise DatabaseException(f"Tablo oluşturma hatası: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def add_missing_columns(self):
        """Eksik sütunları ekle"""
        connection = self.get_connection()
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            
            # kullanicilar tablosu için eksik sütunları kontrol et ve ekle
            columns_to_add = [
                ('kullanicilar', 'twitter_olusturma_tarihi', 'DATETIME'),
                ('kullanicilar', 'proxy_ip', 'VARCHAR(255)'),
                ('kullanicilar', 'proxy_port', 'INT'),
                ('kullanicilar', 'cerezler', 'TEXT'),
                ('hedef_hesaplar', 'twitter_olusturma_tarihi', 'DATETIME'),
                ('hedef_hesaplar', 'proxy_ip', 'VARCHAR(255)'),
                ('hedef_hesaplar', 'proxy_port', 'INT')
            ]
            
            for table, column, data_type in columns_to_add:
                try:
                    # Sütunun var olup olmadığını kontrol et
                    cursor.execute(f"SHOW COLUMNS FROM {table} LIKE '{column}'")
                    if not cursor.fetchone():
                        # Sütun yoksa ekle
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {data_type}")
                        logger.info(f"✅ {table} tablosuna {column} sütunu eklendi")
                except Error as e:
                    logger.error(f"⚠️ {table} tablosuna {column} sütunu eklenirken hata: {e}")
            
            connection.commit()
            
        except Error as e:
            logger.error(f"❌ Sütun ekleme hatası: {e}")
            connection.rollback()
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
    
    @handle_exception
    def get_all_targets(self):
        """Tüm hedef hesapları getir"""
        connection = self.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM hedef_hesaplar WHERE durum = 'aktif' ORDER BY kullanici_adi"
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        except Error as e:
            logger.error(f"❌ Hedef hesaplar getirme hatası: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def get_target_creation_date(self, username):
        """Hedef hesabın Twitter oluşturma tarihini getir"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor()
            query = "SELECT twitter_olusturma_tarihi FROM hedef_hesaplar WHERE kullanici_adi = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            return result[0] if result and result[0] else None
        except Error as e:
            logger.error(f"❌ Hedef hesap Twitter oluşturma tarihi getirme hatası: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def update_target_creation_date(self, username, creation_date):
        """Hedef hesabın Twitter oluşturma tarihini güncelle"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # DATETIME formatında kaydet
            if isinstance(creation_date, str):
                try:
                    formats = [
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%d %H:%M',
                        '%Y-%m-%d',
                        '%d/%m/%Y %H:%M:%S',
                        '%d/%m/%Y %H:%M',
                        '%d/%m/%Y',
                        '%Y:%m:%d:%H:%M',
                        '%Y:%m:%d'
                    ]
                    
                    parsed_date = None
                    for fmt in formats:
                        try:
                            parsed_date = datetime.strptime(creation_date, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if parsed_date is None:
                        print(f"⚠️ Tarih formatı tanınmadı: {creation_date}")
                        return False
                    
                    creation_date = parsed_date
                except Exception as e:
                    print(f"⚠️ Tarih dönüştürme hatası: {e}")
                    return False
            
            query = "UPDATE hedef_hesaplar SET twitter_olusturma_tarihi = %s WHERE kullanici_adi = %s"
            cursor.execute(query, (creation_date, username))
            connection.commit()
            
            return cursor.rowcount > 0
        except Error as e:
            logger.error(f"❌ Hedef hesap Twitter oluşturma tarihi güncelleme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def add_target(self, username, year=None, month=None):
        """Hedef hesap ekle"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Var olup olmadığını kontrol et
            check_query = "SELECT id FROM hedef_hesaplar WHERE kullanici_adi = %s"
            cursor.execute(check_query, (username,))
            existing = cursor.fetchone()
            
            if existing:
                # Güncelle
                update_query = """
                UPDATE hedef_hesaplar 
                SET yil = %s, ay = %s, guncelleme_tarihi = CURRENT_TIMESTAMP 
                WHERE kullanici_adi = %s
                """
                cursor.execute(update_query, (year, month, username))
            else:
                # Yeni ekle
                insert_query = """
                INSERT INTO hedef_hesaplar (kullanici_adi, yil, ay, durum, olusturma_tarihi)
                VALUES (%s, %s, %s, 'aktif', CURRENT_TIMESTAMP)
                """
                cursor.execute(insert_query, (username, year, month))
            
            connection.commit()
            return True
        except Error as e:
            logger.error(f"❌ Hedef hesap ekleme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def delete_target(self, username):
        """Hedef hesabı sil"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            query = "DELETE FROM hedef_hesaplar WHERE kullanici_adi = %s"
            cursor.execute(query, (username,))
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            logger.error(f"❌ Hedef hesap silme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def get_target_stats(self):
        """Hedef hesap istatistiklerini getir"""
        connection = self.get_connection()
        if not connection:
            return {}
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Toplam sayı
            cursor.execute("SELECT COUNT(*) as toplam FROM hedef_hesaplar")
            toplam = cursor.fetchone()['toplam']
            
            # Aktif sayı
            cursor.execute("SELECT COUNT(*) as aktif FROM hedef_hesaplar WHERE durum = 'aktif'")
            aktif = cursor.fetchone()['aktif']
            
            # Tarihli sayı
            cursor.execute("SELECT COUNT(*) as tarihli FROM hedef_hesaplar WHERE twitter_olusturma_tarihi IS NOT NULL")
            tarihli = cursor.fetchone()['tarihli']
            
            return {
                'toplam': toplam,
                'aktif': aktif,
                'tarihli': tarihli
            }
        except Error as e:
            logger.error(f"❌ Hedef hesap istatistik hatası: {e}")
            return {}
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def import_targets_from_file(self, file_path):
        """Dosyadan hedef hesapları içe aktar"""
        try:
            imported_count = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(':')
                    username = parts[0].strip()
                    year = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else None
                    month = int(parts[2]) if len(parts) > 2 and parts[2].strip().isdigit() else None
                    
                    if self.add_target(username, year, month):
                        imported_count += 1
            
            return imported_count
        except Exception as e:
            logger.error(f"❌ Dosyadan içe aktarma hatası: {e}")
            return 0

# Global MySQL manager instance
mysql_manager = MySQLManager()
