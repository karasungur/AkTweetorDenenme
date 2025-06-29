# AkTweetor - Twitter Otomasyon Aracı

🐦 **Modern ve güvenli Twitter hesap yönetimi ve otomasyon aracı**

## 🚀 Özellikler

### 🔐 Hesap Yönetimi

- ✅ Otomatik Twitter giriş işlemleri
- 🔄 Profil bazlı oturum kaydetme
- 🌐 Proxy desteği (HTTP/HTTPS)
- 📊 MySQL veritabanı entegrasyonu
- 🛡️ Güvenli çerez yönetimi

### 🖥️ Gelişmiş Arayüz

- 🎨 Modern PyQt5 tabanlı desktop arayüz
- 📱 Responsive ve kullanıcı dostu tasarım
- 🌈 Özelleştirilebilir tema sistemi
- 📝 Detaylı işlem logları
- 🔍 Gelişmiş profil arama ve filtreleme

### 🌐 IP Yönetimi

- 🖥️ **Normal IP**: Bilgisayarın dış IP adresi
- 🌍 **Tarayıcı IP**: Proxy sonrası taray��cı IP'si
- 🔄 Otomatik IP değiştirme desteği
- ⚡ Optimize edilmiş IP kontrolü (sürekli değil, ihtiyaç bazlı)

### 🔧 Teknik Özellikler

- 🧩 **Modüler mimari** - Services katmanı ile ayrışmış kod
- 🚀 **Performans optimize** - Thread-safe işlemler
- 🛡️ **Anti-detection** - Gelişmiş bot algılama koruması
- 🔄 **Process management** - Zombie process temizleme
- 💾 **Kalıcı profiller** - Uzantı ve ayarları koruma

## 📁 Proje Yapısı

```
AkTweetor/
├── main.py                    # Ana uygulama giriş noktası
├── requirements.txt           # Python bağımlılıkları
├── chromedriver.exe          # Chrome WebDriver
├──
├── ui/                       # Kullanıcı arayüzü
│   ├── main_window.py        # Ana pencere
│   ├── login_window.py       # Giriş yapıcı
│   └── validation_window.py  # Giriş doğrulama
├──
├── services/                 # İş mantığı servisleri
│   ├── ip_service.py         # IP yönetimi
│   └── driver_manager.py     # Chrome driver yönetimi
├──
├── database/                 # Veritabanı katmanı
│   ├── mysql_config.py       # MySQL yapılandırması
│   └── user_manager.py       # Kullanıcı CRUD işlemleri
├──
├── Profiller/               # Kalıcı kullanıcı profilleri
└── TempProfiller/           # Geçici işlem profilleri
```

## 🛠️ Kurulum

### 1. Sistem Gereksinimleri

- **Python 3.11+**
- **Chrome Browser** (güncel sürüm)
- **MySQL Server** (isteğe bağlı)
- **Windows 10/11** (önerilen)

### 2. Kurulum Adımları

```bash
# 1. Projeyi klonlayın
git clone https://github.com/yourusername/AkTweetor.git
cd AkTweetor

# 2. Virtual environment oluşturun
python -m venv venv

# 3. Virtual environment'ı aktive edin
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 5. ChromeDriver'ı indirin
# https://chromedriver.chromium.org/ adresinden
# Chrome sürümünüze uygun driver'ı indirip proje klasörüne koyun

# 6. Uygulamayı başlatın
python main.py
```

### 3. MySQL Kurulumu (İsteğe Bağlı)

```sql
-- Veritabanı oluştur
CREATE DATABASE aktweetor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Kullanıcı oluştur (isteğe bağlı)
CREATE USER 'aktweetor'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON aktweetor.* TO 'aktweetor'@'localhost';
FLUSH PRIVILEGES;
```

## 📋 Kullanım

### 🔐 Giriş Yapıcı

1. **Liste Yükle**: `username:password` formatında kullanıcı listesi seçin
2. **Proxy Ayarları**: İsteğe bağlı proxy yapılandırması
3. **Tarayıcı Ayarları**: Görünür/görünmez mod seçimi
4. **Başlat**: Otomatik giriş işlemini başlatın

### 🔍 Giriş Doğrulama

1. **Profil Listesi**: Kayıtlı profilleri görüntüleyin
2. **Tarayıcı Aç**: Profil ile otomatik giriş
3. **Profil Yönetimi**: Seçili profilleri toplu silme
4. **IP Kontrolü**: Anlık IP durumu takibi

## 🔧 Yapılandırma

### 📁 Dosya Formatları

**Kullanıcı Listesi (`users.txt`):**

```
username1:password1
username2:password2
username3:password3:proxy_ip:proxy_port
```

### 🌐 Proxy Ayarları

- **HTTP/HTTPS Proxy**: `ip:port` formatında
- **Kullanıcı bazlı proxy**: Liste dosyasında belirtilen proxy öncelikli
- **IP Reset URL**: Proxy IP değiştirme için özel URL

## 🛡️ Güvenlik

- 🔒 **Çerez şifreleme**: Hassas veriler güvenli şekilde saklanır
- 🚫 **Anti-detection**: Bot algılama sistemlerini bypass
- 🧹 **Process temizleme**: Zombie process'leri otomatik temizler
- 💾 **Güvenli profil yönetimi**: Tarayıcı ayarları kalıcı olarak korunur

## 🐛 Sorun Giderme

### Yaygın Sorunlar

**ChromeDriver Hatası:**

```
✅ Chrome sürümünüzü kontrol edin: chrome://version
✅ Uyumlu ChromeDriver indirin
✅ chromedriver.exe dosyasını proje klasörüne koyun
```

**IP Alınamıyor:**

```
✅ İnternet bağlantınızı kontrol edin
✅ Firewall ayarlarını kontrol edin
✅ Proxy ayarlarını doğrulayın
```

**MySQL Bağlantı Hatası:**

```
✅ MySQL servisi çalışıyor mu kontrol edin
✅ database/mysql_config.py dosyasındaki ayarları kontrol edin
✅ Kullanıcı izinlerini kontrol edin
```

## 📈 Performans

- ⚡ **H��zlı başlatma**: ~3-5 saniye
- 💾 **Düşük bellek kullanımı**: ~50-100MB
- 🔄 **Eşzamanlı işlem**: Çoklu kullanıcı desteği
- 🧹 **Otomatik temizlik**: Geçici dosya yönetimi

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## ⚠️ Yasal Uyarı

Bu araç eğitim ve araştırma amaçlıdır. Twitter'ın kullanım şartlarına uygun şekilde kullanın. Herhangi bir kötüye kullanımdan geliştirici sorumlu değildir.

## 📞 İletişim

- 📧 Email: your-email@domain.com
- 🐦 Twitter: @yourusername
- 💼 LinkedIn: yourprofile

---

⭐ **Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!**
