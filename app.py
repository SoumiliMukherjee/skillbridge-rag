from contextlib import asynccontextmanager
from fastapi import FastAPI , HTTPException
from pydantic import BaseModel , Field
from job_fetcher import get_live_jobs
from rag_engine import build_vector_stores , recommend_jobs

app_state = {
    'jobs':[],
    'vector_store':None,
    'status':'Not Initialized'
}


def refresh_index(force_refresh:bool = False):
    jobs , status = get_live_jobs(force_refresh=force_refresh)
    if not jobs:
        raise RuntimeError(status or "No jobs available to index.")
    app_state['jobs'] = jobs
    app_state['vector_store'] = build_vector_stores(jobs)
    app_state['status'] = status

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when FastAPI starts up to pre-load jobs and FAISS."""
    refresh_index(force_refresh=False)
    yield

app = FastAPI(title = 'SkillBridge RAG API' , version='1.0.0' , lifespan = lifespan)

class MatchRequest(BaseModel):
    skills : str = Field(...,min_length=2 , description="Comma-separated candidate skills")
    top_k : int = Field(default=4 , ge=1,le=10 , description="Number of jobs to retrieve")
@app.get("/health")
def health_check():
    """Returns server status, job count, and cache/API source message."""
    return {
        'status' : 'ok',
        'jobs_indexed' : len(app_state['jobs']),
        'source_message' : app_state['status']
        }
@ app.post('/refresh')
def refresh_jobs():
    try:
        refresh_index(force_refresh= True)
        return{
            'status':'refreshed',
            'jobs_indexed': len(app_state['jobs']),
            'source_message':app_state['status']
        }
    except Exception as e:
        raise HTTPException(status_code=500 , detail=str(e))
@app.post('/match')
def match_jobs(req:MatchRequest):
    """Runs semantic retrieval + Groq LLM recommendation for the given skills."""
    if app_state['vector_store'] is None:
        raise HTTPException(status_code=503 , detail="Vector store is not ready yet.")
    try:
        recommendations = recommend_jobs(
            user_skills=req.skills,
            vector_store=app_state['vector_store'],
            top_k=req.top_k
        )
        return{
            'recommendations' : recommendations,
            'jobs_searched' : len(app_state['jobs']),
            'source_message' : app_state['status']
        }
    except Exception as e:
        raise HTTPException(status_code=500 , detail=str(e))

@app.get("/jobs")
def list_all_jobs():
    """Returns all indexed jobs so users can browse the full feed."""
    return {"jobs": app_state["jobs"], "total": len(app_state["jobs"])}

    