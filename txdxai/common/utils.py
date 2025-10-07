from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from txdxai.common.errors import UnauthorizedError, ForbiddenError
from txdxai.db.models import User

def get_current_user():
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        raise UnauthorizedError('User not found')
    return user


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user.role != 'ADMIN':
            raise ForbiddenError('Admin access required')
        return fn(*args, **kwargs)
    return wrapper


def same_company_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        company_id = kwargs.get('company_id')
        if company_id and user.company_id != int(company_id):
            raise ForbiddenError('Access denied to different company resources')
        return fn(*args, **kwargs)
    return wrapper


def log_audit(action, entity_type, entity_id=None, payload=None):
    from txdxai.extensions import db
    from txdxai.db.models import AuditLog
    
    try:
        user = get_current_user()
        audit = AuditLog(
            actor_user_id=user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload
        )
        db.session.add(audit)
        db.session.commit()
    except:
        pass
