ALTER TABLE users ADD COLUMN password_expires_at TEXT;
UPDATE users
-- SET password_expires_at = datetime('now', '+90 days')
SET password_expires_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '+90 days')
WHERE password_expires_at IS NULL;