# 📘 Governance Dashboard

## 🧠 Visão Geral

O **Governance Dashboard** é uma plataforma fullstack (FastAPI + Streamlit) voltada para:

- Governança de dados
- Trilha de auditoria imutável
- Controle avançado de sessões
- Segurança institucional
- Integridade criptográfica verificável

Arquitetura simplificada:

```
Streamlit → FastAPI → SQLite (WAL)
                     ↓
               Auditoria Hash Chain
                     ↓
            Integrity Guard (Auto-Lock)
```

---

# 🚀 Execução do Projeto

## Execução (Windows / Linux / macOS)

Execute backend e frontend em terminais separados.

### Windows (CMD)

Backend:

```
set PYTHONPATH=%CD% && uvicorn backend.main:app --reload
```

Frontend:

```
set PYTHONPATH=%CD% && streamlit run frontend/Home.py
```

---

### Linux/macOS

Backend:

```
export PYTHONPATH="$PWD" && uvicorn backend.main:app --reload
```

Frontend:

```
export PYTHONPATH="$PWD" && streamlit run frontend/Home.py
```

Portas padrão:

- Backend: http://127.0.0.1:8000
- Frontend: http://localhost:8501

---

# 🗄️ Sistema de Migrações

O projeto possui um sistema próprio de versionamento de banco (`migrate.py`).

Cada migração:

- É versionada (`V001`, `V002`, etc.)
- Possui checksum SHA-256
- É registrada na tabela `schema_migrations`
- Gera backup automático antes de aplicar

## Inicializar banco do zero

```
python migrate.py --db ./data/dados.db --migrations ./migrations --init-if-missing
```

Isso:

1. Cria a pasta `data/` se necessário
2. Cria o banco SQLite
3. Aplica todas as migrações
4. Registra histórico

## Listar migrações

```
python migrate.py --db ./data/dados.db --migrations ./migrations --list
```

## Dry-run

```
python migrate.py --db ./data/dados.db --migrations ./migrations --dry-run
```

---

# 🔐 Segurança da Aplicação

## 🛡️ Rate Limiting (Proteção contra Força Bruta)

O backend utiliza a biblioteca **slowapi** para proteger rotas críticas:

Rotas protegidas:

- `/login`
- `/refresh`

Limite configurado:

```
5 requisições por minuto por IP
```

Se excedido:

- Retorna HTTP 429 (Too Many Requests)

Isso protege contra ataques de força bruta.

---

## 🔑 Autenticação e Sessões

O sistema implementa:

- Access Token de curta duração
- Refresh Token
- Sessões persistidas em banco
- Revogação individual de sessão
- Revogação global
- Expiração automática por idade da senha
- Aviso de senha prestes a expirar
- Forçar troca de senha

---

# 🔁 Reset de Senha Seguro

Fluxo:

1. `/forgot-password` gera token criptograficamente seguro
2. Apenas o hash do token é persistido
3. Token possui expiração
4. Token é de uso único
5. Evento é auditado

## 🧪 Comportamento em Ambiente DEV

Quando `ENV=dev`:

- O sistema **não envia e-mail real**
- O token de reset é exibido/logado no console do backend

Isso permite testar o fluxo localmente sem SMTP real.

Para produção:

- Configure SMTP no `.env`
- O token será enviado por e-mail real

---

# 🔐 Auditoria e Integridade Criptográfica

O sistema implementa uma cadeia de hash estilo blockchain.

Cada evento contém:

- `prev_hash`
- `event_hash`
- Payload canonicalizado (JSON ordenado)
- SHA-256 determinístico

Qualquer modificação retroativa invalida toda a cadeia subsequente.

---

# 🧪 Verificação de Integridade

Endpoint administrativo:

```
GET /admin/audit/verify
```

Ele:

- Recalcula toda a cadeia
- Detecta adulterações
- Detecta quebra de encadeamento
- Atualiza tabela `audit_integrity`

---

# 🛡️ Bloqueio Automático (Integrity Guard)

O sistema possui um mecanismo de proteção ativa.

Funcionamento:

1. Se a verificação detectar violação:
   - `status = VIOLATED` na tabela `audit_integrity`
2. O middleware `IntegrityGuardMiddleware` intercepta:
   - POST
   - PUT
   - DELETE
   - PATCH
3. Retorna:

```
HTTP 423 Locked
```

Mensagem:

```
SISTEMA BLOQUEADO: Violação de integridade detectada na auditoria.
```

## Rotas permitidas mesmo em bloqueio

- `/login`
- `/refresh`
- `/logout`

Isso permite que o administrador entre e investigue o incidente.

---

# 👤 Gestão de Usuários

- Perfil editável
- Upload de avatar
- Listagem de sessões ativas
- Revogação remota de sessões
- Limpeza de sessões expiradas
- Política de rotação de senha

---

# 🧱 Banco de Dados

- SQLite com WAL habilitado
- Índices estratégicos
- Upsert via VIEW + trigger
- Backup automático nas migrações
- Verificação de checksum de migrações

---

# ⚙️ Variáveis de Ambiente (.env)

Exemplo:

```
ENV=dev

JWT_SECRET=uma-chave-secreta-forte
JWT_ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

DB_BACKEND=sqlite
DB_DSN=./data/dados.db
```

---

# 🏛️ Nível Arquitetural

Este projeto evoluiu de um simples dashboard para:

**Plataforma de Governança com Trilha Imutável e Reação Automática a Violação**

Recursos implementados:

- Auditoria criptográfica encadeada
- Verificação de integridade
- Circuit breaker automático
- Rate limiting contra força bruta
- Reset de senha seguro
- Controle avançado de sessões
- Sistema próprio de migrações

---

# 📦 Dependências Principais

- FastAPI
- Streamlit
- slowapi
- python-jose
- passlib (bcrypt)
- SQLite
- Uvicorn