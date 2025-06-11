import os

class Config:
    # 数据库配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'e8274a7f4d34e4d1e1b69e6e9a0c9bcb073c9f4db13d38e8f7c5c973fa58e2c1'
    
    # MySQL 配置
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '2019010911Cyh__'  # 替换为你的密码
    MYSQL_DB = 'restaurant_db'
    MYSQL_CURSORCLASS = 'DictCursor'  # 使结果以字典形式返回
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 限制上传大小为16MB
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = 1800  # 30分钟