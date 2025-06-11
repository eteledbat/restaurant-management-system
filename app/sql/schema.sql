CREATE DATABASE restaurant_db;
-- 切换到数据库
USE restaurant_db;
-- =========================
-- schema.sql
-- 餐饮信息管理系统建表语句
-- =========================

-- 用户表：包括普通用户、商家、管理员
CREATE TABLE Users (
    user_id      INT PRIMARY KEY AUTO_INCREMENT,
    username     VARCHAR(50) UNIQUE,
    password     VARCHAR(100),
    email        VARCHAR(100),
    phone        VARCHAR(20),
    join_date    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_type    ENUM('user', 'merchant', 'admin') NOT NULL,
    is_deleted   BOOLEAN DEFAULT FALSE
);

-- 餐厅表
CREATE TABLE Restaurants (
    rest_id        INT PRIMARY KEY AUTO_INCREMENT,
    name           VARCHAR(100) NOT NULL,
    address        VARCHAR(255),
    phone          VARCHAR(20),
    opening_hours  VARCHAR(100),
    img_url        TEXT,
    type           VARCHAR(50),
    rating         FLOAT DEFAULT 0.0,
    review_count   INT DEFAULT 0,
    star_count     INT DEFAULT 0
);

-- 商家-餐厅绑定关系表（多对多）
CREATE TABLE MerchantRestaurant (
    merchant_id   INT,
    restaurant_id INT,
    PRIMARY KEY (merchant_id, restaurant_id),
    FOREIGN KEY (merchant_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (restaurant_id) REFERENCES Restaurants(rest_id) ON DELETE CASCADE
);

-- 菜品表
CREATE TABLE Dishes (
    dish_id     INT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    price       DECIMAL(10,2),
    description TEXT,
    rest_id     INT,
    img_url     TEXT,
    rec_count   INT DEFAULT 0,
    FOREIGN KEY (rest_id) REFERENCES Restaurants(rest_id) ON DELETE CASCADE
);

-- 评论表（仅用户可写）
CREATE TABLE Reviews (
    review_id     INT PRIMARY KEY AUTO_INCREMENT,
    user_id       INT,
    rest_id       INT,
    rating        INT CHECK (rating BETWEEN 1 AND 10),
    comment       TEXT,
    timestamp     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    review_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time  TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (rest_id) REFERENCES Restaurants(rest_id) ON DELETE CASCADE
);

-- 回复表（仅商家对自己餐厅的评论可回复）
CREATE TABLE Replies (
    reply_id     INT PRIMARY KEY AUTO_INCREMENT,
    review_id    INT UNIQUE,
    rest_id      INT,
    content      TEXT,
    reply_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (review_id) REFERENCES Reviews(review_id) ON DELETE CASCADE,
    FOREIGN KEY (rest_id) REFERENCES Restaurants(rest_id) ON DELETE CASCADE
);

-- 餐厅收藏表
CREATE TABLE Favourites (
    fav_id    INT PRIMARY KEY AUTO_INCREMENT,
    user_id   INT,
    rest_id   INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (rest_id) REFERENCES Restaurants(rest_id) ON DELETE CASCADE
);

-- 推荐菜品表
CREATE TABLE Recommendations (
    rec_id   INT PRIMARY KEY AUTO_INCREMENT,
    user_id  INT,
    dish_id  INT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (dish_id) REFERENCES Dishes(dish_id) ON DELETE CASCADE
);
