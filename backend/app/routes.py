"""
API Routes
Defines all API endpoints for the QR Attendance Agent
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from datetime import datetime
from typing import Optional

from .models.schemas import (
    QRConversionRequest,
    EveningQRRequest,
    QRResponse,
    HealthCheckResponse,
    ErrorResponse
)
from .services.qr_service import qr_service
from .services.airtable_service import airtable_service
from .config import settings
from .logging_config import logger

# Create router
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
    
    # Test services
    try:
        # Test Airtable connection
        airtable_service.get_today_records()
    except:
        services_status["airtable"] = "degraded"
    
    return HealthCheckResponse(
        status="healthy" if all(v == "operational" for v in services_status.values()) else "degraded",
        timestamp=datetime.now(),
        services=services_status
    )


@router.post("/api/convert-expired-qr", response_model=QRResponse)
async def convert_expired_qr(request: QRConversionRequest, background_tasks: BackgroundTasks):
    """
    Convert expired QR code and generate QR image (Phase 1)
    Returns immediately with QR code and image
    Attendance marking happens in background
    
    - **qr_link**: Original expired QR code link
    - **module_name**: Name of the module/course
    - **username**: NSBM login username (optional)
    - **password**: NSBM login password (optional)
    """
    
    logger.info(f"API Request: Convert expired QR - Module: {request.module_name}")
    
    try:
        # Phase 1: Generate QR code and image (returns immediately)
        result = await qr_service.process_expired_qr(
            qr_link=request.qr_link,
            module_name=request.module_name,
            username=request.username,
            password=request.password
        )
        
        # Extract filename from full path for API response
        qr_image_filename = Path(result["qr_image_path"]).name if result.get("qr_image_path") else None
        
        # Store the converted QR for background task
        converted_qr = result["converted_qr"]
        credentials = result.get("credentials", {})
        
        # Add Phase 2 (attendance marking) to background tasks
        background_tasks.add_task(
            mark_attendance_background,
            converted_qr=converted_qr,
            module_name=request.module_name,
            original_qr=request.qr_link,
            username=credentials.get("username"),
            password=credentials.get("password"),
            is_evening=False
        )
        
        response = QRResponse(
            success=True,
            message="QR code converted and image generated. Attendance marking in progress...",
            original_qr=result["original_qr"],
            converted_qr=result["converted_qr"],
            qr_image_path=f"/api/download/qr/{qr_image_filename}" if qr_image_filename else None,
            screenshot_path=None,  # Will be available after background task completes
            airtable_record_id=None  # Will be created by background task
        )
        
        logger.info("✓ QR conversion successful (Phase 1 complete)")
        return response
        
    except Exception as e:
        logger.error(f"✗ QR conversion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/create-evening-qr", response_model=QRResponse)
async def create_evening_qr(request: EveningQRRequest, background_tasks: BackgroundTasks):
    """
    Create evening QR code from morning QR and generate image (Phase 1)
    Returns immediately with QR code and image
    Attendance marking happens in background
    
    - **morning_qr_link**: Morning session QR code link
    - **module_name**: Name of the module/course
    - **username**: NSBM login username (optional)
    - **password**: NSBM login password (optional)
    """
    
    logger.info(f"API Request: Create evening QR - Module: {request.module_name}")
    
    try:
        # Phase 1: Generate evening QR and image (returns immediately)
        result = await qr_service.process_evening_qr(
            morning_qr_link=request.morning_qr_link,
            module_name=request.module_name,
            username=request.username,
            password=request.password
        )
        
        # Extract filename from full path for API response
        qr_image_filename = Path(result["qr_image_path"]).name if result.get("qr_image_path") else None
        
        # Store the evening QR for background task
        evening_qr = result["evening_qr"]
        credentials = result.get("credentials", {})
        
        # Add Phase 2 (attendance marking) to background tasks
        background_tasks.add_task(
            mark_attendance_background,
            converted_qr=evening_qr,
            module_name=request.module_name,
            original_qr=request.morning_qr_link,
            username=credentials.get("username"),
            password=credentials.get("password"),
            is_evening=True
        )
        
        response = QRResponse(
            success=True,
            message="Evening QR code created and image generated. Attendance marking in progress...",
            original_qr=result["original_qr"],
            evening_qr=result["evening_qr"],
            qr_image_path=f"/api/download/qr/{qr_image_filename}" if qr_image_filename else None,
            screenshot_path=None,  # Will be available after background task completes
            airtable_record_id=None  # Will be created by background task
        )
        
        logger.info("✓ Evening QR creation successful (Phase 1 complete)")
        return response
        
    except Exception as e:
        logger.error(f"✗ Evening QR creation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def mark_attendance_background(
    converted_qr: str,
    module_name: str,
    original_qr: str,
    username: Optional[str],
    password: Optional[str],
    is_evening: bool
):
    """
    Background task to mark attendance (Phase 2)
    This runs after the QR code has been returned to the user
    """
    try:
        logger.info(f"Background: Starting attendance marking for {module_name}")
        
        if is_evening:
            result = await qr_service.mark_attendance_for_evening_qr(
                evening_qr=converted_qr,
                module_name=module_name,
                morning_qr=original_qr,
                username=username,
                password=password
            )
        else:
            result = await qr_service.mark_attendance_for_qr(
                converted_qr=converted_qr,
                module_name=module_name,
                original_qr=original_qr,
                username=username,
                password=password
            )
        
        logger.info(f"✓ Background attendance marking complete: {result['message']}")
        
    except Exception as e:
        logger.error(f"✗ Background attendance marking failed: {str(e)}", exc_info=True)


@router.get("/api/download/qr/{filename}")
async def download_qr_code(filename: str):
    """
    Download generated QR code image
    
    - **filename**: QR code image filename
    """
    
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
    """
    Download confirmation screenshot
    
    - **filename**: Screenshot filename
    """
    
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
    """
    Get all Airtable records created today
    """
    
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
    """
    Get all records for a specific module
    
    - **module_name**: Module name to search for
    """
    
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
    """
    Generate QR code image only (without marking attendance)
    
    - **url**: URL to encode in QR code
    - **label**: Label text for QR code
    """
    
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