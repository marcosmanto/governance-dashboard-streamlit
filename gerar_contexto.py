import os

# Configurações de exclusão (O que NÃO enviar para o ChatGPT)
IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".vscode",
    ".idea",
    "data",  # Ignora a pasta de dados (bancos sqlite, parquets)
    "backend/static",  # Ignora imagens estáticas
}

IGNORE_FILES = {
    "gerar_contexto.py",  # Não precisa incluir este próprio script
    "poetry.lock",
    "package-lock.json",
    ".DS_Store",
    "dados.db",
    ".env",
    "contexto_completo.txt",  # Não incluir o próprio arquivo de saída
    "README.md",  # Geralmente não é necessário para o contexto de código
}

IGNORE_EXTENSIONS = {
    ".pyc",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".db",
    ".sqlite",
    ".parquet",
    ".exe",
    ".bin",
}

OUTPUT_FILE = "contexto_completo.txt"


def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
        out_f.write("CONTEXTO COMPLETO DO PROJETO\n")
        out_f.write("============================\n\n")

        for root, dirs, files in os.walk("."):
            # Modifica a lista 'dirs' in-place para pular pastas ignoradas
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                if file in IGNORE_FILES:
                    continue

                _, ext = os.path.splitext(file)
                if ext.lower() in IGNORE_EXTENSIONS:
                    continue

                file_path = os.path.join(root, file)

                # Escreve o cabeçalho e o conteúdo do arquivo
                out_f.write(f"\n\n{'=' * 50}\n")
                out_f.write(f"FILE: {file_path}\n")
                out_f.write(f"{'=' * 50}\n")

                try:
                    with open(file_path, "r", encoding="utf-8") as in_f:
                        content = in_f.read()
                        out_f.write(content)
                except Exception as e:
                    out_f.write(f"[Erro ao ler arquivo: {e}]")

    print(f"✅ Arquivo gerado com sucesso: {OUTPUT_FILE}")
    print("Agora basta arrastar este arquivo para o ChatGPT.")


if __name__ == "__main__":
    main()
