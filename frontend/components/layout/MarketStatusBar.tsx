"use client";

import { useEffect, useState } from "react";
import { Activity } from "lucide-react";
import { fetchMarketStatus, type MarketStatus } from "@/lib/api";
import { formatInstant } from "@/lib/timezone";
import { useTimezone } from "@/components/layout/TimezoneContext";
import { cn } from "@/lib/utils";

const STATUS_STYLE: Record<string, string> = {
  PRE_MARKET: "bg-violet-500/10 text-violet-700 dark:text-violet-300 border-violet-500/25",
  REGULAR: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/25",
  AFTER_HOURS: "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/25",
  CLOSED: "bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/20",
};

const STATUS_DOT: Record<string, string> = {
  PRE_MARKET: "bg-violet-500 shadow-[0_0_8px_rgba(139,92,246,0.6)] dark:bg-violet-400",
  REGULAR: "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)] animate-pulse-slow dark:bg-emerald-400",
  AFTER_HOURS: "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.6)] dark:bg-amber-400",
  CLOSED: "bg-slate-400 dark:bg-slate-500",
};

export function MarketStatusBar() {
  const { timezone, label: tzLabel } = useTimezone();
  const [status, setStatus] = useState<MarketStatus | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const data = await fetchMarketStatus();
        if (!cancelled) {
          setStatus(data);
          setFailed(false);
        }
      } catch {
        if (!cancelled) setFailed(true);
      }
    };
    load();
    const id = setInterval(load, 60_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (failed && !status) {
    return (
      <div className="border-b border-[color:var(--border)] bg-[color:var(--toolbar-bg)] px-4 py-1.5 text-center text-xs text-muted backdrop-blur-sm">
        市场状态暂不可用
      </div>
    );
  }

  if (!status) return null;

  const nowLocal = formatInstant(status.now_ny, timezone);
  const nextLocal = formatInstant(status.next_transition, timezone);
  const styleKey = STATUS_STYLE[status.status] ?? STATUS_STYLE.CLOSED;
  const dotKey = STATUS_DOT[status.status] ?? STATUS_DOT.CLOSED;

  return (
    <div
      className={cn(
        "flex flex-wrap items-center justify-center gap-x-3 gap-y-1 border-b px-4 py-2 text-xs backdrop-blur-sm",
        styleKey,
      )}
    >
      <div className="flex items-center gap-2">
        <Activity className="h-3.5 w-3.5 opacity-70" />
        <span className={cn("h-1.5 w-1.5 rounded-full", dotKey)} />
        <span className="font-semibold tracking-wide">美股 {status.label_zh}</span>
      </div>
      <span className="hidden opacity-30 sm:inline">|</span>
      <span className="mono-num opacity-80">
        {tzLabel} {nowLocal}
      </span>
      <span className="hidden opacity-30 sm:inline">|</span>
      <span className="opacity-75">
        下次切换 <span className="mono-num font-medium">{status.countdown}</span>
        <span className="opacity-60">（{nextLocal}）</span>
      </span>
    </div>
  );
}
