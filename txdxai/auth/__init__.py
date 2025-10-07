from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

from txdxai.auth import routes
