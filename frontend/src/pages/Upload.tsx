import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import { uploadImage } from "../services/api";

interface SelectedFile {
  file: File;
  name: string;
  size: string;
}

export default function Upload() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<SelectedFile | null>(null);
  const [processingId, setProcessingId] = useState<string>("");
  const [isSuccess, setIsSuccess] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");

  const handleSingleFile = (selectedFiles: FileList | null) => {
    if (!selectedFiles || selectedFiles.length === 0) return;

    const selectedFile = selectedFiles[0];
    if (!selectedFile.type.startsWith("image/")) {
      setError("Unsupported file format. Please select an image.");
      return;
    }

    setFile({
      file: selectedFile,
      name: selectedFile.name,
      size: `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB`,
    });
    setError("");
  };

  const handleFileInput = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    handleSingleFile(event.target.files);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    handleSingleFile(event.dataTransfer.files);
  };

  const removeFile = () => {
    setFile(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError("");

    try {
      const data = await uploadImage(file.file);
      console.log("Upload response:", data);
      setProcessingId(data.processing_id);
      setFile(null);
      setIsSuccess(true);

      // Auto-navigate to processing page after 1.5 seconds
      setTimeout(() => {
        navigate(`/processing/${data.processing_id}`);
      }, 1500);

    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while uploading."
      );
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Layout title="Image Upload">
      <div className="mx-auto flex w-full max-w-2xl flex-col gap-6">
        <header>
          <h1 className="mb-1 text-3xl font-bold text-primary">
            Vehicle Image Upload
          </h1>
          <p className="text-on-surface-variant">
            Upload a vehicle image for pipeline ingestion and validation.
          </p>
        </header>

        {!isSuccess ? (
          <div className="flex flex-col gap-6">
            {/* Upload Area */}
            <div
              onDragOver={(event) => event.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className="flex min-h-[250px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-outline-variant bg-surface-container-lowest p-6 transition-colors hover:bg-surface"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileInput}
                className="hidden"
              />

              <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-container text-on-surface-variant">
                <span className="material-symbols-outlined text-[32px]">
                  upload_file
                </span>
              </div>

              <h3 className="mb-1 text-center text-xl font-semibold">
                Drag and drop image here
              </h3>
              <p className="mb-6 text-sm text-on-surface-variant">
                or click to browse
              </p>

              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation();
                  fileInputRef.current?.click();
                }}
                className="rounded bg-[#3B82F6] px-6 py-2 text-white"
              >
                Select File
              </button>
            </div>

            {/* Staged File */}
            <div className="rounded-xl border border-outline-variant bg-surface-container-lowest">
              <div className="flex items-center justify-between rounded-t-xl border-b border-surface bg-[#F8FAFC] p-4">
                <h3 className="font-semibold">Staged File</h3>
                <span className="rounded bg-surface-container px-2 py-1 text-[10px] font-bold text-on-surface-variant">
                  {file ? "1 FILE" : "0 FILES"}
                </span>
              </div>

              <div className="flex max-h-[300px] flex-col gap-2 overflow-y-auto p-2">
                {!file ? (
                  <div className="py-12 text-center">
                    <p className="text-sm text-on-surface-variant">
                      No file staged.
                    </p>
                  </div>
                ) : (
                  <div className="flex items-center justify-between rounded border border-surface p-3">
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="material-symbols-outlined text-on-surface-variant">
                        image
                      </span>
                      <div className="min-w-0">
                        <span className="block truncate text-sm">
                          {file.name}
                        </span>
                        <span className="text-[10px] text-on-surface-variant">
                          {file.size}
                        </span>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={removeFile}
                      className="p-1 text-on-surface-variant hover:text-error"
                    >
                      <span className="material-symbols-outlined text-[16px]">
                        close
                      </span>
                    </button>
                  </div>
                )}
              </div>

              <div className="border-t border-surface p-4">
                <div className="mb-4 flex items-center justify-between">
                  <span className="text-sm text-on-surface-variant">
                    Total Size:
                  </span>
                  <span className="font-mono text-sm">
                    {file ? file.size : "0.00 MB"}
                  </span>
                </div>

                {error && (
                  <div className="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    {error}
                  </div>
                )}

                <button
                  type="button"
                  disabled={!file || isUploading}
                  onClick={handleUpload}
                  className="flex w-full items-center justify-center gap-2 rounded bg-[#3B82F6] py-2 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isUploading ? (
                    <>
                      <span className="material-symbols-outlined animate-spin">
                        progress_activity
                      </span>
                      Uploading...
                    </>
                  ) : (
                    "Begin Upload"
                  )}
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Success */
          <div className="flex min-h-[300px] flex-col items-center justify-center rounded-xl border border-outline-variant bg-surface-container-lowest p-6">
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full border border-green-200 bg-green-50 text-green-600">
              <span className="material-symbols-outlined text-[32px]">
                check_circle
              </span>
            </div>

            <h3 className="mb-2 text-xl font-semibold">Upload Accepted</h3>
            <p className="mb-4 text-sm text-on-surface-variant text-center">
              Your image has been queued for analysis. Redirecting to processing status page...
            </p>

            <div className="mb-6 rounded border border-outline-variant bg-surface px-4 py-2">
              <span className="font-mono text-sm">
                ID: {processingId}
              </span>
            </div>

            <div className="flex w-full max-w-[280px] flex-col gap-4">
              <button
                type="button"
                onClick={() => navigate(`/processing/${processingId}`)}
                className="rounded bg-[#3B82F6] px-4 py-2 text-white"
              >
                View Status Now
              </button>

              <button
                type="button"
                onClick={() => setIsSuccess(false)}
                className="rounded border border-outline-variant px-4 py-2"
              >
                Upload Another
              </button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}