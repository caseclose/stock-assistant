"use client";

import { TIMEZONE_OPTIONS } from "@/lib/timezone";
import { useTimezone } from "@/components/layout/TimezoneContext";
import { cn } from "@/lib/utils";

export function TimezoneToggle() {
  const { timezone, setTimezone } = useTimezone();

  return (
    <div className="segmented">
      {TIMEZONE_OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          className={cn(
            "segment-btn px-2.5",
            timezone === opt.value && "segment-btn-active",
          )}
          onClick={() => setTimezone(opt.value)}
        >
          {opt.short}
        </button>
      ))}
    </div>
  );
}
