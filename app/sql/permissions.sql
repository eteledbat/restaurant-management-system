-- ===================================
-- 权限管理与数据安全
-- ===================================

-- 创建一个应用使用的数据库用户
CREATE USER IF NOT EXISTS 'restaurant_app'@'localhost' IDENTIFIED BY 'app_password';

-- 授予应用用户访问数据库的权限
GRANT ALL PRIVILEGES ON restaurant_db.* TO 'restaurant_app'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 5. 创建视图限制敏感信息访问
CREATE OR REPLACE VIEW restaurant_db.public_user_info AS
SELECT user_id, username, join_date, user_type
FROM restaurant_db.Users
WHERE is_deleted = FALSE;

-- 6. 创建存储过程进行权限检查

-- 用户发表评论权限检查
DELIMITER $$
CREATE PROCEDURE check_review_permission(IN p_user_id INT)
BEGIN
    DECLARE user_type_val VARCHAR(20);
    DECLARE is_deleted_val BOOLEAN;
    
    SELECT user_type, is_deleted INTO user_type_val, is_deleted_val 
    FROM Users 
    WHERE user_id = p_user_id;
    
    IF user_type_val != 'user' OR is_deleted_val = TRUE THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '只有有效的普通用户账号可以发表评论';
    END IF;
END$$
DELIMITER ;

-- 商家回复评论权限检查
DELIMITER $$
CREATE PROCEDURE check_reply_permission(IN p_user_id INT, IN p_review_id INT)
BEGIN
    DECLARE user_type_val VARCHAR(20);
    DECLARE is_deleted_val BOOLEAN;
    DECLARE rest_id_val INT;
    DECLARE review_rest_id INT;
    DECLARE is_merchant_of_restaurant BOOLEAN DEFAULT FALSE;
    
    SELECT user_type, is_deleted INTO user_type_val, is_deleted_val 
    FROM Users 
    WHERE user_id = p_user_id;
    
    SELECT rest_id INTO review_rest_id 
    FROM Reviews 
    WHERE review_id = p_review_id;
    
    IF review_rest_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '评论不存在';
    END IF;
    
    SELECT COUNT(*) > 0 INTO is_merchant_of_restaurant
    FROM MerchantRestaurant
    WHERE merchant_id = p_user_id AND restaurant_id = review_rest_id;
    
    IF user_type_val != 'merchant' OR is_deleted_val = TRUE OR is_merchant_of_restaurant = FALSE THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '只有该餐厅的商家可以回复此评论';
    END IF;
END$$
DELIMITER ;

-- 删除评论权限检查
DELIMITER $$
CREATE PROCEDURE check_delete_review_permission(IN p_user_id INT, IN p_review_id INT)
BEGIN
    DECLARE user_type_val VARCHAR(20);
    DECLARE review_user_id INT;
    
    SELECT user_type INTO user_type_val
    FROM Users 
    WHERE user_id = p_user_id;
    
    SELECT user_id INTO review_user_id
    FROM Reviews
    WHERE review_id = p_review_id;
    
    IF user_type_val = 'admin' THEN
        -- 管理员可以删除任何评论
        SELECT 1;
    ELSEIF user_type_val = 'user' AND review_user_id = p_user_id THEN
        -- 用户只能删除自己的评论
        SELECT 1;
    ELSE
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '没有权限删除此评论';
    END IF;
END$$
DELIMITER ;

-- 账户注销安全处理
DELIMITER $$
CREATE PROCEDURE deactivate_user(IN p_admin_id INT, IN p_target_user_id INT)
BEGIN
    DECLARE admin_type VARCHAR(20);
    DECLARE target_type VARCHAR(20);
    
    SELECT user_type INTO admin_type
    FROM Users
    WHERE user_id = p_admin_id;
    
    SELECT user_type INTO target_type
    FROM Users
    WHERE user_id = p_target_user_id;
    
    -- 检查权限
    IF admin_type = 'admin' THEN
        -- 管理员可以注销任何账户
        UPDATE Users SET is_deleted = TRUE WHERE user_id = p_target_user_id;
    ELSEIF p_admin_id = p_target_user_id THEN
        -- 用户和商家可以注销自己的账户
        UPDATE Users SET is_deleted = TRUE WHERE user_id = p_admin_id;
    ELSE
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '没有权限执行此操作';
    END IF;
END$$
DELIMITER ;

-- 新增创建评论的存储过程
DELIMITER $$
CREATE PROCEDURE create_review(
    IN p_user_id INT,
    IN p_rest_id INT, 
    IN p_rating INT,
    IN p_comment TEXT
)
BEGIN
    -- 检查用户权限
    CALL check_review_permission(p_user_id);
    
    -- 检查评分范围
    IF p_rating < 1 OR p_rating > 10 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '评分必须在1到10之间';
    END IF;
    
    -- 插入评论
    INSERT INTO Reviews (user_id, rest_id, rating, comment, review_time)
    VALUES (p_user_id, p_rest_id, p_rating, p_comment, NOW());
END$$
DELIMITER ;

-- 新增创建回复的存储过程
DELIMITER $$
CREATE PROCEDURE create_reply(
    IN p_user_id INT,
    IN p_review_id INT,
    IN p_content TEXT
)
BEGIN
    DECLARE v_rest_id INT;
    
    -- 获取评论对应的餐厅ID
    SELECT rest_id INTO v_rest_id
    FROM Reviews
    WHERE review_id = p_review_id;
    
    -- 检查回复权限
    CALL check_reply_permission(p_user_id, p_review_id);
    
    -- 插入回复
    INSERT INTO Replies (review_id, rest_id, content, reply_time)
    VALUES (p_review_id, v_rest_id, p_content, NOW());
END$$
DELIMITER ;

-- 新增更新评论的存储过程
DELIMITER $$
CREATE PROCEDURE update_review(
    IN p_user_id INT,
    IN p_review_id INT,
    IN p_rating INT,
    IN p_comment TEXT
)
BEGIN
    DECLARE v_review_user_id INT;
    
    -- 获取评论作者ID
    SELECT user_id INTO v_review_user_id
    FROM Reviews
    WHERE review_id = p_review_id;
    
    -- 检查权限（只有自己可以修改自己的评论）
    IF v_review_user_id != p_user_id THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '只能修改自己的评论';
    END IF;
    
    -- 检查评分范围
    IF p_rating < 1 OR p_rating > 10 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '评分必须在1到10之间';
    END IF;
    
    -- 更新评论
    UPDATE Reviews
    SET rating = p_rating,
        comment = p_comment,
        updated_time = NOW()
    WHERE review_id = p_review_id;
END$$
DELIMITER ;

-- 新增删除评论的存储过程
DELIMITER $$
CREATE PROCEDURE delete_review(
    IN p_user_id INT,
    IN p_review_id INT
)
BEGIN
    -- 检查删除评论权限
    CALL check_delete_review_permission(p_user_id, p_review_id);
    
    -- 删除评论（触发器会自动删除关联的回复）
    DELETE FROM Reviews
    WHERE review_id = p_review_id;
END$$
DELIMITER ;

-- 新增餐厅收藏存储过程
DELIMITER $$
CREATE PROCEDURE toggle_favourite(
    IN p_user_id INT,
    IN p_rest_id INT,
    IN p_action VARCHAR(10) -- 'add' 或 'remove'
)
BEGIN
    DECLARE v_exists INT;
    
    -- 检查用户是否存在且未被删除
    SELECT COUNT(*) INTO v_exists
    FROM Users
    WHERE user_id = p_user_id AND is_deleted = FALSE;
    
    IF v_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '用户不存在或已被删除';
    END IF;
    
    -- 检查餐厅是否存在
    SELECT COUNT(*) INTO v_exists
    FROM Restaurants
    WHERE rest_id = p_rest_id;
    
    IF v_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '餐厅不存在';
    END IF;
    
    -- 添加或移除收藏
    IF p_action = 'add' THEN
        -- 检查是否已经收藏
        SELECT COUNT(*) INTO v_exists
        FROM Favourites
        WHERE user_id = p_user_id AND rest_id = p_rest_id;
        
        IF v_exists = 0 THEN
            INSERT INTO Favourites (user_id, rest_id, timestamp)
            VALUES (p_user_id, p_rest_id, NOW());
        END IF;
    ELSEIF p_action = 'remove' THEN
        DELETE FROM Favourites
        WHERE user_id = p_user_id AND rest_id = p_rest_id;
    ELSE
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '操作类型必须是 add 或 remove';
    END IF;
END$$
DELIMITER ;

-- 新增菜品推荐存储过程
DELIMITER $$
CREATE PROCEDURE toggle_recommendation(
    IN p_user_id INT,
    IN p_dish_id INT,
    IN p_action VARCHAR(10) -- 'add' 或 'remove'
)
BEGIN
    DECLARE v_exists INT;
    
    -- 检查用户是否存在且未被删除
    SELECT COUNT(*) INTO v_exists
    FROM Users
    WHERE user_id = p_user_id AND is_deleted = FALSE;
    
    IF v_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '用户不存在或已被删除';
    END IF;
    
    -- 检查菜品是否存在
    SELECT COUNT(*) INTO v_exists
    FROM Dishes
    WHERE dish_id = p_dish_id;
    
    IF v_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '菜品不存在';
    END IF;
    
    -- 添加或移除推荐
    IF p_action = 'add' THEN
        -- 检查是否已经推荐
        SELECT COUNT(*) INTO v_exists
        FROM Recommendations
        WHERE user_id = p_user_id AND dish_id = p_dish_id;
        
        IF v_exists = 0 THEN
            INSERT INTO Recommendations (user_id, dish_id)
            VALUES (p_user_id, p_dish_id);
        END IF;
    ELSEIF p_action = 'remove' THEN
        DELETE FROM Recommendations
        WHERE user_id = p_user_id AND dish_id = p_dish_id;
    ELSE
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '操作类型必须是 add 或 remove';
    END IF;
END$$
DELIMITER ;

-- 新增获取商家管理的餐厅存储过程
DELIMITER $$
CREATE PROCEDURE get_merchant_restaurants(
    IN p_user_id INT
)
BEGIN
    DECLARE v_user_type VARCHAR(20);
    
    -- 获取用户类型
    SELECT user_type INTO v_user_type
    FROM Users
    WHERE user_id = p_user_id;
    
    -- 只有商家可以获取关联餐厅
    IF v_user_type != 'merchant' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '只有商家可以获取关联餐厅';
    END IF;
    
    -- 返回商家的餐厅
    SELECT r.*
    FROM Restaurants r
    JOIN MerchantRestaurant mr ON r.rest_id = mr.restaurant_id
    WHERE mr.merchant_id = p_user_id;
END$$
DELIMITER ;