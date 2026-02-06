-- 005_password_reset_tokens.sql

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT NOT NULL,
    token_hash TEXT NOT NULL,

    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT,

    FOREIGN KEY (username) REFERENCES users(username)
);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_username
    ON password_reset_tokens(username);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token_hash
    ON password_reset_tokens(token_hash);
