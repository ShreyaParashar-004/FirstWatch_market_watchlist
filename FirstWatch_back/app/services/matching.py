import re
from dataclasses import dataclass

from app.models import WatchlistCompany, WatchlistTheme
from app.providers import InformationRecord


@dataclass
class Match:
    watch_type: str
    watch_id: int
    watch_label: str
    entities: list[str]
    record: InformationRecord


def _tokens(text: str) -> str:
    return f" {re.sub(r'[^a-z0-9]+', ' ', text.lower())} "


def _contains_term(blob: str, term: str) -> bool:
    term = term.strip().lower()
    if not term:
        return False
    if " " in term:
        return term in blob
    return f" {term} " in _tokens(blob)


def match_records(
    records: list[InformationRecord],
    companies: list[WatchlistCompany],
    themes: list[WatchlistTheme],
) -> list[Match]:
    matches: list[Match] = []
    for rec in records:
        blob = f"{rec.title} {rec.content}".lower()
        for company in companies:
            hit = _contains_term(blob, company.ticker)
            if company.name:
                hit = hit or _contains_term(blob, company.name)
            if hit:
                matches.append(
                    Match(
                        watch_type="company",
                        watch_id=company.id,
                        watch_label=company.ticker,
                        entities=[company.ticker] + ([company.name] if company.name else []),
                        record=rec,
                    )
                )
        for theme in themes:
            keywords = [k.strip() for k in (theme.keywords or "").split(",") if k.strip()]
            terms = [theme.name] + keywords
            if any(_contains_term(blob, t) for t in terms):
                matches.append(
                    Match(
                        watch_type="theme",
                        watch_id=theme.id,
                        watch_label=theme.name,
                        entities=terms[:10],
                        record=rec,
                    )
                )
    return matches
