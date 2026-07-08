"use client";
import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { uploadPaper } from "@/lib/api";
import { Upload, FileText, CheckCircle, Loader } from "lucide-react";

type Stage =
  | "idle"
  | "uploading"
  | "detecting"
  | "extracting"
  | "saving"
  | "done"
  | "error";
interface UploadResult {
  paper_id: string;
  paper_type: "empirical" | "survey" | "theoretical";
  data: {
    name: string;
    authors?: string[];
    key_insights?: string;
  };
}

const STAGES: Stage[] = ["uploading", "detecting", "extracting", "saving"];
const STAGE_LABELS: Record<Stage, string> = {
  idle: "",
  uploading: "PDF uploaded",
  detecting: "Detecting paper type",
  extracting: "Extracting fields with Claude",
  saving: "Saving to database",
  done: "Done",
  error: "Something went wrong",
};

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [link, setLink] = useState("");
  const [stage, setStage] = useState<Stage>("idle");
  const [dragging, setDragging] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const router = useRouter();

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f?.type === "application/pdf") setFile(f);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    try {
      setStage("uploading");
      await new Promise((r) => setTimeout(r, 400));
      setStage("detecting");
      await new Promise((r) => setTimeout(r, 500));
      setStage("extracting");
      const data = await uploadPaper(file, link || undefined);
      setStage("saving");
      await new Promise((r) => setTimeout(r, 300));
      setStage("done");
      setResult(data);
    } catch {
      setStage("error");
    }
  };

  const stageIndex = STAGES.indexOf(stage);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-md mx-auto">
          <h2 className="text-lg font-medium text-neutral-100 mb-6">
            Upload a paper
          </h2>

          {stage === "done" && result ? (
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle size={16} className="text-green-500" />
                <span className="text-sm font-medium text-neutral-100">
                  Paper extracted
                </span>
                <span
                  className={`ml-auto text-xs px-2 py-0.5 rounded-full capitalize font-medium ${
                    result.paper_type === "empirical"
                      ? "bg-purple-500/15 text-purple-300"
                      : result.paper_type === "survey"
                        ? "bg-teal-500/15 text-teal-300"
                        : "bg-amber-500/15 text-amber-300"
                  }`}
                >
                  {result.paper_type as string}
                </span>
              </div>
              <h3 className="text-base font-medium text-neutral-100 mb-1">
                {((result.data as Record<string, unknown>)?.name as string) ||
                  "Untitled"}
              </h3>
              <p className="text-xs text-neutral-500 mb-3">
                {(
                  (result.data as Record<string, unknown>)?.authors as string[]
                )?.join(", ")}
              </p>
              {Boolean(
                (result.data as Record<string, unknown>)?.key_insights
              ) && (
                <p className="text-xs text-neutral-400 mb-4">
                  {
                    (result.data as Record<string, unknown>)
                      .key_insights as string
                  }
                </p>
              )}
              <div className="flex gap-2">
                <button
                  onClick={() => router.push(`/papers/${result.paper_id}`)}
                  className="flex-1 text-sm bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-500"
                >
                  View paper
                </button>
                <button
                  onClick={() => {
                    setFile(null);
                    setStage("idle");
                    setResult(null);
                    setLink("");
                  }}
                  className="flex-1 text-sm border border-neutral-700 text-neutral-300 py-2 rounded-lg hover:bg-neutral-800"
                >
                  Upload another
                </button>
              </div>
            </div>
          ) : (
            <>
              <div
                onDrop={onDrop}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onClick={() => document.getElementById("file-input")?.click()}
                className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors mb-4 ${
                  dragging
                    ? "border-blue-500 bg-blue-500/10"
                    : "border-neutral-700 hover:border-neutral-600 bg-neutral-900"
                }`}
              >
                <input
                  id="file-input"
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
                {file ? (
                  <div className="flex items-center justify-center gap-2">
                    <FileText size={16} className="text-neutral-400" />
                    <span className="text-sm text-neutral-300">{file.name}</span>
                  </div>
                ) : (
                  <>
                    <Upload size={20} className="mx-auto mb-2 text-neutral-600" />
                    <p className="text-sm text-neutral-500">
                      Drop a PDF here or click to browse
                    </p>
                  </>
                )}
              </div>

              <input
                className="w-full text-sm border border-neutral-700 rounded-lg px-3 py-2 mb-4 focus:outline-none focus:border-neutral-500 bg-neutral-900 text-neutral-100"
                placeholder="Paper URL or DOI (optional)"
                value={link}
                onChange={(e) => setLink(e.target.value)}
              />

              {stage !== "idle" && stage !== "error" && (
                <div className="mb-4 space-y-2">
                  {STAGES.map((s, i) => (
                    <div key={s} className="flex items-center gap-2.5">
                      <div
                        className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 text-xs ${
                          i < stageIndex
                            ? "bg-green-500/15 text-green-400"
                            : i === stageIndex
                              ? "bg-purple-500/15 text-purple-300"
                              : "bg-neutral-800 border border-neutral-700"
                        }`}
                      >
                        {i < stageIndex ? (
                          <CheckCircle size={12} />
                        ) : i === stageIndex ? (
                          <Loader size={12} className="animate-spin" />
                        ) : null}
                      </div>
                      <span
                        className={`text-sm ${
                          i < stageIndex
                            ? "text-neutral-100"
                            : i === stageIndex
                              ? "text-purple-300 font-medium"
                              : "text-neutral-500"
                        }`}
                      >
                        {STAGE_LABELS[s]}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {stage === "error" && (
                <p className="text-sm text-red-400 mb-4">
                  Upload failed. Is the backend running?
                </p>
              )}

              <button
                onClick={handleUpload}
                disabled={!file || (stage !== "idle" && stage !== "error")}
                className="w-full bg-indigo-600 text-white text-sm py-2.5 rounded-lg hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {stage !== "idle" && stage !== "error"
                  ? "Processing..."
                  : "Analyse paper"}
              </button>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
