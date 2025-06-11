from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import mysql

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile')
@login_required
def profile():
    """用户个人信息页面"""
    return render_template('user/profile.html')

@user_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑个人信息"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        
        if not email:
            flash('邮箱不能为空', 'error')
            return render_template('user/edit_profile.html')
        
        cur = mysql.connection.cursor()
        try:
            # 修改：使用正确的表名 users
            cur.execute("SELECT COUNT(*) as count FROM users WHERE email = %s AND user_id != %s", 
                       (email, current_user.id))
            if cur.fetchone()['count'] > 0:
                flash('该邮箱已被其他用户使用', 'error')
                return render_template('user/edit_profile.html')
            
            # 修改：使用正确的表名 users
            cur.execute("""
                UPDATE users SET email = %s, phone = %s 
                WHERE user_id = %s
            """, (email, phone, current_user.id))
            mysql.connection.commit()
            
            # 更新当前用户对象的属性
            current_user.email = email
            current_user.phone = phone
            
            flash('个人信息更新成功', 'success')
            return redirect(url_for('user.profile'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'更新失败: {str(e)}', 'error')
        finally:
            cur.close()
    
    return render_template('user/edit_profile.html')

@user_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not all([current_password, new_password, confirm_password]):
            flash('请填写所有字段', 'error')
            return render_template('user/change_password.html')
        
        if new_password != confirm_password:
            flash('新密码两次输入不一致', 'error')
            return render_template('user/change_password.html')
        
        if len(new_password) < 6:
            flash('新密码长度至少6位', 'error')
            return render_template('user/change_password.html')
        
        # 验证当前密码
        if not current_user.check_password(current_password):
            flash('当前密码不正确', 'error')
            return render_template('user/change_password.html')
        
        cur = mysql.connection.cursor()
        try:
            # 修改：不使用哈希，保持与数据库一致的明文存储
            cur.execute("UPDATE users SET password = %s WHERE user_id = %s", 
                       (new_password, current_user.id))
            mysql.connection.commit()
            flash('密码修改成功', 'success')
            return redirect(url_for('user.profile'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'密码修改失败: {str(e)}', 'error')
        finally:
            cur.close()
    
    return render_template('user/change_password.html')

@user_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """注销账号"""
    password = request.form.get('password', '')
    
    if not password:
        flash('请输入密码确认注销', 'error')
        return redirect(url_for('user.profile'))
    
    if not current_user.check_password(password):
        flash('密码不正确', 'error')
        return redirect(url_for('user.profile'))
    
    cur = mysql.connection.cursor()
    try:
        # 修改：使用正确的表名和字段名
        cur.execute("UPDATE users SET is_deleted = 1 WHERE user_id = %s", (current_user.id,))
        mysql.connection.commit()
        flash('账号已注销', 'info')
        
        from flask_login import logout_user
        logout_user()
        return redirect(url_for('main.index'))
    except Exception as e:
        mysql.connection.rollback()
        flash(f'注销失败: {str(e)}', 'error')
        return redirect(url_for('user.profile'))
    finally:
        cur.close()