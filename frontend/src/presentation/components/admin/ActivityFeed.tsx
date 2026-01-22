/**
 * Activity Feed component for recent system events
 */

import { useEffect, useState } from "react";
import { CheckCircle, AlertCircle, Clock, Activity } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { apiClient } from "../../../infrastructure/api/apiClient";

interface Activity {
  id: string;
  type: "tool_run" | "conversation" | "agent_action";
  description: string;
  timestamp: string;
  status: "success" | "pending" | "error";
}

interface ActivityFeedProps {
  isLoading?: boolean;
}

export default function ActivityFeed({ isLoading = false }: ActivityFeedProps) {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [feedLoading, setFeedLoading] = useState(isLoading);

  useEffect(() => {
    const loadActivities = async () => {
      try {
        setFeedLoading(true);
        const [toolRuns, conversations] = await Promise.all([
          apiClient.listToolRuns().catch(() => []),
          apiClient.listConversations().catch(() => []),
        ]);

        const newActivities: Activity[] = [];

        // Add recent tool runs
        (toolRuns as any[]).slice(0, 5).forEach((run: any) => {
          let status: "success" | "pending" | "error" = "pending";
          if (run.status === "executed") status = "success";
          if (run.status === "rejected" || run.status === "failed")
            status = "error";

          newActivities.push({
            id: `toolrun-${run.id}`,
            type: "tool_run",
            description: `Tool run: ${run.tool_id}`,
            timestamp: run.updated_at || run.created_at,
            status,
          });
        });

        // Add recent conversations
        (conversations as any[]).slice(0, 3).forEach((conv: any) => {
          newActivities.push({
            id: `conv-${conv.id}`,
            type: "conversation",
            description: `New conversation: ${conv.title}`,
            timestamp: conv.created_at,
            status: "success",
          });
        });

        // Sort by timestamp (newest first)
        newActivities.sort(
          (a, b) =>
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
        );

        setActivities(newActivities.slice(0, 8));
        setFeedLoading(false);
      } catch (error) {
        console.error("Failed to load activities:", error);
        setFeedLoading(false);
      }
    };

    loadActivities();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success":
        return <CheckCircle size={18} className="text-green-500" />;
      case "error":
        return <AlertCircle size={18} className="text-red-500" />;
      case "pending":
        return <Clock size={18} className="text-yellow-500" />;
      default:
        return <Activity size={18} className="text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "success":
        return "bg-green-50 border-green-200";
      case "error":
        return "bg-red-50 border-red-200";
      case "pending":
        return "bg-yellow-50 border-yellow-200";
      default:
        return "bg-gray-50 border-gray-200";
    }
  };

  if (feedLoading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <p className="mb-4 text-lg font-semibold text-gray-900">
          Recent Activity
        </p>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-gray-100 animate-pulse rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <p className="mb-4 text-lg font-semibold text-gray-900">
          Recent Activity
        </p>
        <div className="flex h-40 items-center justify-center text-gray-500">
          No recent activity
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <p className="mb-4 text-lg font-semibold text-gray-900">
        Recent Activity
      </p>

      <div className="space-y-3">
        {activities.map((activity) => (
          <div
            key={activity.id}
            className={`flex items-center gap-4 rounded-lg border p-4 ${getStatusColor(activity.status)}`}
          >
            <div className="flex-shrink-0">
              {getStatusIcon(activity.status)}
            </div>

            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-medium text-gray-900">
                {activity.description}
              </p>
              <p className="text-xs text-gray-500">
                {formatDistanceToNow(new Date(activity.timestamp), {
                  addSuffix: true,
                })}
              </p>
            </div>

            <div className="text-xs font-semibold text-gray-500 uppercase">
              {activity.type.replace("_", " ")}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
