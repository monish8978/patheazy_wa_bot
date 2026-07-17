import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Dict, Any

from app.database import get_db
from app.models import MessageLog
from app.redis_client import redis_manager
from app.schemas import MessageRequest, ChatBotResponse
from app.chatbot.engine import process_user_message

router = APIRouter()
logger = logging.getLogger(__name__)

# Map text or title representations to their specific payload strings (case-insensitive keys)
BUTTON_MAP = {
    "book a lab test": "FLOW_BOOK_LAB",
    "Connect To Live": "FLOW_LIVE_AGENT",
    "connect to agent": "FLOW_LIVE_AGENT",
    "connect to live agent": "FLOW_LIVE_AGENT",
    "connect to live": "FLOW_LIVE_AGENT",
    "home collection": "BOOK_HOME",
    "walk-in centre": "BOOK_WALKIN",
    "main menu": "MAIN_MENU"
}

@router.post("/simulate", response_model=ChatBotResponse)
@router.post("/patheazy", response_model=ChatBotResponse)
async def simulate_chat(req: MessageRequest, db: AsyncSession = Depends(get_db)):
    """
    Simulates sending messages to the chatbot directly from the frontend web widget.
    Persists history to MySQL and updates session states in Redis.
    """
    # 1. Resolve session ID: prioritize csid from extraParms, fall back to sessionid
    user_id = None
    if req.extraParms:
        try:
            import json
            params = json.loads(req.extraParms)
            if isinstance(params, dict):
                user_id = params.get("csid")
        except Exception:
            pass
    if not user_id:
        user_id = req.sessionid

    if not user_id:
        raise HTTPException(status_code=400, detail="sessionid or csid in extraParms must be provided")

    query_str = req.query.strip()
    
    # Check if query is actually a payload or a button title mapped to a payload (case-insensitive)
    payload = None
    message_text = query_str
    
    query_str_lower = query_str.lower()
    if query_str_lower in BUTTON_MAP:
        payload = BUTTON_MAP[query_str_lower]
        message_text = ""
    elif (query_str.isupper() and any(k in query_str for k in ["FLOW_", "BOOK_", "MAIN_MENU"])):
        payload = query_str
        message_text = ""

    logger.info(f"Simulating chat for Session ID: {user_id} - text: {message_text}, payload: {payload}")

    # 1. Log incoming user message
    user_log = MessageLog(
        user_id=user_id,
        sender="USER",
        message_text=message_text if message_text else f"[Action: {payload}]"
    )
    db.add(user_log)

    try:
        # 2. Process message via finite state machine
        bot_reply = await process_user_message(user_id, message_text, payload, csid=user_id)

        # 3. Log outgoing bot message
        body_list = bot_reply.get("body", [])
        bot_text = ""
        for block in body_list:
            if block.get("type") == "TextBlock":
                bot_text = block.get("text", "")
                break
                
        bot_log = MessageLog(
            user_id=user_id,
            sender="BOT",
            message_text=bot_text
        )
        db.add(bot_log)
        await db.commit()

        # 4. Return formatted response
        return ChatBotResponse(**bot_reply)
    except Exception as e:
        logger.error(f"Error in simulation engine: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/logs/{user_id}")
async def get_conversation_logs(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns audit trails / conversation chat history for a specific user.
    """
    try:
        result = await db.execute(
            select(MessageLog)
            .filter(MessageLog.user_id == user_id)
            .order_by(MessageLog.timestamp)
        )
        logs = result.scalars().all()
        return [log.to_dict() for log in logs]
    except Exception as e:
        logger.error(f"Failed to fetch conversation logs: {e}")
        raise HTTPException(status_code=500, detail="Database log fetch failed")

@router.post("/reset/{user_id}")
async def reset_user_session(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Deletes the ephemeral Redis session state and removes logs to restart cleanly.
    """
    try:
        # Clear redis cache
        await redis_manager.clear_session(user_id)
        
        # Optionally clear database message logs for the user to make testing clean
        # (Using standard execute to delete rows)
        from sqlalchemy import delete
        await db.execute(delete(MessageLog).where(MessageLog.user_id == user_id))
        await db.commit()
        
        return {"status": "SUCCESS", "message": f"Session and logs for user {user_id} have been reset successfully."}
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
