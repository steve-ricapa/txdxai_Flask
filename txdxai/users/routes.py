from flask import request, jsonify
from flask_jwt_extended import jwt_required
from txdxai.users import users_bp
from txdxai.extensions import db
from txdxai.db.models import User
from txdxai.common.errors import ValidationError, NotFoundError, ForbiddenError, ConflictError
from txdxai.common.utils import get_current_user, admin_required, log_audit

@users_bp.route('', methods=['GET'])
@jwt_required()
def get_users():
    user = get_current_user()
    
    users = User.query.filter_by(company_id=user.company_id).all()
    
    return jsonify({
        'users': [u.to_dict() for u in users]
    }), 200


@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user = get_current_user()
    
    user = User.query.get(user_id)
    if not user or user.company_id != current_user.company_id:
        raise NotFoundError('User not found')
    
    return jsonify(user.to_dict()), 200


@users_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_user():
    current_user = get_current_user()
    data = request.get_json()
    
    if not data:
        raise ValidationError('Request body is required')
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'USER')
    
    if not all([username, email, password]):
        raise ValidationError('username, email and password are required')
    
    if role not in ['ADMIN', 'USER']:
        raise ValidationError('role must be ADMIN or USER')
    
    if User.query.filter_by(username=username).first():
        raise ConflictError('Username already exists')
    
    if User.query.filter_by(email=email).first():
        raise ConflictError('Email already exists')
    
    user = User(
        company_id=current_user.company_id,
        username=username,
        email=email,
        role=role
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    log_audit('CREATE', 'USER', user.id, {'username': username, 'role': role})
    
    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201


@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user = get_current_user()
    
    user = User.query.get(user_id)
    if not user or user.company_id != current_user.company_id:
        raise NotFoundError('User not found')
    
    if current_user.role != 'ADMIN' and current_user.id != user_id:
        raise ForbiddenError('Access denied')
    
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')
    
    if 'email' in data:
        if User.query.filter(User.email == data['email'], User.id != user_id).first():
            raise ConflictError('Email already exists')
        user.email = data['email']
    
    if 'password' in data:
        user.set_password(data['password'])
    
    if 'role' in data and current_user.role == 'ADMIN':
        if data['role'] not in ['ADMIN', 'USER']:
            raise ValidationError('role must be ADMIN or USER')
        user.role = data['role']
    
    db.session.commit()
    
    log_audit('UPDATE', 'USER', user.id, {'email': user.email, 'role': user.role})
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    current_user = get_current_user()
    
    user = User.query.get(user_id)
    if not user or user.company_id != current_user.company_id:
        raise NotFoundError('User not found')
    
    if user.id == current_user.id:
        raise ValidationError('Cannot delete yourself')
    
    db.session.delete(user)
    db.session.commit()
    
    log_audit('DELETE', 'USER', user_id, {'username': user.username})
    
    return jsonify({
        'message': 'User deleted successfully'
    }), 200
