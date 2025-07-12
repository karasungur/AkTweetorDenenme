
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
                kat_sayisi INT DEFAULT 1,
                yil INT,
                ay INT,
                twitter_olusturma_tarihi DATETIME,
                proxy_ip VARCHAR(255),
                proxy_port INT,
                durum ENUM('aktif', 'pasif') DEFAULT 'aktif',
                notlar TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_kullanici_adi (kullanici_adi),
                INDEX idx_yil_ay (yil, ay),
                INDEX idx_durum (durum),
                INDEX idx_kat_sayisi (kat_sayisi)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_targets_table)
            
            # profil_kategorileri tablosu
            create_profile_categories_table = """
            CREATE TABLE IF NOT EXISTS profil_kategorileri (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kategori_turu ENUM('profil', 'icerik') NOT NULL,
                ana_kategori VARCHAR(255) NOT NULL,
                alt_kategori VARCHAR(255),
                aciklama TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_kategori_turu (kategori_turu),
                INDEX idx_ana_kategori (ana_kategori)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_profile_categories_table)
            
            # hesap_kategorileri tablosu
            create_account_categories_table = """
            CREATE TABLE IF NOT EXISTS hesap_kategorileri (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kullanici_adi VARCHAR(255) NOT NULL,
                hesap_turu ENUM('giris_yapilan', 'hedef') NOT NULL,
                kategori_id INT,
                kategori_degeri VARCHAR(255),
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (kategori_id) REFERENCES profil_kategorileri(id) ON DELETE CASCADE,
                INDEX idx_kullanici_adi (kullanici_adi),
                INDEX idx_hesap_turu (hesap_turu),
                INDEX idx_kategori_id (kategori_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_account_categories_table)
            
            connection.commit()
            print("✅ Yeni tablo yapısı oluşturuldu")
            logger.info("✅ MySQL tabloları oluşturuldu/kontrol edildi")
            
            # Eksik sütunları ekle
            self.add_missing_columns()
            
            # Varsayılan kategorileri ekle
            self.add_default_categories()
            
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
                ('hedef_hesaplar', 'kat_sayisi', 'INT DEFAULT 1'),
                ('hedef_hesaplar', 'twitter_olusturma_tarihi', 'DATETIME'),
                ('hedef_hesaplar', 'proxy_ip', 'VARCHAR(255)'),
                ('hedef_hesaplar', 'proxy_port', 'INT'),
                ('hedef_hesaplar', 'notlar', 'TEXT')
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
    def add_target(self, username, kat_sayisi=1, year=None, month=None, notlar=None):
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
                # Güncelle - sadece None olmayan değerleri güncelle
                update_parts = []
                update_values = []
                
                if kat_sayisi is not None:
                    update_parts.append("kat_sayisi = %s")
                    update_values.append(kat_sayisi)
                if year is not None:
                    update_parts.append("yil = %s")
                    update_values.append(year)
                if month is not None:
                    update_parts.append("ay = %s")
                    update_values.append(month)
                if notlar is not None:
                    update_parts.append("notlar = %s")
                    update_values.append(notlar)
                
                if update_parts:
                    update_parts.append("guncelleme_tarihi = CURRENT_TIMESTAMP")
                    update_values.append(username)
                    
                    update_query = f"""
                    UPDATE hedef_hesaplar 
                    SET {', '.join(update_parts)}
                    WHERE kullanici_adi = %s
                    """
                    cursor.execute(update_query, update_values)
            else:
                # Yeni ekle
                insert_query = """
                INSERT INTO hedef_hesaplar (kullanici_adi, kat_sayisi, yil, ay, notlar, durum, olusturma_tarihi)
                VALUES (%s, %s, %s, %s, %s, 'aktif', CURRENT_TIMESTAMP)
                """
                cursor.execute(insert_query, (username, kat_sayisi or 1, year, month, notlar))
            
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
    def get_target_proxy(self, username):
        """Hedef hesabın proxy bilgilerini getir"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor()
            query = "SELECT proxy_ip, proxy_port FROM hedef_hesaplar WHERE kullanici_adi = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            
            if result and result[0]:
                return f"http://{result[0]}:{result[1]}" if result[1] else result[0]
            return None
        except Error as e:
            logger.error(f"❌ Hedef hesap proxy getirme hatası: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def import_targets_from_file(self, file_path):
        """Dosyadan hedef hesapları içe aktar - Format: kullaniciadi:katsayisi"""
        try:
            imported_count = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(':')
                    username = parts[0].strip()
                    kat_sayisi = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else 1
                    
                    if self.add_target(username, kat_sayisi):
                        imported_count += 1
            
            return imported_count
        except Exception as e:
            logger.error(f"❌ Dosyadan içe aktarma hatası: {e}")
            return 0
    
    @handle_exception
    def add_default_categories(self):
        """Varsayılan profil kategorilerini ekle"""
        connection = self.get_connection()
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            
            # Varsayılan kategoriler
            default_categories = [
                # Profil kategorileri
                ('profil', 'Yaş Grubu', None, 'Yaş grubu kategorisi'),
                ('profil', 'Cinsiyet', None, 'Cinsiyet kategorisi'),
                ('profil', 'Profil Fotoğrafı', None, 'Profil fotoğrafı kategorisi'),
                ('profil', 'Fotoğraf İçeriği', None, 'Fotoğraf içeriği kategorisi'),
                # İçerik kategorileri
                ('icerik', 'İçerik Türü', None, 'İçerik türü kategorisi'),
            ]
            
            # Her kategoriyi kontrol et ve yoksa ekle
            for kategori_turu, ana_kategori, alt_kategori, aciklama in default_categories:
                check_query = """
                SELECT id FROM profil_kategorileri 
                WHERE kategori_turu = %s AND ana_kategori = %s AND alt_kategori = %s
                """
                cursor.execute(check_query, (kategori_turu, ana_kategori, alt_kategori))
                
                if not cursor.fetchone():
                    insert_query = """
                    INSERT INTO profil_kategorileri (kategori_turu, ana_kategori, alt_kategori, aciklama)
                    VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (kategori_turu, ana_kategori, alt_kategori, aciklama))
            
            connection.commit()
            
        except Error as e:
            logger.error(f"❌ Varsayılan kategori ekleme hatası: {e}")
            connection.rollback()
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def get_categories(self, kategori_turu=None):
        """Kategorileri getir"""
        connection = self.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            if kategori_turu:
                query = """
                SELECT * FROM profil_kategorileri 
                WHERE kategori_turu = %s 
                ORDER BY ana_kategori, alt_kategori
                """
                cursor.execute(query, (kategori_turu,))
            else:
                query = """
                SELECT * FROM profil_kategorileri 
                ORDER BY kategori_turu, ana_kategori, alt_kategori
                """
                cursor.execute(query)
            
            return cursor.fetchall()
        except Error as e:
            logger.error(f"❌ Kategori getirme hatası: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def add_category(self, kategori_turu, ana_kategori, alt_kategori=None, aciklama=None):
        """Yeni kategori ekle"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Var olup olmadığını kontrol et
            check_query = """
            SELECT id FROM profil_kategorileri 
            WHERE kategori_turu = %s AND ana_kategori = %s AND alt_kategori = %s
            """
            cursor.execute(check_query, (kategori_turu, ana_kategori, alt_kategori))
            
            if cursor.fetchone():
                return False  # Zaten var
            
            # Ekle
            insert_query = """
            INSERT INTO profil_kategorileri (kategori_turu, ana_kategori, alt_kategori, aciklama)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (kategori_turu, ana_kategori, alt_kategori, aciklama))
            connection.commit()
            
            return True
        except Error as e:
            logger.error(f"❌ Kategori ekleme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def delete_account_categories(self, kullanici_adi, hesap_turu):
        """Hesabın tüm kategorilerini sil"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            delete_query = """
            DELETE FROM hesap_kategorileri 
            WHERE kullanici_adi = %s AND hesap_turu = %s
            """
            cursor.execute(delete_query, (kullanici_adi, hesap_turu))
            connection.commit()
            
            return True
        except Error as e:
            logger.error(f"❌ Hesap kategorileri silme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def assign_category_to_account(self, kullanici_adi, hesap_turu, kategori_id, kategori_degeri):
        """Hesaba kategori ata"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Var olan atamayı kontrol et
            check_query = """
            SELECT id FROM hesap_kategorileri 
            WHERE kullanici_adi = %s AND hesap_turu = %s AND kategori_id = %s
            """
            cursor.execute(check_query, (kullanici_adi, hesap_turu, kategori_id))
            existing = cursor.fetchone()
            
            if existing:
                # Güncelle
                update_query = """
                UPDATE hesap_kategorileri 
                SET kategori_degeri = %s, guncelleme_tarihi = CURRENT_TIMESTAMP
                WHERE id = %s
                """
                cursor.execute(update_query, (kategori_degeri, existing[0]))
            else:
                # Yeni ekle
                insert_query = """
                INSERT INTO hesap_kategorileri (kullanici_adi, hesap_turu, kategori_id, kategori_degeri)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_query, (kullanici_adi, hesap_turu, kategori_id, kategori_degeri))
            
            connection.commit()
            return True
        except Error as e:
            logger.error(f"❌ Kategori atama hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def get_account_categories(self, kullanici_adi, hesap_turu):
        """Hesabın kategorilerini getir"""
        connection = self.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT hk.*, pk.ana_kategori, pk.alt_kategori, pk.aciklama
            FROM hesap_kategorileri hk
            JOIN profil_kategorileri pk ON hk.kategori_id = pk.id
            WHERE hk.kullanici_adi = %s AND hk.hesap_turu = %s
            ORDER BY pk.ana_kategori, pk.alt_kategori
            """
            cursor.execute(query, (kullanici_adi, hesap_turu))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"❌ Hesap kategori getirme hatası: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @handle_exception
    def import_categories_from_file(self, file_path):
        """Dosyadan kategorileri içe aktar - Format: kategori_turu:ana_kategori:alt_kategori:aciklama"""
        try:
            imported_count = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(':')
                    if len(parts) >= 3:
                        kategori_turu = parts[0].strip()
                        ana_kategori = parts[1].strip()
                        alt_kategori = parts[2].strip() if parts[2].strip() else None
                        aciklama = parts[3].strip() if len(parts) > 3 else None
                        
                        if self.add_category(kategori_turu, ana_kategori, alt_kategori, aciklama):
                            imported_count += 1
            
            return imported_count
        except Exception as e:
            logger.error(f"❌ Kategori dosya içe aktarma hatası: {e}")
            return 0
    
    @handle_exception
    def import_account_categories_from_file(self, file_path, hesap_turu):
        """Dosyadan hesap kategorilerini içe aktar - Format: kullanici_adi:ana_kategori:alt_kategori:deger"""
        try:
            imported_count = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(':')
                    if len(parts) >= 4:
                        kullanici_adi = parts[0].strip()
                        ana_kategori = parts[1].strip()
                        alt_kategori = parts[2].strip()
                        kategori_degeri = parts[3].strip()
                        
                        # Kategori ID'sini bul
                        connection = self.get_connection()
                        if connection:
                            try:
                                cursor = connection.cursor()
                                query = """
                                SELECT id FROM profil_kategorileri 
                                WHERE ana_kategori = %s AND alt_kategori = %s
                                """
                                cursor.execute(query, (ana_kategori, alt_kategori))
                                result = cursor.fetchone()
                                
                                if result:
                                    kategori_id = result[0]
                                    if self.assign_category_to_account(kullanici_adi, hesap_turu, kategori_id, kategori_degeri):
                                        imported_count += 1
                            finally:
                                if connection.is_connected():
                                    cursor.close()
                                    connection.close()
            
            return imported_count
        except Exception as e:
            logger.error(f"❌ Hesap kategori dosya içe aktarma hatası: {e}")
            return 0

# Global MySQL manager instance
mysql_manager = MySQLManager()
