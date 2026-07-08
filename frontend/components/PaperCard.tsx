"use client";
import Link from "next/link";
import { FlaskConical, BookOpen, Lightbulb } from "lucide-react";

export interface Paper {
  paper_id: string;
  paper_type: "empirical" | "survey" | "theoretical";
  name: string;
  authors?: string[];
  key_insights?: string;
  architecture?: string;
  date_of_publication?: string;
  relevance_score?: number;
}

const TYPE_CONFIG: Record<
  Paper["paper_type"],
  { label: string; color: string; Icon: React.ElementType }
> = {
  empirical: {
    label: "Empirical",
    color: "bg-purple-500/15 text-purple-300",
    Icon: FlaskConical,
  },
  survey: {
    label: "Survey",
    color: "bg-teal-500/15 text-teal-300",
    Icon: BookOpen,
  },
  theoretical: {
    label: "Theoretical",
    color: "bg-amber-500/15 text-amber-300",
    Icon: Lightbulb,
  },
};

type Props = {
  paper: Paper;
  selectable?: boolean;
  selected?: boolean;
  onSelect?: (id: string) => void;
  relevanceScore?: number;
};

export default function PaperCard({
  paper,
  selectable,
  selected,
  onSelect,
  relevanceScore,
}: Props) {
  const cfg = TYPE_CONFIG[paper.paper_type] ?? TYPE_CONFIG.empirical;

  const inner = (
    <div
      onClick={
        selectable && onSelect ? () => onSelect(paper.paper_id) : undefined
      }
      className={`bg-neutral-900 border rounded-xl p-4 transition-all h-full ${
        selectable ? "cursor-pointer" : ""
      } ${
        selected
          ? "border-purple-500 ring-2 ring-purple-500/20"
          : "border-neutral-800 hover:border-neutral-700"
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded-full flex items-center gap-1 ${cfg.color}`}
        >
          <cfg.Icon size={10} />
          {cfg.label}
        </span>
        {relevanceScore !== undefined ? (
          <span className="text-xs text-neutral-500 shrink-0">
            {Math.round(relevanceScore * 100)}% match
          </span>
        ) : paper.date_of_publication ? (
          <span className="text-xs text-neutral-500 shrink-0">
            {paper.date_of_publication}
          </span>
        ) : null}
      </div>

      <h3 className="text-sm font-medium text-neutral-100 leading-snug mb-1 line-clamp-2">
        {paper.name || "Untitled"}
      </h3>

      {paper.authors && paper.authors.length > 0 && (
        <p className="text-xs text-neutral-500 mb-2 truncate">
          {paper.authors.join(", ")}
        </p>
      )}

      {paper.key_insights && (
        <p className="text-xs text-neutral-400 line-clamp-2">
          {paper.key_insights}
        </p>
      )}

      {paper.architecture && (
        <span className="inline-block mt-2 text-xs bg-neutral-800 text-neutral-300 px-2 py-0.5 rounded-full border border-neutral-700">
          {paper.architecture}
        </span>
      )}
    </div>
  );

  if (selectable) return inner;
  return (
    <Link href={`/papers/${paper.paper_id}`} className="block h-full">
      {inner}
    </Link>
  );
}
