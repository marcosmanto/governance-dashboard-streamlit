import requests
import streamlit as st


class APIClient:
    def __init__(self, base_url: str, access_token: str, refresh_token: str):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.timeout = 10

    # -------------------------
    # Helpers internos
    # -------------------------

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
        }

    def _refresh_acess_token(self) -> bool:
        """
        Tenta renovar o access token usando o refresh token.
        Retorna True se conseguiu, False se falhou.
        """
        resp = requests.post(
            f"{self.base_url}/refresh",
            headers={
                "Authorization": f"Bearer {self.refresh_token}",
            },
        )
        if resp.status_code != 200:
            return False

        data = resp.json()
        self.access_token = data["access_token"]

        # sincroniza com o session_state
        st.session_state.access_token = self.access_token
        return True

    def _request(self, method: str, path: str, **kwargs):
        """
        Request genérico com retry automático via refresh token.
        """
        resp = requests.request(
            method,
            f"{self.base_url}{path}",
            headers=self._headers(),
            **kwargs,
        )

        if resp.status_code != 401:
            return resp

        # tenta refresh
        if not self._refresh_acess_token():
            self._force_logout()
            return resp

        # retry UMA vez
        return requests.request(
            method,
            f"{self.base_url}{path}",
            headers=self._headers(),
            **kwargs,
        )

    def _force_logout(self):
        st.session_state.api = None
        st.session_state.user = None
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.switch_page("pages/0_🔐_Login.py")

    # -------------------------
    # Métodos públicos
    # -------------------------

    def listar_registros(self):
        return self._request("GET", "/registros", timeout=self.timeout)

    def criar_registro(self, payload: dict):
        return self._request("POST", "/registros", json=payload, timeout=self.timeout)

    def atualizar_registro(self, id_: int, payload: dict):
        return self._request("PUT", f"/registros/{id_}", json=payload, timeout=self.timeout)

    def deletar_registro(self, id_: int):
        return self._request("DELETE", f"/registros/{id_}", timeout=self.timeout)

    def listar_auditoria(self, params: dict):
        return self._request("GET", "/auditoria", params=params, timeout=self.timeout)

    def logout(self):
        return requests.post(
            f"{self.base_url}/logout",
            headers=self._headers(),
            timeout=self.timeout,
        )

    def login(self, username: str, password: str):
        return requests.post(
            f"{self.base_url}/login",
            params={
                "username": username,
                "password": password,
            },
            timeout=self.timeout,
        )
