/**
 * State Badge component for displaying agent lifecycle states
 */

interface StateBadgeProps {
  state: "DEVELOPMENT" | "TESTING" | "PRODUCTION" | "DEPRECATED" | "ARCHIVED";
  size?: "sm" | "md" | "lg";
}

export function StateBadge({ state, size = "md" }: StateBadgeProps) {
  const getColors = () => {
    switch (state) {
      case "DEVELOPMENT":
        return "bg-gray-100 text-gray-800 border-gray-300";
      case "TESTING":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "PRODUCTION":
        return "bg-green-100 text-green-800 border-green-300";
      case "DEPRECATED":
        return "bg-orange-100 text-orange-800 border-orange-300";
      case "ARCHIVED":
        return "bg-red-100 text-red-800 border-red-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case "sm":
        return "px-2 py-1 text-xs";
      case "md":
        return "px-3 py-1.5 text-sm";
      case "lg":
        return "px-4 py-2 text-base";
      default:
        return "px-3 py-1.5 text-sm";
    }
  };

  return (
    <span
      className={`inline-flex items-center border rounded-full font-medium ${getColors()} ${getSizeClasses()}`}
    >
      {state}
    </span>
  );
}
