from datetime import timedelta

from app.models import MarketObservation
from app.providers.market import utcnow
from tests.conftest import auth_header


def test_register_login_me(client):
    headers = auth_header(client, "a@example.com")
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "a@example.com"


def test_auth_required(client):
    assert client.get("/api/watchlist/companies").status_code == 401


def test_user_isolation(client):
    h1 = auth_header(client, "u1@example.com")
    h2 = auth_header(client, "u2@example.com")
    created = client.post("/api/watchlist/companies", json={"ticker": "AAPL", "name": "Apple"}, headers=h1)
    assert created.status_code == 201
    listed = client.get("/api/watchlist/companies", headers=h2)
    assert listed.status_code == 200
    assert listed.json() == []
    other_id = created.json()["id"]
    stolen = client.delete(f"/api/watchlist/companies/{other_id}", headers=h2)
    assert stolen.status_code == 404


def test_company_and_theme_crud(client):
    h = auth_header(client, "watch@example.com")
    c = client.post("/api/watchlist/companies", json={"ticker": "tsla", "name": "Tesla"}, headers=h)
    assert c.status_code == 201
    assert c.json()["ticker"] == "TSLA"
    t = client.post(
        "/api/watchlist/themes",
        json={"name": "solar power", "keywords": ["solar", "renewable energy"]},
        headers=h,
    )
    assert t.status_code == 201
    assert "solar" in t.json()["keywords"]
    companies = client.get("/api/watchlist/companies", headers=h).json()
    themes = client.get("/api/watchlist/themes", headers=h).json()
    assert len(companies) == 1
    assert len(themes) == 1
    assert client.delete(f"/api/watchlist/companies/{companies[0]['id']}", headers=h).status_code == 204
    assert client.delete(f"/api/watchlist/themes/{themes[0]['id']}", headers=h).status_code == 204


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/api/health").json()["status"] == "ok"


def test_tracking_no_data_then_refresh(client):
    h = auth_header(client, "mkt@example.com")
    client.post("/api/watchlist/companies", json={"ticker": "AAPL", "name": "Apple"}, headers=h)
    empty = client.get("/api/tracking/AAPL", headers=h)
    assert empty.status_code == 200
    assert empty.json()["status"] == "no_data"
    refreshed = client.post("/api/tracking/refresh", params={"ticker": "AAPL"}, headers=h)
    assert refreshed.status_code == 200
    assert refreshed.json()["ok"] is True
    data = client.get("/api/tracking/AAPL", headers=h).json()
    assert data["status"] in {"ok", "stale"}
    assert data["latest_price"] is not None


def test_tracking_unwatched_404(client):
    h = auth_header(client, "none@example.com")
    assert client.get("/api/tracking/MSFT", headers=h).status_code == 404


def test_full_window_change_via_stored_observations(client, db):
    h = auth_header(client, "swing@example.com")
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
    data = client.get("/api/tracking/TSLA", params={"window_hours": 24}, headers=h).json()
    assert data["status"] in {"ok", "stale"}
    assert data["significant_movement"] is True
    assert data["change"]["swing"] is True
    assert len(data["observations"]) == 3


def test_stale_when_observations_old(client, db):
    h = auth_header(client, "stale@example.com")
    client.post("/api/watchlist/companies", json={"ticker": "MSFT", "name": "Microsoft"}, headers=h)
    old = utcnow() - timedelta(hours=5)
    db.add(
        MarketObservation(
            ticker="MSFT",
            price=400.0,
            currency="USD",
            observed_at=old,
            retrieved_at=old,
            source="mock",
        )
    )
    db.commit()
    data = client.get("/api/tracking/MSFT", headers=h).json()
    assert data["status"] == "stale"
    assert data["latest_price"] == 400.0
