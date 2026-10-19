"""Utilitários de formatação e limpeza de texto usados pela extração."""

import re

_MONTHS: dict[str, str] = {
    "Jan": "01",
    "Fev": "02",
    "Mar": "03",
    "Abr": "04",
    "Mai": "05",
    "Jun": "06",
    "Jul": "07",
    "Ago": "08",
    "Set": "09",
    "Out": "10",
    "Nov": "11",
    "Dez": "12",
}


def parse_month(month: str) -> str:
    """Converte a abreviação do mês em português para o número com dois dígitos."""
    return _MONTHS[month]


def parse_day(day: str) -> str:
    """Garante o dia com dois dígitos (ex.: '5' -> '05')."""
    return day if len(day) > 1 else "0" + day


def clean_html(html: str | None) -> str:
    """Remove tags, comentários e espaços redundantes de um trecho de HTML."""
    if not html:
        return ""
    cleaned = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", html.strip())
    cleaned = re.sub(r"(?s)<!--(.*?)-->[\n]?", "", cleaned)
    cleaned = re.sub(r"(?s)<.*?>", " ", cleaned)
    cleaned = re.sub(r"&nbsp;", " ", cleaned)

    cleaned = cleaned.replace(";", ":")
    cleaned = cleaned.replace("\n", " ")
    cleaned = cleaned.replace("\r", " ")
    cleaned = cleaned.replace("\t", " ")

    for _ in range(10):
        cleaned = cleaned.replace("  ", " ")

    return cleaned.strip()
