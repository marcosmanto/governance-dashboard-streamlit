import requests

API_URL = "http://127.0.0.1:8000"


def listar_registros():
    r = requests.get(f"{API_URL}/registros", timeout=5)
    r.raise_for_status()
    return r.json()


def criar_registro(payload: dict):
    r = requests.post(f"{API_URL}/registros", json=payload, timeout=5)
    r.raise_for_status()
    return r.json()


def atualizar_registro(id_: int, payload: dict):
    r = requests.put(f"{API_URL}/registros/{id_}", json=payload, timeout=5)
    r.raise_for_status()
    return r.json()


def deletar_registro(id_: int):
    r = requests.delete(f"{API_URL}/registros/{id_}", timeout=5)
    r.raise_for_status()
    return r.json()
