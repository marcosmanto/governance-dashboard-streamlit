# README

## Execução do projeto (Windows / Linux / macOS)

Para executar o **backend (FastAPI/Uvicorn)** e o **frontend (Streamlit)** a partir da **pasta raiz do projeto** (ex.: `.../painel_dados_chatgpt_tutorial` **ou** a pasta **acima** dela), defina o `PYTHONPATH` para que os imports absolutos (`backend.*`, `frontend.*`) funcionem corretamente.

> **Por quê?** O Python procura módulos com base no `sys.path`. Ao rodar scripts a partir de caminhos diferentes, pode faltar o diretório raiz do projeto no `PYTHONPATH`, causando erros como `ModuleNotFoundError: No module named 'frontend'`.

### 1) Windows (Prompt de Comando / CMD)

Abra **dois terminais** (ou abas):

**Backend (Uvicorn):**

```bat
cd caminho\para\pasta-acima-ou-raiz\do\projeto
set PYTHONPATH=%CD% && uvicorn backend.main:app --reload
```

**Frontend (Streamlit):**

```bat
cd caminho\para\pasta-acima-ou-raiz\do\projeto
set "PYTHONPATH=%CD%" && streamlit run frontend\Home.py
```

> Dica (PowerShell):
>
> ```powershell
> $env:PYTHONPATH = (Get-Location).Path
> uvicorn backend.main:app --reload
> # Em outra aba
> $env:PYTHONPATH = (Get-Location).Path
> streamlit run frontend/Home.py
> ```

### 2) Linux / macOS (bash/zsh)

Também em **dois terminais**:

**Backend (Uvicorn):**

```bash
cd /caminho/para/pasta-acima-ou-raiz/do/projeto
export PYTHONPATH="$PWD" && uvicorn backend.main:app --reload
```

**Frontend (Streamlit):**

```bash
cd /caminho/para/pasta-acima-ou-raiz/do/projeto
export PYTHONPATH="$PWD" && streamlit run frontend/app.py
```

### Observações

- Execute **backend** e **frontend** simultaneamente (dois terminais), pois o Streamlit pode chamar a API do FastAPI.
- Se preferir, você pode evitar `PYTHONPATH` com **imports relativos** no `frontend/app.py` (ex.: `from .loaders.registros import ...`), mas manter o `PYTHONPATH` facilita quando há **múltiplos pacotes** (`backend/`, `frontend/`, `migrations/`).
- Se aparecer `ModuleNotFoundError`, verifique:
  1. Você está na **pasta correta**? (`cd` para a raiz do projeto ou **um nível acima** dela, conforme os comandos acima).
  2. O `PYTHONPATH` realmente aponta para a pasta **raiz** do projeto (`echo %PYTHONPATH%` no CMD / `echo $PYTHONPATH` no bash)?
- Portas padrão: Streamlit `http://localhost:8501`, FastAPI/Uvicorn `http://127.0.0.1:8000`.

## Scripts prontos (Windows / Linux / macOS)

A partir da **raiz do projeto**, você pode usar os scripts em `./scripts`:

### Windows (CMD)

- Backend: `scripts\start_backend.bat`
- Frontend: `scripts\start_frontend.bat`
- **Tudo junto (duas janelas):** `scripts\start_all_windows.bat`

### Linux/macOS (bash/zsh)

Primeiro, dê permissão de execução (uma vez):

```bash
chmod +x scripts/*.sh
```

Depois execute:

- Backend: `./scripts/start_backend.sh`
- Frontend: `./scripts/start_frontend.sh`
- **Tudo junto:** `./scripts/start_all.sh`

> Todos os scripts ajustam `PYTHONPATH` para a raiz do projeto antes de iniciar os serviços.

## ⚙️ Configuração do Ambiente (.env)

Este projeto utiliza variáveis de ambiente centralizadas para configuração
de segurança, banco de dados e tempo de expiração de sessões.

### 📁 Arquivo `.env`

Crie um arquivo `.env` **na raiz do projeto** (mesmo nível de `backend/` e `frontend/`).

Exemplo:

```env
# Ambiente
ENV=dev

# JWT
JWT_SECRET=uma-chave-secreta-forte
JWT_ALGORITHM=HS256

# Expiração de tokens
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DB_BACKEND=sqlite
DB_DSN=./data/dados.db
```

## 🔐 Auditoria e Governança de Dados

Este projeto implementa um **sistema de auditoria avançado**, projetado para **ambientes institucionais**, com foco em **integridade, rastreabilidade e não-repúdio**.

---

### 🧾 Trilha de Auditoria Completa (Before / After)

Toda operação de **mutação de dados** (`POST`, `PUT`, `DELETE`) gera automaticamente um evento de auditoria contendo:

- Usuário responsável
- Perfil (role)
- Timestamp em UTC
- Ação executada
- Recurso afetado
- Identificador do registro
- **Estado anterior (`payload_before`)**
- **Estado posterior (`payload_after`)**
- Endpoint e método HTTP

Isso permite reconstruir **exatamente o que mudou, quando e por quem**.

---

### 🔗 Cadeia Criptográfica de Auditoria (Blockchain-style)

Os eventos de auditoria são protegidos por uma **cadeia de hash SHA-256**, inspirada em conceitos de blockchain:

- Cada evento possui um `event_hash`
- Cada evento referencia o `prev_hash` do evento anterior
- O hash é calculado a partir de:
  - metadados do evento
  - payload _before / after_
  - hash do evento anterior

📌 **Qualquer alteração retroativa em um evento invalida toda a cadeia subsequente.**

---

### 🛡️ Bloqueio Automático de Escrita (Circuit Breaker)

Para garantir que dados não sejam corrompidos ou que evidências não sejam "enterradas" após uma violação, o sistema possui um mecanismo de defesa ativa:

1.  **Monitoramento:** O status de integridade é mantido em uma tabela singleton (`audit_integrity`).
2.  **Detecção:** Ao rodar a verificação (`/admin/audit/verify`) e encontrar inconsistência, o status muda para `VIOLATED`.
3.  **Reação:** O middleware `IntegrityGuardMiddleware` intercepta **todas** as requisições de escrita (`POST`, `PUT`, `DELETE`).
4.  **Bloqueio:** Se o status for `VIOLATED`, o sistema retorna **HTTP 423 Locked**, impedindo novas alterações até que um administrador resolva o incidente.

> **Nota:** Rotas de autenticação (`/login`, `/logout`) permanecem ativas para permitir que o administrador acesse o painel e restaure o sistema.

---

### 🧪 Verificação de Integridade

O backend expõe um endpoint administrativo que:

- Recalcula toda a cadeia de hash
- Detecta:
  - eventos adulterados
  - remoções
  - inserções fora de ordem
- Identifica exatamente:
  - o ponto de falha
  - o evento comprometido
  - o motivo da inconsistência

---

### 🖥️ Painel Visual de Integridade (Streamlit)

O frontend possui uma tela dedicada de **Integridade da Auditoria**, com:

- Indicador visual de status:
  - 🟢 Cadeia íntegra
  - 🔴 Violação detectada
- Exibição do ponto exato de falha
- Botão para **reexecutar a verificação**
- Exportação dos resultados para análise externa

---

### 🚨 Detecção de Violação e Evidência

O sistema foi projetado para:

- Detectar adulterações automaticamente
- Gerar evidência técnica verificável
- Servir como base para:
  - auditorias internas
  - investigações
  - compliance regulatório

---

### 🏛️ Princípios Atendidos

A arquitetura de auditoria atende aos seguintes princípios:

- Imutabilidade dos registros
- Não-repúdio
- Rastreabilidade completa
- Evidência forense
- Governança e accountability

---

### ⚠️ Importante

- **Eventos de auditoria nunca são alterados**
- Qualquer modificação de dados gera **um novo evento**
- O passado permanece imutável e verificável

---

### 📌 Casos de Uso

- Governança de dados
- Ambientes regulados
- Sistemas administrativos
- Trilhas de auditoria institucionais
- Estudos de arquitetura segura

## 👤 Gestão de Usuários e Perfil

O sistema oferece um módulo completo de identidade:

- **Perfil do Usuário:** Edição de dados cadastrais e upload de **Avatar**.
- **Gestão de Sessões:**
  - Visualização de sessões ativas.
  - Revogação remota de sessões (logout forçado).
  - Limpeza automática de sessões expiradas.
- **Política de Senhas:**
  - Expiração automática (rotação periódica).
  - Forçar troca no próximo login.

## 🔐 Reset de senha

O sistema implementa um fluxo seguro de redefinição de senha:

- Token criptograficamente seguro
- Apenas hash do token é persistido
- Token com expiração
- Uso único
- `/password-reset/cleanup` endpoint para limpeza de tokens de reset de senha expirados ou usados
- Auditoria completa dos eventos

Fluxo:

1. `/forgot-password` gera token
2. Token é enviado ao usuário
3. `/reset-password` redefine senha
4. Evento auditado
