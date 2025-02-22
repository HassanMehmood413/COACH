# models.py
from sqlalchemy import String, Integer, Text, Column, DateTime
from datetime import datetime
from base import Base  # Import Base from base.py

class ConversationLog(Base):
    __tablename__ = "conversation_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    transcript = Column(Text)
    analysis = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "user_information"  # (Using lowercase table name is preferable)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)  # Changed from EmailStr to String
    password = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
