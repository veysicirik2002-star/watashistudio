import hmac
import re
from functools import wraps

from flask import Blueprint, request, jsonify, current_app

from app.database import lead_ekle, tum_leadler, lead_sil
from app.error_log import son_hatalar
from app.rate_limit import limit_asildi
from app.services.ai_service import ai_service, AIServiceError

api_bp = Blueprint('api', __name__)


def hata(mesaj, kod):
    return jsonify({"basari": False, "hata": mesaj}), kod


def admin_gerekli(f):
    """X-Admin-Key başlığı ADMIN_PASSWORD ile eşleşmeyen istekleri reddeder."""
    @wraps(f)
    def sarmal(*args, **kwargs):
        anahtar = current_app.config.get('ADMIN_PASSWORD', '')
        gelen = request.headers.get('X-Admin-Key', '')
        if not anahtar or not hmac.compare_digest(gelen, anahtar):
            return hata("Yetkisiz erişim.", 401)
        return f(*args, **kwargs)
    return sarmal


@api_bp.route('/sohbet', methods=['POST'])
def sohbet():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'x').split(',')[0].strip()
    if limit_asildi(ip, current_app.config.get('CHAT_RATE_LIMIT', 20)):
        return hata("Çok hızlı yazıyorsun, birkaç saniye bekleyip tekrar dene.", 429)

    veri = request.get_json(silent=True) or {}
    mesaj = str(veri.get('mesaj', '')).strip()
    gecmis = veri.get('gecmis', [])

    if not mesaj:
        return hata("Lütfen bir mesaj yazın.", 400)
    if len(mesaj) > 600:
        return hata("Mesaj en fazla 600 karakter olabilir.", 400)

    try:
        cevap = ai_service.yanit_uret(mesaj, gecmis if isinstance(gecmis, list) else [])
        return jsonify({"basari": True, "cevap": cevap}), 200
    except AIServiceError:
        current_app.logger.exception("[POST /api/sohbet] AI servisi hatası")
        return hata("Yapay zeka şu an yanıt veremiyor, lütfen tekrar deneyin.", 503)
    except Exception:
        current_app.logger.exception("[POST /api/sohbet] beklenmeyen hata")
        return hata("Beklenmeyen bir sunucu hatası oluştu.", 500)


@api_bp.route('/leads', methods=['POST'])
def yeni_lead():
    veri = request.get_json(silent=True) or {}
    isim = str(veri.get('isim', '')).strip()[:120]
    telefon = str(veri.get('telefon', '')).strip()[:40]
    mesaj = str(veri.get('mesaj', '')).strip()[:2000]

    if not isim or not telefon:
        return hata("İsim ve telefon alanları zorunludur.", 400)
    if len(re.sub(r'[^0-9]', '', telefon)) < 7:
        return hata("Lütfen geçerli bir telefon numarası yazın.", 400)

    try:
        kayit_id = lead_ekle(isim, telefon, mesaj)
        return jsonify({"basari": True, "id": kayit_id}), 201
    except Exception:
        current_app.logger.exception("[POST /api/leads] veritabanı hatası")
        return hata("Kayıt sırasında veritabanı hatası oluştu.", 500)


@api_bp.route('/leads', methods=['GET'])
@admin_gerekli
def leadleri_getir():
    try:
        return jsonify({"basari": True, "leads": tum_leadler()}), 200
    except Exception:
        current_app.logger.exception("[GET /api/leads] veritabanı hatası")
        return hata("Kayıtlar alınırken hata oluştu.", 500)


@api_bp.route('/leads/<int:lead_id>', methods=['DELETE'])
@admin_gerekli
def lead_sil_route(lead_id):
    try:
        if lead_sil(lead_id):
            return jsonify({"basari": True}), 200
        return hata("Kayıt bulunamadı.", 404)
    except Exception:
        current_app.logger.exception("[DELETE /api/leads] veritabanı hatası")
        return hata("Silme sırasında hata oluştu.", 500)


@api_bp.route('/hatalar', methods=['GET'])
@admin_gerekli
def hatalari_getir():
    """Son uyarı/hata kayıtları (en yeni üstte). Render loglarına ek olarak."""
    return jsonify({"basari": True, "hatalar": list(son_hatalar.kayitlar)[::-1]}), 200
