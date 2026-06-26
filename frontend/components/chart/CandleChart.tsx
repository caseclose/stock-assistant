"use client";

import { useCallback, useEffect, useRef } from "react";
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
import type { Bar, Interval, LevelItem, TrendlineItem } from "@/lib/api";
import { useTheme } from "@/components/layout/ThemeContext";
import { CHART_THEME } from "@/lib/theme";
import { useTimezone } from "@/components/layout/TimezoneContext";
import { chartLocalization } from "@/lib/timezone";
import { GlossaryTip } from "@/components/ui/GlossaryTip";
import { Skeleton } from "@/components/ui/skeleton";

const MA_CONFIG: { key: string; label: string; color: string }[] = [
  { key: "sma5", label: "SMA5", color: "#94a3b8" },
  { key: "sma10", label: "SMA10", color: "#cbd5e1" },
  { key: "sma20", label: "SMA20", color: "#38bdf8" },
  { key: "sma60", label: "SMA60", color: "#a78bfa" },
  { key: "sma120", label: "SMA120", color: "#c084fc" },
  { key: "sma200", label: "SMA200", color: "#818cf8" },
  { key: "ema20", label: "EMA20", color: "#fbbf24" },
  { key: "ema50", label: "EMA50", color: "#fb7185" },
];

function needsMoreHistory(
  range: { from: number; to: number } | null,
  barCount: number,
  hasMore: boolean,
): boolean {
  if (!range || barCount === 0 || !hasMore) return false;
  if (range.from < 0) return true;
  if (range.to > barCount - 1 + 0.5) return true;
  if (range.to - range.from > barCount * 1.02) return true;
  if (range.from < barCount * 0.15) return true;
  return false;
}

function clampVisibleRange(
  chart: IChartApi,
  barCount: number,
  adjustingRef: { current: boolean },
) {
  const range = chart.timeScale().getVisibleLogicalRange();
  if (!range || barCount === 0) return;
  let from = Number(range.from);
  let to = Number(range.to);
  const span = to - from;
  if (to > barCount - 1) {
    const shift = to - (barCount - 1);
    from -= shift;
    to = barCount - 1;
  }
  if (from < 0) {
    from = 0;
    to = Math.min(barCount - 1, from + span);
  }
  if (from === Number(range.from) && to === Number(range.to)) return;

  adjustingRef.current = true;
  try {
    chart.timeScale().setVisibleLogicalRange({ from, to });
  } finally {
    adjustingRef.current = false;
  }
}

type Props = {
  symbol: string;
  interval: Interval;
  bars: Bar[];
  levels: LevelItem[];
  trendlines?: TrendlineItem[];
  enabledMas: Set<string>;
  loading?: boolean;
  highlightedLevel?: number | null;
  extendedHours?: boolean;
  hasMoreHistory?: boolean;
  loadingMore?: boolean;
  onLoadMore?: (beforeTime: number) => Promise<Bar[] | null>;
};

export function CandleChart({
  symbol,
  interval,
  bars,
  levels,
  trendlines = [],
  enabledMas,
  loading,
  highlightedLevel,
  extendedHours = true,
  hasMoreHistory = true,
  loadingMore = false,
  onLoadMore,
}: Props) {
  const { theme } = useTheme();
  const chartTheme = CHART_THEME[theme];
  const chartThemeRef = useRef(chartTheme);
  chartThemeRef.current = chartTheme;
  const { timezone, label: tzLabel } = useTimezone();
  const intraday = interval !== "1D";
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const maRefs = useRef<Map<string, ISeriesApi<"Line">>>(new Map());
  const levelLinesRef = useRef<ReturnType<ISeriesApi<"Candlestick">["createPriceLine"]>[]>([]);
  const trendlineSeriesRef = useRef<ISeriesApi<"Line">[]>([]);
  const barsRef = useRef<Bar[]>(bars);
  const shouldFitRef = useRef(true);
  const prevBarMetaRef = useRef({ len: 0, firstTime: null as number | null });
  const onLoadMoreRef = useRef(onLoadMore);
  const hasMoreRef = useRef(hasMoreHistory);
  const fillingRef = useRef(false);
  const rangeAdjustingRef = useRef(false);
  const fillHistoryRef = useRef<() => void>(() => {});
  const pushBarsToChartRef = useRef<
    (nextBars: Bar[], opts?: { fit?: boolean; shiftPrepended?: number }) => void
  >(() => {});

  const pushBarsToChart = useCallback(
    (
      nextBars: Bar[],
      opts: { fit?: boolean; shiftPrepended?: number } = {},
    ) => {
      const chart = chartRef.current;
      const candle = candleRef.current;
      const volume = volumeRef.current;
      if (!chart || !candle || !volume || nextBars.length === 0) return;

      candle.setData(
        nextBars.map((b) => ({
          time: b.time as Time,
          open: b.open,
          high: b.high,
          low: b.low,
          close: b.close,
        })),
      );
      volume.setData(
        nextBars.map((b) => ({
          time: b.time as Time,
          value: b.volume,
          color: b.close >= b.open ? chartThemeRef.current.volumeUp : chartThemeRef.current.volumeDown,
        })),
      );

      rangeAdjustingRef.current = true;
      try {
        if (opts.fit) {
          chart.timeScale().fitContent();
        } else if (opts.shiftPrepended && opts.shiftPrepended > 0) {
          const logicalRange = chart.timeScale().getVisibleLogicalRange();
          if (logicalRange) {
            chart.timeScale().setVisibleLogicalRange({
              from: logicalRange.from + opts.shiftPrepended,
              to: logicalRange.to + opts.shiftPrepended,
            });
          }
        }
        clampVisibleRange(chart, nextBars.length, rangeAdjustingRef);
      } finally {
        rangeAdjustingRef.current = false;
      }

      prevBarMetaRef.current = { len: nextBars.length, firstTime: nextBars[0]?.time ?? null };
      barsRef.current = nextBars;
    },
    [],
  );

  useEffect(() => {
    pushBarsToChartRef.current = pushBarsToChart;
  }, [pushBarsToChart]);

  useEffect(() => {
    barsRef.current = bars;
  }, [bars]);
  useEffect(() => {
    onLoadMoreRef.current = onLoadMore;
  }, [onLoadMore]);
  useEffect(() => {
    hasMoreRef.current = hasMoreHistory;
    if (hasMoreHistory) {
      requestAnimationFrame(() => fillHistoryRef.current());
    }
  }, [hasMoreHistory]);
  useEffect(() => {
    shouldFitRef.current = true;
    prevBarMetaRef.current = { len: 0, firstTime: null };
    fillingRef.current = false;
  }, [symbol, interval, extendedHours]);

  useEffect(() => {
    if (!containerRef.current) return;
    const t = chartThemeRef.current;
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: t.background },
        textColor: t.textColor,
      },
      grid: {
        vertLines: { color: t.grid },
        horzLines: { color: t.grid },
      },
      rightPriceScale: { borderColor: t.border },
      timeScale: {
        borderColor: t.border,
        timeVisible: true,
        fixLeftEdge: false,
        fixRightEdge: true,
      },
      crosshair: {
        mode: 1,
        vertLine: { color: t.crosshair, labelBackgroundColor: t.crosshairLabel },
        horzLine: { color: t.crosshair, labelBackgroundColor: t.crosshairLabel },
      },
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
    });
    const candle = chart.addSeries(CandlestickSeries, {
      upColor: t.up,
      downColor: t.down,
      borderVisible: false,
      wickUpColor: t.wickUp,
      wickDownColor: t.wickDown,
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

    const fillHistory = async () => {
      if (fillingRef.current) return;
      const load = onLoadMoreRef.current;
      const c = chartRef.current;
      if (!load || !c || !hasMoreRef.current) return;

      fillingRef.current = true;
      try {
        for (let guard = 0; guard < 12; guard += 1) {
          if (!hasMoreRef.current) break;
          const count = barsRef.current.length;
          const range = c.timeScale().getVisibleLogicalRange();
          if (!needsMoreHistory(range, count, hasMoreRef.current)) break;
          const oldest = barsRef.current[0]?.time;
          if (!oldest) break;
          const prevCount = count;
          const merged = await load(oldest);
          if (!merged || merged.length <= prevCount) break;
          const added = merged.length - prevCount;
          const prepended = added > 0 && merged[0]?.time !== oldest;
          pushBarsToChartRef.current(merged, { shiftPrepended: prepended ? added : 0 });
          await new Promise((r) => setTimeout(r, 0));
        }
      } finally {
        fillingRef.current = false;
      }
    };
    fillHistoryRef.current = () => {
      void fillHistory();
    };

    const onRange = () => {
      if (rangeAdjustingRef.current || fillingRef.current) return;
      fillHistoryRef.current();
    };
    chart.timeScale().subscribeVisibleLogicalRangeChange(onRange);

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
      chart.timeScale().unsubscribeVisibleLogicalRangeChange(onRange);
      chart.remove();
      chartRef.current = null;
      candleRef.current = null;
      volumeRef.current = null;
      maRefs.current.clear();
      levelLinesRef.current = [];
      trendlineSeriesRef.current = [];
    };
  }, []);

  useEffect(() => {
    const chart = chartRef.current;
    const candle = candleRef.current;
    if (!chart || !candle) return;
    const t = chartTheme;
    chart.applyOptions({
      layout: {
        background: { type: ColorType.Solid, color: t.background },
        textColor: t.textColor,
      },
      grid: {
        vertLines: { color: t.grid },
        horzLines: { color: t.grid },
      },
      rightPriceScale: { borderColor: t.border },
      timeScale: { borderColor: t.border },
      crosshair: {
        vertLine: { color: t.crosshair, labelBackgroundColor: t.crosshairLabel },
        horzLine: { color: t.crosshair, labelBackgroundColor: t.crosshairLabel },
      },
    });
    candle.applyOptions({
      upColor: t.up,
      downColor: t.down,
      wickUpColor: t.wickUp,
      wickDownColor: t.wickDown,
    });
    if (barsRef.current.length > 0) {
      pushBarsToChartRef.current(barsRef.current);
    }
  }, [theme, chartTheme]);

  useEffect(() => {
    chartRef.current?.applyOptions({
      timeScale: { timeVisible: intraday, secondsVisible: false },
      localization: chartLocalization(timezone, intraday),
    });
  }, [timezone, intraday]);

  const applyBarData = useCallback(() => {
    const chart = chartRef.current;
    if (!chart || bars.length === 0) return;

    const prev = prevBarMetaRef.current;
    const prepended =
      prev.len > 0 &&
      bars.length > prev.len &&
      bars[0]?.time !== prev.firstTime;
    const added = prepended ? bars.length - prev.len : 0;

    pushBarsToChart(bars, {
      fit: shouldFitRef.current,
      shiftPrepended: shouldFitRef.current ? 0 : added,
    });
    shouldFitRef.current = false;
    requestAnimationFrame(() => fillHistoryRef.current());
  }, [bars, pushBarsToChart]);

  useEffect(() => {
    applyBarData();
  }, [applyBarData]);

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
      const isRes = lv.kind === "resistance";
      const isFar = lv.proximity === "far";
      let color = isRes ? "#ef4444" : "#10b981";
      let lineWidth: 1 | 2 | 3 | 4 = isHl ? 3 : 1;
      let lineStyle: 0 | 1 | 2 | 3 | 4 = isFar ? 3 : 2;

      if (lv.source.startsWith("ma_")) {
        color = isRes ? "#f97316" : "#0ea5e9";
        lineStyle = isFar ? 3 : 0;
        lineWidth = isHl ? 3 : 2;
      } else if (lv.source === "volume_poc") {
        color = isRes ? "#dc2626" : "#059669";
        lineStyle = 0;
        lineWidth = isHl ? 3 : 2;
      } else if (lv.source === "volume_vah" || lv.source === "volume_val") {
        color = isRes ? "#f87171" : "#34d399";
        lineStyle = 3;
      } else if (lv.source === "trendline") {
        color = isRes ? "#b91c1c" : "#047857";
        lineStyle = 1;
        lineWidth = isHl ? 3 : 2;
      } else if (lv.flipped) {
        color = "#d97706";
        lineStyle = 1;
        lineWidth = isHl ? 3 : 2;
      } else if (lv.source.startsWith("fib_")) {
        color = isRes ? "#9333ea" : "#7c3aed";
        lineStyle = 2;
        lineWidth = isHl ? 3 : 1;
      } else if (lv.ma_aligned.length > 0) {
        lineWidth = isHl ? 3 : 2;
      }

      const srcTag =
        lv.source.startsWith("ma_")
          ? lv.source.replace("ma_", "").toUpperCase()
          : lv.source === "volume_poc"
          ? "POC"
          : lv.source.startsWith("fib_")
            ? lv.source.replace("fib_", "F")
            : lv.source === "trendline"
              ? "TL"
              : lv.flipped
                ? "X"
                : isRes
                  ? "R"
                  : "S";
      const line = candle.createPriceLine({
        price: lv.price,
        color: isHl ? chartTheme.highlight : isFar ? `${color}99` : color,
        lineWidth,
        lineStyle,
        axisLabelVisible: true,
        title: srcTag,
      });
      levelLinesRef.current.push(line);
    }
  }, [levels, highlightedLevel, chartTheme]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    for (const series of trendlineSeriesRef.current) {
      chart.removeSeries(series);
    }
    trendlineSeriesRef.current = [];

    for (const tl of trendlines) {
      const span = Math.max(tl.t2 - tl.t1, 1);
      const slope = (tl.p2 - tl.p1) / span;
      const t0 = tl.t1 - span;
      const p0 = tl.p1 - slope * span;
      const series = chart.addSeries(LineSeries, {
        color: tl.kind === "resistance" ? "rgba(239,68,68,0.8)" : "rgba(16,185,129,0.8)",
        lineWidth: 2,
        lineStyle: 0,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      });
      series.setData([
        { time: t0 as Time, value: p0 },
        { time: tl.t1 as Time, value: tl.p1 },
        { time: tl.t2 as Time, value: tl.p2 },
        { time: tl.t_end as Time, value: tl.p_end },
      ]);
      trendlineSeriesRef.current.push(series);
    }
  }, [trendlines]);

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
    <div className="relative flex h-full min-h-[420px] flex-1 flex-col bg-chart">
      <div className="toolbar-strip flex items-center justify-between px-4 py-2.5">
        <div>
          <h1 className="mono-num text-xl font-bold tracking-wide text-primary text-glow">
            {symbol}
          </h1>
          <p className="mono-num text-xs text-muted">
            <GlossaryTip term="interval">
              {interval}
            </GlossaryTip>{" "}
            · {tzLabel}
            {extendedHours ? (
              <>
                {" · "}
                <GlossaryTip term="extended_hours">
                  含盘前盘后
                </GlossaryTip>
              </>
            ) : (
              " · 仅正常盘"
            )}
            {hasMoreHistory ? " · 缩小自动加载更早" : " · 已到最早数据"}
            {" · "}
            <GlossaryTip term="poc">
              POC实线
            </GlossaryTip>
            {" · "}
            <GlossaryTip term="trendline">
              TL斜线
            </GlossaryTip>
            {" · "}
            <GlossaryTip term="fib">
              斐波紫虚线
            </GlossaryTip>
          </p>
        </div>
      </div>
      {loadingMore && !loading && (
        <div className="pointer-events-none absolute left-3 top-16 z-10 rounded-md border border-[color:var(--border)] bg-[color:var(--surface)]/90 px-2.5 py-1 text-xs text-accent shadow-glow-sm backdrop-blur-sm">
          加载更早 K 线…
        </div>
      )}
      {loading && (
        <div
          className="absolute inset-0 z-10 flex items-center justify-center backdrop-blur-sm"
          style={{ background: "color-mix(in srgb, var(--chart-bg) 82%, transparent)" }}
        >
          <Skeleton className="h-full w-full opacity-40" />
        </div>
      )}
      <div ref={containerRef} className="min-h-0 flex-1" />
    </div>
  );
}

export { MA_CONFIG };
