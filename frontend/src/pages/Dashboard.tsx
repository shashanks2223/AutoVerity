import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import { getImagesHistory } from "../services/api";
import type { JobHistoryItem } from "../services/api";

export default function Dashboard() {
  const navigate = useNavigate();

  const [recentJobs, setRecentJobs] = useState<JobHistoryItem[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    processing: 0,
    pending: 0,
    failed: 0,
    successRate: "100.0",
    successPercent: 100,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDashboardData = async () => {
      setLoading(true);
      setError("");
      try {
        // Query recent jobs and overall total
        const recentRes = await getImagesHistory(1, 5);
        const totalCount = recentRes.total;

        // Query pending jobs count
        const pendingRes = await getImagesHistory(1, 1, "pending");
        const pendingCount = pendingRes.total;

        // Query processing jobs count
        const processingRes = await getImagesHistory(1, 1, "processing");
        const processingCount = processingRes.total;

        // Query failed jobs count
        const failedRes = await getImagesHistory(1, 1, "failed");
        const failedCount = failedRes.total;

        const activeCount = pendingCount + processingCount;
        const completedCount = Math.max(0, totalCount - activeCount - failedCount);

        const totalTerminal = completedCount + failedCount;
        const successRateVal = totalTerminal > 0
          ? ((completedCount / totalTerminal) * 100).toFixed(1)
          : "100.0";
        const successPercentVal = totalTerminal > 0
          ? Math.round((completedCount / totalTerminal) * 100)
          : 100;

        setRecentJobs(recentRes.items);
        setStats({
          total: totalCount,
          active: activeCount,
          processing: processingCount,
          pending: pendingCount,
          failed: failedCount,
          successRate: successRateVal,
          successPercent: successPercentVal,
        });
      } catch (err) {
        console.error("Error loading dashboard metrics:", err);
        setError("Failed to load dashboard statistics.");
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const formatTime = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      
      if (diffMins < 1) return "Just now";
      if (diffMins < 60) return `${diffMins}m ago`;
      
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      
      return date.toLocaleDateString([], { month: "short", day: "numeric" });
    } catch {
      return "Unknown";
    }
  };

  const getJobColor = (status: string) => {
    switch (status) {
      case "completed":
        return "green";
      case "processing":
        return "blue";
      case "pending":
        return "yellow";
      case "failed":
      default:
        return "red";
    }
  };

  const getJobStatusLabel = (status: string) => {
    switch (status) {
      case "completed":
        return "Completed";
      case "processing":
        return "Processing";
      case "pending":
        return "Pending";
      case "failed":
      default:
        return "Failed";
    }
  };

  return (
    <Layout title="Dashboard">
      <div className="mx-auto flex w-full flex-col gap-md">
          {/* Heading */}
          <div className="mb-sm flex flex-col gap-xs">
            <h1 className="text-headline-lg font-semibold text-on-surface">
              Pipeline Overview
            </h1>
            <p className="text-body-md text-on-surface-variant">
              Real-time metrics for media processing throughput.
            </p>
          </div>

          {error && (
            <div className="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Metrics */}
          <div className="grid grid-cols-1 gap-md md:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="Total Registered"
              value={loading ? "..." : stats.total.toLocaleString()}
              footer="All uploaded pipeline jobs"
              success
              icon="trending_up"
            />

            <MetricCard
              title="Active Jobs"
              value={loading ? "..." : stats.active.toLocaleString()}
              footer={loading ? "..." : `${stats.processing} processing • ${stats.pending} pending`}
            />

            <MetricCard
              title="Success Rate"
              value={loading ? "..." : `${stats.successRate}%`}
              progress={loading ? 100 : stats.successPercent}
            />

            <MetricCard
              title="Recent Issues"
              value={loading ? "..." : stats.failed.toLocaleString()}
              footer="Failed pipeline attempts"
              error={stats.failed > 0}
              icon="error_outline"
            />
          </div>

          {/* Recent Jobs */}
          <div className="mt-sm flex flex-1 flex-col rounded border border-[#E2E8F0] bg-surface-container-lowest">
            <div className="flex items-center justify-between border-b border-[#F1F5F9] p-md">
              <h2 className="text-headline-sm font-semibold text-on-surface">
                Recent Processing Jobs
              </h2>
              <Link to="/history" className="text-body-sm text-secondary font-semibold hover:underline">
                View all
              </Link>
            </div>

            <div className="flex flex-col">
              {loading ? (
                <div className="flex py-12 justify-center items-center">
                  <span className="material-symbols-outlined animate-spin text-3xl text-[#3B82F6]">
                    sync
                  </span>
                </div>
              ) : recentJobs.length === 0 ? (
                <div className="py-12 text-center text-on-surface-variant text-sm">
                  No jobs found. Upload a vehicle image to get started.
                </div>
              ) : (
                recentJobs.map((job) => {
                  const jobColor = getJobColor(job.status);
                  const statusLabel = getJobStatusLabel(job.status);
                  const path = job.status === "completed"
                    ? `/results/${job.processing_id}`
                    : `/processing/${job.processing_id}`;

                  const vehicleLabel = job.status === "completed" && job.summary
                    ? (job.summary.overall_status === "good" ? "Passed" : job.summary.overall_status.toUpperCase())
                    : job.status === "failed" ? "Failed" : "Scanning...";

                  const confidenceStr = job.status === "completed" && job.summary
                    ? `${Math.round(job.summary.confidence * 100)}%`
                    : "-";

                  return (
                    <div
                      key={job.processing_id}
                      onClick={() => navigate(path)}
                      className="flex cursor-pointer flex-col gap-xs border-b border-[#F1F5F9] p-md transition-colors hover:bg-surface-container-highest"
                    >
                      <div className="mb-1 flex items-center justify-between">
                        <span className="font-mono text-xs font-semibold text-outline">
                          ID: {job.processing_id}
                        </span>

                        <StatusBadge
                          status={statusLabel}
                          color={jobColor}
                        />
                      </div>

                      <div className="truncate text-body-md font-semibold text-on-surface">
                        {job.filename}
                      </div>

                      <div className="mt-2 flex items-center justify-between">
                        <div className="flex gap-md text-body-sm text-on-surface-variant font-medium">
                          <span>Status: {vehicleLabel}</span>
                          <span>Confidence: {confidenceStr}</span>
                        </div>

                        <span className="text-body-sm text-on-surface-variant font-mono">
                          {formatTime(job.created_at)}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
      </div>
    </Layout>
  );
}

/* ---------------- Metric Card Component ---------------- */

interface MetricCardProps {
  title: string;
  value: string;
  footer?: string;
  success?: boolean;
  error?: boolean;
  icon?: string;
  progress?: number;
}

function MetricCard({
  title,
  value,
  footer,
  success,
  error,
  icon,
  progress,
}: MetricCardProps) {
  return (
    <div className="flex flex-col rounded border border-[#E2E8F0] bg-surface-container-lowest p-md transition-shadow hover:shadow-sm">
      <span className="text-label-caps uppercase text-[10px] tracking-wider font-bold text-outline">
        {title}
      </span>

      <div className="mb-xs text-[32px] font-bold leading-10 text-on-surface">
        {value}
      </div>

      {progress !== undefined ? (
        <div className="mt-2 h-1.5 w-full rounded-full bg-surface-container-highest">
          <div
            className="h-1.5 rounded-full bg-[#009668] transition-all duration-1000"
            style={{ width: `${progress}%` }}
          />
        </div>
      ) : footer ? (
        <div
          className={`mt-1 flex items-center gap-xs text-body-sm font-medium ${
            success
              ? "text-[#009668]"
              : error
                ? "text-error"
                : "text-on-surface-variant"
          }`}
        >
          {icon && (
            <span
              className="material-symbols-outlined"
              style={{ fontSize: "14px" }}
            >
              {icon}
            </span>
          )}
          <span>{footer}</span>
        </div>
      ) : null}
    </div>
  );
}

/* ---------------- Status Badge Component ---------------- */

function StatusBadge({
  status,
  color,
}: {
  status: string;
  color: string;
}) {
  const getBadgeStyle = () => {
    switch (color) {
      case "blue":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "green":
        return "bg-green-50 text-green-700 border-green-200";
      case "yellow":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "red":
      default:
        return "bg-red-50 text-red-700 border-red-200";
    }
  };

  return (
    <span className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[9px] font-bold uppercase ${getBadgeStyle()}`}>
      {status === "Processing" && (
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-blue-500" />
      )}
      {status}
    </span>
  );
}