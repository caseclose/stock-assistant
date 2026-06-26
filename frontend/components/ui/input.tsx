import * as React from "react";
import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      className={cn(
        "flex h-9 w-full rounded-md border border-[color:var(--border)] px-3 py-1 font-mono text-sm text-primary shadow-sm transition-colors placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--accent)]/35 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      style={{ background: "var(--input-bg)" }}
      ref={ref}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export { Input };
