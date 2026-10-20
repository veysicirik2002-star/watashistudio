import logging
import sys

from flask import Flask, jsonify
from flask_cors import CORS

from config import config_by_name
from app.database import init_db
from app.error_log import son_hatalar
from app.routes import api_bp


def create_app(config_name='development'):
    """Uygulama fabrikası: ayarları, loglamayı, veritabanını ve rotaları birleştirir."""
    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['development']))
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})

    # Hatalar hem terminale/Render loglarına hem /api/hatalar'a düşer
    terminal = logging.StreamHandler(sys.stdout)
    terminal.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    son_hatalar.setFormatter(logging.Formatter('%(message)s'))
    app.logger.handlers = [terminal, son_hatalar]
    app.logger.setLevel(logging.INFO)

    with app.app_context():
        init_db(app)

    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"durum": "aktif", "basari": True}), 200

    @app.errorhandler(404)
    def bulunamadi(e):
        return jsonify({"basari": False, "hata": "Adres bulunamadı."}), 404

    @app.errorhandler(405)
    def metod_yok(e):
        return jsonify({"basari": False, "hata": "Bu adres bu yöntemi desteklemiyor."}), 405

    @app.errorhandler(Exception)
    def beklenmeyen(e):
        app.logger.exception("Beklenmeyen hata")
        return jsonify({"basari": False, "hata": "Beklenmeyen bir sunucu hatası oluştu."}), 500

    return app
