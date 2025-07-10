from database.mysql_config import mysql_config
from mysql.connector import Error
from datetime import datetime


class UserManager:
    def __init__(self):
        self.mysql_config = mysql_config

    def save_user(self, username, password, cookies=None, year=None, month=None, proxy_ip=None, proxy_port=None):
        """Kullanıcıyı veritabanına kaydet (year/month/proxy dinamik)"""
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
                # Kullanıcı varsa update_user çağır
                return self.update_user(username, password, cookies, year, month, proxy_ip, proxy_port)

            # Yeni kullanıcı ekleme için dinamik sütun & placeholder listeleri
            columns = [
                "kullanici_adi", "sifre",
                "auth_token", "gt", "guest_id", "twid", "lang",
                "__cf_bm", "att", "ct0", "d_prefs", "dnt",
                "guest_id_ads", "guest_id_marketing", "kdt", "personalization_id",
                "son_giris"
            ]
            placeholders = ["%s"] * len(columns)

            # Çerez değerlerini hazırla
            cookie_values = self.prepare_cookie_values(cookies) if cookies else {}
            values = [
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
            ]

            # year ve month ekle (varsa)
            if year is not None:
                columns.append("yil")
                placeholders.append("%s")
                values.append(year)
            if month is not None:
                columns.append("ay")
                placeholders.append("%s")
                values.append(month)

            # proxy bilgileri ekle (varsa)
            if proxy_ip is not None:
                columns.append("proxy_ip")
                placeholders.append("%s")
                values.append(proxy_ip)
            if proxy_port is not None:
                columns.append("proxy_port")
                placeholders.append("%s")
                values.append(proxy_port)

            insert_query = f"""
                INSERT INTO kullanicilar ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """
            cursor.execute(insert_query, tuple(values))
            connection.commit()

            print(f"✅ Kullanıcı kaydedildi: {username}")
            self.log_operation(cursor.lastrowid, 'giris', 'Kullanıcı başarıyla giriş yaptı', 'basarili')
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
        connection = self.mysql_config.get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()

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
                    val = cookie_values.get(field)
                    if val:
                        update_parts.append(f"{field} = %s")
                        values.append(val)

            # Son giriş zamanını her zaman güncelle
            update_parts.append("son_giris = %s")
            values.append(datetime.now())

            if not update_parts:
                return False  # güncellenecek alan yok

            update_query = f"""
                UPDATE kullanicilar
                SET {', '.join(update_parts)}
                WHERE kullanici_adi = %s
            """
            values.append(username)

            cursor.execute(update_query, tuple(values))
            connection.commit()

            print(f"✅ Kullanıcı güncellendi: {username}")
            cursor.execute("SELECT id FROM kullanicilar WHERE kullanici_adi = %s", (username,))
            user_id = cursor.fetchone()[0]
            self.log_operation(user_id, 'giris', 'Kullanıcı bilgileri güncellendi', 'basarili')
            return True

        except Error as e:
            print(f"❌ Kullanıcı güncelleme hatası: {e}")
            connection.rollback()
            return False

        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def prepare_cookie_values(self, cookies):
        """Çerez değerlerini hazırla"""
        cookie_values = {}
        cookie_names = [
            'auth_token', 'gt', 'guest_id', 'twid', 'lang', '__cf_bm',
            'att', 'ct0', 'd_prefs', 'dnt', 'guest_id_ads',
            'guest_id_marketing', 'kdt', 'personalization_id'
        ]
        if isinstance(cookies, dict):
            for name in cookie_names:
                cookie_values[name] = cookies.get(name)
        elif isinstance(cookies, list):
            for cookie in cookies:
                if cookie.get('name') in cookie_names:
                    cookie_values[cookie['name']] = cookie.get('value')
        return cookie_values

    def get_user(self, username):
        """Kullanıcı bilgilerini getir"""
        connection = self.mysql_config.get_connection()
        if not connection:
            return None
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM kullanicilar WHERE kullanici_adi = %s", (username,))
            return cursor.fetchone()
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
                cursor.execute(
                    "SELECT * FROM kullanicilar WHERE durum = %s ORDER BY olusturma_tarihi DESC",
                    (status,)
                )
            else:
                cursor.execute("SELECT * FROM kullanicilar ORDER BY olusturma_tarihi DESC")
            return cursor.fetchall()
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
            cursor.execute("DELETE FROM kullanicilar WHERE kullanici_adi = %s", (username,))
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
            cursor.execute(
                """
                INSERT INTO islem_logları
                  (kullanici_id, islem_tipi, islem_detayi, durum, hata_mesaji)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, operation_type, details, status, error_message)
            )
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
            cursor.execute("SELECT COUNT(*) FROM kullanicilar")
            stats['toplam'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM kullanicilar WHERE durum = 'aktif'")
            stats['aktif'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM kullanicilar WHERE DATE(son_giris) = CURDATE()")
            stats['bugun_giris'] = cursor.fetchone()[0]
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

    def get_user_cookies(self, username):
        """Kullanıcının çerezlerini getir"""
        connection = self.mysql_config.get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT auth_token, gt, guest_id, twid, lang, __cf_bm, att, ct0, 
                   d_prefs, dnt, guest_id_ads, guest_id_marketing, kdt, personalization_id
            FROM kullanicilar WHERE kullanici_adi = %s
            """
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            if result:
                # None değerleri temizle
                cookies = {k: v for k, v in result.items() if v is not None}
                return cookies

            return None

        except Error as e:
            print(f"❌ Çerez getirme hatası: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_user_creation_date(self, username):
        """Kullanıcının oluşturulma tarihini getir"""
        connection = self.mysql_config.get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor()
            query = "SELECT olusturma_tarihi FROM kullanicilar WHERE kullanici_adi = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            return result[0] if result and result[0] else None

        except Error as e:
            print(f"❌ Oluşturma tarihi getirme hatası: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def update_user_creation_date(self, username, creation_date):
        """Kullanıcının oluşturulma tarihini güncelle"""
        connection = self.mysql_config.get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()
            query = "UPDATE kullanicilar SET olusturma_tarihi = %s WHERE kullanici_adi = %s"
            cursor.execute(query, (creation_date, username))
            connection.commit()

            return cursor.rowcount > 0

        except Error as e:
            print(f"❌ Oluşturma tarihi güncelleme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def update_user_cookies(self, username, cookies):
        """Kullanıcının çerezlerini güncelle"""
        connection = self.mysql_config.get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()

            # Çerez değerlerini hazırla
            cookie_values = self.prepare_cookie_values(cookies)

            # Güncelleme sorgusu
            query = """
            UPDATE kullanicilar SET 
                auth_token = %s, gt = %s, guest_id = %s, twid = %s, lang = %s,
                __cf_bm = %s, att = %s, ct0 = %s, d_prefs = %s, dnt = %s,
                guest_id_ads = %s, guest_id_marketing = %s, kdt = %s, personalization_id = %s,
                son_giris = %s
            WHERE kullanici_adi = %s
            """

            values = [
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
                datetime.now(),
                username
            ]

            cursor.execute(query, values)
            connection.commit()

            return cursor.rowcount > 0

        except Error as e:
            print(f"❌ Çerez güncelleme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_user_twitter_creation_date(self, username):
        """Kullanıcının Twitter oluşturma tarihini getir"""
        connection = self.mysql_config.get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor()
            
            # Önce sütunun varlığını kontrol et
            cursor.execute("SHOW COLUMNS FROM kullanicilar LIKE 'twitter_olusturma_tarihi'")
            if not cursor.fetchone():
                return None
                
            query = "SELECT twitter_olusturma_tarihi FROM kullanicilar WHERE kullanici_adi = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            return result[0] if result and result[0] else None

        except Error as e:
            print(f"❌ Kullanıcı Twitter oluşturma tarihi getirme hatası: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def update_user_twitter_creation_date(self, username, creation_date):
        """Kullanıcının Twitter oluşturma tarihini güncelle"""
        connection = self.mysql_config.get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()
            
            # Önce sütunun varlığını kontrol et
            cursor.execute("SHOW COLUMNS FROM kullanicilar LIKE 'twitter_olusturma_tarihi'")
            if not cursor.fetchone():
                # Sütun yoksa ekle
                cursor.execute("ALTER TABLE kullanicilar ADD COLUMN twitter_olusturma_tarihi VARCHAR(50)")
                
            query = "UPDATE kullanicilar SET twitter_olusturma_tarihi = %s WHERE kullanici_adi = %s"
            cursor.execute(query, (creation_date, username))
            connection.commit()

            return cursor.rowcount > 0

        except Error as e:
            print(f"❌ Kullanıcı Twitter oluşturma tarihi güncelleme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_user_proxy(self, username):
        """Kullanıcının proxy bilgisini getir"""
        connection = self.mysql_config.get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor()
            
            # Önce sütunların varlığını kontrol et
            cursor.execute("SHOW COLUMNS FROM kullanicilar LIKE 'proxy_ip'")
            if not cursor.fetchone():
                return None
                
            query = "SELECT proxy_ip, proxy_port FROM kullanicilar WHERE kullanici_adi = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            if result and result[0]:
                proxy_ip, proxy_port = result
                return f"http://{proxy_ip}:{proxy_port}" if proxy_port else f"http://{proxy_ip}"

            return None

        except Error as e:
            print(f"❌ Kullanıcı proxy getirme hatası: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()


# Global user manager
user_manager = UserManager()