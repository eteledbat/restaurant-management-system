from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import mysql

restaurant_bp = Blueprint('restaurant', __name__)

@restaurant_bp.route('/list')
def restaurant_list():
    """餐厅列表页面 - 支持分类筛选和排序"""
    cur = None
    try:
        cur = mysql.connection.cursor()
        
        # 获取筛选参数
        category_name = request.args.get('category_name', '')
        search_keyword = request.args.get('search', '')
        sort_by = request.args.get('sort', 'rating')  # 默认按评分排序
        
        print(f"调试信息 - category_name: {category_name}, search_keyword: {search_keyword}, sort_by: {sort_by}")
        
        # 使用 restaurants 表的 type 字段与 restaurantcategories 表关联
        base_query = """
            SELECT r.*,
                   rc.category_name,
                   rc.description as category_description,
                   COALESCE(r.rating, 0) as avg_rating,
                   COALESCE(r.review_count, 0) as review_count
            FROM restaurants r
            LEFT JOIN restaurantcategories rc ON r.type = rc.category_name
        """
        
        params = []
        conditions = []
        
        # 添加分类筛选条件
        if category_name:
            conditions.append("r.type = %s")
            params.append(category_name)
        
        # 添加搜索条件
        if search_keyword:
            conditions.append("(r.name LIKE %s OR r.address LIKE %s OR r.type LIKE %s)")
            params.extend([f'%{search_keyword}%', f'%{search_keyword}%', f'%{search_keyword}%'])
        
        # 组合查询条件
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # 添加排序
        if sort_by == 'rating':
            base_query += " ORDER BY r.rating DESC, r.name"
        elif sort_by == 'name':
            base_query += " ORDER BY r.name ASC"
        elif sort_by == 'reviews':
            base_query += " ORDER BY r.review_count DESC, r.rating DESC"
        else:
            base_query += " ORDER BY r.rating DESC, r.name"
        
        print(f"执行查询: {base_query}")
        print(f"参数: {params}")
        
        cur.execute(base_query, params)
        restaurants = cur.fetchall()
        
        print(f"找到 {len(restaurants)} 家餐厅")
        
        # 获取所有活跃的分类
        try:
            cur.execute("""
                SELECT category_id, category_name, description
                FROM restaurantcategories 
                WHERE is_active = 1
                ORDER BY category_name
            """)
            categories = cur.fetchall()
            print(f"找到 {len(categories)} 个分类")
        except Exception as cat_error:
            print(f"获取分类失败: {cat_error}")
            categories = []
        
        return render_template('restaurants/list.html', 
                             restaurants=restaurants, 
                             categories=categories,
                             selected_category=category_name,
                             search_keyword=search_keyword,
                             current_sort=sort_by)
        
    except Exception as e:
        print(f"获取餐厅列表失败详细错误: {e}")
        import traceback
        traceback.print_exc()
        flash('获取餐厅列表失败', 'error')
        return render_template('restaurants/list.html', 
                             restaurants=[], 
                             categories=[],
                             selected_category='',
                             search_keyword='',
                             current_sort='rating')
    finally:
        if cur:
            cur.close()

@restaurant_bp.route('/detail/<int:rest_id>')
def detail(rest_id):
    """餐厅详情页"""
    cur = mysql.connection.cursor()
    try:
        # 获取餐厅信息
        cur.execute("""
            SELECT r.*, 
                   COALESCE(AVG(rev.rating), 0) as rating,
                   COUNT(rev.review_id) as review_count,
                   COUNT(DISTINCT f.user_id) as star_count
            FROM Restaurants r 
            LEFT JOIN Reviews rev ON r.rest_id = rev.rest_id
            LEFT JOIN Favourites f ON r.rest_id = f.rest_id
            WHERE r.rest_id = %s
            GROUP BY r.rest_id
        """, (rest_id,))
        restaurant = cur.fetchone()
        
        if not restaurant:
            flash('餐厅不存在', 'error')
            return redirect(url_for('restaurant.restaurant_list'))
        
        # 获取菜品信息和用户推荐状态
        if current_user.is_authenticated:
            cur.execute("""
                SELECT d.*, 
                       COUNT(DISTINCT rec.user_id) as rec_count,
                       CASE WHEN EXISTS(SELECT 1 FROM Recommendations WHERE user_id = %s AND dish_id = d.dish_id) 
                            THEN 1 ELSE 0 END as user_recommended
                FROM Dishes d
                LEFT JOIN Recommendations rec ON d.dish_id = rec.dish_id
                WHERE d.rest_id = %s
                GROUP BY d.dish_id
                ORDER BY d.name
            """, (current_user.id, rest_id))
        else:
            cur.execute("""
                SELECT d.*, 
                       COUNT(DISTINCT rec.user_id) as rec_count,
                       0 as user_recommended
                FROM Dishes d
                LEFT JOIN Recommendations rec ON d.dish_id = rec.dish_id
                WHERE d.rest_id = %s
                GROUP BY d.dish_id
                ORDER BY d.name
            """, (rest_id,))
        
        dishes = cur.fetchall()
        
        # 获取评论信息
        cur.execute("""
            SELECT r.review_id, r.user_id, r.rating, r.comment, r.review_time,
                   u.username
            FROM Reviews r
            JOIN Users u ON r.user_id = u.user_id
            WHERE r.rest_id = %s
            ORDER BY r.review_time DESC
        """, (rest_id,))
        reviews = cur.fetchall()
        
        # 获取回复信息
        cur.execute("""
            SELECT rep.review_id, rep.content, rep.reply_time
            FROM Replies rep
            JOIN Reviews r ON rep.review_id = r.review_id
            WHERE r.rest_id = %s
            ORDER BY rep.reply_time ASC
        """, (rest_id,))
        replies_data = cur.fetchall()
        
        # 组织回复数据
        replies_by_review = {}
        for reply in replies_data:
            review_id = reply['review_id']
            if review_id not in replies_by_review:
                replies_by_review[review_id] = []
            replies_by_review[review_id].append({
                'content': reply['content'],
                'reply_time': reply['reply_time']
            })
        
        # 将回复添加到评论中
        for review in reviews:
            review_id = review['review_id']
            review['replies'] = replies_by_review.get(review_id, [])
        
        # 检查用户是否收藏了该餐厅
        is_favorited = False
        if current_user.is_authenticated and current_user.user_type == 'user':
            cur.execute("SELECT COUNT(*) as count FROM Favourites WHERE user_id = %s AND rest_id = %s", 
                       (current_user.id, rest_id))
            is_favorited = cur.fetchone()['count'] > 0
        
        return render_template('restaurants/detail.html', 
                             restaurant=restaurant, 
                             dishes=dishes, 
                             reviews=reviews,
                             is_favorited=is_favorited)
    except Exception as e:
        print(f"详情页错误: {e}")
        flash('加载餐厅详情时出错', 'error')
        return redirect(url_for('restaurant.restaurant_list'))
    finally:
        cur.close()

@restaurant_bp.route('/toggle_favorite', methods=['POST'])
@login_required
def toggle_favorite():
    """切换收藏状态"""
    if current_user.user_type != 'user':
        return jsonify({'success': False, 'error': '只有普通用户可以收藏餐厅'}), 403
    
    data = request.get_json()
    rest_id = data.get('rest_id')
    
    if not rest_id:
        return jsonify({'success': False, 'error': '餐厅ID不能为空'}), 400
    
    cur = mysql.connection.cursor()
    try:
        # 检查是否已收藏
        cur.execute("SELECT COUNT(*) as count FROM Favourites WHERE user_id = %s AND rest_id = %s", 
                   (current_user.id, rest_id))
        is_favorited = cur.fetchone()['count'] > 0
        
        if is_favorited:
            # 取消收藏
            cur.execute("DELETE FROM Favourites WHERE user_id = %s AND rest_id = %s", 
                       (current_user.id, rest_id))
            action = 'removed'
        else:
            # 添加收藏
            cur.execute("INSERT INTO Favourites (user_id, rest_id, timestamp) VALUES (%s, %s, NOW())", 
                       (current_user.id, rest_id))
            action = 'added'
        
        mysql.connection.commit()
        return jsonify({'success': True, 'action': action})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cur.close()

@restaurant_bp.route('/favorites')
@login_required
def favorites():
    """用户收藏的餐厅"""
    if current_user.user_type != 'user':
        flash('只有普通用户可以查看收藏', 'error')
        return redirect(url_for('main.index'))
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT r.*, f.timestamp,
                   COALESCE(AVG(rev.rating), 0) as rating,
                   COUNT(rev.review_id) as review_count
            FROM Favourites f
            JOIN Restaurants r ON f.rest_id = r.rest_id
            LEFT JOIN Reviews rev ON r.rest_id = rev.rest_id
            WHERE f.user_id = %s
            GROUP BY r.rest_id, f.timestamp
            ORDER BY f.timestamp DESC
        """, (current_user.id,))
        favorites = cur.fetchall()
        return render_template('restaurants/favourites.html', favorites=favorites)
    finally:
        cur.close()