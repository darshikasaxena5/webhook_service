from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.proxy_headers import ProxyHeadersMiddleware
from app.api.endpoints import subscriptions, ingestion, status

app = FastAPI(
    title="Webhook Delivery Service",
    description="A service to ingest, queue, and deliver webhooks reliably.",
    version="0.1.0",
)

# --- CORS Configuration --- 
origins = [
    "http://localhost:3000", # Allow Next.js default dev server
    "http://localhost",
    "https://webhook-service-bp86k9nnd-darshika-saxenas-projects.vercel.app",
    "https://webhook-service-smoky.vercel.app"
    "https://webhook-service-psi.vercel.app/"
]

# Add proxy headers middleware - MUST BE FIRST
# This ensures that the app properly processes X-Forwarded-Proto header
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

# Force HTTPS for all requests in production
# This helps when running behind proxies that terminate SSL
if not "localhost" in origins[0]:  # Only add in production environment
    app.add_middleware(HTTPSRedirectMiddleware)
    
    # Add trusted host middleware in production
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=[
            "webhookservice-production.up.railway.app",
            "*.railway.app"  # Wildcard for Railway subdomains
        ]
    )

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
