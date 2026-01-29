ALTER TABLE auditoria ADD COLUMN prev_hash TEXT;
ALTER TABLE auditoria ADD COLUMN event_hash TEXT;

-- índice ajuda na verificação sequencial
CREATE INDEX IF NOT EXISTS idx_auditoria_id ON auditoria(id);
