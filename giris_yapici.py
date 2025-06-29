import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import random
import requests
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class GirisYapici:
    def __init__(self, parent, colors, return_callback):
        self.parent = parent
        self.colors = colors
        self.return_callback = return_callback  # Ana menüye dönüş callback'i
        self.users = []
        self.current_ip = "Kontrol ediliyor..."
        self.ip_thread_running = True
        
        self.create_window()
        self.start_ip_monitoring()

    def create_window(self):
        """Giriş Yapıcı penceresini oluştur"""
        # Ana pencerede frame oluştur (Toplevel yerine)
        self.window_frame = tk.Frame(self.parent, bg=self.colors['background'])
        self.window_frame.pack(fill="both", expand=True)
        
        # Ana frame
        main_frame = tk.Frame(self.window_frame, bg=self.colors['background'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Üst kısım - Başlık ve Geri butonu
        header_frame = tk.Frame(main_frame, bg=self.colors['background'])
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Geri butonu (sol tarafta)
        back_btn = tk.Button(
            header_frame,
            text="← Ana Menüye Dön",
            command=self.return_to_main,
            font=("Arial", 12, "bold"),
            bg=self.colors['text_secondary'],
            fg="#FFFFFF",
            activebackground="#555555",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        )
        back_btn.pack(side="left")
        
        # Başlık (ortada)
        title_label = tk.Label(
            header_frame,
            text="📥 Giriş Yapıcı",
            font=("Arial", 20, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['background']
        )
        title_label.pack(side="left", expand=True)
        
        # Sol ve sağ paneller
        content_frame = tk.Frame(main_frame, bg=self.colors['background'])
        content_frame.pack(fill="both", expand=True)
        
        # Sol panel - Ayarlar
        left_frame = tk.Frame(content_frame, bg=self.colors['background_alt'], relief="ridge", bd=1)
        left_frame.pack(side="left", fill="y", padx=(0, 10), pady=5, ipadx=10, ipady=10)
        
        self.create_settings_panel(left_frame)
        
        # Sağ panel - Kullanıcı listesi ve loglar
        right_frame = tk.Frame(content_frame, bg=self.colors['background'])
        right_frame.pack(side="right", fill="both", expand=True)
        
        self.create_user_panel(right_frame)
        
        # Alt panel - IP ve kontroller
        bottom_frame = tk.Frame(main_frame, bg=self.colors['background'])
        bottom_frame.pack(fill="x", pady=(10, 0))
        
        self.create_bottom_panel(bottom_frame)

    def return_to_main(self):
        """Ana menüye dön"""
        self.ip_thread_running = False
        self.window_frame.destroy()
        self.return_callback()

    def create_settings_panel(self, parent):
        """Ayarlar panelini oluştur"""
        settings_label = tk.Label(
            parent,
            text="⚙️ Ayarlar",
            font=("Arial", 14, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['background_alt']
        )
        settings_label.pack(anchor="w", pady=(0, 15))
        
        # Proxy ayarları
        proxy_frame = tk.LabelFrame(
            parent,
            text="🌐 Proxy Ayarları",
            font=("Arial", 10, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['background_alt']
        )
        proxy_frame.pack(fill="x", pady=(0, 15))
        
        self.proxy_enabled = tk.BooleanVar()
        proxy_check = tk.Checkbutton(
            proxy_frame,
            text="Proxy Kullanılsın mı?",
            variable=self.proxy_enabled,
            font=("Arial", 9),
            fg=self.colors['text_primary'],
            bg=self.colors['background_alt'],
            command=self.toggle_proxy_fields
        )
        proxy_check.pack(anchor="w", padx=5, pady=5)
        
        tk.Label(
            proxy_frame,
            text="Proxy IP:Port:",
            font=("Arial", 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['background_alt']
        ).pack(anchor="w", padx=5)
        
        self.proxy_entry = tk.Entry(
            proxy_frame,
            font=("Arial", 9),
            state="disabled",
            width=25
        )
        self.proxy_entry.pack(fill="x", padx=5, pady=(0, 5))
        
        tk.Label(
            proxy_frame,
            text="IP Reset URL:",
            font=("Arial", 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['background_alt']
        ).pack(anchor="w", padx=5)
        
        self.reset_url_entry = tk.Entry(
            proxy_frame,
            font=("Arial", 9),
            state="disabled",
            width=25
        )
        self.reset_url_entry.pack(fill="x", padx=5, pady=(0, 5))
        
        # Tarayıcı ayarları
        browser_frame = tk.LabelFrame(
            parent,
            text="👀 Tarayıcı Ayarları",
            font=("Arial", 10, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['background_alt']
        )
        browser_frame.pack(fill="x", pady=(0, 15))
        
        self.browser_visible = tk.BooleanVar(value=True)
        browser_check = tk.Checkbutton(
            browser_frame,
            text="Tarayıcı Görünsün mü?",
            variable=self.browser_visible,
            font=("Arial", 9),
            fg=self.colors['text_primary'],
            bg=self.colors['background_alt']
        )
        browser_check.pack(anchor="w", padx=5, pady=5)
        
        # Başlat butonu
        start_btn = tk.Button(
            parent,
            text="🚀 Giriş İşlemini Başlat",
            command=self.start_login_process,
            font=("Arial", 12, "bold"),
            bg=self.colors['primary'],
            fg="#FFFFFF",
            activebackground=self.colors['primary_hover'],
            relief="flat",
            pady=10,
            cursor="hand2"
        )
        start_btn.pack(fill="x", pady=(10, 0))

    def create_user_panel(self, parent):
        """Kullanıcı panelini oluştur"""
        # Kullanıcı listesi
        user_frame = tk.LabelFrame(
            parent,
            text="📥 Kullanıcı Listesi",
            font=("Arial", 12, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['background']
        )
        user_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Liste yükle butonu
        load_btn = tk.Button(
            user_frame,
            text="📁 Liste Yükle",
            command=self.load_user_list,
            font=("Arial", 10),
            bg=self.colors['secondary'],
            fg="#FFFFFF",
            activebackground=self.colors['secondary_hover'],
            relief="flat",
            cursor="hand2"
        )
        load_btn.pack(pady=5)
        
        # Kullanıcı listesi
        list_frame = tk.Frame(user_frame, bg=self.colors['background'])
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.user_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Arial", 9),
            bg="#FFFFFF",
            selectbackground=self.colors['primary']
        )
        self.user_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.user_listbox.yview)
        
        # Log alanı
        log_frame = tk.LabelFrame(
            parent,
            text="📝 İşlem Logları",
            font=("Arial", 12, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['background']
        )
        log_frame.pack(fill="both", expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            font=("Consolas", 9),
            bg="#F8F8F8",
            fg=self.colors['text_primary']
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    def create_bottom_panel(self, parent):
        """Alt paneli oluştur"""
        # IP gösterimi
        ip_frame = tk.Frame(parent, bg=self.colors['background'])
        ip_frame.pack(fill="x")
        
        tk.Label(
            ip_frame,
            text="🌐 Şu anki IP:",
            font=("Arial", 10, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['background']
        ).pack(side="left")
        
        self.ip_label = tk.Label(
            ip_frame,
            text=self.current_ip,
            font=("Arial", 10),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        )
        self.ip_label.pack(side="left", padx=(10, 0))

    def toggle_proxy_fields(self):
        """Proxy alanlarını etkinleştir/devre dışı bırak"""
        state = "normal" if self.proxy_enabled.get() else "disabled"
        self.proxy_entry.config(state=state)
        self.reset_url_entry.config(state=state)

    def load_user_list(self):
        """Kullanıcı listesini yükle"""
        file_path = filedialog.askopenfilename(
            title="Kullanıcı Listesi Seç",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                
                self.users = []
                self.user_listbox.delete(0, tk.END)
                
                for line in lines:
                    line = line.strip()
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            username = parts[0]
                            password = parts[1]
                            proxy = None
                            proxy_port = None
                            
                            if len(parts) >= 4:
                                proxy = parts[2]
                                proxy_port = parts[3]
                            
                            user_data = {
                                'username': username,
                                'password': password,
                                'proxy': proxy,
                                'proxy_port': proxy_port,
                                'original_line': line
                            }
                            
                            self.users.append(user_data)
                            
                            # Display text'i düzelt
                            if proxy and proxy_port:
                                display_text = f"{username} (Proxy: {proxy}:{proxy_port})"
                            else:
                                display_text = f"{username} (Proxy: Yok)"
                            
                            self.user_listbox.insert(tk.END, display_text)
                
                self.log_message(f"✅ {len(self.users)} kullanıcı yüklendi.")
                
            except Exception as e:
                messagebox.showerror("Hata", f"Dosya okuma hatası: {str(e)}")

    def start_ip_monitoring(self):
        """IP takibini başlat"""
        def monitor_ip():
            while self.ip_thread_running:
                try:
                    # Eğer aktif driver varsa onun IP'sini kontrol et
                    if hasattr(self, 'active_driver') and self.active_driver:
                        try:
                            # Tarayıcının IP'sini kontrol et
                            original_window = self.active_driver.current_window_handle
                            self.active_driver.execute_script("window.open('');")
                            self.active_driver.switch_to.window(self.active_driver.window_handles[-1])
                            
                            self.active_driver.get("https://api.ipify.org")
                            time.sleep(1)
                            
                            browser_ip = self.active_driver.find_element("tag name", "body").text.strip()
                            self.current_ip = f"{browser_ip} (Tarayıcı)"
                            
                            # Sekmeyi kapat ve geri dön
                            self.active_driver.close()
                            self.active_driver.switch_to.window(original_window)
                            
                        except:
                            # Tarayıcı IP kontrolü başarısız olursa normal IP kontrolü yap
                            response = requests.get("https://api.ipify.org", timeout=5)
                            self.current_ip = response.text.strip()
                    else:
                        # Normal IP kontrolü
                        response = requests.get("https://api.ipify.org", timeout=5)
                        self.current_ip = response.text.strip()
                    
                    self.ip_label.config(text=self.current_ip)
                except:
                    self.current_ip = "Bağlantı hatası"
                    self.ip_label.config(text=self.current_ip)
                
                time.sleep(10)  # 10 saniyede bir kontrol et
        
        thread = threading.Thread(target=monitor_ip, daemon=True)
        thread.start()

    def start_login_process(self):
        """Giriş işlemini başlat"""
        if not self.users:
            messagebox.showwarning("Uyarı", "Önce kullanıcı listesi yükleyin!")
            return
        
        # Thread'de çalıştır
        thread = threading.Thread(target=self.login_process_thread, daemon=True)
        thread.start()

    def login_process_thread(self):
        """Giriş işlemi thread'i"""
        self.log_message("🚀 Giriş işlemi başlatılıyor...")
        
        for i, user in enumerate(self.users, 1):
            try:
                self.log_message(f"\n[{i}/{len(self.users)}] {user['username']} işleniyor...")
            
                # Profil kontrolü - sadece temel klasör kontrolü
                base_profile_path = f"./Profiller/{user['username']}"
                if os.path.exists(base_profile_path):
                    # Klasör varsa ama boşsa veya sadece temp dosyalar varsa devam et
                    try:
                        files = os.listdir(base_profile_path)
                        important_files = [f for f in files if f in ['Default', 'Local State', 'Preferences']]
                        if len(important_files) >= 2:  # Önemli dosyalar varsa atla
                            self.log_message(f"⏭️ {user['username']} zaten giriş yapmış, atlanıyor.")
                            continue
                    except:
                        pass
            
                # Tarayıcı başlat
                driver = self.create_driver(user)
                if not driver:
                    continue
            
                # Giriş işlemi
                success = self.perform_login(driver, user)
            
                if success:
                    self.log_message(f"✅ {user['username']} başarıyla giriş yaptı.")
                    # Scroll simülasyonu
                    self.simulate_scroll(driver)
                    
                    # IP reset
                    if self.proxy_enabled.get() and self.reset_url_entry.get():
                        self.reset_ip(driver)
                        
                    # Profili kalıcı hale getir
                    self.save_profile_permanently(user['username'], driver)
                else:
                    self.log_message(f"❌ {user['username']} giriş başarısız.")
                    driver.quit()
            
                # Kullanıcılar arası bekleme
                if i < len(self.users):
                    wait_time = random.randint(3, 8)
                    self.log_message(f"⏳ Sonraki kullanıcı için {wait_time} saniye bekleniyor...")
                    time.sleep(wait_time)
                
            except Exception as e:
                self.log_message(f"❌ {user['username']} işlenirken hata: {str(e)}")

        self.log_message("\n🎉 Tüm kullanıcılar işlendi!")

    def create_driver(self, user):
        """Chrome driver oluştur"""
        try:
            options = Options()
            
            # Profil ayarı - basit path kullan
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            profile_path = os.path.abspath(f"./TempProfiller/{user['username']}_{unique_id}")
            
            # Profil dizinini oluştur
            os.makedirs(profile_path, exist_ok=True)
            
            # Mevcut Chrome process'lerini kontrol et ve kapat
            self.close_existing_chrome_processes(user['username'])
            
            options.add_argument(f"--user-data-dir={profile_path}")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-default-apps")
            
            # Headless ayarı
            if not self.browser_visible.get():
                options.add_argument("--headless=new")
            
            # Proxy ayarı
            proxy_to_use = None
            if user['proxy'] and user['proxy_port']:
                proxy_to_use = f"{user['proxy']}:{user['proxy_port']}"
                self.log_message(f"🌐 Özel proxy kullanılıyor: {proxy_to_use}")
            elif self.proxy_enabled.get() and self.proxy_entry.get():
                proxy_to_use = self.proxy_entry.get()
                self.log_message(f"🌐 Genel proxy kullanılıyor: {proxy_to_use}")
            
            if proxy_to_use:
                # Kimlik doğrulamalı proxy kontrolü
                if proxy_to_use.count(':') >= 3:
                    self.log_message(f"⚠️ Kimlik doğrulamalı proxy tespit edildi, atlanıyor.")
                    return None
                options.add_argument(f"--proxy-server={proxy_to_use}")
            
            # Diğer ayarlar
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")  # Hızlandırmak için
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            service = Service("chromedriver.exe")
            service.hide_command_prompt_window = True
            
            driver = webdriver.Chrome(service=service, options=options)
            self.active_driver = driver  # Aktif driver'ı kaydet
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
            
        except Exception as e:
            self.log_message(f"❌ Tarayıcı başlatma hatası: {str(e)}")
            return None
            
    def close_existing_chrome_processes(self, username):
        """Mevcut Chrome process'lerini kapat"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        if proc.info['cmdline']:
                            cmdline = ' '.join(proc.info['cmdline'])
                            if username in cmdline and 'user-data-dir' in cmdline:
                                proc.terminate()
                                proc.wait(timeout=3)
                                self.log_message(f"🔄 {username} için mevcut Chrome process kapatıldı")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
        except ImportError:
            # psutil yoksa basit kontrol
            pass
        except Exception as e:
            self.log_message(f"⚠️ Process kapatma hatası: {str(e)}")

    def perform_login(self, driver, user):
        """Giriş işlemini gerçekleştir"""
        try:
            # Giriş sayfasına git
            driver.get("https://x.com/i/flow/login?lang=tr")
            
            # Kullanıcı adı girişi
            self.wait_and_type(driver, "//*[@autocomplete='username']", user['username'])
            
            # İleri butonuna tıkla
            self.wait_and_click(driver, "//button[.//span[text()='İleri']]")
            
            # Şifre girişi
            self.wait_and_type(driver, "//*[@autocomplete='current-password']", user['password'])
            
            # Giriş yap butonuna tıkla
            self.wait_and_click(driver, "//button[.//span[text()='Giriş yap']]")
            
            # Giriş başarılı mı kontrol et
            time.sleep(5)
            if "home" in driver.current_url.lower() or "x.com" in driver.current_url:
                return True
            
            return False
            
        except Exception as e:
            self.log_message(f"❌ Giriş hatası: {str(e)}")
            return False
            
    def save_profile_permanently(self, username, driver):
        """Profili kalıcı klasöre kaydet"""
        try:
            # Driver'ı kapat ve biraz bekle
            temp_profile = driver.capabilities['chrome']['userDataDir']
            permanent_profile = f"./Profiller/{username}"
            
            # Driver'ı tamamen kapat
            driver.quit()
            if hasattr(self, 'active_driver') and self.active_driver == driver:
                self.active_driver = None
            time.sleep(3)  # Chrome'un tamamen kapanması için bekle
            
            # Geçici profili kalıcı konuma kopyala
            if os.path.exists(temp_profile) and not os.path.exists(permanent_profile):
                import shutil
                try:
                    shutil.copytree(temp_profile, permanent_profile, ignore_dangling_symlinks=True)
                    self.log_message(f"💾 {username} profili kalıcı olarak kaydedildi.")
                    
                    # Geçici profili temizle
                    try:
                        shutil.rmtree(temp_profile)
                        self.log_message(f"🧹 {username} geçici profili temizlendi.")
                    except:
                        pass
                        
                except Exception as copy_error:
                    self.log_message(f"⚠️ Profil kopyalama hatası: {str(copy_error)}")
                    # Alternatif yöntem: sadece önemli dosyaları kopyala
                    self.copy_important_files(temp_profile, permanent_profile, username)
                    
        except Exception as e:
            self.log_message(f"⚠️ Profil kaydetme hatası: {str(e)}")

    def copy_important_files(self, temp_profile, permanent_profile, username):
        """Önemli profil dosyalarını kopyala"""
        try:
            import shutil
            os.makedirs(permanent_profile, exist_ok=True)
            
            # Kopyalanacak önemli dosyalar
            important_files = [
                'Local State',
                'Preferences',
                'Default/Preferences',
                'Default/Local State'
            ]
            
            copied_count = 0
            for file_path in important_files:
                src = os.path.join(temp_profile, file_path)
                dst = os.path.join(permanent_profile, file_path)
                
                if os.path.exists(src):
                    try:
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)
                        copied_count += 1
                    except:
                        continue
            
            if copied_count > 0:
                self.log_message(f"💾 {username} profili kısmen kaydedildi ({copied_count} dosya).")
            else:
                self.log_message(f"⚠️ {username} profili kaydedilemedi.")
                
        except Exception as e:
            self.log_message(f"⚠️ Önemli dosya kopyalama hatası: {str(e)}")

    def wait_and_type(self, driver, xpath, text):
        """Element bekle ve yazı yaz"""
        wait_time = random.randint(800, 3000) / 1000
        time.sleep(wait_time)
        
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            element.clear()
            
            # Karakter karakter yaz
            for char in text:
                element.send_keys(char)
                time.sleep(random.randint(50, 150) / 1000)
                
        except TimeoutException:
            # Alternatif yöntem dene
            element = driver.find_element(By.CSS_SELECTOR, "input")
            element.clear()
            element.send_keys(text)

    def wait_and_click(self, driver, xpath):
        """Element bekle ve tıkla"""
        wait_time = random.randint(1000, 3000) / 1000
        time.sleep(wait_time)
        
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            element.click()
        except TimeoutException:
            # Alternatif yöntem dene
            element = driver.find_element(By.CSS_SELECTOR, "button[type='button']")
            element.click()

    def simulate_scroll(self, driver):
        """Organik scroll simülasyonu"""
        scroll_duration = random.randint(10, 20)
        self.log_message(f"📜 {scroll_duration} saniye scroll simülasyonu yapılıyor...")
        
        start_time = time.time()
        while time.time() - start_time < scroll_duration:
            scroll_amount = random.randint(300, 600)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.randint(1000, 3000) / 1000)

    def reset_ip(self, driver):
        """IP sıfırlama"""
        try:
            reset_url = self.reset_url_entry.get()
            self.log_message(f"🔄 IP sıfırlanıyor: {reset_url}")
            driver.get(reset_url)
            time.sleep(10)
        except Exception as e:
            self.log_message(f"❌ IP sıfırlama hatası: {str(e)}")

    def log_message(self, message):
        """Log mesajı ekle"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.parent.update()
