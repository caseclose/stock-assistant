export type Theme = "light" | "dark";

export const THEME_STORAGE_KEY = "stock-assistant-theme";

export const DEFAULT_THEME: Theme = "dark";

export function loadStoredTheme(): Theme {
  if (typeof window === "undefined") return DEFAULT_THEME;
  const raw = localStorage.getItem(THEME_STORAGE_KEY);
  if (raw === "light" || raw === "dark") return raw;
  return DEFAULT_THEME;
}

export function storeTheme(theme: Theme) {
  localStorage.setItem(THEME_STORAGE_KEY, theme);
}

export type ChartTheme = {
  background: string;
  textColor: string;
  grid: string;
  border: string;
  crosshair: string;
  crosshairLabel: string;
  up: string;
  down: string;
  wickUp: string;
  wickDown: string;
  volumeUp: string;
  volumeDown: string;
  highlight: string;
};

export const CHART_THEME: Record<Theme, ChartTheme> = {
  light: {
    background: "#f6f9fc",
    textColor: "#64748b",
    grid: "rgba(14, 165, 233, 0.1)",
    border: "rgba(14, 165, 233, 0.2)",
    crosshair: "rgba(2, 132, 199, 0.5)",
    crosshairLabel: "#ffffff",
    up: "#059669",
    down: "#dc2626",
    wickUp: "#10b981",
    wickDown: "#ef4444",
    volumeUp: "rgba(5, 150, 105, 0.38)",
    volumeDown: "rgba(220, 38, 38, 0.35)",
    highlight: "#0284c7",
  },
  dark: {
    background: "#0a0f1a",
    textColor: "#94a3b8",
    grid: "rgba(34, 211, 238, 0.05)",
    border: "rgba(56, 189, 248, 0.12)",
    crosshair: "rgba(34, 211, 238, 0.35)",
    crosshairLabel: "#0c1220",
    up: "#34d399",
    down: "#f87171",
    wickUp: "#6ee7b7",
    wickDown: "#fca5a5",
    volumeUp: "rgba(52,211,153,0.35)",
    volumeDown: "rgba(248,113,113,0.35)",
    highlight: "#22d3ee",
  },
};
