import re
import time
from collections import defaultdict, deque
from functools import wraps

from flask import Blueprint, render_template, request, jsonify, Response, current_app

from app.database import lead_ekle, tum_leadler, lead_sil
from app.services.ai_service import ai_service

pages_bp = Blueprint('pages', __name__)
api_bp = Blueprint('api', __name__)

_istekler = defaultdict(deque)


def limit_asildi(ip, limit, pencere=60):
    simdi = time.time()
    kuyruk = _istekler[ip]
    while kuyruk and simdi - kuyruk[0] > pencere:
        kuyruk.popleft()
    if len(kuyruk) >= limit:
        return True
    kuyruk.append(simdi)
    return False


def admin_gerekli(f):
    @wraps(f)
    def sarmal(*a, **k):
        sifre = current_app.config.get('ADMIN_PASSWORD', '')
        auth = request.authorization
        if not sifre or not auth or auth.password != sifre:
            return Response('Yönetim girişi gerekli', 401,
                            {'WWW-Authenticate': 'Basic realm="Watashi Studio Yonetim"'})
        return f(*a, **k)
    return sarmal


@pages_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@pages_bp.route('/dashboard', methods=['GET'])
@admin_gerekli
def dashboard():
    return render_template('dashboard.html')


@api_bp.route('/sohbet', methods=['POST'])
def sohbet():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'x').split(',')[0].strip()
    if limit_asildi(ip, current_app.config.get('CHAT_RATE_LIMIT', 20)):
        return jsonify({"basari": False, "hata": "Çok hızlı yazıyorsun maceracı! Birkaç saniye bekleyip tekrar dene. 🐢"}), 429

    veri = request.get_json(silent=True) or {}
    mesaj = str(veri.get('mesaj', '')).strip()
    gecmis = veri.get('gecmis', [])

    if not mesaj:
        return jsonify({"basari": False, "hata": "Lütfen bir mesaj yazın."}), 400
    if len(mesaj) > 600:
        return jsonify({"basari": False, "hata": "Mesajın biraz uzun, 600 karakterin altında tutar mısın?"}), 400

    try:
        sonuc = ai_service.yanit_uret(mesaj, gecmis if isinstance(gecmis, list) else [])
        return jsonify({"basari": True, **sonuc}), 200
    except Exception:
        current_app.logger.exception("[/api/sohbet] AI servisi hatası")
        return jsonify({"basari": False, "hata": "Beklenmeyen bir sunucu hatası oluştu."}), 500


@api_bp.route('/leads', methods=['POST'])
def yeni_lead():
    veri = request.get_json(silent=True) or {}
    isim = str(veri.get('isim', '')).strip()[:120]
    telefon = str(veri.get('telefon', '')).strip()[:40]
    mesaj = str(veri.get('mesaj', '')).strip()[:2000]
    kaynak = str(veri.get('kaynak', '')).strip()[:30]

    if not isim or not telefon:
        return jsonify({"basari": False, "hata": "İsim ve telefon alanları zorunludur."}), 400
    if len(re.sub(r'[^0-9]', '', telefon)) < 7:
        return jsonify({"basari": False, "hata": "Lütfen geçerli bir telefon numarası yaz."}), 400

    if kaynak:
        mesaj = '[' + kaynak + '] ' + mesaj

    try:
        kayit_id = lead_ekle(isim, telefon, mesaj)
        return jsonify({
            "basari": True,
            "mesaj": "Harika! Projeniz Watashi Studio ekibine ulaştı, yakında arayacağız!",
            "id": kayit_id
        }), 201
    except Exception:
        current_app.logger.exception("[POST /api/leads] veritabanı hatası")
        return jsonify({"basari": False, "hata": "Kayıt sırasında veritabanı hatası oluştu."}), 500


@api_bp.route('/leads', methods=['GET'])
@admin_gerekli
def leadleri_getir():
    try:
        return jsonify({"basari": True, "leads": tum_leadler()}), 200
    except Exception:
        current_app.logger.exception("[GET /api/leads] veritabanı hatası")
        return jsonify({"basari": False, "hata": "Kayıtlar alınırken hata oluştu."}), 500


@api_bp.route('/leads/<int:lead_id>', methods=['DELETE'])
@admin_gerekli
def lead_sil_route(lead_id):
    try:
        if lead_sil(lead_id):
            return jsonify({"basari": True}), 200
        return jsonify({"basari": False, "hata": "Kayıt bulunamadı."}), 404
    except Exception:
        current_app.logger.exception("[DELETE /api/leads] veritabanı hatası")
        return jsonify({"basari": False, "hata": "Silme sırasında hata oluştu."}), 500
