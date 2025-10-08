from flask import Flask, jsonify, send_from_directory
from txdxai.config import Config
from txdxai.extensions import db, jwt, migrate, cors
from txdxai.common.errors import handle_error, TxDxAIError
from flasgger import Swagger
import os

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='../basic_frontend')
    app.config.from_object(config_class)
    
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "TxDxAI API",
            "description": "Multi-tenant Cybersecurity and Ticket Automation API",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Authorization: Bearer {token}'"
            }
        },
        "security": [{"Bearer": []}]
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    
    from txdxai.auth import auth_bp
    from txdxai.companies import companies_bp
    from txdxai.users import users_bp
    from txdxai.tickets import tickets_bp
    from txdxai.integrations import integrations_bp
    from txdxai.systems import systems_bp
    from txdxai.alerts import alerts_bp
    from txdxai.vulnerabilities import vulnerabilities_bp
    from txdxai.analytics import analytics_bp
    from txdxai.admin import admin_bp
    from txdxai.agents import agents_bp
    from txdxai.voice import voice_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(integrations_bp)
    app.register_blueprint(systems_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(vulnerabilities_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(voice_bp)
    
    app.register_error_handler(TxDxAIError, handle_error)
    app.register_error_handler(Exception, handle_error)
    
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/script.js')
    def script():
        return send_from_directory(app.static_folder, 'script.js')
    
    @app.route('/favicon.ico')
    def favicon():
        return '', 204
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'}), 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
