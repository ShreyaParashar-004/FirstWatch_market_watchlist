from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Quote:
    ticker: str
    price: float
    currency: str
    observed_at: datetime
    source: str


@dataclass
class InformationRecord:
    canonical_id: str
    source: str
    url: str
    title: str
    content: str
    published_at: datetime
    retrieved_at: datetime
    is_primary: bool = False
    extra: dict = field(default_factory=dict)


@dataclass
class AnalysisResult:
    event_type: str
    theme: str
    entities: list[str]
    sentiment: str
    impact_direction: str
    potential_impact: str
    time_horizon: str
    confidence: float
    reason: str
    evidence: list[dict]
    fallback: bool = False


class MarketDataProvider(ABC):
    @abstractmethod
    def get_quote(self, ticker: str) -> Quote:
        raise NotImplementedError


class InformationProvider(ABC):
    @abstractmethod
    def fetch(self, query_hints: list[str]) -> list[InformationRecord]:
        raise NotImplementedError


class AIAnalysisProvider(ABC):
    @abstractmethod
    def analyze(self, evidence: list[dict], context: dict) -> AnalysisResult:
        raise NotImplementedError
