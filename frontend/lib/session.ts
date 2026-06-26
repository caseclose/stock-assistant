const SESSION_LABELS: Record<string, string> = {
  PRE: "盘前",
  PRE_MARKET: "盘前",
  REGULAR: "盘中",
  REGULAR_MARKET: "盘中",
  POST: "盘后",
  POSTPOST: "盘后",
  AFTER_HOURS: "盘后",
  CLOSED: "休市",
};

export function formatSessionLabel(state: string | null | undefined): string | null {
  if (!state) return null;
  return SESSION_LABELS[state] ?? state;
}
