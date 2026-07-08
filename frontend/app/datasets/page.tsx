"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { listDatasets } from "@/lib/api";
import { Database, ExternalLink } from "lucide-react";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listDatasets()
      .then(setDatasets)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-medium text-neutral-100">Datasets</h2>
            <span className="text-sm text-neutral-500">
              {datasets.length} datasets
            </span>
          </div>
          {loading ? (
            <p className="text-sm text-neutral-500">Loading...</p>
          ) : datasets.length === 0 ? (
            <p className="text-sm text-neutral-500">
              No datasets yet. Upload papers that reference datasets.
            </p>
          ) : (
            <div className="space-y-3">
              {datasets.map((d) => (
                <div
                  key={d._id as string}
                  className="bg-neutral-900 border border-neutral-800 rounded-xl p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2.5">
                      <Database
                        size={14}
                        className="text-neutral-500 mt-0.5 shrink-0"
                      />
                      <div>
                        <h3 className="text-sm font-medium text-neutral-100">
                          {d.dataset_name as string}
                        </h3>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {Boolean(d.task) && (
                            <span className="text-xs text-neutral-500">
                              {d.task as string}
                            </span>
                          )}
                          {Boolean(d.modality) && (
                            <span className="text-xs text-neutral-500">
                              {d.modality as string}
                            </span>
                          )}
                          {Boolean(d.samples) && (
                            <span className="text-xs text-neutral-500">
                              {(d.samples as number).toLocaleString()} samples
                            </span>
                          )}
                          {Boolean(d.classes) && (
                            <span className="text-xs text-neutral-500">
                              {d.classes as number} classes
                            </span>
                          )}
                          {Boolean(d.support) && (
                            <span className="text-xs text-neutral-500">
                              {d.support as string}
                            </span>
                          )}
                          <span
                            className={`text-xs px-1.5 py-0.5 rounded-full ${
                              d.public
                                ? "bg-green-500/15 text-green-400"
                                : "bg-neutral-800 text-neutral-400"
                            }`}
                          >
                            {d.public ? "public" : "private"}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      {Array.isArray(d.paper_ids) && (
                        <span className="text-xs text-neutral-500">
                          {(d.paper_ids as unknown[]).length} paper
                          {(d.paper_ids as unknown[]).length !== 1 ? "s" : ""}
                        </span>
                      )}
                      {Boolean(d.link) && (
                        <a
                          href={d.link as string}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-neutral-500 hover:text-neutral-300 flex items-center gap-1"
                        >
                          <ExternalLink size={11} /> Link
                        </a>
                      )}
                    </div>
                  </div>
                  {Boolean(d.key_insights) && (
                    <p className="text-xs text-neutral-400 mt-2 ml-6 leading-relaxed">
                      {d.key_insights as string}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
