/**
 * Metrics Chart component using Recharts
 */

import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
}

interface MetricsChartProps {
  data: ChartDataPoint[];
  title: string;
  type: "bar" | "pie";
  isLoading?: boolean;
}

const DEFAULT_COLORS = [
  "#3b82f6", // blue
  "#10b981", // green
  "#f59e0b", // amber
  "#ef4444", // red
  "#8b5cf6", // purple
  "#06b6d4", // cyan
];

export default function MetricsChart({
  data,
  title,
  type,
  isLoading = false,
}: MetricsChartProps) {
  if (isLoading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <p className="mb-4 text-lg font-semibold text-gray-900">{title}</p>
        <div className="h-64 bg-gray-100 animate-pulse rounded" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <p className="mb-4 text-lg font-semibold text-gray-900">{title}</p>
        <div className="flex h-64 items-center justify-center text-gray-500">
          No data available
        </div>
      </div>
    );
  }

  // Prepare chart data
  const chartData = data.map((item, index) => ({
    name: item.label,
    value: item.value,
    fill: item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length],
  }));

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <p className="mb-4 text-lg font-semibold text-gray-900">{title}</p>

      <ResponsiveContainer width="100%" height={300}>
        {type === "bar" ? (
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="value" fill="#3b82f6" />
          </BarChart>
        ) : (
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value }) => `${name}: ${value}`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
