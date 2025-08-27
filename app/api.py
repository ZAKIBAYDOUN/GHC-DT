"""
FastAPI routes for GHC Digital Twin API
Provides REST endpoints for the Digital Twin functionality
"""

import os
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .ghc_twin import app as langgraph_app, digital_twin

# Initialize FastAPI app
api = FastAPI(
    title="GHC Digital Twin API",
    description="Digital Twin API for Green Hill Canarias project",
    version="1.0.0"
)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
if ALLOWED_ORIGINS and ALLOWED_ORIGINS[0]:
    api.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Request/Response Models
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    final_answer: str
    error: str = None

class IngestRequest(BaseModel):
    texts: List[str]

class IngestResponse(BaseModel):
    status: str
    message: str

class HealthResponse(BaseModel):
    status: str
    message: str

# Authentication dependency for ingestion
def verify_ingest_token(x_ingest_token: str = Header(...)):
    """Verify the ingestion token"""
    expected_token = os.getenv("INGEST_AUTH_TOKEN")
    if not expected_token:
        raise HTTPException(status_code=500, detail="Ingestion token not configured")
    
    if x_ingest_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid ingestion token")
    
    return x_ingest_token

# API Routes
@api.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="GHC Digital Twin API is running"
    )

@api.post("/api/twin/query", response_model=QueryResponse)
async def query_twin(request: QueryRequest) -> QueryResponse:
    """
    Process a question through the Digital Twin and return an answer
    """
    try:
        # Prepare initial state
        initial_state = {
            "question": request.question,
            "context_docs": None,
            "final_answer": "",
            "error": None
        }
        
        # Run the LangGraph
        result = langgraph_app.invoke(initial_state)
        
        return QueryResponse(
            final_answer=result.get("final_answer", "I apologize, but I couldn't generate an answer."),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@api.post("/api/twin/ingest_texts", response_model=IngestResponse)
async def ingest_texts(
    request: IngestRequest,
    token: str = Depends(verify_ingest_token)
) -> IngestResponse:
    """
    Ingest text documents into the vector store
    Requires X-INGEST-TOKEN header for authentication
    """
    try:
        if not request.texts:
            raise HTTPException(status_code=400, detail="No texts provided for ingestion")
        
        # Use the digital twin's ingest method
        result = digital_twin.ingest_documents(request.texts)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return IngestResponse(
            status=result["status"],
            message=result["message"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting texts: {str(e)}"
        )

# For compatibility with LangGraph Cloud
app = api