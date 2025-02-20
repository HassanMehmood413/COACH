# app/models.py
from sqlalchemy import Table, Column, Integer, String, Text, DateTime, func, JSON
from database import metadata

conversations = Table(
    "conversations",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", String, nullable=False),
    Column("transcript", Text, nullable=False),
    Column("analysis", JSON, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
)
