from flask import Blueprint

systems_bp = Blueprint('systems', __name__, url_prefix='/api/systems')

from txdxai.systems import routes
