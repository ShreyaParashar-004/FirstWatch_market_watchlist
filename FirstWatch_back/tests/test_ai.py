from app.providers.ai import MockAIAnalysisProvider, fallback_analysis, sanitize_analysis


def test_sanitize_drops_invented_urls():
    evidence = [{"source": "BBC", "url": "https://www.bbc.com/real", "title": "Real", "published_at": "2026-01-01"}]
    raw = {
        "event_type": "emerging_signal",
        "theme": "solar",
        "entities": ["Tesla"],
        "sentiment": "positive",
        "impact_direction": "positive",
        "potential_impact": "medium",
        "time_horizon": "short_term",
        "confidence": 0.8,
        "reason": "ok",
        "evidence": [
            {"source": "Fake", "url": "https://evil.example/invented", "title": "Nope"},
            {"source": "BBC", "url": "https://www.bbc.com/real", "title": "Real"},
        ],
    }
    result = sanitize_analysis(raw, evidence, {"watch_label": "solar"})
    urls = [e.get("url") for e in result.evidence]
    assert "https://evil.example/invented" not in urls
    assert "https://www.bbc.com/real" in urls


def test_ai_fallback_no_invention():
    evidence = [{"source": "Reuters", "url": "https://www.reuters.com/x", "title": "T", "content": "c"}]
    result = fallback_analysis(evidence, {"watch_label": "TSLA", "entities": ["TSLA"]})
    assert result.fallback is True
    assert result.event_type == "relevant_information"
    assert result.impact_direction == "uncertain"
    assert result.evidence == evidence


def test_mock_ai_uses_only_provided_evidence():
    provider = MockAIAnalysisProvider()
    evidence = [
        {
            "source": "Reuters",
            "url": "https://www.reuters.com/mock/tesla-battery-storage",
            "title": "Tesla expands battery storage",
            "content": "expand",
            "published_at": "2026-01-01",
        }
    ]
    result = provider.analyze(evidence, {"watch_label": "TSLA", "entities": ["TSLA"]})
    assert result.evidence[0]["url"] == evidence[0]["url"]
    assert result.impact_direction == "positive"


def test_mock_ai_failure_raises():
    provider = MockAIAnalysisProvider(fail=True)
    try:
        provider.analyze([], {})
        assert False, "expected failure"
    except RuntimeError as exc:
        assert "ai provider unavailable" in str(exc)
