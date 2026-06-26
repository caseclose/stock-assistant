"use client";

import { useEffect, useState } from "react";
import { fetchMarketStatus, type MarketStatus } from "@/lib/api";
import { formatInstant } from "@/lib/timezone";
import { useTimezone } from "@/components/layout/TimezoneContext";
import { cn } from "@/lib/utils";

const STATUS_STYLE: Record<string, string> = {
  PRE_MARKET: "bg-violet-100 text-violet-800 border-violet-200",
  REGULAR: "bg-emerald-100 text-emerald-800 border-emerald-200",
  AFTER_HOURS: "bg-amber-100 text-amber-800 border-amber-200",
  CLOSED: "bg-slate-100 text-slate-600 border-slate-200",
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
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-1.5 text-center text-xs text-slate-500">
        市场状态暂不可用
      </div>
    );
  }

  if (!status) return null;

  const nowLocal = formatInstant(status.now_ny, timezone);
  const nextLocal = formatInstant(status.next_transition, timezone);

  return (
    <div
      className={cn(
        "flex flex-wrap items-center justify-center gap-x-2 gap-y-1 border-b px-4 py-1.5 text-xs",
        STATUS_STYLE[status.status] ?? STATUS_STYLE.CLOSED,
      )}
    >
      <span className="font-semibold">美股 {status.label_zh}</span>
      <span className="opacity-70">·</span>
      <span className="opacity-80">
        {tzLabel} {nowLocal}
      </span>
      <span className="opacity-70">·</span>
      <span className="opacity-80">
        下次切换 {status.countdown}（{nextLocal}）
      </span>
    </div>
  );
}
