"""Useful mixins for database models"""

from sqlalchemy import Column, Integer, String, Text, DECIMAL, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class ProgressMixin:
    """Mixin for progress tracking"""
    progress_percentage = Column(DECIMAL(5, 2), default=0.0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

class MetadataMixin:
    """Mixin for JSON metadata storage"""
    metadata = Column(JSONB, default=dict)

class ColorMixin:
    """Mixin for color customization"""
    color = Column(String(7), default='#3498db')

class StatisticsMixin:
    """Mixin for denormalized statistics"""
    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime(timezone=True))
