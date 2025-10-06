"""
Pydantic Models for Request/Response Validation
Defines all data structures used in the API
"""

from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, Literal
from datetime import datetime


class QRConversionRequest(BaseModel):
    """Request model for converting expired QR codes"""
    qr_link: str = Field(..., description="Original QR code link")
    module_name: str = Field(..., description="Name of the module/course")
    username: Optional[str] = Field(None, description="NSBM login username")
    password: Optional[str] = Field(None, description="NSBM login password")
    
    @validator('qr_link')
    def validate_qr_link(cls, v):
        if not v.startswith('https://students.nsbm.ac.lk/attendence/'):
            raise ValueError('Invalid NSBM QR link format')
        return v


class EveningQRRequest(BaseModel):
    """Request model for creating evening QR from morning QR"""
    morning_qr_link: str = Field(..., description="Morning session QR code link")
    module_name: str = Field(..., description="Name of the module/course")
    username: Optional[str] = Field(None, description="NSBM login username")
    password: Optional[str] = Field(None, description="NSBM login password")
    
    @validator('morning_qr_link')
    def validate_morning_qr_link(cls, v):
        if not v.startswith('https://students.nsbm.ac.lk/attendence/'):
            raise ValueError('Invalid NSBM QR link format')
        return v


class QRResponse(BaseModel):
    """Response model for QR code operations"""
    success: bool = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    original_qr: Optional[str] = Field(None, description="Original QR code link")
    converted_qr: Optional[str] = Field(None, description="Converted QR code link")
    evening_qr: Optional[str] = Field(None, description="Evening QR code link")
    qr_image_path: Optional[str] = Field(None, description="Path to QR code image")
    screenshot_path: Optional[str] = Field(None, description="Path to confirmation screenshot")
    airtable_record_id: Optional[str] = Field(None, description="Airtable record ID")
    timestamp: datetime = Field(default_factory=datetime.now)


class AttendanceMarkResponse(BaseModel):
    """Response model for attendance marking"""
    success: bool
    message: str
    screenshot_path: Optional[str] = None
    details: Optional[dict] = None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str = "1.0.0"
    services: dict


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class AirtableRecord(BaseModel):
    """Airtable record structure"""
    module_name: str
    original_qr_link: str
    converted_qr_link: Optional[str] = None
    evening_qr_link: Optional[str] = None
    date: str
    timestamp: str
    status: Literal["success", "failed", "pending"]


__all__ = [
    "QRConversionRequest",
    "EveningQRRequest", 
    "QRResponse",
    "AttendanceMarkResponse",
    "HealthCheckResponse",
    "ErrorResponse",
    "AirtableRecord"
]