import requests
from requests.auth import HTTPBasicAuth


class APIClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(username, password)
        self.timeout = 10

    def listar_registros(self):
        return requests.get(
            f"{self.base_url}/registros",
            auth=self.auth,
            timeout=self.timeout,
        )

    def criar_registro(self, payload: dict):
        return requests.post(
            f"{self.base_url}/registros",
            json=payload,
            auth=self.auth,
            timeout=self.timeout,
        )

    def atualizar_registro(self, id_: int, payload: dict):
        return requests.put(
            f"{self.base_url}/registros/{id_}",
            json=payload,
            auth=self.auth,
            timeout=self.timeout,
        )

    def deletar_registro(self, id_: int):
        return requests.delete(
            f"{self.base_url}/registros/{id_}",
            auth=self.auth,
            timeout=self.timeout,
        )

    def test_auth(self) -> bool:
        """
        Testa se as credenciais são válidas.
        Regra: GET /registros precisa retornar 200.
        """
        resp = self.listar_registros()
        return resp.status_code == 200

    def me(self):
        return requests.get(
            f"{self.base_url}/me",
            auth=self.auth,
            timeout=self.timeout,
        )

    def listar_auditoria(self, params: dict):
        return requests.get(
            f"{self.base_url}/auditoria",
            params=params,
            auth=self.auth,
            timeout=self.timeout,
        )
