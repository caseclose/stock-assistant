"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import {
  getGlossaryEntry,
  type GlossaryId,
  type GlossaryLang,
} from "@/lib/glossary";
import { cn } from "@/lib/utils";

type Props = {
  term: GlossaryId;
  lang?: GlossaryLang;
  /** Hover duration before tooltip opens (ms). */
  delayMs?: number;
  children: ReactNode;
  className?: string;
  /** Mouse hover only (e.g. inside another button). */
  hoverOnly?: boolean;
};

export function GlossaryTip({
  term,
  lang = "zh",
  delayMs = 650,
  children,
  className,
  hoverOnly = false,
}: Props) {
  const entry = getGlossaryEntry(term);
  const triggerRef = useRef<HTMLSpanElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState({ top: 0, left: 0 });

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const placeTooltip = useCallback(() => {
    const el = triggerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const width = 288;
    const left = Math.max(8, Math.min(rect.left, window.innerWidth - width - 8));
    const top = rect.bottom + 6;
    setPos({ top, left });
  }, []);

  const scheduleOpen = useCallback(() => {
    clearTimer();
    timerRef.current = setTimeout(() => {
      placeTooltip();
      setOpen(true);
    }, delayMs);
  }, [clearTimer, delayMs, placeTooltip]);

  const close = useCallback(() => {
    clearTimer();
    setOpen(false);
  }, [clearTimer]);

  useEffect(() => {
    if (!open) return;
    const onScroll = () => placeTooltip();
    window.addEventListener("scroll", onScroll, true);
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("resize", onScroll);
    };
  }, [open, placeTooltip]);

  useEffect(() => () => clearTimer(), [clearTimer]);

  if (!entry) {
    return <span className={className}>{children}</span>;
  }

  return (
    <>
      <span
        ref={triggerRef}
        className={cn(className)}
        onMouseEnter={scheduleOpen}
        onMouseLeave={close}
        onFocus={hoverOnly ? undefined : scheduleOpen}
        onBlur={hoverOnly ? undefined : close}
        tabIndex={hoverOnly ? undefined : 0}
        role={hoverOnly ? undefined : "button"}
        aria-describedby={open ? `glossary-${term}` : undefined}
      >
        {children}
      </span>
      {open &&
        typeof document !== "undefined" &&
        createPortal(
          <div
            id={`glossary-${term}`}
            role="tooltip"
            className="pointer-events-auto fixed z-[9999] w-72 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-elevated)] p-3 text-left shadow-panel backdrop-blur-md"
            style={{ top: pos.top, left: pos.left }}
            onMouseEnter={clearTimer}
            onMouseLeave={close}
          >
            <p className="text-sm font-semibold text-primary">{entry.title[lang]}</p>
            <p className="mt-1.5 text-xs leading-relaxed text-secondary">{entry.desc[lang]}</p>
            <p className="mt-2 rounded-md border border-[color:var(--border-subtle)] bg-[color:var(--accent-dim)] px-2 py-1.5 text-[11px] leading-relaxed text-secondary">
              <span className="font-medium text-accent">
                {lang === "zh" ? "示例" : "Example"}
              </span>
              {" · "}
              {entry.example[lang]}
            </p>
            <p className="mt-2 text-[10px] text-muted">
              {lang === "zh" ? "悬停约 0.6 秒显示 · 仅供参考" : "~0.6s hover · Info only"}
            </p>
          </div>,
          document.body,
        )}
    </>
  );
}
