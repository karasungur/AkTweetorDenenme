
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

class MySQLManager:
    def __init__(self):
        # MySQL bağlantı bilgileri
        self.host = 'localhost'
        self.database = 'aktweetor'
        self.username = 'root'
        self.password = ''
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
                collation='utf8mb4_unicode_ci',
                autocommit=False
            )
            print("✅ MySQL bağlantı havuzu oluşturuldu")
            
            # Eski tabloları temizle ve yeni yapıyı oluştur
            self.cleanup_old_tables()
            self.create_new_tables()
            
        except Error as e:
            print(f"❌ MySQL bağlantı havuzu hatası: {e}")
            self.connection_pool = None
    
    def get_connection(self):
        """Bağlantı havuzundan bağlantı al"""
        try:
            if self.connection_pool:
                connection = self.connection_pool.get_connection()
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
                return connection
        except Error as e:
            print(f"❌ MySQL bağlantı hatası: {e}")
            return None
    
    def cleanup_old_tables(self):
        """Eski tabloları temizle"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Eski tabloları listele ve sil
            old_tables = [
                'hesap_kategorileri',
                'kullanici_kategorileri', 
                'islem_logları',
                'sistem_ayarları'
            ]
            
            for table in old_tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    print(f"🗑️ Eski tablo silindi: {table}")
                except Error:
                    pass
            
            connection.commit()
            print("✅ Eski tablolar temizlendi")
            
        except Error as e:
            print(f"❌ Eski tablo temizleme hatası: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def create_new_tables(self):
        """Yeni tablo yapısını oluştur"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # kullanicilar tablosu - giriş yapılan hesaplar
            create_users_table = """
            CREATE TABLE IF NOT EXISTS kullanicilar (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kullanici_adi VARCHAR(255) NOT NULL UNIQUE,
                sifre VARCHAR(255) NOT NULL,
                yil INT NULL,
                ay INT NULL,
                proxy_ip VARCHAR(45) NULL,
                proxy_port INT NULL,
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
                son_ip VARCHAR(45),
                notlar TEXT,
                INDEX idx_kullanici_adi (kullanici_adi),
                INDEX idx_durum (durum),
                INDEX idx_son_giris (son_giris)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_users_table)
            
            # hedef_hesaplar tablosu - sadece hedef hesaplar
            create_targets_table = """
            CREATE TABLE IF NOT EXISTS hedef_hesaplar (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kullanici_adi VARCHAR(255) NOT NULL UNIQUE,
                yil INT NULL,
                ay INT NULL,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                durum ENUM('aktif', 'pasif') DEFAULT 'aktif',
                notlar TEXT NULL,
                INDEX idx_kullanici_adi (kullanici_adi),
                INDEX idx_yil_ay (yil, ay),
                INDEX idx_durum (durum)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_targets_table)
            
            connection.commit()
            print("✅ Yeni tablo yapısı oluşturuldu")
            return True
            
        except Error as e:
            print(f"❌ Tablo oluşturma hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    # KULLANICILAR TABLOSU İŞLEMLERİ
    def save_user(self, username, password, cookies=None, year=None, month=None, proxy_ip=None, proxy_port=None):
        """Kullanıcıyı veritabanına kaydet"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Önce kullanıcı var mı kontrol et
            check_query = "SELECT id FROM kullanicilar WHERE kullanici_adi = %s"
            cursor.execute(check_query, (username,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Kullanıcı varsa güncelle
                return self.update_user(username, password, cookies, year, month, proxy_ip, proxy_port)
            else:
                # Yeni kullanıcı ekle
                insert_query = """
                INSERT INTO kullanicilar (
                    kullanici_adi, sifre, yil, ay, proxy_ip, proxy_port,
                    auth_token, gt, guest_id, twid, lang, __cf_bm, att, ct0, 
                    d_prefs, dnt, guest_id_ads, guest_id_marketing, kdt, 
                    personalization_id, son_giris
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                # Çerez değerlerini hazırla
                cookie_values = self.prepare_cookie_values(cookies) if cookies else {}
                
                values = (
                    username, password, year, month, proxy_ip, proxy_port,
                    cookie_values.get('auth_token'),
                    cookie_values.get('gt'),
                    cookie_values.get('guest_id'),
                    cookie_values.get('twid'),
                    cookie_values.get('lang'),
                    cookie_values.get('__cf_bm'),
                    cookie_values.get('att'),
                    cookie_values.get('ct0'),
                    cookie_values.get('d_prefs'),
                    cookie_values.get('dnt'),
                    cookie_values.get('guest_id_ads'),
                    cookie_values.get('guest_id_marketing'),
                    cookie_values.get('kdt'),
                    cookie_values.get('personalization_id'),
                    datetime.now()
                )
                
                cursor.execute(insert_query, values)
                connection.commit()
                
                print(f"✅ Kullanıcı kaydedildi: {username}")
                return True
                
        except Error as e:
            print(f"❌ Kullanıcı kaydetme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def update_user(self, username, password=None, cookies=None, year=None, month=None, proxy_ip=None, proxy_port=None):
        """Mevcut kullanıcıyı güncelle"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Güncelleme sorgusu hazırla
            update_parts = []
            values = []
            
            if password:
                update_parts.append("sifre = %s")
                values.append(password)
            
            if year is not None:
                update_parts.append("yil = %s")
                values.append(year)
            
            if month is not None:
                update_parts.append("ay = %s")
                values.append(month)
            
            if proxy_ip is not None:
                update_parts.append("proxy_ip = %s")
                values.append(proxy_ip)
            
            if proxy_port is not None:
                update_parts.append("proxy_port = %s")
                values.append(proxy_port)
            
            if cookies:
                cookie_values = self.prepare_cookie_values(cookies)
                cookie_fields = [
                    'auth_token', 'gt', 'guest_id', 'twid', 'lang', '__cf_bm',
                    'att', 'ct0', 'd_prefs', 'dnt', 'guest_id_ads', 
                    'guest_id_marketing', 'kdt', 'personalization_id'
                ]
                
                for field in cookie_fields:
                    if field in cookie_values and cookie_values[field]:
                        update_parts.append(f"{field} = %s")
                        values.append(cookie_values[field])
            
            # Son giriş zamanını güncelle
            update_parts.append("son_giris = %s")
            values.append(datetime.now())
            
            if update_parts:
                update_query = f"""
                UPDATE kullanicilar 
                SET {', '.join(update_parts)}
                WHERE kullanici_adi = %s
                """
                values.append(username)
                
                cursor.execute(update_query, values)
                connection.commit()
                
                print(f"✅ Kullanıcı güncellendi: {username}")
                return True
            
        except Error as e:
            print(f"❌ Kullanıcı güncelleme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
        
        return False
    
    def get_user(self, username):
        """Kullanıcı bilgilerini getir"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM kullanicilar WHERE kullanici_adi = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            return user
            
        except Error as e:
            print(f"❌ Kullanıcı getirme hatası: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_all_users(self, status=None):
        """Tüm kullanıcıları getir"""
        connection = self.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            if status:
                query = "SELECT * FROM kullanicilar WHERE durum = %s ORDER BY olusturma_tarihi DESC"
                cursor.execute(query, (status,))
            else:
                query = "SELECT * FROM kullanicilar ORDER BY olusturma_tarihi DESC"
                cursor.execute(query)
            
            users = cursor.fetchall()
            return users
            
        except Error as e:
            print(f"❌ Kullanıcı listesi getirme hatası: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def delete_user(self, username):
        """Kullanıcıyı sil"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            query = "DELETE FROM kullanicilar WHERE kullanici_adi = %s"
            cursor.execute(query, (username,))
            connection.commit()
            
            if cursor.rowcount > 0:
                print(f"✅ Kullanıcı silindi: {username}")
                return True
            else:
                print(f"⚠️ Kullanıcı bulunamadı: {username}")
                return False
                
        except Error as e:
            print(f"❌ Kullanıcı silme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def import_users_from_file(self, file_path):
        """Dosyadan kullanıcıları içe aktar"""
        try:
            imported_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            for line in lines:
                line = line.strip()
                if line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        username = parts[0]
                        password = parts[1]
                        year = None
                        month = None
                        proxy_ip = None
                        proxy_port = None
                        
                        # Opsiyonel alanları kontrol et
                        if len(parts) >= 4:
                            try:
                                year = int(parts[2]) if parts[2] else None
                                month = int(parts[3]) if parts[3] else None
                            except ValueError:
                                pass
                        
                        if len(parts) >= 6:
                            proxy_ip = parts[4] if parts[4] else None
                            try:
                                proxy_port = int(parts[5]) if parts[5] else None
                            except ValueError:
                                pass
                        
                        if self.save_user(username, password, None, year, month, proxy_ip, proxy_port):
                            imported_count += 1
            
            return imported_count
            
        except Exception as e:
            print(f"❌ Dosya içe aktarma hatası: {e}")
            return 0
    
    # HEDEF HESAPLAR TABLOSU İŞLEMLERİ
    def add_target(self, username, year=None, month=None, notes=None):
        """Hedef hesap ekle"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Önce var mı kontrol et
            check_query = "SELECT id FROM hedef_hesaplar WHERE kullanici_adi = %s"
            cursor.execute(check_query, (username,))
            existing = cursor.fetchone()
            
            if existing:
                # Güncelle
                update_query = """
                UPDATE hedef_hesaplar 
                SET yil = %s, ay = %s, notlar = %s, guncelleme_tarihi = %s
                WHERE kullanici_adi = %s
                """
                cursor.execute(update_query, (year, month, notes, datetime.now(), username))
                print(f"✅ Hedef hesap güncellendi: {username}")
            else:
                # Yeni ekle
                insert_query = """
                INSERT INTO hedef_hesaplar (kullanici_adi, yil, ay, notlar)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_query, (username, year, month, notes))
                print(f"✅ Hedef hesap eklendi: {username}")
            
            connection.commit()
            return True
            
        except Error as e:
            print(f"❌ Hedef hesap ekleme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_all_targets(self, status=None):
        """Tüm hedef hesapları getir"""
        connection = self.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            if status:
                query = "SELECT * FROM hedef_hesaplar WHERE durum = %s ORDER BY olusturma_tarihi DESC"
                cursor.execute(query, (status,))
            else:
                query = "SELECT * FROM hedef_hesaplar ORDER BY olusturma_tarihi DESC"
                cursor.execute(query)
            
            targets = cursor.fetchall()
            return targets
            
        except Error as e:
            print(f"❌ Hedef hesap listesi getirme hatası: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
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
            
            if cursor.rowcount > 0:
                print(f"✅ Hedef hesap silindi: {username}")
                return True
            else:
                print(f"⚠️ Hedef hesap bulunamadı: {username}")
                return False
                
        except Error as e:
            print(f"❌ Hedef hesap silme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def import_targets_from_file(self, file_path):
        """Dosyadan hedef hesapları içe aktar"""
        try:
            imported_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            for line in lines:
                line = line.strip()
                if line:
                    parts = line.split(':')
                    username = parts[0]
                    year = None
                    month = None
                    
                    if len(parts) >= 3:
                        try:
                            year = int(parts[1]) if parts[1] else None
                            month = int(parts[2]) if parts[2] else None
                        except ValueError:
                            pass
                    
                    if self.add_target(username, year, month):
                        imported_count += 1
            
            return imported_count
            
        except Exception as e:
            print(f"❌ Dosya içe aktarma hatası: {e}")
            return 0
    
    # YARDIMCI METODLAR
    def prepare_cookie_values(self, cookies):
        """Çerez değerlerini hazırla"""
        cookie_values = {}
        
        # Çerez listesi
        cookie_names = [
            'auth_token', 'gt', 'guest_id', 'twid', 'lang', '__cf_bm',
            'att', 'ct0', 'd_prefs', 'dnt', 'guest_id_ads', 
            'guest_id_marketing', 'kdt', 'personalization_id'
        ]
        
        if isinstance(cookies, dict):
            # Dict formatında çerezler
            for cookie_name in cookie_names:
                cookie_values[cookie_name] = cookies.get(cookie_name)
        elif isinstance(cookies, list):
            # Selenium cookie formatında
            for cookie in cookies:
                if cookie['name'] in cookie_names:
                    cookie_values[cookie['name']] = cookie['value']
        
        return cookie_values
    
    def get_user_stats(self):
        """Kullanıcı istatistiklerini getir"""
        connection = self.get_connection()
        if not connection:
            return {}
        
        try:
            cursor = connection.cursor()
            
            stats = {}
            
            # Toplam kullanıcı sayısı
            cursor.execute("SELECT COUNT(*) FROM kullanicilar")
            stats['toplam_kullanici'] = cursor.fetchone()[0]
            
            # Aktif kullanıcı sayısı
            cursor.execute("SELECT COUNT(*) FROM kullanicilar WHERE durum = 'aktif'")
            stats['aktif_kullanici'] = cursor.fetchone()[0]
            
            # Proxy'li kullanıcı sayısı
            cursor.execute("SELECT COUNT(*) FROM kullanicilar WHERE proxy_ip IS NOT NULL")
            stats['proxyli_kullanici'] = cursor.fetchone()[0]
            
            return stats
            
        except Error as e:
            print(f"❌ İstatistik getirme hatası: {e}")
            return {}
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_target_stats(self):
        """Hedef hesap istatistiklerini getir"""
        connection = self.get_connection()
        if not connection:
            return {}
        
        try:
            cursor = connection.cursor()
            
            stats = {}
            
            # Toplam hedef hesap sayısı
            cursor.execute("SELECT COUNT(*) FROM hedef_hesaplar")
            stats['toplam_hedef'] = cursor.fetchone()[0]
            
            # Aktif hedef hesap sayısı
            cursor.execute("SELECT COUNT(*) FROM hedef_hesaplar WHERE durum = 'aktif'")
            stats['aktif_hedef'] = cursor.fetchone()[0]
            
            # Tarihli hedef hesap sayısı
            cursor.execute("SELECT COUNT(*) FROM hedef_hesaplar WHERE yil IS NOT NULL AND ay IS NOT NULL")
            stats['tarihli_hedef'] = cursor.fetchone()[0]
            
            return stats
            
        except Error as e:
            print(f"❌ İstatistik getirme hatası: {e}")
            return {}
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

# Global MySQL yöneticisi
mysql_manager = MySQLManager()
