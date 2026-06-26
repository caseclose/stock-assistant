"use client";

import { useState } from "react";
import { BarChart3, Sparkles } from "lucide-react";
import type { Analysis, LevelItem } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { GlossaryTip } from "@/components/ui/GlossaryTip";
import { maGlossaryId, signalGlossaryId, sourceGlossaryId } from "@/lib/glossary";
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

function ScoreMeter({ score }: { score: number }) {
  const pct = Math.min(100, Math.max(0, score));
  const hue = pct >= 60 ? "from-emerald-500 to-cyan-400" : pct >= 40 ? "from-amber-500 to-yellow-400" : "from-red-500 to-orange-400";
  return (
    <div className="mt-3">
      <div className="h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
        <div
          className={cn("h-full rounded-full bg-gradient-to-r transition-all duration-500", hue)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function LevelCard({
  lv,
  lang,
  onHover,
}: {
  lv: LevelItem;
  lang: "zh" | "en";
  onHover: (p: number | null) => void;
}) {
  const isRes = lv.kind === "resistance";
  const isNear = lv.proximity === "near";
  return (
    <button
      type="button"
      className={cn(
        "w-full rounded-lg border p-3 text-left transition-all duration-200",
        isNear
          ? "border-[color:var(--border)] bg-[color:var(--surface)]/60 hover:border-[color:var(--accent)]/30 hover:bg-[color:var(--accent-dim)]"
          : "border-dashed hover:border-[color:var(--border)]",
      )}
      style={
        isNear
          ? undefined
          : {
              borderColor: "var(--level-far-border)",
              background: "var(--level-far-bg)",
            }
      }
      onMouseEnter={() => onHover(lv.price)}
      onMouseLeave={() => onHover(null)}
    >
      <div className="flex items-center justify-between gap-2">
        <Badge variant={isRes ? "danger" : "success"}>
          <GlossaryTip term={isRes ? "resistance" : "support"} lang={lang} hoverOnly>
            {isRes ? "压力" : "支撑"}
          </GlossaryTip>{" "}
          <GlossaryTip term="num_level_price" lang={lang} hoverOnly>
            <span className="mono-num">${lv.price.toFixed(2)}</span>
          </GlossaryTip>
        </Badge>
        <div className="flex flex-wrap items-center justify-end gap-1">
          <GlossaryTip term={isNear ? "near" : "far"} lang={lang} hoverOnly>
            <span
              className={cn(
                "rounded px-1.5 py-0.5 text-[10px]",
                isNear
                  ? "bg-[color:var(--tag-near-bg)] text-[color:var(--tag-near-text)]"
                  : "bg-[color:var(--tag-bg)] text-[color:var(--tag-text)]",
              )}
            >
              {isNear ? "近端" : "远端"}
            </span>
          </GlossaryTip>
          <GlossaryTip term={sourceGlossaryId(lv.source)} lang={lang} hoverOnly>
            <span
              className="rounded px-1.5 py-0.5 text-[10px]"
              style={{ background: "var(--tag-bg)", color: "var(--tag-text)" }}
            >
              {sourceLabel(lv.source)}
            </span>
          </GlossaryTip>
          {lv.flipped && (
            <GlossaryTip term="flipped" lang={lang} hoverOnly>
              <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] text-amber-700 dark:text-amber-300">
                翻转
              </span>
            </GlossaryTip>
          )}
          <GlossaryTip term="strength" lang={lang} hoverOnly>
            <span className="mono-num text-xs text-muted">强度 {lv.strength.toFixed(0)}</span>
          </GlossaryTip>
        </div>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-secondary">{lv.reason_zh}</p>
      <p className="mono-num mt-1 text-[11px] text-muted">
        <GlossaryTip term="num_touches" lang={lang} hoverOnly>
          {lv.touches} 次回踩
        </GlossaryTip>{" "}
        ·{" "}
        <GlossaryTip term="num_pivot_count" lang={lang} hoverOnly>
          {lv.pivots} pivots
        </GlossaryTip>{" "}
        ·{" "}
        <GlossaryTip term="num_volume_score" lang={lang} hoverOnly>
          量能 {lv.volume_score.toFixed(0)}
        </GlossaryTip>
        {lv.bounce_rate != null && (
          <>
            {" · "}
            <GlossaryTip term="bounce_rate" lang={lang} hoverOnly>
              守住 {lv.bounce_rate.toFixed(0)}%
            </GlossaryTip>
          </>
        )}
        {lv.hit_rate != null && (
          <>
            {" · "}
            <GlossaryTip term="hit_rate" lang={lang} hoverOnly>
              回测 {lv.hit_rate.toFixed(0)}%
            </GlossaryTip>
          </>
        )}
        {lv.ma_aligned.length > 0 ? ` · ${lv.ma_aligned.join("/")}` : ""} ·{" "}
        <GlossaryTip term="num_distance_pct" lang={lang} hoverOnly>
          {lv.distance_pct > 0 ? "+" : ""}
          {lv.distance_pct.toFixed(2)}%
        </GlossaryTip>
      </p>
    </button>
  );
}

function LevelSection({
  title,
  titleTerm,
  levels,
  lang,
  onHighlightLevel,
}: {
  title: string;
  titleTerm: "resistance" | "support";
  levels: LevelItem[];
  lang: "zh" | "en";
  onHighlightLevel?: (price: number | null) => void;
}) {
  const near = levels.filter((l) => l.proximity === "near");
  const far = levels.filter((l) => l.proximity === "far");

  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-primary">
        <GlossaryTip term={titleTerm} lang={lang}>
          {title}
        </GlossaryTip>
      </h3>
      {levels.length === 0 ? (
        <p className="text-xs text-muted">暂无显著{title.includes("压力") ? "压力位" : "支撑位"}</p>
      ) : (
        <div className="space-y-3">
          {near.length > 0 && (
            <div>
              <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-accent">
                <GlossaryTip term="near" lang={lang}>
                  近端 · 距现价 ≤15%
                </GlossaryTip>
              </p>
              <div className="space-y-2">
                {near.map((lv) => (
                  <LevelCard
                    key={`near-${lv.kind}-${lv.price}`}
                    lv={lv}
                    lang={lang}
                    onHover={onHighlightLevel ?? (() => {})}
                  />
                ))}
              </div>
            </div>
          )}
          {far.length > 0 && (
            <div>
              <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-muted">
                <GlossaryTip term="far" lang={lang}>
                  远端 · 历史结构
                </GlossaryTip>
              </p>
              <div className="space-y-2">
                {far.map((lv) => (
                  <LevelCard
                    key={`far-${lv.kind}-${lv.price}`}
                    lv={lv}
                    lang={lang}
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

function PanelShell({ children }: { children: React.ReactNode }) {
  return (
    <aside className="panel flex h-full w-80 shrink-0 flex-col shadow-panel">{children}</aside>
  );
}

export function AnalysisPanel({ analysis, loading, error, onHighlightLevel }: Props) {
  const [lang, setLang] = useState<"zh" | "en">("zh");

  if (loading) {
    return (
      <PanelShell>
        <div className="space-y-4 p-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      </PanelShell>
    );
  }

  if (error) {
    return (
      <PanelShell>
        <p className="p-4 text-sm text-red-600 dark:text-red-400">{error}</p>
      </PanelShell>
    );
  }

  if (!analysis) {
    return (
      <PanelShell>
        <div className="flex flex-1 flex-col items-center justify-center gap-2 p-4 text-muted">
          <Sparkles className="h-8 w-8 text-accent opacity-30" />
          <p className="text-sm">选择标的查看分析</p>
        </div>
      </PanelShell>
    );
  }

  const resistances = analysis.levels.filter((l) => l.kind === "resistance");
  const supports = analysis.levels.filter((l) => l.kind === "support");

  return (
    <PanelShell>
      <div className="border-b border-[color:var(--border)] p-4">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-accent" />
              <h2 className="text-sm font-semibold text-primary">分析 Analysis</h2>
            </div>
            <p className="mt-0.5 text-[10px] text-muted">
              {lang === "zh" ? "悬停术语或数字约 0.6 秒查看释义" : "Hover terms or numbers ~0.6s for help"}
            </p>
          </div>
          <div className="segmented text-xs">
            {(["zh", "en"] as const).map((l) => (
              <button
                key={l}
                type="button"
                onClick={() => setLang(l)}
                className={cn("segment-btn px-2 py-1", lang === l && "segment-btn-active")}
              >
                {l.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-3 flex items-end gap-2">
          <GlossaryTip term="verdict" lang={lang}>
            <Badge variant={verdictVariant(analysis.verdict)} className="text-sm">
              {verdictLabel(analysis.verdict)}
            </Badge>
          </GlossaryTip>
          <GlossaryTip term="composite" lang={lang}>
            <span className="mono-num text-3xl font-bold text-glow text-primary">
              {analysis.composite}
            </span>
          </GlossaryTip>
          <span className="mb-1 text-xs text-muted">
            <GlossaryTip term="num_score_scale" lang={lang}>
              / 100
            </GlossaryTip>
          </span>
        </div>
        <ScoreMeter score={analysis.composite} />
        <p className="mt-3 text-xs leading-relaxed text-secondary">
          {lang === "zh" ? analysis.summary_zh : analysis.summary_en}
        </p>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-4 p-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">
                <GlossaryTip term="signal_breakdown" lang={lang}>
                  信号分项
                </GlossaryTip>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {analysis.verdict_reasons.map((r) => (
                <div
                  key={r.key}
                  className="rounded-md border border-[color:var(--border-subtle)] bg-[color:var(--surface)]/50 px-2 py-1.5 text-xs"
                >
                  <div className="flex justify-between font-medium text-secondary">
                    <GlossaryTip term={signalGlossaryId(r.key)} lang={lang}>
                      <span className="capitalize">{r.key}</span>
                    </GlossaryTip>
                    <span className="mono-num">
                      <GlossaryTip term="num_sub_score" lang={lang}>
                        {r.score}
                      </GlossaryTip>
                      {" × "}
                      <GlossaryTip term="num_weight" lang={lang}>
                        {(r.weight * 100).toFixed(0)}%
                      </GlossaryTip>
                    </span>
                  </div>
                  <p className="mt-0.5 text-muted">
                    {lang === "zh" ? r.text_zh : r.text_en}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">
                <GlossaryTip term="ma" lang={lang}>
                  均线 MA
                </GlossaryTip>
              </CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-1 text-xs">
              {analysis.moving_averages.map((ma) => (
                <div
                  key={ma.name}
                  className={cn(
                    "mono-num rounded border px-2 py-1",
                    ma.relation === "above"
                      ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
                      : "border-red-500/25 bg-red-500/10 text-red-700 dark:text-red-300",
                  )}
                >
                  <GlossaryTip term={maGlossaryId(ma.name)} lang={lang}>
                    {ma.name}
                  </GlossaryTip>{" "}
                  <GlossaryTip term="num_ma_price" lang={lang}>
                    {ma.value.toFixed(2)}
                  </GlossaryTip>
                  <span className="ml-1 opacity-70">
                    (
                    <GlossaryTip term={ma.relation === "above" ? "ma_above" : "ma_below"} lang={lang}>
                      {ma.relation === "above" ? "上" : "下"}
                    </GlossaryTip>
                    )
                  </span>
                  <span className="ml-1 opacity-60">
                    <GlossaryTip term="num_ma_distance_pct" lang={lang}>
                      {ma.distance_pct > 0 ? "+" : ""}
                      {ma.distance_pct.toFixed(1)}%
                    </GlossaryTip>
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Separator className="bg-[color:var(--border-subtle)]" />

          {analysis.trendlines.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold text-primary">
                <GlossaryTip term="trendline" lang={lang}>
                  趋势线 Trendlines
                </GlossaryTip>
              </h3>
              <div className="space-y-1 text-xs text-secondary">
                {analysis.trendlines.map((tl, i) => (
                  <div
                    key={`tl-${i}`}
                    className="mono-num rounded border border-[color:var(--border)] bg-[color:var(--surface)]/50 px-2 py-1.5"
                  >
                    <GlossaryTip term={tl.kind === "resistance" ? "resistance" : "support"} lang={lang}>
                      {tl.kind === "resistance" ? "压力" : "支撑"}
                    </GlossaryTip>
                    斜线 ·{" "}
                    <GlossaryTip term="strength" lang={lang}>
                      强度 {tl.strength.toFixed(0)}
                    </GlossaryTip>{" "}
                    ·{" "}
                    <GlossaryTip term="num_trendline_end_price" lang={lang}>
                      终点 ${tl.p_end.toFixed(2)}
                    </GlossaryTip>
                  </div>
                ))}
              </div>
            </div>
          )}

          <LevelSection
            title="压力位 Resistance"
            titleTerm="resistance"
            levels={resistances}
            lang={lang}
            onHighlightLevel={onHighlightLevel}
          />

          <LevelSection
            title="支撑位 Support"
            titleTerm="support"
            levels={supports}
            lang={lang}
            onHighlightLevel={onHighlightLevel}
          />
        </div>
      </ScrollArea>
    </PanelShell>
  );
}
