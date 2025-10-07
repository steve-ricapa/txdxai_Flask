from flask import Blueprint

vulnerabilities_bp = Blueprint('vulnerabilities', __name__, url_prefix='/api/vulnerabilities')

from txdxai.vulnerabilities import routes
