DELIMITER $$

-- 插入评论时更新餐厅评分
CREATE TRIGGER trg_after_insert_review
AFTER INSERT ON Reviews
FOR EACH ROW
BEGIN
  UPDATE Restaurants
  SET rating = (
      SELECT AVG(rating)
      FROM Reviews
      WHERE rest_id = NEW.rest_id
  ),
      review_count = (
      SELECT COUNT(*)
      FROM Reviews
      WHERE rest_id = NEW.rest_id
  )
  WHERE rest_id = NEW.rest_id;
END$$

-- 更新评论评分时更新餐厅评分
CREATE TRIGGER trg_after_update_review
AFTER UPDATE ON Reviews
FOR EACH ROW
BEGIN
  UPDATE Restaurants
  SET rating = (
      SELECT AVG(rating)
      FROM Reviews
      WHERE rest_id = NEW.rest_id
  )
  WHERE rest_id = NEW.rest_id;
END$$

-- 删除评论时更新餐厅评分，并自动删除商家回复
CREATE TRIGGER trg_after_delete_review
AFTER DELETE ON Reviews
FOR EACH ROW
BEGIN
  DELETE FROM Replies
  WHERE review_id = OLD.review_id;

  UPDATE Restaurants
  SET rating = (
      SELECT IFNULL(AVG(rating), 0)
      FROM Reviews
      WHERE rest_id = OLD.rest_id
  ),
      review_count = (
      SELECT COUNT(*)
      FROM Reviews
      WHERE rest_id = OLD.rest_id
  )
  WHERE rest_id = OLD.rest_id;
END$$

DELIMITER ;

DELIMITER $$

-- 收藏餐厅时更新餐厅的收藏数
CREATE TRIGGER trg_after_insert_favourite
AFTER INSERT ON Favourites
FOR EACH ROW
BEGIN
  UPDATE Restaurants
  SET star_count = (
      SELECT COUNT(*)
      FROM Favourites
      WHERE rest_id = NEW.rest_id
  )
  WHERE rest_id = NEW.rest_id;
END$$

-- 取消收藏餐厅时更新餐厅的收藏数
CREATE TRIGGER trg_after_delete_favourite
AFTER DELETE ON Favourites
FOR EACH ROW
BEGIN
  UPDATE Restaurants
  SET star_count = (
      SELECT COUNT(*)
      FROM Favourites
      WHERE rest_id = OLD.rest_id
  )
  WHERE rest_id = OLD.rest_id;
END$$

-- 推荐菜品时更新菜品的推荐数
CREATE TRIGGER trg_after_insert_recommendation
AFTER INSERT ON Recommendations
FOR EACH ROW
BEGIN
  UPDATE Dishes
  SET rec_count = (
      SELECT COUNT(*)
      FROM Recommendations
      WHERE dish_id = NEW.dish_id
  )
  WHERE dish_id = NEW.dish_id;
END$$

-- 取消推荐菜品时更新菜品的推荐数
CREATE TRIGGER trg_after_delete_recommendation
AFTER DELETE ON Recommendations
FOR EACH ROW
BEGIN
  UPDATE Dishes
  SET rec_count = (
      SELECT COUNT(*)
      FROM Recommendations
      WHERE dish_id = OLD.dish_id
  )
  WHERE dish_id = OLD.dish_id;
END$$

DELIMITER ;

-- 邮箱格式检查触发器
DELIMITER $$
CREATE TRIGGER trg_check_email_format
BEFORE INSERT ON Users
FOR EACH ROW
BEGIN
    IF NEW.email IS NOT NULL AND NEW.email NOT REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '邮箱格式不正确';
    END IF;
END$$

-- 同样检查更新操作
CREATE TRIGGER trg_check_email_format_update
BEFORE UPDATE ON Users
FOR EACH ROW
BEGIN
    IF NEW.email IS NOT NULL AND NEW.email NOT REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '邮箱格式不正确';
    END IF;
END$$
DELIMITER ;