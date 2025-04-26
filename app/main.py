from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import subscriptions, ingestion, status

app = FastAPI(
    title="Webhook Delivery Service",
    description="A service to ingest, queue, and deliver webhooks reliably.",
    version="0.1.0",
)

# --- CORS Configuration --- 
origins = [
    "http://localhost:3000", # Allow Next.js default dev server
    "http://localhost", # Allow other local development if needed
    # Add any other origins (e.g., your deployed frontend URL) here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allow all headers
)

# --- Health Check --- 
@app.get("/health", tags=["Health"])
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}

# Include API routers
app.include_router(
    subscriptions.router,
    prefix="/subscriptions",
    # tags=["Subscriptions"] # Optional: Redundant if tags are set in the router itself
)

app.include_router(
    ingestion.router,
    prefix="/ingest",
    # tags=["Ingestion"] # Optional
)

app.include_router(
    status.router, 
    prefix="/status", # Using /status as base prefix for these endpoints
    # tags=["Status & Analytics"] # Optional
)

# Later: Add routers for status
