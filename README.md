# 🍽️ 餐饮信息管理系统

一个功能完善的餐饮信息管理系统，支持用户、商家和管理员三种角色，提供餐厅浏览、评论、收藏、管理等全方位功能。

## ✨ 功能特色

### 👥 多角色系统
- **普通用户**：浏览餐厅、查看菜品、发表评论、收藏餐厅
- **商家用户**：管理餐厅信息、菜品管理、回复用户评论
- **管理员**：系统管理、用户管理、餐厅审核、分类管理

### 🔍 核心功能
- **智能搜索**：支持餐厅名称、菜品、地址多维度搜索
- **分类浏览**：按餐厅类型快速筛选
- **评分排行**：基于用户评分的餐厅排行榜
- **个人中心**：收藏管理、评论历史、个人信息
- **实时互动**：用户评论与商家回复系统

### 🎨 用户体验
- 响应式设计，支持手机、平板、电脑
- 直观的用户界面和流畅的交互体验
- 图片上传与展示功能
- 实时消息提示系统

## 🏗️ 技术架构

### 后端技术栈
- **框架**：Flask (Python Web框架)
- **数据库**：MySQL
- **认证**：Flask-Login (用户会话管理)
- **文件上传**：Werkzeug
- **模板引擎**：Jinja2

### 前端技术栈
- **UI框架**：Bootstrap 5
- **图标**：Font Awesome
- **JavaScript**：原生JS + Bootstrap组件
- **样式**：CSS3 + 自定义样式

### 开发工具
- **版本控制**：Git
- **部署**：支持Render云部署
- **环境管理**：requirements.txt

## 📁 项目结构

```
restaurant-management-system/
├── app/                          # 应用主目录
│   ├── __init__.py              # Flask应用初始化
│   ├── models.py                # 数据模型
│   ├── routes/                  # 路由模块
│   │   ├── __init__.py
│   │   ├── main.py             # 主页路由
│   │   ├── auth.py             # 认证路由
│   │   ├── restaurant.py       # 餐厅相关路由
│   │   ├── review.py           # 评论路由
│   │   ├── user.py             # 用户路由
│   │   ├── merchant.py         # 商家路由
│   │   └── admin.py            # 管理员路由
│   ├── templates/               # HTML模板
│   │   ├── base.html           # 基础模板
│   │   ├── index.html          # 首页
│   │   ├── auth/               # 认证相关页面
│   │   ├── restaurant/         # 餐厅相关页面
│   │   ├── user/               # 用户中心页面
│   │   ├── merchant/           # 商家管理页面
│   │   └── admin/              # 管理后台页面
│   └── static/                 # 静态资源
│       ├── css/                # 样式文件
│       ├── js/                 # JavaScript文件
│       ├── images/             # 图片资源
│       └── uploads/            # 用户上传文件
├── config.py                   # 配置文件
├── run.py                      # 应用启动文件
├── requirements.txt            # Python依赖
├── render.yaml                 # Render部署配置
├── database/                   # 数据库相关
│   └── init.sql               # 数据库初始化脚本
├── README.md                  # 项目说明
├── .gitignore                 # Git忽略文件
└── LICENSE                    # 开源协议
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- MySQL 5.7+
- pip (Python包管理器)

### 本地部署

1. **克隆项目**
   ```bash
   git clone https://github.com/你的用户名/restaurant-management-system.git
   cd restaurant-management-system
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **数据库配置**
   ```bash
   # 创建MySQL数据库
   mysql -u root -p
   CREATE DATABASE restaurant_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   
   # 导入数据库结构
   mysql -u root -p restaurant_db < database/init.sql
   ```

5. **环境变量配置**
   
   创建 `.env` 文件（可选）：
   ```env
   SECRET_KEY=your-secret-key-here
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your-password
   MYSQL_DB=restaurant_db
   ```

6. **启动应用**
   ```bash
   python run.py
   ```

7. **访问系统**
   
   打开浏览器访问：`http://localhost:5000`

### 默认账户

系统提供以下测试账户：

- **管理员**：admin / admin123
- **商家**：merchant1 / merchant123  
- **用户**：user1 / user123

## 🗄️ 数据库设计

### 主要数据表

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| Users | 用户表 | user_id, username, email, user_type |
| Restaurants | 餐厅表 | rest_id, name, address, phone, type |
| Dishes | 菜品表 | dish_id, rest_id, name, price, description |
| Reviews | 评论表 | review_id, user_id, rest_id, rating, comment |
| Replies | 回复表 | reply_id, review_id, content, reply_time |
| RestaurantCategories | 餐厅分类表 | category_id, category_name, description |
| MerchantRestaurant | 商家餐厅关联表 | merchant_id, restaurant_id |

## 🎯 功能模块详解

### 用户端功能
- ✅ 用户注册/登录/登出
- ✅ 餐厅浏览与搜索
- ✅ 分类筛选
- ✅ 餐厅详情查看
- ✅ 菜品浏览
- ✅ 用户评论与评分
- ✅ 餐厅收藏
- ✅ 个人信息管理
- ✅ 评论历史查看

### 商家端功能
- ✅ 商家注册与认证
- ✅ 餐厅信息管理
- ✅ 菜品管理（增删改查）
- ✅ 图片上传
- ✅ 用户评论查看
- ✅ 评论回复功能
- ✅ 餐厅数据统计

### 管理员功能
- ✅ 用户管理（查看、禁用、启用）
- ✅ 餐厅管理（审核、编辑、删除）
- ✅ 分类管理（增删改查）
- ✅ 评论管理（删除不当评论）
- ✅ 商家分配管理
- ✅ 系统数据统计
- ✅ 问题报告处理

## 🔧 配置说明

### 配置文件 (config.py)
```python
class Config:
    SECRET_KEY = 'your-secret-key'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root' 
    MYSQL_PASSWORD = 'password'
    MYSQL_DB = 'restaurant_db'
    UPLOAD_FOLDER = 'app/static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
```

### 支持的图片格式
- PNG, JPG, JPEG, GIF
- 最大文件大小：16MB

## 🚀 部署指南

### Render云部署

1. Fork此项目到您的GitHub
2. 在Render创建新的Web Service
3. 连接您的GitHub仓库
4. 使用项目中的 `render.yaml` 配置文件
5. 配置环境变量
6. 部署即可

### Docker部署 (可选)

```dockerfile
# Dockerfile示例
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "run.py"]
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📝 开发计划

### 待实现功能
- [ ] 在线支付集成
- [ ] 外卖配送功能
- [ ] 实时聊天客服
- [ ] 移动端APP
- [ ] 数据分析报表
- [ ] API接口文档

### 优化计划
- [ ] 性能优化
- [ ] 缓存机制
- [ ] 数据库索引优化
- [ ] 前端框架升级

## 🐛 已知问题

- 图片上传大小限制为16MB
- 部分浏览器兼容性问题
- 报告问题功能待优化

## 📜 开源协议

本项目采用 MIT License 开源协议。

## 👨‍💻 作者信息

- **作者**：[陈烨泓]
- **邮箱**：[cyh2022@mail.ustc.edu.cn]
- **GitHub**：[https://github.com/eteledbat]

## 🙏 致谢

感谢以下开源项目：
- [Flask](https://flask.palletsprojects.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Font Awesome](https://fontawesome.com/)
- [MySQL](https://www.mysql.com/)

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 📧 邮箱：[cyh2022@mail.ustc.edu.cn]
- 🐛 Issue：[https://github.com/eteledbat/restaurant-management-system/issues]

---

⭐ 如果这个项目对您有帮助，请给个Star支持一下！