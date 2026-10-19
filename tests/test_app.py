"""Testes das rotas Flask com o test client."""

import json
import logging
from typing import Any

import pytest
from flask.testing import FlaskClient

import app as app_module
from extractor.extractor_service import ExtractionError


@pytest.fixture
def client() -> FlaskClient:
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_health_responde_ok(client: FlaskClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert "timestamp" in body


def test_homepage_retorna_leituras(client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
    readings: dict[str, Any] = {"date": "01/01/2026", "readings": {}}
    monkeypatch.setattr(app_module, "extract", lambda url: (readings, False))
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_json()
    assert body["source"] == "Canção Nova"
    assert body["today"] == readings
    assert "evangelização" in body["objective"]


def test_homepage_indica_origem_cache(client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
    readings: dict[str, Any] = {"date": "01/01/2026", "readings": {}}
    monkeypatch.setattr(app_module, "extract", lambda url: (readings, True))
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json()["source"] == "Canção Nova (cache)"


def test_homepage_responde_502_sem_cache(
    client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def falha(url: str) -> tuple[dict[str, Any], bool]:
        raise ExtractionError("sem cache")

    monkeypatch.setattr(app_module, "extract", falha)
    response = client.get("/")
    assert response.status_code == 502
    assert response.get_json()["error"] == "upstream_unavailable"


def test_json_formatter_produz_json_estruturado() -> None:
    formatter = app_module.JsonFormatter()
    record = logging.LogRecord("teste", logging.INFO, __file__, 1, "mensagem de teste", None, None)
    record.extra_customizado = "valor"  # type: ignore[attr-defined]
    payload = json.loads(formatter.format(record))
    assert payload["event"] == "mensagem de teste"
    assert payload["level"] == "INFO"
    assert payload["extra_customizado"] == "valor"
    assert "timestamp" in payload
