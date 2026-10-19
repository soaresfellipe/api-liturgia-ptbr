# Runbook — API Liturgia Diária

Procedimentos operacionais para os principais incidentes e manutenções desta API.

## Sintomas e primeira resposta

### `GET /` retorna `502 {"error": "upstream_unavailable"}`

A extração da fonte falhou e não há leitura em cache na instância. Causas prováveis: Canção Nova fora do ar, mudança no HTML do site ou bloqueio de rede.

1. **Verifique a fonte manualmente:** abra <https://liturgia.cancaonova.com/pb/> no navegador. A página carrega com as leituras do dia?
   - Se não carrega: o problema é na fonte. Não há ação no repositório; a API volta quando a fonte voltar (o retry automático já tenta novamente a cada requisição).
   - Se carrega: a estrutura do HTML provavelmente mudou — siga "Parser quebrado" abaixo.
2. **Rode o teste de integração contra a fonte real:**
   ```bash
   pytest -m integration -v
   ```
   Falhas aqui com o site no ar indicam mudança de estrutura.
3. **Confirme o deploy:** a Vercel faz deploy automático na `main`. Verifique em <https://vercel.com> se o último deploy está ativo.

### Respostas com `"source": "Canção Nova (cache)"`

Comportamento esperado em falha transitória da fonte: `extract()` serve a última leitura bem-sucedida mantida em memória pela instância. Em serverless o cache é por instância e reinicia a cada cold start — pode haver 502 mesmo depois de uma resposta em cache.

## Parser quebrado (mudança de HTML na fonte)

O parser depende de: `dia-calendar`, `mes-calendar`, `ano-calendar`, `cor-liturgica`, `entry-title` e `liturgia-1..4` (seções de leitura, com `<p>` inicial vazio de espaçamento).

1. Atualize o snapshot: baixe a página atual e salve em `tests/fixtures/liturgia.html`.
2. Compare a estrutura dos parágrafos de cada seção com o que `_READING_PROFILES` e `_build_reading`/`_build_psalm` esperam (índices relativos aos parágrafos não vazios).
3. Ajuste os índices dos perfis em `extractor/extractor_service.py` conforme a nova estrutura.
4. Rode `pytest` — os testes de parse vão validar cada campo (`title`, `head`, `text`, `footer`, `footer_response`).
5. Se algum elemento básico (`dia-calendar` etc.) renomeou no site, atualize também `_required_tag_by_id`/`_required_tag_by_class` em `parse()`.
6. Rode o teste de integração (`pytest -m integration`) e valide manualmente com `flask --app app run` + `curl localhost:5000/`.

## Dependências

- `requirements.txt` usa pins exatos; Werkzeug é fixado explicitamente por compatibilidade com o Flask.
- Dependabot abre PRs semanais. Antes de aprovar: confira o changelog da dependência e evite releases com menos de 7 dias sem necessidade (política em `AGENTS.md`).
- Após atualizar o Flask/Werkzeug, valide localmente `flask --app app run` + `curl localhost:5000/` antes do merge (um mismatch Flask/Werkzeug quebra a app no import, como ocorreu em 2026-10).

## Deploy

- Este repositório é um fork: conecte-o a um projeto próprio na Vercel (Import Project) para habilitar deploy automático no push da `main` (`vercel.json` já configurado).
- Após o deploy, smoke test na URL do seu projeto (substitua `SEU-PROJETO`):
  `curl https://SEU-PROJETO.vercel.app/health` e `curl https://SEU-PROJETO.vercel.app/ | head -c 500`.

## Próximos passos sugeridos (exigem serviços externos)

- Error tracking (Sentry) e alertas: criar projeto no Sentry, adicionar DSN como variável de ambiente na Vercel e instrumentar `app.py`.
- Métricas/tracing: integrar APM (ex.: OpenTelemetry) se o volume justificar.
