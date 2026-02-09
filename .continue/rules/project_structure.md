# Arquitetura Painel de Dados

Este é um projeto de análise de dados e dashboard utilizando Python, Pandas, Polars e Streamlit.

## Estrutura de Diretórios
- `/backend`: Lógica de negócio, CRUD e conexão com banco de dados (SQLAlchemy/SQLite).
- `/frontend`: Interface do usuário em Streamlit (`Home.py` e `/pages`).
- `/migrations`: Scripts de migração de banco de dados.
- `/data`: Armazenamento de dados brutos e bancos SQLite (APENAS LEITURA).

## Padrões de Código (Data Owner Guidelines)
1. **Bibliotecas:** Priorize `polars` para manipulação de dados e `streamlit` para UI.
2. **Banco de Dados:** O arquivo principal é `dados.db`. Ignore arquivos `.bak`.
3. **Auditoria:** Toda alteração de dados deve passar pelo `crud_auditoria.py`.
4. **Performance:** Evite carregar datasets inteiros em memória; use LazyFrames.

## O que Ignorar
Não analise, indexe ou sugira alterações em arquivos dentro de:
- `.venv`
- `__pycache__`
- Arquivos `.pptx`, `.pdf` ou `.docx`.


# Estrutura do Projeto SARI / Painel de Dados

Este é um projeto fullstack Python focada em dados da ANTT. O Agente deve navegar nas pastas abaixo para entender o contexto.

## Mapeamento de Diretórios
- **/backend**: Contém a API e regras de negócio (FastAPI/Python).
  - `/audit`: Lógica crítica de auditoria (`hash.py`, `middleware.py`). **Prioridade Máxima.**
  - `/db`: Adaptadores de banco de dados (Postgres/SQLite).
  - `/users`: Gestão de usuários e autenticação.
- **/frontend**: Interface do usuário (`streamlit`).
  - `Home.py`: Entrypoint da aplicação.
  - `/pages`: Telas do sistema.
- **/migrations**: Scripts SQL e Python para versionamento do banco.
- **/data**: Arquivos `.db` (SQLite) e `.parquet`. **O Agente NÃO deve ler o conteúdo binário destes arquivos, apenas a estrutura.**

## Stack Tecnológico
- **Lógica:** Python 3.12+ (Uso intensivo de Type Hints).
- **Dados:** Polars (Preferencial para volumetria) e Pandas (Legado).
- **Interface:** Streamlit.
- **ORM:** SQLAlchemy.

## Regras de Negócio (CODAM)
- Nunca exponha senhas ou chaves de API.
- Alterações em `/backend/audit` exigem validação de hash chain.
- O sistema deve ser agnóstico ao S.O. (Windows/Linux).