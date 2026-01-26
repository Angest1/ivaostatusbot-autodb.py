CREATE DATABASE IF NOT EXISTS ivaostatusbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ivaostatusbot;

CREATE TABLE IF NOT EXISTS snapshots_day (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pilots_day (
    id INT AUTO_INCREMENT PRIMARY KEY,
    snapshot_id INT NOT NULL,
    created_at DATETIME,
    user_id VARCHAR(20),
    callsign VARCHAR(20),
    departure VARCHAR(4),
    arrival VARCHAR(4),
    aircraft VARCHAR(20),
    pob INT DEFAULT 0,
    route TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots_day(id) ON DELETE CASCADE,
    INDEX idx_snapshot_id (snapshot_id),
    INDEX idx_user_id (user_id),
    INDEX idx_callsign (callsign)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS atcs_day (
    id INT AUTO_INCREMENT PRIMARY KEY,
    snapshot_id INT NOT NULL,
    created_at DATETIME,
    user_id VARCHAR(20),
    callsign VARCHAR(20),
    frequency FLOAT,
    atis TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots_day(id) ON DELETE CASCADE,
    INDEX idx_snapshot_id (snapshot_id),
    INDEX idx_user_id (user_id),
    INDEX idx_callsign (callsign)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- WEEK Partition (Weekly Reset)
CREATE TABLE IF NOT EXISTS snapshots_week (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pilots_week (
    id INT AUTO_INCREMENT PRIMARY KEY,
    snapshot_id INT NOT NULL,
    created_at DATETIME,
    user_id VARCHAR(20),
    callsign VARCHAR(20),
    departure VARCHAR(4),
    arrival VARCHAR(4),
    aircraft VARCHAR(20),
    pob INT DEFAULT 0,
    route TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots_week(id) ON DELETE CASCADE,
    INDEX idx_snapshot_id (snapshot_id),
    INDEX idx_user_id (user_id),
    INDEX idx_callsign (callsign)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS atcs_week (
    id INT AUTO_INCREMENT PRIMARY KEY,
    snapshot_id INT NOT NULL,
    created_at DATETIME,
    user_id VARCHAR(20),
    callsign VARCHAR(20),
    frequency FLOAT,
    atis TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots_week(id) ON DELETE CASCADE,
    INDEX idx_snapshot_id (snapshot_id),
    INDEX idx_user_id (user_id),
    INDEX idx_callsign (callsign)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- MONTH Partition (Monthly Reset)
CREATE TABLE IF NOT EXISTS snapshots_month (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pilots_month (
    id INT AUTO_INCREMENT PRIMARY KEY,
    snapshot_id INT NOT NULL,
    created_at DATETIME,
    user_id VARCHAR(20),
    callsign VARCHAR(20),
    departure VARCHAR(4),
    arrival VARCHAR(4),
    aircraft VARCHAR(20),
    pob INT DEFAULT 0,
    route TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots_month(id) ON DELETE CASCADE,
    INDEX idx_snapshot_id (snapshot_id),
    INDEX idx_user_id (user_id),
    INDEX idx_callsign (callsign)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS atcs_month (
    id INT AUTO_INCREMENT PRIMARY KEY,
    snapshot_id INT NOT NULL,
    created_at DATETIME,
    user_id VARCHAR(20),
    callsign VARCHAR(20),
    frequency FLOAT,
    atis TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots_month(id) ON DELETE CASCADE,
    INDEX idx_snapshot_id (snapshot_id),
    INDEX idx_user_id (user_id),
    INDEX idx_callsign (callsign)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
