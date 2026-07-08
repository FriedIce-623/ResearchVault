"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Upload,
  MessageCircle,
  GitCompare,
  Database,
} from "lucide-react";

const nav = [
  { href: "/", label: "Library", icon: BookOpen },
  { href: "/upload", label: "Upload paper", icon: Upload },
  { href: "/chat", label: "Chat", icon: MessageCircle },
  { href: "/compare", label: "Compare", icon: GitCompare },
  { href: "/datasets", label: "Datasets", icon: Database },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="w-56 min-h-screen bg-neutral-900 border-r border-neutral-800 flex flex-col py-6 px-3 shrink-0">
      <div className="px-3 mb-8">
        <h1 className="text-sm font-semibold text-neutral-100">ResearchVault</h1>
        <p className="text-xs text-neutral-500 mt-0.5">AI paper analyser</p>
      </div>
      <nav className="flex flex-col gap-0.5">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
              path === href
                ? "bg-neutral-800 text-neutral-100 font-medium"
                : "text-neutral-400 hover:text-neutral-100 hover:bg-neutral-800/60"
            }`}
          >
            <Icon size={15} />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
