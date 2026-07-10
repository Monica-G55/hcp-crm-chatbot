import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchInteractions } from "../store/interactionSlice";

export default function InteractionList() {
  const dispatch = useDispatch();
  const { items, status } = useSelector((state) => state.interactions);

  useEffect(() => {
    dispatch(fetchInteractions());
  }, [dispatch]);

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Logged Interactions</h3>
      {status === "loading" && <p>Loading...</p>}
      {items.length === 0 && status !== "loading" && (
        <p style={{ color: "#9ca3af" }}>No interactions logged yet.</p>
      )}
      {items.map((i) => (
        <div className="interaction-item" key={i.id}>
          <strong>{i.hcp_name}</strong>
          <span className={`badge ${i.sentiment || "neutral"}`}>{i.sentiment || "neutral"}</span>
          <div style={{ fontSize: 13, color: "#6b7280", marginTop: 4 }}>{i.summary}</div>
          <div style={{ fontSize: 12, color: "#9ca3af", marginTop: 4 }}>
            {new Date(i.interaction_date).toLocaleString()} · {i.interaction_type}
            {i.products_discussed?.length ? ` · ${i.products_discussed.join(", ")}` : ""}
          </div>
        </div>
      ))}
    </div>
  );
}
