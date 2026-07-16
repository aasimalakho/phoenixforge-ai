import React, { useState, useRef, useEffect } from "react";
import { sendChat } from "../api/client";

const SUGGESTIONS = [
  "Why did stg_orders fail?",
  "Show impacted datasets",
  "Who owns the failing asset?",
  "What changed in the last 24 hours?",
];

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: "agent",
      text:
        "Ask me about any incident, dataset, or lineage relationship PhoenixForge AI has seen. " +
        "Try one of the suggestions below to get started.",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text) => {
    const message = text ?? input;
    if (!message.trim() || busy) return;
    setMessages((m) => [...m, { role: "user", text: message }]);
    setInput("");
    setBusy(true);
    try {
      const res = await sendChat(message);
      setMessages((m) => [...m, { role: "agent", text: res.answer }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "agent", text: "Couldn't reach the backend. Is it running?" }]);
    }
    setBusy(false);
  };

  return (
    <div>
      <div className="page-eyebrow">Natural language interface</div>
      <h1 className="page-title">Ask PhoenixForge</h1>
      <p className="page-sub">
        Backed by the same DataHub metadata context and incident history the agents use.
      </p>

      <div className="card">
        <div className="chat-window">
          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble ${m.role === "user" ? "chat-user" : "chat-agent"}`}>
              {m.text}
            </div>
          ))}
          {busy && <div className="chat-bubble chat-agent loading-line">// thinking...</div>}
          <div ref={endRef} />
        </div>

        <div className="btn-row" style={{ marginBottom: 12, flexWrap: "wrap" }}>
          {SUGGESTIONS.map((s) => (
            <button key={s} className="btn" style={{ fontSize: 12 }} onClick={() => send(s)}>
              {s}
            </button>
          ))}
        </div>

        <div className="chat-input-row">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask a question..."
          />
          <button className="btn btn-primary" onClick={() => send()} disabled={busy}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
