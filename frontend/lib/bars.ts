import type { Bar } from "@/lib/api";

export function mergeBars(older: Bar[], current: Bar[]): Bar[] {
  const map = new Map<number, Bar>();
  for (const b of older) map.set(b.time, b);
  for (const b of current) map.set(b.time, b);
  return [...map.values()].sort((a, b) => a.time - b.time);
}
