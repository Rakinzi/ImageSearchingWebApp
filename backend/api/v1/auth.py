from flask import Blueprint, request, jsonify, current_app
from flask_smorest import Blueprint as SmorestBlueprint
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from marshmallow import Schema, fields, validate
from datetime import datetime, timedelta
import secrets

from extensions import db, limiter
from models.user import User
from models.audit_log import AuditLog
from services.email_service import EmailService
from middleware.auth import require_auth
from middleware.audit_logger import AuditLogger
from utils.validators import validate_email, validate_password, ValidationError
from utils.security import sanitize_input

auth_bp = SmorestBlueprint('auth', __name__, description='Authentication operations')
email_service = EmailService()

class RegisterSchema(Schema):
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)

class ResetPasswordSchema(Schema):
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=128))

class UserResponseSchema(Schema):
    id = fields.Int()
    email = fields.Email()
    name = fields.Str()
    is_verified = fields.Bool()
    is_active = fields.Bool()
    last_login_at = fields.DateTime(allow_none=True)
    login_count = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class TokenResponseSchema(Schema):
    access_token = fields.Str()
    refresh_token = fields.Str()
    user = fields.Nested(UserResponseSchema)

@auth_bp.route('/register', methods=['POST'])
@auth_bp.arguments(RegisterSchema)
@auth_bp.response(201, TokenResponseSchema)
@limiter.limit("5 per minute")
def register(json_data):
    try:
        email = json_data['email'].lower().strip()
        password = json_data['password']
        name = sanitize_input(json_data['name'], max_length=100)
        
        is_valid_email, email_or_error = validate_email(email)
        if not is_valid_email:
            AuditLogger.log_login_attempt(
                user_id=None,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                success=False,
                error_message=f"Invalid email: {email_or_error}"
            )
            return jsonify({'error': email_or_error}), 400
        
        is_valid_password, password_errors = validate_password(password)
        if not is_valid_password:
            return jsonify({'error': 'Password requirements not met', 'details': password_errors}), 400
        
        if User.query.filter_by(email=email).first():
            AuditLogger.log_suspicious_activity(
                'duplicate_registration_attempt',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                additional_data={'email': email},
                risk_level='medium'
            )
            return jsonify({'error': 'Email already registered'}), 409
        
        verification_token = secrets.token_urlsafe(32)
        token_expires = datetime.utcnow() + timedelta(hours=24)
        
        user = User(
            email=email,
            name=name,
            verification_token=verification_token,
            verification_token_expires_at=token_expires
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        AuditLogger.log_login_attempt(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            success=True
        )
        
        try:
            email_service.send_verification_email(
                user.email,
                user.name,
                verification_token
            )
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {str(e)}")
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'Registration successful. Please check your email to verify your account.',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
@auth_bp.arguments(LoginSchema)
@auth_bp.response(200, TokenResponseSchema)
@limiter.limit("10 per minute")
def login(json_data):
    try:
        email = json_data['email'].lower().strip()
        password = json_data['password']
        
        user = User.query.filter_by(email=email, is_active=True).first()
        
        if not user or not user.check_password(password):
            AuditLogger.log_login_attempt(
                user_id=user.id if user else None,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                success=False,
                error_message="Invalid credentials"
            )
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_verified:
            return jsonify({
                'error': 'Please verify your email first',
                'needs_verification': True
            }), 403
        
        user.update_login_info()
        
        AuditLogger.log_login_attempt(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            success=True
        )
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@limiter.limit("20 per minute")
def refresh():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'User account is inactive'}), 403
        
        access_token = create_access_token(identity=current_user_id)
        
        return jsonify({'access_token': access_token}), 200
    
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/verify-email/<token>', methods=['GET'])
@limiter.limit("10 per hour")
def verify_email(token):
    try:
        user = User.query.filter_by(verification_token=token).first()
        
        if not user:
            return jsonify({'error': 'Invalid verification token'}), 400
        
        if user.verification_token_expires_at < datetime.utcnow():
            return jsonify({'error': 'Verification token has expired'}), 400
        
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires_at = None
        
        db.session.commit()
        
        AuditLog.log_auth_event(
            'email_verified',
            user_id=user.id,
            ip_address=request.remote_addr,
            status='success'
        )
        
        return jsonify({'message': 'Email verified successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Email verification error: {str(e)}")
        return jsonify({'error': 'Verification failed'}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
@auth_bp.arguments(ForgotPasswordSchema)
@limiter.limit("3 per minute")
def forgot_password(json_data):
    try:
        email = json_data['email'].lower().strip()
        user = User.query.filter_by(email=email, is_active=True).first()
        
        if user:
            reset_token = secrets.token_urlsafe(32)
            user.reset_password_token = reset_token
            user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=1)
            
            db.session.commit()
            
            try:
                email_service.send_password_reset_email(
                    user.email,
                    user.name,
                    reset_token
                )
            except Exception as e:
                current_app.logger.error(f"Failed to send reset email: {str(e)}")
        
        return jsonify({
            'message': 'If your email is registered, you will receive a password reset link'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password reset error: {str(e)}")
        return jsonify({'error': 'Request failed'}), 500

@auth_bp.route('/reset-password/<token>', methods=['POST'])
@auth_bp.arguments(ResetPasswordSchema)
@limiter.limit("5 per hour")
def reset_password(json_data, token):
    try:
        new_password = json_data['new_password']
        
        is_valid_password, password_errors = validate_password(new_password)
        if not is_valid_password:
            return jsonify({'error': 'Password requirements not met', 'details': password_errors}), 400
        
        user = User.query.filter_by(reset_password_token=token).first()
        
        if not user:
            return jsonify({'error': 'Invalid reset token'}), 400
        
        if user.reset_token_expires_at < datetime.utcnow():
            return jsonify({'error': 'Reset token has expired'}), 400
        
        user.set_password(new_password)
        user.reset_password_token = None
        user.reset_token_expires_at = None
        
        db.session.commit()
        
        AuditLogger.log_password_change(
            user_id=user.id,
            ip_address=request.remote_addr,
            success=True
        )
        
        return jsonify({'message': 'Password reset successful'}), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password reset error: {str(e)}")
        return jsonify({'error': 'Password reset failed'}), 500

@auth_bp.route('/me', methods=['GET'])
@require_auth
@limiter.limit("100 per hour")
def get_current_user(current_user):
    return jsonify(current_user.to_dict()), 200

@auth_bp.route('/logout', methods=['POST'])
@require_auth
@limiter.limit("10 per minute")
def logout(current_user):
    try:
        jti = get_jwt()['jti']
        
        AuditLogger.log_logout(
            user_id=current_user.id,
            ip_address=request.remote_addr,
            session_id=jti
        )
        
        return jsonify({'message': 'Logged out successfully'}), 200
    
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/resend-verification', methods=['POST'])
@auth_bp.arguments(ForgotPasswordSchema)
@limiter.limit("3 per hour")
def resend_verification(json_data):
    try:
        email = json_data['email'].lower().strip()
        user = User.query.filter_by(email=email, is_active=True).first()
        
        if not user:
            return jsonify({
                'message': 'If your email is registered, you will receive a verification link'
            }), 200
        
        if user.is_verified:
            return jsonify({'error': 'Email is already verified'}), 400
        
        verification_token = secrets.token_urlsafe(32)
        user.verification_token = verification_token
        user.verification_token_expires_at = datetime.utcnow() + timedelta(hours=24)
        
        db.session.commit()
        
        try:
            email_service.send_verification_email(
                user.email,
                user.name,
                verification_token
            )
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {str(e)}")
        
        return jsonify({'message': 'Verification email sent successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Resend verification error: {str(e)}")
        return jsonify({'error': 'Request failed'}), 500