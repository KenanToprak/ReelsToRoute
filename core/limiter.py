from slowapi import Limiter
from slowapi.util import get_remote_address

# Hız sınırlayıcıyı oluşturuyoruz (IP adresine göre)
limiter = Limiter(key_func=get_remote_address)
