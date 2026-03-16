-- ============================================================
-- DeoDap Analytics — Fresh Database Setup
-- Run this on a brand new (empty) database
-- ============================================================

-- 1. Users
CREATE TABLE IF NOT EXISTS users (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    username         VARCHAR(80)  NOT NULL UNIQUE,
    email            VARCHAR(120) UNIQUE,
    password_hash    VARCHAR(255) NOT NULL,
    role             ENUM('admin','user') NOT NULL DEFAULT 'user',
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    force_pw_change  BOOLEAN NOT NULL DEFAULT FALSE,
    created_by       INT DEFAULT NULL,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. Departments
CREATE TABLE IF NOT EXISTS departments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    parent_id   INT DEFAULT NULL,
    description TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- 3. User <-> Department (many-to-many)
CREATE TABLE IF NOT EXISTS user_departments (
    user_id       INT NOT NULL,
    department_id INT NOT NULL,
    PRIMARY KEY (user_id, department_id),
    FOREIGN KEY (user_id)       REFERENCES users(id)       ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);

-- 4. Dashboards
CREATE TABLE IF NOT EXISTS dashboards (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(150) NOT NULL,
    description  TEXT,
    embed_src    TEXT NOT NULL,
    embed_title  VARCHAR(200),
    iframe_raw   TEXT,
    embed_filter TEXT DEFAULT NULL,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_by   INT DEFAULT NULL,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 5. Dashboard <-> Department (many-to-many)
CREATE TABLE IF NOT EXISTS department_dashboards (
    dashboard_id  INT NOT NULL,
    department_id INT NOT NULL,
    PRIMARY KEY (dashboard_id, department_id),
    FOREIGN KEY (dashboard_id)  REFERENCES dashboards(id)  ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);

-- 6. Dashboard <-> User direct assignment (many-to-many)
CREATE TABLE IF NOT EXISTS user_dashboards (
    user_id      INT NOT NULL,
    dashboard_id INT NOT NULL,
    PRIMARY KEY (user_id, dashboard_id),
    FOREIGN KEY (user_id)      REFERENCES users(id)      ON DELETE CASCADE,
    FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE
);

-- 7. Dashboard view tracking
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

-- 8. Login audit
CREATE TABLE IF NOT EXISTS login_audit (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT DEFAULT NULL,
    username   VARCHAR(80),
    ip_address VARCHAR(45),
    status     ENUM('success','failed') NOT NULL,
    logged_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================
-- After running this SQL, create your admin user by running
-- this on the server:
--
--   cd /var/www/analytics_app
--   source venv/bin/activate
--   python create_admin.py
--
-- ============================================================
