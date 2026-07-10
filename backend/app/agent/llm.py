import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

def call_llm(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    """Generic call to the Groq-hosted LLM."""
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        **kwargs,
    )
    return completion.choices[0].message.content


# def extract_interaction_details(raw_text: str) -> dict:
    """
    Uses the LLM to turn free-form rep notes / chat text into structured
    interaction data: hcp name, summary, products discussed, sentiment.
    """
    system_prompt = (
        "You are a pharma CRM assistant. Extract structured data from a field "
        "rep's notes about a visit to a healthcare professional (HCP). "
        "Return ONLY valid JSON with keys: "
        "hcp_name (string), summary (1-2 sentence summary), "
        "products_discussed (array of strings), sentiment (positive/neutral/negative), "
        "interaction_type (visit/call/email)."
    )
    result = call_llm(system_prompt, raw_text, json_mode=True)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {
            "hcp_name": "Unknown",
            "summary": raw_text[:200],
            "products_discussed": [],
            "sentiment": "neutral",
            "interaction_type": "visit",
        }
def extract_interaction_details(raw_text: str) -> dict:
    """
    Uses the LLM to convert free-form interaction notes into structured CRM data.
    """

    system_prompt = """
    You are a Healthcare CRM AI Assistant.

    Extract structured information from the sales representative's interaction notes.

    Return ONLY valid JSON in this format:

    {
      "hcp_name": "",
      "summary": "",
      "products_discussed": [],
      "materials_shared": [],
      "samples_distributed": [],
      "sentiment": "",
      "interaction_type": ""
    }

    Rules:

    - hcp_name = Doctor/HCP name.
    - summary = Only actual product or medicine names.
    - products_discussed = Only actual product or medicine names. Never include brochures, leaflets, visual aids, documents, or any shared materials.
    - materials_shared = Brochures, Visual Aids, Leaflets, Clinical Papers, Product Literature, etc.
    - samples_distributed = Medicine samples actually given.
    - sentiment = positive, neutral or negative.
    - interaction_type = visit, call or email.

    Example:

    Input:
    Today I met Dr. Smith and discussed Product X efficiency.
    The sentiment was positive.
    I shared brochures.

    Output:

    {
      "hcp_name":"Dr. Smith",
      "summary":"Product X",
      "products_discussed":["Product X"],
      "materials_shared":["Brochures"],
      "samples_distributed":[],
      "sentiment":"positive",
      "interaction_type":"visit"
    }

    Return JSON only.
    """

    result = call_llm(system_prompt, raw_text, json_mode=True)

    print(result)   # Debug

    try:
        return json.loads(result)
    except Exception:
        return {
            "hcp_name": "Unknown",
            "summary": raw_text[:200],
            "products_discussed": [],
            "materials_shared": [],
            "samples_distributed": [],
            "sentiment": "neutral",
            "interaction_type": "visit",
        }

def summarize_history(interactions: list) -> str:
    """Summarizes a list of past interactions into a readable report."""
    system_prompt = (
        "You are a pharma CRM assistant. Summarize the following list of past "
        "HCP interactions into a short, readable report highlighting trends, "
        "repeated topics, and sentiment over time."
    )
    text = "\n".join(
        f"- {i.get('interaction_date')}: {i.get('summary')} "
        f"(products: {i.get('products_discussed')}, sentiment: {i.get('sentiment')})"
        for i in interactions
    )
    if not text:
        return "No prior interactions found for this HCP."
    return call_llm(system_prompt, text)


def classify_intent(message: str) -> str:
    """Classifies user chat intent into one of the 5 tool names."""
    system_prompt = (
        "Classify the user's message into exactly one of these intents: "
        "log_interaction, edit_interaction, fetch_hcp_history, "
        "schedule_followup, generate_summary. "
        "Reply with ONLY the intent label, nothing else."
    )
    result = call_llm(system_prompt, message)
    return result.strip().lower()

def extract_edit_details(message: str) -> dict:
    """
    Uses the LLM to understand what fields the user wants to edit.
    Returns ONLY the fields mentioned by the user.
    """

    system_prompt = """
You are an AI assistant for a Healthcare CRM.

The user is EDITING an existing interaction.

Return ONLY valid JSON.
Return ONLY the fields that need to be updated.
Do not return explanations or markdown.

Possible fields:
- hcp_name
- interaction_type
- sentiment
- summary
- products_discussed
- materials_shared

IMPORTANT RULES:

- This is an EDIT request, not a new interaction.
- Only update the fields explicitly mentioned by the user.
- If the user says "instead of", "replace", "actually", "change to", or "not", return ONLY the NEW value.
- Never include the old value.
- Do NOT put shared materials inside summary.
- Do NOT put shared materials inside products_discussed.
- Do NOT put products inside materials_shared.

Recognize the following as shared materials:
- Samples
- Product Samples
- Brochures
- Leaflets
- Clinical Papers
- Clinical Study Reports
- Visual Aids
- Product Literature
- Patient Education Leaflets
- Flyers

Examples:

User:
Sorry the doctor's name is Dr. John.

Output:
{
  "hcp_name": "Dr. John"
}

User:
The sentiment should be neutral.

Output:
{
  "sentiment": "neutral"
}

User:
We discussed CardioPlus and Aspirin.

Output:
{
  "products_discussed": ["CardioPlus", "Aspirin"]
}

User:
We discussed Product Y instead of Product X.

Output:
{
  "products_discussed": ["Product Y"]
}

User:
Actually we discussed Product Alpha.

Output:
{
  "products_discussed": ["Product Alpha"]
}

User:
Outcome should be Doctor requested more samples.

Output:
{
  "summary": "Doctor requested more samples."
}

User:
I shared brochures and clinical papers.

Output:
{
  "materials_shared": ["Brochures", "Clinical Papers"]
}

User:
Shared sample.

Output:
{
  "materials_shared": ["Samples"]
}

User:
I shared samples.

Output:
{
  "materials_shared": ["Samples"]
}

User:
I shared product samples.

Output:
{
  "materials_shared": ["Product Samples"]
}

User:
Instead of brochures, I shared samples.

Output:
{
  "materials_shared": ["Samples"]
}

User:
The doctor's name is Dr. John. The sentiment was neutral. I shared samples instead of brochures.

Output:
{
  "hcp_name": "Dr. John",
  "sentiment": "neutral",
  "materials_shared": ["Samples"]
}

Return JSON only.
"""

    result = call_llm(system_prompt, message, json_mode=True)

    print("LLM Response:", result)

    try:
        return json.loads(result)
    except Exception as e:
        print("JSON Parse Error:", e)
        return {}