import logging
from collections import deque
from datetime import datetime


class SonHatalar(logging.Handler):
    """Son uyarı/hataları bellekte tutar; /api/hatalar ile okunur (Render loglarına ek)."""

    def __init__(self, kapasite=50):
        super().__init__(level=logging.WARNING)
        self.kayitlar = deque(maxlen=kapasite)

    def emit(self, record):
        self.kayitlar.append({
            "zaman": datetime.now().isoformat(timespec="seconds"),
            "seviye": record.levelname,
            "mesaj": self.format(record)[:2000],
        })


son_hatalar = SonHatalar()
