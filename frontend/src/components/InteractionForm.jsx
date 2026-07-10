import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { submitInteraction, fetchInteractions } from "../store/interactionSlice";

export default function InteractionForm() {
  const dispatch = useDispatch();
  const interactionData = useSelector(
  (state) => state.chat.interactionData
);
  const [form, setForm] = useState({
    hcp_name: "",
    interaction_type: "visit",
    date: new Date().toISOString().slice(0, 10),
    time: new Date().toTimeString().slice(0, 5),
    attendees: "",
    topics: "",
    sentiment: "neutral",
    outcomes: "",
    followups: "",
  });
  const [materials, setMaterials] = useState([]);
  const [samples, setSamples] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  useEffect(() => {
  if (!interactionData) return;

  setForm((prev) => ({
    ...prev,
    hcp_name: interactionData.hcp_name || "",
    interaction_type: interactionData.interaction_type || "visit",
topics: interactionData.summary || "",
    sentiment: interactionData.sentiment || "neutral",
    outcomes: interactionData.summary || "",
    followups: interactionData.followups || "",
  }));

setMaterials(interactionData.materials_shared || []);
}, [interactionData]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const addMaterial = () => {
    const name = prompt("Material name (e.g. CardioPlus Brochure)");
    if (name) setMaterials([...materials, name]);
  };

  const addSample = () => {
    const name = prompt("Sample name (e.g. CardioPlus 10mg - 2 units)");
    if (name) setSamples([...samples, name]);
  };

  // Combine all structured fields into one text block - the Log Interaction
  // tool's LLM step will extract/clean this into the final structured record.
  const buildRawInput = () => {
    return [
      `HCP: ${form.hcp_name}`,
      `Interaction Type: ${form.interaction_type}`,
      `Date: ${form.date} ${form.time}`,
      form.attendees && `Attendees: ${form.attendees}`,
      form.topics && `Topics Discussed: ${form.topics}`,
      materials.length ? `Materials Shared: ${materials.join(", ")}` : null,
      samples.length ? `Samples Distributed: ${samples.join(", ")}` : null,
      `Observed Sentiment: ${form.sentiment}`,
      form.outcomes && `Outcomes: ${form.outcomes}`,
      form.followups && `Follow-up Actions: ${form.followups}`,
    ]
      .filter(Boolean)
      .join(". ");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.hcp_name || !form.topics) return;
    setSubmitting(true);
    await dispatch(
      submitInteraction({
        hcp_name: form.hcp_name,
        rep_name: "Field Rep",
        interaction_type: form.interaction_type,
        raw_input: buildRawInput(),
      })
    );
    await dispatch(fetchInteractions());
    setSubmitting(false);
    setMaterials([]);
    setSamples([]);
    setForm({
      hcp_name: "",
      interaction_type: "visit",
      date: new Date().toISOString().slice(0, 10),
      time: new Date().toTimeString().slice(0, 5),
      attendees: "",
      topics: "",
      sentiment: "neutral",
      outcomes: "",
      followups: "",
    });
  };

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h3 className="card-title">Interaction Details</h3>

      <div className="form-row">
        <div className="form-group">
          <label>HCP Name</label>
          <input
            name="hcp_name"
            value={form.hcp_name}
            onChange={handleChange}
            placeholder="Search or select HCP..."
          />
        </div>
        <div className="form-group">
          <label>Interaction Type</label>
          <select name="interaction_type" value={form.interaction_type} onChange={handleChange}>
            <option value="visit">Meeting</option>
            <option value="call">Call</option>
            <option value="email">Email</option>
          </select>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Date</label>
          <input type="date" name="date" value={form.date} onChange={handleChange} />
        </div>
        <div className="form-group">
          <label>Time</label>
          <input type="time" name="time" value={form.time} onChange={handleChange} />
        </div>
      </div>

      <div className="form-group">
        <label>Attendees</label>
        <input
          name="attendees"
          value={form.attendees}
          onChange={handleChange}
          placeholder="Enter names or search..."
        />
      </div>

      <div className="form-group">
        <label>Topics Discussed</label>
        <textarea
          name="topics"
          value={form.topics}
          onChange={handleChange}
          placeholder="Enter key discussion points..."
        />
      </div>

      <div className="section-label">Materials Shared / Samples Distributed</div>

      <div className="form-group">
        <label style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          Materials Shared
          <button type="button" className="btn-secondary" onClick={addMaterial}>
            + Search/Add
          </button>
        </label>
        {materials.length === 0 ? (
          <p className="empty-hint">No materials added.</p>
        ) : (
          <ul className="suggestion-list">
            {materials.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="form-group">
        <label style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          Samples Distributed
          <button type="button" className="btn-secondary" onClick={addSample}>
            + Add Sample
          </button>
        </label>
        {samples.length === 0 ? (
          <p className="empty-hint">No samples added.</p>
        ) : (
          <ul className="suggestion-list">
            {samples.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="section-label">Observed/Inferred HCP Sentiment</div>
      <div className="pill-row">
        {["positive", "neutral", "negative"].map((s) => (
          <label className="pill-option" key={s}>
            <input
              type="radio"
              name="sentiment"
              value={s}
              checked={form.sentiment === s}
              onChange={handleChange}
            />
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </label>
        ))}
      </div>

      <div className="form-group" style={{ marginTop: 18 }}>
        <label>Outcomes</label>
        <textarea
          name="outcomes"
          value={form.outcomes}
          onChange={handleChange}
          placeholder="Key outcomes or agreements..."
        />
      </div>

      <div className="form-group">
        <label>Follow-up Actions</label>
        <textarea
          name="followups"
          value={form.followups}
          onChange={handleChange}
          placeholder="Enter next steps or tasks..."
        />
      </div>

      <button className="btn-primary" type="submit" disabled={submitting}>
        {submitting ? "Logging..." : "Log Interaction"}
      </button>
    </form>
  );
}
