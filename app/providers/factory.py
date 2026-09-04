from app.config import get_settings
from app.providers.ai import MockAIAnalysisProvider, OpenAIAnalysisProvider
from app.providers.information import MockInformationProvider, RssInformationProvider
from app.providers.market import MockMarketDataProvider, YahooMarketDataProvider


def get_market_provider():
    name = get_settings().market_data_provider.lower()
    if name == "yahoo":
        return YahooMarketDataProvider()
    return MockMarketDataProvider()


def get_information_provider():
    name = get_settings().information_provider.lower()
    if name in {"rss", "bbc"}:
        return RssInformationProvider()
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
    return MockAIAnalysisProvider()
