import { cn } from "@/lib/utils";

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md", className)}
      style={{
        background: `linear-gradient(to right, var(--skeleton-from), var(--skeleton-via), var(--skeleton-from))`,
      }}
      {...props}
    />
  );
}

export { Skeleton };
