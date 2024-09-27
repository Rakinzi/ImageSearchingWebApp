from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from controller.models import User 
from werkzeug.security import check_password_hash, generate_password_hash

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')
    
    # Query user by email
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Invalid credentials"}), 401

@auth_blueprint.route('/register', methods=['POST'])
def register():
    email = request.json.get('email')
    password = request.json.get('password')
    hashed_password = generate_password_hash(password)
    
    new_user = User(email=email, password=hashed_password)
    new_user.save()  # Assuming your model has a save method
    return jsonify({"msg": "User registered"}), 201

@auth_blueprint.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify({"email": user.email}), 200
