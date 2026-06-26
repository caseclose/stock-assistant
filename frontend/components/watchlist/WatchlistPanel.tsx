"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Plus, Trash2 } from "lucide-react";
import {
  addToWatchlist,
  fetchWatchlist,
  removeFromWatchlist,
  type WatchlistItem,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { formatSessionLabel } from "@/lib/session";
import { cn } from "@/lib/utils";

type Props = {
  selected: string | null;
  onSelect: (symbol: string) => void;
};

export function WatchlistPanel({ selected, onSelect }: Props) {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [adding, setAdding] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await fetchWatchlist();
      setItems(data.items);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setInitialLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 15_000);
    return () => clearInterval(id);
  }, [load]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    const sym = draft.trim().toUpperCase();
    if (!sym || adding) return;

    setAdding(true);
    setError(null);
    setInitialLoading(false);
    setItems((prev) => {
      if (prev.some((i) => i.symbol === sym)) return prev;
      return [
        ...prev,
        { symbol: sym, price: null, change_pct: null, market_state: null },
      ];
    });
    setDraft("");

    try {
      await addToWatchlist(sym);
      onSelect(sym);
      await load();
    } catch (err) {
      setItems((prev) => prev.filter((i) => i.symbol !== sym));
      setError(err instanceof Error ? err.message : "添加失败");
    } finally {
      setAdding(false);
    }
  }

  async function handleRemove(sym: string) {
    const prev = items;
    setItems((cur) => cur.filter((i) => i.symbol !== sym));
    try {
      await removeFromWatchlist(sym);
      await load();
    } catch (err) {
      setItems(prev);
      setError(err instanceof Error ? err.message : "删除失败");
    }
  }

  const showSkeleton = initialLoading && items.length === 0;

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-slate-900">自选 Watchlist</h2>
        <form onSubmit={handleAdd} className="mt-3 flex gap-2">
          <Input
            placeholder="AAPL"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="uppercase"
            disabled={adding}
          />
          <Button type="submit" size="icon" disabled={adding || !draft.trim()}>
            {adding ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
          </Button>
        </form>
        {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
      </div>
      <ScrollArea className="flex-1">
        <div className="p-2">
          {showSkeleton && (
            <div className="space-y-2 p-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          )}
          {!showSkeleton && items.length === 0 && (
            <p className="p-4 text-center text-sm text-slate-500">添加美股代码开始看盘</p>
          )}
          {items.map((item) => {
            const active = selected === item.symbol;
            const pct = item.change_pct;
            const up = pct != null && pct >= 0;
            return (
              <div
                key={item.symbol}
                className={cn(
                  "mb-1 flex w-full items-center justify-between rounded-lg px-3 py-2 transition-colors",
                  active ? "bg-slate-100 ring-1 ring-slate-300" : "hover:bg-slate-50",
                )}
              >
                <button
                  type="button"
                  onClick={() => onSelect(item.symbol)}
                  className="min-w-0 flex-1 text-left"
                >
                  <div className="font-medium text-slate-900">{item.symbol}</div>
                  <div className="text-xs text-slate-500">
                    {item.price != null ? `$${item.price.toFixed(2)}` : "—"}
                    {formatSessionLabel(item.market_state) &&
                      ` · ${formatSessionLabel(item.market_state)}`}
                  </div>
                </button>
                <div className="flex shrink-0 items-center gap-2">
                  {pct != null && (
                    <span className={cn("text-sm font-medium", up ? "text-emerald-600" : "text-red-600")}>
                      {up ? "+" : ""}
                      {pct.toFixed(2)}%
                    </span>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-slate-400 hover:text-red-600"
                    onClick={() => handleRemove(item.symbol)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </aside>
  );
}
