# 餐饮信息管理系统

本项目是一个基于 Flask + MySQL 构建的 B/S 架构 Web 应用，用于管理餐厅信息、菜品、用户订单等内容，适合作为数据库课程设计或全栈练习项目。

## 🧰 技术栈

- 后端框架：Flask (Python)
- 数据库：MySQL
- 前端页面：HTML + CSS + JavaScript
- 部署平台：Render（支持一键部署）

## 📁 项目结构

```bash
restaurant-management-system/
├── app.py                # 主应用入口
├── templates/            # 存放 HTML 页面
│   └── index.html
├── static/               # 静态文件：CSS/JS
├── requirements.txt      # Python 依赖
├── render.yaml           # Render 部署配置（可选）
└── README.md             # 项目说明文件
```

## 🚀 启动方式（本地运行）

1. 克隆项目
   ```bash
   git clone https://github.com/你的用户名/restaurant-management-system.git
   cd restaurant-management-system
   ```

2. 创建虚拟环境（可选但推荐）
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

4. 启动项目
   ```bash
   python app.py
   ```

5. 打开浏览器访问：
   ```
   http://localhost:5000
   ```

## 🌐 部署方式（Render）

- 登录 [https://render.com](https://render.com)
- 创建 Web Service，绑定你的 GitHub 仓库
- 设置启动命令：
  ```bash
  gunicorn app:app
  ```
- 自动部署完成后即可访问项目

## ✍️ 功能计划（示例）

- [x] 首页展示
- [ ] 餐厅信息管理（增删改查）
- [ ] 菜品管理
- [ ] 用户下单与订单列表
- [ ] 管理员登录后台

## 📌 作者信息

- 开发者：你的名字
- GitHub：https://github.com/eteledbat
