-- BDIC-SE 知识库门户网站数据库结构
-- MySQL 建表SQL

-- 创建数据库
CREATE DATABASE IF NOT EXISTS bdic_se_kb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bdic_se_kb;

-- 1. 讲师表
CREATE TABLE instructors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '讲师姓名',
    avatar_url VARCHAR(500) DEFAULT NULL COMMENT '讲师头像图片链接',
    bio TEXT DEFAULT NULL COMMENT '讲师简介',
    email VARCHAR(150) DEFAULT NULL COMMENT '邮箱',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_email (email)
) ENGINE=InnoDB COMMENT='讲师信息表';

-- 2. 课程表
CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL COMMENT '课程标题',
    description TEXT DEFAULT NULL COMMENT '课程描述',
    cover_images JSON DEFAULT NULL COMMENT '封面图片列表(JSON格式)',
    stage ENUM('S1', 'S2', 'S3', 'S4') NOT NULL COMMENT '学期阶段',
    instructor_id INT NOT NULL COMMENT '讲师ID',
    average_rating DECIMAL(3,2) DEFAULT 0.00 COMMENT '平均评分(0.00-5.00)',
    total_reviews INT DEFAULT 0 COMMENT '总评价数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (instructor_id) REFERENCES instructors(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_stage (stage),
    INDEX idx_instructor (instructor_id),
    INDEX idx_rating (average_rating)
) ENGINE=InnoDB COMMENT='课程信息表';

-- 3. 用户表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(150) NOT NULL UNIQUE COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '加密后的密码',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB COMMENT='用户信息表';

-- 4. 评价表（合并评分和评论）
CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    course_id INT NOT NULL COMMENT '课程ID',
    rating TINYINT CHECK (rating >= 1 AND rating <= 5) DEFAULT NULL COMMENT '评分(1-5分)',
    content TEXT DEFAULT NULL COMMENT '评论内容',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY unique_user_course (user_id, course_id) COMMENT '每个用户对每门课程只能评价一次',
    INDEX idx_course (course_id),
    INDEX idx_rating (rating),
    INDEX idx_created (created_at)
) ENGINE=InnoDB COMMENT='课程评价表';

-- 插入一些示例数据

-- 示例讲师数据
INSERT INTO instructors (name, avatar_url, bio, email) VALUES
('Dr. Smith', '/static/images/avatars/smith.jpg', 'Computer Science Professor with 10+ years experience', 'smith@university.edu'),
('Prof. Johnson', '/static/images/avatars/johnson.jpg', 'Mathematics Department Head', 'johnson@university.edu'),
('Dr. Wang', '/static/images/avatars/wang.jpg', 'Software Engineering Expert', 'wang@university.edu'),
('Prof. Brown', '/static/images/avatars/brown.jpg', 'Data Science Researcher', 'brown@university.edu');

-- 示例课程数据
INSERT INTO courses (title, description, cover_images, stage, instructor_id) VALUES
('Programming Fundamentals', 'Introduction to programming concepts and Python basics', 
 '["cover1.jpg", "cover2.jpg", "cover3.jpg"]', 'S1', 1),
('Discrete Mathematics', 'Mathematical foundations for computer science', 
 '["math1.jpg", "math2.jpg"]', 'S1', 2),
('Data Structures and Algorithms', 'Core computer science concepts and problem solving', 
 '["ds1.jpg", "ds2.jpg", "ds3.jpg"]', 'S2', 1),
('Database Systems', 'Relational databases and SQL programming', 
 '["db1.jpg", "db2.jpg"]', 'S2', 3),
('Software Engineering', 'Software development lifecycle and best practices', 
 '["se1.jpg", "se2.jpg"]', 'S3', 3),
('Machine Learning', 'Introduction to AI and machine learning algorithms', 
 '["ml1.jpg", "ml2.jpg", "ml3.jpg"]', 'S3', 4),
('Advanced Programming', 'Advanced software development concepts', 
 '["adv1.jpg", "adv2.jpg"]', 'S4', 1),
('Capstone Project', 'Final year project and research', 
 '["cap1.jpg", "cap2.jpg"]', 'S4', 3);

-- 示例用户数据
INSERT INTO users (username, email, password_hash) VALUES
('student1', 'student1@example.com', '$2b$12$example_hash_here'),
('student2', 'student2@example.com', '$2b$12$example_hash_here'),
('student3', 'student3@example.com', '$2b$12$example_hash_here');

-- 示例评价数据
INSERT INTO reviews (user_id, course_id, rating, content) VALUES
(1, 1, 5, '这门课程非常好！老师讲解清晰，内容丰富。'),
(2, 1, 4, '不错的入门课程，但是作业有点多。'),
(1, 2, 3, '数学内容比较难，需要多花时间理解。'),
(3, 1, 5, '强烈推荐！对编程入门很有帮助。'),
(2, 3, 4, '算法讲解得很详细，但需要多练习。');

-- 更新课程的平均评分和评价数量
UPDATE courses SET 
    average_rating = (
        SELECT COALESCE(AVG(rating), 0) 
        FROM reviews 
        WHERE course_id = courses.id AND rating IS NOT NULL
    ),
    total_reviews = (
        SELECT COUNT(*) 
        FROM reviews 
        WHERE course_id = courses.id
    );
