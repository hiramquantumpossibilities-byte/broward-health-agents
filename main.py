"""
Broward Health AI Content Generation API
6-Agent System for generating healthcare blog content
"""
import os
import asyncio
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

# Import agents
from agents.writer import WriterAgent
from agents.seo import SEOAgent
from agents.reviewer import ReviewerAgent
from agents.research import ResearchAgent
from agents.image import ImageAgent
from agents.approver import ApproverAgent

app = FastAPI(title="Broward Health AI Content API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
supabase: Optional[Client] = None

def get_supabase() -> Client:
    global supabase
    if supabase is None:
        # Hardcoded for deployment - should use env vars in production
        supabase_url = "https://kzwjzxmjjnlolpdpzuvz.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt6d2p6eG1qam5sb2xwZHB6dXZ6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTYyMjM0NjgwMCwiZXhwIjoxOTM3OTIyODAwfQ.UJ9D_4J5JjQRMXHNmKZQJhJhL4Z1HbG8dWmu5X7kF7I"
        print(f"Connecting to Supabase: {supabase_url}")
        supabase = create_client(supabase_url, supabase_key)
    return supabase

# Models
class GenerateRequest(BaseModel):
    topic: str
    category_id: str
    keywords: Optional[List[str]] = None
    requested_by: Optional[str] = None

class GenerationStatus(BaseModel):
    id: str
    status: str
    topic: str
    current_agent: Optional[str] = None
    created_at: str

class DraftResponse(BaseModel):
    id: str
    title: str
    content: str
    seo_score: int
    workflow_status: str

# Agent execution pipeline
async def run_generation_pipeline(request_id: str, topic: str, category_id: str, keywords: List[str]):
    """Execute the full 6-agent pipeline"""
    sb = get_supabase()
    
    try:
        # Update status to research
        sb.table('generation_requests').update({
            'status': 'research',
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', request_id).execute()
        
        # 1. Research Agent
        research_agent = ResearchAgent(sb)
        research_result = await research_agent.execute({
            'topic': topic,
            'keywords': keywords
        })
        
        # 2. Writer Agent
        sb.table('generation_requests').update({
            'status': 'writing',
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', request_id).execute()
        
        writer_agent = WriterAgent(sb)
        writer_result = await writer_agent.execute({
            'topic': topic,
            'category_id': category_id,
            'keywords': keywords,
            'research': research_result
        })
        
        # 3. Reviewer Agent
        sb.table('generation_requests').update({
            'status': 'reviewing',
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', request_id).execute()
        
        reviewer_agent = ReviewerAgent(sb)
        reviewer_result = await reviewer_agent.execute({
            'draft_id': writer_result.get('draft_id')
        })
        
        # 4. SEO Agent
        sb.table('generation_requests').update({
            'status': 'seo',
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', request_id).execute()
        
        seo_agent = SEOAgent(sb)
        seo_result = await seo_agent.execute({
            'draft_id': writer_result.get('draft_id')
        })
        
        # 5. Image Agent
        sb.table('generation_requests').update({
            'status': 'imaging',
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', request_id).execute()
        
        image_agent = ImageAgent(sb)
        image_result = await image_agent.execute({
            'draft_id': writer_result.get('draft_id'),
            'title': writer_result.get('title'),
            'topic': topic
        })
        
        # 6. Approver Agent
        sb.table('generation_requests').update({
            'status': 'approving',
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', request_id).execute()
        
        approver_agent = ApproverAgent(sb)
        approver_result = await approver_agent.execute({
            'draft_id': writer_result.get('draft_id')
        })
        
        # Complete
        sb.table('generation_requests').update({
            'status': 'complete',
            'completed_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', request_id).execute()
        
    except Exception as e:
        # Mark as failed
        sb.table('generation_requests').update({
            'status': 'failed',
            'completed_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', request_id).execute()
        print(f"Generation failed: {e}")

@app.post("/v1/generate", response_model=GenerationStatus)
async def generate_content(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Start a new content generation request"""
    sb = get_supabase()
    
    # Create request record
    result = sb.table('generation_requests').insert({
        'id': str(uuid4()),
        'topic': request.topic,
        'category_id': request.category_id,
        'keywords': request.keywords or [],
        'status': 'pending',
        'requested_by': request.requested_by,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create request")
    
    request_id = result.data[0]['id']
    
    # Run generation in background
    background_tasks.add_task(
        run_generation_pipeline,
        request_id,
        request.topic,
        request.category_id,
        request.keywords or []
    )
    
    return GenerationStatus(
        id=request_id,
        status='pending',
        topic=request.topic,
        created_at=result.data[0]['created_at']
    )

@app.get("/v1/generate/{request_id}", response_model=GenerationStatus)
async def get_generation_status(request_id: str):
    """Get status of a generation request"""
    sb = get_supabase()
    
    result = sb.table('generation_requests').select('*').eq('id', request_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Request not found")
    
    req = result.data[0]
    
    return GenerationStatus(
        id=req['id'],
        status=req['status'],
        topic=req['topic'],
        current_agent=req.get('status'),
        created_at=req['created_at']
    )

@app.get("/v1/drafts")
async def list_drafts():
    """List all drafts - debug version"""
    try:
        sb = get_supabase()
        result = sb.table('drafts').select('*').limit(5).execute()
        return {"drafts": result.data, "count": len(result.data)}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

@app.get("/v1/drafts/{draft_id}")
async def get_draft(draft_id: str):
    """Get a specific draft with sections"""
    sb = get_supabase()
    
    # Get draft
    draft_result = sb.table('drafts').select('*').eq('id', draft_id).execute()
    
    if not draft_result.data:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Get sections
    sections_result = sb.table('draft_sections').select('*').eq('draft_id', draft_id).order('order_index').execute()
    
    return {
        'draft': draft_result.data[0],
        'sections': sections_result.data
    }

@app.get("/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "agents": ["research", "writer", "reviewer", "seo", "image", "approver"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
