
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from config.settings import settings

class CustomFormatter(logging.Formatter):
    """Özel log formatter'ı"""
    
    def __init__(self):
        super().__init__()
        
        # Renkli log formatları
        self.COLORS = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
            'RESET': '\033[0m'      # Reset
        }
        
        self.base_format = "[{asctime}] [{levelname:8s}] [{name}] {message}"
        self.date_format = "%Y-%m-%d %H:%M:%S"
    
    def format(self, record):
        # Terminal için renkli format
        if hasattr(record.levelname, '__call__'):
            level_name = record.levelname()
        else:
            level_name = record.levelname
            
        color = self.COLORS.get(level_name, self.COLORS['RESET'])
        
        # Konsol için renkli
        console_format = f"{color}{self.base_format}{self.COLORS['RESET']}"
        formatter = logging.Formatter(console_format, self.date_format, style='{')
        
        return formatter.format(record)

class Logger:
    def __init__(self, name: str = "AkTweetor"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.setup_logger()
    
    def setup_logger(self):
        """Logger'ı ayarla"""
        # Logger seviyesi
        log_level = getattr(logging, settings.get('app.log_level', 'INFO').upper())
        self.logger.setLevel(log_level)
        
        # Tekrar handler eklemeyi önle
        if self.logger.handlers:
            return
        
        # Log dizinini oluştur
        log_dir = settings.get('directories.logs', './logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Konsol handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(CustomFormatter())
        console_handler.setLevel(log_level)
        self.logger.addHandler(console_handler)
        
        # Dosya handler (rotating)
        log_file = os.path.join(log_dir, f"{self.name.lower()}.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        file_format = "[{asctime}] [{levelname:8s}] [{name}] {message}"
        file_formatter = logging.Formatter(file_format, "%Y-%m-%d %H:%M:%S", style='{')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        
        # Hata log dosyası
        error_file = os.path.join(log_dir, f"{self.name.lower()}_errors.log")
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setFormatter(file_formatter)
        error_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        self.logger.exception(message, *args, **kwargs)

# Global logger instance
logger = Logger()
