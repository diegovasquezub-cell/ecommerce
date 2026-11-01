"""Pruebas del webhook de Telegram sin red ni modelo: grafo y envío simulados."""
from fastapi.testclient import TestClient

import api.app as appmod

UPDATE = {"message": {"chat": {"id": 42}, "text": "hola"}}
HEADER = {"X-Telegram-Bot-Api-Secret-Token": "s3cr3to"}


class GrafoFalso:
    def invoke(self, entrada, config):
        self.thread = config["configurable"]["thread_id"]
        return {"ruta": "generica", "motivo": "m", "respuesta": "resp"}


def _cliente(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SECRET", "s3cr3to")
    monkeypatch.setenv("TELEGRAM_TOKEN", "TOKEN")
    enviados = []
    monkeypatch.setattr(
        appmod.httpx, "post",
        lambda url, json, timeout: enviados.append((url, json)) or type("R", (), {"raise_for_status": lambda s: None})(),
    )
    return enviados


def test_secreto_incorrecto_da_403(monkeypatch):
    _cliente(monkeypatch)
    with TestClient(appmod.app) as c:
        assert c.post("/telegram", json=UPDATE).status_code == 403
        assert c.post("/telegram", json=UPDATE, headers={"X-Telegram-Bot-Api-Secret-Token": "x"}).status_code == 403


def test_mensaje_se_responde_con_thread_chat_id(monkeypatch):
    enviados = _cliente(monkeypatch)
    with TestClient(appmod.app) as c:
        grafo = GrafoFalso()
        c.app.state.graph = grafo
        assert c.post("/telegram", json=UPDATE, headers=HEADER).json() == {"ok": True}
    assert grafo.thread == "42"
    assert enviados == [("https://api.telegram.org/botTOKEN/sendMessage", {"chat_id": 42, "text": "resp"})]


def test_update_sin_texto_se_ignora(monkeypatch):
    enviados = _cliente(monkeypatch)
    with TestClient(appmod.app) as c:
        r = c.post("/telegram", json={"message": {"chat": {"id": 1}, "sticker": {}}}, headers=HEADER)
        assert r.status_code == 200
    assert enviados == []