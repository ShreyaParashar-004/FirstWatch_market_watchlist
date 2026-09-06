// Types mirror the FastAPI backend schemas. No data is invented client-side.

export interface AuthUser {
  id?: number | string;
  email?: string;
  [key: string]: unknown;
}

export interface TokenResponse {
  access_token?: string;
  token?: string;
  token_type?: string;
  [key: string]: unknown;
}

export interface WatchCompany {
  id: number;
  ticker?: string | null;
  name?: string | null;
  [key: string]: unknown;
}

export interface WatchTheme {
  id: number;
  name?: string | null;
  keyword?: string | null;
  [key: string]: unknown;
}

export interface Observation {
  ticker: string;
  price: number | null;
  currency: string | null;
  observed_at: string | null;
  retrieved_at: string | null;
  source: string | null;
}

export interface TrackingChange {
  type: string | null;
  start_price: number | null;
  end_price: number | null;
  min_price: number | null;
  max_price: number | null;
  net_pct: number | null;
  range_pct: number | null;
  swing: boolean | null;
  significant: boolean | null;
}

export interface Tracking {
  ticker: string;
  status: string;
  latest_price: number | null;
  currency: string | null;
  latest_observed_at: string | null;
  window_hours: number | null;
  significant_movement: boolean | null;
  change: TrackingChange | null;
  observations: Observation[];
  message: string | null;
}

export interface SignalEvidence {
  source: string | null;
  url: string | null;
  title: string | null;
  published_at: string | null;
}

export interface Signal {
  id: number;
  watch_type: string | null;
  watch_id: number | null;
  watch_label: string | null;
  title: string | null;
  summary: string | null;
  event_type: string | null;
  direction: string | null;
  sentiment: string | null;
  potential_impact: string | null;
  time_horizon: string | null;
  confidence: number | null;
  affected_entities: string[] | null;
  evidence_count: number | null;
  evidence: SignalEvidence[] | null;
  first_evidence_at: string | null;
  latest_evidence_at: string | null;
  market_already_moved: boolean | null;
  signal_kind: string | null;
  source_agreement: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Notification {
  id: number;
  signal_id: number;
  title: string;
  watch_label: string;
  created_at: string;
  read_at: string | null;
}
