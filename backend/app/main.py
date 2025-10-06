"""
FastAPI Application Entry Point
Main application configuration and setup
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from pathlib import Path
import time

from .routes import router
from .config import settings
from .logging_config import logger

# Initialize FastAPI application
app = FastAPI(
    title="QR Attendance Agent API",
    description="Professional QR code attendance automation system for NSBM",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    logger.info(f"➜ {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"✓ {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Time: {process_time:.3f}s"
        )
        
        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"✗ {request.method} {request.url.path} "
            f"Error: {str(e)} "
            f"Time: {process_time:.3f}s",
            exc_info=True
        )
        raise


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error for {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation Error",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception for {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": str(exc)
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Actions to perform on application startup"""
    logger.info("=" * 60)
    logger.info("🚀 QR Attendance Agent Starting...")
    logger.info("=" * 60)
    logger.info(f"Environment: Production")
    logger.info(f"Host: {settings.APP_HOST}")
    logger.info(f"Port: {settings.APP_PORT}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    logger.info(f"QR Code Directory: {settings.QR_CODE_DIR}")
    logger.info(f"Screenshot Directory: {settings.SCREENSHOT_DIR}")
    logger.info("=" * 60)
    
    # Create necessary directories
    settings.QR_CODE_DIR.mkdir(parents=True, exist_ok=True)
    settings.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("✓ All directories initialized")
    logger.info("✓ Application ready to accept requests")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Actions to perform on application shutdown"""
    logger.info("=" * 60)
    logger.info("🛑 QR Attendance Agent Shutting Down...")
    logger.info("=" * 60)


# Calculate frontend directory path
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"

# Mount static files for CSS and JS
if (frontend_dir / "css").exists():
    app.mount("/static/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
    logger.info(f"✓ CSS mounted from: {frontend_dir / 'css'}")

if (frontend_dir / "js").exists():
    app.mount("/static/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")
    logger.info(f"✓ JS mounted from: {frontend_dir / 'js'}")
# Mount screenshots directory for serving images
app.mount("/screenshots", StaticFiles(directory=str(settings.SCREENSHOT_DIR)), name="screenshots")
logger.info(f"✓ Screenshots mounted from: {settings.SCREENSHOT_DIR}")

# Serve frontend HTML at root
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend application at root"""
    html_file = frontend_dir / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(), status_code=200)
    return JSONResponse(
        content={
            "service": "QR Attendance Agent",
            "version": "1.0.0",
            "status": "operational",
            "error": "Frontend not found",
            "endpoints": {
                "docs": "/docs",
                "health": "/health"
            }
        }
    )


# Alternative app route
@app.get("/app", response_class=HTMLResponse)
async def serve_frontend_app():
    """Serve the frontend application at /app"""
    html_file = frontend_dir / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(), status_code=200)
    return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)


# Include API routes
app.include_router(router, tags=["QR Attendance"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower()
    )