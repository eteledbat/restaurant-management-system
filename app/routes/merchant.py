from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import mysql
import os
from werkzeug.utils import secure_filename
from flask import current_app

# 在文件顶部添加允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


merchant_bp = Blueprint('merchant', __name__)

@merchant_bp.route('/my_restaurants')
@login_required
def my_restaurants():
    """我的餐厅列表"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以查看管理的餐厅', 'error')
        return redirect(url_for('main.index'))
    
    cur = mysql.connection.cursor()
    try:
        # 获取该商家管理的所有餐厅 - 修复字段名
        cur.execute("""
            SELECT r.*, 
                   COALESCE(AVG(rv.rating), 0) as avg_rating,
                   COUNT(rv.review_id) as review_count
            FROM Restaurants r
            JOIN MerchantRestaurant mr ON r.rest_id = mr.restaurant_id
            LEFT JOIN Reviews rv ON r.rest_id = rv.rest_id
            WHERE mr.merchant_id = %s
            GROUP BY r.rest_id, r.name, r.address, r.phone, r.opening_hours, r.type, r.img_url, r.rating, r.review_count, r.star_count
            ORDER BY r.name
        """, (current_user.id,))
        
        restaurants = cur.fetchall()
        return render_template('merchant/my_restaurants.html', restaurants=restaurants)
    finally:
        cur.close()

@merchant_bp.route('/manage_dishes')
@login_required
def manage_dishes():
    """管理菜品"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以访问此页面', 'error')
        return redirect(url_for('main.index'))
    
    cur = mysql.connection.cursor()
    try:
        # 获取商家的所有餐厅和菜品
        cur.execute("""
            SELECT r.rest_id, r.name as restaurant_name,
                   d.dish_id, d.name as dish_name, d.price, d.description, d.img_url,
                   COALESCE(COUNT(rec.user_id), 0) as rec_count
            FROM Restaurants r
            JOIN MerchantRestaurant mr ON r.rest_id = mr.restaurant_id
            LEFT JOIN Dishes d ON r.rest_id = d.rest_id
            LEFT JOIN Recommendations rec ON d.dish_id = rec.dish_id
            WHERE mr.merchant_id = %s
            GROUP BY r.rest_id, d.dish_id
            ORDER BY r.name, d.name
        """, (current_user.id,))
        dishes_data = cur.fetchall()
        
        # 获取商家的餐厅列表（用于添加新菜品）
        cur.execute("""
            SELECT r.rest_id, r.name
            FROM Restaurants r
            JOIN MerchantRestaurant mr ON r.rest_id = mr.restaurant_id
            WHERE mr.merchant_id = %s
            ORDER BY r.name
        """, (current_user.id,))
        restaurants = cur.fetchall()
        
        return render_template('merchant/manage_dishes.html', dishes_data=dishes_data, restaurants=restaurants)
    finally:
        cur.close()

@merchant_bp.route('/add_dish', methods=['POST'])
@login_required
def add_dish():
    """添加菜品"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以添加菜品', 'error')
        return redirect(url_for('main.index'))
    
    rest_id = request.form.get('rest_id', type=int)
    name = request.form.get('name', '').strip()
    price = request.form.get('price', type=float)
    description = request.form.get('description', '').strip()
    
    if not all([rest_id, name, price]):
        flash('请填写所有必需字段', 'error')
        return redirect(url_for('merchant.manage_dishes'))
    
    # 处理图片上传
    img_url = None
    if 'dish_image' in request.files:
        file = request.files['dish_image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 生成唯一文件名
            import uuid
            unique_filename = str(uuid.uuid4()) + '.' + filename.rsplit('.', 1)[1].lower()
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            img_url = url_for('static', filename='uploads/' + unique_filename)
    
    cur = mysql.connection.cursor()
    try:
        # 验证餐厅是否属于当前商家
        cur.execute("""
            SELECT COUNT(*) as count FROM MerchantRestaurant 
            WHERE merchant_id = %s AND restaurant_id = %s
        """, (current_user.id, rest_id))
        
        if cur.fetchone()['count'] == 0:
            flash('您无权在该餐厅添加菜品', 'error')
            return redirect(url_for('merchant.manage_dishes'))
        
        # 添加菜品
        cur.execute("""
            INSERT INTO Dishes (rest_id, name, price, description, img_url)
            VALUES (%s, %s, %s, %s, %s)
        """, (rest_id, name, price, description, img_url))
        mysql.connection.commit()
        flash('菜品添加成功', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'添加失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('merchant.manage_dishes'))

@merchant_bp.route('/edit_dish/<int:dish_id>')
@login_required
def edit_dish(dish_id):
    """编辑菜品页面"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以编辑菜品', 'error')
        return redirect(url_for('main.index'))
    
    cur = mysql.connection.cursor()
    try:
        # 获取菜品信息并验证权限
        cur.execute("""
            SELECT d.*, r.name as restaurant_name
            FROM Dishes d
            JOIN Restaurants r ON d.rest_id = r.rest_id
            JOIN MerchantRestaurant mr ON r.rest_id = mr.restaurant_id
            WHERE d.dish_id = %s AND mr.merchant_id = %s
        """, (dish_id, current_user.id))
        
        dish = cur.fetchone()
        if not dish:
            flash('菜品不存在或您无权编辑', 'error')
            return redirect(url_for('merchant.manage_dishes'))
        
        return render_template('merchant/edit_dish.html', dish=dish)
    finally:
        cur.close()

@merchant_bp.route('/update_dish/<int:dish_id>', methods=['POST'])
@login_required
def update_dish(dish_id):
    """更新菜品信息"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以编辑菜品', 'error')
        return redirect(url_for('main.index'))
    
    name = request.form.get('name', '').strip()
    price = request.form.get('price', type=float)
    description = request.form.get('description', '').strip()
    
    if not all([name, price]):
        flash('请填写所有必需字段', 'error')
        return redirect(url_for('merchant.edit_dish', dish_id=dish_id))
    
    cur = mysql.connection.cursor()
    try:
        # 验证权限并获取当前菜品信息
        cur.execute("""
            SELECT d.img_url
            FROM Dishes d
            JOIN Restaurants r ON d.rest_id = r.rest_id
            JOIN MerchantRestaurant mr ON r.rest_id = mr.restaurant_id
            WHERE d.dish_id = %s AND mr.merchant_id = %s
        """, (dish_id, current_user.id))
        
        dish = cur.fetchone()
        if not dish:
            flash('菜品不存在或您无权编辑', 'error')
            return redirect(url_for('merchant.manage_dishes'))
        
        # 处理图片上传
        img_url = dish['img_url']  # 保持原有图片
        if 'dish_image' in request.files:
            file = request.files['dish_image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # 生成唯一文件名
                import uuid
                unique_filename = str(uuid.uuid4()) + '.' + filename.rsplit('.', 1)[1].lower()
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                img_url = url_for('static', filename='uploads/' + unique_filename)
        
        # 更新菜品
        cur.execute("""
            UPDATE Dishes 
            SET name = %s, price = %s, description = %s, img_url = %s
            WHERE dish_id = %s
        """, (name, price, description, img_url, dish_id))
        mysql.connection.commit()
        flash('菜品更新成功', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'更新失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('merchant.manage_dishes'))

@merchant_bp.route('/delete_dish/<int:dish_id>', methods=['POST'])
@login_required
def delete_dish(dish_id):
    """删除菜品"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以删除菜品', 'error')
        return redirect(url_for('main.index'))
    
    cur = mysql.connection.cursor()
    try:
        # 验证权限
        cur.execute("""
            SELECT d.name
            FROM Dishes d
            JOIN Restaurants r ON d.rest_id = r.rest_id
            JOIN MerchantRestaurant mr ON r.rest_id = mr.restaurant_id
            WHERE d.dish_id = %s AND mr.merchant_id = %s
        """, (dish_id, current_user.id))
        
        dish = cur.fetchone()
        if not dish:
            flash('菜品不存在或您无权删除', 'error')
            return redirect(url_for('merchant.manage_dishes'))
        
        # 删除菜品
        cur.execute("DELETE FROM Dishes WHERE dish_id = %s", (dish_id,))
        mysql.connection.commit()
        flash(f'菜品 "{dish["name"]}" 删除成功', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'删除失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('merchant.manage_dishes'))

# 查看和管理回复
@merchant_bp.route('/replies')
@login_required
def replies():
    """查看和管理回复"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以查看回复', 'error')
        return redirect(url_for('main.index'))
    
    cur = mysql.connection.cursor()
    try:
        # 获取该商家管理的餐厅的所有评论和回复
        cur.execute("""
            SELECT rv.review_id, rv.rating, rv.comment as review_text, rv.timestamp as review_date,
                   u.username as reviewer_name,
                   rest.name as restaurant_name, rest.rest_id,
                   r.reply_id, r.content as reply_text, r.reply_time as reply_date
            FROM Reviews rv
            JOIN Restaurants rest ON rv.rest_id = rest.rest_id
            JOIN MerchantRestaurant mr ON rest.rest_id = mr.restaurant_id
            LEFT JOIN Users u ON rv.user_id = u.user_id
            LEFT JOIN Replies r ON rv.review_id = r.review_id
            WHERE mr.merchant_id = %s
            ORDER BY rv.timestamp DESC
        """, (current_user.id,))
        
        reviews = cur.fetchall()
        return render_template('merchant/replies.html', reviews=reviews)
    finally:
        cur.close()

@merchant_bp.route('/edit_reply/<int:reply_id>')
@login_required
def edit_reply(reply_id):
    """编辑回复页面"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以编辑回复', 'error')
        return redirect(url_for('main.index'))
    
    cur = mysql.connection.cursor()
    try:
        # 获取回复信息，包含原始评论信息
        cur.execute("""
            SELECT r.reply_id, r.content as reply_text, r.reply_time as created_at, r.updated_at,
                   rv.review_id, rv.rating, rv.comment as review_text, rv.timestamp as review_date,
                   u.username as reviewer_name,
                   rest.name as restaurant_name, rest.rest_id
            FROM Replies r
            JOIN Reviews rv ON r.review_id = rv.review_id
            JOIN Restaurants rest ON rv.rest_id = rest.rest_id
            JOIN MerchantRestaurant mr ON rest.rest_id = mr.restaurant_id
            LEFT JOIN Users u ON rv.user_id = u.user_id
            WHERE r.reply_id = %s AND mr.merchant_id = %s
        """, (reply_id, current_user.id))
        
        reply = cur.fetchone()
        if not reply:
            flash('回复不存在或您无权编辑', 'error')
            return redirect(url_for('merchant.replies'))
        
        return render_template('merchant/edit_reply.html', reply=reply)
    finally:
        cur.close()

# 更新回复
@merchant_bp.route('/update_reply/<int:reply_id>', methods=['POST'])
@login_required
def update_reply(reply_id):
    """更新回复"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以编辑回复', 'error')
        return redirect(url_for('main.index'))
    
    reply_text = request.form.get('reply_text', '').strip()
    
    if not reply_text:
        flash('回复内容不能为空', 'error')
        return redirect(url_for('merchant.edit_reply', reply_id=reply_id))
    
    if len(reply_text) > 1000:
        flash('回复内容不能超过1000个字符', 'error')
        return redirect(url_for('merchant.edit_reply', reply_id=reply_id))
    
    cur = mysql.connection.cursor()
    try:
        # 验证权限：确保这个回复是对该商家管理的餐厅的评论的回复
        cur.execute("""
            SELECT r.reply_id, rest.rest_id, rest.name as restaurant_name
            FROM Replies r
            JOIN Reviews rv ON r.review_id = rv.review_id
            JOIN Restaurants rest ON rv.rest_id = rest.rest_id
            JOIN MerchantRestaurant mr ON rest.rest_id = mr.restaurant_id
            WHERE r.reply_id = %s AND mr.merchant_id = %s
        """, (reply_id, current_user.id))
        
        reply = cur.fetchone()
        if not reply:
            flash('回复不存在或您无权编辑', 'error')
            return redirect(url_for('merchant.replies'))
        
        # 更新回复
        cur.execute("""
            UPDATE Replies 
            SET content = %s, updated_at = CURRENT_TIMESTAMP
            WHERE reply_id = %s
        """, (reply_text, reply_id))
        
        mysql.connection.commit()
        flash('回复更新成功', 'success')
        return redirect(url_for('merchant.replies'))
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'更新失败: {str(e)}', 'error')
        return redirect(url_for('merchant.edit_reply', reply_id=reply_id))
    finally:
        cur.close()

# 添加新回复
@merchant_bp.route('/add_reply', methods=['POST'])
@login_required
def add_reply():
    """添加回复"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以添加回复', 'error')
        return redirect(url_for('main.index'))
    
    review_id = request.form.get('review_id')
    reply_content = request.form.get('reply_content', '').strip()
    
    if not review_id or not reply_content:
        flash('回复内容不能为空', 'error')
        return redirect(url_for('merchant.replies'))
    
    if len(reply_content) > 1000:
        flash('回复内容不能超过1000个字符', 'error')
        return redirect(url_for('merchant.replies'))
    
    cur = mysql.connection.cursor()
    try:
        # 验证权限：确保这个评论是对该商家管理的餐厅的评论
        cur.execute("""
            SELECT rv.review_id, rest.name as restaurant_name
            FROM Reviews rv
            JOIN Restaurants rest ON rv.rest_id = rest.rest_id
            JOIN MerchantRestaurant mr ON rest.rest_id = mr.restaurant_id
            WHERE rv.review_id = %s AND mr.merchant_id = %s
        """, (review_id, current_user.id))
        
        review = cur.fetchone()
        if not review:
            flash('评论不存在或您无权回复', 'error')
            return redirect(url_for('merchant.replies'))
        
        # 检查是否已经回复过
        cur.execute("SELECT reply_id FROM Replies WHERE review_id = %s", (review_id,))
        existing_reply = cur.fetchone()
        
        if existing_reply:
            flash('您已经回复过这条评论了', 'warning')
            return redirect(url_for('merchant.replies'))
        
        # 添加回复
        cur.execute("""
            INSERT INTO Replies (review_id, content, reply_time)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
        """, (review_id, reply_content))
        
        mysql.connection.commit()
        flash('回复发送成功', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'回复失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('merchant.replies'))

# 删除回复
@merchant_bp.route('/delete_reply/<int:reply_id>', methods=['POST'])
@login_required
def delete_reply(reply_id):
    """删除回复"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以删除回复', 'error')
        return redirect(url_for('main.index'))
    
    cur = mysql.connection.cursor()
    try:
        # 验证权限：确保这个回复是该商家的
        cur.execute("""
            SELECT r.reply_id, rest.name as restaurant_name
            FROM Replies r
            JOIN Reviews rv ON r.review_id = rv.review_id
            JOIN Restaurants rest ON rv.rest_id = rest.rest_id
            JOIN MerchantRestaurant mr ON rest.rest_id = mr.restaurant_id
            WHERE r.reply_id = %s AND mr.merchant_id = %s
        """, (reply_id, current_user.id))
        
        reply = cur.fetchone()
        if not reply:
            flash('回复不存在或您无权删除', 'error')
            return redirect(url_for('merchant.replies'))
        
        # 删除回复
        cur.execute("DELETE FROM Replies WHERE reply_id = %s", (reply_id,))
        
        mysql.connection.commit()
        flash('回复删除成功', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'删除失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('merchant.replies'))

# 路由别名（兼容性）
@merchant_bp.route('/manage_replies')
@login_required
def manage_replies():
    """管理回复的别名路由（重定向到replies）"""
    return redirect(url_for('merchant.replies'))

@merchant_bp.route('/edit_restaurant/<int:rest_id>')
@login_required
def edit_restaurant(rest_id):
    """编辑餐厅信息页面"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以编辑餐厅信息', 'error')
        return redirect(url_for('main.index'))
    
    cur = mysql.connection.cursor()
    try:
        # 验证商家权限并获取餐厅信息
        cur.execute("""
            SELECT r.*
            FROM Restaurants r
            JOIN MerchantRestaurant mr ON r.rest_id = mr.restaurant_id
            WHERE r.rest_id = %s AND mr.merchant_id = %s
        """, (rest_id, current_user.id))
        
        restaurant = cur.fetchone()
        if not restaurant:
            flash('餐厅不存在或您无权编辑', 'error')
            return redirect(url_for('merchant.my_restaurants'))
        
        return render_template('merchant/edit_restaurant.html', restaurant=restaurant)
    finally:
        cur.close()

@merchant_bp.route('/update_restaurant/<int:rest_id>', methods=['POST'])
@login_required
def update_restaurant(rest_id):
    """更新餐厅信息"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以编辑餐厅信息', 'error')
        return redirect(url_for('main.index'))
    
    name = request.form.get('name', '').strip()
    address = request.form.get('address', '').strip()
    phone = request.form.get('phone', '').strip()
    opening_hours = request.form.get('opening_hours', '').strip()
    restaurant_type = request.form.get('type', '').strip()
    
    if not all([name, address, restaurant_type]):
        flash('请填写所有必需字段', 'error')
        return redirect(url_for('merchant.edit_restaurant', rest_id=rest_id))
    
    cur = mysql.connection.cursor()
    try:
        # 验证权限
        cur.execute("""
            SELECT r.img_url
            FROM Restaurants r
            JOIN MerchantRestaurant mr ON r.rest_id = mr.restaurant_id
            WHERE r.rest_id = %s AND mr.merchant_id = %s
        """, (rest_id, current_user.id))
        
        restaurant = cur.fetchone()
        if not restaurant:
            flash('餐厅不存在或您无权编辑', 'error')
            return redirect(url_for('merchant.my_restaurants'))
        
        # 处理图片上传
        img_url = restaurant['img_url']  # 保持原有图片
        if 'restaurant_image' in request.files:
            file = request.files['restaurant_image']
            if file and file.filename != '' and allowed_file(file.filename):
                # 删除旧图片（如果存在且不是默认图片）
                if img_url and img_url.startswith('/static/uploads/'):
                    old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                               img_url.split('/')[-1])
                    if os.path.exists(old_file_path):
                        try:
                            os.remove(old_file_path)
                        except:
                            pass  # 忽略删除失败
                
                # 保存新图片
                filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + '.' + filename.rsplit('.', 1)[1].lower()
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                img_url = url_for('static', filename='uploads/' + unique_filename)
        
        # 更新餐厅信息
        cur.execute("""
            UPDATE Restaurants 
            SET name = %s, address = %s, phone = %s, opening_hours = %s, type = %s, img_url = %s
            WHERE rest_id = %s
        """, (name, address, phone, opening_hours, restaurant_type, img_url, rest_id))
        
        mysql.connection.commit()
        flash('餐厅信息更新成功', 'success')
        return redirect(url_for('merchant.my_restaurants'))
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'更新失败: {str(e)}', 'error')
        return redirect(url_for('merchant.edit_restaurant', rest_id=rest_id))
    finally:
        cur.close()

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS