import type { Time } from "lightweight-charts";

export type DisplayTimezone = "Asia/Shanghai" | "America/New_York";

export const DEFAULT_TIMEZONE: DisplayTimezone = "Asia/Shanghai";

export const TIMEZONE_OPTIONS: { value: DisplayTimezone; label: string; short: string }[] = [
  { value: "Asia/Shanghai", label: "北京时间", short: "北京" },
  { value: "America/New_York", label: "美东时间", short: "美东" },
];

const STORAGE_KEY = "stock-assistant-timezone";

export function loadStoredTimezone(): DisplayTimezone {
  if (typeof window === "undefined") return DEFAULT_TIMEZONE;
  const v = localStorage.getItem(STORAGE_KEY);
  if (v === "Asia/Shanghai" || v === "America/New_York") return v;
  return DEFAULT_TIMEZONE;
}

export function storeTimezone(tz: DisplayTimezone) {
  localStorage.setItem(STORAGE_KEY, tz);
}

export function timezoneLabel(tz: DisplayTimezone): string {
  return TIMEZONE_OPTIONS.find((o) => o.value === tz)?.label ?? tz;
}

export function formatInstant(
  iso: string,
  tz: DisplayTimezone,
  withSeconds = false,
): string {
  const d = new Date(iso);
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: tz,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: withSeconds ? "2-digit" : undefined,
    hour12: false,
  }).format(d);
}

function timeToDate(time: Time): Date | null {
  if (typeof time === "number") {
    return new Date(time * 1000);
  }
  if (typeof time === "string") {
    return new Date(time);
  }
  if (time && typeof time === "object" && "year" in time) {
    return new Date(Date.UTC(time.year, time.month - 1, time.day));
  }
  return null;
}

function formatChartTime(d: Date, tz: DisplayTimezone, intraday: boolean): string {
  if (intraday) {
    return new Intl.DateTimeFormat("zh-CN", {
      timeZone: tz,
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(d);
  }
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: tz,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(d);
}

export function chartLocalization(tz: DisplayTimezone, intraday: boolean) {
  const fmt = (time: Time) => {
    const d = timeToDate(time);
    if (!d) return "";
    return formatChartTime(d, tz, intraday);
  };
  return {
    locale: "zh-CN",
    timeFormatter: fmt,
    dateFormatter: fmt,
  };
}
