"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../../lib/api";

export default function CreateCampaignPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<any[]>([]);
  const [contacts, setContacts] = useState<any[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [form, setForm] = useState({
    name: "", description: "", template_id: 0,
    daily_limit: 500, rate_per_minute: 20, scheduled_at: "",
  });
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/templates").then(setTemplates).catch(() => {});
    api("/api/contacts?page_size=200").then((d) => setContacts(d.items)).catch(() => {});
  }, []);

  function toggle(id: number) {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  }

  async function submit() {
    setError("");
    try {
      const payload: any = {
        ...form,
        template_id: Number(form.template_id),
        contact_ids: Array.from(selected),
        scheduled_at: form.scheduled_at ? new Date(form.scheduled_at).toISOString() : null,
      };
      await api("/api/campaigns", { method: "POST", body: JSON.stringify(payload) });
      router.push("/campaigns");
    } catch (e: any) { setError(e.message); }
  }

  return (
    <div style={{ maxWidth: 720 }}>
      <h1>New Campaign</h1>
      <div className="card">
        <label>Campaign name</label>
        <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <label>Description</label>
        <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <label>Template</label>
        <select value={form.template_id} onChange={(e) => setForm({ ...form, template_id: Number(e.target.value) })}>
          <option value={0}>— select template —</option>
          {templates.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <div className="row">
          <div style={{ flex: 1 }}>
            <label>Daily limit</label>
            <input type="number" value={form.daily_limit} onChange={(e) => setForm({ ...form, daily_limit: Number(e.target.value) })} />
          </div>
          <div style={{ flex: 1 }}>
            <label>Rate (emails/min)</label>
            <input type="number" value={form.rate_per_minute} onChange={(e) => setForm({ ...form, rate_per_minute: Number(e.target.value) })} />
          </div>
          <div style={{ flex: 1 }}>
            <label>Schedule (optional)</label>
            <input type="datetime-local" value={form.scheduled_at} onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })} />
          </div>
        </div>

        <label>Contacts ({selected.size} selected)</label>
        <div style={{ maxHeight: 260, overflow: "auto", border: "1px solid var(--border)", borderRadius: 8 }}>
          <table>
            <tbody>
              {contacts.map((c) => (
                <tr key={c.id} onClick={() => toggle(c.id)} style={{ cursor: "pointer" }}>
                  <td style={{ width: 30 }}><input type="checkbox" checked={selected.has(c.id)} readOnly /></td>
                  <td>{c.first_name} {c.last_name}</td>
                  <td className="muted">{c.email}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt">
          <button disabled={!form.name || !form.template_id || selected.size === 0} onClick={submit}>
            Create campaign
          </button>
        </div>
        {error && <div className="error">{error}</div>}
      </div>
    </div>
  );
}
