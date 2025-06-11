from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import mysql

review_bp = Blueprint('review', __name__)

@review_bp.route('/my_reviews')
@login_required
def my_reviews():
    """用户的评论列表"""
    if current_user.user_type != 'user':
        flash('只有用户可以访问此页面', 'error')
        return redirect(url_for('main.index'))
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT r.*, rest.name as restaurant_name
            FROM reviews r
            JOIN restaurants rest ON r.rest_id = rest.rest_id
            WHERE r.user_id = %s
            ORDER BY r.review_time DESC
        """, (current_user.id,))
        reviews = cur.fetchall()
        return render_template('reviews/my_reviews.html', reviews=reviews)
    finally:
        cur.close()

@review_bp.route('/edit/<int:review_id>')
@login_required
def edit_review(review_id):
    """编辑评论页面"""
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT r.*, rest.name as restaurant_name
            FROM reviews r
            JOIN restaurants rest ON r.rest_id = rest.rest_id
            WHERE r.review_id = %s AND r.user_id = %s
        """, (review_id, current_user.id))
        review = cur.fetchone()
        
        if not review:
            flash('评论不存在或无权限编辑', 'error')
            return redirect(url_for('review.my_reviews'))
        
        return render_template('reviews/edit_review.html', review=review)
    finally:
        cur.close()

@review_bp.route('/post/<int:rest_id>', methods=['POST'])
@login_required
def post_review(rest_id):
    """发表评论"""
    if current_user.user_type != 'user':
        flash('只有普通用户可以发表评论', 'error')
        return redirect(url_for('restaurant.detail', rest_id=rest_id))
    
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '')
    
    if not rating or rating < 1 or rating > 10:
        flash('请选择1-10分的评分', 'error')
        return redirect(url_for('restaurant.detail', rest_id=rest_id))
    
    if not comment.strip():
        flash('请填写评论内容', 'error')
        return redirect(url_for('restaurant.detail', rest_id=rest_id))
    
    cur = mysql.connection.cursor()
    try:
        # 检查用户是否已经对该餐厅发表过评论
        cur.execute("SELECT COUNT(*) as count FROM reviews WHERE user_id = %s AND rest_id = %s", 
                   (current_user.id, rest_id))
        existing_count = cur.fetchone()['count']
        
        if existing_count > 0:
            flash('您已经对该餐厅发表过评论，请编辑现有评论', 'warning')
            return redirect(url_for('restaurant.detail', rest_id=rest_id))
        
        # 插入新评论
        cur.execute("""
            INSERT INTO reviews (user_id, rest_id, rating, comment, review_time)
            VALUES (%s, %s, %s, %s, NOW())
        """, (current_user.id, rest_id, rating, comment))
        mysql.connection.commit()
        
        # 更新餐厅统计
        update_restaurant_stats(rest_id)
        
        flash('评论发表成功！', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'发表评论失败: {str(e)}', 'error')
    finally:
        cur.close()
    
    return redirect(url_for('restaurant.detail', rest_id=rest_id))

@review_bp.route('/update/<int:review_id>', methods=['POST'])
@login_required
def update_review(review_id):
    """更新评论"""
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '')
    
    if not rating or rating < 1 or rating > 10:
        flash('请选择1-10分的评分', 'error')
        return redirect(url_for('review.edit_review', review_id=review_id))
    
    if not comment.strip():
        flash('请填写评论内容', 'error')
        return redirect(url_for('review.edit_review', review_id=review_id))
    
    cur = mysql.connection.cursor()
    try:
        # 检查评论是否存在且属于当前用户
        cur.execute("SELECT user_id, rest_id FROM reviews WHERE review_id = %s", (review_id,))
        review = cur.fetchone()
        
        if not review:
            flash('评论不存在', 'error')
            return redirect(url_for('review.my_reviews'))
        
        if review['user_id'] != current_user.id:
            flash('只能修改自己的评论', 'error')
            return redirect(url_for('review.my_reviews'))
        
        # 更新评论
        cur.execute("""
            UPDATE reviews 
            SET rating = %s, comment = %s
            WHERE review_id = %s
        """, (rating, comment, review_id))
        mysql.connection.commit()
        flash('评论更新成功！', 'success')
        return redirect(url_for('restaurant.detail', rest_id=review['rest_id']))
    except Exception as e:
        mysql.connection.rollback()
        flash(f'更新失败: {str(e)}', 'error')
        return redirect(url_for('review.edit_review', review_id=review_id))
    finally:
        cur.close()

@review_bp.route('/delete/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    """删除评论"""
    cur = mysql.connection.cursor()
    try:
        # 检查评论是否存在且属于当前用户
        cur.execute("SELECT user_id, rest_id FROM reviews WHERE review_id = %s", (review_id,))
        review = cur.fetchone()
        
        if not review:
            flash('评论不存在', 'error')
            return redirect(url_for('review.my_reviews'))
        
        if review['user_id'] != current_user.id and current_user.user_type != 'admin':
            flash('只能删除自己的评论', 'error')
            return redirect(url_for('review.my_reviews'))
        
        rest_id = review['rest_id']
        
        # 删除评论
        cur.execute("DELETE FROM reviews WHERE review_id = %s", (review_id,))
        mysql.connection.commit()
        
        # 更新餐厅统计
        update_restaurant_stats(rest_id)
        
        flash('评论删除成功', 'success')
        
        # 根据来源页面重定向
        if request.referrer and 'detail' in request.referrer:
            return redirect(url_for('restaurant.detail', rest_id=rest_id))
        else:
            return redirect(url_for('review.my_reviews'))
    except Exception as e:
        mysql.connection.rollback()
        flash(f'删除失败: {str(e)}', 'error')
        return redirect(url_for('review.my_reviews'))
    finally:
        cur.close()

@review_bp.route('/reply/<int:review_id>', methods=['POST'])
@login_required
def reply_review(review_id):
    """商家回复评论"""
    if current_user.user_type != 'merchant':
        flash('只有商家可以回复评论', 'error')
        return redirect(url_for('main.index'))
    
    reply_content = request.form.get('reply_content', '').strip()
    if not reply_content:
        flash('回复内容不能为空', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    cur = mysql.connection.cursor()
    try:
        # 获取评论信息
        cur.execute("SELECT rest_id FROM reviews WHERE review_id = %s", (review_id,))
        review = cur.fetchone()
        
        if not review:
            flash('评论不存在', 'error')
            return redirect(url_for('main.index'))
        
        # 检查商家是否拥有该餐厅（需要根据您的数据库结构调整）
        # 假设有 merchant_restaurants 表或类似的关联表
        cur.execute("""
            SELECT COUNT(*) as count FROM merchantrestaurant 
            WHERE restaurant_id = %s AND merchant_id = %s
        """, (review['rest_id'], current_user.id))
        
        if cur.fetchone()['count'] == 0:
            flash('您无权回复该餐厅的评论', 'error')
            return redirect(url_for('restaurant.detail', rest_id=review['rest_id']))
        
        # 插入回复（需要根据您的数据库结构调整）
        cur.execute("""
            INSERT INTO replies (review_id, content, reply_time)
            VALUES (%s, %s, NOW())
        """, (review_id, reply_content))
        mysql.connection.commit()
        flash('回复成功', 'success')
        
        return redirect(url_for('restaurant.detail', rest_id=review['rest_id']))
    except Exception as e:
        mysql.connection.rollback()
        flash(f'回复失败: {str(e)}', 'error')
        return redirect(request.referrer or url_for('main.index'))
    finally:
        cur.close()

@review_bp.route('/recommend_dish', methods=['POST'])
@login_required
def recommend_dish():
    """推荐菜品"""
    if current_user.user_type != 'user':
        return jsonify({'error': '只有用户可以推荐菜品'}), 403
    
    dish_id = request.json.get('dish_id')
    if not dish_id:
        return jsonify({'error': '菜品ID不能为空'}), 400
    
    cur = mysql.connection.cursor()
    try:
        # 检查是否已经推荐过
        cur.execute("SELECT COUNT(*) as count FROM recommendations WHERE user_id = %s AND dish_id = %s", 
                   (current_user.id, dish_id))
        is_recommended = cur.fetchone()['count'] > 0
        
        if is_recommended:
            # 取消推荐
            cur.execute("DELETE FROM recommendations WHERE user_id = %s AND dish_id = %s", 
                       (current_user.id, dish_id))
            action = 'removed'
        else:
            # 添加推荐
            cur.execute("INSERT INTO recommendations (user_id, dish_id) VALUES (%s, %s)", 
                       (current_user.id, dish_id))
            action = 'added'
        
        mysql.connection.commit()
        return jsonify({'success': True, 'action': action})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

def update_restaurant_stats(rest_id):
    """更新餐厅的评分和评论数统计"""
    cur = mysql.connection.cursor()
    try:
        # 注意：这里假设 restaurants 表有 rating 和 review_count 字段
        # 如果没有这些字段，请删除这个函数的调用
        cur.execute("""
            UPDATE restaurants 
            SET rating = (
                SELECT COALESCE(AVG(rating), 0) 
                FROM reviews 
                WHERE rest_id = %s
            ),
            review_count = (
                SELECT COUNT(*) 
                FROM reviews 
                WHERE rest_id = %s
            )
            WHERE rest_id = %s
        """, (rest_id, rest_id, rest_id))
        mysql.connection.commit()
    except Exception as e:
        print(f"更新餐厅统计失败: {e}")
        mysql.connection.rollback()
    finally:
        cur.close()