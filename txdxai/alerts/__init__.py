from flask import Blueprint

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

from txdxai.alerts import routes
