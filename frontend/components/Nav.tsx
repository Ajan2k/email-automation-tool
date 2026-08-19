"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  ["/dashboard", "📊 Dashboard"],
  ["/contacts", "👤 Contacts"],
  ["/imports", "📥 Import"],
  ["/templates", "📝 Templates"],
  ["/campaigns", "🚀 Campaigns"],
  ["/conversations", "💬 Conversations"],
  ["/ai-replies", "🤖 AI Replies"],
];

export default function Nav() {
  const pathname = usePathname();
  if (pathname === "/login" || pathname === "/") return null;
  return (
    <nav className="sidebar">
      <div className="brand">✉️ AI Email Platform</div>
      {links.map(([href, label]) => (
        <Link key={href} href={href} className={pathname.startsWith(href) ? "active" : ""}>
          {label}
        </Link>
      ))}
      <a
        href="/login"
        onClick={() => typeof window !== "undefined" && localStorage.removeItem("auth_token")}
      >
        🚪 Logout
      </a>
    </nav>
  );
}
