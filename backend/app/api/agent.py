"""API router for AI Operations Agent interactions."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.agent import AgentRequest, AgentResponse
from app.agent.agent import certificate_agent
from app.utils.logger import logger

router = APIRouter()

@router.post("", response_model=AgentResponse, summary="Query the AI Operations Agent")
async def ask_agent(request: AgentRequest, db: Session = Depends(get_db)):
    """
    Submit an operational question in natural language.
    The agent autonomously selects and executes appropriate tools against the database
    and returns a factual response with telemetry.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        response = await certificate_agent.process_query(
            question=request.question.strip(),
            db=db,
        )
        return response
    except Exception as e:
        logger.error(f"Error handling agent query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the agent request."
        )
