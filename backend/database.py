# database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from ssl import create_default_context

from config import DATABASE_URL
from base import Base  # Import Base from base.py
from models import ConversationLog

# Setup SSL context if needed
ssl_context = create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = False

# Create asynchronous engine
engine = create_async_engine(DATABASE_URL,echo=True,connect_args={"ssl": ssl_context})

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

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



async def get_conversation_logs(user_id: str) -> list:
    """
    Retrieve conversation logs for a specific user.
    """
    async with async_session() as session:
        result = await session.execute(
            select(ConversationLog).filter(ConversationLog.user_id == user_id)
        )
        return result.scalars().all()

async def get_db():
    """
    Dependency generator for an async database session.
    """
    async with async_session() as session:
        yield session
