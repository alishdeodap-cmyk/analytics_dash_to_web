-- Migration 003: Add embed_filter column to dashboards
-- Run once: mysql -u DB_USER -p -h RDS_HOST DB_NAME < migrations/003_embed_filter.sql

ALTER TABLE dashboards
    ADD COLUMN embed_filter TEXT DEFAULT NULL AFTER iframe_raw;
