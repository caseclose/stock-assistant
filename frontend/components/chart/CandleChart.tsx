"use client";

import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  HistogramSeries,
  IChartApi,
  ISeriesApi,
  LineSeries,
  Time,
} from "lightweight-charts";
import type { Bar, Interval, LevelItem } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

const MA_CONFIG: { key: string; label: string; color: string }[] = [
  { key: "sma5", label: "SMA5", color: "#94a3b8" },
  { key: "sma10", label: "SMA10", color: "#64748b" },
  { key: "sma20", label: "SMA20", color: "#3b82f6" },
  { key: "sma60", label: "SMA60", color: "#8b5cf6" },
  { key: "sma120", label: "SMA120", color: "#a855f7" },
  { key: "sma200", label: "SMA200", color: "#6366f1" },
  { key: "ema20", label: "EMA20", color: "#f59e0b" },
  { key: "ema50", label: "EMA50", color: "#ef4444" },
];

type Props = {
  symbol: string;
  interval: Interval;
  bars: Bar[];
  levels: LevelItem[];
  enabledMas: Set<string>;
  loading?: boolean;
  highlightedLevel?: number | null;
};

export function CandleChart({
  symbol,
  interval,
  bars,
  levels,
  enabledMas,
  loading,
  highlightedLevel,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const maRefs = useRef<Map<string, ISeriesApi<"Line">>>(new Map());
  const levelLinesRef = useRef<ReturnType<ISeriesApi<"Candlestick">["createPriceLine"]>[]>([]);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#ffffff" },
        textColor: "#334155",
      },
      grid: {
        vertLines: { color: "#f1f5f9" },
        horzLines: { color: "#f1f5f9" },
      },
      rightPriceScale: { borderColor: "#e2e8f0" },
      timeScale: { borderColor: "#e2e8f0", timeVisible: true },
      crosshair: { mode: 1 },
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
    });
    const candle = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });
    const volume = chart.addSeries(HistogramSeries, {
      color: "#cbd5e1",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    chartRef.current = chart;
    candleRef.current = candle;
    volumeRef.current = volume;

    const ro = new ResizeObserver(() => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    });
    ro.observe(containerRef.current);
    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      candleRef.current = null;
      volumeRef.current = null;
      maRefs.current.clear();
      levelLinesRef.current = [];
    };
  }, []);

  useEffect(() => {
    if (!candleRef.current || !volumeRef.current || bars.length === 0) return;
    candleRef.current.setData(
      bars.map((b) => ({
        time: b.time as Time,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      })),
    );
    volumeRef.current.setData(
      bars.map((b) => ({
        time: b.time as Time,
        value: b.volume,
        color: b.close >= b.open ? "rgba(16,185,129,0.4)" : "rgba(239,68,68,0.4)",
      })),
    );
    chartRef.current?.timeScale().fitContent();
  }, [bars]);

  useEffect(() => {
    const chart = chartRef.current;
    const candle = candleRef.current;
    if (!chart || !candle) return;

    for (const line of levelLinesRef.current) {
      candle.removePriceLine(line);
    }
    levelLinesRef.current = [];

    for (const lv of levels) {
      const isHl = highlightedLevel != null && Math.abs(lv.price - highlightedLevel) < 0.01;
      const color = lv.kind === "resistance" ? "#ef4444" : "#10b981";
      const line = candle.createPriceLine({
        price: lv.price,
        color: isHl ? "#0f172a" : color,
        lineWidth: isHl ? 2 : 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: lv.kind === "resistance" ? "R" : "S",
      });
      levelLinesRef.current.push(line);
    }
  }, [levels, highlightedLevel]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    for (const [key, series] of maRefs.current) {
      if (!enabledMas.has(key)) {
        chart.removeSeries(series);
        maRefs.current.delete(key);
      }
    }

    for (const cfg of MA_CONFIG) {
      if (!enabledMas.has(cfg.key)) continue;
      let series = maRefs.current.get(cfg.key);
      if (!series) {
        series = chart.addSeries(LineSeries, {
          color: cfg.color,
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
        });
        maRefs.current.set(cfg.key, series);
      }
      const data = bars
        .filter((b) => b[cfg.key] != null)
        .map((b) => ({ time: b.time as Time, value: b[cfg.key] as number }));
      series.setData(data);
    }
  }, [bars, enabledMas]);

  return (
    <div className="relative flex h-full min-h-[420px] flex-1 flex-col">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">{symbol}</h1>
          <p className="text-xs text-slate-500">{interval} · US equities</p>
        </div>
      </div>
      {loading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/70">
          <Skeleton className="h-full w-full" />
        </div>
      )}
      <div ref={containerRef} className="min-h-0 flex-1" />
    </div>
  );
}

export { MA_CONFIG };
