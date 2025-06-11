from flask import Flask, g, render_template
from flask_login import LoginManager
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
import secrets
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 全局变量
mysql = MySQL()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'e8274a7f4d34e4d1e1b69e6e9a0c9bcb073c9f4db13d38e8f7c5c973fa58e2c1')
    
    # MySQL配置
    app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
    app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
    app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
    app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'restaurant_db')
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    
    # 文件上传配置
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    
    # 初始化扩展
    mysql.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Flask-Login配置
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'info'
    
    # 用户加载器
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.get(user_id)
    
    # 添加全局上下文处理器
    @app.context_processor
    def inject_categories():
        """为所有模板提供分类数据"""
        try:
            from app import mysql
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT category_id, category_name 
                FROM restaurantcategories 
                WHERE is_active = 1 
                ORDER BY category_name 
                LIMIT 10
            """)
            nav_categories = cur.fetchall()
            cur.close()
            return {'nav_categories': nav_categories}
        except:
            return {'nav_categories': []}
    # 注册蓝图
    try:
        from app.routes.main import main_bp
        app.register_blueprint(main_bp)
        print("Successfully imported main_bp")
    except ImportError as e:
        print(f"Warning: Could not import main_bp: {e}")
    
    try:
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        print("Successfully imported auth_bp")
    except ImportError as e:
        print(f"Warning: Could not import auth_bp: {e}")
    
    try:
        from app.routes.user import user_bp
        app.register_blueprint(user_bp, url_prefix='/user')
        print("Successfully imported user_bp")
    except ImportError as e:
        print(f"Warning: Could not import user_bp: {e}")
    
    try:
        from app.routes.restaurants import restaurant_bp
        app.register_blueprint(restaurant_bp, url_prefix='/restaurant')
        print("Successfully imported restaurant_bp")
    except ImportError as e:
        print(f"Warning: Could not import restaurant_bp: {e}")
    
    try:
        from app.routes.merchant import merchant_bp
        app.register_blueprint(merchant_bp, url_prefix='/merchant')
        print("Successfully imported merchant_bp")
    except ImportError as e:
        print(f"Warning: Could not import merchant_bp: {e}")
    
    try:
        from app.routes.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        print("Successfully imported admin_bp")
    except ImportError as e:
        print(f"Warning: Could not import admin_bp: {e}")
# 在现有蓝图注册代码后添加：
    try:
        from app.routes.reviews import review_bp
        app.register_blueprint(review_bp, url_prefix='/review')
        print("Successfully imported review_bp")
    except ImportError as e:
        print(f"Warning: Could not import review_bp: {e}")
    
    # 安全头设置
    @app.after_request
    def add_security_headers(response):
        if app.debug:
            # 开发环境放宽CSP限制
            response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:"
        
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    # 错误处理
    @app.errorhandler(404)
    def not_found_error(error):
        try:
            return render_template('errors/404.html'), 404
        except:
            return '<h1>404 - 页面未找到</h1>', 404
    
    @app.errorhandler(500)
    def internal_error(error):
        try:
            return render_template('errors/500.html'), 500
        except:
            return '<h1>500 - 服务器错误</h1>', 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        try:
            return render_template('errors/403.html'), 403
        except:
            return '<h1>403 - 访问被拒绝</h1>', 403
    
    # 创建上传目录
    upload_dir = os.path.join(app.root_path, 'static', 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    return app