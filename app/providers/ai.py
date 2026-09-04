import json
import re

from app.providers import AnalysisResult, AIAnalysisProvider

ALLOWED_SENTIMENT = {"positive", "negative", "neutral", "mixed"}
ALLOWED_DIRECTION = {"positive", "negative", "mixed", "uncertain"}
ALLOWED_IMPACT = {"low", "medium", "high"}
ALLOWED_HORIZON = {"short_term", "medium_term", "long_term", "uncertain"}

SYSTEM_PROMPT = """You are a market-intelligence interpreter.
You MUST only use the provided evidence. Never invent news, articles, sources, URLs, dates, quotes, companies, prices, or market events.
If evidence is insufficient, use uncertain/neutral values.
Do not give buy/sell recommendations or guaranteed outcomes.
Return a single JSON object with keys:
event_type, theme, entities, sentiment, impact_direction, potential_impact, time_horizon, confidence, reason, evidence
evidence must be a list of objects copied from input (source, url, title, published_at) — do not add new ones.
Use language like: emerging signal, potential direction, potentially affected companies, confidence, evidence, time horizon.
"""


def fallback_analysis(evidence: list[dict], context: dict) -> AnalysisResult:
    entities = list(context.get("entities") or [])
    theme = context.get("theme") or context.get("watch_label") or ""
    return AnalysisResult(
        event_type="relevant_information",
        theme=theme,
        entities=entities,
        sentiment="neutral",
        impact_direction="uncertain",
        potential_impact="low",
        time_horizon="uncertain",
        confidence=0.3,
        reason="Relevant information detected. AI analysis unavailable; deterministic summary used.",
        evidence=list(evidence),
        fallback=True,
    )


def _clip(value: str, allowed: set[str], default: str) -> str:
    v = (value or "").strip().lower()
    return v if v in allowed else default


def sanitize_analysis(raw: dict, evidence: list[dict], context: dict) -> AnalysisResult:
    allowed_urls = {e.get("url") for e in evidence}
    cleaned_ev = []
    for item in raw.get("evidence") or []:
        if isinstance(item, dict) and item.get("url") in allowed_urls:
            cleaned_ev.append(item)
    if not cleaned_ev:
        cleaned_ev = list(evidence)
    entities = raw.get("entities") or context.get("entities") or []
    if not isinstance(entities, list):
        entities = []
    entities = [str(e) for e in entities][:20]
    try:
        conf = float(raw.get("confidence", 0.3))
    except (TypeError, ValueError):
        conf = 0.3
    conf = min(0.95, max(0.0, conf))
    return AnalysisResult(
        event_type=str(raw.get("event_type") or "relevant_information")[:128],
        theme=str(raw.get("theme") or context.get("watch_label") or "")[:255],
        entities=entities,
        sentiment=_clip(str(raw.get("sentiment", "")), ALLOWED_SENTIMENT, "neutral"),
        impact_direction=_clip(str(raw.get("impact_direction", "")), ALLOWED_DIRECTION, "uncertain"),
        potential_impact=_clip(str(raw.get("potential_impact", "")), ALLOWED_IMPACT, "low"),
        time_horizon=_clip(str(raw.get("time_horizon", "")), ALLOWED_HORIZON, "uncertain"),
        confidence=conf,
        reason=str(raw.get("reason") or "Relevant information detected.")[:2000],
        evidence=cleaned_ev,
        fallback=False,
    )


class MockAIAnalysisProvider(AIAnalysisProvider):
    def __init__(self, fail: bool = False):
        self.fail = fail

    def analyze(self, evidence: list[dict], context: dict) -> AnalysisResult:
        if self.fail:
            raise RuntimeError("ai provider unavailable")
        blob = " ".join(
            f"{e.get('title','')} {e.get('content','')}" for e in evidence
        ).lower()
        direction = "uncertain"
        sentiment = "neutral"
        impact = "low"
        if any(w in blob for w in ("expand", "incentive", "growth", "record")):
            direction = "positive"
            sentiment = "positive"
            impact = "medium"
        if any(w in blob for w in ("recall", "probe", "decline", "mixed")):
            if direction == "positive":
                direction = "mixed"
                sentiment = "mixed"
            else:
                direction = "negative"
                sentiment = "negative"
                impact = "medium"
        entities = list(context.get("entities") or [])
        return AnalysisResult(
            event_type="emerging_signal",
            theme=str(context.get("watch_label") or ""),
            entities=entities,
            sentiment=sentiment,
            impact_direction=direction,
            potential_impact=impact,
            time_horizon="short_term",
            confidence=0.5,
            reason="Emerging signal based only on provided evidence. Potential direction is interpretive, not a prediction of returns.",
            evidence=[{k: e.get(k) for k in ("source", "url", "title", "published_at")} for e in evidence],
            fallback=False,
        )


class OpenAIAnalysisProvider(AIAnalysisProvider):
    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def analyze(self, evidence: list[dict], context: dict) -> AnalysisResult:
        if not self.api_key:
            raise RuntimeError("ai provider unavailable")
        import httpx

        payload_evidence = [
            {
                "source": e.get("source"),
                "url": e.get("url"),
                "title": e.get("title"),
                "content": e.get("content"),
                "published_at": str(e.get("published_at")),
            }
            for e in evidence
        ]
        user = json.dumps({"context": context, "evidence": payload_evidence}, default=str)
        body = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{self.base_url}/chat/completions", headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
        text = data["choices"][0]["message"]["content"]
        text = re.sub(r"^```json\s*|\s*```$", "", text.strip())
        raw = json.loads(text)
        return sanitize_analysis(raw, payload_evidence, context)
