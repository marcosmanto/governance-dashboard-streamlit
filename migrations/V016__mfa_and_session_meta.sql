-- Adiciona suporte a MFA na tabela de usuários
ALTER TABLE users ADD COLUMN mfa_secret TEXT;
ALTER TABLE users ADD COLUMN mfa_enabled INTEGER DEFAULT 0;

-- Adiciona metadados na tabela de sessões para auditoria
ALTER TABLE user_sessions ADD COLUMN ip_address TEXT;
ALTER TABLE user_sessions ADD COLUMN user_agent TEXT;