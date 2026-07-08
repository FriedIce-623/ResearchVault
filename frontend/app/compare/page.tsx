"use client";
import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import PaperCard, { type Paper } from "@/components/PaperCard";
import { listPapers, comparePapers } from "@/lib/api";
import { GitCompare, Loader, LayoutGrid } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const COLORS = ["#6366f1", "#14b8a6", "#f59e0b", "#ef4444"];

type CompareResult = {
  dimensions: {
    dimension: string;
    papers: {
      paper_id: string;
      name: string;
      value: string;
      numeric_value?: number;
    }[];
  }[];
  summary: string;
  key_differences: string[];
  recommendation: string;
};

export default function ComparePage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [maxWarning, setMaxWarning] = useState(false);

  useEffect(() => {
    listPapers().then(setPapers);
  }, []);

  const toggle = (id: string) => {
    if (selected.includes(id)) {
      setSelected((prev) => prev.filter((x) => x !== id));
      setMaxWarning(false);
    } else if (selected.length >= 4) {
      setMaxWarning(true);
    } else {
      setSelected((prev) => [...prev, id]);
      setMaxWarning(false);
    }
  };

  const run = async (compareAll = false) => {
    if (!compareAll && selected.length < 2) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await comparePapers(
        compareAll ? undefined : selected,
        compareAll,
      );
      setResult(data);
    } finally {
      setLoading(false);
    }
  };

  const chartData =
    result?.dimensions
      .filter((d) => d.papers.some((p) => p.numeric_value != null))
      .map((d) => {
        const row: Record<string, unknown> = { dimension: d.dimension };
        d.papers.forEach((p) => {
          if (p.numeric_value != null)
            row[p.name || p.paper_id] = p.numeric_value;
        });
        return row;
      }) || [];

  const paperNames =
    result?.dimensions[0]?.papers.map((p) => p.name || p.paper_id) || [];
  const manyPapers = (result?.dimensions[0]?.papers.length ?? 0) > 2;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-medium text-neutral-100">
              Compare papers
            </h2>
            <div className="flex items-center gap-3">
              {maxWarning && (
                <span className="text-xs text-amber-400">Maximum 4 papers</span>
              )}
              <span className="text-sm text-neutral-500">
                {selected.length} / 4 selected
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-5">
            {papers.map((p) => (
              <PaperCard
                key={p.paper_id as string}
                paper={p}
                selectable
                selected={selected.includes(p.paper_id as string)}
                onSelect={toggle}
              />
            ))}
          </div>

          <div className="flex gap-3 mb-8">
            <button
              onClick={() => run(false)}
              disabled={selected.length < 2 || loading}
              className="flex items-center gap-2 bg-indigo-600 text-white text-sm px-5 py-2.5 rounded-lg hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {loading ? (
                <Loader size={14} className="animate-spin" />
              ) : (
                <GitCompare size={14} />
              )}
              {loading ? "Comparing..." : `Compare ${selected.length} papers`}
            </button>
            <button
              onClick={() => run(true)}
              disabled={loading || papers.length < 2}
              className="flex items-center gap-2 border border-neutral-700 text-neutral-300 text-sm px-5 py-2.5 rounded-lg hover:bg-neutral-800 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <LayoutGrid size={14} />
              Compare all {papers.length} papers
            </button>
          </div>

          {result && (
            <div className="space-y-5">
              <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
                <h3 className="text-sm font-medium text-neutral-100 mb-2">
                  Summary
                </h3>
                <p className="text-sm text-neutral-300 leading-relaxed">
                  {result.summary}
                </p>
                {result.key_differences?.length > 0 && (
                  <ul className="mt-3 space-y-1">
                    {result.key_differences.map((d, i) => (
                      <li key={i} className="text-sm text-neutral-400 flex gap-2">
                        <span className="text-neutral-600 shrink-0">·</span>
                        {d}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-x-auto">
                <table className="w-full" style={{ tableLayout: "fixed" }}>
                  <thead>
                    <tr className="border-b border-neutral-800">
                      <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wide w-32">
                        Dimension
                      </th>
                      {result.dimensions[0]?.papers.map((p) => (
                        <th
                          key={p.paper_id}
                          className={`text-left px-4 py-3 text-xs font-medium text-neutral-300 ${manyPapers ? "text-[11px]" : ""}`}
                        >
                          {p.name || p.paper_id}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.dimensions.map((dim, i) => (
                      <tr
                        key={i}
                        className="border-b border-neutral-800/60 last:border-0"
                      >
                        <td
                          className={`px-4 py-3 text-neutral-500 capitalize font-medium ${manyPapers ? "text-[11px]" : "text-xs"}`}
                        >
                          {dim.dimension}
                        </td>
                        {dim.papers.map((p) => (
                          <td
                            key={p.paper_id}
                            className={`px-4 py-3 text-neutral-300 leading-relaxed ${manyPapers ? "text-[11px]" : "text-sm"}`}
                          >
                            {p.value || "—"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {chartData.length > 0 && (
                <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
                  <h3 className="text-sm font-medium text-neutral-100 mb-4">
                    Metric comparison
                  </h3>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={chartData}>
                      <XAxis
                        dataKey="dimension"
                        tick={{ fontSize: 12, fill: "#a3a3a3" }}
                        stroke="#404040"
                      />
                      <YAxis tick={{ fontSize: 12, fill: "#a3a3a3" }} stroke="#404040" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#171717",
                          border: "1px solid #404040",
                          borderRadius: 8,
                          fontSize: 12,
                        }}
                        labelStyle={{ color: "#e5e5e5" }}
                        itemStyle={{ color: "#e5e5e5" }}
                      />
                      <Legend wrapperStyle={{ fontSize: 12, color: "#a3a3a3" }} />
                      {paperNames.map((name, i) => (
                        <Bar
                          key={name}
                          dataKey={name}
                          fill={COLORS[i % COLORS.length]}
                          radius={[3, 3, 0, 0]}
                        />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {result.recommendation && (
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
                  <p className="text-sm text-blue-300 leading-relaxed">
                    {result.recommendation}
                  </p>
                </div>
              )}

              <button
                onClick={() => {
                  setResult(null);
                  setSelected([]);
                  window.scrollTo(0, 0);
                }}
                className="text-sm text-neutral-500 hover:text-neutral-300"
              >
                ← Compare different papers
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
