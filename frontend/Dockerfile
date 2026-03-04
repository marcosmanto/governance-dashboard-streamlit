# frontend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Garante que o Python encontre os módulos a partir da raiz do projeto (/app)
ENV PYTHONPATH=/app

# Inicia o Streamlit apontando para 0.0.0.0 (necessário em containers)
CMD ["streamlit", "run", "frontend/Home.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
