from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from app.models.user import User  
from app import mysql
from app.utils import validate_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"登录尝试 - 用户名: {username}, 密码: {password}")  # 调试信息
        
        if not username or not password:
            flash('请填写用户名和密码', 'danger')
            return render_template('auth/login.html')
        
        user = User.get_by_username(username)
        print(f"找到用户: {user}")  # 调试信息
        
        if not user or not user.check_password(password):
            flash('用户名或密码错误', 'danger')
            return render_template('auth/login.html')
        
        login_user(user)
        flash('登录成功!', 'success')
        
        # 根据用户类型重定向
        if user.is_admin():
            return redirect(url_for('admin.dashboard'))
        else:
            # 商家和普通用户都跳转到首页
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        email = request.form.get('email')
        phone = request.form.get('phone')
        user_type = request.form.get('user_type', 'user')  # 修改：默认为 'user'
        
        # 表单验证
        error = None
        
        if not username or not password or not confirm or not email:
            error = '请填写所有必填字段'
        elif password != confirm:
            error = '两次密码输入不一致'
        elif not validate_email(email):
            error = '邮箱格式不正确'
        elif User.get_by_username(username):
            error = '该用户名已被使用'
        elif User.get_by_email(email):
            error = '该邮箱已被使用'
        
        if error:
            flash(error, 'danger')
            return render_template('auth/register.html')
        
        # 创建用户
        try:
            User.create(username, password, email, phone, user_type)
            flash('注册成功，请登录', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'注册失败: {str(e)}', 'danger')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功退出登录!', 'info')
    return redirect(url_for('main.index'))