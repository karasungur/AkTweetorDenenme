from database.mysql_config import mysql_config
from mysql.connector import Error
from datetime import datetime

class UserManager:
    def __init__(self):
        self.mysql_config = mysql_config
    
    def save_user(self, username, password, cookies=None):
        """Kullanıcıyı veritabanına kaydet"""
        connection = self.mysql_config.get_connection()
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
                return self.update_user(username, password, cookies)
            else:
                # Yeni kullanıcı ekle
                insert_query = """
                INSERT INTO kullanicilar (
                    kullanici_adi, sifre, auth_token, gt, guest_id, twid, lang,
                    __cf_bm, att, ct0, d_prefs, dnt, guest_id_ads, 
                    guest_id_marketing, kdt, personalization_id, son_giris
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                # Çerez değerlerini hazırla
                cookie_values = self.prepare_cookie_values(cookies) if cookies else {}
                
                values = (
                    username,
                    password,
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
                
                # İşlem logunu kaydet
                self.log_operation(cursor.lastrowid, 'giris', f'Kullanıcı başarıyla giriş yaptı', 'basarili')
                
                return True
                
        except Error as e:
            print(f"❌ Kullanıcı kaydetme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def update_user(self, username, password=None, cookies=None):
        """Mevcut kullanıcıyı güncelle"""
        connection = self.mysql_config.get_connection()
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
                
                # Kullanıcı ID'sini al ve log kaydet
                cursor.execute("SELECT id FROM kullanicilar WHERE kullanici_adi = %s", (username,))
                user_id = cursor.fetchone()[0]
                self.log_operation(user_id, 'giris', f'Kullanıcı bilgileri güncellendi', 'basarili')
                
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
    
    def get_user(self, username):
        """Kullanıcı bilgilerini getir"""
        connection = self.mysql_config.get_connection()
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
        connection = self.mysql_config.get_connection()
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
        connection = self.mysql_config.get_connection()
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
    
    def log_operation(self, user_id, operation_type, details, status='basarili', error_message=None):
        """İşlem logunu kaydet"""
        connection = self.mysql_config.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            query = """
            INSERT INTO islem_logları (kullanici_id, islem_tipi, islem_detayi, durum, hata_mesaji)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, operation_type, details, status, error_message))
            connection.commit()
            return True
            
        except Error as e:
            print(f"❌ Log kaydetme hatası: {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_user_stats(self):
        """Kullanıcı istatistiklerini getir"""
        connection = self.mysql_config.get_connection()
        if not connection:
            return {}
        
        try:
            cursor = connection.cursor()
            
            stats = {}
            
            # Toplam kullanıcı sayısı
            cursor.execute("SELECT COUNT(*) FROM kullanicilar")
            stats['toplam'] = cursor.fetchone()[0]
            
            # Aktif kullanıcı sayısı
            cursor.execute("SELECT COUNT(*) FROM kullanicilar WHERE durum = 'aktif'")
            stats['aktif'] = cursor.fetchone()[0]
            
            # Bugün giriş yapan kullanıcı sayısı
            cursor.execute("SELECT COUNT(*) FROM kullanicilar WHERE DATE(son_giris) = CURDATE()")
            stats['bugun_giris'] = cursor.fetchone()[0]
            
            # Çerezi olan kullanıcı sayısı
            cursor.execute("SELECT COUNT(*) FROM kullanicilar WHERE auth_token IS NOT NULL")
            stats['cerezli'] = cursor.fetchone()[0]
            
            return stats
            
        except Error as e:
            print(f"❌ İstatistik getirme hatası: {e}")
            return {}
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

# Global user manager
user_manager = UserManager()
