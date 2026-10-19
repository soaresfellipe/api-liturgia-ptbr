---
name: update-parser
description: Atualiza o parser do extractor quando o HTML da Canção Nova muda e as leituras vêm vazias/502. Use quando o test de integração falhar ou o site mudar de estrutura.
---

# Atualizar o parser da liturgia

## Quando usar

- `GET /` retorna `502 upstream_unavailable` com o site da Canção Nova no ar.
- `pytest -m integration` falha.
- Campos (`title`, `head`, `text`) vieram vazios ou deslocados na resposta da API.

## Passos

1. Baixe a página atual e atualize o snapshot:
   ```powershell
   python -c "import requests; open('tests/fixtures/liturgia.html','wb').write(requests.get('https://liturgia.cancaonova.com/pb/', timeout=10).content)"
   ```
2. Inspecione a estrutura de parágrafos de cada seção (`liturgia-1..4`) com BeautifulSoup, contando `<p>` não vazios.
3. Ajuste `_READING_PROFILES` (índices `head_index`, `head_response_index`, `body` e `dash`) em `extractor/extractor_service.py` conforme a nova estrutura — os índices são relativos aos parágrafos não vazios.
4. Se elementos básicos (`dia-calendar`, `cor-liturgica`, `entry-title`) mudaram de id/classe, atualize `parse()`.
5. Atualize as asserções dos testes (`tests/test_extractor.py`) com os valores reais do novo snapshot.
6. Valide: `pytest`, `pytest -m integration`, `mypy`, `ruff check .` e, por fim, `flask --app app run` + `curl localhost:5000/`.
7. Documente a mudança de estrutura em `docs/runbook.md` se ela introduzir um novo padrão.

## Cuidados

- Não confie em índices absolutos dos parágrafos originais: o código descarta `<p>` vazios iniciais antes de indexar.
- Mantenha o comportamento dos campos do JSON estável para consumidores da API.
