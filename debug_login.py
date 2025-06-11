from app import create_app
from app.models.user import User

app = create_app()

with app.app_context():
    # 测试您尝试登录的用户名和密码
    username = "user1"  # 替换为您尝试登录的用户名
    password = "user123"  # 替换为您尝试登录的密码
    
    print(f"尝试登录: 用户名='{username}', 密码='{password}'")
    
    # 第一步：检查用户是否存在
    user = User.get_by_username(username)
    print(f"用户查询结果: {user}")
    
    if user:
        print(f"找到用户: ID={user.id}, 用户名={user.username}, 类型={user.user_type}")
        
        # 第二步：检查密码验证
        password_result = user.check_password(password)
        print(f"密码验证结果: {password_result}")
        
        # 第三步：直接查询数据库中的密码
        from app import mysql
        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        db_result = cur.fetchone()
        cur.close()
        
        if db_result:
            stored_password = db_result['password']
            print(f"数据库中存储的密码: '{stored_password}'")
            print(f"输入的密码: '{password}'")
            print(f"密码是否匹配: {stored_password == password}")
        else:
            print("数据库中未找到该用户")
    else:
        print("用户不存在")