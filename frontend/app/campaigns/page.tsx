"use client";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [stats, setStats] = useState<Record<number, any>>({});
  const [error, setError] = useState("");

  const load = () =>
    api("/api/campaigns").then(async (list) => {
      setCampaigns(list);
      const s: Record<number, any> = {};
      for (const c of list) s[c.id] = await api(`/api/campaigns/${c.id}/stats`).catch(() => null);
      setStats(s);
    }).catch(() => {});

  useEffect(() => { load(); }, []);

  async function action(id: number, verb: string) {
    setError("");
    try { await api(`/api/campaigns/${id}/${verb}`, { method: "POST" }); load(); }
    catch (e: any) { setError(e.message); }
  }

  const badge = (s: string) => {
    const v = s.toLowerCase();
    if (v === "running") return "green";
    if (v === "paused" || v === "scheduled") return "amber";
    if (v === "cancelled") return "red";
    return "";
  };

  return (
    <div>
      <div className="spread">
        <h1>Campaigns</h1>
        <a className="btn" href="/campaigns/create">+ New campaign</a>
      </div>
      {error && <div className="error">{error}</div>}
      <table>
        <thead>
          <tr><th>Name</th><th>Status</th><th>Contacts</th><th>Sent</th><th>Opened</th><th>Replied</th><th>Bounced</th><th></th></tr>
        </thead>
        <tbody>
          {campaigns.map((c) => {
            const s = stats[c.id];
            return (
              <tr key={c.id}>
                <td><b>{c.name}</b><div className="muted" style={{ fontSize: 12 }}>{c.description}</div></td>
                <td><span className={`badge ${badge(c.status)}`}>{c.status}</span></td>
                <td>{s?.total_contacts ?? "…"}</td>
                <td>{s?.sent ?? "…"}</td>
                <td>{s?.opened ?? "…"}</td>
                <td>{s?.replied ?? "…"}</td>
                <td>{s?.bounced ?? "…"}</td>
                <td className="row">
                  {["draft", "scheduled", "paused"].includes(c.status.toLowerCase()) && (
                    <button className="success" onClick={() => action(c.id, "launch")}>▶ Launch</button>
                  )}
                  {c.status.toLowerCase() === "running" && (
                    <button className="secondary" onClick={() => action(c.id, "pause")}>⏸ Pause</button>
                  )}
                </td>
              </tr>
            );
          })}
          {campaigns.length === 0 && <tr><td colSpan={8} className="muted">No campaigns yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
