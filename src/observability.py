"""Rastreamento de erros com Sentry, ligado somente quando há `SENTRY_DSN`."""

from __future__ import annotations

import os
from typing import Any

import sentry_sdk

# Rotas sem valor para traces: só geram volume na cota do Sentry.
IGNORED_TRANSACTIONS = ("/health", "/sw.js", "/static")


def traces_sampler(context: dict[str, Any]) -> float:
    """Descarta health check e estáticos; o resto segue a taxa configurada."""
    path = (context.get("asgi_scope") or {}).get("path", "")
    if path.startswith(IGNORED_TRANSACTIONS):
        return 0.0
    return float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.05"))


def init_sentry(release: str) -> bool:
    """Inicializa o Sentry se `SENTRY_DSN` estiver definido.

    Sem a variável nada é enviado: quem roda o photo3x4 localmente não
    manda dados para lugar nenhum. As fotos nunca são anexadas aos eventos:
    nem o corpo da requisição nem as variáveis locais da pilha (que teriam os
    bytes da imagem) são enviados.
    """
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return False
    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        release=f"photo3x4@{release}",
        send_default_pii=False,
        max_request_body_size="never",
        include_local_variables=False,
        traces_sampler=traces_sampler,
    )
    return True
