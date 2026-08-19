"use client";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";

export default function AIRepliesPage() {
  const [drafts, setDrafts] = useState<any[]>([]);
  const [status, setStatus] = useState("draft");

  useEffect(() => {
    api(`/api/ai-replies${status ? `?status=${status}` : ""}`).then(setDrafts).catch(() => {});
  }, [status]);

  const badge = (s: string) => {
    const v = s.toLowerCase();
    if (v === "approved" || v === "sent") return "green";
    if (v === "rejected") return "red";
    return "amber";
  };

  return (
    <div>
      <div className="spread">
        <h1>AI Replies</h1>
        <select value={status} onChange={(e) => setStatus(e.target.value)} style={{ maxWidth: 200 }}>
          <option value="draft">Pending review</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="sent">Sent</option>
          <option value="">All</option>
        </select>
      </div>
      <table>
        <thead><tr><th>Classification</th><th>Draft</th><th>Status</th><th>Created</th><th></th></tr></thead>
        <tbody>
          {drafts.map((d) => (
            <tr key={d.id}>
              <td>
                <span className="badge">{d.classification}</span>
                {d.requires_human_attention === "true" && <span className="badge red" style={{ marginLeft: 6 }}>⚠</span>}
              </td>
              <td className="muted" style={{ maxWidth: 420 }}>{(d.edited_body || d.draft_body).slice(0, 120)}…</td>
              <td><span className={`badge ${badge(d.status)}`}>{d.status}</span></td>
              <td className="muted">{new Date(d.created_at).toLocaleString()}</td>
              <td><a href={`/conversations/${d.conversation_id}`}>Review →</a></td>
            </tr>
          ))}
          {drafts.length === 0 && <tr><td colSpan={5} className="muted">Nothing here.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
