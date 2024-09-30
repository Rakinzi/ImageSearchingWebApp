from flask import Blueprint, request, jsonify, render_template, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from flask import current_app as app
from model.users_model import User  # Import User here
from database.db import db  # Import db here if needed
from main import mail  # Import the mail instance from main

users_blueprint = Blueprint('users', __name__)

# Initialize the email serializer
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

@users_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 400

    hashed_password = generate_password_hash(password, method='sha256')
    user = User(username=username, email=email, password=hashed_password)
    db.session.add(user)
    db.session.commit()

    # Send verification email
    token = s.dumps(email, salt='email-confirm')
    link = url_for('users.confirm_email', token=token, _external=True)
    send_email(email, 'Confirm your Email', 'email_verification.html', link=link)

    return jsonify({"message": "Registered successfully, please verify your email."})

@users_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Login failed"}), 401

    if not user.is_verified:
        return jsonify({"message": "Please verify your email before logging in"}), 403

    return jsonify({"message": "Logged in successfully"})

@users_blueprint.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except:
        return jsonify({"message": "The confirmation link is invalid or has expired."}), 400

    user = User.query.filter_by(email=email).first_or_404()

    if user.is_verified:
        return jsonify({"message": "Account already verified."})

    user.is_verified = True
    db.session.commit()

    return jsonify({"message": "Email verified successfully."})

def send_email(to, subject, template, **kwargs):
    msg = Message(subject, recipients=[to], html=render_template(template, **kwargs))
    mail.send(msg)
