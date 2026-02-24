from datetime import datetime


def saudacao_usuario(nome: str) -> str:
    hora = datetime.now().hour
    if 5 <= hora < 12:
        periodo = "Bom dia"
    elif 12 <= hora < 18:
        periodo = "Boa tarde"
    else:
        periodo = "Boa noite"

    # Pega apenas o primeiro nome se for composto
    primeiro_nome = nome.split()[0] if nome else "Usuário"
    return f"{periodo}, {primeiro_nome}!"
