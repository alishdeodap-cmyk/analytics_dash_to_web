-- Run this in MySQL to set up your database
 
CREATE DATABASE IF NOT EXISTS justshop24;
USE justshop24;
 
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
-- Create a dedicated MySQL user for the app
CREATE USER IF NOT EXISTS 'justshop24_user'@'localhost' IDENTIFIED BY 'YOUR_DB_PASSWORD';
GRANT ALL PRIVILEGES ON justshop24.* TO 'justshop24_user'@'localhost';
FLUSH PRIVILEGES;