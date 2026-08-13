import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Layout from "../components/Layout";
import { getImageResults } from "../services/api";
import type { JobResultsResponse } from "../services/api";

interface AnalysisCardData {
  title: string;
  icon: string;
  status: "Pass" | "Warn" | "Fail";
  value: string;
  detail: string;
}

export default function Results() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const [results, setResults] = useState<JobResultsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [showShareMessage, setShowShareMessage] = useState(false);

  const processingId = id || "";

  useEffect(() => {
    if (!processingId) {
      setError("No processing ID specified.");
      setLoading(false);
      return;
    }

    const fetchResults = async () => {
      try {
        const response = await getImageResults(processingId);
        if (response.status === "pending" || response.status === "processing") {
          // If status isn't complete/failed yet, redirect back to processing
          navigate(`/processing/${processingId}`);
          return;
        }
        setResults(response);
      } catch (err) {
        console.error("Error loading results:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load analysis results."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [processingId, navigate]);

  const handleExport = () => {
    if (!results) return;

    const blob = new Blob(
      [JSON.stringify(results, null, 2)],
      { type: "application/json" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${processingId}-analysis.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const handleShare = async () => {
    const shareData = {
      title: "AutoVerity Analysis Results",
      text: `Analysis results for job ${processingId}`,
      url: window.location.href,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(window.location.href);
        setShowShareMessage(true);
        setTimeout(() => setShowShareMessage(false), 2000);
      }
    } catch {
      // Sharing cancelled
    }
  };

  const getExtension = (filename: string) => {
    return (filename.split('.').pop() || 'jpg').toLowerCase();
  };

  if (loading) {
    return (
      <Layout title="Analysis Results">
        <div className="flex flex-col items-center justify-center py-12">
          <span className="material-symbols-outlined animate-spin text-[48px] text-[#3B82F6] mb-4">
            sync
          </span>
          <p className="text-on-surface-variant font-medium">Fetching analysis results...</p>
        </div>
      </Layout>
    );
  }

  if (error || !results) {
    return (
      <Layout title="Analysis Results">
        <div className="mx-auto flex w-full max-w-2xl flex-col justify-center gap-6">
          <div className="flex flex-col items-center justify-center rounded-xl border border-red-200 bg-red-50 p-8 text-center">
            <span className="material-symbols-outlined text-[48px] text-red-600 mb-4">
              error_outline
            </span>
            <h3 className="text-xl font-bold text-red-800 mb-2">Error Loading Results</h3>
            <p className="text-red-700 mb-6">{error || "Could not find results data"}</p>
            <button
              onClick={() => navigate("/history")}
              className="rounded bg-[#3B82F6] px-6 py-2 text-white font-semibold"
            >
              Back to History
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  // Construct image URL
  const baseApiUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  const filename = results.image?.filename || "image.jpg";
  const imageUrl = `${baseApiUrl}/uploads/${results.processing_id}.${getExtension(filename)}`;

  const analysis = results.analysis;
  const summary = results.summary;

  // Build analysis cards mapping
  const cards: AnalysisCardData[] = [];
  if (analysis) {
    cards.push({
      title: "Blur Detection",
      icon: "blur_on",
      status: analysis.blur.is_blurry ? "Fail" : "Pass",
      value: analysis.blur.is_blurry ? "Blurry image detected" : "Sharp image (Clear)",
      detail: `${analysis.blur.score.toFixed(2)} (Thresh: ${analysis.blur.threshold.toFixed(2)})`,
    });

    cards.push({
      title: "Brightness Check",
      icon: "light_mode",
      status: analysis.brightness.is_low_light ? "Warn" : "Pass",
      value: analysis.brightness.is_low_light ? "Low-light environment" : "Normal exposure",
      detail: `Avg: ${analysis.brightness.average_brightness.toFixed(1)} (Thresh: ${analysis.brightness.threshold.toFixed(1)})`,
    });

    cards.push({
      title: "License Plate Validation",
      icon: "directions_car",
      status: analysis.vehicle_number.detected_number
        ? (analysis.vehicle_number.format_valid ? "Pass" : "Warn")
        : "Fail",
      value: analysis.vehicle_number.detected_number
        ? `${analysis.vehicle_number.detected_number} ${analysis.vehicle_number.format_valid ? "(Valid Format)" : "(Invalid Format)"}`
        : "No plate text detected",
      detail: analysis.vehicle_number.confidence
        ? `Confidence: ${(analysis.vehicle_number.confidence * 100).toFixed(0)}%`
        : "Confidence: N/A",
    });

    cards.push({
      title: "Image Dimensions",
      icon: "aspect_ratio",
      status: analysis.dimensions.valid ? "Pass" : "Warn",
      value: `${analysis.dimensions.width} x ${analysis.dimensions.height}`,
      detail: analysis.dimensions.valid ? "Aspect Ratio standard" : "Low resolution or invalid aspect",
    });

    cards.push({
      title: "Duplicate Check",
      icon: "content_copy",
      status: analysis.duplicate.is_duplicate ? "Fail" : "Pass",
      value: analysis.duplicate.is_duplicate ? "Duplicate image flagged" : "Unique submission",
      detail: `Similarity: ${(analysis.duplicate.similarity * 100).toFixed(0)}%`,
    });
  }

  // Map summary assessment status
  const assessmentStatus = summary?.overall_status || "warning";
  const assessmentConfidence = summary?.confidence !== undefined ? Math.round(summary.confidence * 100) : 0;
  const issues = summary?.issues || [];

  const getAssessmentStyles = () => {
    switch (assessmentStatus) {
      case "good":
        return {
          label: "Passed",
          color: "text-green-700 bg-green-50 border-green-200",
          icon: "verified",
          iconBg: "bg-green-500",
        };
      case "warning":
        return {
          label: "Warning",
          color: "text-amber-700 bg-amber-50 border-amber-200",
          icon: "warning",
          iconBg: "bg-amber-500",
        };
      case "failed":
      default:
        return {
          label: "Failed",
          color: "text-red-700 bg-red-50 border-red-200",
          icon: "gpp_bad",
          iconBg: "bg-red-500",
        };
    }
  };

  const statusStyle = getAssessmentStyles();

  return (
    <Layout title="Analysis Results">
      <div className="flex flex-col gap-6">
        {/* Sub Header / Toolbar */}
        <div className="flex flex-col gap-4 border-b border-outline-variant pb-4">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="rounded p-1 text-on-surface hover:bg-surface-container hover:text-primary transition-colors"
            >
              <span className="material-symbols-outlined">arrow_back</span>
            </button>
            <span className="rounded bg-surface-container px-2 py-0.5 font-mono text-[10px] font-bold text-outline">
              ID: {processingId}
            </span>
          </div>

          <div className="flex items-start justify-between gap-2 flex-wrap md:flex-nowrap">
            <h1 className="text-2xl font-bold text-on-surface">
              Vehicle Ingestion Report
            </h1>
            <span className="rounded border border-outline-variant bg-surface-container-low px-2 py-1 font-mono text-[10px] text-on-surface-variant truncate">
              {filename}
            </span>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleExport}
              className="flex flex-1 items-center justify-center gap-2 rounded border border-[#E2E8F0] bg-surface-container-lowest px-3 py-2 text-sm font-semibold text-on-surface-variant transition-all hover:bg-surface-container-low"
            >
              <span className="material-symbols-outlined text-[18px]">download</span>
              Export JSON
            </button>

            <button
              type="button"
              onClick={handleShare}
              className="flex flex-1 items-center justify-center gap-2 rounded border border-[#E2E8F0] bg-surface-container-lowest px-3 py-2 text-sm font-semibold text-on-surface-variant transition-all hover:bg-surface-container-low"
            >
              <span className="material-symbols-outlined text-[18px]">share</span>
              Share Report
            </button>
          </div>

          {showShareMessage && (
            <div className="rounded border border-green-200 bg-green-50 p-2 text-center text-sm text-green-700">
              Results URL copied to clipboard.
            </div>
          )}
        </div>
        <div className="mb-6 flex flex-col gap-6">
          {/* Source Image */}
          <section className="relative flex flex-col overflow-hidden rounded-lg border border-[#E2E8F0] bg-surface-container-lowest">
            <div className="flex items-center justify-between border-b border-[#F1F5F9] bg-surface-container px-4 py-3">
              <span className="font-semibold text-on-surface">Source Image</span>
              {results.image?.width && results.image?.height && (
                <span className="font-mono text-xs text-outline">
                  {results.image.width}x{results.image.height}
                </span>
              )}
            </div>

            <div className="relative flex h-[350px] w-full items-center justify-center bg-[#111827]">


              <img
                className="h-full w-full object-contain"
                src={imageUrl}
                alt={filename}
                onError={(e) => {
                  // Fallback if image fails to load
                  (e.target as HTMLImageElement).src =
                    "https://lh3.googleusercontent.com/aida-public/AB6AXuAzkmswJ9w4dRNyT5E3cI1nHR--M1_t3e-iDp0k73dNwB-PpUeVc2e6dSshVpH8QsNLp88jtwdP-2UOtJCEvrX-jBNfUaSFMFkcfOtHlmqTR1zBzYMN_NhnYNJa-fCrs9YOC7ey8rhcET5tJoMJ4g-Rf47fF-wQeSNBF8Bx8VKcg1XBi_jEIXY1JAr7hpHvYyKezEeo0PbNy5qCrNlfgYb1-4wr3oWZq6kVIWUnrsS_a7cVoUtR_m0N";
                }}
              />
            </div>
          </section>

          {/* Overall Assessment */}
          <section className="rounded-lg border border-[#E2E8F0] bg-surface-container-lowest p-6">
            <h2 className="mb-4 text-lg font-semibold text-on-surface">
              Overall Assessment
            </h2>

            <div className={`mb-6 flex items-center gap-4 rounded-lg border p-4 ${statusStyle.color}`}>
              <div className={`flex h-12 w-12 items-center justify-center rounded-full text-white ${statusStyle.iconBg}`}>
                <span className="material-symbols-outlined text-[24px]">
                  {statusStyle.icon}
                </span>
              </div>

              <div className="flex-1">
                <p className="mb-1 text-xs uppercase tracking-wider text-outline font-bold">
                  Pipeline Status
                </p>
                <p className="text-xl font-bold leading-none">
                  {statusStyle.label}
                </p>
              </div>
            </div>

            {/* Confidence */}
            <div className="mb-6 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-on-surface-variant font-medium">
                  Pipeline Confidence Score
                </span>
                <span className="font-mono text-sm font-bold">
                  {assessmentConfidence}%
                </span>
              </div>
              <div className="h-2.5 w-full overflow-hidden rounded-full bg-surface-container">
                <div
                  className={`h-full transition-all duration-1000 ${
                    assessmentStatus === "good"
                      ? "bg-green-500"
                      : assessmentStatus === "warning"
                      ? "bg-amber-500"
                      : "bg-red-500"
                  }`}
                  style={{ width: `${assessmentConfidence}%` }}
                />
              </div>
            </div>

            {/* Issues tags */}
            {issues.length > 0 && (
              <div className="border-t border-[#F1F5F9] pt-4">
                <h4 className="text-sm font-bold text-on-surface mb-2">Identified Issues:</h4>
                <div className="flex flex-wrap gap-2">
                  {issues.map((issue, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center rounded-full bg-amber-50 border border-amber-200 px-3 py-1 text-xs font-semibold text-amber-800"
                    >
                      {issue}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </section>
        </div>

        {/* Analysis Modules */}
        <h3 className="mb-4 border-b border-outline-variant pb-2 text-lg font-semibold text-on-surface">
          Analysis Modules
        </h3>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {cards.map((module) => (
            <AnalysisCard key={module.title} module={module} />
          ))}
        </div>
      </div>
    </Layout>
  );
}

/* ---------------- Analysis Card Component ---------------- */

function AnalysisCard({ module }: { module: AnalysisCardData }) {
  const isPass = module.status === "Pass";
  const isWarn = module.status === "Warn";

  const getStatusBadgeStyles = () => {
    if (isPass) {
      return "bg-green-50 text-green-700 border border-green-200";
    }
    if (isWarn) {
      return "bg-amber-50 text-amber-700 border border-amber-200";
    }
    return "bg-red-50 text-red-700 border border-red-200";
  };

  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-surface-container-lowest p-6 shadow-sm">
      <div className="mb-4 flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-outline">
            {module.icon}
          </span>
          <h4 className="font-semibold text-on-surface">{module.title}</h4>
        </div>

        <span className={`inline-flex items-center rounded px-2 py-0.5 font-mono text-[10px] font-bold uppercase ${getStatusBadgeStyles()}`}>
          {module.status}
        </span>
      </div>

      <div className="space-y-3">
        <p className="font-semibold text-on-surface-variant text-sm">
          {module.value}
        </p>

        <div className="flex items-center justify-between border-t border-[#F1F5F9] pt-3">
          <span className="text-xs text-outline font-medium">Metric Info</span>
          <span className="font-mono text-xs text-on-surface">
            {module.detail}
          </span>
        </div>
      </div>
    </div>
  );
}