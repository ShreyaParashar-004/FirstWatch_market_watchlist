from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    companies: Mapped[list["WatchlistCompany"]] = relationship(back_populates="user")
    themes: Mapped[list["WatchlistTheme"]] = relationship(back_populates="user")
    signals: Mapped[list["Signal"]] = relationship(back_populates="user")


class WatchlistCompany(Base):
    __tablename__ = "watchlist_companies"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_user_ticker"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="companies")


class WatchlistTheme(Base):
    __tablename__ = "watchlist_themes"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_theme"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    keywords: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="themes")


class MarketObservation(Base):
    __tablename__ = "market_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True)
    price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source: Mapped[str] = mapped_column(String(64))


class InformationItem(Base):
    __tablename__ = "information_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_id: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(128), index=True)
    url: Mapped[str] = mapped_column(String(1024))
    title: Mapped[str] = mapped_column(String(1024))
    content: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    trusted: Mapped[bool] = mapped_column(Boolean, default=True)


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    watch_type: Mapped[str] = mapped_column(String(16))
    watch_id: Mapped[int] = mapped_column(Integer)
    watch_label: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(1024))
    summary: Mapped[str] = mapped_column(Text)
    event_type: Mapped[str] = mapped_column(String(128), default="relevant_information")
    direction: Mapped[str] = mapped_column(String(32), default="uncertain")
    sentiment: Mapped[str] = mapped_column(String(32), default="neutral")
    potential_impact: Mapped[str] = mapped_column(String(16), default="low")
    time_horizon: Mapped[str] = mapped_column(String(32), default="uncertain")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    affected_entities: Mapped[str] = mapped_column(Text, default="[]")
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    evidence_json: Mapped[str] = mapped_column(Text, default="[]")
    first_evidence_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    latest_evidence_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    market_already_moved: Mapped[bool] = mapped_column(Boolean, default=False)
    signal_kind: Mapped[str] = mapped_column(String(32), default="early")
    source_agreement: Mapped[str] = mapped_column(String(16), default="uncertain")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="signals")
