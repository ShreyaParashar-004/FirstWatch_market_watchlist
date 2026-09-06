from datetime import datetime, timezone

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
        quotes = self.get_quotes(ticker)
        if not quotes:
            raise RuntimeError("no market data")
        return quotes[-1]

    def get_quotes(self, ticker: str) -> list[Quote]:
        import httpx

        headers = {"User-Agent": "FirstWatch/0.1 (market-intelligence; educational)"}
        requested_symbol = ticker.upper()
        symbols = [requested_symbol]
        if "." not in requested_symbol:
            symbols.append(f"{requested_symbol}.NS")
        data = None
        with httpx.Client(timeout=10.0) as client:
            for candidate in symbols:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{candidate}"
                resp = client.get(url, params={"interval": "1m", "range": "1d"}, headers=headers)
                if resp.status_code == 404 and candidate != symbols[-1]:
                    continue
                resp.raise_for_status()
                data = resp.json()
                break
        if data is None:
            raise RuntimeError("no market data")
        result = (data.get("chart") or {}).get("result") or []
        if not result:
            raise RuntimeError("no market data")
        chart = result[0]
        meta = chart.get("meta") or {}
        currency = meta.get("currency") or "USD"
        timestamps = chart.get("timestamp") or []
        closes = ((chart.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
        quotes = []
        for ts, close in zip(timestamps, closes):
            if ts is None or close is None:
                continue
            observed = datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)
            quotes.append(Quote(requested_symbol, float(close), currency, observed, "yahoo"))
        return quotes
