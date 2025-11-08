"""
FastAPI Backend for Lead Scoring & Prioritization Agent
Handles API requests and communicates with Gemini LLM
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor

from core_scoring import initialize_gemini, score_single_lead, get_priority_label
from chat_agent import chat_with_leads, get_suggested_questions

# =============================================================================
# FASTAPI APP INITIALIZATION
# =============================================================================

app = FastAPI(
    title="Lead Scoring API",
    description="AI-powered lead scoring using Google Gemini API",
    version="1.0.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initia
model = None

@app.on_event("startup")
async def startup_event():
    """Initialize Gemini model when API starts."""
    global model
    try:
        model = initialize_gemini()
        print("=" * 70)
        print("BACKEND API SERVER STARTED")
        print("=" * 70)
        print("✅ Gemini API initialized successfully")
        print("🔗 Backend ready to receive requests from frontend")
        print("=" * 70)
    except Exception as e:
        print(f"❌ Failed to initialize Gemini API: {e}")


# =============================================================================
# PYDANTIC MODELS (REQUEST/RESPONSE SCHEMAS)
# =============================================================================

class LeadInput(BaseModel):
    """Schema for single lead input."""
    role: str = Field(..., description="Job title/role of the lead")
    company_size: str = Field(..., description="Company size range (e.g., '50-200', '1000+')")
    message: str = Field(..., description="Lead's message or inquiry")
    
    class Config:
        schema_extra = {
            "example": {
                "role": "CTO",
                "company_size": "500-1000",
                "message": "We have an urgent migration deadline approaching. Need enterprise plan for 300+ users."
            }
        }


class LeadBatchInput(BaseModel):
    """Schema for batch lead input."""
    leads: List[LeadInput]


class LeadScore(BaseModel):
    """Schema for lead scoring response."""
    score: int
    justification: str
    priority_label: str
    success: bool
    error: Optional[str] = None
    timestamp: str


class LeadBatchScore(BaseModel):
    """Schema for batch scoring response."""
    results: List[LeadScore]
    total: int
    successful: int
    failed: int


class HealthCheck(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: str
    gemini_initialized: bool


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/", response_model=dict)
async def root():
    """Root endpoint - API information."""
    return {
        "name": "Lead Scoring API (Backend)",
        "version": "1.0.0",
        "description": "AI-powered lead scoring using Google Gemini",
        "flow": "Frontend → Backend API → Gemini LLM → Backend → Frontend",
        "endpoints": {
            "/health": "Health check",
            "/score": "Score a single lead (POST)",
            "/score/batch": "Score multiple leads (POST)",
            "/docs": "Interactive API documentation"
        }
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy" if model is not None else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "gemini_initialized": model is not None
    }


@app.post("/score", response_model=LeadScore)
async def score_lead(lead: LeadInput):
    """
    Score a single lead.
    
    Flow: Frontend → This endpoint → Gemini LLM → Response
    
    Args:
        lead: LeadInput object with role, company_size, and message
        
    Returns:
        LeadScore object with score, justification, and metadata
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Gemini API not initialized. Please check your GEMINI_API_KEY."
        )
    
    try:
        # Call Gemini LLM through core_scoring module
        result = score_single_lead(
            model=model,
            role=lead.role,
            company_size=lead.company_size,
            message=lead.message
        )
        
        return {
            "score": result["score"],
            "justification": result["justification"],
            "priority_label": get_priority_label(result["score"]),
            "success": result["success"],
            "error": result.get("error"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error scoring lead: {str(e)}"
        )


async def process_single_lead_async(lead: LeadInput, semaphore: asyncio.Semaphore):
    """
    Process a single lead with concurrency control.
    
    Args:
        lead: LeadInput object
        semaphore: Asyncio semaphore to limit concurrent workers
        
    Returns:
        dict: Lead score result
    """
    async with semaphore:
        try:
            # Run the synchronous scoring function in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                score_single_lead,
                model,
                lead.role,
                lead.company_size,
                lead.message
            )
            
            lead_score = {
                "score": result["score"],
                "justification": result["justification"],
                "priority_label": get_priority_label(result["score"]),
                "success": result["success"],
                "error": result.get("error"),
                "timestamp": datetime.now().isoformat()
            }
            
            return lead_score
            
        except Exception as e:
            return {
                "score": 0,
                "justification": "Error processing.",
                "priority_label": "🚫 Junk/Error",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


@app.post("/score/batch", response_model=LeadBatchScore)
async def score_leads_batch(batch: LeadBatchInput):
    """
    Score multiple leads in batch with 100 concurrent workers (NLP is instant!).
    
    Flow: Frontend → This endpoint → 100 Parallel Workers → Response
    
    Args:
        batch: LeadBatchInput object with list of leads
        
    Returns:
        LeadBatchScore object with results for all leads
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Gemini API not initialized. Please check your GEMINI_API_KEY."
        )
    
    # Create a semaphore to limit concurrent workers to 100 (NLP is CPU-light)
    semaphore = asyncio.Semaphore(100)
    
    # Process all leads concurrently with 100 workers
    tasks = [process_single_lead_async(lead, semaphore) for lead in batch.leads]
    results = await asyncio.gather(*tasks)
    
    # Count successful and failed
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    return {
        "results": results,
        "total": len(batch.leads),
        "successful": successful,
        "failed": failed
    }


# =============================================================================
# CHAT AGENT ENDPOINTS
# =============================================================================

class ChatQuery(BaseModel):
    """Schema for chat query."""
    query: str = Field(..., description="User's question about the lead data")
    leads_data: List[dict] = Field(..., description="List of scored leads")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Who are the top 5 leads?",
                "leads_data": [
                    {
                        "full_name": "Michael Chen",
                        "email": "mchen@techcorp.com",
                        "company_name": "TechCorp",
                        "role": "CTO",
                        "score": 95,
                        "priority_label": "🔥 High Priority"
                    }
                ]
            }
        }


class ChatResponse(BaseModel):
    """Schema for chat response."""
    answer: str
    success: bool
    error: Optional[str] = None
    leads_analyzed: int
    timestamp: str


@app.post("/chat", response_model=ChatResponse)
async def chat_about_leads(chat_query: ChatQuery):
    """
    Chat with AI about lead data.
    
    Flow: Frontend → This endpoint → Gemini LLM (with data context) → Response
    
    Args:
        chat_query: ChatQuery with user question and lead data
        
    Returns:
        ChatResponse with AI answer
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Gemini API not initialized. Please check your GEMINI_API_KEY."
        )
    
    try:
        result = chat_with_leads(
            model=model,
            query=chat_query.query,
            leads_data=chat_query.leads_data
        )
        
        return {
            "answer": result["answer"],
            "success": result["success"],
            "error": result.get("error"),
            "leads_analyzed": result.get("leads_analyzed", 0),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat query: {str(e)}"
        )


@app.post("/chat/suggestions")
async def get_chat_suggestions(leads_data: List[dict]):
    """
    Get suggested questions based on available lead data.
    
    Args:
        leads_data: List of scored leads
        
    Returns:
        List of suggested questions
    """
    try:
        suggestions = get_suggested_questions(leads_data)
        return {
            "suggestions": suggestions,
            "success": True
        }
    except Exception as e:
        return {
            "suggestions": [],
            "success": False,
            "error": str(e)
        }


# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("LEAD SCORING BACKEND API")
    print("=" * 70)
    print()
    print("🚀 Starting FastAPI backend server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("📊 Alternative docs: http://localhost:8000/redoc")
    print("🔗 Backend will handle requests from frontend")
    print()
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
