# backend/app/__init__.py
"""
QR Attendance Agent Application Package
"""

__version__ = "1.0.0"
__author__ = "QR Attendance Team"

# backend/app/models/__init__.py
"""
Data Models Package
"""

from .schemas import *

# backend/app/services/__init__.py
"""
Services Package
"""

from backend.app.services.gemini_service import gemini_service
from backend.app.services.airtable_service import airtable_service
from backend.app.services.qr_generator import qr_generator_service
from backend.app.services.scraping_service import scraping_service
from backend.app.services.qr_service import qr_service

__all__ = [
    "gemini_service",
    "airtable_service", 
    "qr_generator_service",
    "scraping_service",
    "qr_service"
]

# backend/app/utils/__init__.py
"""
Utilities Package
"""

from backend.app.utils.helpers import *