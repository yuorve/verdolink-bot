CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    humidity REAL,
    light REAL
);

CREATE TABLE IF NOT EXISTS current_state (
    id INTEGER PRIMARY KEY,
    humidity REAL,
    light REAL,
    last_action TEXT,
    chat_id INTEGER,
    last_notified_status TEXT
);

INSERT OR IGNORE INTO current_state (id, humidity, light, last_action, chat_id, last_notified_status)
VALUES (1, 50.0, 100.0, 'Initial', NULL, 'Ideal');