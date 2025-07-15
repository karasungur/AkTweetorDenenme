
import os
import json
from typing import Dict, Any

# Proje kök dizini
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# İşletim sistemine göre chromedriver varsayılan adı
DEFAULT_DRIVER = "chromedriver.exe" if os.name == "nt" else "chromedriver"

class Settings:
    def __init__(self):
        self.config_file = "config/app_config.json"
        self.default_config = {
            "database": {
                "host": "localhost",
                "port": 3306,
                "username": "root",
                "password": "",
                "database": "aktweetor",
                "pool_size": 5
            },
            "selenium": {
                "driver_path": DEFAULT_DRIVER,
                "timeout": 10,
                "headless": False,
                "page_load_timeout": 30,
                "implicit_wait": 5
            },
            "proxy": {
                "enabled": False,
                "default_proxy": "",
                "reset_url": "",
                "timeout": 5
            },
            "app": {
                "name": "AkTweetor",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO"
            },
            "directories": {
                "profiles": "./Profiller",
                "temp_profiles": "./TempProfiller",
                "logs": "./logs"
            }
        }
        self.config = self.load_config()

    def resolve_path(self, path: str) -> str:
        """Verilen yolu proje köküne göre çözümler"""
        if os.path.isabs(path):
            return path
        return os.path.join(BASE_DIR, path)
    
    def load_config(self) -> Dict[str, Any]:
        """Konfigürasyonu yükle"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Varsayılan değerlerle birleştir
                return self.merge_config(self.default_config, config)
            else:
                # İlk kez çalışıyorsa varsayılan config'i kaydet
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            print(f"⚠️ Config yükleme hatası: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any] = None):
        """Konfigürasyonu kaydet"""
        if config is None:
            config = self.config
        
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Config kaydetme hatası: {e}")
    
    def get(self, key_path: str, default=None):
        """Nokta notasyonu ile değer al (örn: 'database.host')"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """Nokta notasyonu ile değer ayarla"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        self.save_config()
    
    def merge_config(self, base: Dict, override: Dict) -> Dict:
        """İki config'i birleştir"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_config(result[key], value)
            else:
                result[key] = value
        
        return result

# Global settings instance
settings = Settings()
