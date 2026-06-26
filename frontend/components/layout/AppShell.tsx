"use client";

import { useCallback, useEffect, useState } from "react";
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
import { DisclaimerBanner } from "@/components/layout/DisclaimerBanner";
import { WatchlistPanel } from "@/components/watchlist/WatchlistPanel";
import { CandleChart, MA_CONFIG } from "@/components/chart/CandleChart";
import { AnalysisPanel } from "@/components/analysis/AnalysisPanel";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";

const DEFAULT_MAS = new Set(["sma20", "ema20", "ema50"]);

export function AppShell() {
  const [symbol, setSymbol] = useState<string | null>(null);
  const [interval, setInterval] = useState<Interval>("1H");
  const [bars, setBars] = useState<Bar[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [enabledMas, setEnabledMas] = useState<Set<string>>(() => new Set(DEFAULT_MAS));
  const [barsLoading, setBarsLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [barsError, setBarsError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [highlightedLevel, setHighlightedLevel] = useState<number | null>(null);

  useEffect(() => {
    fetchWatchlist()
      .then((d) => {
        if (d.items.length > 0 && !symbol) setSymbol(d.items[0].symbol);
      })
      .catch(() => {});
  }, [symbol]);

  const loadChart = useCallback(async (sym: string, iv: Interval) => {
    setBarsLoading(true);
    setBarsError(null);
    try {
      const [barsRes] = await Promise.all([
        fetchBars(sym, iv),
        subscribeStream(sym, iv).catch(() => {}),
      ]);
      setBars(barsRes.bars);
    } catch (e) {
      setBarsError(e instanceof Error ? e.message : "K线加载失败");
      setBars([]);
    } finally {
      setBarsLoading(false);
    }
  }, []);

  const loadAnalysis = useCallback(async (sym: string, iv: Interval) => {
    setAnalysisLoading(true);
    setAnalysisError(null);
    try {
      const res = await fetchAnalysis(sym, iv);
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
    loadChart(symbol, interval);
    loadAnalysis(symbol, interval);
  }, [symbol, interval, loadChart, loadAnalysis]);

  useEffect(() => {
    if (!symbol) return;
    let ws: WebSocket | null = null;
    let closed = false;

    function connect() {
      ws = new WebSocket(streamWsUrl());
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data) as {
            type: string;
            symbol: string;
            interval: string;
            bar: Bar;
          };
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
    <div className="flex h-screen flex-col bg-white text-slate-900">
      <DisclaimerBanner />
      <div className="flex min-h-0 flex-1">
        <WatchlistPanel
          selected={symbol}
          onSelect={(s) => {
            setSymbol(s);
            setHighlightedLevel(null);
          }}
        />
        <main className="flex min-w-0 flex-1 flex-col">
          <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 px-4 py-2">
            <div className="flex rounded-lg border border-slate-200 bg-slate-50 p-0.5">
              {INTERVALS.map((iv) => (
                <Button
                  key={iv.value}
                  variant="ghost"
                  size="sm"
                  className={cn(
                    "h-7 px-3",
                    interval === iv.value && "bg-white shadow-sm",
                  )}
                  onClick={() => setInterval(iv.value)}
                >
                  {iv.label}
                </Button>
              ))}
            </div>
            <div className="ml-auto flex flex-wrap items-center gap-3">
              {MA_CONFIG.map((ma) => (
                <label key={ma.key} className="flex cursor-pointer items-center gap-1.5 text-xs text-slate-600">
                  <Checkbox
                    checked={enabledMas.has(ma.key)}
                    onCheckedChange={() => toggleMa(ma.key)}
                  />
                  <span style={{ color: ma.color }}>{ma.label}</span>
                </label>
              ))}
            </div>
          </div>
          {barsError && (
            <div className="border-b border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
              {barsError}
            </div>
          )}
          {symbol ? (
            <CandleChart
              symbol={symbol}
              interval={interval}
              bars={bars}
              levels={analysis?.levels ?? []}
              enabledMas={enabledMas}
              loading={barsLoading}
              highlightedLevel={highlightedLevel}
            />
          ) : (
            <div className="flex flex-1 items-center justify-center text-slate-500">
              从左侧自选列表选择标的
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
  );
}
