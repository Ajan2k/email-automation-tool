"use client";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<any[]>([]);
  const [status, setStatus] = useState("");

  useEffect(() => {
    const params = status ? `?status=${status}` : "";
    api(`/api/conversations${params}`).then(setConversations).catch(() => {});
  }, [status]);

  return (
    <div>
      <div className="spread">
        <h1>Conversations</h1>
        <select value={status} onChange={(e) => setStatus(e.target.value)} style={{ maxWidth: 200 }}>
          <option value="">All</option>
          <option value="NEEDS_REVIEW">Needs review</option>
          <option value="OPEN">Open</option>
          <option value="CLOSED">Closed</option>
        </select>
      </div>
      <table>
        <thead><tr><th>Subject</th><th>Status</th><th>Classification</th><th>Last message</th></tr></thead>
        <tbody>
          {conversations.map((c) => (
            <tr key={c.id}>
              <td><a href={`/conversations/${c.id}`}>{c.subject || "(no subject)"}</a></td>
              <td><span className={`badge ${c.status.toLowerCase() === "needs_review" ? "amber" : ""}`}>{c.status}</span></td>
              <td><span className="badge">{c.classification}</span></td>
              <td className="muted">{c.last_message_at ? new Date(c.last_message_at).toLocaleString() : "—"}</td>
            </tr>
          ))}
          {conversations.length === 0 && (
            <tr><td colSpan={4} className="muted">No conversations yet — replies to your campaigns will appear here.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
