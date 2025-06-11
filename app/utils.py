import re
import os
import uuid
from flask import current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

def validate_email(email):
    """验证邮箱格式是否正确"""
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(pattern, email):
        return False
    return True

def allowed_file(filename):
    """检查文件扩展名是否允许上传"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_image(file, folder='general'):
    """保存上传的图片"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        target_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
            
        file_path = os.path.join(target_folder, unique_filename)
        file.save(file_path)
        
        # 返回相对于static文件夹的路径
        return f"/static/uploads/{folder}/{unique_filename}"
        
    return None

def is_admin():
    """检查当前用户是否是管理员"""
    return current_user.is_authenticated and current_user.user_type == 'admin'

def is_merchant():
    """检查当前用户是否是商家"""
    return current_user.is_authenticated and current_user.user_type == 'merchant'

def is_regular_user():
    """检查当前用户是否是普通用户"""
    return current_user.is_authenticated and current_user.user_type == 'user'