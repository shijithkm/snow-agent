from pydantic import BaseModel
from datetime import datetime


class TicketRequest(BaseModel):
    description: str
    alert_id: str | None = None
    ticket_type: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    work_comments: str | None = None