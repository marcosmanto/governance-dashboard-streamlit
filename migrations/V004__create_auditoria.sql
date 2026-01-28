CREATE TABLE auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    resource_id INTEGER,
    payload_before TEXT,
    payload_after TEXT,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL
);
