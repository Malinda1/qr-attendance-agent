"""
API Routes
Defines all API endpoints for the QR Attendance Agent
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime

from .models.schemas import (
    QRConversionRequest,
    EveningQRRequest,
    ManualAttendanceRequest,
    QRResponse,
    AttendanceMarkResponse,
    HealthCheckResponse
)
from .services.qr_service import qr_service
from .services.airtable_service import airtable_service
from .config import settings
from .logging_config import logger

router = APIRouter()


@router.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "service": "QR Attendance Agent API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs"
    }


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    
    services_status = {
        "gemini": "operational",
        "airtable": "operational",
        "qr_generator": "operational",
        "web_scraper": "operational"
    }
    
    try:
        airtable_service.get_today_records()
    except:
        services_status["airtable"] = "degraded"
    
    return HealthCheckResponse(
        status="healthy" if all(v == "operational" for v in services_status.values()) else "degraded",
        timestamp=datetime.now(),
        services=services_status
    )


@router.post("/api/convert-expired-qr", response_model=QRResponse)
async def convert_expired_qr(request: QRConversionRequest):
    """
    Convert expired QR code and generate QR image (Phase 1 ONLY)
    Attendance marking happens via separate endpoint
    """
    logger.info(f"API Request: Convert expired QR - Module: {request.module_name}")
    
    try:
        result = await qr_service.process_expired_qr(
            qr_link=request.qr_link,
            module_name=request.module_name,
            username=request.username,
            password=request.password
        )
        
        qr_image_filename = Path(result["qr_image_path"]).name if result.get("qr_image_path") else None
        
        response = QRResponse(
            success=True,
            message="QR code converted and image generated successfully",
            original_qr=result["original_qr"],
            converted_qr=result["converted_qr"],
            qr_image_path=f"/api/download/qr/{qr_image_filename}" if qr_image_filename else None,
            attendance_marked=False
        )
        
        logger.info("✓ QR conversion successful (Phase 1 complete)")
        return response
        
    except Exception as e:
        logger.error(f"✗ QR conversion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/create-evening-qr", response_model=QRResponse)
async def create_evening_qr(request: EveningQRRequest):
    """
    Create evening QR code from morning QR and generate image (Phase 1 ONLY)
    Attendance marking happens via separate endpoint
    """
    logger.info(f"API Request: Create evening QR - Module: {request.module_name}")
    
    try:
        result = await qr_service.process_evening_qr(
            morning_qr_link=request.morning_qr_link,
            module_name=request.module_name,
            username=request.username,
            password=request.password
        )
        
        qr_image_filename = Path(result["qr_image_path"]).name if result.get("qr_image_path") else None
        
        response = QRResponse(
            success=True,
            message="Evening QR code created and image generated successfully",
            original_qr=result["original_qr"],
            evening_qr=result["evening_qr"],
            qr_image_path=f"/api/download/qr/{qr_image_filename}" if qr_image_filename else None,
            attendance_marked=False
        )
        
        logger.info("✓ Evening QR creation successful (Phase 1 complete)")
        return response
        
    except Exception as e:
        logger.error(f"✗ Evening QR creation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/mark-attendance", response_model=AttendanceMarkResponse)
async def mark_attendance_manually(request: ManualAttendanceRequest):
    """
    Manual attendance marking endpoint (Phase 2)
    Called when user clicks "Mark Attendance" button
    """
    logger.info(f"API Request: Manual attendance marking - Module: {request.module_name}")
    
    try:
        if request.is_evening:
            result = await qr_service.mark_attendance_for_evening_qr(
                evening_qr=request.qr_link,
                module_name=request.module_name,
                morning_qr=request.original_qr,
                username=request.username,
                password=request.password
            )
        else:
            result = await qr_service.mark_attendance_for_qr(
                converted_qr=request.qr_link,
                module_name=request.module_name,
                original_qr=request.original_qr,
                username=request.username,
                password=request.password
            )
        
        screenshot_filename = None
        if result.get("screenshot_path"):
            screenshot_filename = Path(result["screenshot_path"]).name
        
        response = AttendanceMarkResponse(
            success=True,
            message="Attendance marked successfully",
            screenshot_path=f"/api/download/screenshot/{screenshot_filename}" if screenshot_filename else None,
            screenshot_filename=screenshot_filename,
            airtable_record_id=result.get("airtable_record_id"),
            details={
                "module": request.module_name,
                "qr_link": request.qr_link,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info("✓ Manual attendance marking successful")
        return response
        
    except Exception as e:
        logger.error(f"✗ Manual attendance marking failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/download/qr/{filename}")
async def download_qr_code(filename: str):
    """Download generated QR code image"""
    logger.info(f"QR code download requested: {filename}")
    
    file_path = settings.QR_CODE_DIR / filename
    
    if not file_path.exists():
        logger.warning(f"QR code file not found: {filename}")
        raise HTTPException(status_code=404, detail="QR code not found")
    
    return FileResponse(
        path=str(file_path),
        media_type="image/png",
        filename=filename
    )


@router.get("/api/download/screenshot/{filename}")
async def download_screenshot(filename: str):
    """Download confirmation screenshot"""
    logger.info(f"Screenshot download requested: {filename}")
    
    file_path = settings.SCREENSHOT_DIR / filename
    
    if not file_path.exists():
        logger.warning(f"Screenshot file not found: {filename}")
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    return FileResponse(
        path=str(file_path),
        media_type="image/png",
        filename=filename
    )


@router.get("/api/records/today")
async def get_today_records():
    """Get all Airtable records created today"""
    logger.info("Today's records requested")
    
    try:
        records = airtable_service.get_today_records()
        return {
            "success": True,
            "count": len(records),
            "records": records
        }
    except Exception as e:
        logger.error(f"Failed to fetch today's records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/records/module/{module_name}")
async def get_module_records(module_name: str):
    """Get all records for a specific module"""
    logger.info(f"Module records requested: {module_name}")
    
    try:
        records = airtable_service.search_records(module_name)
        return {
            "success": True,
            "module_name": module_name,
            "count": len(records),
            "records": records
        }
    except Exception as e:
        logger.error(f"Failed to fetch module records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/generate-qr-only")
async def generate_qr_only(url: str, label: str = "QR Code"):
    """Generate QR code image only (without marking attendance)"""
    logger.info(f"QR generation only requested for: {url}")
    
    try:
        qr_image_path = qr_service.generate_qr_only(url, label)
        filename = Path(qr_image_path).name
        
        return {
            "success": True,
            "message": "QR code generated successfully",
            "qr_image_path": f"/api/download/qr/{filename}",
            "download_url": f"/api/download/qr/{filename}"
        }
    except Exception as e:
        logger.error(f"QR generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]