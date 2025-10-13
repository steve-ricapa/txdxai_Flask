from flask import Blueprint

chat_bp = Blueprint('chat', __name__, url_prefix='/api')

from txdxai.chat import routes
