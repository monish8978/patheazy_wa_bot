import base64
import json
import logging
import aiohttp
from app.config import settings

logger = logging.getLogger(__name__)

async def push_lead_to_crm(full_name: str, phone: str, agent_remarks: str, form_data: dict = None, csid: str = None) -> bool:
    """
    Asynchronously pushes lead data to C-Zentrix CRM Lead API.
    """
    # Split full name into first and last name
    parts = (full_name or "").strip().split(maxsplit=1)
    first_name = parts[0] if len(parts) >= 1 else ""
    last_name = parts[1] if len(parts) == 2 else ""

    # Construct data dict
    data_dict = {
        "first_name": first_name,
        "last_name": last_name,
        "country_name": "",
        "state_name": "",
        "city_name": "",
        "lead_source_name": "",
        "product_type_name": "",
        "disposition_name": "",
        "sub_disposition_name": "",
        "lead_status_name": "NEW",
        "phone": phone,
        "mobile_no": phone,
        "person_mail": "",
        "created_by": "",
        "assigned_to_dept_name": "",
        "assigned_to_user_name": "",
        "assigned_by": "",
        "lead_state": ""
    }

    if form_data:
        data_dict["person_info_customized_gender"] = form_data.get("gender", "")
        data_dict["person_info_customized_age"] = form_data.get("age", "")
        data_dict["person_info_customized_pincode"] = form_data.get("pincode", "")
        data_dict["person_info_customized_addres"] = form_data.get("address", "")
        data_dict["lead_details_customized_test"] = form_data.get("tests", "")
        data_dict["lead_details_customized_preferred_date_time"] = form_data.get("date_time", "")

    if csid:
        data_dict["csid"] = csid
    
    try:
        # Encode as JSON, then to base64
        data_json = json.dumps(data_dict)
        data_b64 = base64.b64encode(data_json.encode("utf-8")).decode("utf-8")
        
        # Build query parameters
        params = {
            "data": data_b64,
            "client_id": settings.CRM_CLIENT_ID,
            "lead_create": "1",
            "auth_token": settings.CRM_AUTH_TOKEN
        }
        
        if csid:
            params["csid"] = csid
        
        logger.info(f"Sending lead to CRM: Name={first_name} {last_name}, Phone={phone}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(settings.CRM_API_URL, params=params) as response:
                response_text = await response.text()
                if response.status == 200:
                    logger.info(f"Successfully pushed lead to CRM. Response: {response_text}")
                    return True, response_text
                else:
                    logger.error(f"Failed to push lead to CRM. HTTP Status: {response.status}, Response: {response_text}")
                    return False, f"HTTP {response.status}: {response_text}"
    except Exception as e:
        logger.error(f"Exception while pushing lead to CRM: {e}")
        return False, str(e)
