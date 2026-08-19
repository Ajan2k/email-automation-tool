"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { setToken } from "../../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function getErrorMessage(res: Response, fallback: string): Promise<string> {
    try {
      const data = await res.json();
      return data.detail || fallback;
    } catch {
      return `${fallback} (${res.status} ${res.statusText || "Server Error"})`;
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "register") {
        const res = await fetch("/api/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, full_name: name }),
        });
        if (!res.ok) throw new Error(await getErrorMessage(res, "Registration failed"));
      }
      const form = new URLSearchParams({ username: email, password });
      const res = await fetch("/api/auth/login", { method: "POST", body: form });
      if (!res.ok) throw new Error(await getErrorMessage(res, "Login failed"));
      const data = await res.json();
      setToken(data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 380, margin: "10vh auto" }}>
      <h1>✉️ AI Email Platform</h1>
      <div className="card">
        <form onSubmit={submit}>
          {mode === "register" && (
            <>
              <label>Full name</label>
              <input value={name} onChange={(e) => setName(e.target.value)} />
            </>
          )}
          <label>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
          <div className="mt">
            <button disabled={busy} style={{ width: "100%" }}>
              {mode === "login" ? "Sign in" : "Create account"}
            </button>
          </div>
          {error && <div className="error">{error}</div>}
        </form>
        <p className="muted mt" style={{ fontSize: 13 }}>
          {mode === "login" ? (
            <>
              No account?{" "}
              <a href="#" onClick={() => setMode("register")}>
                Register
              </a>
            </>
          ) : (
            <>
              Have an account?{" "}
              <a href="#" onClick={() => setMode("login")}>
                Sign in
              </a>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
