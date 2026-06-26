"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchAnalysis,
  fetchBars,
  fetchWatchlist,
  INTERVALS,
  subscribeStream,
  streamWsUrl,
  type Analysis,
  type Bar,
  type Interval,
} from "@/lib/api";
import { mergeBars } from "@/lib/bars";
import { DisclaimerBanner } from "@/components/layout/DisclaimerBanner";
import { MarketStatusBar } from "@/components/layout/MarketStatusBar";
import { TimezoneProvider } from "@/components/layout/TimezoneContext";
import { TimezoneToggle } from "@/components/layout/TimezoneToggle";
import { ThemeProvider } from "@/components/layout/ThemeContext";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { WatchlistPanel } from "@/components/watchlist/WatchlistPanel";
import { CandleChart, MA_CONFIG } from "@/components/chart/CandleChart";
import { AnalysisPanel } from "@/components/analysis/AnalysisPanel";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";

const DEFAULT_MAS = new Set(["sma20", "ema20", "ema50"]);

export function AppShell() {
  const [symbol, setSymbol] = useState<string | null>(null);
  const [interval, setInterval] = useState<Interval>("1H");
  const [extendedHours, setExtendedHours] = useState(true);
  const [bars, setBars] = useState<Bar[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [enabledMas, setEnabledMas] = useState<Set<string>>(() => new Set(DEFAULT_MAS));
  const [barsLoading, setBarsLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [barsError, setBarsError] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [streamWarning, setStreamWarning] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [highlightedLevel, setHighlightedLevel] = useState<number | null>(null);
  const [hasMoreHistory, setHasMoreHistory] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const loadingMoreRef = useRef(false);
  const hasMoreRef = useRef(true);
  const barsRef = useRef<Bar[]>([]);

  useEffect(() => {
    barsRef.current = bars;
  }, [bars]);
  useEffect(() => {
    hasMoreRef.current = hasMoreHistory;
  }, [hasMoreHistory]);

  useEffect(() => {
    fetchWatchlist()
      .then((d) => {
        if (d.items.length > 0 && !symbol) setSymbol(d.items[0].symbol);
      })
      .catch(() => {});
  }, [symbol]);

  const loadChart = useCallback(async (sym: string, iv: Interval, ext: boolean) => {
    setBarsLoading(true);
    setBarsError(null);
    setHistoryError(null);
    try {
      const barsRes = await fetchBars(sym, iv, 500, ext);
      setBars(barsRes.bars);
      barsRef.current = barsRes.bars;
      setHasMoreHistory(barsRes.has_more);
      window.setTimeout(() => {
        void subscribeStream(sym, iv, ext)
          .then(() => setStreamWarning(null))
          .catch(() => {
            setStreamWarning("实时流连接失败，图表将仅定期刷新");
          });
      }, 0);
    } catch (e) {
      setBarsError(e instanceof Error ? e.message : "K线加载失败");
      setBars([]);
    } finally {
      setBarsLoading(false);
    }
  }, []);

  const handleLoadMore = useCallback(
    async (beforeTime: number): Promise<Bar[] | null> => {
      if (!symbol || loadingMoreRef.current || !hasMoreRef.current) {
        return barsRef.current.length ? barsRef.current : null;
      }
      loadingMoreRef.current = true;
      setLoadingMore(true);
      try {
        const res = await fetchBars(symbol, interval, 500, extendedHours, beforeTime);
        if (res.bars.length === 0) {
          setHasMoreHistory(false);
          hasMoreRef.current = false;
          return null;
        }
        const merged = mergeBars(res.bars, barsRef.current);
        barsRef.current = merged;
        setBars(merged);
        const hasMore = res.has_more;
        setHasMoreHistory(hasMore);
        hasMoreRef.current = hasMore;
        return merged;
      } catch (e) {
        setHistoryError(e instanceof Error ? e.message : "加载更早 K 线失败");
        return barsRef.current.length ? barsRef.current : null;
      } finally {
        loadingMoreRef.current = false;
        setLoadingMore(false);
      }
    },
    [symbol, interval, extendedHours],
  );

  const loadAnalysis = useCallback(async (sym: string, iv: Interval, ext: boolean) => {
    setAnalysisLoading(true);
    setAnalysisError(null);
    try {
      const res = await fetchAnalysis(sym, iv, ext);
      setAnalysis(res);
    } catch (e) {
      setAnalysisError(e instanceof Error ? e.message : "分析加载失败");
      setAnalysis(null);
    } finally {
      setAnalysisLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!symbol) return;
    setHasMoreHistory(true);
    loadChart(symbol, interval, extendedHours);
    loadAnalysis(symbol, interval, extendedHours);
  }, [symbol, interval, extendedHours, loadChart, loadAnalysis]);

  useEffect(() => {
    if (!symbol) return;
    let ws: WebSocket | null = null;
    let closed = false;

    function connect() {
      ws = new WebSocket(streamWsUrl());
      ws.onopen = () => {
        setStreamWarning(null);
      };
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data) as {
            type: string;
            symbol: string;
            interval: string;
            bar: Bar;
          };
          if (msg.type === "ping") return;
          if (msg.type !== "bar" || msg.symbol !== symbol || msg.interval !== interval) return;
          setBars((prev) => {
            if (prev.length === 0) return [msg.bar];
            const last = prev[prev.length - 1];
            if (last.time === msg.bar.time) {
              return [...prev.slice(0, -1), msg.bar];
            }
            return [...prev, msg.bar];
          });
        } catch {
          /* ignore */
        }
      };
      ws.onclose = () => {
        if (!closed) setTimeout(connect, 3000);
      };
    }
    connect();
    return () => {
      closed = true;
      ws?.close();
    };
  }, [symbol, interval]);

  function toggleMa(key: string) {
    setEnabledMas((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  return (
    <ThemeProvider>
    <TimezoneProvider>
      <div className="flex h-screen flex-col text-foreground">
        <DisclaimerBanner />
        <MarketStatusBar />
        <div className="flex min-h-0 flex-1">
          <WatchlistPanel
            selected={symbol}
            onSelect={(s) => {
              setSymbol(s);
              setHighlightedLevel(null);
            }}
          />
          <main className="flex min-w-0 flex-1 flex-col border-x border-[color:var(--border-subtle)]">
            <div className="toolbar-strip flex flex-wrap items-center gap-3 px-4 py-2.5">
              <div className="segmented">
                {INTERVALS.map((iv) => (
                  <button
                    key={iv.value}
                    type="button"
                    className={cn(
                      "segment-btn mono-num",
                      interval === iv.value && "segment-btn-active",
                    )}
                    onClick={() => setInterval(iv.value)}
                  >
                    {iv.label}
                  </button>
                ))}
              </div>
              <label className="flex cursor-pointer items-center gap-1.5 text-xs text-muted">
                <Checkbox
                  checked={extendedHours}
                  onCheckedChange={(v) => setExtendedHours(v === true)}
                />
                <span>盘前盘后</span>
              </label>
              <TimezoneToggle />
              <ThemeToggle />
              <div className="ml-auto flex flex-wrap items-center gap-3">
                {MA_CONFIG.map((ma) => (
                  <label
                    key={ma.key}
                    className="flex cursor-pointer items-center gap-1.5 text-xs text-muted"
                  >
                    <Checkbox
                      checked={enabledMas.has(ma.key)}
                      onCheckedChange={() => toggleMa(ma.key)}
                    />
                    <span style={{ color: ma.color }} className="mono-num">
                      {ma.label}
                    </span>
                  </label>
                ))}
              </div>
            </div>
            {barsError && <div className="alert-error px-4 py-2">{barsError}</div>}
            {streamWarning && !barsError && (
              <div className="alert-warn px-4 py-2">{streamWarning}</div>
            )}
            {historyError && !barsLoading && (
              <div className="alert-warn px-4 py-1.5 text-xs">{historyError}</div>
            )}
            {symbol ? (
              <CandleChart
                symbol={symbol}
                interval={interval}
                bars={bars}
                levels={analysis?.levels ?? []}
                trendlines={analysis?.trendlines ?? []}
                enabledMas={enabledMas}
                loading={barsLoading}
                highlightedLevel={highlightedLevel}
                extendedHours={extendedHours}
                hasMoreHistory={hasMoreHistory}
                loadingMore={loadingMore}
                onLoadMore={handleLoadMore}
              />
            ) : (
              <div className="flex flex-1 flex-col items-center justify-center gap-3 text-muted">
                <div className="h-12 w-12 rounded-full border border-[color:var(--border)] bg-[color:var(--accent-dim)] shadow-glow-sm" />
                <p className="text-sm text-secondary">从左侧自选列表选择标的</p>
                <p className="brand-mark">Select a symbol to begin</p>
              </div>
            )}
          </main>
          <AnalysisPanel
            analysis={analysis}
            loading={analysisLoading}
            error={analysisError}
            onHighlightLevel={setHighlightedLevel}
          />
        </div>
      </div>
    </TimezoneProvider>
    </ThemeProvider>
  );
}
