# Migrações do SQLite — Guia do Projeto

Este documento explica **o que são as migrações**, **como rodá‑las** no projeto e traz um **guia rápido** sobre idempotência, triggers, WAL, upsert **e os índices criados**, além de **documentar os objetivos das migrações disponíveis (V001, V002, V003)**.

> Banco padrão usado nos exemplos: `./painel_dados_chatgpt_tutorial/data/dados.db`

---

## 1) Visão geral

- As migrações ficam na pasta `./migrations` com o padrão `VNNN__descricao.ext` (`.sql` ou `.py`).
- O `migrate.py` executa as migrações **em ordem** (V001 → V002 → V003...), registra o histórico em `schema_migrations` e cria **backup automático** (`.bak_YYYYMMDD_HHMMSS.db`).
- Você pode **inicializar** o banco automaticamente com `--init-if-missing` (detalhes na seção 3).

Estrutura típica:

```
painel_dados_chatgpt_tutorial/
├─ data/
│  └─ dados.db
├─ migrations/
│  ├─ V001__create_registros.py
│  ├─ V002__auditoria_registros.py
│  └─ V003__unicidade_upsert_e_wal.py
└─ migrate.py
```

---

## 2) Conceitos essenciais (linguagem simples)

### 2.1 Idempotente

> Rodar 1x ou 10x produz o **mesmo estado final**. Ex.: `CREATE TABLE IF NOT EXISTS` e checagens por catálogo antes de `ALTER TABLE`.

### 2.2 WAL Mode (Write‑Ahead Logging)

Melhora **desempenho e concorrência** (leitores não bloqueiam escritores). Persistente no arquivo após `PRAGMA journal_mode = WAL;`.

### 2.3 Upsert

`INSERT ... ON CONFLICT(chave) DO UPDATE ...` — insere se não existir, **atualiza** se já existir.

### 2.4 PRAGMAs úteis para índices

- `PRAGMA index_list('tabela')`: lista índices e mostra colunas `seq`, `name`, `unique`, `origin (c/u/pk)` e `partial (0/1)`.
- `PRAGMA index_info('indice')` / `PRAGMA index_xinfo('indice')`: mostra **colunas** e **ordem** dentro do índice.

> Referências: documentação de PRAGMAs do SQLite e materiais sobre `index_list`/`index_info`.

---

## 3) Como rodar as migrações

### 3.1 Listar migrações

```bash
python migrate.py --db ./data/dados.db --migrations ./migrations --list
```

### 3.2 Simular (sem alterar o banco)

```bash
python migrate.py --db ./data/dados.db --migrations ./migrations --dry-run
```

### 3.3 Aplicar tudo (ordem crescente)

```bash
python migrate.py --db ./data/dados.db --migrations ./migrations
```

### 3.4 Aplicar até uma versão específica

```bash
python migrate.py --db ./data/dados.db --migrations ./migrations --target-version 2
```

### 3.5 Marcar como aplicado **sem executar** (cuidado)

```bash
python migrate.py --db ./data/dados.db --migrations ./migrations --fake
```

### 3.6 **Criar o arquivo do banco caso não exista**

```bash
python migrate.py --db ./data/dados.db --migrations ./migrations --init-if-missing
```

- Cria a **pasta** se faltar, gera um banco **vazio** e segue aplicando as migrações (V001 cria tabela e faz seed).

> Dica de caminho: se você estiver **na pasta acima** do projeto, use `--db ./painel_dados_chatgpt_tutorial/data/dados.db` e `--migrations ./painel_dados_chatgpt_tutorial/migrations`.

---

## 4) Objetivos das migrações disponíveis

### V001 — `create_registros` (Python)

- Cria a tabela `registros` (`id`, `data`, `categoria`, `valor`).
- **Seed idempotente**: insere dados iniciais apenas se a tabela estiver vazia.

### V002 — `auditoria_registros` (Python)

- Garante as colunas de auditoria: `criado_em`, `atualizado_em`, `origem` (adiciona se faltarem).
- Backfill: preenche valores `NULL` com `CURRENT_TIMESTAMP` e default de `origem` (`'script_migracao'`).
- (Re)cria **gatilhos**:
  - `AFTER UPDATE`: atualiza `atualizado_em` quando você não alterou esse campo manualmente (evita loop).
  - `AFTER INSERT`: se `criado_em`/`origem` vierem `NULL`, define defaults.
- Cria índices em datas (`criado_em`, `atualizado_em`).

### V003 — `unicidade_upsert_e_wal` (Python)

- Remove **duplicados** por `(data, categoria)`, mantendo o mais recente.
- Impõe unicidade com **índice único** `UNIQUE(data, categoria)`.
- Cria **view** `vw_registros_upsert` + **gatilho `INSTEAD OF INSERT`** para permitir **upsert** via `INSERT` na view.
- Ativa **WAL** e `synchronous = NORMAL` (aplicado fora de transação para persistir).

> **Sobre `origem` no upsert da view:** a versão original da V003 definia `origem` como `'upsert'` quando ausente. Caso você prefira **manter a origem anterior** quando não enviar `origem` no upsert, ajuste o gatilho para enviar `NEW.origem` (sem `COALESCE('upsert')`) e usar `COALESCE(excluded.origem, registros.origem)` no `DO UPDATE`. Podemos disponibilizar uma V004 de ajuste se desejar.

---

## 5) Índices criados e o que cada um faz

A tabela `registros` ficou com estes índices (nomes padrão das migrações):

- **`ux_registros_data_categoria`** — **Único** (enforce): colunas `(data, categoria)`
  - **Papel**: garante **no máximo 1 linha** por `(data, categoria)` e acelera buscas por `data` + `categoria` (seek único) e por faixas de `data`.
  - **Exemplos**:
    - `SELECT ... WHERE data='2025-01-02' AND categoria='A';`
    - `SELECT ... WHERE data BETWEEN '2025-01-01' AND '2025-01-31';`

- **`ix_registros_categoria_data`** — não-único: colunas `(categoria, data)`
  - **Papel**: consultas que começam por **`categoria`** (igualdade) e refinam/ordenam por `data`.
  - **Exemplos**:
    - `SELECT ... WHERE categoria='A' AND data BETWEEN ...`
    - `SELECT ... WHERE categoria='A' ORDER BY data DESC`

- **`idx_registros_atualizado_em`** — não-único: coluna `(atualizado_em)`
  - **Papel**: feeds de **recém-alterados** e filtros por período de atualização.

- **`idx_registros_criado_em`** — não-único: coluna `(criado_em)`
  - **Papel**: listagens/ordenações por **criação** e filtros por período.

> **Por que dois índices compostos em ordens diferentes?** A ordem da coluna **à esquerda** num índice composto define os padrões que ele atende bem. `(data, categoria)` atende consultas que partem de `data`; `(categoria, data)` atende consultas que partem de `categoria`. Se um desses padrões não existe no seu uso, você pode remover o índice correspondente para reduzir custo de escrita.

> Como inspecionar:
>
> ```sql
> PRAGMA index_list('registros');
> PRAGMA index_info('ux_registros_data_categoria');
> PRAGMA index_info('ix_registros_categoria_data');
> -- Para detalhes extras (ordem DESC, expressões):
> PRAGMA index_xinfo('ux_registros_data_categoria');
> ```

---

## 6) Dicas de desempenho e verificação

- Use `EXPLAIN QUERY PLAN <sua_consulta>;` para ver qual índice o otimizador escolheu.
- Evite índices redundantes: cada índice extra **encarece INSERT/UPDATE/DELETE**. Mantenha apenas os que cobrem suas consultas frequentes.
- Para cargas massivas, faça **transações grandes** e, se preciso, use `INSERT ... ON CONFLICT` direto na tabela em vez da view.

---

## 7) Problemas comuns

- **"Banco não encontrado"** → use `--init-if-missing` ou corrija o caminho do `--db`.
- **Mudou arquivo de migração já aplicada (checksum diferente)** → crie uma **nova** migração para alterações posteriores.
- **Horário**: `CURRENT_TIMESTAMP` é em **UTC** no SQLite. Se quiser horário local, ajuste gatilhos para `datetime('now','localtime')`.

---

## 8) Apêndice rápido sobre PRAGMAs de índice

- `PRAGMA index_list('tabela')` retorna colunas: `seq`, `name`, `unique (0/1)`, `origin (c/u/pk)`, `partial (0/1)`.
- `PRAGMA index_info('indice')` lista as colunas do índice (ordem importa!).
- `PRAGMA index_xinfo('indice')` inclui detalhes extras (ex.: ordem DESC, colunas computadas).
