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
