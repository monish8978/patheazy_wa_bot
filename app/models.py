import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from app.database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String(50), primary_key=True)
    user_id = Column(String(100), nullable=False)
    customer_name = Column(String(150), nullable=False)
    mobile_number = Column(String(20), nullable=False)
    issue_type = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    sub_category = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="OPEN")
    assigned_to = Column(String(50), default="Support Team")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "ticket_id": self.ticket_id,
            "user_id": self.user_id,
            "customer_name": self.customer_name,
            "mobile_number": self.mobile_number,
            "issue_type": self.issue_type,
            "category": self.category,
            "sub_category": self.sub_category,
            "description": self.description,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class MessageLog(Base):
    __tablename__ = "message_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    sender = Column(String(10), nullable=False)  # 'USER' or 'BOT'
    message_text = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "user_id": self.user_id,
            "sender": self.sender,
            "message_text": self.message_text,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
