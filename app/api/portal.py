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

@router.post("/simulate", response_model=ChatBotResponse)
async def simulate_chat(req: MessageRequest, db: AsyncSession = Depends(get_db)):
    """
    Simulates sending messages to the chatbot directly from the frontend web widget.
    Persists history to MySQL and updates session states in Redis.
    """
    user_id = req.sessionid
    query_str = req.query.strip()
    
    # Check if query is actually a payload (e.g. MBOB_REGISTRATION or FLOW_MBOB)
    payload = None
    message_text = query_str
    
    if (query_str.isupper() and any(k in query_str for k in ["FLOW_", "BOOK_", "MAIN_MENU"])) or query_str == "Connect to Live":
        payload = query_str
        message_text = ""

    logger.info(f"Simulating chat for {user_id} - text: {message_text}, payload: {payload}")

    # 1. Log incoming user message
    user_log = MessageLog(
        user_id=user_id,
        sender="USER",
        message_text=message_text if message_text else f"[Action: {payload}]"
    )
    db.add(user_log)

    try:
        # 2. Process message via finite state machine
        bot_reply = await process_user_message(user_id, message_text, payload)

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
