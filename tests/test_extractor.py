"""Testes de parse do HTML da liturgia contra o snapshot fixture."""

from pathlib import Path
from typing import Any

import pytest
import requests

import extractor.extractor_service as es
from extractor.extractor_service import RETRY_ATTEMPTS, ExtractionError, extract, fetch, parse

FIXTURE = Path(__file__).parent / "fixtures" / "liturgia.html"


def _fixture_html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_extrai_data_cor_e_titulo() -> None:
    data = parse(_fixture_html())
    assert data["date"] == "19/10/2026"
    assert data["date_string"] == {"day": "19", "month": "Out", "year": "2026"}
    assert data["color"] == "Verde"
    assert data["entry_title"] == "29ª Semana do Tempo Comum | Segunda-feira"


def test_parse_extrai_primeira_leitura() -> None:
    reading: dict[str, Any] = parse(_fixture_html())["readings"]["first_reading"]
    assert reading["title"]
    assert reading["head"]
    assert reading["text"]
    assert reading["footer"]
    assert reading["footer_response"]
    assert "<p" in reading["all_html"]
    assert "<strong" not in reading["text"]


def test_parse_extrai_salmo() -> None:
    psalm: dict[str, Any] = parse(_fixture_html())["readings"]["psalm"]
    assert psalm["title"]
    assert psalm["response"]
    assert isinstance(psalm["content_psalm"], list)
    assert psalm["content_psalm"]
    assert all("—" not in verse for verse in psalm["content_psalm"])


def test_parse_extrai_evangelho() -> None:
    gospel: dict[str, Any] = parse(_fixture_html())["readings"]["gospel"]
    assert gospel["title"]
    assert gospel["head"]
    assert "head_response" in gospel
    assert gospel["text"]
    assert "<strong" not in gospel["text"]


def test_parse_extrai_segunda_leitura_quando_presente() -> None:
    # O snapshot de dia de semana não tem 2ª leitura; reutilizamos o bloco da
    # 1ª leitura como liturgia-3 para exercitar o perfil específico dessa seção.
    html = _fixture_html().replace('id="liturgia-1"', 'id="liturgia-3"')
    data = parse(html)
    second: dict[str, Any] = data["readings"]["second_reading"]
    assert second["title"] == "Primeira Leitura (Ef 2,1-10)"
    assert second["text"]
    assert second["footer"] == "Palavra do Senhor."


def test_parse_lida_com_ausencia_de_secoes() -> None:
    # Remove todas as seções de leitura; o parse não deve quebrar.
    html = _fixture_html()
    for liturgia_id in ("liturgia-1", "liturgia-2", "liturgia-4"):
        html = html.replace(f'id="{liturgia_id}"', 'id="removida"')
    data = parse(html)
    assert data["readings"] == {}


def test_parse_levanta_extraction_error_se_elemento_basico_faltar() -> None:
    html = _fixture_html().replace('id="dia-calendar"', 'id="outro-elemento"')
    with pytest.raises(ExtractionError):
        parse(html)


class _FakeResponse:
    def __init__(self, text: str = "ok", status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


def test_fetch_retorna_html_em_sucesso(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, int]] = []

    def fake_get(url: str, timeout: int) -> _FakeResponse:
        calls.append((url, timeout))
        return _FakeResponse(text="<html>conteudo</html>")

    monkeypatch.setattr(requests, "get", fake_get)
    assert fetch("http://exemplo.teste") == "<html>conteudo</html>"
    assert calls == [("http://exemplo.teste", es.REQUEST_TIMEOUT_SECONDS)]


def test_fetch_faz_retry_e_levanta_extraction_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def fake_get(url: str, timeout: int) -> _FakeResponse:
        calls.append(1)
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(es.time, "sleep", lambda segundos: None)
    with pytest.raises(ExtractionError):
        fetch("http://exemplo.teste")
    assert len(calls) == RETRY_ATTEMPTS


def test_extract_faz_fallback_para_cache_em_falha(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(es, "_last_good", {"date": "01/01/2026", "readings": {}})
    monkeypatch.setattr(es, "fetch", lambda url: "<html>ininterpretavel</html>")
    data, from_cache = extract("http://exemplo.teste")
    assert from_cache is True
    assert data["date"] == "01/01/2026"


def test_extract_levanta_erro_sem_cache_disponivel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(es, "_last_good", None)
    monkeypatch.setattr(es, "fetch", lambda url: "<html>ininterpretavel</html>")
    with pytest.raises(ExtractionError):
        extract("http://exemplo.teste")


@pytest.mark.integration
def test_integracao_fonte_real() -> None:
    """Bate na página real da Canção Nova; roda apenas com `pytest -m integration`."""
    data, from_cache = extract()
    assert from_cache is False
    assert data["date"]
    assert data["readings"]
