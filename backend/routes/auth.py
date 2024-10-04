from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from datetime import datetime
import secrets
from models.user import User, db
from services.email_service import EmailService
import re

auth_bp = Blueprint('auth', __name__)
email_service = EmailService()

def is_valid_email(email):
    # Regular expression to validate email format
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        # Validate input
        if not all(k in data for k in ['email', 'password', 'name']):
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate email format
        if not is_valid_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400

        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409

        # Create user
        user = User(
            email=data['email'],
            name=data['name'],
            verification_token=secrets.token_urlsafe(32),
            verification_token_expires_at=datetime.utcnow() + current_app.config['VERIFICATION_TOKEN_EXPIRES']
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        # Send verification email
        email_service.send_verification_email(
            user.email,
            user.name,
            user.verification_token
        )

        return jsonify({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/verify-email/<token>', methods=['GET'])
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

        return jsonify({'message': 'Email verified successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        if not all(k in data for k in ['email', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400

        user = User.query.filter_by(email=data['email']).first()

        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user.is_verified:
            return jsonify({'error': 'Please verify your email first'}), 403

        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)

        return jsonify({'access_token': access_token}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()

        if 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400

        user = User.query.filter_by(email=data['email']).first()

        if not user:
            # Return success even if user doesn't exist for security
            return jsonify({'message': 'If your email is registered, you will receive a password reset link'}), 200

        # Generate reset token
        user.reset_password_token = secrets.token_urlsafe(32)
        user.reset_token_expires_at = datetime.utcnow() + current_app.config['PASSWORD_RESET_TOKEN_EXPIRES']

        db.session.commit()

        # Send reset email
        email_service.send_password_reset_email(
            user.email,
            user.name,
            user.reset_password_token
        )

        return jsonify({'message': 'If your email is registered, you will receive a password reset link'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    try:
        data = request.get_json()

        if 'new_password' not in data:
            return jsonify({'error': 'New password is required'}), 400

        user = User.query.filter_by(reset_password_token=token).first()

        if not user:
            return jsonify({'error': 'Invalid reset token'}), 400

        if user.reset_token_expires_at < datetime.utcnow():
            return jsonify({'error': 'Reset token has expired'}), 400

        user.set_password(data['new_password'])
        user.reset_password_token = None
        user.reset_token_expires_at = None

        db.session.commit()

        return jsonify({'message': 'Password reset successful'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify(user.to_dict()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    try:
        data = request.get_json()

        if 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400

        user = User.query.filter_by(email=data['email']).first()

        if not user:
            return jsonify({'message': 'If your email is registered, you will receive a verification link'}), 200

        if user.is_verified:
            return jsonify({'error': 'Email is already verified'}), 400

        # Generate new verification token
        user.verification_token = secrets.token_urlsafe(32)
        user.verification_token_expires_at = datetime.utcnow() + current_app.config['VERIFICATION_TOKEN_EXPIRES']

        db.session.commit()

        # Resend verification email
        email_service.send_verification_email(
            user.email,
            user.name,
            user.verification_token
        )

        return jsonify({'message': 'Verification email sent successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500