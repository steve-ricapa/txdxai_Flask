from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

from txdxai.admin import routes
