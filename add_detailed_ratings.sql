-- 扩展评价表：添加三个细化评分字段
-- BDIC-SE Knowledge Base Portal - Reviews Enhancement

-- 添加三个细化评分字段到reviews表
ALTER TABLE reviews 
ADD COLUMN learning_gain TINYINT DEFAULT NULL COMMENT '课程收获评分(1-5分)',
ADD COLUMN workload TINYINT DEFAULT NULL COMMENT '繁忙程度评分(1-5分,1=轻松,5=繁忙)', 
ADD COLUMN difficulty TINYINT DEFAULT NULL COMMENT '课程难度评分(1-5分,1=简单,5=困难)';

-- 添加索引以提升查询性能
ALTER TABLE reviews 
ADD INDEX idx_learning_gain (learning_gain),
ADD INDEX idx_workload (workload),
ADD INDEX idx_difficulty (difficulty);

-- 为MySQL 8.0+版本添加检查约束（可选，MySQL 5.x会忽略）
-- ALTER TABLE reviews 
-- ADD CONSTRAINT chk_learning_gain CHECK (learning_gain IS NULL OR (learning_gain >= 1 AND learning_gain <= 5)),
-- ADD CONSTRAINT chk_workload CHECK (workload IS NULL OR (workload >= 1 AND workload <= 5)),
-- ADD CONSTRAINT chk_difficulty CHECK (difficulty IS NULL OR (difficulty >= 1 AND difficulty <= 5));

-- 更新一些示例数据（可选）
UPDATE reviews SET 
    learning_gain = CASE 
        WHEN rating >= 4 THEN 4 + FLOOR(RAND() * 2)
        WHEN rating = 3 THEN 3 + FLOOR(RAND() * 2) 
        ELSE rating
    END,
    workload = 2 + FLOOR(RAND() * 4),
    difficulty = 2 + FLOOR(RAND() * 4)
WHERE id IN (SELECT id FROM (SELECT id FROM reviews LIMIT 5) AS temp);
