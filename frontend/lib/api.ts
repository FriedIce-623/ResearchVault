const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
console.log("BASE =", BASE);
export async function uploadPaper(file: File, link?: string) {
  const form = new FormData();
  form.append("file", file);
  if (link) form.append("link", link);
  const res = await fetch(`${BASE}/api/ingest/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

/*export async function listPapers(paperType?: string) {
  const params = new URLSearchParams()
  if (paperType) params.set("paper_type", paperType)
  const res = await fetch(`${BASE}/api/papers?${params}`)
  return res.json()
}*/
export async function listPapers(paperType?: string) {
  const params = new URLSearchParams();
  if (paperType) params.set("paper_type", paperType);

  const url = `${BASE}/api/papers?${params}`;
  // console.log("Fetching:", url);

  const res = await fetch(url);

  console.log("Status:", res.status);

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

export async function searchPapers(query: string, paperType?: string) {
  const params = new URLSearchParams({ q: query });
  if (paperType) params.set("paper_type", paperType);
  const res = await fetch(`${BASE}/api/papers/search?${params}`);
  return res.json();
}

export async function getPaper(paperId: string) {
  const res = await fetch(`${BASE}/api/papers/${paperId}`);
  return res.json();
}

export async function deletePaper(paperId: string) {
  await fetch(`${BASE}/api/papers/${paperId}`, { method: "DELETE" });
}

export async function askQuestion(
  question: string,
  sessionId: string,
  paperIds?: string[],
) {
  const res = await fetch(`${BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      session_id: sessionId,
      paper_ids: paperIds,
    }),
  });
  return res.json();
}

export async function comparePapers(
  paperIds?: string[],
  compareAll?: boolean,
  dimensions?: string[],
) {
  const res = await fetch(`${BASE}/api/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      paper_ids: paperIds,
      compare_all: compareAll ?? false,
      dimensions,
    }),
  });
  return res.json();
}

export async function listDatasets() {
  const res = await fetch(`${BASE}/api/papers/datasets/all`);
  return res.json();
}
