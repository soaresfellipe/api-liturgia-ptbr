# Deploy na 20i (catolicoapp.com)

A plataforma Linux da 20i suporta Python (além de PHP/Perl). Este guia cobre a
verificação e os dois modos de execução possíveis, em ordem de preferência.

## Pré-requisitos

- Acesso SSH ao hosting (incluído nos planos reseller Linux) ou terminal do StackCP.
- Python **3.9 ou mais recente** no servidor (o código usa `from __future__ import annotations` e `removeprefix`).

## Passo 0 — Verificar o ambiente

```bash
ssh seu-usuario@catolicoapp.com
python3 --version
python3 -m venv --help >/dev/null && echo "venv ok"
```

Se `python3 --version` retornar `< 3.9`, pare aqui: os pins atuais (Flask 3.1)
não instalam. Nesse caso, considere o deploy na Vercel Hobby (grátis) ou uma
porta para PHP (ver `docs/runbook.md` para próximos passos).

## Passo 1 — Enviar o código e instalar dependências

```bash
cd ~/domains/catolicoapp.com/htdocs   # ajuste ao caminho real do seu pacote
git clone https://github.com/soaresfellipe/api-liturgia-ptbr.git api-liturgia
cd api-liturgia
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Passo 2 — Escolher o modo de execução

### Modo A — WSGI (preferível; procure no StackCP por "Python" / "Setup Python App" / Passenger)

1. No painel, crie a aplicação Python apontando o diretório para a pasta do
   projeto e o arquivo de entrada para `wsgi.py` (ele expõe `application`).
2. Se o painel pedir o virtualenv, informe `.venv` criado no passo 1.
3. Teste: `curl https://catolicoapp.com/health`.

Se o painel não tiver opção de Python mas o Apache tiver `mod_wsgi`, um
`.htaccess` do tipo Passenger no diretório da app também pode funcionar
(`PassengerPython .venv/bin/python3` + `PassengerAppRoot`).

### Modo B — CGI (fallback universal; mais lento: um processamento por requisição)

1. Copie o projeto para um diretório servido e habilite CGI:
   ```bash
   chmod +x cgi-bin/app.cgi
   ```
2. Garanta que o diretório `cgi-bin` do domínio aponta para `cgi-bin/app.cgi`
   (ou copie o arquivo para o `cgi-bin` existente e ajuste o `sys.path`).
3. Variáveis de ambiente via `.htaccess`, se necessário:
   ```apache
   SetEnv LITURGIA_BASE_URL "https://liturgia.cancaonova.com/pb/"
   SetEnv LOG_LEVEL "INFO"
   ```
4. Teste: `curl https://catolicoapp.com/cgi-bin/app.cgi/health`.

> No modo CGI a resposta pode levar alguns segundos (o interpreter sobe e o
> scraping roda a cada chamada). Para mitigar, agende um cron no StackCP que
> escreve a resposta de `/` em um arquivo estático a cada hora e sirva esse
> arquivo — a liturgia muda uma vez por dia.

## Passo 3 — Smoke test

```bash
curl https://catolicoapp.com/health          # ou a URL do modo escolhido
curl https://catolicoapp.com/ | head -c 500
```

Esperado: `{"status": "ok", "timestamp": "..."}` no health e o JSON de leituras
na raiz. Em falha da fonte, `502 {"error": "upstream_unavailable"}`.

## Limitações conhecidas

- Sem processo persistente: o cache de fallback em memória não sobrevive entre
  processos CGI; no modo WSGI ele vale enquanto o processo viver.
- Timeouts do servidor (geralmente 30–60s) são maiores que os nossos (~9s no
  pior caso de retry), então o retry não deve estourar o limite.
