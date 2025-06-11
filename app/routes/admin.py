from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from app import mysql
import os
import uuid

admin_bp = Blueprint('admin', __name__)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    """装饰器：要求管理员权限"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != 'admin':
            flash('需要管理员权限', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """管理员仪表板"""
    cur = mysql.connection.cursor()
    try:
        # 获取统计数据
        cur.execute("SELECT COUNT(*) as count FROM Users WHERE user_type = 'user' AND is_deleted = FALSE")
        user_count = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM Users WHERE user_type = 'merchant' AND is_deleted = FALSE")
        merchant_count = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM Restaurants")
        restaurant_count = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM Reviews")
        review_count = cur.fetchone()['count']
        
        # 获取最近的用户注册
        cur.execute("""
            SELECT username, email, user_type, join_date 
            FROM Users 
            WHERE is_deleted = FALSE 
            ORDER BY join_date DESC 
            LIMIT 10
        """)
        recent_users = cur.fetchall()
        
        # 获取最近的评论
        cur.execute("""
            SELECT r.comment, r.rating, r.review_time, u.username, rest.name as restaurant_name
            FROM Reviews r
            JOIN Users u ON r.user_id = u.user_id
            JOIN Restaurants rest ON r.rest_id = rest.rest_id
            ORDER BY r.review_time DESC
            LIMIT 10
        """)
        recent_reviews = cur.fetchall()
        
        return render_template('admin/dashboard.html',
                             user_count=user_count,
                             merchant_count=merchant_count,
                             restaurant_count=restaurant_count,
                             review_count=review_count,
                             recent_users=recent_users,
                             recent_reviews=recent_reviews)
    finally:
        cur.close()

@admin_bp.route('/restaurants')
@login_required
@admin_required
def manage_restaurants():
    """管理餐厅"""
    cur = mysql.connection.cursor()
    try:
        # 获取餐厅信息和关联的商家详细信息
        cur.execute("""
            SELECT r.*, 
                   COALESCE(AVG(rev.rating), 0) as avg_rating,
                   COUNT(DISTINCT rev.review_id) as review_count
            FROM Restaurants r
            LEFT JOIN Reviews rev ON r.rest_id = rev.rest_id
            GROUP BY r.rest_id
            ORDER BY r.name
        """)
        restaurants = cur.fetchall()
        
        # 获取每个餐厅的商家信息
        for restaurant in restaurants:
            cur.execute("""
                SELECT u.user_id, u.username 
                FROM Users u
                JOIN MerchantRestaurant mr ON u.user_id = mr.merchant_id
                WHERE mr.restaurant_id = %s AND u.user_type = 'merchant'
                ORDER BY u.username
            """, (restaurant['rest_id'],))
            restaurant['merchant_list'] = cur.fetchall()
        
        # 获取所有商家列表（用于分配）
        cur.execute("""
            SELECT user_id, username 
            FROM Users 
            WHERE user_type = 'merchant' AND is_deleted = FALSE 
            ORDER BY username
        """)
        merchants = cur.fetchall()
        
        return render_template('admin/restaurants.html', restaurants=restaurants, merchants=merchants)
    finally:
        cur.close()

@admin_bp.route('/add_restaurant', methods=['POST'])
@login_required
@admin_required
def add_restaurant():
    """添加餐厅"""
    name = request.form.get('name', '').strip()
    address = request.form.get('address', '').strip()
    phone = request.form.get('phone', '').strip()
    opening_hours = request.form.get('opening_hours', '').strip()
    type_cuisine = request.form.get('type', '').strip()
    merchant_ids = request.form.getlist('merchant_ids')
    
    if not all([name, address, type_cuisine]):
        flash('请填写所有必需字段', 'error')
        return redirect(url_for('admin.manage_restaurants'))
    
    # 处理图片上传
    img_url = None
    if 'restaurant_image' in request.files:
        file = request.files['restaurant_image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 生成唯一文件名
            unique_filename = str(uuid.uuid4()) + '.' + filename.rsplit('.', 1)[1].lower()
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            
            # 确保上传目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            img_url = url_for('static', filename='uploads/' + unique_filename)
    
    cur = mysql.connection.cursor()
    try:
        # 添加餐厅
        cur.execute("""
            INSERT INTO Restaurants (name, address, phone, opening_hours, type, img_url)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, address, phone, opening_hours, type_cuisine, img_url))
        
        restaurant_id = cur.lastrowid
        
        # 绑定商家
        for merchant_id in merchant_ids:
            if merchant_id:
                cur.execute("""
                    INSERT INTO MerchantRestaurant (merchant_id, restaurant_id)
                    VALUES (%s, %s)
                """, (merchant_id, restaurant_id))
        
        mysql.connection.commit()
        flash('餐厅添加成功', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'添加失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('admin.manage_restaurants'))

@admin_bp.route('/edit_restaurant/<int:rest_id>')
@login_required
@admin_required
def edit_restaurant(rest_id):
    """编辑餐厅页面"""
    cur = mysql.connection.cursor()
    try:
        # 获取餐厅信息
        cur.execute("""
            SELECT r.*, u.username as merchant_name, u.user_id as merchant_id
            FROM Restaurants r
            LEFT JOIN MerchantRestaurant mr ON r.rest_id = mr.restaurant_id
            LEFT JOIN Users u ON mr.merchant_id = u.user_id
            WHERE r.rest_id = %s
        """, (rest_id,))
        
        restaurant = cur.fetchone()
        if not restaurant:
            flash('餐厅不存在', 'error')
            return redirect(url_for('admin.manage_restaurants'))
        
        # 获取所有商家用户
        cur.execute("""
            SELECT user_id, username, email 
            FROM Users 
            WHERE user_type = 'merchant'
            ORDER BY username
        """)
        merchants = cur.fetchall()
        
        # 获取餐厅类别
        cur.execute("""
            SELECT category_name, description
            FROM restaurantcategories 
            WHERE is_active = 1
            ORDER BY category_name
        """)
        categories = cur.fetchall()
        
        return render_template('admin/edit_restaurant.html', 
                             restaurant=restaurant, 
                             merchants=merchants,
                             categories=categories)
    finally:
        cur.close()

@admin_bp.route('/update_restaurant/<int:rest_id>', methods=['POST'])
@login_required
@admin_required
def update_restaurant(rest_id):
    """更新餐厅信息"""
    name = request.form.get('name', '').strip()
    address = request.form.get('address', '').strip()
    phone = request.form.get('phone', '').strip()
    opening_hours = request.form.get('opening_hours', '').strip()
    restaurant_type = request.form.get('type', '').strip()
    merchant_id = request.form.get('merchant_id')
    
    if not all([name, address, restaurant_type]):
        flash('请填写所有必需字段', 'error')
        return redirect(url_for('admin.edit_restaurant', rest_id=rest_id))
    
    cur = mysql.connection.cursor()
    try:
        # 获取当前餐厅信息
        cur.execute("SELECT img_url FROM Restaurants WHERE rest_id = %s", (rest_id,))
        restaurant = cur.fetchone()
        
        if not restaurant:
            flash('餐厅不存在', 'error')
            return redirect(url_for('admin.manage_restaurants'))
        
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
        
        # 更新商家关联
        if merchant_id:
            # 删除现有关联
            cur.execute("DELETE FROM MerchantRestaurant WHERE restaurant_id = %s", (rest_id,))
            # 添加新关联
            cur.execute("""
                INSERT INTO MerchantRestaurant (merchant_id, restaurant_id) 
                VALUES (%s, %s)
            """, (merchant_id, rest_id))
        else:
            # 如果没有选择商家，删除所有关联
            cur.execute("DELETE FROM MerchantRestaurant WHERE restaurant_id = %s", (rest_id,))
        
        mysql.connection.commit()
        flash('餐厅信息更新成功', 'success')
        return redirect(url_for('admin.manage_restaurants'))
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'更新失败: {str(e)}', 'error')
        return redirect(url_for('admin.edit_restaurant', rest_id=rest_id))
    finally:
        cur.close()

@admin_bp.route('/delete_restaurant/<int:rest_id>', methods=['POST'])
@login_required
@admin_required
def delete_restaurant(rest_id):
    """删除餐厅"""
    cur = mysql.connection.cursor()
    try:
        # 获取餐厅信息
        cur.execute("SELECT name, img_url FROM Restaurants WHERE rest_id = %s", (rest_id,))
        restaurant = cur.fetchone()
        
        if not restaurant:
            flash('餐厅不存在', 'error')
            return redirect(url_for('admin.manage_restaurants'))
        
        restaurant_name = restaurant['name']
        
        # 删除相关数据
        cur.execute("DELETE FROM Reviews WHERE rest_id = %s", (rest_id,))
        cur.execute("DELETE FROM Dishes WHERE rest_id = %s", (rest_id,))
        cur.execute("DELETE FROM MerchantRestaurant WHERE restaurant_id = %s", (rest_id,))
        cur.execute("DELETE FROM Restaurants WHERE rest_id = %s", (rest_id,))
        
        # 删除图片文件
        if restaurant['img_url'] and restaurant['img_url'].startswith('/static/uploads/'):
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                   restaurant['img_url'].split('/')[-1])
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass  # 忽略删除失败
        
        mysql.connection.commit()
        flash(f'餐厅 "{restaurant_name}" 删除成功', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'删除失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('admin.manage_restaurants'))

@admin_bp.route('/assign_merchant', methods=['POST'])
@login_required
@admin_required
def assign_merchant():
    """分配商家到餐厅"""
    restaurant_id = request.form.get('restaurant_id', type=int)
    merchant_id = request.form.get('merchant_id', type=int)
    
    if not all([restaurant_id, merchant_id]):
        flash('请选择餐厅和商家', 'error')
        return redirect(url_for('admin.manage_restaurants'))
    
    cur = mysql.connection.cursor()
    try:
        # 检查是否已经分配
        cur.execute("""
            SELECT COUNT(*) as count FROM MerchantRestaurant 
            WHERE merchant_id = %s AND restaurant_id = %s
        """, (merchant_id, restaurant_id))
        
        if cur.fetchone()['count'] > 0:
            flash('该商家已经管理该餐厅', 'warning')
            return redirect(url_for('admin.manage_restaurants'))
        
        # 添加分配
        cur.execute("""
            INSERT INTO MerchantRestaurant (merchant_id, restaurant_id)
            VALUES (%s, %s)
        """, (merchant_id, restaurant_id))
        mysql.connection.commit()
        flash('商家分配成功', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'分配失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('admin.manage_restaurants'))

@admin_bp.route('/remove_merchant', methods=['POST'])
@login_required
@admin_required
def remove_merchant():
    """从餐厅移除商家"""
    restaurant_id = request.form.get('restaurant_id', type=int)
    merchant_id = request.form.get('merchant_id', type=int)
    
    if not all([restaurant_id, merchant_id]):
        return jsonify({'success': False, 'error': '参数错误'}), 400
    
    cur = mysql.connection.cursor()
    try:
        # 获取餐厅和商家名称用于确认
        cur.execute("""
            SELECT r.name as restaurant_name, u.username as merchant_name
            FROM Restaurants r, Users u
            WHERE r.rest_id = %s AND u.user_id = %s
        """, (restaurant_id, merchant_id))
        info = cur.fetchone()
        
        if not info:
            return jsonify({'success': False, 'error': '餐厅或商家不存在'}), 400
        
        # 检查是否存在绑定关系
        cur.execute("""
            SELECT COUNT(*) as count FROM MerchantRestaurant 
            WHERE merchant_id = %s AND restaurant_id = %s
        """, (merchant_id, restaurant_id))
        
        if cur.fetchone()['count'] == 0:
            return jsonify({'success': False, 'error': '商家未绑定到该餐厅'}), 400
        
        # 移除绑定关系
        cur.execute("""
            DELETE FROM MerchantRestaurant 
            WHERE merchant_id = %s AND restaurant_id = %s
        """, (merchant_id, restaurant_id))
        mysql.connection.commit()
        
        return jsonify({
            'success': True, 
            'message': f'已将商家 "{info["merchant_name"]}" 从餐厅 "{info["restaurant_name"]}" 移除'
        })
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cur.close()

@admin_bp.route('/reviews')
@login_required
@admin_required
def manage_reviews():
    """管理评论"""
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT r.*, u.username, rest.name as restaurant_name,
                   rep.reply_id, rep.content as reply_content, rep.reply_time
            FROM Reviews r
            JOIN Users u ON r.user_id = u.user_id
            JOIN Restaurants rest ON r.rest_id = rest.rest_id
            LEFT JOIN Replies rep ON r.review_id = rep.review_id
            ORDER BY r.review_time DESC
        """)
        reviews_data = cur.fetchall()
        
        # 处理评论和回复
        reviews = {}
        for row in reviews_data:
            review_id = row['review_id']
            if review_id not in reviews:
                reviews[review_id] = {
                    'review_id': review_id,
                    'user_id': row['user_id'],
                    'rest_id': row['rest_id'],
                    'username': row['username'],
                    'restaurant_name': row['restaurant_name'],
                    'rating': row['rating'],
                    'comment': row['comment'],
                    'review_time': row['review_time'],
                    'reply_content': row['reply_content'],
                    'reply_time': row['reply_time']
                }
        
        reviews_list = list(reviews.values())
        return render_template('admin/reviews.html', reviews=reviews_list)
    finally:
        cur.close()

@admin_bp.route('/delete_review/<int:review_id>', methods=['POST'])
@login_required
@admin_required
def delete_review(review_id):
    """管理员删除评论"""
    cur = mysql.connection.cursor()
    try:
        # 获取评论信息
        cur.execute("SELECT rest_id FROM Reviews WHERE review_id = %s", (review_id,))
        review = cur.fetchone()
        
        if not review:
            flash('评论不存在', 'error')
            return redirect(url_for('admin.manage_reviews'))
        
        # 删除评论
        cur.execute("DELETE FROM Reviews WHERE review_id = %s", (review_id,))
        mysql.connection.commit()
        
        flash('评论删除成功', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'删除失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('admin.manage_reviews'))

@admin_bp.route('/delete_reply/<int:reply_id>', methods=['POST'])
@login_required
@admin_required
def delete_reply(reply_id):
    """管理员删除商家回复"""
    cur = mysql.connection.cursor()
    try:
        # 获取回复信息
        cur.execute("SELECT review_id FROM Replies WHERE reply_id = %s", (reply_id,))
        reply = cur.fetchone()
        
        if not reply:
            flash('回复不存在', 'error')
            return redirect(url_for('admin.manage_reviews'))
        
        # 删除回复
        cur.execute("DELETE FROM Replies WHERE reply_id = %s", (reply_id,))
        mysql.connection.commit()
        
        flash('回复删除成功', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'删除失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('admin.manage_reviews'))

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    """管理用户"""
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT user_id, username, email, phone, join_date, user_type, is_deleted
            FROM Users 
            ORDER BY join_date DESC
        """)
        users = cur.fetchall()
        return render_template('admin/users.html', users=users)
    finally:
        cur.close()

@admin_bp.route('/toggle_user_status/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """切换用户状态（启用/禁用）"""
    if user_id == current_user.id:
        flash('不能禁用自己的账号', 'error')
        return redirect(url_for('admin.manage_users'))
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT is_deleted, username FROM Users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()
        
        if not user:
            flash('用户不存在', 'error')
            return redirect(url_for('admin.manage_users'))
        
        new_status = not user['is_deleted']
        cur.execute("UPDATE Users SET is_deleted = %s WHERE user_id = %s", (new_status, user_id))
        mysql.connection.commit()
        
        status_text = '禁用' if new_status else '启用'
        flash(f'用户 "{user["username"]}" {status_text}成功', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'操作失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/manage_categories')
@login_required
@admin_required
def manage_categories():
    """管理餐厅类别"""
    cur = mysql.connection.cursor()
    try:
        # 获取所有类别及使用该类别的餐厅数量
        cur.execute("""
            SELECT rc.*, 
                   COUNT(r.rest_id) as restaurant_count
            FROM restaurantcategories rc
            LEFT JOIN restaurants r ON rc.category_name = r.type
            GROUP BY rc.category_id
            ORDER BY rc.category_name
        """)
        categories = cur.fetchall()
        
        return render_template('admin/categories.html', categories=categories)
    except Exception as e:
        flash(f'获取类别列表失败: {str(e)}', 'error')
        return render_template('admin/categories.html', categories=[])
    finally:
        cur.close()

@admin_bp.route('/add_category', methods=['POST'])
@login_required
@admin_required
def add_category():
    """添加新类别"""
    cur = mysql.connection.cursor()
    try:
        category_name = request.form.get('category_name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not category_name:
            flash('类别名称不能为空', 'error')
            return redirect(url_for('admin.manage_categories'))
        
        # 检查类别是否已存在
        cur.execute("SELECT COUNT(*) as count FROM restaurantcategories WHERE category_name = %s", (category_name,))
        if cur.fetchone()['count'] > 0:
            flash('类别名称已存在', 'error')
            return redirect(url_for('admin.manage_categories'))
        
        # 插入新类别 - 默认为活跃状态
        cur.execute("""
            INSERT INTO restaurantcategories (category_name, description, is_active, created_at)
            VALUES (%s, %s, 1, NOW())
        """, (category_name, description))
        
        mysql.connection.commit()
        flash('类别添加成功', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'添加失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('admin.manage_categories'))

# 移除 toggle_category_status 路由，保留其他路由
# 修改 edit_category 路由，移除 is_active 处理

@admin_bp.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    """编辑类别"""
    cur = mysql.connection.cursor()
    
    if request.method == 'GET':
        try:
            # 获取类别信息
            cur.execute("SELECT * FROM restaurantcategories WHERE category_id = %s", (category_id,))
            category = cur.fetchone()
            
            if not category:
                flash('类别不存在', 'error')
                return redirect(url_for('admin.manage_categories'))
            
            return render_template('admin/edit_category.html', category=category)
        except Exception as e:
            print(f"获取类别信息失败: {e}")
            flash('获取类别信息失败', 'error')
            return redirect(url_for('admin.manage_categories'))
        finally:
            cur.close()
    
    elif request.method == 'POST':
        try:
            category_name = request.form.get('category_name', '').strip()
            description = request.form.get('description', '').strip()
            
            print(f"调试信息 - category_id: {category_id}, category_name: {category_name}, description: {description}")
            
            if not category_name:
                flash('类别名称不能为空', 'error')
                return redirect(url_for('admin.edit_category', category_id=category_id))
            
            # 检查类别是否存在
            cur.execute("SELECT category_name FROM restaurantcategories WHERE category_id = %s", (category_id,))
            existing_category = cur.fetchone()
            
            if not existing_category:
                flash('类别不存在', 'error')
                return redirect(url_for('admin.manage_categories'))
            
            # 检查类别名称是否已存在（排除当前类别）
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM restaurantcategories 
                WHERE category_name = %s AND category_id != %s
            """, (category_name, category_id))
            
            result = cur.fetchone()
            if result['count'] > 0:
                flash('类别名称已存在', 'error')
                return redirect(url_for('admin.edit_category', category_id=category_id))
            
            # 更新类别信息
            cur.execute("""
                UPDATE restaurantcategories 
                SET category_name = %s, description = %s
                WHERE category_id = %s
            """, (category_name, description, category_id))
            
            # 检查是否有行被更新
            if cur.rowcount == 0:
                flash('更新失败：未找到要更新的类别', 'error')
                return redirect(url_for('admin.edit_category', category_id=category_id))
            
            mysql.connection.commit()
            flash('类别信息更新成功', 'success')
            return redirect(url_for('admin.manage_categories'))
            
        except Exception as e:
            mysql.connection.rollback()
            print(f"更新类别失败: {e}")
            import traceback
            traceback.print_exc()
            flash(f'更新失败: {str(e)}', 'error')
            return redirect(url_for('admin.edit_category', category_id=category_id))
        finally:
            cur.close()

@admin_bp.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """删除类别"""
    cur = mysql.connection.cursor()
    try:
        print(f"尝试删除类别 ID: {category_id}")
        
        # 获取类别信息
        cur.execute("SELECT category_name FROM restaurantcategories WHERE category_id = %s", (category_id,))
        category = cur.fetchone()
        
        if not category:
            print(f"类别 {category_id} 不存在")
            flash('类别不存在', 'error')
            return redirect(url_for('admin.manage_categories'))
        
        category_name = category['category_name']
        print(f"找到类别: {category_name}")
        
        # 检查是否有餐厅在使用这个类别
        cur.execute("SELECT COUNT(*) as count FROM restaurants WHERE type = %s", (category_name,))
        result = cur.fetchone()
        restaurant_count = result['count']
        
        print(f"使用该类别的餐厅数量: {restaurant_count}")
        
        if restaurant_count > 0:
            message = f'无法删除类别 "{category_name}"，有 {restaurant_count} 家餐厅正在使用此类别'
            print(message)
            flash(message, 'error')
            return redirect(url_for('admin.manage_categories'))
        
        # 删除类别
        cur.execute("DELETE FROM restaurantcategories WHERE category_id = %s", (category_id,))
        
        if cur.rowcount == 0:
            print(f"删除失败: 没有找到类别 {category_id}")
            flash('删除失败：未找到要删除的类别', 'error')
            return redirect(url_for('admin.manage_categories'))
        
        mysql.connection.commit()
        print(f"成功删除类别: {category_name}")
        flash(f'类别 "{category_name}" 删除成功', 'success')
        
        return redirect(url_for('admin.manage_categories'))
        
    except Exception as e:
        mysql.connection.rollback()
        print(f"删除类别失败: {e}")
        import traceback
        traceback.print_exc()
        flash(f'删除失败: {str(e)}', 'error')
        return redirect(url_for('admin.manage_categories'))
    finally:
        cur.close()

@admin_bp.route('/issue_reports')
@login_required
@admin_required
def manage_issues():
    """管理问题报告"""
    status_filter = request.args.get('status', 'all')
    
    cur = mysql.connection.cursor()
    try:
        # 确保表存在
        cur.execute("""
            CREATE TABLE IF NOT EXISTS IssueReports (
                report_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NULL,
                reporter_name VARCHAR(100) NOT NULL,
                reporter_email VARCHAR(100),
                issue_type ENUM('bug', 'feature', 'complaint', 'suggestion', 'other') NOT NULL,
                subject VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                status ENUM('pending', 'in_progress', 'resolved', 'closed') DEFAULT 'pending',
                priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                admin_response TEXT,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE SET NULL
            )
        """)
        
        # 构建查询条件
        where_clause = ""
        params = []
        
        if status_filter != 'all':
            where_clause = "WHERE ir.status = %s"
            params.append(status_filter)
        
        # 获取问题报告
        query = f"""
            SELECT ir.*, u.username
            FROM IssueReports ir
            LEFT JOIN Users u ON ir.user_id = u.user_id
            {where_clause}
            ORDER BY 
                CASE ir.status 
                    WHEN 'pending' THEN 1 
                    WHEN 'in_progress' THEN 2 
                    WHEN 'resolved' THEN 3 
                    WHEN 'closed' THEN 4 
                END,
                CASE ir.priority 
                    WHEN 'urgent' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'medium' THEN 3 
                    WHEN 'low' THEN 4 
                END,
                ir.created_at DESC
        """
        
        cur.execute(query, params)
        issues = cur.fetchall()
        
        # 获取统计信息
        cur.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM IssueReports 
            GROUP BY status
        """)
        stats_result = cur.fetchall()
        stats = {row['status']: row['count'] for row in stats_result}
        
        mysql.connection.commit()
        return render_template('admin/issues.html', issues=issues, stats=stats, current_filter=status_filter)
    finally:
        cur.close()

@admin_bp.route('/update_issue/<int:report_id>', methods=['POST'])
@login_required
@admin_required
def update_issue(report_id):
    """更新问题报告状态"""
    status = request.form.get('status')
    priority = request.form.get('priority')
    admin_response = request.form.get('admin_response', '').strip()
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            UPDATE IssueReports 
            SET status = %s, priority = %s, admin_response = %s, updated_at = CURRENT_TIMESTAMP
            WHERE report_id = %s
        """, (status, priority, admin_response, report_id))
        
        mysql.connection.commit()
        flash('问题报告更新成功', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'更新失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('admin.manage_issues'))

@admin_bp.route('/manage_restaurant_merchants/<int:rest_id>')
@login_required
@admin_required
def manage_restaurant_merchants(rest_id):
    """管理餐厅的商户"""
    cur = mysql.connection.cursor()
    try:
        # 获取餐厅信息
        cur.execute("SELECT * FROM Restaurants WHERE rest_id = %s", (rest_id,))
        restaurant = cur.fetchone()
        
        if not restaurant:
            flash('餐厅不存在', 'error')
            return redirect(url_for('admin.manage_restaurants'))
        
        # 获取当前管理这家餐厅的商户
        cur.execute("""
            SELECT u.user_id, u.username, u.email, u.phone
            FROM MerchantRestaurant mr
            JOIN Users u ON mr.merchant_id = u.user_id
            WHERE mr.restaurant_id = %s
            ORDER BY u.username
        """, (rest_id,))
        current_merchants = cur.fetchall()
        
        # 获取所有商户（显示是否已分配）
        cur.execute("""
            SELECT u.user_id, u.username, u.email, u.phone,
                   CASE WHEN mr.merchant_id IS NOT NULL THEN TRUE ELSE FALSE END as is_assigned
            FROM Users u
            LEFT JOIN MerchantRestaurant mr ON u.user_id = mr.merchant_id 
                AND mr.restaurant_id = %s
            WHERE u.user_type = 'merchant' AND u.is_deleted = FALSE
            ORDER BY is_assigned DESC, u.username
        """, (rest_id,))
        all_merchants = cur.fetchall()
        
        return render_template('admin/manage_restaurant_merchants.html', 
                             restaurant=restaurant,
                             current_merchants=current_merchants,
                             all_merchants=all_merchants)
    finally:
        cur.close()

@admin_bp.route('/assign_merchant_to_restaurant', methods=['POST'])
@login_required
@admin_required
def assign_merchant_to_restaurant():
    """为餐厅分配商户"""
    restaurant_id = request.form.get('restaurant_id')
    merchant_id = request.form.get('merchant_id')
    
    if not restaurant_id or not merchant_id:
        flash('参数错误', 'error')
        return redirect(url_for('admin.manage_restaurants'))
    
    cur = mysql.connection.cursor()
    try:
        # 检查餐厅和商户是否存在
        cur.execute("SELECT name FROM Restaurants WHERE rest_id = %s", (restaurant_id,))
        restaurant = cur.fetchone()
        
        cur.execute("SELECT username FROM Users WHERE user_id = %s AND user_type = 'merchant'", (merchant_id,))
        merchant = cur.fetchone()
        
        if not restaurant or not merchant:
            flash('餐厅或商户不存在', 'error')
            return redirect(url_for('admin.manage_restaurant_merchants', rest_id=restaurant_id))
        
        # 检查是否已经分配
        cur.execute("""
            SELECT COUNT(*) as count FROM MerchantRestaurant 
            WHERE merchant_id = %s AND restaurant_id = %s
        """, (merchant_id, restaurant_id))
        
        result = cur.fetchone()
        if result['count'] > 0:
            flash(f'商户 {merchant["username"]} 已经是该餐厅的管理商户', 'warning')
        else:
            # 添加新的分配
            cur.execute("""
                INSERT INTO MerchantRestaurant (merchant_id, restaurant_id)
                VALUES (%s, %s)
            """, (merchant_id, restaurant_id))
            mysql.connection.commit()
            flash(f'成功将商户 {merchant["username"]} 分配给餐厅 {restaurant["name"]}', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'分配失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('admin.manage_restaurant_merchants', rest_id=restaurant_id))

@admin_bp.route('/remove_merchant_from_restaurant', methods=['POST'])
@login_required
@admin_required
def remove_merchant_from_restaurant():
    """移除餐厅的商户"""
    restaurant_id = request.form.get('restaurant_id')
    merchant_id = request.form.get('merchant_id')
    
    if not restaurant_id or not merchant_id:
        flash('参数错误', 'error')
        return redirect(url_for('admin.manage_restaurants'))
    
    cur = mysql.connection.cursor()
    try:
        # 获取商户和餐厅名称用于提示
        cur.execute("SELECT username FROM Users WHERE user_id = %s", (merchant_id,))
        merchant = cur.fetchone()
        
        cur.execute("SELECT name FROM Restaurants WHERE rest_id = %s", (restaurant_id,))
        restaurant = cur.fetchone()
        
        # 删除关联
        cur.execute("""
            DELETE FROM MerchantRestaurant 
            WHERE merchant_id = %s AND restaurant_id = %s
        """, (merchant_id, restaurant_id))
        
        mysql.connection.commit()
        
        if merchant and restaurant:
            flash(f'成功移除商户 {merchant["username"]} 对餐厅 {restaurant["name"]} 的管理权限', 'success')
        else:
            flash('商户移除成功', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'移除失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('admin.manage_restaurant_merchants', rest_id=restaurant_id))