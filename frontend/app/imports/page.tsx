"use client";
import { useEffect, useState } from "react";
import { api, getToken } from "../../lib/api";

export default function ImportsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api("/api/imports").then(setHistory).catch(() => {});
  }, [result]);

  async function upload(path: string) {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(path, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
        body: form,
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");
      const data = await res.json();
      if (path.includes("preview")) setPreview(data);
      else { setResult(data); setPreview(null); }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h1>Import Contacts</h1>
      <div className="card" style={{ maxWidth: 640 }}>
        <p className="muted" style={{ marginTop: 0 }}>
          Upload a <b>.xlsx</b> or <b>.csv</b> with columns: first_name, last_name, email, company,
          job_title, website, linkedin, industry
        </p>
        <input
          type="file"
          accept=".xlsx,.csv"
          onChange={(e) => { setFile(e.target.files?.[0] || null); setPreview(null); setResult(null); }}
        />
        <div className="row mt">
          <button className="secondary" disabled={!file || busy} onClick={() => upload("/api/imports/preview")}>
            🔍 Preview
          </button>
          <button disabled={!file || busy || !preview} onClick={() => upload("/api/imports/run")}>
            📥 Import {preview ? `${preview.valid} contacts` : ""}
          </button>
        </div>
        {error && <div className="error">{error}</div>}
      </div>

      {preview && (
        <div className="card mt" style={{ maxWidth: 640 }}>
          <h2 style={{ marginTop: 0 }}>Detected {preview.total.toLocaleString()} rows</h2>
          <p>
            <span className="badge green">Valid: {preview.valid}</span>{" "}
            <span className="badge red">Invalid: {preview.invalid}</span>{" "}
            <span className="badge amber">Duplicates: {preview.duplicates}</span>
          </p>
          {preview.errors?.length > 0 && (
            <details>
              <summary className="muted">Show errors</summary>
              {preview.errors.map((e: any, i: number) => (
                <div key={i} className="muted" style={{ fontSize: 13 }}>Row {e.row}: {e.error}</div>
              ))}
            </details>
          )}
        </div>
      )}

      {result && (
        <div className="card mt" style={{ maxWidth: 640 }}>
          ✅ Imported <b>{result.imported}</b> contacts ({result.invalid} invalid, {result.duplicates} duplicates skipped)
        </div>
      )}

      <h2 className="mt">Import history</h2>
      <table>
        <thead><tr><th>File</th><th>Status</th><th>Total</th><th>Imported</th><th>Invalid</th><th>Duplicates</th></tr></thead>
        <tbody>
          {history.map((j) => (
            <tr key={j.id}>
              <td>{j.filename}</td><td><span className="badge">{j.status}</span></td>
              <td>{j.total}</td><td>{j.imported}</td><td>{j.invalid}</td><td>{j.duplicates}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
