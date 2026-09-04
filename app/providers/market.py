from datetime import datetime, timedelta, timezone

from app.providers import Quote


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


MOCK_QUOTES: dict[str, Quote] = {
    "AAPL": Quote("AAPL", 190.0, "USD", utcnow(), "mock"),
    "TSLA": Quote("TSLA", 180.0, "USD", utcnow(), "mock"),
    "MSFT": Quote("MSFT", 420.0, "USD", utcnow(), "mock"),
}


class MockMarketDataProvider:
    def __init__(self, quotes: dict[str, Quote] | None = None, fail: bool = False):
        self.quotes = quotes if quotes is not None else dict(MOCK_QUOTES)
        self.fail = fail

    def get_quote(self, ticker: str) -> Quote:
        if self.fail:
            raise RuntimeError("market provider unavailable")
        key = ticker.upper()
        if key in self.quotes:
            q = self.quotes[key]
            return Quote(key, q.price, q.currency, utcnow(), q.source)
        return Quote(key, 100.0, "USD", utcnow(), "mock")


class YahooMarketDataProvider:
    """Single real market provider. Yahoo public chart endpoint. No API key."""

    def get_quote(self, ticker: str) -> Quote:
        import httpx

        symbol = ticker.upper()
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {"interval": "1m", "range": "1d"}
        headers = {"User-Agent": "FirstWatch/0.1 (market-intelligence; educational)"}
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        result = (data.get("chart") or {}).get("result") or []
        if not result:
            raise RuntimeError("no market data")
        meta = result[0].get("meta") or {}
        price = meta.get("regularMarketPrice")
        currency = meta.get("currency") or "USD"
        ts = meta.get("regularMarketTime")
        if price is None:
            raise RuntimeError("no price in payload")
        observed = datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None) if ts else utcnow()
        return Quote(symbol, float(price), currency, observed, "yahoo")


def utcnow_offset(seconds: int) -> datetime:
    return utcnow() + timedelta(seconds=seconds)
