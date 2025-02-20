# database.py
import os
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from sqlalchemy import create_engine
from ssl import create_default_context

from config import DATABASE_URL

# Modify the engine creation:
ssl_context = create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = False

# Create asynchronous engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    connect_args={
        "ssl": ssl_context
    }
)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class ConversationLog(Base):
    __tablename__ = "conversation_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    transcript = Column(Text)
    analysis = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

async def init_db():
    """
    Initialize the database by creating the necessary tables.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def save_conversation(user_id: str, transcript: str, analysis: str = None):
    """
    Save a conversation to the database.
    """
    async with async_session() as session:
        conv_log = ConversationLog(
            user_id=user_id,
            transcript=transcript,
            analysis=analysis
        )
        session.add(conv_log)
        await session.commit()
        return conv_log
