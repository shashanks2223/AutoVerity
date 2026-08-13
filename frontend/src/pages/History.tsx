import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import { getImagesHistory } from "../services/api";
import type { JobHistoryItem } from "../services/api";

export default function History() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [jobs, setJobs] = useState<JobHistoryItem[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalJobs, setTotalJobs] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const limit = 10; // Items per page

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await getImagesHistory(page, limit, statusFilter || undefined, search.trim() || undefined);
        setJobs(response.items);
        setTotalPages(response.pages);
        setTotalJobs(response.total);
      } catch (err) {
        console.error("Failed to load history:", err);
        setError("Could not load processing history from server.");
      } finally {
        setLoading(false);
      }
    };

    // Debounce search input a bit so we don't spam requests on every keystroke
    const handler = setTimeout(() => {
      fetchHistory();
    }, 300);

    return () => {
      clearTimeout(handler);
    };
  }, [page, statusFilter, search]);

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
    setPage(1); // Reset to first page
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setPage(1); // Reset to first page
  };

  const formatTime = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      // Format as "08:14 AM" or "Yest, 14:20"
      const now = new Date();
      const isToday = date.toDateString() === now.toDateString();
      
      const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      if (isToday) {
        return timeStr;
      }
      
      const isYesterday = new Date(now.setDate(now.getDate() - 1)).toDateString() === date.toDateString();
      if (isYesterday) {
        return `Yest, ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
      }
      
      return `${date.toLocaleDateString([], { month: 'short', day: 'numeric' })}, ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    } catch {
      return "Unknown";
    }
  };

  const getConfidenceScore = (job: JobHistoryItem) => {
    if (job.status !== "completed") return 0;
    return job.summary ? Math.round(job.summary.confidence * 100) : 0;
  };

  const getVehicleLabel = (job: JobHistoryItem) => {
    if (job.status === "pending") return "Queued...";
    if (job.status === "processing") return "Scanning...";
    if (job.status === "failed") return "N/A";
    
    if (job.summary) {
      if (job.summary.overall_status === "good") return "Passed";
      return job.summary.overall_status.toUpperCase();
    }
    return "-";
  };

  // Maps backend lower case status to UI-friendly name
  const getUiFriendlyStatus = (status: string) => {
    switch (status) {
      case "pending":
        return "Pending";
      case "processing":
        return "Processing";
      case "completed":
        return "Completed";
      case "failed":
        return "Failed";
      default:
        return status;
    }
  };

  return (
    <Layout title="History">
      <div className="flex flex-col gap-md">
        {/* Page Header */}
        <header className="flex flex-col gap-4 border-b border-outline-variant bg-surface-container-lowest pb-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-on-surface">
              Processing History
            </h2>
            <p className="mt-1 text-sm text-on-surface-variant">
              Manage and review image analysis jobs ({totalJobs} total).
            </p>
          </div>

          {/* Upload Link */}
          <Link
            to="/upload"
            className="flex items-center gap-1 rounded bg-[#3B82F6] px-4 py-2 text-white font-semibold transition-opacity hover:opacity-90 text-sm"
          >
            <span className="material-symbols-outlined text-[18px]">add</span>
            New Upload
          </Link>
        </div>

        <div className="flex gap-2">
          {/* Search */}
          <div className="relative flex-1">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-on-surface-variant">
              search
            </span>
            <input
              value={search}
              onChange={handleSearchChange}
              className="w-full rounded border border-outline-variant bg-surface py-2 pl-10 pr-4 text-sm outline-none focus:border-secondary"
              placeholder="Search filename or ID..."
              type="text"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={handleStatusChange}
            className="rounded border border-outline-variant bg-surface px-4 py-2 text-sm outline-none font-medium focus:border-secondary"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </header>

      {/* Jobs */}
      <div className="flex flex-col overflow-hidden bg-background">
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <span className="material-symbols-outlined animate-spin text-4xl text-[#3B82F6]">
                sync
              </span>
            </div>
          ) : error ? (
            <div className="flex h-64 items-center justify-center">
              <div className="text-center text-red-600">
                <span className="material-symbols-outlined text-4xl mb-2">error</span>
                <p className="font-semibold">{error}</p>
              </div>
            </div>
          ) : jobs.length === 0 ? (
            <div className="flex h-64 items-center justify-center">
              <div className="text-center">
                <span className="material-symbols-outlined mb-2 text-4xl text-on-surface-variant">
                  search_off
                </span>
                <p className="font-semibold text-on-surface">No jobs found</p>
                <p className="text-sm text-on-surface-variant">
                  Try a different search or filter criteria.
                </p>
              </div>
            </div>
          ) : (
            jobs.map((job) => {
              // Terminal redirect path
              const path = job.status === "completed"
                ? `/results/${job.processing_id}`
                : `/processing/${job.processing_id}`;

              const conf = getConfidenceScore(job);

              return (
                <Link
                  key={job.processing_id}
                  to={path}
                  className="block rounded-lg border border-outline-variant bg-surface-container-lowest p-4 shadow-sm transition-colors hover:bg-surface-container-low"
                >
                  {/* Job Header */}
                  <div className="mb-3 flex items-start justify-between">
                    <div>
                      <div className="mb-1 font-mono text-[10px] text-on-surface-variant">
                        ID: {job.processing_id}
                      </div>

                      <div className="flex items-center gap-1.5 font-semibold text-on-surface text-sm">
                        <span className="material-symbols-outlined text-[16px] text-on-surface-variant">
                          image
                        </span>
                        {job.filename}
                      </div>
                    </div>

                    <span className="text-[11px] text-on-surface-variant font-mono">
                      {formatTime(job.created_at)}
                    </span>
                  </div>

                  {/* Status + Vehicle */}
                  <div className="mb-3 flex gap-8">
                    <div className="flex flex-col">
                      <span className="text-[9px] font-bold uppercase tracking-wider text-outline">
                        Status
                      </span>
                      <StatusBadge status={getUiFriendlyStatus(job.status)} />
                    </div>

                    <div className="flex flex-col">
                      <span className="text-[9px] font-bold uppercase tracking-wider text-outline">
                        Pipeline Score
                      </span>
                      <span className="mt-0.5 text-xs font-semibold">
                        {getVehicleLabel(job)}
                      </span>
                    </div>
                  </div>

                  {/* Confidence / Progress */}
                  <div className="mt-3 flex items-center justify-between border-t border-surface-container-high pt-3">
                    <div className="flex flex-1 items-center gap-2">
                      <span className="text-[9px] font-bold text-outline w-12">
                        {job.status === "processing" ? "PROG" : "CONF"}
                      </span>

                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-container-high max-w-[200px]">
                        <div
                          className={`h-full transition-all ${getProgressColor(getUiFriendlyStatus(job.status))}`}
                          style={{
                            width: `${job.status === "processing" ? 50 : job.status === "pending" ? 10 : conf}%`,
                          }}
                        />
                      </div>

                      <span className="text-[10px] font-mono text-on-surface-variant font-bold">
                        {job.status === "processing" ? "50%" : job.status === "pending" ? "10%" : `${conf}%`}
                      </span>
                    </div>
                  </div>
                </Link>
              );
            })
          )}
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && !loading && (
          <footer className="flex flex-shrink-0 items-center justify-between border-t border-outline-variant bg-surface-container-lowest px-6 py-4">
            <span className="text-xs text-on-surface-variant">
              Page {page} of {totalPages}
            </span>

            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="rounded border border-outline-variant px-3 py-1 text-xs font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-container"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="rounded border border-outline-variant px-3 py-1 text-xs font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-container"
              >
                Next
              </button>
            </div>
          </footer>
        )}
      </div>
     </div>
    </Layout>
  );
}

/* ---------------- Status Badge ---------------- */

function StatusBadge({ status }: { status: string }) {
  if (status === "Completed") {
    return (
      <span className="mt-0.5 inline-flex w-fit items-center gap-1 rounded bg-green-50 px-1.5 py-0.5 text-[9px] font-bold uppercase text-green-700 border border-green-200">
        <span className="material-symbols-outlined text-[10px]">check_circle</span>
        Completed
      </span>
    );
  }

  if (status === "Processing") {
    return (
      <span className="mt-0.5 inline-flex w-fit items-center gap-1 rounded bg-blue-50 px-1.5 py-0.5 text-[9px] font-bold uppercase text-blue-700 border border-blue-200">
        <span className="material-symbols-outlined animate-spin text-[10px]">sync</span>
        Processing
      </span>
    );
  }

  if (status === "Pending") {
    return (
      <span className="mt-0.5 inline-flex w-fit items-center gap-1 rounded bg-amber-50 px-1.5 py-0.5 text-[9px] font-bold uppercase text-amber-700 border border-amber-200">
        <span className="material-symbols-outlined text-[10px]">hourglass_empty</span>
        Pending
      </span>
    );
  }

  return (
    <span className="mt-0.5 inline-flex w-fit items-center gap-1 rounded bg-red-50 px-1.5 py-0.5 text-[9px] font-bold uppercase text-red-700 border border-red-200">
      <span className="material-symbols-outlined text-[10px]">error</span>
      Failed
    </span>
  );
}

/* ---------------- Progress Color ---------------- */

function getProgressColor(status: string) {
  switch (status) {
    case "Completed":
      return "bg-green-500";
    case "Processing":
      return "bg-blue-500";
    case "Pending":
      return "bg-amber-400";
    case "Failed":
    default:
      return "bg-red-500";
  }
}