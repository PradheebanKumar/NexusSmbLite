from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.database import engine, Base
from backend.routers import owners, inventory, sales, expenses, analytics, chat, whatsapp, actions, alerts, upload, shop_public
from backend.services.scheduler import start_scheduler, stop_scheduler
from backend import models, auth
from backend.agents.orchestrator import AgentOrchestrator
from backend.database import get_db
from sqlalchemy.orm import Session


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables
    Base.metadata.create_all(bind=engine)
    # Start background scheduler
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Nexus-SMB Lite API",
    description="AI Workforce for MSMEs — inventory, finance, agents, and WhatsApp bot",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(owners.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(expenses.router)
app.include_router(analytics.router)
app.include_router(chat.router)
app.include_router(whatsapp.router)
app.include_router(actions.router)
app.include_router(alerts.router)
app.include_router(upload.router)
app.include_router(shop_public.router)   # public — no auth, for customers


@app.get("/")
def root():
    return {"message": "Nexus-SMB Lite API", "status": "running", "docs": "/docs"}


@app.post("/api/agents/run-check")
def manual_agent_run(
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    """Manually trigger agent check for current owner."""
    orchestrator = AgentOrchestrator(db, owner.id)
    result = orchestrator.run_daily_check()
    return {"message": "Agent check complete", "result": result}
