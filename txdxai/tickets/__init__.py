from flask import Blueprint

tickets_bp = Blueprint('tickets', __name__, url_prefix='/api/tickets')

from txdxai.tickets import routes
