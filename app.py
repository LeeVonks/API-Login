from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
import jwt
import datetime
from functools import wraps
import hashlib
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Konfigurasi MySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Fungsi untuk menghasilkan token JWT
def generate_token(user_id):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id
    }
    token = jwt.encode(payload, os.getenv('SECRET_KEY'), algorithm='HS256')
    return token

# Fungsi dekorator untuk memastikan pengguna terotentikasi
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=['HS256'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(*args, **kwargs)

    return decorated

# API Register
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data['email']
    password = data['password']
    address = data['address']
    age = data['age']

    # Cek apakah email sudah ada
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    if user:
        return jsonify({'message': 'Email sudah terdaftar!'}), 400

    # Enkripsi password menggunakan hashlib
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (email, password, address, age) VALUES (%s, %s, %s, %s)", (email, hashed_password, address, age))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'User registered successfully!'}), 201

# API Login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    # Enkripsi password menggunakan hashlib
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, email, password FROM users WHERE email = %s AND password = %s", (email, hashed_password))
    user = cur.fetchone()
    cur.close()

    if user:
        token = generate_token(user['id'])
        return jsonify({'token': token}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401

# Contoh API yang memerlukan autentikasi
@app.route('/protected', methods=['GET'])
@token_required
def protected():
    return jsonify({'message': 'This is a protected route!'})

if __name__ == '__main__':
    app.run(debug=True)
