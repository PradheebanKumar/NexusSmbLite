# NexusSMB Lite

NexusSMB Lite is a web application for small and medium businesses to manage inventory, sales, expenses, analytics, customer interactions, and day-to-day operational alerts from one place.

Developed by Pradheeban Kumar.

## Features

- Inventory, sales, and expense management
- Business dashboard and analytics
- Customer and shop chat interfaces
- File uploads for purchase bills and sales records
- Automated alerts and scheduled operational checks
- WhatsApp integration support

## Technology

- Frontend: React, Vite, Tailwind CSS
- Backend: FastAPI and SQLAlchemy
- Database: SQLite for local development

## Run locally

### Backend

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and add your own values.
4. Start the API:

   ```bash
   uvicorn backend.main:app --reload
   ```

The API will be available at `http://localhost:8000`, with interactive documentation at `/docs`.

### Frontend

1. Open the `frontend` folder.
2. Install packages and run the development server:

   ```bash
   npm install
   npm run dev
   ```

Open `http://localhost:5173` in your browser.

## Environment variables

The following values are configured in `.env` and must never be committed:

- `DATABASE_URL`
- `SECRET_KEY`
- `GEMINI_API_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_NUMBER`

## Repository contents

The repository intentionally excludes credentials, local databases, virtual environments, installed packages, generated frontend builds, and personal editor/assistant settings.
