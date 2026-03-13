-- ============================================================
-- Migration 001: Upgrade existing users table + create all new tables
-- Run this ONCE against your admin_powerbi_analytics database
-- ============================================================

USE admin_powerbi_analytics;

-- STEP 1: Rename 'password' column to 'password_hash' in existing users table
ALTER TABLE users CHANGE COLUMN `password` `password_hash` VARCHAR(255) NOT NULL;

-- STEP 2: Add new columns to users table
ALTER TABLE users
    ADD COLUMN email VARCHAR(120) UNIQUE AFTER username,
    ADD COLUMN role ENUM('admin', 'user') NOT NULL DEFAULT 'user' AFTER password_hash,
    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE AFTER role,
    ADD COLUMN force_pw_change BOOLEAN NOT NULL DEFAULT FALSE AFTER is_active,
    ADD COLUMN created_by INT AFTER force_pw_change,
    ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

-- STEP 3: Promote your first user (id=1) to admin and skip forced password change
--         Change the WHERE clause if your admin user has a different id
UPDATE users SET role = 'admin', force_pw_change = FALSE WHERE id = 1;

-- STEP 4: Create departments table (supports sub-departments via parent_id)
CREATE TABLE IF NOT EXISTS departments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    parent_id   INT DEFAULT NULL,
    description TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- STEP 5: User <-> Department mapping (many-to-many)
CREATE TABLE IF NOT EXISTS user_departments (
    user_id       INT NOT NULL,
    department_id INT NOT NULL,
    PRIMARY KEY (user_id, department_id),
    FOREIGN KEY (user_id)       REFERENCES users(id)       ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);

-- STEP 6: Dashboards table
CREATE TABLE IF NOT EXISTS dashboards (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    description TEXT,
    embed_src   TEXT NOT NULL,
    embed_title VARCHAR(200),
    iframe_raw  TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_by  INT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- STEP 7: Dashboard <-> Department permission mapping (many-to-many)
CREATE TABLE IF NOT EXISTS department_dashboards (
    dashboard_id  INT NOT NULL,
    department_id INT NOT NULL,
    PRIMARY KEY (dashboard_id, department_id),
    FOREIGN KEY (dashboard_id)  REFERENCES dashboards(id)  ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);

-- STEP 8: Recently-viewed tracking (one row per user+dashboard pair)
CREATE TABLE IF NOT EXISTS dashboard_views (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    dashboard_id INT NOT NULL,
    last_viewed  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    view_count   INT NOT NULL DEFAULT 1,
    UNIQUE KEY uq_user_dash (user_id, dashboard_id),
    FOREIGN KEY (user_id)      REFERENCES users(id)      ON DELETE CASCADE,
    FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE
);

-- STEP 9: Login audit log
CREATE TABLE IF NOT EXISTS login_audit (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT DEFAULT NULL,
    username   VARCHAR(80),
    ip_address VARCHAR(45),
    status     ENUM('success', 'failed') NOT NULL,
    logged_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
