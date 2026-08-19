"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";

export default function ContactsPage() {
  const [data, setData] = useState<any>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");

  const load = useCallback(() => {
    const params = new URLSearchParams({ page: String(page), page_size: "25" });
    if (search) params.set("search", search);
    if (status) params.set("status", status);
    api(`/api/contacts?${params}`).then(setData).catch(() => {});
  }, [page, search, status]);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  return (
    <div>
      <div className="spread">
        <h1>Contacts {data ? `(${data.total.toLocaleString()})` : ""}</h1>
        <a className="btn" href="/imports">📥 Import contacts</a>
      </div>
      <div className="row" style={{ marginBottom: 16 }}>
        <input
          placeholder="Search name, email, job title…"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          style={{ maxWidth: 320 }}
        />
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} style={{ maxWidth: 180 }}>
          <option value="">All statuses</option>
          <option value="ACTIVE">Active</option>
          <option value="UNSUBSCRIBED">Unsubscribed</option>
          <option value="BOUNCED">Bounced</option>
        </select>
      </div>
      <table>
        <thead>
          <tr><th>Name</th><th>Email</th><th>Job title</th><th>Industry</th><th>Status</th></tr>
        </thead>
        <tbody>
          {data?.items.map((c: any) => (
            <tr key={c.id}>
              <td>{c.first_name} {c.last_name}</td>
              <td>{c.email}</td>
              <td>{c.job_title}</td>
              <td>{c.industry}</td>
              <td><span className={`badge ${c.status === "ACTIVE" || c.status === "active" ? "green" : "red"}`}>{c.status}</span></td>
            </tr>
          ))}
          {data && data.items.length === 0 && (
            <tr><td colSpan={5} className="muted">No contacts yet — import an Excel/CSV file.</td></tr>
          )}
        </tbody>
      </table>
      {data && data.total > data.page_size && (
        <div className="row mt">
          <button className="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>← Prev</button>
          <span className="muted">Page {page} of {Math.ceil(data.total / data.page_size)}</span>
          <button className="secondary" disabled={page >= Math.ceil(data.total / data.page_size)} onClick={() => setPage(page + 1)}>Next →</button>
        </div>
      )}
    </div>
  );
}
