"""Testes unitários dos utilitários de formatação."""

import pytest

from extractor.utils import clean_html, parse_day, parse_month


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("5", "05"),
        ("19", "19"),
        ("01", "01"),
    ],
)
def test_parse_day_preenche_zero_a_esquerda(entrada: str, esperado: str) -> None:
    assert parse_day(entrada) == esperado


@pytest.mark.parametrize(
    ("mes", "esperado"),
    [
        ("Jan", "01"),
        ("Fev", "02"),
        ("Set", "09"),
        ("Dez", "12"),
    ],
)
def test_parse_month_converte_abreviacao(mes: str, esperado: str) -> None:
    assert parse_month(mes) == esperado


def test_clean_html_remove_tags_comentarios_e_espacos() -> None:
    html = "<p>  Olá&nbsp;mundo </p><!-- comentario -->\n\t<span>  fim  </span>"
    assert clean_html(html) == "Olá mundo fim"


def test_clean_html_remove_script_e_style() -> None:
    html = "<style>x{}</style>Texto<script>evil()</script>"
    assert clean_html(html) == "Texto"


def test_clean_html_aceita_none_e_vazio() -> None:
    assert clean_html(None) == ""
    assert clean_html("") == ""
