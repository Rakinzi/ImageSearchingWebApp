CREATE DATABASE IF NOT EXISTS image_search_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE image_search_db;

CREATE USER IF NOT EXISTS 'app_user'@'%' IDENTIFIED BY 'secure_app_password';
GRANT ALL PRIVILEGES ON image_search_db.* TO 'app_user'@'%';

SET GLOBAL sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

FLUSH PRIVILEGES;