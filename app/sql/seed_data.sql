-- ===================================
-- 测试数据
-- ===================================

USE restaurant_db;

-- 清空表中的所有数据（如果需要）
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE Recommendations;
TRUNCATE TABLE Favourites;
TRUNCATE TABLE Replies;
TRUNCATE TABLE Reviews;
TRUNCATE TABLE Dishes;
TRUNCATE TABLE MerchantRestaurant;
TRUNCATE TABLE Restaurants;
TRUNCATE TABLE Users;
SET FOREIGN_KEY_CHECKS = 1;

-- 插入用户数据
INSERT INTO Users (username, password, email, phone, user_type) VALUES
-- 管理员
('admin', '$2b$12$1oE9vBM6oHmJRzT0.jZ2f.81Xjw9xY4OiRlJ9GnD.BBMOrjSCoca2', 'admin@example.com', '13800000000', 'admin'),
-- 商家
('merchant1', '$2b$12$iQEv3EIIGs9QQI5Azl8YG.41vH1jQ0ZuFY12UNPdOJlSzB1gKLUri', 'merchant1@example.com', '13800000001', 'merchant'),
('merchant2', '$2b$12$1oE9vBM6oHmJRzT0.jZ2f.Y1ztuoRh7.7g1ZiG7/q71bD7NubXIIm', 'merchant2@example.com', '13800000002', 'merchant'),
('merchant3', '$2b$12$1oE9vBM6oHmJRzT0.jZ2f.uqSzGl4b5vQzx.9/imzpBBCNxQBeY7C', 'merchant3@example.com', '13800000003', 'merchant'),
-- 普通用户
('user1', '$2b$12$1oE9vBM6oHmJRzT0.jZ2f.e0ZJeI2IWi9MnFXu39bKqxW6h2qx5bG', 'user1@example.com', '13900000001', 'user'),
('user2', '$2b$12$1oE9vBM6oHmJRzT0.jZ2f.7RnL6GdYGFzHzHjJGTLu3N4QYc.Q7lC', 'user2@example.com', '13900000002', 'user'),
('user3', '$2b$12$1oE9vBM6oHmJRzT0.jZ2f.tQE9ttiLHlX5PUv1tJcw0D6WZvPLSxW', 'user3@example.com', '13900000003', 'user'),
('user4', '$2b$12$1oE9vBM6oHmJRzT0.jZ2f.0CO8jqgV4QeZ1ZFxk9dt0EaIyDw23ty', 'user4@example.com', '13900000004', 'user'),
('user5', '$2b$12$1oE9vBM6oHmJRzT0.jZ2f.Vpq2XH1LzUSYDA6TWyLjCxxsRCEwPxe', 'user5@example.com', '13900000005', 'user');

-- 插入餐厅数据
INSERT INTO Restaurants (name, address, phone, opening_hours, img_url, type) VALUES
('川香园', '北京市海淀区中关村大街1号', '010-12345678', '10:00-22:00', '/static/images/2.jpg', '川菜'),
('江南味道', '上海市浦东新区张杨路500号', '021-87654321', '11:00-21:30', '/static/images/2.jpg', '江浙菜'),
('北方面馆', '天津市和平区南京路89号', '022-55667788', '08:00-20:00', '/static/images/2.jpg', '面食'),
('海鲜世家', '广东省广州市越秀区北京路123号', '020-98765432', '11:30-23:00', '/static/images/2.jpg', '粤菜'),
('老北京烤鸭', '北京市东城区王府井大街10号', '010-11223344', '11:00-21:00', '/static/images/2.jpg', '京菜');

-- 关联商家和餐厅
INSERT INTO MerchantRestaurant (merchant_id, restaurant_id) VALUES
(2, 1), -- merchant1 管理川香园
(2, 2), -- merchant1 也管理江南味道
(3, 3), -- merchant2 管理北方面馆
(4, 4), -- merchant3 管理海鲜世家
(4, 5); -- merchant3 也管理老北京烤鸭

-- 插入菜品数据
INSERT INTO Dishes (name, price, description, rest_id, img_url) VALUES
-- 川香园的菜品
('麻婆豆腐', 38.00, '经典川菜，麻辣鲜香', 1, '/static/images/1.jpg'),
('鱼香肉丝', 42.00, '甜酸可口，下饭佳品', 1, '/static/images/1.jpg'),
('水煮牛肉', 68.00, '麻辣鲜香，肉质鲜嫩', 1, '/static/images/1.jpg'),

-- 江南味道的菜品
('西湖醋鱼', 88.00, '杭帮名菜，鲜美可口', 2, '/static/images/1.jpg'),
('东坡肉', 58.00, '肥而不腻，入口即化', 2, '/static/images/1.jpg'),
('龙井虾仁', 66.00, '清新爽口，茶香四溢', 2, '/static/images/1.jpg'),

-- 北方面馆的菜品
('牛肉拉面', 28.00, '汤浓面劲道，牛肉鲜嫩', 3, '/static/images/1.jpg'),
('羊肉泡馍', 32.00, '陕西名吃，回味无穷', 3, '/static/images/1.jpg'),
('炸酱面', 26.00, '北京特色，浓郁可口', 3, '/static/images/1.jpg'),

-- 海鲜世家的菜品
('清蒸大闸蟹', 188.00, '秋季时令，肥美多汁', 4, '/static/images/1.jpg'),
('白灼虾', 98.00, '鲜甜可口，肉质紧实', 4, '/static/images/1.jpg'),
('葱姜炒蟹', 168.00, '香气扑鼻，回味无穷', 4, '/static/images/1.jpg'),

-- 老北京烤鸭的菜品
('北京烤鸭', 238.00, '外脆里嫩，香而不腻', 5, '/static/images/1.jpg'),
('炒合菜', 42.00, '老北京传统小菜', 5, '/static/images/1.jpg'),
('豆汁', 8.00, '北京特色小吃，风味独特', 5, '/static/images/1.jpg');

-- 插入评论数据
INSERT INTO Reviews (user_id, rest_id, rating, comment, review_time, updated_time) VALUES
-- 川香园的评论
(5, 1, 9, '麻婆豆腐很正宗，服务也很热情，下次还会来！', NOW(), NULL),
(6, 1, 8, '菜品味道不错，但是环境可以再提升一下', NOW(), NULL),
(7, 1, 7, '价格有点贵，但是菜品质量确实不错', NOW(), NOW()),

-- 江南味道的评论
(5, 2, 10, '西湖醋鱼太美味了，完全是正宗的杭帮菜！', NOW(), NULL),
(8, 2, 9, '环境很优雅，服务态度也很好，推荐！', NOW(), NULL),

-- 北方面馆的评论
(6, 3, 8, '牛肉拉面汤头很浓郁，面条筋道', NOW(), NULL),
(9, 3, 6, '位置有点难找，但是菜品味道不错', NOW(), NULL),
(7, 3, 7, '羊肉泡馍很地道，店内比较拥挤', NOW(), NOW()),

-- 海鲜世家的评论
(8, 4, 9, '海鲜新鲜，烹饪手法也很到位', NOW(), NULL),
(9, 4, 10, '白灼虾真的太好吃了，服务一流！', NOW(), NULL),

-- 老北京烤鸭的评论
(5, 5, 10, '烤鸭皮脆肉嫩，正宗的北京味道', NOW(), NULL),
(6, 5, 8, '店面装修很有老北京风格，菜品正宗', NOW(), NULL),
(7, 5, 9, '豆汁很有特色，烤鸭做的也很地道', NOW(), NULL);

-- 插入商家回复
INSERT INTO Replies (review_id, rest_id, content, reply_time, updated_at) VALUES
(1, 1, '感谢您的好评！我们会继续努力提供优质的服务和美食', NOW(), NULL),
(2, 1, '非常感谢您的建议，我们会注意改进用餐环境', NOW(), NULL),
(4, 2, '谢谢您的肯定，期待您的再次光临', NOW(), NULL),
(6, 3, '感谢您的评价，欢迎再来品尝我们的其他面食', NOW(), NULL),
(9, 4, '非常感谢您的好评，我们一直坚持选用最新鲜的食材', NOW(), NULL),
(11, 5, '谢谢您的好评！传统工艺制作的烤鸭就是不一样', NOW(), NULL);

-- 收藏餐厅
INSERT INTO Favourites (user_id, rest_id) VALUES
(5, 1), (5, 5),
(6, 2), (6, 3),
(7, 4), (7, 1),
(8, 2), (8, 5),
(9, 3), (9, 4);

-- 推荐菜品
INSERT INTO Recommendations (user_id, dish_id) VALUES
(5, 1), (5, 13),
(6, 4), (6, 7),
(7, 10), (7, 3),
(8, 5), (8, 15),
(9, 9), (9, 11);

SET SQL_SAFE_UPDATES = 0;
-- 更新餐厅评分和评论数(如果触发器未生效)
UPDATE Restaurants r
SET r.rating = (SELECT AVG(rv.rating) FROM Reviews rv WHERE rv.rest_id = r.rest_id),
    r.review_count = (SELECT COUNT(*) FROM Reviews rv WHERE rv.rest_id = r.rest_id);
SET SQL_SAFE_UPDATES = 1;