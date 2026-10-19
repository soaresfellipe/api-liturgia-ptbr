## O que este PR faz

<!-- Descreva a mudança e a motivação. Referencie a issue relacionada, se houver. -->

## Checklist

- [ ] `ruff format .` e `ruff check .` passam
- [ ] `mypy app.py extractor` passa
- [ ] `pytest` passa (cobertura mínima de 80%)
- [ ] Documentação atualizada (README/AGENTS.md/runbook), se aplicável
- [ ] Validado localmente com `flask --app app run` + `curl localhost:5000/`, se a mudança afeta o runtime
