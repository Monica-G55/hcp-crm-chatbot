# HCP CRM – Log Interaction Screen

This is my submission for the AI-First CRM assignment. The task was to design
the "Log Interaction Screen" for a pharma CRM's HCP module — basically a
screen where a field rep can log their visit/call with a doctor, either by
filling a form or by just typing/chatting about what happened.

I built it with React (form + chat UI), FastAPI for the backend, and a
LangGraph agent that talks to Groq's `gemma2-9b-it` model to handle the
"smart" parts — pulling structured info out of plain text, summarizing a
doctor's history, etc.

## How I approached it

The way I thought about this: a field rep after a long day of doctor visits
doesn't want to fill 10 form fields for every visit. So the chat mode lets
them just type something like "met Dr. Iyer, discussed CardioPlus samples,
she seemed positive" and the agent figures out the rest — who the HCP is,
what was discussed, the sentiment — and logs it. The form mode is still
there for reps who prefer structured entry, or for more detailed logging
(materials shared, samples given, follow-up actions etc).

Both modes end up going through the same `log_interaction` tool under the
hood, so the data ends up consistent either way.

## What the LangGraph agent actually does

The agent sits behind the chat box. When a message comes in, it:
1. figures out what the rep is trying to do (log something new, edit
   something, look up history, etc.)
2. routes that to the right tool
3. the tool does its thing against the DB (and calls the LLM if it needs to
   extract/summarize anything)
4. sends back a reply + whatever data the frontend needs

## The 5 tools

- **log_interaction** – takes free text and gets the LLM to pull out HCP
  name, a short summary, products discussed, and sentiment, then saves it.
- **edit_interaction** – lets you go back and change something on a
  previously logged interaction (sentiment, summary, etc.)
- **fetch_hcp_history** – pulls up everything logged for a given HCP.
- **schedule_followup** – creates a follow-up reminder tied to a specific
  interaction (e.g. "send literature in 2 weeks").
- **generate_summary** – asks the LLM to turn a doctor's whole interaction
  history into a short readable report, useful before your next visit.

## Stack

- React + Redux for the frontend, Google Inter font
- FastAPI backend
- LangGraph for the agent
- Groq `gemma2-9b-it` for the LLM calls
- MySQL for the database (works with Postgres too, just swap the connection
  string)

## Running it locally

**Backend**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        
pip install -r requirements.txt

copy .env.example .env
# then open .env and add:
#   - your GROQ_API_KEY (get one free at console.groq.com/keys)
#   - your DATABASE_URL (I used MySQL, e.g. mysql+pymysql://root:@localhost:3306/hcp_crm)

uvicorn app.main:app --reload --port 8000
```
Once it's running, `http://localhost:8000"

**Frontend**
```bash
cd frontend
npm install
npm start
```
Opens at `http://localhost:3000`.

Make sure the backend is running first, otherwise the frontend calls will
just fail with a connection error.

## Things to try in the chat box

```text
Met Dr. Ramesh Kumar today, discussed OncoBoost trial results, the sentiment was  positive and i share the Phase III report.
```
```text
Edit Prompt: Sorry the name was Dr.Smith and the sentiment was negative
```

``` New text
Show history for Dr. Smith
```

```text
Generate summary for Dr. Smith



## Project layout

```
backend/
  app/
    main.py            → FastAPI entrypoint
    database.py        → DB connection/session setup
    models.py           → HCP, Interaction, FollowUp tables
    schemas.py           → request/response validation
    agent/
      llm.py               → all the Groq calls (extraction, summarizing, intent classification)
      tools.py              → the 5 tools
      agent.py               → wires the tools into a LangGraph graph
    routes/
      interactions.py         → form-mode REST endpoints
      chat.py                   → the /chat endpoint the agent runs behind

frontend/
  src/
    store/       → redux slices for interactions + chat
    components/  → the form, the chat panel, the interaction list
    api/         → axios calls to the backend
```

## A couple of honest notes

- I used MySQL since that's what I'm more used to; Postgres works fine too,
  just change `DATABASE_URL`.
- Tables get created automatically on first run via SQLAlchemy — didn't set
  up proper migrations (Alembic) since this was scoped as an assignment, not
  a production build.
- `edit_interaction` and `schedule_followup` are easiest to demo through the
  `/docs` Swagger page since they need an interaction ID — in a real product
  I'd have the frontend show IDs/edit buttons directly on the interaction
  list instead of expecting the rep to know the ID.
- Model used is `gemma2-9b-it` as required by the task; swapping to
  `llama-3.3-70b-versatile` in `app/agent/llm.py` gives noticeably better
  summaries if higher quality is ever needed.
