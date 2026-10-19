from flask import Flask, jsonify
from flask_cors import CORS
from config import config_by_name
from app.database import init_db
from app.routes import pages_bp, api_bp

def create_app(config_name='development'):
    """Uygulama fabrikası: Ayarları, veritabanını ve rotaları birleştirir."""
    app = Flask(__name__)
    
    app.config.from_object(config_by_name.get(config_name, config_by_name['development']))
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
    
    with app.app_context():
        init_db(app)
        
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"durum": "aktif", "basari": True}), 200
        
    return app
