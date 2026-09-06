from datetime import timedelta

from app.models import MarketObservation
from app.providers.market import utcnow
from tests.conftest import auth_header


def test_signal_generation_early(client, db):
    h = auth_header(client, "sig@example.com")
    client.post("/api/watchlist/companies", json={"ticker": "TSLA", "name": "Tesla"}, headers=h)
    client.post(
        "/api/watchlist/themes",
        json={"name": "solar power", "keywords": ["solar", "renewable energy"]},
        headers=h,
    )
    db.add(
        MarketObservation(
            ticker="TSLA",
            price=180.0,
            currency="USD",
            observed_at=utcnow(),
            retrieved_at=utcnow(),
            source="mock",
        )
    )
    db.commit()
    refreshed = client.post("/api/signals/refresh", headers=h)
    assert refreshed.status_code == 200
    assert refreshed.json()["ok"] is True
    signals = client.get("/api/signals", headers=h).json()
    assert len(signals) >= 1
    kinds = {s["signal_kind"] for s in signals}
    assert "early" in kinds
    tesla = next(s for s in signals if s["watch_label"] == "TSLA")
    assert tesla["evidence_count"] >= 1
    assert tesla["evidence"][0]["url"]
    assert tesla["market_already_moved"] is False
    assert "Early signal" in tesla["summary"]


def test_signal_confirmed_when_market_moved(client, db):
    h = auth_header(client, "conf@example.com")
    client.post("/api/watchlist/companies", json={"ticker": "TSLA", "name": "Tesla"}, headers=h)
    t0 = utcnow() - timedelta(hours=3)
    for i, price in enumerate([180.0, 175.0, 180.0]):
        db.add(
            MarketObservation(
                ticker="TSLA",
                price=price,
                currency="USD",
                observed_at=t0 + timedelta(hours=i),
                retrieved_at=utcnow(),
                source="mock",
            )
        )
    db.commit()
    client.post("/api/signals/refresh", headers=h)
    signals = client.get("/api/signals", headers=h).json()
    tesla = next(s for s in signals if s["watch_label"] == "TSLA")
    assert tesla["signal_kind"] == "confirmed"
    assert tesla["market_already_moved"] is True
    assert "Confirmed movement" in tesla["summary"]


def test_signals_isolated(client):
    h1 = auth_header(client, "s1@example.com")
    h2 = auth_header(client, "s2@example.com")
    client.post("/api/watchlist/companies", json={"ticker": "TSLA", "name": "Tesla"}, headers=h1)
    client.post("/api/signals/refresh", headers=h1)
    assert client.get("/api/signals", headers=h2).json() == []


def test_ai_fallback_still_creates_signal(client, monkeypatch):
    from app.providers.ai import MockAIAnalysisProvider
    from app.services import signals as signals_mod

    monkeypatch.setattr(signals_mod, "get_ai_provider", lambda: MockAIAnalysisProvider(fail=True))
    h = auth_header(client, "failai@example.com")
    client.post(
        "/api/watchlist/themes",
        json={"name": "recyclable materials", "keywords": ["recyclable"]},
        headers=h,
    )
    result = client.post("/api/signals/refresh", headers=h)
    assert result.status_code == 200
    signals = client.get("/api/signals", headers=h).json()
    assert len(signals) >= 1
    assert "Relevant information detected" in signals[0]["summary"]
