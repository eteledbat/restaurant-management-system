import MySQLdb
import MySQLdb.cursors
import os
from dotenv import load_dotenv

load_dotenv()

test_users = [
    ('admin', 'admin123', 'admin', 'admin@example.com'),
    ('merchant1', 'merchant123', 'merchant', 'merchant1@example.com'),
    ('merchant2', 'merchant123', 'merchant', 'merchant2@example.com'),
    ('merchant3', 'merchant123', 'merchant', 'merchant3@example.com'),
    ('user1', 'user123', 'customer', 'user1@example.com'),
    ('user2', 'user123', 'customer', 'user2@example.com'),
    ('user3', 'user123', 'customer', 'user3@example.com'),
    ('user4', 'user123', 'customer', 'user4@example.com'),
    ('user5', 'user123', 'customer', 'user5@example.com'),
]

try:
    connection = MySQLdb.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        user=os.environ.get('MYSQL_USER', 'root'),
        passwd=os.environ.get('MYSQL_PASSWORD', ''),
        db=os.environ.get('MYSQL_DB', 'restaurant_db'),
        cursorclass=MySQLdb.cursors.DictCursor
    )
    
    cursor = connection.cursor()
    
    print("开始处理用户...")
    print("-" * 50)
    
    success_count = 0
    created_count = 0
    
    for username, password, user_type, email in test_users:
        try:
            # 检查用户是否存在
            cursor.execute("SELECT user_id FROM Users WHERE username = %s", (username,))
            user_exists = cursor.fetchone()
            
            if user_exists:
                # 更新现有用户的密码 - 使用 password 字段
                cursor.execute(
                    "UPDATE Users SET password = %s WHERE username = %s",
                    (password, username)
                )
                print(f"✓ 重置用户 {username} 的密码为 {password}")
                success_count += 1
            else:
                # 创建新用户 - 使用 password 字段
                cursor.execute("""
                    INSERT INTO Users (username, email, password, user_type)
                    VALUES (%s, %s, %s, %s)
                """, (username, email, password, user_type))
                print(f"+ 创建新用户 {username}，密码: {password}，类型: {user_type}")
                created_count += 1
        
        except Exception as e:
            print(f"✗ 处理用户 {username} 失败: {e}")
    
    connection.commit()
    print("-" * 50)
    print(f"处理完成！重置了 {success_count} 个用户密码，创建了 {created_count} 个新用户")
    
    # 显示所有用户的当前状态
    print("\n当前数据库中的用户列表:")
    print("-" * 80)
    cursor.execute("SELECT user_id, username, password, user_type, email FROM Users ORDER BY user_id")
    all_users = cursor.fetchall()
    
    for user in all_users:
        email = user.get('email', 'N/A')
        print(f"ID: {user['user_id']:<3} | 用户名: {user['username']:<10} | 密码: {user['password']:<12} | 类型: {user['user_type']:<8} | 邮箱: {email}")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"数据库操作失败: {e}")