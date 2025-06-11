from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user
from app import mysql

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首页"""
    cur = mysql.connection.cursor()
    try:
        # 获取评分最高的餐厅，相同评分按评论数排序
        cur.execute("""
            SELECT r.*, 
                   COALESCE(AVG(rev.rating), 0) as rating,
                   COUNT(rev.review_id) as review_count
            FROM Restaurants r 
            LEFT JOIN Reviews rev ON r.rest_id = rev.rest_id
            GROUP BY r.rest_id
            HAVING COUNT(rev.review_id) > 0
            ORDER BY rating DESC, review_count DESC, r.name
        """)
        all_restaurants = cur.fetchall()
        
        # 处理并列排名
        top_restaurants = []
        current_rank = 1
        prev_rating = None
        
        for i, restaurant in enumerate(all_restaurants):
            if len(top_restaurants) >= 3 and restaurant['rating'] != prev_rating:
                break
                
            if prev_rating is not None and restaurant['rating'] != prev_rating:
                current_rank = i + 1
            
            restaurant_dict = dict(restaurant)
            restaurant_dict['rank'] = current_rank
            top_restaurants.append(restaurant_dict)
            prev_rating = restaurant['rating']

        # 获取所有分类
        cur.execute("""
            SELECT category_id, category_name, description
            FROM restaurantcategories 
            ORDER BY category_name
        """)
        categories = cur.fetchall()
        
        return render_template('index.html', top_restaurants=top_restaurants,categories=categories)
    finally:
        cur.close()

@main_bp.route('/search')
def search():
    """搜索餐厅和菜品"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')  # all, restaurant, dish
    
    if not query:
        flash('请输入搜索关键词', 'warning')
        return redirect(url_for('main.index'))
    
    cur = mysql.connection.cursor()
    try:
        restaurants = []
        dishes = []
        
        if search_type in ['all', 'restaurant']:
            # 搜索餐厅
            cur.execute("""
                SELECT r.*, 
                       COALESCE(AVG(rev.rating), 0) as rating,
                       COUNT(rev.review_id) as review_count
                FROM Restaurants r 
                LEFT JOIN Reviews rev ON r.rest_id = rev.rest_id
                WHERE r.name LIKE %s OR r.type LIKE %s OR r.address LIKE %s
                GROUP BY r.rest_id
                ORDER BY rating DESC, r.name
                LIMIT 20
            """, (f'%{query}%', f'%{query}%', f'%{query}%'))
            restaurants = cur.fetchall()
        
        if search_type in ['all', 'dish']:
            # 搜索菜品
            cur.execute("""
                SELECT d.*, r.name as restaurant_name, r.rest_id,
                       COUNT(DISTINCT rec.user_id) as rec_count
                FROM Dishes d
                JOIN Restaurants r ON d.rest_id = r.rest_id
                LEFT JOIN Recommendations rec ON d.dish_id = rec.dish_id
                WHERE d.name LIKE %s OR d.description LIKE %s
                GROUP BY d.dish_id
                ORDER BY rec_count DESC, d.name
                LIMIT 20
            """, (f'%{query}%', f'%{query}%'))
            dishes = cur.fetchall()
        
        return render_template('search_results.html', 
                             query=query, 
                             search_type=search_type,
                             restaurants=restaurants, 
                             dishes=dishes)
    except Exception as e:
        flash(f'搜索出错: {str(e)}', 'error')
        return redirect(url_for('main.index'))
    finally:
        cur.close()

@main_bp.route('/api/cities')
def api_cities():
    """获取城市列表API"""
    cur = mysql.connection.cursor()
    try:
        # 从餐厅地址中提取城市信息
        cur.execute("""
            SELECT DISTINCT 
                CASE 
                    WHEN address LIKE '%市%' THEN 
                        CONCAT(
                            SUBSTRING_INDEX(
                                SUBSTRING_INDEX(address, '市', 1), 
                                CASE 
                                    WHEN address LIKE '%省%' THEN '省'
                                    WHEN address LIKE '%自治区%' THEN '自治区'
                                    WHEN address LIKE '%直辖市%' THEN '直辖市'
                                    ELSE '|'  -- 不太可能的分隔符
                                END, 
                                -1
                            ), 
                            '市'
                        )
                    ELSE NULL
                END as city
            FROM Restaurants 
            WHERE address IS NOT NULL AND address != ''
            HAVING city IS NOT NULL AND city != '市'
            ORDER BY city
        """)
        
        cities = [row['city'] for row in cur.fetchall()]
        
        # 如果提取失败，提供默认城市列表
        if not cities:
            cities = ['北京市', '上海市', '广州市', '深圳市', '杭州市', '南京市', '武汉市', '成都市']
        
        return jsonify({'cities': cities})
    except Exception as e:
        return jsonify({'cities': [], 'error': str(e)})
    finally:
        cur.close()

@main_bp.route('/city_restaurants')
def city_restaurants():
    """按城市显示餐厅"""
    city = request.args.get('city', '').strip()
    
    cur = mysql.connection.cursor()
    try:
        if city:
            # 搜索指定城市的餐厅
            cur.execute("""
                SELECT r.*, 
                       COALESCE(AVG(rev.rating), 0) as rating,
                       COUNT(rev.review_id) as review_count
                FROM Restaurants r 
                LEFT JOIN Reviews rev ON r.rest_id = rev.rest_id
                WHERE r.address LIKE %s
                GROUP BY r.rest_id
                ORDER BY rating DESC, r.name
            """, (f'%{city}%',))
            restaurants = cur.fetchall()
        else:
            restaurants = []
        
        return render_template('city_restaurants.html', 
                             restaurants=restaurants, 
                             selected_city=city)
    finally:
        cur.close()

@main_bp.route('/report_issue')
def report_issue():
    """问题报告页面"""
    return render_template('report_issue.html')

@main_bp.route('/submit_issue', methods=['POST'])
def submit_issue():
    """提交问题报告"""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    issue_type = request.form.get('issue_type', '').strip()
    subject = request.form.get('subject', '').strip()
    description = request.form.get('description', '').strip()
    
    if not all([name, issue_type, subject, description]):
        flash('请填写所有必需字段', 'error')
        return redirect(url_for('main.report_issue'))
    
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
        
        # 插入问题报告
        user_id = current_user.id if current_user.is_authenticated else None
        cur.execute("""
            INSERT INTO IssueReports (user_id, reporter_name, reporter_email, issue_type, subject, description)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, name, email, issue_type, subject, description))
        
        mysql.connection.commit()
        flash('问题报告提交成功，我们会尽快处理', 'success')
        return redirect(url_for('main.index'))
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'提交失败: {str(e)}', 'error')
        return redirect(url_for('main.report_issue'))
    finally:
        cur.close()

@main_bp.route('/api/restaurant_categories')
def api_restaurant_categories():
    """获取餐厅类别API"""
    cur = mysql.connection.cursor()
    try:
        # 确保表存在并获取所有活跃类别
        cur.execute("""
            CREATE TABLE IF NOT EXISTS RestaurantCategories (
                category_id INT AUTO_INCREMENT PRIMARY KEY,
                category_name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 插入现有的餐厅类别（如果还没有）
        cur.execute("""
            INSERT IGNORE INTO RestaurantCategories (category_name, description) 
            SELECT DISTINCT type, CONCAT(type, '类型餐厅') 
            FROM Restaurants 
            WHERE type IS NOT NULL AND type != ''
        """)
        
        # 获取所有活跃类别
        cur.execute("""
            SELECT category_name, description
            FROM RestaurantCategories 
            WHERE is_active = TRUE
            ORDER BY category_name
        """)
        
        categories = cur.fetchall()
        mysql.connection.commit()
        
        return jsonify({
            'categories': [{'name': cat['category_name'], 'description': cat['description']} for cat in categories]
        })
    except Exception as e:
        return jsonify({'categories': [], 'error': str(e)})
    finally:
        cur.close()