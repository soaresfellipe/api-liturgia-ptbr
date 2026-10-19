"""Entrypoint WSGI para hospedagens compartilhadas (mod_wsgi, Passenger e similares).

Aponte o painel/`.htaccess` para este arquivo: ele expõe o callable
`application` que servidores WSGI esperam.
"""

from app import app

application = app
