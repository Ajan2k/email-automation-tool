"use client";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "../../../lib/api";

export default function ConversationDetailPage() {
  const { id } = useParams();
  const [conversation, setConversation] = useState<any>(null);
  const [drafts, setDrafts] = useState<any[]>([]);
  const [editBody, setEditBody] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const conv = await api(`/api/conversations/${id}`);
    setConversation(conv);
    const all = await api(`/api/ai-replies`);
    const mine = all.filter((d: any) => d.conversation_id === Number(id));
    setDrafts(mine);
    const pending = mine.find((d: any) => d.status.toLowerCase() === "draft");
    if (pending) setEditBody(pending.edited_body || pending.draft_body);
  }, [id]);

  useEffect(() => { load().catch(() => {}); }, [load]);

  const pending = drafts.find((d) => d.status.toLowerCase() === "draft");

  async function act(verb: string) {
    if (!pending) return;
    setBusy(true);
    setError("");
    try {
      if (verb === "approve") {
        await api(`/api/ai-replies/${pending.id}`, { method: "PATCH", body: JSON.stringify({ edited_body: editBody }) });
        await api(`/api/ai-replies/${pending.id}/approve`, { method: "POST" });
      } else {
        await api(`/api/ai-replies/${pending.id}/${verb}`, { method: "POST" });
      }
      await load();
    } catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  }

  if (!conversation) return <p className="muted">Loading…</p>;

  return (
    <div style={{ maxWidth: 780 }}>
      <h1>{conversation.subject || "Conversation"}</h1>
      <p>
        <span className="badge">{conversation.status}</span>{" "}
        <span className="badge">{conversation.classification}</span>
      </p>

      {conversation.messages.map((m: any) => (
        <div key={m.id} className={`msg ${m.direction.toLowerCase()}`}>
          <div className="meta">
            {m.direction.toLowerCase() === "outbound" ? "You" : m.from_email} · {new Date(m.created_at).toLocaleString()}
          </div>
          <div dangerouslySetInnerHTML={{ __html: m.body }} />
        </div>
      ))}

      {pending && (
        <div className="card mt" style={{ borderColor: "var(--amber)" }}>
          <h2 style={{ marginTop: 0 }}>🤖 AI Suggested Reply</h2>
          <p className="muted" style={{ fontSize: 13 }}>
            Classification: <b>{pending.classification}</b> — {pending.reason}
            {pending.requires_human_attention === "true" && (
              <span className="badge red" style={{ marginLeft: 8 }}>⚠ Needs human attention</span>
            )}
          </p>
          <textarea value={editBody} onChange={(e) => setEditBody(e.target.value)} style={{ minHeight: 180 }} />
          <div className="row mt">
            <button className="success" disabled={busy} onClick={() => act("approve")}>✓ Approve & Send</button>
            <button className="secondary" disabled={busy} onClick={() => act("regenerate")}>↻ Regenerate</button>
            <button className="danger" disabled={busy} onClick={() => act("reject")}>✕ Reject</button>
          </div>
          <p className="muted mt" style={{ fontSize: 12 }}>
            Nothing is sent without your approval. Approving queues the reply through the worker.
          </p>
          {error && <div className="error">{error}</div>}
        </div>
      )}
    </div>
  );
}
