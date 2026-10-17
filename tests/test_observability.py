"""Garante que o Sentry só liga com `SENTRY_DSN` e respeita a amostragem."""

import sentry_sdk
from fastapi.testclient import TestClient

from src.observability import init_sentry, traces_sampler


def test_sem_dsn_nao_inicializa(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    assert init_sentry(release="test") is False
    assert not sentry_sdk.get_client().is_active()


def test_app_sobe_sem_sentry(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    from src.api import app

    response = TestClient(app).get("/health")
    assert response.status_code == 200


def test_sampler_descarta_health_e_estaticos(monkeypatch):
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "0.05")
    assert traces_sampler({"asgi_scope": {"path": "/health"}}) == 0.0
    assert traces_sampler({"asgi_scope": {"path": "/static/app.js"}}) == 0.0
    assert traces_sampler({"asgi_scope": {"path": "/api/process"}}) == 0.05
