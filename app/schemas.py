from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr

    model_config = {"from_attributes": True}


class CompanyCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=32)
    name: str = ""


class CompanyOut(BaseModel):
    id: int
    ticker: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ThemeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    keywords: list[str] = Field(default_factory=list)


class ThemeOut(BaseModel):
    id: int
    name: str
    keywords: list[str]
    created_at: datetime


class ObservationOut(BaseModel):
    ticker: str
    price: float
    currency: str
    observed_at: datetime
    retrieved_at: datetime
    source: str


class ChangeDetail(BaseModel):
    type: str
    start_price: float
    end_price: float
    min_price: float
    max_price: float
    net_pct: float
    range_pct: float
    swing: bool
    significant: bool


class TrackingResponse(BaseModel):
    ticker: str
    status: Literal["ok", "stale", "no_data"]
    latest_price: float | None = None
    currency: str | None = None
    latest_observed_at: datetime | None = None
    window_hours: int
    significant_movement: bool = False
    change: ChangeDetail | None = None
    observations: list[ObservationOut] = Field(default_factory=list)
    message: str | None = None


class EvidenceOut(BaseModel):
    source: str
    url: str
    title: str
    published_at: datetime | None = None


class SignalOut(BaseModel):
    id: int
    watch_type: str
    watch_id: int
    watch_label: str
    title: str
    summary: str
    event_type: str
    direction: str
    sentiment: str
    potential_impact: str
    time_horizon: str
    confidence: float
    affected_entities: list[str]
    evidence_count: int
    evidence: list[EvidenceOut]
    first_evidence_at: datetime | None
    latest_evidence_at: datetime | None
    market_already_moved: bool
    signal_kind: str
    source_agreement: str
    created_at: datetime
    updated_at: datetime


class RefreshResult(BaseModel):
    ok: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class NotificationOut(BaseModel):
    id: int
    signal_id: int
    title: str
    watch_label: str
    created_at: datetime
    read_at: datetime | None


class ErrorResponse(BaseModel):
    detail: str
