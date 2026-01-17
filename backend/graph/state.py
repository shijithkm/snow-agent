from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SNOWState(BaseModel):
    ticket_id: Optional[str] = None
    description: Optional[str] = None
    intent: Optional[str] = None
    alert_id: Optional[str] = None
    ticket_type: Optional[str] = None
    assigned_to: Optional[str] = None
    closed: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[str] = None