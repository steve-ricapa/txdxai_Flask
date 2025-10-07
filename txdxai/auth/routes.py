from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from txdxai.auth import auth_bp
from txdxai.extensions import db
from txdxai.db.models import User, Company
from txdxai.common.errors import ValidationError, UnauthorizedError, ConflictError
from txdxai.common.utils import log_audit

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        raise ValidationError('Request body is required')
    
    company_name = data.get('company_name')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([company_name, username, email, password]):
        raise ValidationError('company_name, username, email and password are required')
    
    if User.query.filter_by(username=username).first():
        raise ConflictError('Username already exists')
    
    if User.query.filter_by(email=email).first():
        raise ConflictError('Email already exists')
    
    company = Company.query.filter_by(name=company_name).first()
    if not company:
        company = Company(name=company_name)
        db.session.add(company)
        db.session.flush()
    
    user = User(
        company_id=company.id,
        username=username,
        email=email,
        role='ADMIN'
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    log_audit('REGISTER', 'USER', user.id, {'username': username, 'role': 'ADMIN'})
    
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'message': 'Admin user registered successfully',
        'user': user.to_dict(include_company=True),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        raise ValidationError('Request body is required')
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        raise ValidationError('username and password are required')
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        raise UnauthorizedError('Invalid username or password')
    
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    log_audit('LOGIN', 'USER', user.id)
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(include_company=True),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200
