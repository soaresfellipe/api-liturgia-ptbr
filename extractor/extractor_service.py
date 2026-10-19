"""Extração das leituras litúrgicas diárias do site da Canção Nova."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

from .utils import clean_html, parse_day, parse_month

logger = logging.getLogger(__name__)

DEFAULT_URL = "https://liturgia.cancaonova.com/pb/"
REQUEST_TIMEOUT_SECONDS = 4
RETRY_ATTEMPTS = 2
RETRY_BACKOFF_SECONDS = 1.0

# Perfis das seções de leitura. Os índices são relativos à lista de parágrafos
# SEM os parágrafos vazios iniciais (espaçadores do site). Estrutura típica:
# 1ª/2ª leitura: título, cabeçalho, corpo..., rodapé, resposta do rodapé.
# Evangelho: título, aleluia, verso do aleluia, cabeçalho, resposta, corpo..., rodapé, resposta.
_READING_PROFILES: dict[str, dict[str, Any]] = {
    "first_reading": {
        "liturgia_id": "liturgia-1",
        "head_index": 1,
        "body": slice(2, -2),
        "dash": "- ",
    },
    "second_reading": {
        "liturgia_id": "liturgia-3",
        "head_index": 1,
        "body": slice(2, -2),
        "dash": "- ",
    },
    "gospel": {
        "liturgia_id": "liturgia-4",
        "head_index": 3,
        "head_response_index": 4,
        "body": slice(5, -2),
        "dash": " — ",
    },
}

# Cache em memória com a última extração bem-sucedida (fallback por instância).
_last_good: dict[str, Any] | None = None


class ExtractionError(Exception):
    """A página upstream não pôde ser obtida ou interpretada."""


def fetch(url: str = DEFAULT_URL) -> str:
    """Baixa a página da liturgia com timeout e retry com backoff."""
    last_error: Exception | None = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.RequestException as exc:
            last_error = exc
            logger.warning(
                "upstream_fetch_failed",
                extra={"url": url, "attempt": attempt, "error": str(exc)},
            )
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
        else:
            return response.text
    raise ExtractionError("upstream unavailable") from last_error


def _section(soup: BeautifulSoup, liturgia_id: str) -> Tag | None:
    tag = soup.find(id=liturgia_id)
    return tag if isinstance(tag, Tag) else None


def _required_tag_by_id(soup: BeautifulSoup, id_: str) -> Tag:
    tag = soup.find(id=id_)
    if not isinstance(tag, Tag):
        raise ExtractionError(f"missing element id={id_}")
    return tag


def _required_tag_by_class(soup: BeautifulSoup, css_class: str) -> Tag:
    tag = soup.find(class_=css_class)
    if not isinstance(tag, Tag):
        raise ExtractionError(f"missing element class={css_class}")
    return tag


def _remove_strong(paragraphs: list[Tag]) -> None:
    for phrase in paragraphs:
        for strong in phrase.find_all("strong"):
            strong.decompose()


def _non_empty_paragraphs(paragraphs: list[Tag]) -> list[Tag]:
    """Descarta parágrafos vazios no início do bloco (espaçadores do site)."""
    start = 0
    while start < len(paragraphs) and not paragraphs[start].get_text(strip=True):
        start += 1
    return paragraphs[start:]


def _at(paragraphs: list[Tag], index: int) -> Tag:
    try:
        return paragraphs[index]
    except IndexError as exc:
        raise ExtractionError("reading structure shorter than expected") from exc


def _strip_bullet(text: str) -> str:
    """Remove marcadores de linha ('— ' e '- ') usados pelo site no início dos parágrafos."""
    return text.replace("— ", "").strip().removeprefix("- ").strip()


def _build_reading(
    all_paragraphs: list[Tag],
    head_index: int,
    body: slice,
    dash: str,
    head_response_index: int | None = None,
) -> dict[str, Any]:
    """Extrai uma leitura comum (1ª/2ª leitura ou evangelho) de um bloco de parágrafos."""
    paragraphs = _non_empty_paragraphs(all_paragraphs)
    reading: dict[str, Any] = {
        "title": _at(paragraphs, 0).get_text(),
        "head": _at(paragraphs, head_index).get_text().replace(dash, ""),
        "footer": paragraphs[-2].get_text().replace(dash, ""),
        "footer_response": paragraphs[-1].get_text().replace(dash, ""),
        "all_html": " ".join(p.prettify() for p in all_paragraphs),
    }
    if head_response_index is not None:
        reading["head_response"] = _at(paragraphs, head_response_index).get_text().replace(dash, "")
    body_paragraphs = paragraphs[body]
    _remove_strong(body_paragraphs)
    reading["text"] = " ".join(p.get_text() for p in body_paragraphs).replace("  ", " ")
    return reading


def _build_psalm(all_paragraphs: list[Tag]) -> dict[str, Any]:
    """Extrai o salmo, cujo corpo é uma lista de versículos em vez de texto corrido."""
    paragraphs = _non_empty_paragraphs(all_paragraphs)
    psalm: dict[str, Any] = {
        "title": _at(paragraphs, 0).get_text(),
        "response": _strip_bullet(_at(paragraphs, 1).get_text()),
        "all_html": " ".join(p.prettify() for p in all_paragraphs),
    }
    content: list[str] = []
    for phrase in paragraphs[2:]:
        _remove_strong([phrase])
        text = _strip_bullet(phrase.get_text())
        if text:
            content.append(text)
    psalm["content_psalm"] = content
    return psalm


def parse(html: str) -> dict[str, Any]:
    """Interpreta o HTML da página da liturgia no dicionário de leituras."""
    soup = BeautifulSoup(html, "html.parser")

    day = _required_tag_by_id(soup, "dia-calendar").get_text()
    month = _required_tag_by_id(soup, "mes-calendar").get_text()
    year = _required_tag_by_id(soup, "ano-calendar").get_text()

    color_raw = _required_tag_by_class(soup, "cor-liturgica").get_text()
    color_parts = color_raw.split(":", 1)
    color = clean_html(color_parts[1] if len(color_parts) > 1 else color_parts[0])

    readings: dict[str, Any] = {}
    psalm_section = _section(soup, "liturgia-2")
    if psalm_section is not None:
        readings["psalm"] = _build_psalm(psalm_section.find_all("p"))

    for key, profile in _READING_PROFILES.items():
        section = _section(soup, profile["liturgia_id"])
        if section is not None:
            readings[key] = _build_reading(
                section.find_all("p"),
                head_index=profile["head_index"],
                body=profile["body"],
                dash=profile["dash"],
                head_response_index=profile.get("head_response_index"),
            )

    return {
        "date_string": {"day": day, "month": month, "year": year},
        "date": f"{parse_day(day)}/{parse_month(month)}/{year}",
        "color": color,
        "entry_title": clean_html(_required_tag_by_class(soup, "entry-title").get_text()),
        "readings": readings,
    }


def extract(url: str = DEFAULT_URL) -> tuple[dict[str, Any], bool]:
    """Extrai as leituras do dia; em falha, serve a última extração em cache.

    Retorna ``(leituras, from_cache)``. Levanta ``ExtractionError`` quando não
    há cache disponível.
    """
    global _last_good
    try:
        data = parse(fetch(url))
    except (ExtractionError, AttributeError, IndexError, KeyError, TypeError) as exc:
        logger.error("extraction_failed", extra={"url": url, "error": str(exc)})
        cached = _last_good
        if cached is None:
            raise ExtractionError("no cached readings available") from exc
        logger.warning("serving_cached_readings")
        return cached, True
    _last_good = data
    return data, False
