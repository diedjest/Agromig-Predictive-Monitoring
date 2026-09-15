CREATE TABLE IF NOT EXISTS grain_profiles (
    id SERIAL PRIMARY KEY,
    crop_name VARCHAR(50) NOT NULL,
    optimal_temp REAL NOT NULL,
    max_temp REAL NOT NULL,
    target_moisture REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS drying_sessions (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES grain_profiles(id),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'IN_PROGRESS'
);

CREATE TABLE IF NOT EXISTS sensor_logs (
    id BIGSERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES drying_sessions(id),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperature REAL NOT NULL,
    moisture_in REAL NOT NULL,
    moisture_out REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS alert_logs (
    id BIGSERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES drying_sessions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    action_required TEXT NOT NULL
);

INSERT INTO grain_profiles (crop_name, optimal_temp, max_temp, target_moisture)
VALUES ('Wheat', 45.0, 55.0, 14.0)
ON CONFLICT DO NOTHING;