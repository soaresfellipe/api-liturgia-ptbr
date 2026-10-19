"""Gera JSON estático das leituras para hospedagens sem WSGI (ex.: 20i).

Uso: python scripts/generate_static.py [dir_destino]

Gera `index.json` (resposta da raiz da API) e `health.json` no diretório
informado (padrão: ./static_out). Em caso de falha da fonte, sai com código
1 sem sobrescrever os arquivos anteriores.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402

ROTAS = (("/", "index.json"), ("/health", "health.json"))


def main() -> int:
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("static_out")
    destino.mkdir(parents=True, exist_ok=True)
    cliente = app.test_client()
    for rota, nome in ROTAS:
        resposta = cliente.get(rota)
        if resposta.status_code != 200:
            print(f"{nome}: fonte indisponível (HTTP {resposta.status_code})", file=sys.stderr)
            return 1
        (destino / nome).write_bytes(resposta.get_data())
        print(f"{nome}: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
