"use client";

import { useState } from "react";
import type { Analysis, LevelItem } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

type Props = {
  analysis: Analysis | null;
  loading?: boolean;
  error?: string | null;
  onHighlightLevel?: (price: number | null) => void;
};

function verdictVariant(verdict: string) {
  if (verdict.includes("BUY")) return "success" as const;
  if (verdict.includes("SELL")) return "danger" as const;
  return "warning" as const;
}

function verdictLabel(verdict: string) {
  const map: Record<string, string> = {
    STRONG_BUY: "强烈买入",
    BUY: "买入",
    HOLD: "观望",
    SELL: "卖出",
    STRONG_SELL: "强烈卖出",
  };
  return map[verdict] ?? verdict;
}

function sourceLabel(source: string) {
  const map: Record<string, string> = {
    swing: "摆动",
    volume_poc: "POC",
    volume_vah: "VAH",
    volume_val: "VAL",
    psychological: "整数",
    trendline: "趋势线",
    fib_236: "F23.6",
    fib_382: "F38.2",
    fib_500: "F50",
    fib_618: "F61.8",
    fib_786: "F78.6",
    ma_sma20: "SMA20",
    ma_sma50: "SMA50",
    ma_sma60: "SMA60",
    ma_sma120: "SMA120",
    ma_sma200: "SMA200",
    ma_ema20: "EMA20",
    ma_ema50: "EMA50",
  };
  return map[source] ?? source;
}

function LevelCard({
  lv,
  onHover,
}: {
  lv: LevelItem;
  onHover: (p: number | null) => void;
}) {
  const isRes = lv.kind === "resistance";
  const isNear = lv.proximity === "near";
  return (
    <button
      type="button"
      className={cn(
        "w-full rounded-lg border p-3 text-left transition-colors hover:border-slate-400 hover:bg-slate-50",
        isNear ? "border-slate-300 bg-white" : "border-dashed border-slate-200 bg-slate-50/80",
      )}
      onMouseEnter={() => onHover(lv.price)}
      onMouseLeave={() => onHover(null)}
    >
      <div className="flex items-center justify-between gap-2">
        <Badge variant={isRes ? "danger" : "success"}>
          {isRes ? "压力" : "支撑"} ${lv.price.toFixed(2)}
        </Badge>
        <div className="flex flex-wrap items-center justify-end gap-1">
          <span
            className={cn(
              "rounded px-1.5 py-0.5 text-[10px]",
              isNear ? "bg-sky-100 text-sky-800" : "bg-slate-200 text-slate-600",
            )}
          >
            {isNear ? "近端" : "远端"}
          </span>
          <span className="rounded bg-slate-200 px-1.5 py-0.5 text-[10px] text-slate-600">
            {sourceLabel(lv.source)}
          </span>
          {lv.flipped && (
            <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] text-amber-800">
              翻转
            </span>
          )}
          <span className="text-xs text-slate-500">强度 {lv.strength.toFixed(0)}</span>
        </div>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-slate-600">{lv.reason_zh}</p>
      <p className="mt-1 text-[11px] text-slate-400">
        {lv.touches} 次回踩 · {lv.pivots} pivots · 量能 {lv.volume_score.toFixed(0)}
        {lv.bounce_rate != null ? ` · 守住 ${lv.bounce_rate.toFixed(0)}%` : ""}
        {lv.hit_rate != null ? ` · 回测 ${lv.hit_rate.toFixed(0)}%` : ""}
        {lv.ma_aligned.length > 0 ? ` · ${lv.ma_aligned.join("/")}` : ""} ·{" "}
        {lv.distance_pct > 0 ? "+" : ""}
        {lv.distance_pct.toFixed(2)}%
      </p>
    </button>
  );
}

function LevelSection({
  title,
  levels,
  onHighlightLevel,
}: {
  title: string;
  levels: LevelItem[];
  onHighlightLevel?: (price: number | null) => void;
}) {
  const near = levels.filter((l) => l.proximity === "near");
  const far = levels.filter((l) => l.proximity === "far");

  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-slate-800">{title}</h3>
      {levels.length === 0 ? (
        <p className="text-xs text-slate-500">暂无显著{title.includes("压力") ? "压力位" : "支撑位"}</p>
      ) : (
        <div className="space-y-3">
          {near.length > 0 && (
            <div>
              <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-sky-700">
                近端 · 距现价 ≤15%
              </p>
              <div className="space-y-2">
                {near.map((lv) => (
                  <LevelCard
                    key={`near-${lv.kind}-${lv.price}`}
                    lv={lv}
                    onHover={onHighlightLevel ?? (() => {})}
                  />
                ))}
              </div>
            </div>
          )}
          {far.length > 0 && (
            <div>
              <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-slate-500">
                远端 · 历史结构
              </p>
              <div className="space-y-2">
                {far.map((lv) => (
                  <LevelCard
                    key={`far-${lv.kind}-${lv.price}`}
                    lv={lv}
                    onHover={onHighlightLevel ?? (() => {})}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function AnalysisPanel({ analysis, loading, error, onHighlightLevel }: Props) {
  const [lang, setLang] = useState<"zh" | "en">("zh");

  if (loading) {
    return (
      <aside className="flex h-full w-80 shrink-0 flex-col border-l border-slate-200 bg-slate-50 p-4">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="mt-4 h-40 w-full" />
      </aside>
    );
  }

  if (error) {
    return (
      <aside className="flex h-full w-80 shrink-0 flex-col border-l border-slate-200 bg-slate-50 p-4">
        <p className="text-sm text-red-600">{error}</p>
      </aside>
    );
  }

  if (!analysis) {
    return (
      <aside className="flex h-full w-80 shrink-0 flex-col border-l border-slate-200 bg-slate-50 p-4">
        <p className="text-sm text-slate-500">选择标的查看分析</p>
      </aside>
    );
  }

  const resistances = analysis.levels.filter((l) => l.kind === "resistance");
  const supports = analysis.levels.filter((l) => l.kind === "support");

  return (
    <aside className="flex h-full w-80 shrink-0 flex-col border-l border-slate-200 bg-slate-50">
      <div className="border-b border-slate-200 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">分析 Analysis</h2>
          <div className="flex rounded-md border border-slate-200 bg-white text-xs">
            {(["zh", "en"] as const).map((l) => (
              <button
                key={l}
                type="button"
                onClick={() => setLang(l)}
                className={cn(
                  "px-2 py-1",
                  lang === l ? "bg-slate-900 text-white" : "text-slate-600",
                )}
              >
                {l.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <Badge variant={verdictVariant(analysis.verdict)} className="text-sm">
            {verdictLabel(analysis.verdict)}
          </Badge>
          <span className="text-2xl font-bold text-slate-900">{analysis.composite}</span>
          <span className="text-xs text-slate-500">/ 100</span>
        </div>
        <p className="mt-2 text-xs leading-relaxed text-slate-600">
          {lang === "zh" ? analysis.summary_zh : analysis.summary_en}
        </p>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-4 p-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">信号分项</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {analysis.verdict_reasons.map((r) => (
                <div key={r.key} className="rounded-md bg-slate-100 px-2 py-1.5 text-xs">
                  <div className="flex justify-between font-medium text-slate-700">
                    <span className="capitalize">{r.key}</span>
                    <span>
                      {r.score} × {(r.weight * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="mt-0.5 text-slate-600">
                    {lang === "zh" ? r.text_zh : r.text_en}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">均线 MA</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-1 text-xs">
              {analysis.moving_averages.map((ma) => (
                <div
                  key={ma.name}
                  className={cn(
                    "rounded px-2 py-1",
                    ma.relation === "above" ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800",
                  )}
                >
                  {ma.name} {ma.value.toFixed(2)}
                  <span className="ml-1 opacity-70">
                    ({ma.relation === "above" ? "上" : "下"})
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Separator />

          {analysis.trendlines.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold text-slate-800">趋势线 Trendlines</h3>
              <div className="space-y-1 text-xs text-slate-600">
                {analysis.trendlines.map((tl, i) => (
                  <div key={`tl-${i}`} className="rounded border border-slate-200 bg-white px-2 py-1.5">
                    {tl.kind === "resistance" ? "压力" : "支撑"}斜线 · 强度 {tl.strength.toFixed(0)} ·
                    终点 ${tl.p_end.toFixed(2)}
                  </div>
                ))}
              </div>
            </div>
          )}

          <LevelSection
            title="压力位 Resistance"
            levels={resistances}
            onHighlightLevel={onHighlightLevel}
          />

          <LevelSection
            title="支撑位 Support"
            levels={supports}
            onHighlightLevel={onHighlightLevel}
          />
        </div>
      </ScrollArea>
    </aside>
  );
}
