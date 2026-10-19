#!/usr/bin/env python3
"""Fallback CGI para hospedagens sem WSGI dedicado (execução lenta, use só se necessário).

Requisitos: Python >= 3.9 com dependências instaladas, handler CGI habilitado
e permissão de execução (chmod +x).
"""

import sys
from pathlib import Path
from wsgiref.handlers import CGIHandler

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402

CGIHandler().run(app)
