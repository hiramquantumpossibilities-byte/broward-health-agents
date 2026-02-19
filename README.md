# Broward Health AI Content Agents
FastAPI application with 6 AI agents for generating healthcare content.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload
```

## Environment

Copy `.env.example` to `.env` and fill in:
- OPENAI_API_KEY or ANTHROPIC_API_KEY
- SUPABASE_URL
- SUPABASE_SERVICE_KEY

## API Endpoints

- `POST /v1/generate` - Start content generation
- `GET /v1/generate/{id}` - Get generation status
- `GET /v1/health` - Health check
