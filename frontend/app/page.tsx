"use client";
import { useEffect, useState, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import PaperCard, { type Paper } from "@/components/PaperCard";
import { listPapers, searchPapers } from "@/lib/api";
import { Search } from "lucide-react";

export default function LibraryPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState("");
  const [search, setSearch] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const load = useCallback(async (q: string, type: string) => {
    setLoading(true);
    try {
      const data =
        q.trim().length > 2
          ? await searchPapers(q.trim(), type || undefined)
          : await listPapers(type || undefined);
      setPapers(data);
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => load(search, typeFilter), 300);
    return () => clearTimeout(t);
  }, [search, typeFilter, load]);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-medium text-neutral-100">Paper library</h2>
            <span className="text-sm text-neutral-500">
              {papers.length} papers
            </span>
          </div>

          <div className="flex gap-3 mb-6">
            <div className="relative flex-1 max-w-sm">
              <Search
                size={14}
                className="absolute left-3 top-2.5 text-neutral-500"
              />
              <input
                className="w-full pl-8 pr-3 py-2 text-sm border border-neutral-700 rounded-lg bg-neutral-900 text-neutral-100 focus:outline-none focus:border-neutral-500"
                placeholder="Search papers..."
                value={search}
                onChange={(e) => {
                  const v = e.target.value;
                  setSearch(v);
                  if (v.trim().length > 2) setIsSearching(true);
                }}
              />
            </div>
            <select
              className="text-sm border border-neutral-700 rounded-lg px-3 py-2 bg-neutral-900 text-neutral-100 focus:outline-none"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="">All types</option>
              <option value="empirical">Empirical</option>
              <option value="survey">Survey</option>
              <option value="theoretical">Theoretical</option>
            </select>
          </div>

          {loading ? (
            <p className="text-sm text-neutral-500">
              {isSearching ? "Searching..." : "Loading..."}
            </p>
          ) : papers.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-sm text-neutral-500 mb-2">
                {search ? "No papers matched your search" : "No papers yet"}
              </p>
              {!search && (
                <a
                  href="/upload"
                  className="text-sm text-indigo-400 hover:underline"
                >
                  Upload your first paper →
                </a>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {papers.map((p) => (
                <PaperCard
                  key={p.paper_id}
                  paper={p}
                  relevanceScore={p.relevance_score}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
