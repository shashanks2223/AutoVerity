import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Layout from "../components/Layout";
import { getImageStatus, getImageFailure } from "../services/api";
import type { JobFailureResponse } from "../services/api";

export default function Processing() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [status, setStatus] = useState<string>("pending");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [failureDetails, setFailureDetails] = useState<JobFailureResponse | null>(null);

  useEffect(() => {
    if (!id) {
      setError("No processing ID provided.");
      setLoading(false);
      return;
    }

    let intervalId: any;

    const checkStatus = async () => {
      try {
        const response = await getImageStatus(id);
        setStatus(response.status);

        if (response.status === "completed") {
          clearInterval(intervalId);
          navigate(`/results/${id}`);
        } else if (response.status === "failed") {
          clearInterval(intervalId);
          fetchFailureDetails();
        }
      } catch (err) {
        console.error("Error checking job status:", err);
        // We do not stop polling immediately on standard network errors,
        // but if it is a 404/terminal API error, we can stop.
        if (err instanceof Error && err.message.includes("not found")) {
          clearInterval(intervalId);
          setError("Processing job not found.");
          setLoading(false);
        }
      }
    };

    const fetchFailureDetails = async () => {
      try {
        const details = await getImageFailure(id);
        setFailureDetails(details);
      } catch (err) {
        console.error("Error fetching failure details:", err);
        setFailureDetails({
          processing_id: id,
          status: "failed",
          failure_reason: "An error occurred during processing, but details could not be retrieved.",
        });
      } finally {
        setLoading(false);
      }
    };

    // First check immediate
    checkStatus().finally(() => {
      setLoading(false);
    });

    // Start polling every 2 seconds
    intervalId = setInterval(checkStatus, 2000);

    return () => {
      clearInterval(intervalId);
    };
  }, [id, navigate]);

  const getStatusMessage = () => {
    switch (status) {
      case "pending":
        return "Waiting in queue...";
      case "processing":
        return "Analyzing image (OCR, Blur, Brightness, Duplicates)...";
      case "completed":
        return "Analysis complete! Redirecting...";
      case "failed":
        return "Analysis failed.";
      default:
        return "Checking status...";
    }
  };

  return (
    <Layout title="Processing Status">
      <div className="mx-auto flex w-full max-w-2xl flex-col justify-center gap-6">
        {loading && !failureDetails ? (
          <div className="flex flex-col items-center justify-center py-12">
            <span className="material-symbols-outlined animate-spin text-[48px] text-[#3B82F6] mb-4">
              sync
            </span>
            <p className="text-on-surface-variant font-medium">Loading status...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-red-200 bg-red-50 p-8 text-center">
            <span className="material-symbols-outlined text-[48px] text-red-600 mb-4">
              error_outline
            </span>
            <h3 className="text-xl font-bold text-red-800 mb-2">Error</h3>
            <p className="text-red-700 mb-6">{error}</p>
            <button
              onClick={() => navigate("/upload")}
              className="rounded bg-[#3B82F6] px-6 py-2 text-white font-semibold"
            >
              Back to Upload
            </button>
          </div>
        ) : failureDetails ? (
          <div className="flex flex-col rounded-xl border border-[#ba1a1a]/20 bg-surface-container-lowest p-6 shadow-sm">
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-[#ba1a1a]/10 text-[#ba1a1a] self-center">
              <span className="material-symbols-outlined text-[32px]">
                gpp_bad
              </span>
            </div>

            <h2 className="text-2xl font-bold text-center text-on-surface mb-2">
              Processing Pipeline Failure
            </h2>
            <p className="text-on-surface-variant text-center text-sm mb-6">
              The image processing job encountered a terminal error.
            </p>

            <div className="space-y-4 border-t border-outline-variant pt-6">
              <div className="flex justify-between items-center text-sm">
                <span className="text-outline">Job ID:</span>
                <span className="font-mono bg-surface-container px-2 py-0.5 rounded text-xs">
                  {id}
                </span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-outline">Status:</span>
                <span className="inline-flex items-center gap-1 rounded bg-red-50 px-2 py-0.5 text-xs font-bold uppercase text-red-700">
                  {status}
                </span>
              </div>
              <div className="flex flex-col gap-2 text-sm">
                <span className="text-outline">Failure Reason:</span>
                <div className="bg-red-50 border border-red-100 rounded-lg p-4 font-mono text-xs text-red-700 whitespace-pre-wrap">
                  {failureDetails.failure_reason}
                </div>
              </div>
            </div>

            <div className="mt-8 flex gap-4">
              <button
                onClick={() => navigate("/upload")}
                className="flex-1 rounded bg-[#3B82F6] py-2.5 font-semibold text-white text-center hover:opacity-90"
              >
                Try Another Upload
              </button>
              <button
                onClick={() => navigate("/history")}
                className="flex-1 rounded border border-outline-variant py-2.5 font-semibold text-on-surface text-center hover:bg-surface-container"
              >
                View History
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-xl border border-outline-variant bg-surface-container-lowest p-8 shadow-sm">
            <div className="relative mb-8 flex h-24 w-24 items-center justify-center">
              <span className="material-symbols-outlined text-[64px] text-[#3B82F6] animate-pulse">
                hourglass_empty
              </span>
              <span className="absolute inset-0 rounded-full border-4 border-[#3B82F6]/20 border-t-[#3B82F6] animate-spin"></span>
            </div>

            <h2 className="text-2xl font-bold text-on-surface mb-2">
              Processing Pipeline Ingestion
            </h2>
            <span className="font-mono text-xs bg-surface-container px-2 py-1 rounded text-outline mb-6">
              ID: {id}
            </span>

            {/* Simulated steps */}
            <div className="w-full space-y-4 mb-8">
              <div className="flex items-center gap-3">
                <span className={`material-symbols-outlined text-[20px] ${status === "pending" ? "text-blue-500 animate-bounce" : "text-green-500 font-bold"}`}>
                  {status === "pending" ? "radio_button_checked" : "check_circle"}
                </span>
                <span className={`text-sm ${status === "pending" ? "font-semibold text-on-surface" : "text-outline"}`}>
                  Job Ingested and Queued
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className={`material-symbols-outlined text-[20px] ${status === "processing" ? "text-blue-500 animate-spin" : status === "pending" ? "text-outline" : "text-green-500 font-bold"}`}>
                  {status === "processing" ? "sync" : status === "pending" ? "radio_button_unchecked" : "check_circle"}
                </span>
                <span className={`text-sm ${status === "processing" ? "font-semibold text-on-surface" : "text-outline"}`}>
                  Executing Image Analysis Suite
                </span>
              </div>
            </div>

            <div className="w-full bg-surface-container rounded-full h-2 mb-4 overflow-hidden">
              <div
                className="bg-[#3B82F6] h-full rounded-full transition-all duration-500 ease-out"
                style={{ width: status === "pending" ? "30%" : "70%" }}
              ></div>
            </div>

            <p className="text-sm font-medium text-on-surface-variant text-center animate-pulse">
              {getStatusMessage()}
            </p>
          </div>
        )}
      </div>
    </Layout>
  );
}
