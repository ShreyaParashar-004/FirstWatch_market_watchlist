import hashlib
import ipaddress
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse, urlencode

from app.providers import InformationRecord
from app.providers.market import utcnow

TRUSTED_HOSTS = {
    "reuters.com",
    "www.reuters.com",
    "apnews.com",
    "www.apnews.com",
    "bbc.com",
    "www.bbc.com",
    "bbc.co.uk",
    "www.bbc.co.uk",
    "feeds.bbci.co.uk",
    "ft.com",
    "www.ft.com",
    "bloomberg.com",
    "www.bloomberg.com",
    "cnbc.com",
    "www.cnbc.com",
    "wsj.com",
    "www.wsj.com",
    "sec.gov",
    "www.sec.gov",
    "federalreserve.gov",
    "www.federalreserve.gov",
}

PRIMARY_HOST_HINTS = ("sec.gov", "investor.", "ir.", "federalreserve.gov", "treasury.gov")

BBC_RSS = "https://feeds.bbci.co.uk/news/business/rss.xml"
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"
GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


def host_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def is_trusted_url(url: str) -> bool:
    host = host_of(url)
    if host in TRUSTED_HOSTS:
        return True
    return any(host.endswith("." + h) or host == h for h in TRUSTED_HOSTS)


def is_safe_external_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname
    if parsed.scheme != "https" or not hostname or parsed.username or parsed.password:
        return False
    hostname = hostname.lower()
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        return False
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return True
    return not (address.is_private or address.is_loopback or address.is_link_local or address.is_multicast)


def is_primary_url(url: str) -> bool:
    host = host_of(url)
    path = urlparse(url).path.lower()
    return any(h in host or h in path for h in PRIMARY_HOST_HINTS)


def parse_rss_date(value: str | None) -> datetime:
    if not value:
        return utcnow()
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return utcnow()


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").strip()


class MockInformationProvider:
    def __init__(self, records: list[InformationRecord] | None = None, fail: bool = False):
        self.fail = fail
        self.records = records if records is not None else default_mock_records()

    def fetch(self, query_hints: list[str]) -> list[InformationRecord]:
        if self.fail:
            raise RuntimeError("information provider unavailable")
        if not query_hints:
            return list(self.records)
        hints = [h.lower() for h in query_hints]
        matched = []
        for rec in self.records:
            blob = f"{rec.title} {rec.content}".lower()
            if any(h.lower() in blob or h.lower() in rec.title.lower() for h in hints):
                matched.append(rec)
        return matched or list(self.records)


class RssInformationProvider:
    """Single real information provider: BBC Business RSS (free, public)."""

    def __init__(self, feed_url: str = BBC_RSS):
        self.feed_url = feed_url

    def fetch(self, query_hints: list[str]) -> list[InformationRecord]:
        import httpx

        headers = {"User-Agent": "FirstWatch/0.1 (market-intelligence; educational)"}
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            resp = client.get(self.feed_url, headers=headers)
            resp.raise_for_status()
            xml_text = resp.text
        records = parse_rss(xml_text, source_name="BBC")
        if not query_hints:
            return records
        hints = [h.lower() for h in query_hints]
        filtered = []
        for rec in records:
            blob = f"{rec.title} {rec.content}".lower()
            if any(h in blob for h in hints):
                filtered.append(rec)
        return filtered if filtered else records


class GoogleNewsRssInformationProvider:
    """Free Google News RSS search provider."""

    def __init__(self, feed_url: str = GOOGLE_NEWS_RSS, max_records: int = 50):
        self.feed_url = feed_url
        self.max_records = max_records

    def fetch(self, query_hints: list[str]) -> list[InformationRecord]:
        import httpx

        hints = list(dict.fromkeys(h.strip() for h in query_hints if h.strip()))
        if not hints:
            return []
        headers = {"User-Agent": "FirstWatch/0.1 (market-intelligence; educational)"}
        records_by_url: dict[str, InformationRecord] = {}
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            for hint in hints:
                params = {
                    "q": hint,
                    "hl": "en-US",
                    "gl": "US",
                    "ceid": "US:en",
                }
                resp = client.get(
                    f"{self.feed_url}?{urlencode(params)}",
                    headers=headers,
                )
                resp.raise_for_status()
                for record in parse_rss(
                    resp.text,
                    source_name="news.google.com",
                    allow_untrusted=True,
                ):
                    records_by_url.setdefault(record.url.lower(), record)
                    if len(records_by_url) >= self.max_records:
                        break
                if len(records_by_url) >= self.max_records:
                    break
        return list(records_by_url.values())


class GDELTInformationProvider:
    """Free GDELT news search provider."""

    def __init__(self, api_url: str = GDELT_DOC_API, max_records: int = 50):
        self.api_url = api_url
        self.max_records = max_records

    def fetch(self, query_hints: list[str]) -> list[InformationRecord]:
        import httpx

        hints = [hint.strip() for hint in query_hints if hint.strip()]
        if not hints:
            return []
        query = "(" + " OR ".join(f'"{hint}"' for hint in dict.fromkeys(hints)) + ")"
        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": self.max_records,
            "sort": "datedesc",
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": "FirstWatch/0.1 (market-intelligence; educational)",
        }
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            resp = client.get(self.api_url, params=params, headers=headers)
            resp.raise_for_status()
            payload = resp.json()
        records: list[InformationRecord] = []
        retrieved_at = utcnow()
        for article in payload.get("articles", []):
            url = str(article.get("url") or "").strip()
            title = str(article.get("title") or "").strip()
            published_at = _parse_gdelt_date(article.get("seendate"))
            if not url.startswith(("http://", "https://")) or not title or published_at is None:
                continue
            canonical_id = hashlib.sha256(url.encode("utf-8")).hexdigest()
            records.append(
                InformationRecord(
                    canonical_id=canonical_id,
                    source=str(article.get("domain") or host_of(url)),
                    url=url,
                    title=title,
                    content="",
                    published_at=published_at,
                    retrieved_at=retrieved_at,
                    is_primary=is_primary_url(url),
                )
            )
        return records


def _parse_gdelt_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ")
    except (TypeError, ValueError):
        return None


def parse_rss(
    xml_text: str,
    source_name: str,
    allow_untrusted: bool = False,
) -> list[InformationRecord]:
    root = ET.fromstring(xml_text)
    items: list[InformationRecord] = []
    now = utcnow()
    for item in root.findall(".//item"):
        title = _strip_html((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        desc = _strip_html(item.findtext("description") or "")
        guid = (item.findtext("guid") or link).strip()
        pub = parse_rss_date(item.findtext("pubDate"))
        if not title or not link.startswith("http"):
            continue
        if not is_trusted_url(link) and source_name != "BBC" and not allow_untrusted:
            continue
        canonical = hashlib.sha256(guid.encode("utf-8")).hexdigest()
        items.append(
            InformationRecord(
                canonical_id=canonical,
                source=source_name,
                url=link,
                title=title,
                content=desc,
                published_at=pub,
                retrieved_at=now,
                is_primary=is_primary_url(link),
            )
        )
    return items


def default_mock_records() -> list[InformationRecord]:
    now = utcnow()
    return [
        InformationRecord(
            canonical_id="mock-tesla-battery-1",
            source="Reuters",
            url="https://www.reuters.com/mock/tesla-battery-storage",
            title="Tesla expands battery storage project pipeline",
            content=(
                "Tesla said it is expanding grid-scale battery storage deployments. "
                "The company cited demand from utilities for energy storage."
            ),
            published_at=now,
            retrieved_at=now,
            is_primary=False,
        ),
        InformationRecord(
            canonical_id="mock-solar-1",
            source="BBC",
            url="https://www.bbc.com/news/mock-solar-policy",
            title="Governments signal new solar power incentives",
            content=(
                "Several governments outlined potential incentives for solar power and "
                "renewable energy manufacturing. Details remain under consultation."
            ),
            published_at=now,
            retrieved_at=now,
            is_primary=False,
        ),
        InformationRecord(
            canonical_id="mock-apple-1",
            source="AP",
            url="https://apnews.com/mock/apple-supply",
            title="Apple suppliers report mixed component demand",
            content="Suppliers tied to Apple reported mixed orders for components used in upcoming devices.",
            published_at=now,
            retrieved_at=now,
            is_primary=False,
        ),
        InformationRecord(
            canonical_id="mock-recycle-1",
            source="FT",
            url="https://www.ft.com/mock/recyclable-materials",
            title="Recyclable materials standards under review",
            content="Regulators are reviewing standards for recyclable materials used in packaging and batteries.",
            published_at=now,
            retrieved_at=now,
            is_primary=False,
        ),
    ]
