"use client";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [editing, setEditing] = useState<any>(null);
  const [preview, setPreview] = useState<any>(null);
  const [error, setError] = useState("");

  const load = () => api("/api/templates").then(setTemplates).catch(() => {});
  useEffect(() => { load(); }, []);

  async function save() {
    setError("");
    try {
      if (editing.id) {
        await api(`/api/templates/${editing.id}`, { method: "PATCH", body: JSON.stringify(editing) });
      } else {
        await api("/api/templates", { method: "POST", body: JSON.stringify(editing) });
      }
      setEditing(null);
      load();
    } catch (e: any) { setError(e.message); }
  }

  async function showPreview(id: number) {
    setPreview(await api(`/api/templates/${id}/preview`, { method: "POST", body: JSON.stringify({}) }));
  }

  return (
    <div>
      <div className="spread">
        <h1>Templates</h1>
        <button onClick={() => setEditing({ name: "", subject: "", body: "" })}>+ New template</button>
      </div>

      {editing && (
        <div className="card" style={{ maxWidth: 720, marginBottom: 20 }}>
          <h2 style={{ marginTop: 0 }}>{editing.id ? "Edit" : "New"} template</h2>
          <label>Name</label>
          <input value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
          <label>Subject — use {"{{first_name}}, {{company_name}}, {{job_title}}, {{industry}}"}</label>
          <input value={editing.subject} onChange={(e) => setEditing({ ...editing, subject: e.target.value })} />
          <label>Body</label>
          <textarea value={editing.body} onChange={(e) => setEditing({ ...editing, body: e.target.value })} />
          <div className="row mt">
            <button onClick={save}>Save</button>
            <button className="secondary" onClick={() => setEditing(null)}>Cancel</button>
          </div>
          {error && <div className="error">{error}</div>}
        </div>
      )}

      {preview && (
        <div className="card" style={{ maxWidth: 720, marginBottom: 20 }}>
          <div className="spread">
            <h2 style={{ margin: 0 }}>Preview (sample contact)</h2>
            <button className="secondary" onClick={() => setPreview(null)}>✕</button>
          </div>
          <p><b>Subject:</b> {preview.subject}</p>
          <div style={{ whiteSpace: "pre-wrap" }}>{preview.body}</div>
        </div>
      )}

      <table>
        <thead><tr><th>Name</th><th>Subject</th><th></th></tr></thead>
        <tbody>
          {templates.map((t) => (
            <tr key={t.id}>
              <td>{t.name}</td>
              <td className="muted">{t.subject}</td>
              <td className="row">
                <button className="secondary" onClick={() => showPreview(t.id)}>Preview</button>
                <button className="secondary" onClick={() => setEditing(t)}>Edit</button>
              </td>
            </tr>
          ))}
          {templates.length === 0 && <tr><td colSpan={3} className="muted">No templates yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
