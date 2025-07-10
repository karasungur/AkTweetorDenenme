
class AkTweetorException(Exception):
    """Ana exception sınıfı"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

class DatabaseException(AkTweetorException):
    """Veritabanı hataları"""
    pass

class SeleniumException(AkTweetorException):
    """Selenium hataları"""
    pass

class ProxyException(AkTweetorException):
    """Proxy hataları"""
    pass

class ConfigException(AkTweetorException):
    """Konfigürasyon hataları"""
    pass

class TwitterLoginException(SeleniumException):
    """Twitter giriş hataları"""
    pass

class ProfileException(AkTweetorException):
    """Profil işlemi hataları"""
    pass

def handle_exception(func):
    """Exception handling decorator"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AkTweetorException as e:
            from utils.logger import logger
            logger.error(f"AkTweetor hatası in {func.__name__}: {e.message}")
            raise
        except Exception as e:
            from utils.logger import logger
            logger.exception(f"Beklenmeyen hata in {func.__name__}: {str(e)}")
            raise AkTweetorException(f"Beklenmeyen hata: {str(e)}")
    
    return wrapper
