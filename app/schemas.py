from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class MessageRequest(BaseModel):
    query: str = Field(..., description="Plain text user message or button payload identifier")
    app_id: Optional[str] = Field("1212", description="App application identifier")
    sessionid: Optional[str] = Field(None, description="Unique chat session identifier")
    clientId: Optional[int] = Field(205, description="Client account identifier")
    botId: Optional[int] = Field(1212, description="Chat bot identifier")
    extraParms: Optional[str] = Field(None, description="Serialized JSON or string of extra parameters")

class ChatBotResponse(BaseModel):
    type: str = Field("adaptiveCard", description="Type of container structure")
    responseType: str = Field("", description="State category of active response")
    body: List[Dict[str, Any]] = Field([], description="Visual building blocks")
    actions: List[Dict[str, Any]] = Field([], description="Interactive actions array")


