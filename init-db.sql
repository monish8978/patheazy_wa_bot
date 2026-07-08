-- Initialize Database for BOB Bank Chatbot
CREATE DATABASE IF NOT EXISTS bob_db;
USE bob_db;



-- 2. Create message_logs table for conversation audits
CREATE TABLE IF NOT EXISTS message_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    sender VARCHAR(10) NOT NULL, -- 'USER' or 'BOT'
    message_text TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
