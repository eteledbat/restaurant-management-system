from app import mysql, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM Users WHERE user_id = %s AND is_deleted = FALSE", (user_id,))
        user = cur.fetchone()
        if user:
            return User(user)
        return None
    finally:
        cur.close()

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['user_id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.phone = user_data['phone']
        self.user_type = user_data['user_type']
        self.join_date = user_data['join_date']
        self.is_deleted = user_data['is_deleted']
    
    def get_id(self):
        return str(self.id)
    
    @staticmethod
    def get_by_username(username):
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM Users WHERE username = %s AND is_deleted = FALSE", (username,))
            user_data = cur.fetchone()
            if user_data:
                return User(user_data)
            return None
        finally:
            cur.close()
    
    @staticmethod
    def create(username, password, email, phone, user_type='user'):
        cur = mysql.connection.cursor()
        try:
            hashed_password = generate_password_hash(password)
            cur.execute("""
                INSERT INTO Users (username, password, email, phone, user_type)
                VALUES (%s, %s, %s, %s, %s)
            """, (username, hashed_password, email, phone, user_type))
            mysql.connection.commit()
            return cur.lastrowid
        finally:
            cur.close()
    
    def check_password(self, password):
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT password FROM Users WHERE user_id = %s", (self.id,))
            hashed_password = cur.fetchone()['password']
            return check_password_hash(hashed_password, password)
        finally:
            cur.close()

class Restaurant:
    @staticmethod
    def get_all():
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM Restaurants ORDER BY name")
            return cur.fetchall()
        finally:
            cur.close()
    
    @staticmethod
    def get_by_id(rest_id):
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM Restaurants WHERE rest_id = %s", (rest_id,))
            return cur.fetchone()
        finally:
            cur.close()
    
    @staticmethod
    def get_top_rated(limit=5):
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM Restaurants ORDER BY rating DESC LIMIT %s", (limit,))
            return cur.fetchall()
        finally:
            cur.close()

# 添加其他模型...