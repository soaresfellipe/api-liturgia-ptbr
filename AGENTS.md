# AGENTS.md

Instruções para agentes de código trabalhando neste repositório.

## Visão geral

API Flask que serve as leituras litúrgicas diárias extraídas por scraping de `https://liturgia.cancaonova.com/pb/` a cada requisição. Hospedada na Vercel (deploy automático na `main`).

## Comandos

| Ação | Comando |
| --- | --- |
| Instalar | `pip install -r requirements.txt -r requirements-dev.txt` |
| Rodar | `flask --app app run` |
| Testes | `pytest` (integração: `pytest -m integration`) |
| Lint | `ruff check .` |
| Formatar | `ruff format .` |
| Types | `mypy app.py extractor` |
| Deps não usadas/ausentes | `deptry .` |
| Código morto | `vulture app.py extractor` |
| Hooks | `pre-commit install` |

## Convenções

- Código e comentários em português (strings de API mantidas como estão).
- Nomes em `snake_case` (funções, variáveis, módulos); `PascalCase` apenas para classes, se surgirem.
- Type hints obrigatórios; `mypy` roda em modo **strict** e deve passar sem erros.
- Formatação via `ruff format`; lint via `ruff check` (inclui ordenação de imports, regras pep8-naming).
- Docstrings curtas em funções públicas explicando o propósito.

## Antes de commitar

1. `ruff format .` e `ruff check .`
2. `mypy app.py extractor`
3. `pytest` (cobertura mínima de 80%)
4. Hooks de pre-commit instalados (`pre-commit install`) rodam gitleaks, ruff e mypy.

## Gotchas

- **Scraping**: o parser depende da estrutura de HTML da Canção Nova (`dia-calendar`, `liturgia-1..4`, `cor-liturgica`, `entry-title`). Mudanças no site quebram a extração — ver `docs/runbook.md`. O teste de parse usa o snapshot `tests/fixtures/liturgia.html`; atualize-o apenas com uma página real e verifique o diff do resultado.
- **A 2ª leitura nem sempre existe**: `second_reading` só aparece em certos dias; o código lida com a ausência de qualquer seção.
- **Deps**: `requirements.txt` usa pins exatos (`==`). Não adote releases com menos de 7 dias de existência sem necessidade; `Werkzeug` está fixado explicitamente por compatibilidade com o Flask. Os pins também estão espelhados em `pyproject.toml` (`[project].dependencies`, para o deptry) — mantenha os dois em sincronia.
- **Serverless**: a app roda na Vercel — timeout/retry do fetch são dimensionados para caber no limite de duração da função (não aumente sem revisar isso).
- **Cache de fallback**: `extract()` mantém a última leitura bem-sucedida em memória por instância; em serverless isso é por instância do runtime, não global.

## Deploy

Push na `main` dispara deploy na Vercel. Valide localmente antes (`flask --app app run` + `curl localhost:5000/`).
