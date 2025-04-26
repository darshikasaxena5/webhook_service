# Webhook Delivery System

A robust and scalable system for receiving, queuing, and reliably delivering webhook payloads to subscribed endpoints. Built with FastAPI, Supabase (PostgreSQL), Redis, and Next.js.

## Features

*   **Webhook Subscription:** Manage target URLs for webhook delivery via API or UI.
*   **Payload Queuing:** Ingests incoming webhooks and queues them for delivery.
*   **Reliable Delivery:** Uses background workers and retry mechanisms (future enhancement) to ensure payloads reach their destination.
*   **Status Monitoring:** Provides a dashboard to view system statistics and recent delivery activity.
*   **Scalability:** Designed with containers and asynchronous processing for scalability.

## Tech Stack

*   **Backend:**
    *   Python 3.11+
    *   FastAPI
    *   Uvicorn (ASGI Server)
    *   PostgreSQL (via Supabase)
    *   Supabase Python Client
    *   Redis (for caching/queuing - planned)
*   **Frontend:**
    *   Node.js / npm
    *   Next.js
    *   React
    *   TypeScript
    *   Tailwind CSS
*   **Database:** PostgreSQL (Managed by Supabase)
*   **Containerization:** Docker & Docker Compose

## Prerequisites

*   Docker
*   Docker Compose
*   Supabase Account (for PostgreSQL database and authentication - provide connection details via environment variables)
*   Redis Instance (optional, if caching/advanced queuing is implemented - provide connection details)

## Project Structure

```
.
├── app/            # FastAPI backend source code
│   ├── api/        # API route definitions
│   ├── core/       # Configuration, core settings
│   ├── db/         # Database interaction logic
│   ├── models/     # Pydantic models
│   ├── services/   # Business logic (e.g., delivery worker - planned)
│   └── main.py     # FastAPI application entrypoint
├── frontend/       # Next.js frontend source code
│   ├── public/
│   └── src/
├── .env.example    # Example environment variables (Backend & Frontend)
├── docker-compose.yml # Docker Compose configuration
├── Dockerfile      # Dockerfile for the backend service
├── requirements.txt # Python dependencies
├── README.md       # This file
└── ...             # Other configuration files (.gitignore, etc.)
```
*(Note: Add/adjust structure based on your actual layout)*

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```

2.  **Configure Environment Variables:**
    *   Copy `.env.example` to `.env` in the root directory.
    *   Fill in your Supabase URL and Key (`SUPABASE_URL`, `SUPABASE_KEY`).
    *   If using Redis, add `REDIS_URL`.
    *   Configure any other necessary variables (e.g., `SECRET_KEY` for FastAPI).
    *   Navigate to `frontend/`.
    *   Copy `frontend/.env.local.example` (if it exists) to `frontend/.env.local`.
    *   Update `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` to point to your backend service (e.g., `http://localhost:8000` if running locally via Docker Compose).

3.  **Build and Run with Docker Compose:**
    *   From the project root directory:
    ```bash
    docker-compose up --build -d
    ```
    This command will:
    *   Build the Docker images for the backend and frontend services (if not already built).
    *   Start the containers defined in `docker-compose.yml`.

## Running the Application

*   **Backend API:** Accessible at `http://localhost:8000` (or the port specified in `docker-compose.yml`).
    *   **API Docs (Swagger):** `http://localhost:8000/docs`
    *   **API Docs (ReDoc):** `http://localhost:8000/redoc`
*   **Frontend UI:** Accessible at `http://localhost:3000` (or the port specified for the frontend service).

## Database Schema

The database schema involves three main tables:

1.  `subscriptions`: Stores details of subscribed webhook endpoints (target URL, secrets, etc.).
2.  `webhook_deliveries`: Tracks incoming webhook payloads, their status (pending, success, failed), and associated subscription.
3.  `delivery_attempts`: Logs each attempt made to deliver a specific webhook payload, including status codes and responses.


## Development


```bash
# Example: Backend local setup
# cd <project_root>
# python -m venv venv
# source venv/bin/activate
# pip install -r requirements.txt
# uvicorn app.main:app --reload --port 8000

# Example: Frontend local setup
# cd frontend
# npm install
# npm run dev
```
