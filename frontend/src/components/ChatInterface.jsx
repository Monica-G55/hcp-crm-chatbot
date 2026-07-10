import React, { useState, useRef, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { sendMessage } from "../store/chatSlice";
import { fetchInteractions } from "../store/interactionSlice";

export default function ChatInterface() {
  const dispatch = useDispatch();
  const { messages, status } = useSelector((state) => state.chat);
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const message = input;
    setInput("");
    await dispatch(sendMessage({ message, rep_name: "Field Rep" }));
    dispatch(fetchInteractions());
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSend();
  };

  return (
    <div className="assistant-panel">
      <div className="assistant-header">
        <div className="title-row">🤖 AI Assistant</div>
        <div className="subtitle">Log interaction via chat</div>
      </div>

      <div className="chat-window">
        {messages.length === 0 && (
          <p style={{ color: "#9ca3af", fontSize: 13, lineHeight: 1.5 }}>
            Log interaction details here (e.g., "Met Dr. Smith, discussed Product X
            efficacy, positive sentiment, shared brochure") or ask for help.
          </p>
        )}
        {messages.map((m, idx) => (
          <div key={idx} className={`chat-bubble ${m.role}`}>
            {m.text}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe interaction..."
        />
        <button className="btn-primary" onClick={handleSend} disabled={status === "loading"}>
          Log
        </button>
      </div>
    </div>
  );
}
