import hashlib
import re
from datetime import datetime

from app.providers import InformationRecord
from app.providers.information import host_of, is_primary_url, is_safe_external_url, is_trusted_url

UNTRUSTED_REJECT = "untrusted_or_incomplete"


def _norm_title(title: str) -> str:
    return re.sub(r"\s+", " ", (title or "").strip().lower())


def content_hash(source: str, title: str, url: str) -> str:
    blob = f"{source.lower()}|{_norm_title(title)}|{url.strip().lower()}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def validate_record(rec: InformationRecord) -> str | None:
    if not rec.title or not rec.title.strip():
        return UNTRUSTED_REJECT
    if not rec.url or not rec.url.startswith("http"):
        return UNTRUSTED_REJECT
    if not rec.source:
        return UNTRUSTED_REJECT
    if rec.published_at is None:
        return UNTRUSTED_REJECT
    if rec.source == "mock" or rec.url.startswith("https://www.reuters.com/mock"):
        return None
    if rec.canonical_id.startswith("mock-"):
        return None
    source_host = rec.source.strip().lower().removeprefix("www.")
    url_host = host_of(rec.url).removeprefix("www.")
    if not is_trusted_url(rec.url) and (
        not is_safe_external_url(rec.url) or source_host != url_host
    ):
        return UNTRUSTED_REJECT
    return None


def normalize(rec: InformationRecord) -> InformationRecord:
    rec.title = rec.title.strip()
    rec.content = (rec.content or "").strip()
    rec.url = rec.url.strip()
    rec.source = rec.source.strip()
    rec.is_primary = rec.is_primary or is_primary_url(rec.url)
    if isinstance(rec.published_at, datetime) and rec.published_at.tzinfo:
        rec.published_at = rec.published_at.replace(tzinfo=None)
    return rec


def deduplicate(records: list[InformationRecord]) -> list[InformationRecord]:
    seen_canon: set[str] = set()
    seen_hash: set[str] = set()
    seen_url: set[str] = set()
    out: list[InformationRecord] = []
    for rec in records:
        rec = normalize(rec)
        if validate_record(rec):
            continue
        url_key = rec.url.strip().lower()
        h = content_hash(rec.source, rec.title, rec.url)
        if rec.canonical_id in seen_canon or h in seen_hash or url_key in seen_url:
            continue
        seen_canon.add(rec.canonical_id)
        seen_hash.add(h)
        seen_url.add(url_key)
        out.append(rec)
    return out
