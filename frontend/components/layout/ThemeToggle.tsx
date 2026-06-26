"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/components/layout/ThemeContext";
import { cn } from "@/lib/utils";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={cn(
        "flex h-7 items-center gap-1.5 rounded-md px-2.5 text-xs transition-all duration-200",
        "text-muted hover:text-primary hover:bg-[color:var(--hover-bg)]",
      )}
      title={isDark ? "切换浅色模式" : "切换深色模式"}
      aria-label={isDark ? "切换浅色模式" : "切换深色模式"}
    >
      {isDark ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
      <span className="hidden sm:inline">{isDark ? "浅色" : "深色"}</span>
    </button>
  );
}
