from app.providers import InformationRecord
from app.providers.information import default_mock_records
from app.providers.market import utcnow
from app.services.matching import match_records
from app.services.normalize import deduplicate, validate_record


def test_dedup_by_url_and_canonical():
    now = utcnow()
    a = InformationRecord("id-1", "Reuters", "https://www.reuters.com/a", "Hello", "x", now, now)
    b = InformationRecord("id-1", "Reuters", "https://www.reuters.com/a", "Hello", "x", now, now)
    c = InformationRecord("id-2", "Reuters", "https://www.reuters.com/a", "Hello", "x", now, now)
    d = InformationRecord("id-3", "BBC", "https://www.bbc.com/b", "Other", "y", now, now)
    out = deduplicate([a, b, c, d])
    assert len(out) == 2
    urls = {r.url for r in out}
    assert "https://www.bbc.com/b" in urls


def test_reject_incomplete_untrusted():
    now = utcnow()
    bad = InformationRecord("x", "", "not-a-url", "", "", now, now)
    assert validate_record(bad) is not None
    ok = default_mock_records()[0]
    assert validate_record(ok) is None


def test_watchlist_matching_company_and_theme():
    records = default_mock_records()
    companies = [type("C", (), {"id": 1, "ticker": "TSLA", "name": "Tesla"})()]
    themes = [type("T", (), {"id": 2, "name": "solar power", "keywords": "solar,renewable energy"})()]
    matches = match_records(records, companies, themes)
    labels = {(m.watch_type, m.watch_label) for m in matches}
    assert ("company", "TSLA") in labels
    assert ("theme", "solar power") in labels
