"""
LangGraph agent for the HCP Log Interaction chat interface.

Role of the agent:
The agent sits behind the "conversational chat" mode of the Log Interaction
screen. A field rep types a natural-language message (e.g. "Met Dr. Iyer
today, discussed CardioPlus samples, she was positive"). The agent classifies
the rep's intent, routes to the correct tool node, executes it against the
database (using the LLM for any extraction/summarization needed), and returns
a conversational reply plus the structured result.
"""
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from .llm import classify_intent, extract_edit_details
from . import tools
LAST_INTERACTION_ID = None

class AgentState(TypedDict):
    message: str
    rep_name: str
    intent: Optional[str]
    result: Optional[dict]
    reply: Optional[str]
    interaction_id: Optional[int]
    db: Session


def classify_node(state: AgentState) -> AgentState:
    state["intent"] = classify_intent(state["message"])
    return state


def log_node(state: AgentState) -> AgentState:
    global LAST_INTERACTION_ID

    result = tools.log_interaction(
        state["db"],
        state["message"],
        state["rep_name"]
    )

    LAST_INTERACTION_ID = result["interaction_id"]

    state["result"] = result
    state["interaction_id"] = result["interaction_id"]

    state["reply"] = (
        f"Logged interaction with {result.get('hcp_name')}. "
        f"Summary: {result.get('summary')}"
    )
    return state


# def edit_node(state: AgentState) -> AgentState:
#     from sqlalchemy import desc

#     # Get the most recently logged interaction
#     interaction = (
#         state["db"]
#         .query(tools.Interaction)
#         .order_by(desc(tools.Interaction.id))
#         .first()
#     )

#     if not interaction:
#         state["reply"] = "No interaction found to edit."
#         return state

#     message = state["message"].lower()

#     # Simple correction example
#     if "dr.john" in message:
#         hcp = tools._get_or_create_hcp(state["db"], "Dr. John")
#         interaction.hcp_id = hcp.id

#     interaction.updated_at = tools.datetime.utcnow()

#     state["db"].commit()
#     state["db"].refresh(interaction)

#     state["reply"] = f"Interaction updated successfully. HCP name changed to {interaction.hcp.name}."

#     state["result"] = {
#         "interaction_id": interaction.id,
#         "hcp_name": interaction.hcp.name,
#     }

#     return state
def edit_node(state: AgentState) -> AgentState:
    global LAST_INTERACTION_ID
    
    interaction = (
    state["db"]
    .query(tools.Interaction)
    .filter(
    tools.Interaction.id == LAST_INTERACTION_ID
)
    .first()
)

    if not interaction:
        state["reply"] = "No interaction found."
        return state

    updates = extract_edit_details(state["message"])

    if not updates:
        state["reply"] = "I couldn't understand what you wanted to edit."
        return state

    if "hcp_name" in updates:
        hcp = tools._get_or_create_hcp(state["db"], updates["hcp_name"])
        interaction.hcp_id = hcp.id

    if "summary" in updates:
        interaction.summary = updates["summary"]

    if "sentiment" in updates:
        interaction.sentiment = updates["sentiment"]

    if "interaction_type" in updates:
        interaction.interaction_type = updates["interaction_type"]

    if "products_discussed" in updates:
        interaction.products_discussed = updates["products_discussed"]

    if "materials_shared" in updates:
        interaction.materials_shared = updates["materials_shared"]

    interaction.updated_at = tools.datetime.utcnow()

    state["db"].commit()
    state["db"].refresh(interaction)

    state["reply"] = "Interaction updated successfully."

    state["result"] = {
        "interaction_id": interaction.id,
        "hcp_name": interaction.hcp.name,
        "summary": interaction.summary,
        "interaction_type": interaction.interaction_type,
        "sentiment": interaction.sentiment,
        "products_discussed": interaction.products_discussed,
        "materials_shared": interaction.materials_shared,
    }

    return state

def history_node(state: AgentState) -> AgentState:
    hcp_name = state["message"].split("history")[-1].strip(" :for")
    result = tools.fetch_hcp_history(state["db"], hcp_name or state["message"])
    state["result"] = result
    if "error" in result:
        state["reply"] = result["error"]
    else:
        state["reply"] = f"Found {result['total_interactions']} past interactions for {result['hcp_name']}."
    return state


def followup_node(state: AgentState) -> AgentState:
    state["result"] = {"error": "Please provide interaction_id and follow-up date via the form/API."}
    state["reply"] = "To schedule a follow-up, please provide the interaction ID and number of days."
    return state


def summary_node(state: AgentState) -> AgentState:
    hcp_name = state["message"].split("summary")[-1].strip(" :for")
    result = tools.generate_summary(state["db"], hcp_name or state["message"])
    state["result"] = result
    state["reply"] = result.get("report", result.get("error", "Could not generate summary."))
    return state


def fallback_node(state: AgentState) -> AgentState:
    state["reply"] = (
        "I can help you log interactions, edit them, fetch HCP history, "
        "schedule follow-ups, or generate summaries. Could you rephrase?"
    )
    return state


def route(state: AgentState) -> str:
    intent = state.get("intent", "")
    mapping = {
        "log_interaction": "log",
        "edit_interaction": "edit",
        "fetch_hcp_history": "history",
        "schedule_followup": "followup",
        "generate_summary": "summary",
    }
    return mapping.get(intent, "fallback")


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("classify", classify_node)
    graph.add_node("log", log_node)
    graph.add_node("edit", edit_node)
    graph.add_node("history", history_node)
    graph.add_node("followup", followup_node)
    graph.add_node("summary", summary_node)
    graph.add_node("fallback", fallback_node)

    graph.set_entry_point("classify")
    graph.add_conditional_edges("classify", route, {
        "log": "log",
        "edit": "edit",
        "history": "history",
        "followup": "followup",
        "summary": "summary",
        "fallback": "fallback",
    })
    for node in ["log", "edit", "history", "followup", "summary", "fallback"]:
        graph.add_edge(node, END)

    return graph.compile()


hcp_agent = build_graph()


def run_agent(db: Session, message: str, rep_name: str = "Field Rep") -> dict:
    initial_state: AgentState = {
        "message": message,
        "rep_name": rep_name,
        "intent": None,
        "result": None,
        "reply": None,
        "db": db,
        "interaction_id": LAST_INTERACTION_ID,
    }
    final_state = hcp_agent.invoke(initial_state)
    return {
        "reply": final_state["reply"],
        "tool_used": final_state["intent"],
        "data": final_state["result"],
    }
