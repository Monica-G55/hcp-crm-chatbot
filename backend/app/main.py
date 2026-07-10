from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routes import interactions, chat

# Create tables on startup (fine for an assignment; use Alembic migrations in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-First HCP CRM - Log Interaction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interactions.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "HCP CRM Log Interaction API"}
