import React from "react";
import InteractionForm from "./InteractionForm";
import ChatInterface from "./ChatInterface";
import InteractionList from "./InteractionList";

export default function LogInteractionScreen() {
  return (
    <div className="app-shell">
      <div className="header">
        <h1>Log HCP Interaction</h1>
        <p>Record your HCP engagement using the structured form, or describe it to the AI Assistant.</p>
      </div>

      <div className="workspace">
        <InteractionForm />
        <ChatInterface />
      </div>

      <InteractionList />
    </div>
  );
}
