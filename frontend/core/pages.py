from enum import Enum


class Page(Enum):
    LOGIN = ("login", "pages/0_🔐_Login.py")
    HOME = ("home", "Home.py")
    GERENCIAR = ("gerenciar", "pages/2_✏️_Gerenciar.py")
    AUDITORIA = ("auditoria", "pages/3_📜_Auditoria.py")
    ADMIN = ("admin", "pages/4_🛠️_Administração.py")
    INTEGRIDADE = ("integridade", "pages/5_🔐_Integridade_Auditoria.py")
    USERS = ("users", "pages/6_🧑‍💼_Usuários.py")
    CHANGE_PASSWORD = ("change_password", "pages/7_🔑_Troca_de_Senha.py")
    RESET_PASSWORD = ("reset_password", "pages/8_🔑_Redefinir_Senha.py")
    PROFILE = ("profile", "pages/9_👤_Perfil.py")

    def __init__(self, key, path):
        self.key = key
        self.path = path
