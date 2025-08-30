from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
from pipeline import QuranQAPipeline
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration
try:
    from .config.config import (
        CORS_ORIGINS, CORS_ALLOW_CREDENTIALS, MAX_WORKERS,
        API_HOST, API_PORT, API_RELOAD, API_LOG_LEVEL
    )
except ImportError:
    # Fallback for when running directly
    from config.config import (
        CORS_ORIGINS, CORS_ALLOW_CREDENTIALS, MAX_WORKERS,
        API_HOST, API_PORT, API_RELOAD, API_LOG_LEVEL
    )

# Initialize FastAPI app
app = FastAPI(
    title="Quran Chatbot API",
    description="API for the Quranic linguistic analysis chatbot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool executor for running the pipeline
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Pydantic models for request/response
class QuestionRequest(BaseModel):
    question: str
    verbose: Optional[bool] = False

class QuestionResponse(BaseModel):
    answer: str
    question_type: Optional[str] = None
    target_entity: Optional[str] = None
    surah_filter: Optional[int] = None
    processing_time: Optional[float] = None

class HealthResponse(BaseModel):
    status: str
    message: str

class PipelineStatus(BaseModel):
    stage: str
    message: str
    timestamp: float

# Global pipeline instance
pipeline = None

def get_pipeline():
    """Get or create a pipeline instance."""
    global pipeline
    if pipeline is None:
        pipeline = QuranQAPipeline(verbose=False)
    return pipeline

@app.on_event("startup")
async def startup_event():
    """Initialize the pipeline on startup."""
    logger.info("Initializing Quran Chatbot API...")
    get_pipeline()
    logger.info("Quran Chatbot API initialized successfully")

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with API information."""
    return HealthResponse(
        status="healthy",
        message="Quran Chatbot API is running. Use /docs for API documentation."
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Quran Chatbot API is operational"
    )

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question to the Quran chatbot.
    
    This endpoint processes Arabic questions about Quranic words, roots, and linguistic analysis.
    """
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Get pipeline instance
        pipeline = get_pipeline()
        
        # Run the pipeline in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(
            executor, 
            pipeline.answer_question, 
            request.question
        )
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        # Extract additional information if verbose mode is requested
        question_type = None
        target_entity = None
        surah_filter = None
        
        if request.verbose:
            # You could add logic here to extract more details from the pipeline
            # For now, we'll return the basic response
            pass
        
        return QuestionResponse(
            answer=answer,
            question_type=question_type,
            target_entity=target_entity,
            surah_filter=surah_filter,
            processing_time=round(processing_time, 3)
        )
        
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )

@app.post("/ask/stream")
async def ask_question_stream(request: QuestionRequest):
    """
    Ask a question with streaming status updates.
    
    This endpoint provides real-time updates as the question is processed through the pipeline.
    """
    try:
        status_updates = []
        
        def status_callback(msg: str):
            status_updates.append(msg.strip())
        
        # Create a new pipeline instance with status callback
        pipeline = QuranQAPipeline(verbose=True, status_callback=status_callback)
        
        # Run the pipeline in a thread pool
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(
            executor, 
            pipeline.answer_question, 
            request.question
        )
        
        return {
            "answer": answer,
            "status_updates": status_updates,
            "total_stages": len(status_updates)
        }
        
    except Exception as e:
        logger.error(f"Error processing question with streaming: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )

@app.get("/examples")
async def get_examples():
    """Get example questions that can be asked to the chatbot."""
    examples = [
        {
            "arabic": "ما معنى كلمة غفر؟",
            "english": "What is the meaning of the word 'ghafara'?",
            "type": "word_meaning"
        },
        {
            "arabic": "كم مرة ورد جذر سجد في القرآن؟",
            "english": "How many times does the root 'sajada' appear in the Quran?",
            "type": "frequency_word_root"
        },
        {
            "arabic": "ما الفرق بين كلمة عقل وكلمة فهم؟",
            "english": "What is the difference between the words 'aql' and 'fahm'?",
            "type": "difference_two_words"
        },
        {
            "arabic": "استخرج جميع الآيات التي تحتوي على جذر كتب",
            "english": "Extract all verses containing the root 'kataba'",
            "type": "root_ayah_extraction"
        },
        {
            "arabic": "ما هي الصيغ الصرفية لكلمة علم؟",
            "english": "What are the morphological forms of the word 'ilm'?",
            "type": "morphology"
        }
    ]
    
    return {
        "examples": examples,
        "total": len(examples),
        "note": "These are example questions in Arabic that demonstrate the chatbot's capabilities."
    }

@app.get("/capabilities")
async def get_capabilities():
    """Get information about what the chatbot can do."""
    capabilities = {
        "supported_languages": ["Arabic"],
        "question_types": [
            "word_meaning",
            "frequency_word_root", 
            "difference_two_words",
            "root_ayah_extraction",
            "morphology",
            "dictionary_lookup"
        ],
        "features": [
            "Arabic word analysis",
            "Root-based search",
            "Morphological analysis",
            "Frequency counting",
            "Verse extraction",
            "Linguistic comparison"
        ],
        "data_sources": [
            "Quran text",
            "Arabic dictionary",
            "Morphological analysis",
            "Root analysis"
        ]
    }
    
    return capabilities

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_RELOAD,
        log_level=API_LOG_LEVEL
    )
