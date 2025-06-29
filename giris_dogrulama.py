import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import requests
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class GirisDogrulama:
    def __init__(self, parent, colors, return_callback):
        self.parent = parent
        self.colors = colors
        self.return_callback = return_callback  # Ana menüye dönüş callback'i
        self.profiles = []
        self.filtered_profiles = []
        self.current_ip = "Kontrol ediliyor..."
        self.ip_thread_running = True
        self.drivers = []
        
        self.create_window()
        self.load_profiles()
        self.start_ip_monitoring()
    
    def create_window(self):
        """Giriş Doğrulama penceresini oluştur"""
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
            text="🔍 Giriş Doğrulama/Silme",
            font=("Arial", 20, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['background']
        )
        title_label.pack(side="left", expand=True)
        
        # Üst panel - Arama ve kontroller
        top_frame = tk.Frame(main_frame, bg=self.colors['background'])
        top_frame.pack(fill="x", pady=(0, 10))
        
        self.create_top_panel(top_frame)
        
        # Orta panel - Profil listesi
        middle_frame = tk.Frame(main_frame, bg=self.colors['background'])
        middle_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.create_profile_panel(middle_frame)
        
        # Alt panel - IP ve proxy ayarları
        bottom_frame = tk.Frame(main_frame, bg=self.colors['background'])
        bottom_frame.pack(fill="x")
        
        self.create_bottom_panel(bottom_frame)

    def return_to_main(self):
        """Ana menüye dön"""
        self.ip_thread_running = False
    
        # Açık driver'ları kapat - geçici dosya temizleme yok
        for driver_info in self.drivers:
            try:
                driver_info['driver'].quit()
                # Geçici profil temizleme kaldırıldı - artık kalıcı profil kullanıyoruz
            except:
                pass
    
        self.window_frame.destroy()
        self.return_callback()
    
    def create_top_panel(self, parent):
        """Üst paneli oluştur"""
        # Arama kutusu
        search_frame = tk.Frame(parent, bg=self.colors['background'])
        search_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            search_frame,
            text="🔍 Arama:",
            font=("Arial", 12, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['background']
        ).pack(side="left")
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_profiles)
        
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Arial", 11),
            width=30
        )
        self.search_entry.pack(side="left", padx=(10, 0))
        
        # Kontrol butonları
        control_frame = tk.Frame(parent, bg=self.colors['background'])
        control_frame.pack(fill="x")
        
        # Sol taraf butonları
        left_buttons = tk.Frame(control_frame, bg=self.colors['background'])
        left_buttons.pack(side="left")
        
        select_all_btn = tk.Button(
            left_buttons,
            text="✅ Tümünü Seç",
            command=self.select_all,
            font=("Arial", 10),
            bg=self.colors['secondary'],
            fg="#FFFFFF",
            activebackground=self.colors['secondary_hover'],
            relief="flat",
            cursor="hand2"
        )
        select_all_btn.pack(side="left", padx=(0, 5))
        
        deselect_all_btn = tk.Button(
            left_buttons,
            text="❌ Seçimi Kaldır",
            command=self.deselect_all,
            font=("Arial", 10),
            bg=self.colors['text_secondary'],
            fg="#FFFFFF",
            activebackground="#555555",
            relief="flat",
            cursor="hand2"
        )
        deselect_all_btn.pack(side="left", padx=(0, 5))
        
        delete_btn = tk.Button(
            left_buttons,
            text="🗑️ Sil",
            command=self.delete_selected,
            font=("Arial", 10, "bold"),
            bg=self.colors['error'],
            fg="#FFFFFF",
            activebackground="#B71C1C",
            relief="flat",
            cursor="hand2"
        )
        delete_btn.pack(side="left")
        
        # Sağ taraf butonları
        right_buttons = tk.Frame(control_frame, bg=self.colors['background'])
        right_buttons.pack(side="right")
        
        refresh_btn = tk.Button(
            right_buttons,
            text="🔄 Yenile",
            command=self.load_profiles,
            font=("Arial", 10),
            bg=self.colors['primary'],
            fg="#FFFFFF",
            activebackground=self.colors['primary_hover'],
            relief="flat",
            cursor="hand2"
        )
        refresh_btn.pack(side="right")
    
    def create_profile_panel(self, parent):
        """Profil panelini oluştur"""
        # Profil listesi frame
        list_frame = tk.LabelFrame(
            parent,
            text="📁 Profil Listesi",
            font=("Arial", 12, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['background']
        )
        list_frame.pack(fill="both", expand=True)
        
        # Scrollable frame oluştur
        canvas = tk.Canvas(list_frame, bg="#FFFFFF")
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel binding
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        self.canvas = canvas
    
    def create_bottom_panel(self, parent):
        """Alt paneli oluştur"""
        # Proxy ayarları
        proxy_frame = tk.LabelFrame(
            parent,
            text="🌐 Proxy Ayarları",
            font=("Arial", 10, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['background']
        )
        proxy_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        proxy_control_frame = tk.Frame(proxy_frame, bg=self.colors['background'])
        proxy_control_frame.pack(fill="x", padx=5, pady=5)
        
        self.proxy_enabled = tk.BooleanVar()
        proxy_check = tk.Checkbutton(
            proxy_control_frame,
            text="Proxy kullanılsın mı?",
            variable=self.proxy_enabled,
            font=("Arial", 9),
            fg=self.colors['text_primary'],
            bg=self.colors['background'],
            command=self.toggle_proxy_fields
        )
        proxy_check.pack(side="left")
        
        self.proxy_entry = tk.Entry(
            proxy_control_frame,
            font=("Arial", 9),
            state="disabled",
            width=20
        )
        self.proxy_entry.pack(side="left", padx=(10, 0))

        # Proxy ayarları kısmının sonuna ekle (proxy_entry.pack satırından sonra)
        tk.Label(
            proxy_control_frame,
            text="IP Reset URL:",
            font=("Arial", 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['background']
        ).pack(anchor="w", padx=(5, 0), pady=(5, 0))

        self.reset_url_entry = tk.Entry(
            proxy_control_frame,
            font=("Arial", 9),
            state="disabled",
            width=20
        )
        self.reset_url_entry.pack(side="left", padx=(10, 0), pady=(0, 5))
        
        # IP bilgisi ve kontrol
        ip_frame = tk.LabelFrame(
            parent,
            text="🌐 IP Bilgisi",
            font=("Arial", 10, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['background']
        )
        ip_frame.pack(side="right", fill="x", expand=True)
        
        ip_control_frame = tk.Frame(ip_frame, bg=self.colors['background'])
        ip_control_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Label(
            ip_control_frame,
            text="Şu anki IP:",
            font=("Arial", 9, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['background']
        ).pack(side="left")
        
        self.ip_label = tk.Label(
            ip_control_frame,
            text=self.current_ip,
            font=("Arial", 9),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        )
        self.ip_label.pack(side="left", padx=(10, 0))
        
        ip_change_btn = tk.Button(
            ip_control_frame,
            text="🔄 IP Değiştir",
            command=self.change_ip,
            font=("Arial", 9),
            bg=self.colors['primary'],
            fg="#FFFFFF",
            activebackground=self.colors['primary_hover'],
            relief="flat",
            cursor="hand2"
        )
        ip_change_btn.pack(side="right")
    
    def load_profiles(self):
        """Profilleri yükle"""
        self.profiles = []
        profiles_dir = "./Profiller"
        
        if os.path.exists(profiles_dir):
            try:
                for item in os.listdir(profiles_dir):
                    item_path = os.path.join(profiles_dir, item)
                    if os.path.isdir(item_path):
                        self.profiles.append(item)
            except Exception as e:
                messagebox.showerror("Hata", f"Profiller yüklenirken hata: {str(e)}")
        
        self.profiles.sort()
        self.filtered_profiles = self.profiles.copy()
        self.update_profile_display()
    
    def filter_profiles(self, *args):
        """Profilleri filtrele"""
        search_text = self.search_var.get().lower()
        if search_text:
            self.filtered_profiles = [p for p in self.profiles if search_text in p.lower()]
        else:
            self.filtered_profiles = self.profiles.copy()
        
        self.update_profile_display()
    
    def update_profile_display(self):
        """Profil görünümünü güncelle"""
        # Mevcut widget'ları temizle
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.profile_vars = {}
        
        if not self.filtered_profiles:
            no_profile_label = tk.Label(
                self.scrollable_frame,
                text="Profil bulunamadı",
                font=("Arial", 12),
                fg=self.colors['text_secondary'],
                bg="#FFFFFF"
            )
            no_profile_label.pack(pady=20)
            return
        
        for i, profile in enumerate(self.filtered_profiles):
            profile_frame = tk.Frame(
                self.scrollable_frame,
                bg="#F8F8F8" if i % 2 == 0 else "#FFFFFF",
                relief="ridge",
                bd=1
            )
            profile_frame.pack(fill="x", padx=5, pady=2)
            
            # Checkbox
            var = tk.BooleanVar()
            self.profile_vars[profile] = var
            
            checkbox = tk.Checkbutton(
                profile_frame,
                variable=var,
                bg=profile_frame.cget("bg")
            )
            checkbox.pack(side="left", padx=5, pady=5)
            
            # Profil adı
            profile_label = tk.Label(
                profile_frame,
                text=f"👤 {profile}",
                font=("Arial", 10),
                fg=self.colors['text_primary'],
                bg=profile_frame.cget("bg"),
                cursor="hand2"
            )
            profile_label.pack(side="left", padx=(0, 10), pady=5)
            
            # Çift tıklama ile tarayıcı aç
            profile_label.bind("<Double-Button-1>", lambda e, p=profile: self.open_browser(p))
            
            # Tarayıcı aç butonu
            open_btn = tk.Button(
                profile_frame,
                text="🌐 Aç",
                command=lambda p=profile: self.open_browser(p),
                font=("Arial", 8),
                bg=self.colors['secondary'],
                fg="#FFFFFF",
                activebackground=self.colors['secondary_hover'],
                relief="flat",
                cursor="hand2"
            )
            open_btn.pack(side="right", padx=5, pady=2)
        
        # Canvas scroll region güncelle
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def select_all(self):
        """Tümünü seç"""
        for var in self.profile_vars.values():
            var.set(True)
    
    def deselect_all(self):
        """Seçimi kaldır"""
        for var in self.profile_vars.values():
            var.set(False)
    
    def delete_selected(self):
        """Seçili profilleri sil"""
        selected_profiles = [profile for profile, var in self.profile_vars.items() if var.get()]
        
        if not selected_profiles:
            messagebox.showwarning("Uyarı", "Silinecek profil seçilmedi!")
            return
        
        # Onay iste
        result = messagebox.askyesno(
            "Onay",
            f"{len(selected_profiles)} profil silinecek. Emin misiniz?\n\n" +
            "\n".join(selected_profiles[:5]) +
            ("..." if len(selected_profiles) > 5 else "")
        )
        
        if result:
            deleted_count = 0
            for profile in selected_profiles:
                try:
                    profile_path = os.path.join("./Profiller", profile)
                    if os.path.exists(profile_path):
                        shutil.rmtree(profile_path)
                        deleted_count += 1
                except Exception as e:
                    messagebox.showerror("Hata", f"{profile} silinirken hata: {str(e)}")
            
            messagebox.showinfo("Başarılı", f"{deleted_count} profil silindi.")
            self.load_profiles()
    
    def open_browser(self, profile):
        """Tarayıcı aç"""
        try:
            # Önce mevcut Chrome process'lerini kapat
            self.close_existing_chrome_processes(profile)
        
            options = Options()
        
            # Kalıcı profil kullan - geçici kopyalama yok
            original_profile_path = os.path.abspath(f"./Profiller/{profile}")
        
            # Profil yoksa uyarı ver
            if not os.path.exists(original_profile_path):
                messagebox.showwarning("Uyarı", f"{profile} profili bulunamadı!")
                return
        
            options.add_argument(f"--user-data-dir={original_profile_path}")
        
            # Proxy ayarı
            if self.proxy_enabled.get() and self.proxy_entry.get():
                proxy = self.proxy_entry.get()
                options.add_argument(f"--proxy-server={proxy}")
        
            # Diğer ayarlar
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-default-apps")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
        
            service = Service("chromedriver.exe")
            service.hide_command_prompt_window = True
        
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
            # Twitter'a git
            driver.get("https://x.com/")

            # Tarayıcının IP adresini kontrol et ve güncelle
            self.check_browser_ip(driver)
        
            # Driver'ı listeye ekle - temp_path artık None
            self.drivers.append({
                'driver': driver,
                'profile': profile,
                'temp_path': None  # Artık geçici profil yok
            })
        
            messagebox.showinfo("Başarılı", f"{profile} profili için tarayıcı açıldı.\n✅ Uzantılar ve ayarlar kalıcı olarak korunacak!")
        
        except Exception as e:
            messagebox.showerror("Hata", f"Tarayıcı açılırken hata: {str(e)}")
    
    def close_existing_chrome_processes(self, profile):
        """Mevcut Chrome process'lerini kapat"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        if proc.info['cmdline']:
                            cmdline = ' '.join(proc.info['cmdline'])
                            if profile in cmdline and 'user-data-dir' in cmdline:
                                proc.terminate()
                                proc.wait(timeout=3)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
        except ImportError:
            # psutil yoksa basit kontrol
            pass
        except Exception as e:
            print(f"Process kapatma hatası: {str(e)}")
    
    def toggle_proxy_fields(self):
        """Proxy alanlarını etkinleştir/devre dışı bırak"""
        state = "normal" if self.proxy_enabled.get() else "disabled"
        self.proxy_entry.config(state=state)
        self.reset_url_entry.config(state=state)
    
    def change_ip(self):
        """IP değiştir"""
        if not self.proxy_enabled.get() or not self.proxy_entry.get():
            messagebox.showwarning("Uyarı", "Önce proxy ayarlarını yapın!")
            return
    
        if not self.reset_url_entry.get():
            messagebox.showwarning("Uyarı", "IP Reset URL'sini girin!")
            return
    
        # Açık tarayıcılar varsa onlarda IP reset yap
        if self.drivers:
            for driver_info in self.drivers:
                try:
                    driver = driver_info['driver']
                    reset_url = self.reset_url_entry.get()
                
                    # Yeni sekme aç
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[-1])
                
                    # Reset URL'sine git
                    driver.get(reset_url)
                    time.sleep(5)
                
                    # IP'yi tekrar kontrol et
                    self.check_browser_ip(driver)
                
                    messagebox.showinfo("Başarılı", f"{driver_info['profile']} için IP sıfırlandı.")
                
                except Exception as e:
                    messagebox.showerror("Hata", f"IP sıfırlama hatası: {str(e)}")
        else:
            messagebox.showinfo("Bilgi", "Açık tarayıcı bulunamadı.")
    
    def start_ip_monitoring(self):
        """IP takibini başlat"""
        def monitor_ip():
            while self.ip_thread_running:
                try:
                    response = requests.get("https://api.ipify.org", timeout=5)
                    self.current_ip = response.text.strip()
                    self.ip_label.config(text=self.current_ip)
                except:
                    self.current_ip = "Bağlantı hatası"
                    self.ip_label.config(text=self.current_ip)
            
            time.sleep(1)
    
        thread = threading.Thread(target=monitor_ip, daemon=True)
        thread.start()

    def check_browser_ip(self, driver):
        """Tarayıcının IP adresini kontrol et"""
        try:
            # Yeni sekme aç
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
        
            # IP kontrol sitesine git
            driver.get("https://api.ipify.org")
            time.sleep(2)
        
            # IP adresini al
            browser_ip = driver.find_element("tag name", "body").text.strip()
        
            # IP label'ını güncelle
            self.ip_label.config(text=f"{browser_ip} (Tarayıcı)")
        
            # Sekmeyi kapat ve ana sekmeye dön
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        
        except Exception as e:
            print(f"IP kontrol hatası: {str(e)}")
