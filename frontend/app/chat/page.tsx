"use client";
import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { askQuestion, listPapers } from "@/lib/api";
import { Send, X } from "lucide-react";

type Message = {
  role: "user" | "assistant";
  content: string;
  citations?: { paper_id: string; section: string }[];
};

function ChatContent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [papers, setPapers] = useState<Record<string, unknown>[]>([]);
  const searchParams = useSearchParams();
  const [selectedIds, setSelectedIds] = useState<string[]>(() => {
    const paperId = searchParams.get("paper");
    return paperId ? [paperId] : [];
  });
  const sessionId = useRef(crypto.randomUUID());
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listPapers().then(setPapers);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const toggle = (id: string) =>
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );

  const send = async () => {
    if (!input.trim() || loading) return;
    const q = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", content: q }]);
    setLoading(true);
    try {
      const data = await askQuestion(
        q,
        sessionId.current,
        selectedIds.length ? selectedIds : undefined,
      );
      setMessages((m) => [
        ...m,
        { role: "assistant", content: data.answer, citations: data.citations },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: "Something went wrong. Is the backend running?",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 overflow-hidden" style={{ height: "100vh" }}>
        <aside className="w-52 border-r border-neutral-800 bg-neutral-900 p-4 overflow-y-auto shrink-0">
          <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
            Filter by paper
          </p>
          <p className="text-xs text-neutral-600 mb-3">
            None selected = search all
          </p>
          {papers.map((p) => {
            const pid = p.paper_id as string;
            const sel = selectedIds.includes(pid);
            return (
              <button
                key={pid}
                onClick={() => toggle(pid)}
                className={`w-full text-left text-xs px-2 py-1.5 rounded-lg mb-1 flex items-center gap-1.5 transition-colors ${
                  sel
                    ? "bg-indigo-600 text-white"
                    : "text-neutral-400 hover:bg-neutral-800"
                }`}
              >
                {sel && <X size={10} />}
                <span className="truncate">{p.name as string}</span>
              </button>
            );
          })}
        </aside>

        <div className="flex flex-col flex-1 overflow-hidden">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-20">
                <p className="text-sm text-neutral-500">
                  Ask anything about your papers
                </p>
                <p className="text-xs text-neutral-600 mt-1">
                  Select papers on the left to focus the search
                </p>
              </div>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-lg ${
                    m.role === "user"
                      ? "bg-indigo-600 text-white text-sm px-4 py-2.5 rounded-2xl rounded-br-sm"
                      : "text-sm text-neutral-300"
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">
                    {m.content}
                  </p>
                  {m.citations && m.citations.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {m.citations.map((c, j) => (
                        <span
                          key={j}
                          className="text-xs bg-blue-500/15 text-blue-300 px-2 py-0.5 rounded-full"
                        >
                          {c.section}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <span className="text-sm text-neutral-500 animate-pulse">
                  Thinking...
                </span>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="border-t border-neutral-800 p-4 bg-neutral-900">
            <div className="flex gap-2 max-w-2xl mx-auto">
              <input
                className="flex-1 text-sm border border-neutral-700 rounded-xl px-4 py-2.5 bg-neutral-900 text-neutral-100 focus:outline-none focus:border-neutral-500"
                placeholder="Ask about your papers..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
              />
              <button
                onClick={send}
                disabled={!input.trim() || loading}
                className="bg-indigo-600 text-white p-2.5 rounded-xl hover:bg-indigo-500 disabled:opacity-40"
              >
                <Send size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense>
      <ChatContent />
    </Suspense>
  );
}
