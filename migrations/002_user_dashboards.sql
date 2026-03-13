-- ============================================================
-- Migration 002: Add user_dashboards table
-- Switches permission model from department-based to user-based
-- Run this ONCE against your admin_powerbi_analytics database
-- ============================================================

USE admin_powerbi_analytics;

-- Direct user <-> dashboard assignment (replaces department_dashboards for access control)
CREATE TABLE IF NOT EXISTS user_dashboards (
    user_id      INT NOT NULL,
    dashboard_id INT NOT NULL,
    PRIMARY KEY (user_id, dashboard_id),
    FOREIGN KEY (user_id)      REFERENCES users(id)      ON DELETE CASCADE,
    FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE
);
