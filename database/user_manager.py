from database.mysql import mysql_manager
from mysql.connector import Error
from datetime import datetime
import mysql.connector

class UserManager:
    def __init__(self):
        self.mysql_manager = mysql_manager

    def get_connection(self):
        """MySQL bağlantısı al"""
        return self.mysql_manager.get_connection()

    def save_user(self, username, password, cookie_dict=None, year=None, month=None, proxy_ip=None, proxy_port=None, user_agent=None):
        """Kullanıcıyı veritabanına kaydet"""
        connection = self.get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()

            # Kullanıcının var olup olmadığını kontrol et
            check_query = "SELECT id FROM kullanicilar WHERE kullanici_adi = %s"
            cursor.execute(check_query, (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                # Kullanıcı var, güncelle
                update_parts = ["sifre = %s", "proxy_ip = %s", "proxy_port = %s", "user_agent = %s", "guncelleme_tarihi = CURRENT_TIMESTAMP"]
                update_values = [password, proxy_ip, proxy_port, user_agent]
                
                if cookie_dict:
                    import json
                    update_parts.append("cerezler = %s")
                    update_values.append(json.dumps(cookie_dict))
                
                update_values.append(username)
                
                update_query = f"""
                UPDATE kullanicilar 
                SET {', '.join(update_parts)}
                WHERE kullanici_adi = %s
                """
                cursor.execute(update_query, update_values)
            else:
                # Yeni kullanıcı ekle
                insert_parts = ["kullanici_adi", "sifre", "proxy_ip", "proxy_port", "user_agent", "durum", "olusturma_tarihi"]
                insert_values = [username, password, proxy_ip, proxy_port, user_agent, 'aktif']
                insert_placeholders = ["%s", "%s", "%s", "%s", "%s", "%s", "CURRENT_TIMESTAMP"]
                
                if cookie_dict:
                    import json
                    insert_parts.append("cerezler")
                    insert_values.append(json.dumps(cookie_dict))
                    insert_placeholders.append("%s")
                
                insert_query = f"""
                INSERT INTO kullanicilar 
                ({', '.join(insert_parts)}) 
                VALUES ({', '.join(insert_placeholders)})
                """
                cursor.execute(insert_query, insert_values)

            connection.commit()
            return True

        except Error as e:
            print(f"❌ Kullanıcı kaydetme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_user(self, username):
        """Kullanıcı bilgilerini getir"""
        connection = self.get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM kullanicilar WHERE kullanici_adi = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            return result

        except Error as e:
            print(f"❌ Kullanıcı getirme hatası: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_all_users(self):
        """Tüm kullanıcıları getir"""
        connection = self.get_connection()
        if not connection:
            return []

        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM kullanicilar ORDER BY kullanici_adi"
            cursor.execute(query)
            results = cursor.fetchall()
            return results

        except Error as e:
            print(f"❌ Kullanıcılar getirme hatası: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_logged_in_users(self):
        """Giriş yapmış kullanıcıları getir"""
        connection = self.get_connection()
        if not connection:
            return []

        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT kullanici_adi FROM kullanicilar 
            WHERE durum = 'aktif' AND son_giris IS NOT NULL
            ORDER BY kullanici_adi
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return [user['kullanici_adi'] for user in results]

        except Error as e:
            print(f"❌ Giriş yapmış kullanıcılar getirme hatası: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def update_user(self, username, password=None, cookie_dict=None):
        """Kullanıcı bilgilerini güncelle"""
        connection = self.get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()

            # Güncelleme sorgusu oluştur
            updates = []
            values = []

            if password is not None:
                updates.append("sifre = %s")
                values.append(password)

            if cookie_dict:
                # Çerezleri JSON olarak kaydet
                import json
                updates.append("cerezler = %s")
                values.append(json.dumps(cookie_dict))

            # Son giriş zamanını güncelle
            updates.append("son_giris = CURRENT_TIMESTAMP")
            updates.append("guncelleme_tarihi = CURRENT_TIMESTAMP")

            if not updates:
                return True

            values.append(username)

            query = f"UPDATE kullanicilar SET {', '.join(updates)} WHERE kullanici_adi = %s"
            cursor.execute(query, values)
            connection.commit()

            return cursor.rowcount > 0

        except Error as e:
            print(f"❌ Kullanıcı güncelleme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_user_twitter_creation_date(self, username):
        """Kullanıcının Twitter oluşturma tarihini getir"""
        connection = self.get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor()
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
        """Kullanıcının Twitter oluşturma tarihini güncelle (DATETIME formatında)"""
        connection = self.get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()

            # DATETIME formatında kaydet (saat ve dakika ile birlikte)
            if isinstance(creation_date, str):
                # Eğer string formatında gelirse datetime'a çevir
                try:
                    # Çeşitli formatları dene
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
        """Kullanıcının proxy bilgilerini getir"""
        connection = self.get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor()
            query = "SELECT proxy_ip, proxy_port FROM kullanicilar WHERE kullanici_adi = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            if result and result[0]:
                return {
                    'ip': result[0],
                    'port': result[1]
                }
            return None

        except Error as e:
            print(f"❌ Kullanıcı proxy getirme hatası: {e}")
            return None
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

            return cursor.rowcount > 0

        except Error as e:
            print(f"❌ Kullanıcı silme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_user_cookies(self, username):
        """Kullanıcının çerezlerini getir"""
        connection = self.get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor()
            query = "SELECT cerezler FROM kullanicilar WHERE kullanici_adi = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            if result and result[0]:
                import json
                try:
                    return json.loads(result[0])
                except json.JSONDecodeError:
                    print(f"⚠️ {username} için çerez JSON formatı hatalı")
                    return None
            return None

        except Error as e:
            print(f"❌ Kullanıcı çerez getirme hatası: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def update_user_cookies(self, username, cookie_dict):
        """Kullanıcının çerezlerini güncelle"""
        connection = self.get_connection()
        if not connection:
            print(f"❌ {username} için MySQL bağlantısı alınamadı")
            return False

        try:
            cursor = connection.cursor()
            import json
            
            # Önce kullanıcının var olup olmadığını kontrol et
            check_query = "SELECT id FROM kullanicilar WHERE kullanici_adi = %s"
            cursor.execute(check_query, (username,))
            user_exists = cursor.fetchone()
            
            if not user_exists:
                print(f"❌ {username} kullanıcısı veritabanında bulunamadı")
                return False
            
            # Çerezleri JSON olarak hazırla
            cookies_json = json.dumps(cookie_dict)
            print(f"🔍 {username} için çerez JSON boyutu: {len(cookies_json)} karakter")
            
            # Çerezleri güncelle
            query = "UPDATE kullanicilar SET cerezler = %s, guncelleme_tarihi = CURRENT_TIMESTAMP WHERE kullanici_adi = %s"
            cursor.execute(query, (cookies_json, username))
            connection.commit()
            
            affected_rows = cursor.rowcount
            print(f"✅ {username} için {affected_rows} satır güncellendi")
            
            return affected_rows > 0

        except Error as e:
            print(f"❌ {username} çerez güncelleme hatası: {e}")
            connection.rollback()
            return False
        except Exception as e:
            print(f"❌ {username} beklenmeyen hata: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_user_agent(self, username):
        """Kullanıcının user-agent'ını getir"""
        connection = self.get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor()
            query = "SELECT user_agent FROM kullanicilar WHERE kullanici_adi = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            return result[0] if result and result[0] else None

        except Error as e:
            print(f"❌ Kullanıcı user-agent getirme hatası: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def update_user_agent(self, username, user_agent):
        """Kullanıcının user-agent'ını güncelle"""
        connection = self.get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()
            
            query = "UPDATE kullanicilar SET user_agent = %s WHERE kullanici_adi = %s"
            cursor.execute(query, (user_agent, username))
            connection.commit()

            return cursor.rowcount > 0

        except Error as e:
            print(f"❌ Kullanıcı user-agent güncelleme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def update_device_specs(self, username, device_info):
        """Kullanıcının cihaz özelliklerini güncelle"""
        connection = self.get_connection()
        if not connection:
            return False

        try:
            cursor = connection.cursor()
            
            # Cihaz özelliklerini JSON formatında kaydet
            import json
            device_specs = {
                'device_name': device_info['name'],
                'screen_width': device_info['device_metrics']['width'],
                'screen_height': device_info['device_metrics']['height'],
                'device_pixel_ratio': device_info['device_metrics']['device_scale_factor'],
                'user_agent': device_info['user_agent']
            }
            
            query = "UPDATE kullanicilar SET cihaz_ozellikleri = %s WHERE kullanici_adi = %s"
            cursor.execute(query, (json.dumps(device_specs), username))
            connection.commit()

            return cursor.rowcount > 0

        except Error as e:
            print(f"❌ Kullanıcı cihaz özellikleri güncelleme hatası: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_device_specs(self, username):
        """Kullanıcının cihaz özelliklerini getir"""
        connection = self.get_connection()
        if not connection:
            return None

        try:
            cursor = connection.cursor()
            query = "SELECT cihaz_ozellikleri FROM kullanicilar WHERE kullanici_adi = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            if result and result[0]:
                import json
                try:
                    return json.loads(result[0])
                except json.JSONDecodeError:
                    print(f"⚠️ {username} için cihaz özellikleri JSON formatı hatalı")
                    return None
            return None

        except Error as e:
            print(f"❌ Kullanıcı cihaz özellikleri getirme hatası: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

# Global user manager instance
user_manager = UserManager()