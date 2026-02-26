import { useEffect, useState } from "react";
import "./App.css";

export default function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);

  async function loadHistory() {
    const res = await fetch("/api/history?limit=20");
    if (!res.ok) throw new Error(`History failed: ${res.status}`);
    const data = await res.json();
    setHistory(data);
  }

  useEffect(() => {
    loadHistory().catch((err) => setError(String(err.message || err)));
  }, []);

  async function onExtract() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch("/api/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      const body = await res.json().catch(() => ({}));

      if (!res.ok)
        throw new Error(body.detail || `Extract failed: ${res.status}`);
      setResult(body);
      await loadHistory();
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  }

  async function onClearHistory() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/history", { method: "DELETE" });
      if (!res.ok) throw new Error(`Clear failed: ${res.status}`);
      await loadHistory();
      setResult(null);
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{ maxWidth: 950, margin: "40px auto", fontFamily: "system-ui" }}
    >
      <h1>Lead Parser</h1>

      <label style={{ display: "block", marginBottom: 8 }}>
        Paste a lead message:
      </label>

      <textarea
        rows={8}
        style={{ width: "100%", padding: 10 }}
        placeholder='Example: "Hi, I’m Sam from Acme. Email: sam@acme.com. Need a demo next week."'
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <div style={{ marginTop: 12, display: "flex", gap: 12 }}>
        <button onClick={onExtract} disabled={loading || !text.trim()}>
          {loading ? "Working..." : "Extract"}
        </button>
        <button onClick={onClearHistory} disabled={loading}>
          Clear History
        </button>
        <button
          onClick={() => {
            setText("");
            setResult(null);
            setError("");
          }}
          disabled={loading}
        >
          Clear Input
        </button>
      </div>

      {error && (
        <div style={{ marginTop: 16, color: "crimson" }}>Error: {error}</div>
      )}

      {result && (
        <div style={{ marginTop: 18 }}>
          <h2>Result</h2>
          <pre style={{ background: "#111", color: "#0f0", padding: 12 }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}

      <div style={{ marginTop: 26 }}>
        <h2>History (latest 20)</h2>
        <ul style={{ paddingLeft: 18 }}>
          {history.map((h) => (
            <li key={h.id} style={{ marginBottom: 14 }}>
              <div>
                <strong>#{h.id}</strong> [{h.status}]{" "}
                <small>{h.created_at}</small>
              </div>

              <div style={{ whiteSpace: "pre-wrap" }}>{h.input_text}</div>

              {h.parsed_json && (
                <div style={{ marginTop: 6 }}>
                  <small>parsed_json saved (string in DB)</small>
                </div>
              )}

              {h.error_message && (
                <div style={{ color: "crimson" }}>{h.error_message}</div>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
