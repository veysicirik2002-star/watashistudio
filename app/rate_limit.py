import time
from collections import defaultdict, deque

_istekler = defaultdict(deque)


def limit_asildi(ip, limit, pencere=60):
    """Aynı IP'den `pencere` saniyede `limit` isteği geçerse True döner."""
    simdi = time.time()
    kuyruk = _istekler[ip]
    while kuyruk and simdi - kuyruk[0] > pencere:
        kuyruk.popleft()
    if len(kuyruk) >= limit:
        return True
    kuyruk.append(simdi)
    return False
