"use client";

import { TIMEZONE_OPTIONS } from "@/lib/timezone";
import { useTimezone } from "@/components/layout/TimezoneContext";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function TimezoneToggle() {
  const { timezone, setTimezone } = useTimezone();

  return (
    <div className="flex rounded-lg border border-slate-200 bg-slate-50 p-0.5">
      {TIMEZONE_OPTIONS.map((opt) => (
        <Button
          key={opt.value}
          variant="ghost"
          size="sm"
          className={cn(
            "h-7 px-2.5 text-xs",
            timezone === opt.value && "bg-white shadow-sm",
          )}
          onClick={() => setTimezone(opt.value)}
        >
          {opt.short}
        </Button>
      ))}
    </div>
  );
}
