from flask import Blueprint

companies_bp = Blueprint('companies', __name__, url_prefix='/api/companies')

from txdxai.companies import routes
