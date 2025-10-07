from flask import Blueprint

integrations_bp = Blueprint('integrations', __name__, url_prefix='/api/integrations')

from txdxai.integrations import routes
