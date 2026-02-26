import { useEffect, useState } from "react";
import "./App.css";

export default function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadHistory() {
    const res = await fetch("/api/history?limit=20");
    if (!res.ok) throw new Error(`History failed: ${res.status}`);
    const data = await res.json();
    setHistory(data);
  }

  useEffect(() => {
    loadHistory().catch((e) => setError(String(e.message || e)));
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

      if (!res.ok) {
        throw new Error(body.detail || `Extract failed: ${res.status}`);
      }

      setResult(body);
      await loadHistory();
    } catch (e) {
      setError(String(e.message || e));
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
    } catch (e) {
      setError(String(e.message || e));
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
            <li key={h.id} style={{ marginBottom: 18 }}>
              <div>
                <strong>#{h.id}</strong> [{h.status}]{" "}
                <small>{h.created_at}</small>
              </div>

              <div style={{ marginTop: 6, whiteSpace: "pre-wrap" }}>
                {h.input_text}
              </div>

              {h.parsed && (
                <div style={{ marginTop: 10 }}>
                  <div style={{ fontSize: 12, opacity: 0.8 }}>parsed</div>
                  <pre
                    style={{
                      background: "#111",
                      color: "#0f0",
                      padding: 12,
                      overflowX: "auto",
                    }}
                  >
                    {JSON.stringify(h.parsed, null, 2)}
                  </pre>
                </div>
              )}

              {!h.parsed && h.parsed_json && (
                <div style={{ marginTop: 10 }}>
                  <div style={{ fontSize: 12, opacity: 0.8 }}>
                    parsed_json (string; parse failed or not validated)
                  </div>
                  <pre
                    style={{
                      background: "#222",
                      color: "#ddd",
                      padding: 12,
                      overflowX: "auto",
                    }}
                  >
                    {h.parsed_json}
                  </pre>
                </div>
              )}

              {h.error_message && (
                <div style={{ marginTop: 10, color: "crimson" }}>
                  {h.error_message}
                </div>
              )}
            </li>
          ))}
        </ul>

        {history.length === 0 && (
          <div style={{ marginTop: 12, opacity: 0.7 }}>
            No history yet. Run Extract to create entries.
          </div>
        )}
      </div>
    </div>
  );
}
