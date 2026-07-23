import logging
from typing import Dict, Any, List
from app.config import settings
from app.redis_client import redis_manager
from app.chatbot.flows import MAIN_MENU, BOOK_LAB_MENU
from app.crm_client import push_lead_to_crm
from app.database import AsyncSessionLocal
from app.models import MessageLog

import re

logger = logging.getLogger(__name__)

def is_valid_name(name: str) -> bool:
    if not name:
        return False
    # Ensure name contains only alphabets and spaces, and is at least 2 characters long
    return bool(re.match(r"^[a-zA-Z\s]{2,}$", name.strip()))

MONTHS_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12
}

def parse_flexible_datetime(dt_str: str) -> str:
    """
    Parses a wide range of user inputs for date & time and returns a normalized
    string in the format: "DD/MM/YYYY at HH:MM AM/PM".
    If invalid or unparseable, returns None.
    """
    if not dt_str:
        return None
    
    # Normalize string: lowercase, remove commas, replace multiple spaces with single space
    s = dt_str.strip().lower()
    s = s.replace(" at ", " ").replace(",", " ")
    s = re.sub(r'\s+', ' ', s)
    
    import datetime
    now = datetime.datetime.now()
    current_year = now.year
    
    day, month, year = None, None, None
    hour, minute, ampm = 10, 0, "AM" # Defaults
    
    # 1. Parse Date Component
    numeric_date_match = re.search(r'\b(\d{1,2})[-./](\d{1,2})[-./](\d{2,4})\b', s)
    if numeric_date_match:
        d_str, m_str, y_str = numeric_date_match.groups()
        day = int(d_str)
        month = int(m_str)
        year = int(y_str)
        if year < 100:
            year += 2000 if year >= 20 else 2100
        s = s.replace(numeric_date_match.group(0), "")
    else:
        month_name = None
        for m_name in MONTHS_MAP:
            if re.search(r'\b' + re.escape(m_name) + r'\b', s):
                month_name = m_name
                month = MONTHS_MAP[m_name]
                break
        
        if month:
            clean_s = re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1', s)
            month_escaped = re.escape(month_name)
            
            pattern1 = rf'\b(\d{{1,2}})\s+{month_escaped}(?:\s+(\d{{2,4}}))?\b'
            pattern2 = rf'\b{month_escaped}\s+(\d{{1,2}})(?:\s+(\d{{2,4}}))?\b'
            
            match1 = re.search(pattern1, clean_s)
            match2 = re.search(pattern2, clean_s)
            
            if match1:
                day = int(match1.group(1))
                year = int(match1.group(2)) if match1.group(2) else current_year
                if year < 100:
                    year += 2000
                s = clean_s.replace(match1.group(0), "")
            elif match2:
                day = int(match2.group(1))
                year = int(match2.group(2)) if match2.group(2) else current_year
                if year < 100:
                    year += 2000
                s = clean_s.replace(match2.group(0), "")
        else:
            if "tomorrow" in s:
                tomorrow_date = now + datetime.timedelta(days=1)
                day, month, year = tomorrow_date.day, tomorrow_date.month, tomorrow_date.year
                s = s.replace("tomorrow", "")
            elif "today" in s:
                day, month, year = now.day, now.month, now.year
                s = s.replace("today", "")
    
    if not day or not month or not year:
        return None
        
    try:
        datetime.date(year, month, day)
    except ValueError:
        return None
        
    # 2. Parse Time Component
    time_match_colon = re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b', s)
    time_match_no_colon = re.search(r'\b(\d{1,2})\s*(am|pm)\b', s)
    time_match_just_hour = re.search(r'\b(\d{1,2})\b', s)
    
    if time_match_colon:
        h_str, m_str, ampm_str = time_match_colon.groups()
        hour = int(h_str)
        minute = int(m_str)
        if ampm_str:
            ampm = ampm_str.upper()
        else:
            if hour > 12:
                hour -= 12
                ampm = "PM"
            elif hour == 12:
                ampm = "PM"
            elif hour == 0:
                hour = 12
                ampm = "AM"
            else:
                ampm = "AM"
    elif time_match_no_colon:
        h_str, ampm_str = time_match_no_colon.groups()
        hour = int(h_str)
        minute = 0
        ampm = ampm_str.upper()
    elif time_match_just_hour:
        h_str = time_match_just_hour.group(1)
        hour = int(h_str)
        minute = 0
        if hour > 12:
            hour -= 12
            ampm = "PM"
        elif hour == 12:
            ampm = "PM"
        elif hour == 0:
            hour = 12
            ampm = "AM"
        else:
            ampm = "AM"
            
    if not (1 <= hour <= 12) or not (0 <= minute <= 59):
        return None
        
    return f"{day:02d}/{month:02d}/{year:04d} at {hour:02d}:{minute:02d} {ampm}"

def is_valid_date_time(dt_str: str) -> bool:
    return parse_flexible_datetime(dt_str) is not None

def build_chat_response(text: str, buttons: List[Dict[str, str]] = None) -> Dict[str, Any]:
    body_blocks = [{"type": "TextBlock", "text": text}]
    
    choices = []
    actions = []
    if buttons:
        for b in buttons:
            title = b["title"]
            if len(title) > 24:
                title = title[:24]
                
            if b["payload"] == "FLOW_LIVE_AGENT":
                choices.append({
                    "id": "FLOW_LIVE_AGENT",
                    "title": title,
                    "value": "Connect To Agent",
                    "payload": "FLOW_LIVE_AGENT"
                })
                actions.append({
                    "type": "Action.Submit",
                    "title": "Connect To Live Agent",
                    "id": "connectToLiveAgentSubmitForm",
                    "value": "Connect To Live Agent",
                    "actionId": settings.LIVE_AGENT_ACTION_ID
                })
            elif b["payload"] == "Connect to Live":
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

def is_fuzzy_greeting(text: str) -> bool:
    if not text:
        return False
    text = text.lower().strip()
    
    # Exact triggers (expanded list)
    greetings = [
        "hi", "hello", "hey", "hy", "start", "restart", "hlo", "hii", 
        "main menu", "menu", "namaste", "namaskar", "yo", "yoo", "gm", 
        "good morning", "good evening", "heyyy", "hola", "heya", "hye", 
        "hay", "heyy", "hii", "hiii"
    ]
    if text in greetings:
        return True
        
    # Fuzzy matching for spelling mismatches
    import difflib
    for g in greetings:
        if abs(len(text) - len(g)) <= 2:
            ratio = difflib.SequenceMatcher(None, text, g).ratio()
            if ratio >= 0.75:
                return True
                
    return False

async def process_user_message(user_id: str, text: str, payload: str = None, csid: str = None, identifier: str = None) -> Dict[str, Any]:
    if identifier:
        await redis_manager.update_session(user_id, context_update={"identifier": identifier})

    session = await redis_manager.get_session(user_id)
    flow = session.get("current_flow")
    step = session.get("current_step")

    logger.info(f"User {user_id} - Flow: {flow}, Step: {step}, Payload: {payload}, Text: {text}")

    # Determine if user is new (has no previous message logs in MySQL)
    from app.database import AsyncSessionLocal
    from app.models import MessageLog
    from sqlalchemy import select
    
    is_new_user = True
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(MessageLog).filter(MessageLog.user_id == user_id).limit(1)
            )
            if result.scalar() is not None:
                is_new_user = False
    except Exception as e:
        logger.error(f"Error checking if user is new: {e}")

    # Build dynamic main menu text
    if is_new_user:
        main_menu_text = "Hello! Patheazy Labs\nEasy Path To Quality Diagnostics"
    else:
        main_menu_text = "Hello! Welcome to Patheazy Labs\nEasy Path To Quality Diagnostics"

    # Process payload if text contains common triggers
    if text:
        normalized_text = text.lower().strip()
        if is_fuzzy_greeting(normalized_text):
            payload = "MAIN_MENU"
        elif normalized_text == "book a lab test":
            payload = "FLOW_BOOK_LAB"
        elif normalized_text in ["connect with the live agent", "connect to live agent", "live agent", "connect to live", "connect to agent", "Connect To Live"]:
            payload = "FLOW_LIVE_AGENT"

    # Standard "Main Menu" reset
    if payload == "MAIN_MENU":
        await redis_manager.clear_session(user_id)
        return build_chat_response(text=main_menu_text, buttons=MAIN_MENU["buttons"])

    # If user pressed connect to agent button
    if payload in ["Connect to Live", "FLOW_LIVE_AGENT"]:
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
            if not text or not is_valid_name(text):
                return build_chat_response(text="Invalid name. Please enter a valid Name (letters and spaces only, no numbers or special characters).")
            await redis_manager.update_session(user_id, flow="home_collection", step="gender", context_update={"name": text.strip()})
            return build_chat_response(text="Please Enter your\nGender (e.g., Male, Female, Other)")
        elif step == "gender":
            if not text or text.lower().strip() not in ["male", "m", "female", "f", "other", "o"]:
                return build_chat_response(text="Invalid input. Please enter a valid Gender (e.g., Male, Female, Other).")
            await redis_manager.update_session(user_id, flow="home_collection", step="age", context_update={"gender": text.strip()})
            return build_chat_response(text="Please Enter your\nAge")
        elif step == "age":
            if not text or not text.strip().isdigit() or not (0 < int(text.strip()) < 120):
                return build_chat_response(text="Invalid age. Please enter a valid Age (e.g., 25).")
            await redis_manager.update_session(user_id, flow="home_collection", step="pincode", context_update={"age": text.strip()})
            return build_chat_response(text="Please Enter your\nPincode")
        elif step == "pincode":
            if not text or not text.strip().isdigit() or len(text.strip()) != 6:
                return build_chat_response(text="Invalid pincode. Please enter a valid 6-digit Pincode (numbers only).")
            await redis_manager.update_session(user_id, flow="home_collection", step="address", context_update={"pincode": text.strip()})
            return build_chat_response(text="Please Enter your\naddress")
        elif step == "address":
            if not text or len(text.strip()) < 5:
                return build_chat_response(text="Invalid address. Please enter a complete address.")
            await redis_manager.update_session(user_id, flow="home_collection", step="tests", context_update={"address": text.strip()})
            return build_chat_response(text="Please specify the laboratory tests you wish to book.\n\nKindly list all required test names in a single message. We look forward to assisting you.")
        elif step == "tests":
            if not text or len(text.strip()) < 2:
                return build_chat_response(text="Invalid test name. Please enter the tests you wish to book.")
            await redis_manager.update_session(user_id, flow="home_collection", step="date_time", context_update={"tests": text.strip()})
            return build_chat_response(text="Please Enter your Preferred Date and Time.\n(For example: DD/MM/YYYY at 10:00 AM)")
        elif step == "date_time":
            normalized_dt = parse_flexible_datetime(text)
            if not normalized_dt:
                return build_chat_response(text="Invalid format. Please enter date and time in the correct format:\nDD/MM/YYYY at HH:MM AM/PM\n(For example: 17/07/2026 at 10:00 AM)")
            # Extract collected variables
            ctx = session.get("context", {})
            full_name = ctx.get("name", "")
            phone = ctx.get("identifier") or identifier or user_id or ""
            age = ctx.get("age", "")
            gender = ctx.get("gender", "")
            pincode = ctx.get("pincode", "")
            address = ctx.get("address", "")
            tests = ctx.get("tests", "")
            date_time = normalized_dt

            remarks = (
                f"Home Collection Booking - Age: {age}, Gender: {gender}, "
                f"Pincode: {pincode}, Address: {address}, Tests: {tests}, "
                f"Preferred Time: {date_time}"
            )
            form_data = {
                "name": full_name,
                "mobile": phone,
                "age": age,
                "gender": gender,
                "pincode": pincode,
                "address": address,
                "tests": tests,
                "date_time": date_time,
                "disposition_name": "Test Booking",
                "sub_disposition_name": "Home Collection"
            }
            # Push lead to C-Zentrix CRM
            success, response_text = await push_lead_to_crm(
                full_name=full_name,
                phone=phone,
                agent_remarks=remarks,
                form_data=form_data,
                csid=csid or user_id
            )

            # Log CRM response in database message logs
            try:
                async with AsyncSessionLocal() as db:
                    crm_log = MessageLog(
                        user_id=user_id,
                        sender="SYSTEM",
                        message_text=f"[CRM Lead Push Response]\nStatus: {'SUCCESS' if success else 'FAILED'}\nResponse: {response_text}"
                    )
                    db.add(crm_log)
                    await db.commit()
            except Exception as db_err:
                logger.error(f"Failed to write CRM log to database: {db_err}")

            await redis_manager.clear_session(user_id)
            if success:
                response_msg = (
                    "Thank you for providing your details.\n"
                    "Your home collection booking has been successfully registered.\n"
                    "Our Patheazy support team will contact you shortly to confirm your appointment.\n\n"
                    "Warm regards,\n🤖 Patheazy Labs Virtual Assistant"
                )
            else:
                response_msg = (
                    "Thank you for providing your details.\n"
                    "We are experiencing a temporary sync delay. However, our Patheazy support team has received your request and will contact you shortly to confirm your booking details.\n\n"
                    "Warm regards,\n🤖 Patheazy Labs Virtual Assistant"
                )

            return build_chat_response(
                text=response_msg,
                buttons=[{"title": "Main Menu", "payload": "MAIN_MENU"}]
            )

    elif flow == "walk_in":
        if step == "name":
            if not text or not is_valid_name(text):
                return build_chat_response(text="Invalid name. Please enter a valid Name (letters and spaces only, no numbers or special characters).")
            await redis_manager.update_session(user_id, flow="walk_in", step="gender", context_update={"name": text.strip()})
            return build_chat_response(text="Please Enter your\nGender (e.g., Male, Female, Other)")
        elif step == "gender":
            if not text or text.lower().strip() not in ["male", "m", "female", "f", "other", "o"]:
                return build_chat_response(text="Invalid input. Please enter a valid Gender (e.g., Male, Female, Other).")
            await redis_manager.update_session(user_id, flow="walk_in", step="age", context_update={"gender": text.strip()})
            return build_chat_response(text="Please Enter your\nAge")
        elif step == "age":
            if not text or not text.strip().isdigit() or not (0 < int(text.strip()) < 120):
                return build_chat_response(text="Invalid age. Please enter a valid Age (e.g., 25).")

            # Extract collected variables
            ctx = session.get("context", {})
            full_name = ctx.get("name", "")
            phone = ctx.get("identifier") or identifier or user_id or ""
            gender = ctx.get("gender", "")
            age = text.strip()

            remarks = f"Walk-in Centre Booking - Age: {age}, Gender: {gender}"
            form_data = {
                "name": full_name,
                "mobile": phone,
                "gender": gender,
                "age": age,
                "disposition_name": "Test Booking",
                "sub_disposition_name": "Walk In"
            }
            # Push lead to C-Zentrix CRM
            success, response_text = await push_lead_to_crm(
                full_name=full_name,
                phone=phone,
                agent_remarks=remarks,
                form_data=form_data,
                csid=csid or user_id
            )

            # Log CRM response in database message logs
            try:
                async with AsyncSessionLocal() as db:
                    crm_log = MessageLog(
                        user_id=user_id,
                        sender="SYSTEM",
                        message_text=f"[CRM Lead Push Response]\nStatus: {'SUCCESS' if success else 'FAILED'}\nResponse: {response_text}"
                    )
                    db.add(crm_log)
                    await db.commit()
            except Exception as db_err:
                logger.error(f"Failed to write CRM log to database: {db_err}")

            await redis_manager.clear_session(user_id)
            if success:
                response_msg = (
                    "Thank you for providing your details.\n"
                    "Your walk-in appointment has been successfully registered.\n"
                    "Our customer care executive will reach out to you shortly to confirm the center details.\n\n"
                    "Warm regards,\n🤖 Patheazy Labs Virtual Assistant"
                )
            else:
                response_msg = (
                    "Thank you for providing your details.\n"
                    "We are experiencing a temporary sync delay. However, our customer care executive has received your request and will reach out to you shortly to confirm the center details.\n\n"
                    "Warm regards,\n🤖 Patheazy Labs Virtual Assistant"
                )

            return build_chat_response(
                text=response_msg,
                buttons=[{"title": "Main Menu", "payload": "MAIN_MENU"}]
            )

    # Default fallback
    await redis_manager.clear_session(user_id)
    return build_chat_response(text=main_menu_text, buttons=MAIN_MENU["buttons"])
