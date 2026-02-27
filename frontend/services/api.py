import json
import logging
import sys

import requests
import streamlit as st

from backend.core.config import settings
from frontend.core.pages import Page
from frontend.services.navigation import get_current_page

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)


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

    def ensure_user_refresh(self):
        """
        Força uma chamada leve ao backend apenas para sincronizar contexto.
        """
        resp = self._request("GET", "/me")

        if resp.status_code != 200:
            return False

        return True

    def _sync_user_from_headers(self, resp):
        logger.debug("Sincronizando dados de usuário...")
        header = resp.headers.get("X-User-Context")

        if not header:
            return

        try:
            data = json.loads(header)
            st.session_state.user = data
        except Exception as e:
            logger.error(f"Erro ao decodificar X-User-Context: {e}")

    def _refresh_acess_token(self) -> bool:
        """'
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
        self.refresh_token = data["refresh_token"]

        # sincroniza com o session_state
        st.session_state.access_token = self.access_token
        st.session_state.refresh_token = self.refresh_token

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

        self._sync_user_from_headers(resp)

        if resp.status_code == 403:
            try:
                detail = resp.json().get("detail")
            except Exception:
                detail = None

            current_page = get_current_page()

            if detail in ("PASSWORD_CHANGE_REQUIRED", "PASSWORD_EXPIRED"):
                if current_page != Page.CHANGE_PASSWORD.key:
                    # ⚠️ Apenas em desenvolvimento, retorna o token no response
                    if settings.ENV == "dev":
                        logger.warning(f"Password change required or expired. Detail: {detail}")

                    st.session_state.force_password_change = True
                    st.switch_page(Page.CHANGE_PASSWORD.path)
                    st.stop()

        # 🔁 fluxo normal de refresh
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
        st.switch_page(Page.LOGIN.path)

    # -------------------------
    # Métodos públicos (sem auth)
    # -------------------------

    @staticmethod
    def listar_registros_publico(base_url: str, timeout: int = 10):
        return requests.get(
            f"{base_url.rstrip('/')}/registros",
            timeout=timeout,
        )

    # -------------------------
    # Métodos públicos (com auth)
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

    def login(self, username: str, password: str, otp_code: str | None = None):
        params = {
            "username": username,
            "password": password,
        }
        if otp_code:
            params["otp_code"] = otp_code

        return requests.post(
            f"{self.base_url}/login",
            params=params,
            timeout=self.timeout,
        )
