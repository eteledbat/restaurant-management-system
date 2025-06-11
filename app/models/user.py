from flask_login import UserMixin
from app import mysql

class User(UserMixin):
    def __init__(self, user_id, username, email, user_type, phone=None, join_date=None):
        self.id = user_id
        self.username = username
        self.email = email
        self.user_type = user_type
        self.phone = phone
        self.join_date = join_date  # 添加这个参数
    
    @staticmethod
    def get(user_id):
        """根据用户ID获取用户对象"""
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE user_id = %s AND is_deleted = 0", (user_id,))
            user_data = cur.fetchone()
            cur.close()
            
            if user_data:
                return User(
                    user_id=user_data['user_id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    user_type=user_data['user_type'],
                    phone=user_data.get('phone'),
                    join_date=user_data.get('join_date')
                )
            return None
        except Exception as e:
            print(f"获取用户失败: {e}")
            return None
    
    @staticmethod
    def get_by_username(username):
        """根据用户名获取用户对象"""
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE username = %s AND is_deleted = 0", (username,))
            user_data = cur.fetchone()
            cur.close()
            
            if user_data:
                return User(
                    user_id=user_data['user_id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    user_type=user_data['user_type'],
                    phone=user_data.get('phone'),
                    join_date=user_data.get('join_date')
                )
            return None
        except Exception as e:
            print(f"根据用户名获取用户失败: {e}")
            return None
    
    @staticmethod
    def get_by_email(email):
        """根据邮箱获取用户对象"""
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE email = %s AND is_deleted = 0", (email,))
            user_data = cur.fetchone()
            cur.close()
            
            if user_data:
                return User(
                    user_id=user_data['user_id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    user_type=user_data['user_type'],
                    phone=user_data.get('phone'),
                    join_date=user_data.get('join_date')
                )
            return None
        except Exception as e:
            print(f"根据邮箱获取用户失败: {e}")
            return None
    
    def check_password(self, password):
        """验证密码"""
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT password FROM users WHERE user_id = %s", (self.id,))
            result = cur.fetchone()
            cur.close()
            
            if result:
                stored_password = result['password']
                print(f"调试信息 - 用户: {self.username}, 输入密码: '{password}', 存储密码: '{stored_password}'")
                return stored_password == password
            return False
        except Exception as e:
            print(f"密码验证失败: {e}")
            return False
    
    @staticmethod
    def create(username, password, email, phone=None, user_type='user'):
        """创建新用户"""
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO users (username, email, password, user_type, phone, is_deleted)
                VALUES (%s, %s, %s, %s, %s, 0)
            """, (username, email, password, user_type, phone))
            mysql.connection.commit()
            user_id = cur.lastrowid
            cur.close()
            
            return User.get(user_id)
        except Exception as e:
            mysql.connection.rollback()
            raise Exception(f"创建用户失败: {str(e)}")
    
    def get_id(self):
        """Flask-Login要求的方法"""
        return str(self.id)
    
    def is_admin(self):
        """检查是否为管理员"""
        return self.user_type == 'admin'
    
    def is_merchant(self):
        """检查是否为商家"""
        return self.user_type == 'merchant'
    
    def is_customer(self):
        """检查是否为顾客"""
        return self.user_type == 'user'
    
    def __repr__(self):
        return f'<User {self.username}>'