CREATE TABLE role_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    requested_role TEXT NOT NULL,
    justification TEXT,
    status TEXT DEFAULT 'PENDING', -- PENDING, APPROVED, REJECTED
    created_at TEXT NOT NULL,
    processed_at TEXT,
    processed_by TEXT,
    FOREIGN KEY(username) REFERENCES users(username)
);
