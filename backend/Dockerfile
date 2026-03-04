# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instala dependências do sistema (necessário para compilar algumas libs Python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do projeto
COPY . .

# Cria diretórios necessários para persistência
RUN mkdir -p data backend/static

# Expõe a porta (apenas documentação, quem expõe de verdade é o docker-compose)
EXPOSE 8000

# Comando de inicialização:
# 1. Roda migrações (cria banco se não existir)
# 2. Inicia o servidor Uvicorn em modo produção (sem reload)
CMD ["sh", "-c", "python migrate.py --db ./data/dados.db --init-if-missing && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
