import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import engine, Base
from app.redis_client import redis_manager
from app.api.portal import router as portal_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ==========================================
    # STARTUP LIFECYCLE
    # ==========================================
    logger.info("Initializing services on startup...")
    
    # Establish connection pool with Redis
    await redis_manager.connect()
    
    # Create DB schemas in MySQL if not present (asynchronously)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("MySQL Database schema synced successfully.")
    except Exception as e:
        logger.critical(f"Database schema synchronization failed: {e}")
    
    yield
    
    # ==========================================
    # SHUTDOWN LIFECYCLE
    # ==========================================
    logger.info("Cleaning up active connections...")
    await redis_manager.close()
    await engine.dispose()
    logger.info("Application shut down cleanly.")

app = FastAPI(
    title="BOB Bank Chatbot Core",
    description="High-scale production-ready dialogue bot engine for Bank of Bhutan (BOB). Includes Docker Compose, Celery, Redis, and MySQL.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for cross-origin widget integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folders and register templates directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Mount system routers
app.include_router(portal_router, prefix="/api", tags=["Simulation & CRM"])

@app.get("/")
async def render_dashboard(request: Request):
    """
    Renders the administrative dashboard containing the premium chatbot testing widget and CRM Ticket Tracker.
    """
    try:
        # Starlette < 0.35.0 (older FastAPI) compatibility
        return templates.TemplateResponse("index.html", {"request": request})
    except TypeError:
        # Starlette >= 0.35.0 (newer FastAPI) compatibility
        return templates.TemplateResponse(request=request, name="index.html")

@app.get("/health")
async def health():
    """
    Consolidated health probe endpoint for Kubernetes or load balancer readiness checks.
    """
    return {"status": "HEALTHY", "service": "BOB Bank Chatbot"}
