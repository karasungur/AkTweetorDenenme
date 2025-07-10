
import asyncio
import aiohttp
import time
import random
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config.settings import settings
from utils.logger import logger

class AsyncSeleniumWrapper:
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        self.executor.shutdown(wait=True)
    
    async def create_driver_async(self, profile_path: str, proxy: Optional[str] = None, headless: bool = False) -> Optional[webdriver.Chrome]:
        """Async olarak Chrome driver oluştur"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._create_driver_sync,
            profile_path, proxy, headless
        )
    
    def _create_driver_sync(self, profile_path: str, proxy: Optional[str] = None, headless: bool = False) -> Optional[webdriver.Chrome]:
        """Senkron Chrome driver oluşturma"""
        try:
            options = Options()
            options.add_argument(f"--user-data-dir={profile_path}")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-default-apps")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            
            if headless:
                options.add_argument("--headless=new")
            
            if proxy:
                options.add_argument(f"--proxy-server={proxy}")
            
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            driver_path = settings.get('selenium.driver_path', 'chromedriver.exe')
            service = Service(driver_path)
            service.hide_command_prompt_window = True
            
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Timeout ayarları
            driver.set_page_load_timeout(settings.get('selenium.page_load_timeout', 30))
            driver.implicitly_wait(settings.get('selenium.implicit_wait', 5))
            
            logger.info(f"Chrome driver başarıyla oluşturuldu: {profile_path}")
            return driver
            
        except Exception as e:
            logger.error(f"Chrome driver oluşturma hatası: {e}")
            return None
    
    async def perform_login_async(self, driver: webdriver.Chrome, username: str, password: str) -> bool:
        """Async olarak Twitter'a giriş yap"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._perform_login_sync,
            driver, username, password
        )
    
    def _perform_login_sync(self, driver: webdriver.Chrome, username: str, password: str) -> bool:
        """Senkron Twitter giriş işlemi"""
        try:
            logger.info(f"Twitter giriş işlemi başlatılıyor: {username}")
            
            driver.get("https://x.com/i/flow/login?lang=tr")
            
            # Kullanıcı adı girişi
            self._wait_and_type(driver, "//*[@autocomplete='username']", username)
            
            # İleri butonuna tıkla
            self._wait_and_click(driver, "//button[.//span[text()='İleri']]")
            
            # Şifre girişi
            self._wait_and_type(driver, "//*[@autocomplete='current-password']", password)
            
            # Giriş yap butonuna tıkla
            self._wait_and_click(driver, "//button[.//span[text()='Giriş yap']]")
            
            # Giriş başarılı mı kontrol et
            time.sleep(5)
            if "home" in driver.current_url.lower() or "x.com" in driver.current_url:
                logger.info(f"Twitter giriş başarılı: {username}")
                return True
            
            logger.warning(f"Twitter giriş başarısız: {username}")
            return False
            
        except Exception as e:
            logger.error(f"Twitter giriş hatası {username}: {e}")
            return False
    
    def _wait_and_type(self, driver: webdriver.Chrome, xpath: str, text: str):
        """Element bekle ve yazı yaz"""
        wait_time = random.randint(800, 3000) / 1000
        time.sleep(wait_time)
        
        try:
            timeout = settings.get('selenium.timeout', 10)
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            element.clear()
            
            # İnsan gibi yazma simülasyonu
            for char in text:
                element.send_keys(char)
                time.sleep(random.randint(50, 150) / 1000)
                
        except TimeoutException:
            # Fallback
            element = driver.find_element(By.CSS_SELECTOR, "input")
            element.clear()
            element.send_keys(text)
    
    def _wait_and_click(self, driver: webdriver.Chrome, xpath: str):
        """Element bekle ve tıkla"""
        wait_time = random.randint(1000, 3000) / 1000
        time.sleep(wait_time)
        
        try:
            timeout = settings.get('selenium.timeout', 10)
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            element.click()
        except TimeoutException:
            # Fallback
            element = driver.find_element(By.CSS_SELECTOR, "button[type='button']")
            element.click()
    
    async def get_current_ip_async(self) -> str:
        """Async olarak mevcut IP'yi al"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            timeout = aiohttp.ClientTimeout(total=settings.get('proxy.timeout', 5))
            async with self.session.get('https://api.ipify.org', timeout=timeout) as response:
                if response.status == 200:
                    ip = await response.text()
                    return ip.strip()
                else:
                    return "IP alınamadı"
        except asyncio.TimeoutError:
            return "Timeout"
        except Exception as e:
            logger.error(f"IP alma hatası: {e}")
            return "Hata"
    
    async def reset_ip_async(self, driver: webdriver.Chrome, reset_url: str):
        """Async olarak IP sıfırla"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._reset_ip_sync,
            driver, reset_url
        )
    
    def _reset_ip_sync(self, driver: webdriver.Chrome, reset_url: str):
        """Senkron IP sıfırlama"""
        try:
            logger.info(f"IP sıfırlanıyor: {reset_url}")
            
            # Yeni sekme aç
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            
            # Reset URL'sine git
            driver.get(reset_url)
            time.sleep(10)
            
            # Sekmeyi kapat
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            
            logger.info("IP sıfırlama tamamlandı")
            
        except Exception as e:
            logger.error(f"IP sıfırlama hatası: {e}")
    
    async def simulate_scroll_async(self, driver: webdriver.Chrome, duration: int = None):
        """Async olarak scroll simülasyonu"""
        if duration is None:
            duration = random.randint(10, 20)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._simulate_scroll_sync,
            driver, duration
        )
    
    def _simulate_scroll_sync(self, driver: webdriver.Chrome, duration: int):
        """Senkron scroll simülasyonu"""
        logger.info(f"Scroll simülasyonu başlatılıyor: {duration} saniye")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            scroll_amount = random.randint(300, 600)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.randint(1000, 3000) / 1000)
        
        logger.info("Scroll simülasyonu tamamlandı")
