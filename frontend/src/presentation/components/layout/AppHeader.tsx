import type { ReactNode } from "react";
import { cn } from "../../utils/cn";

type AppHeaderVariant = "compact" | "tall";

interface AppHeaderProps {
  children: ReactNode;
  variant?: AppHeaderVariant;
  sticky?: boolean;
  className?: string;
}

export default function AppHeader({
  children,
  variant = "compact",
  sticky = false,
  className,
}: AppHeaderProps) {
  return (
    <header
      className={cn(
        "w-full border-b border-gray-200 bg-white/80 backdrop-blur-sm",
        sticky && "sticky top-0 z-10",
        variant === "compact"
          ? "h-14 px-4 flex items-center justify-between flex-shrink-0"
          : "px-6 py-4 flex items-center justify-between flex-shrink-0",
        className,
      )}
    >
      {children}
    </header>
  );
}
