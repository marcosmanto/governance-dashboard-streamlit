CREATE TABLE audit_integrity (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    status TEXT NOT NULL DEFAULT 'OK', -- 'OK' | 'VIOLATED'
    last_check_at TEXT,
    violated_at TEXT,
    violated_event_id INTEGER,
    reason TEXT
);

-- Inicializa com estado saudável
INSERT INTO audit_integrity (id, status, last_check_at)
VALUES (1, 'OK', CURRENT_TIMESTAMP);