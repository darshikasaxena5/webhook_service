# Webhook Delivery System

A robust and scalable system for receiving, queuing, and reliably delivering webhook payloads to subscribed endpoints. Built with FastAPI, Celery, Supabase (PostgreSQL), Redis, and potentially a Next.js frontend.

## Features

*   **Webhook Subscription Management:** Create, read, update, and delete webhook target URLs and associated secrets via API.
*   **Secure Webhook Ingestion:** Accepts incoming webhook payloads, verifies signatures (HMAC-SHA256), and queues them for delivery.
*   **Reliable Delivery:** Uses Celery background workers with configurable automatic retries and exponential backoff to deliver webhooks.
*   **Status Monitoring & Analytics:** Provides API endpoints to check delivery status, list delivery attempts, view system statistics, and see recent activity.
*   **Caching:** Uses Redis to cache subscription details for improved performance.
*   **Scalability:** Designed with containerization (Docker) and asynchronous task processing (Celery) for scalability.
*   **Periodic Cleanup:** Automatically cleans up old delivery attempt logs.

## Tech Stack

*   **Backend:**
    *   Python 3.11+
    *   FastAPI (ASGI Framework)
    *   Uvicorn (ASGI Server for development/workers)
    *   Gunicorn (WSGI Server for production)
    *   Celery (Distributed Task Queue)
    *   Pydantic (Data Validation)
    *   Supabase Python Client (Database Interaction)
    *   httpx (HTTP Client for sending webhooks)
    *   python-dotenv (Environment Variable Management)
*   **Database:** PostgreSQL (Managed by Supabase)
*   **Cache/Broker:** Redis
*   **Containerization:** Docker & Docker Compose
*   **Frontend (Optional - see `frontend/` directory):**
    *   Node.js / npm
    *   Next.js
    *   React
    *   TypeScript
    *   Tailwind CSS

## Architecture Overview

1.  **API (FastAPI):** The core backend service (`app/main.py`) exposes RESTful endpoints defined in `app/api/endpoints/`. It handles incoming HTTP requests.
2.  **Database (Supabase):** PostgreSQL database managed via Supabase stores subscriptions, delivery tasks, and attempt logs. Interactions are handled by modules in `app/db/` using the Supabase Python client (`app/db/client.py`). Pydantic models (`app/models/`) define data structures.
3.  **Cache (Redis):** Used to cache subscription details (`app/core/cache.py`) to reduce database lookups during delivery.
4.  **Task Queue (Celery + Redis):**
    *   When a webhook is ingested (`/ingest/{subscription_id}`), a delivery task is added to the Celery queue (using Redis as the broker).
    *   Celery workers (`app/tasks/delivery.py`), configured in `app/tasks/celery_app.py`, pick up these tasks.
    *   Workers attempt to deliver the webhook payload using `httpx`.
    *   Automatic retries with exponential backoff are configured for transient failures or non-2xx responses.
    *   Delivery attempts are logged to the database.
5.  **Scheduled Tasks (Celery Beat):** A Celery Beat service runs periodic tasks, such as cleaning up old logs (`app/tasks/cleanup.py`).
6.  **Security:** Incoming webhooks can be secured using HMAC-SHA256 signatures verified by `app/core/security.py`.
7.  **Containerization (Docker):** The backend application (`app/Dockerfile`) and its dependencies (API, worker, beat, Redis) are managed using Docker and orchestrated locally with `docker-compose.yml`.

## Project Structure

```
.
├── app/                 # FastAPI backend source code
│   ├── api/             # API route definitions (endpoints)
│   │   └── endpoints/
│   ├── core/            # Core components (security, cache)
│   ├── db/              # Database interaction logic (Supabase client, CRUD functions)
│   ├── models/          # Pydantic data models
│   ├── tasks/           # Celery tasks (delivery, cleanup, app definition)
│   ├── __init__.py
│   ├── Dockerfile       # Dockerfile for the backend service (API/Worker/Beat)
│   ├── main.py          # FastAPI application entrypoint
│   └── requirements.txt # Python dependencies
├── frontend/            # Next.js frontend source code (if present)
│   ├── ...
├── .env.example         # Example environment variables (copy to .env)
├── .gitignore
├── docker-compose.yml   # Docker Compose configuration for local development
└── README.md            # This file
```

## Prerequisites

*   Docker
*   Docker Compose (usually included with Docker Desktop)
*   Supabase Account & Project (for PostgreSQL database)
*   Git

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url> # Replace with the actual URL
    cd <repository-directory>
    ```

2.  **Configure Environment Variables:**
    *   Copy `.env.example` to a new file named `.env` in the project root directory.
    *   Open the `.env` file and fill in the required values:
        *   `SUPABASE_URL`: Your Supabase project URL.
        *   `SUPABASE_KEY`: Your Supabase project `service_role` key (or `anon` key if appropriate security policies are in place, but `service_role` is often needed for backend operations).
        *   `REDIS_URL`: The connection URL for your Redis instance (defaults to `redis://redis:6379/0` for Docker Compose setup).
    *   (Optional) Configure webhook delivery and cleanup settings:
        *   `WEBHOOK_MAX_RETRIES`: Max number of retries for webhook delivery (default: 5).
        *   `INITIAL_RETRY_DELAY_SECONDS`: Initial delay before the first retry (default: 10).
        *   `MAX_RETRY_BACKOFF_SECONDS`: Maximum delay between retries (default: 900).
        *   `WEBHOOK_DELIVERY_TIMEOUT_SECONDS`: Timeout for webhook POST requests (default: 10).
        *   `LOG_RETENTION_HOURS`: How long to keep delivery attempt logs (default: 72).

3.  **Database Setup (Supabase):**
    *   Ensure your Supabase project has the required tables. You might need to run SQL scripts based on the Pydantic models in `app/models/` or define them using the Supabase dashboard:
        *   `subscriptions` (columns matching `app/models/subscription.py::Subscription`)
        *   `webhook_deliveries` (columns matching `app/models/webhook.py::WebhookDelivery`)
        *   `delivery_attempts` (columns matching `app/models/attempt.py::DeliveryAttempt`)
    *   *Note: Consider adding migrations for schema management in a production scenario.*

4.  **Build and Run with Docker Compose:**
    *   From the project root directory:
    ```bash
    docker-compose up --build -d
    ```
    This command will:
    *   Build the Docker image for the `app` using `app/Dockerfile`.
    *   Start containers for:
        *   `redis`: The Redis cache/broker.
        *   `api`: The FastAPI backend service.
        *   `worker`: The Celery worker process.
        *   `beat`: The Celery Beat scheduler process.
    *   *(If a `frontend` service is defined in `docker-compose.yml`, it will also be started).*

## Running the Application

*   **Backend API:** Accessible at `http://localhost:8000` (as defined in `docker-compose.yml`).
    *   **API Docs (Swagger):** `http://localhost:8000/docs`
    *   **API Docs (ReDoc):** `http://localhost:8000/redoc`
*   **Frontend UI:** If configured, typically accessible at `http://localhost:3000`.

## API Endpoints

The following endpoints are available (base URL: `http://localhost:8000`):

*   `GET /health`: Basic health check. Returns `{"status": "ok"}`.
*   `POST /subscriptions/`: Create a new webhook subscription.
    *   *Request Body:* `SubscriptionCreate` model (`target_url`, optional `secret_key`).
    *   *Response:* `Subscription` model.
*   `GET /subscriptions/`: List all subscriptions (paginated).
    *   *Query Params:* `page` (default 1), `limit` (default 10).
    *   *Response:* `PaginatedSubscriptions` model.
*   `GET /subscriptions/{subscription_id}`: Get details of a specific subscription.
    *   *Response:* `Subscription` model.
*   `PUT /subscriptions/{subscription_id}`: Update a subscription.
    *   *Request Body:* `SubscriptionUpdate` model (optional `target_url`, `secret_key`).
    *   *Response:* `Subscription` model.
*   `DELETE /subscriptions/{subscription_id}`: Delete a subscription.
    *   *Response:* `204 No Content`.
*   `POST /ingest/{subscription_id}`: Ingest a webhook payload for delivery.
    *   *Request Header (Optional):* `X-Webhook-Signature-256: sha256=<hmac-sha256-signature>` (Required if `secret_key` is set for the subscription).
    *   *Request Body:* Raw JSON payload.
    *   *Response:* `202 Accepted`. Triggers background delivery task.
*   `GET /status/deliveries/{delivery_id}/status`: Get status and attempt history for a specific delivery task.
    *   *Response:* `DeliveryStatus` model (contains `delivery` details and list of `attempts`).
*   `GET /status/subscriptions/{subscription_id}/attempts`: List recent delivery attempts for a subscription.
    *   *Query Params:* `limit` (default 20).
    *   *Response:* List of `DeliveryAttempt` models.
*   `GET /status/stats`: Get aggregated system dashboard statistics.
    *   *Response:* `SystemStats` model (total subscriptions, recent success/failure counts).
*   `GET /status/activity`: Get recent system activity feed (subscription creations, delivery attempts).
    *   *Query Params:* `limit` (default 5).
    *   *Response:* List of `ActivityItem` models.

## Database Schema

The database schema involves three main tables managed in Supabase:

1.  **`subscriptions`**: Stores details of subscribed webhook endpoints (ID, target URL, secret key, timestamps). Corresponds to `app/models/subscription.py`.
2.  **`webhook_deliveries`**: Tracks incoming webhook payloads, their status (pending, processing, success, failed_attempt, failed), associated subscription ID, and timestamps. Corresponds to `app/models/webhook.py`.
3.  **`delivery_attempts`**: Logs each attempt made to deliver a specific webhook payload, including the outcome, status code, response body (potentially truncated), error message, and timestamp. Corresponds to `app/models/attempt.py`.

## Local Development (Without Docker)

While Docker Compose is recommended, you can run services locally:

1.  **Setup Backend:**
    ```bash
    # Navigate to project root
    cd <project_root>
    python -m venv venv
    source venv/bin/activate # or .\venv\Scripts\activate on Windows
    pip install -r app/requirements.txt
    pip install gunicorn # Or install if added to requirements
    # Ensure .env file exists in root with SUPABASE_* and REDIS_URL
    # Start API server (will use settings from .env)
    uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
    ```

2.  **Run Redis:** You'll need a separate Redis instance running and accessible via the `REDIS_URL` in your `.env`.

3.  **Run Celery Worker:**
    ```bash
    # In a new terminal, with venv activated and .env present
    celery -A app.tasks.celery_app worker --loglevel=INFO
    ```

4.  **Run Celery Beat:**
    ```bash
    # In another terminal, with venv activated and .env present
    celery -A app.tasks.celery_app beat --loglevel=INFO --scheduler celery.beat.PersistentScheduler
    ```

5.  **Setup Frontend:**
    ```bash
    cd frontend
    # Update .env.local's NEXT_PUBLIC_API_BASE_URL if needed
    npm install
    npm run dev
    ```
