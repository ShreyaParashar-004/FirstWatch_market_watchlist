from app.config import get_settings
from app.providers.ai import MockAIAnalysisProvider, OpenAIAnalysisProvider
from app.providers.information import (
    GDELTInformationProvider,
    GoogleNewsRssInformationProvider,
    MockInformationProvider,
    RssInformationProvider,
)
from app.providers.market import MockMarketDataProvider, YahooMarketDataProvider


def get_market_provider():
    name = get_settings().market_data_provider.lower()
    if name == "yahoo":
        return YahooMarketDataProvider()
    return MockMarketDataProvider()


def get_information_provider():
    name = get_settings().information_provider.lower()
    if name in {"google", "google_news", "google-news"}:
        return GoogleNewsRssInformationProvider()
    if name in {"rss", "bbc"}:
        return RssInformationProvider()
    if name == "gdelt":
        return GDELTInformationProvider()
    return MockInformationProvider()


def get_ai_provider():
    settings = get_settings()
    name = settings.ai_provider.lower()
    if name in {"openai", "real"}:
        return OpenAIAnalysisProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            base_url=settings.openai_base_url,
        )
    if name == "groq":
        return OpenAIAnalysisProvider(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            base_url=settings.groq_base_url,
        )
    return MockAIAnalysisProvider()
