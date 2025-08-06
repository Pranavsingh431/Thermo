-- Thermal Inspection System Database Schema

-- Users and Authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'operator',
    substation_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Substations
CREATE TABLE substations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    location VARCHAR(200),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transmission Towers
CREATE TABLE towers (
    id SERIAL PRIMARY KEY,
    substation_id INTEGER REFERENCES substations(id),
    tower_number VARCHAR(50) NOT NULL,
    tower_type VARCHAR(20), -- '1C', '2C', '4C'
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    installation_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Thermal Scans
CREATE TABLE thermal_scans (
    id SERIAL PRIMARY KEY,
    tower_id INTEGER REFERENCES towers(id),
    operator_id INTEGER REFERENCES users(id),
    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ambient_temperature DECIMAL(5, 2),
    weather_condition VARCHAR(50),
    line_selection VARCHAR(10), -- 'incoming', 'outgoing'
    phase_selection VARCHAR(5), -- 'R', 'Y', 'B'
    equipment_used VARCHAR(100) DEFAULT 'FLIR T560',
    scan_status VARCHAR(20) DEFAULT 'completed',
    notes TEXT
);

-- Thermal Images
CREATE TABLE thermal_images (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER REFERENCES thermal_scans(id),
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(200) NOT NULL,
    file_size INTEGER,
    image_width INTEGER,
    image_height INTEGER,
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(20) DEFAULT 'pending' -- 'pending', 'processing', 'completed', 'failed'
);

-- AI Detection Results
CREATE TABLE ai_detections (
    id SERIAL PRIMARY KEY,
    image_id INTEGER REFERENCES thermal_images(id),
    component_type VARCHAR(50), -- 'nuts_bolts', 'mid_span_joint', 'polymer_insulator'
    detection_confidence DECIMAL(5, 4),
    bounding_box_x INTEGER,
    bounding_box_y INTEGER,
    bounding_box_width INTEGER,
    bounding_box_height INTEGER,
    max_temperature DECIMAL(5, 2),
    hotspot_classification VARCHAR(20), -- 'normal', 'potential', 'critical'
    model_version VARCHAR(20),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Logs
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    log_level VARCHAR(10), -- 'INFO', 'WARNING', 'ERROR'
    message TEXT,
    module VARCHAR(50),
    user_id INTEGER REFERENCES users(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_thermal_scans_tower_date ON thermal_scans(tower_id, scan_date);
CREATE INDEX idx_thermal_images_scan ON thermal_images(scan_id);
CREATE INDEX idx_ai_detections_image ON ai_detections(image_id);
CREATE INDEX idx_ai_detections_hotspot ON ai_detections(hotspot_classification);
CREATE INDEX idx_system_logs_timestamp ON system_logs(timestamp);

-- Sample data for Mumbai substations
INSERT INTO substations (name, code, location) VALUES
('Kalwa Substation', 'KLW', 'Kalwa, Thane'),
('Mahape Substation', 'MHP', 'Mahape, Navi Mumbai'),
('Taloja Substation', 'TLJ', 'Taloja, Navi Mumbai'),
('Kharghar Substation', 'KHR', 'Kharghar, Navi Mumbai'),
('Dharavi Substation', 'DHR', 'Dharavi, Mumbai'),
('Ghatkopar Substation', 'GHT', 'Ghatkopar, Mumbai'); 