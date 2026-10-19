"""API das leituras litúrgicas diárias (fonte: Canção Nova)."""

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from flask import Flask, Response, jsonify

from extractor.extractor_service import DEFAULT_URL, ExtractionError, extract

app = Flask(__name__)

# Atributos padrão de LogRecord que não devem vazar como campos extras do JSON.
_RESERVED_LOG_ATTRS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "stack_print",
        "taskName",
        "thread",
        "threadName",
    }
)


class JsonFormatter(logging.Formatter):
    """Formata registros de log como uma linha JSON estruturada."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        payload.update(
            {key: value for key, value in record.__dict__.items() if key not in _RESERVED_LOG_ATTRS}
        )
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    """Configura logging estruturado (uma linha JSON por evento) na raiz."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


configure_logging()


@app.route("/")
def homepage() -> tuple[Response, int] | Response:
    """Retorna as leituras litúrgicas do dia, com fallback para a última leitura em cache."""
    try:
        liturgy, from_cache = extract(os.getenv("LITURGIA_BASE_URL", DEFAULT_URL))
    except ExtractionError:
        logging.getLogger(__name__).error("extraction_failed_without_fallback")
        return jsonify({"error": "upstream_unavailable", "source": "Canção Nova"}), 502

    response = {
        "objective": (
            "A API_LITURGIA_DIARIA visa disponibilizar via api as leituras "
            "para facilitar a criação de aplicações que almejam a evangelização."
        ),
        "source": "Canção Nova (cache)" if from_cache else "Canção Nova",
        "today": liturgy,
    }
    return jsonify(response)


@app.route("/health")
def health() -> Response:
    """Health check simples para probes e monitoramento."""
    return jsonify(
        {
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


if __name__ == "__main__":
    app.run()
