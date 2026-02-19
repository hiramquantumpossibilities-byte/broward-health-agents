"""
Broward Health AI Content Generation API - FIXED
"""
import os
import asyncio
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Broward Health AI Content API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase - hardcoded for deployment
from supabase import create_client

def get_supabase():
    try:
        return create_client(
            "https://kzwjzxmjjnlolpdpzuvz.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt6d2p6eG1qam5sb2xwZHB6dXZ6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTYyMjM0NjgwMCwiZXhwIjoxOTM3OTIyODAwfQ.UJ9D_4J5JjQRMXHNmKZQJhJhL4Z1HbG8dWmu5X7kF7I"
        )
    except Exception as e:
        print(f"Supabase connection error: {e}")
        return None

@app.get("/v1/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/v1/categories")
async def list_categories():
    sb = get_supabase()
    if not sb:
        return {"error": "Database not connected"}
    try:
        result = sb.table('categories').select('*').execute()
        return {"categories": result.data}
    except Exception as e:
        return {"error": str(e)}

@app.get("/v1/drafts")
async def list_drafts():
    sb = get_supabase()
    if not sb:
        return {"error": "Database not connected"}
    try:
        result = sb.table('drafts').select('*').limit(10).execute()
        return {"drafts": result.data, "count": len(result.data)}
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/generate")
async def generate_content(topic: str, category_id: str, keywords: List[str] = []):
    sb = get_supabase()
    if not sb:
        return {"error": "Database not connected"}
    try:
        # Create request
        req = sb.table('generation_requests').insert({
            'topic': topic,
            'category_id': category_id,
            'keywords': keywords,
            'status': 'pending'
        }).execute()
        return {"id": req.data[0]['id'], "status": "pending", "topic": topic}
    except Exception as e:
        return {"error": str(e)}

@app.get("/v1/generate/{request_id}")
async def get_generation(request_id: str):
    sb = get_supabase()
    if not sb:
        return {"error": "Database not connected"}
    try:
        result = sb.table('generation_requests').select('*').eq('id', request_id).execute()
        if not result.data:
            return {"error": "Request not found"}
        return result.data[0]
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
