import logging
from typing import Dict, Any, List
from app.config import settings
from app.redis_client import redis_manager
from app.chatbot.flows import MAIN_MENU, BOOK_LAB_MENU

logger = logging.getLogger(__name__)

def build_chat_response(text: str, buttons: List[Dict[str, str]] = None) -> Dict[str, Any]:
    body_blocks = [{"type": "TextBlock", "text": text}]
    
    choices = []
    actions = []
    if buttons:
        for b in buttons:
            title = b["title"]
            if len(title) > 24:
                title = title[:24]
                
            if b["payload"] == "Connect to Live":
                # Render specifically as Action.Submit inside the root actions array
                actions.append({
                    "type": "Action.Submit",
                    "title": "Connect To Live Agent",
                    "id": "connectToLiveAgentSubmitForm",
                    "value": "Connect To Live Agent",
                    "actionId": settings.LIVE_AGENT_ACTION_ID
                })
            else:
                choices.append({
                    "id": b["payload"],
                    "title": title,
                    "value": title,
                    "payload": b["payload"]
                })
            
    if choices:
        body_blocks.append({
            "type": "Button",
            "id": "serviceType",
            "style": "expanded",
            "choices": choices
        })
        
    return {
        "type": "adaptiveCard",
        "responseType": "",
        "body": body_blocks,
        "actions": actions
    }

async def process_user_message(user_id: str, text: str, payload: str = None) -> Dict[str, Any]:
    session = await redis_manager.get_session(user_id)
    flow = session.get("current_flow")
    step = session.get("current_step")

    logger.info(f"User {user_id} - Flow: {flow}, Step: {step}, Payload: {payload}, Text: {text}")

    # Process payload if text contains common triggers
    if text:
        normalized_text = text.lower().strip()
        if normalized_text in ["hi", "hello", "main menu", "start"]:
            payload = "MAIN_MENU"
        elif normalized_text == "book a lab test":
            payload = "FLOW_BOOK_LAB"
        elif normalized_text in ["connect with the live agent", "connect to live agent", "live agent", "connect to live"]:
            payload = "Connect to Live"

    # Standard "Main Menu" reset
    if payload == "MAIN_MENU":
        await redis_manager.clear_session(user_id)
        return build_chat_response(text=MAIN_MENU["text"], buttons=MAIN_MENU["buttons"])

    # If user pressed connect to agent button
    if payload == "Connect to Live":
        await redis_manager.clear_session(user_id)
        return build_chat_response(text="Hello,\n\nPlease wait while our customer care\nexecutive will connect to you shortly\n~Team Patheazy")

    # If user pressed book lab test
    if payload == "FLOW_BOOK_LAB":
        await redis_manager.update_session(user_id, flow="booking", step="type")
        return build_chat_response(text=BOOK_LAB_MENU["text"], buttons=BOOK_LAB_MENU["buttons"])

    # Handle booking flows
    if flow == "booking" and step == "type":
        if payload == "BOOK_HOME" or (text and "home collection" in text.lower()):
            await redis_manager.update_session(user_id, flow="home_collection", step="name")
            return build_chat_response(text="Please Enter your Name.")
        elif payload == "BOOK_WALKIN" or (text and "walk-in" in text.lower()):
            await redis_manager.update_session(user_id, flow="walk_in", step="name")
            return build_chat_response(text="Please Enter your Name")
        else:
            return build_chat_response(text=BOOK_LAB_MENU["text"], buttons=BOOK_LAB_MENU["buttons"])

    elif flow == "home_collection":
        if step == "name":
            if not text or len(text.strip()) < 2:
                return build_chat_response(text="Invalid name. Please enter a valid Name.")
            await redis_manager.update_session(user_id, flow="home_collection", step="mobile")
            return build_chat_response(text="Please Enter your\nMobile Number")
        elif step == "mobile":
            if not text or not text.strip().isdigit() or len(text.strip()) < 10:
                return build_chat_response(text="Invalid number. Please enter a valid Mobile Number.")
            await redis_manager.update_session(user_id, flow="home_collection", step="gender")
            return build_chat_response(text="Please Enter your\nGender (e.g., Male, Female, Other)")
        elif step == "gender":
            if not text or text.lower().strip() not in ["male", "m", "female", "f", "other", "o"]:
                return build_chat_response(text="Invalid input. Please enter a valid Gender (e.g., Male, Female, Other).")
            await redis_manager.update_session(user_id, flow="home_collection", step="age")
            return build_chat_response(text="Please Enter your\nAge")
        elif step == "age":
            if not text or not text.strip().isdigit() or not (0 < int(text.strip()) < 120):
                return build_chat_response(text="Invalid age. Please enter a valid Age (e.g., 25).")
            await redis_manager.update_session(user_id, flow="home_collection", step="pincode")
            return build_chat_response(text="Please Enter your\nPincode")
        elif step == "pincode":
            if not text or not text.strip().isdigit() or len(text.strip()) != 6:
                return build_chat_response(text="Invalid pincode. Please enter a valid 6-digit Pincode.")
            await redis_manager.update_session(user_id, flow="home_collection", step="address")
            return build_chat_response(text="Please Enter your\naddress")
        elif step == "address":
            if not text or len(text.strip()) < 5:
                return build_chat_response(text="Invalid address. Please enter a complete address.")
            await redis_manager.update_session(user_id, flow="home_collection", step="tests")
            return build_chat_response(text="Please specify the laboratory tests you wish to book.\n\nKindly list all required test names in a single message. We look forward to assisting you.")
        elif step == "tests":
            if not text or len(text.strip()) < 2:
                return build_chat_response(text="Invalid test name. Please enter the tests you wish to book.")
            await redis_manager.update_session(user_id, flow="home_collection", step="date_time")
            return build_chat_response(text="Please Enter your Preferred Date and Time.\n(For example: DD/MM/YYYY at 10:00 AM)")
        elif step == "date_time":
            await redis_manager.clear_session(user_id)
            return build_chat_response(
                text="Thank you for providing your details.\nYour home collection booking has been successfully registered.\nOur Patheazy support team will contact you shortly to confirm your appointment.\n\nWarm regards,\n🤖 Patheazy Labs Virtual Assistant",
                buttons=[{"title": "Main Menu", "payload": "MAIN_MENU"}]
            )

    elif flow == "walk_in":
        if step == "name":
            if not text or len(text.strip()) < 2:
                return build_chat_response(text="Invalid name. Please enter a valid Name.")
            await redis_manager.update_session(user_id, flow="walk_in", step="mobile")
            return build_chat_response(text="Please Enter your\nMobile Number")
        elif step == "mobile":
            if not text or not text.strip().isdigit() or len(text.strip()) < 10:
                return build_chat_response(text="Invalid number. Please enter a valid Mobile Number.")
            await redis_manager.update_session(user_id, flow="walk_in", step="gender")
            return build_chat_response(text="Please Enter your\nGender (e.g., Male, Female, Other)")
        elif step == "gender":
            if not text or text.lower().strip() not in ["male", "m", "female", "f", "other", "o"]:
                return build_chat_response(text="Invalid input. Please enter a valid Gender (e.g., Male, Female, Other).")
            await redis_manager.update_session(user_id, flow="walk_in", step="age")
            return build_chat_response(text="Please Enter your\nAge")
        elif step == "age":
            if not text or not text.strip().isdigit() or not (0 < int(text.strip()) < 120):
                return build_chat_response(text="Invalid age. Please enter a valid Age (e.g., 25).")
            await redis_manager.clear_session(user_id)
            return build_chat_response(
                text="Thank you for providing your details.\nYour walk-in appointment has been successfully registered.\nOur customer care executive will reach out to you shortly to confirm the center details.\n\nWarm regards,\n🤖 Patheazy Labs Virtual Assistant",
                buttons=[{"title": "Main Menu", "payload": "MAIN_MENU"}]
            )

    # Default fallback
    await redis_manager.clear_session(user_id)
    return build_chat_response(text=MAIN_MENU["text"], buttons=MAIN_MENU["buttons"])
