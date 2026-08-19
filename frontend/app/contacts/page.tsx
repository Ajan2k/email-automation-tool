"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";

export default function ContactsPage() {
  const [data, setData] = useState<any>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [country, setCountry] = useState("");
  const [companySize, setCompanySize] = useState("");

  const load = useCallback(() => {
    const params = new URLSearchParams({ page: String(page), page_size: "25" });
    if (search) params.set("search", search);
    if (status) params.set("status", status);
    if (country) params.set("country", country);
    if (companySize) params.set("company_size", companySize);
    api(`/api/contacts?${params}`).then(setData).catch(() => {});
  }, [page, search, status, country, companySize]);

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
      <div className="row" style={{ marginBottom: 16, flexWrap: "wrap" }}>
        <input
          placeholder="Search name, email, job title, skills…"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          style={{ maxWidth: 300 }}
        />
        <input
          placeholder="Country…"
          value={country}
          onChange={(e) => { setCountry(e.target.value); setPage(1); }}
          style={{ maxWidth: 160 }}
        />
        <select value={companySize} onChange={(e) => { setCompanySize(e.target.value); setPage(1); }} style={{ maxWidth: 170 }}>
          <option value="">All company sizes</option>
          <option value="1001-5000">1001–5000</option>
          <option value="5001-10000">5001–10000</option>
          <option value="10001+">10001+</option>
        </select>
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} style={{ maxWidth: 160 }}>
          <option value="">All statuses</option>
          <option value="ACTIVE">Active</option>
          <option value="UNSUBSCRIBED">Unsubscribed</option>
          <option value="BOUNCED">Bounced</option>
        </select>
      </div>
      <table>
        <thead>
          <tr><th>Name</th><th>Email</th><th>Job title</th><th>Industry</th><th>Country</th><th>Size</th><th>Links</th><th>Status</th></tr>
        </thead>
        <tbody>
          {data?.items.map((c: any) => (
            <tr key={c.id}>
              <td>
                <b>{c.full_name || `${c.first_name} ${c.last_name}`}</b>
                {c.skills && (
                  <div className="muted" style={{ fontSize: 11, maxWidth: 220, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {c.skills.split(";").slice(0, 3).join(" · ")}
                  </div>
                )}
              </td>
              <td>{c.email}{c.phone && <div className="muted" style={{ fontSize: 11 }}>{c.phone}</div>}</td>
              <td>{c.job_title}</td>
              <td>{c.industry}</td>
              <td>{c.country}</td>
              <td className="muted">{c.company_size}</td>
              <td>{c.linkedin && <a href={c.linkedin} target="_blank" rel="noreferrer">in</a>}</td>
              <td><span className={`badge ${c.status === "ACTIVE" || c.status === "active" ? "green" : "red"}`}>{c.status}</span></td>
            </tr>
          ))}
          {data && data.items.length === 0 && (
            <tr><td colSpan={8} className="muted">No contacts yet — import an Excel/CSV file.</td></tr>
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
