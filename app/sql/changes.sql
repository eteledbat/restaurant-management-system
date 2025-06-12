USE restaurant_db;
ALTER TABLE Users MODIFY password VARCHAR(512);

UPDATE Users SET password = 'pbkdf2:sha256:260000$851AcXXee1g4cEql$6b18a99590c76a8eebb843d76b3ed973388e8aaaa61d4974dc81d8811f77e820' WHERE username = 'admin';
UPDATE Users SET password = 'pbkdf2:sha256:260000$UWOEGsv9J7D3yfjy$1e9ea1068a51cbfb61c6f6e0e87e58674dec13f29b62624be0742d7c0817403e' WHERE username = 'merchant1';
UPDATE Users SET password = 'pbkdf2:sha256:260000$Yo43wilIH7k0sRvj$b75080a1b7cf8a74d59f7f07ac4fcf5365faaaf00499bf235b0c46fb30deffa2' WHERE username = 'merchant2';
UPDATE Users SET password = 'pbkdf2:sha256:260000$mP31VSHbdwHvA5so$d06d7ff07075f15c801bcac16764200c32ca19928fec15e578f1010a7a80833d' WHERE username = 'user1';
UPDATE Users SET password = 'pbkdf2:sha256:260000$HWyOjfoDdHBrdtWZ$cc77996a7b8cb21fcdaea1769af19bff46911c18d0b68cc9be17b5a57ef5efc6' WHERE username = 'user2';

UPDATE Users SET password = 'pbkdf2:sha256:260000$mP31VSHbdwHvA5so$d06d7ff07075f15c801bcac16764200c32ca19928fec15e578f1010a7a80833d' WHERE username IN ('user3', 'user4', 'user5');
UPDATE Users SET password = 'pbkdf2:sha256:260000$Yo43wilIH7k0sRvj$b75080a1b7cf8a74d59f7f07ac4fcf5365faaaf00499bf235b0c46fb30deffa2' WHERE username = 'merchant3';

-- 创建问题报告表
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
);

-- 创建餐厅类别表
CREATE TABLE IF NOT EXISTS RestaurantCategories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入现有的餐厅类别
INSERT IGNORE INTO RestaurantCategories (category_name, description) 
SELECT DISTINCT type, CONCAT(type, '类型餐厅') 
FROM Restaurants 
WHERE type IS NOT NULL AND type != '';