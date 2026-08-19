"use client";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/analytics/dashboard").then(setStats).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (!stats) return <p className="muted">Loading…</p>;

  const cards = [
    ["Contacts", stats.total_contacts],
    ["Campaigns", stats.total_campaigns],
    ["Emails sent", stats.emails_sent],
    ["Delivered", stats.emails_delivered],
    ["Opened", stats.emails_opened],
    ["Clicked", stats.emails_clicked],
    ["Replied", stats.emails_replied],
    ["Bounced", stats.emails_bounced],
  ];
  const rates = [
    ["Delivery rate", stats.delivery_rate],
    ["Open rate", stats.open_rate],
    ["Click rate", stats.click_rate],
    ["Reply rate", stats.reply_rate],
    ["Bounce rate", stats.bounce_rate],
  ];

  return (
    <div>
      <div className="spread">
        <h1>Dashboard</h1>
        {stats.pending_ai_reviews > 0 && (
          <a href="/ai-replies" className="badge amber">
            🔴 {stats.pending_ai_reviews} replies need review
          </a>
        )}
      </div>
      <div className="grid">
        {cards.map(([label, value]) => (
          <div className="card" key={label as string}>
            <div className="label">{label}</div>
            <div className="value">{(value as number).toLocaleString()}</div>
          </div>
        ))}
      </div>
      <h2 className="mt">Rates</h2>
      <div className="grid">
        {rates.map(([label, value]) => (
          <div className="card" key={label as string}>
            <div className="label">{label}</div>
            <div className="value">{value}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}
