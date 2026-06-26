const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export type Interval = "1Min" | "5Min" | "15Min" | "1H" | "1D";

export const INTERVALS: { value: Interval; label: string }[] = [
  { value: "1Min", label: "1m" },
  { value: "5Min", label: "5m" },
  { value: "15Min", label: "15m" },
  { value: "1H", label: "1H" },
  { value: "1D", label: "1D" },
];

export type WatchlistItem = {
  symbol: string;
  price: number | null;
  change_pct: number | null;
  market_state: string | null;
};

export type Bar = {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  [key: string]: number;
};

export type VerdictReason = {
  key: string;
  score: number;
  weight: number;
  text_zh: string;
  text_en: string;
};

export type TrendlineItem = {
  kind: "resistance" | "support";
  t1: number;
  p1: number;
  t2: number;
  p2: number;
  t_end: number;
  p_end: number;
  strength: number;
};

export type LevelItem = {
  price: number;
  kind: "resistance" | "support";
  strength: number;
  touches: number;
  pivots: number;
  distance_pct: number;
  source: string;
  flipped: boolean;
  bounce_rate: number | null;
  volume_score: number;
  hit_rate: number | null;
  ma_aligned: string[];
  reason_zh: string;
  reason_en: string;
};

export type MovingAverage = {
  name: string;
  value: number;
  relation: "above" | "below";
  distance_pct: number;
};

export type MarketStatus = {
  status: string;
  label_zh: string;
  label_en: string;
  is_extended: boolean;
  is_open: boolean;
  now_ny: string;
  next_transition: string;
  countdown: string;
};

export type Analysis = {
  symbol: string;
  interval: string;
  verdict: string;
  composite: number;
  summary_zh: string;
  summary_en: string;
  verdict_reasons: VerdictReason[];
  levels: LevelItem[];
  trendlines: TrendlineItem[];
  moving_averages: MovingAverage[];
  components: Record<string, number>;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export function fetchWatchlist() {
  return api<{ items: WatchlistItem[] }>("/api/watchlist");
}

export function fetchMarketStatus() {
  return api<MarketStatus>("/api/market/status");
}

export function addToWatchlist(symbol: string) {
  return api<{ ok: boolean }>("/api/watchlist", {
    method: "POST",
    body: JSON.stringify({ symbol }),
  });
}

export function removeFromWatchlist(symbol: string) {
  return api<{ ok: boolean }>(`/api/watchlist/${encodeURIComponent(symbol)}`, {
    method: "DELETE",
  });
}

export function fetchBars(
  symbol: string,
  interval: Interval,
  limit = 300,
  extendedHours = true,
  before?: number,
) {
  const q = new URLSearchParams({
    interval,
    limit: String(limit),
    extended_hours: String(extendedHours),
  });
  if (before != null) {
    q.set("before", String(before));
  }
  return api<{ symbol: string; interval: string; bars: Bar[]; has_more: boolean }>(
    `/api/symbols/${encodeURIComponent(symbol)}/bars?${q}`,
  );
}

export function fetchAnalysis(
  symbol: string,
  interval: Interval,
  extendedHours = true,
) {
  const q = new URLSearchParams({
    interval,
    extended_hours: String(extendedHours),
  });
  return api<Analysis>(
    `/api/symbols/${encodeURIComponent(symbol)}/analysis?${q}`,
  );
}

export function subscribeStream(
  symbol: string,
  interval: Interval,
  extendedHours = true,
) {
  return api<{ ok: boolean }>("/api/stream/subscribe", {
    method: "POST",
    body: JSON.stringify({ symbol, interval, extended_hours: extendedHours }),
  });
}

export function streamWsUrl() {
  const base = API_BASE.replace(/^http/, "ws");
  return `${base}/ws/stream`;
}
