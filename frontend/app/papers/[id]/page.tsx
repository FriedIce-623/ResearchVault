"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import { getPaper } from "@/lib/api";
import { ArrowLeft, ExternalLink, Code } from "lucide-react";

function Field({ label, value }: { label: string; value: unknown }) {
  if (!value || (Array.isArray(value) && value.length === 0)) return null;
  return (
    <div className="py-2.5 border-b border-neutral-800/60 last:border-0">
      <dt className="text-xs text-neutral-500 mb-0.5">{label}</dt>
      <dd className="text-sm text-neutral-300 leading-relaxed">
        {Array.isArray(value)
          ? value.join(", ")
          : typeof value === "object"
            ? Object.entries(value as Record<string, string>)
                .map(([k, v]) => `${k}: ${v}`)
                .join(" · ")
            : String(value)}
      </dd>
    </div>
  );
}

export default function PaperDetailPage() {
  const { id } = useParams();
  const [paper, setPaper] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    if (id) getPaper(id as string).then(setPaper);
  }, [id]);

  if (!paper)
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 p-8">
          <p className="text-sm text-neutral-500">Loading...</p>
        </main>
      </div>
    );

  const type = paper.paper_type as string;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-300 mb-6"
          >
            <ArrowLeft size={14} /> Library
          </Link>
          <div className="flex items-start gap-3 mb-4">
            <div className="flex-1">
              <h2 className="text-xl font-medium text-neutral-100 leading-snug mb-1">
                {paper.name as string}
              </h2>
              <p className="text-sm text-neutral-500">
                {(paper.authors as string[])?.join(", ")}
              </p>
            </div>
            <span
              className={`text-xs font-medium px-2.5 py-1 rounded-full capitalize shrink-0 ${
                type === "empirical"
                  ? "bg-purple-500/15 text-purple-300"
                  : type === "survey"
                    ? "bg-teal-500/15 text-teal-300"
                    : "bg-amber-500/15 text-amber-300"
              }`}
            >
              {type}
            </span>
          </div>

          <div className="flex gap-2 mb-8 flex-wrap">
            {Boolean(paper.doi) && (
              <a
                href={paper.doi as string}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs border border-neutral-700 text-neutral-400 px-3 py-1.5 rounded-lg hover:bg-neutral-800"
              >
                <ExternalLink size={11} /> DOI / link
              </a>
            )}
            {Boolean(paper.code_link) && (
              <a
                href={paper.code_link as string}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs border border-neutral-700 text-neutral-400 px-3 py-1.5 rounded-lg hover:bg-neutral-800"
              >
                <Code size={11} /> Code
              </a>
            )}
            <Link
              href={`/chat?paper=${paper.paper_id}`}
              className="inline-flex items-center gap-1.5 text-xs bg-indigo-600 text-white px-3 py-1.5 rounded-lg hover:bg-indigo-500"
            >
              Chat about this paper
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
              <h3 className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-3">
                Overview
              </h3>
              <dl>
                <Field label="Published" value={paper.date_of_publication} />
                <Field label="Key insights" value={paper.key_insights} />
                <Field label="Limitations" value={paper.limitations} />
              </dl>
            </div>

            {type === "empirical" && (
              <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
                <h3 className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-3">
                  Technical
                </h3>
                <dl>
                  <Field label="Architecture" value={paper.architecture} />
                  <Field label="Key techniques" value={paper.key_techniques} />
                  <Field label="Preprocessing" value={paper.preprocessing} />
                  <Field
                    label="Training strategy"
                    value={paper.training_strategy}
                  />
                </dl>
              </div>
            )}

            {type === "survey" && (
              <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
                <h3 className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-3">
                  Survey details
                </h3>
                <dl>
                  <Field
                    label="Time period"
                    value={paper.time_period_covered}
                  />
                  <Field label="Research gaps" value={paper.research_gaps} />
                  <Field
                    label="Papers surveyed"
                    value={paper.papers_surveyed}
                  />
                </dl>
              </div>
            )}

            {type === "theoretical" && (
              <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
                <h3 className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-3">
                  Theory
                </h3>
                <dl>
                  <Field label="Propositions" value={paper.propositions} />
                  <Field label="Assumptions" value={paper.assumptions} />
                  <Field label="Applicability" value={paper.applicability} />
                </dl>
              </div>
            )}

            {Boolean(paper.metrics_used || paper.results) && (
              <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
                <h3 className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-3">
                  Metrics & results
                </h3>
                <dl>
                  <Field label="Metrics used" value={paper.metrics_used} />
                  <Field label="Results" value={paper.results} />
                </dl>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
