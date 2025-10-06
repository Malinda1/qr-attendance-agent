"""
Main QR Service
Orchestrates all QR code operations and workflows
"""

from typing import Dict, Any, Optional
from ..logging_config import logger, log_function_call
from .gemini_service import gemini_service
from .airtable_service import airtable_service
from .qr_generator import qr_generator_service
from .scraping_service import scraping_service


class QRService:
    """Main service orchestrating QR code workflows"""
    
    def __init__(self):
        """Initialize QR Service"""
        self.gemini = gemini_service
        self.airtable = airtable_service
        self.qr_gen = qr_generator_service
        self.scraper = scraping_service
        logger.info("QR Service initialized")
    
    @log_function_call
    async def process_expired_qr(
        self,
        qr_link: str,
        module_name: str,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Phase 1: Convert expired QR and generate QR code image
        Returns immediately without marking attendance
        
        Args:
            qr_link: Original expired QR link
            module_name: Module/course name
            username: NSBM login username (optional)
            password: NSBM login password (optional)
            
        Returns:
            Dictionary with QR code and image (attendance marking happens separately)
        """
        
        logger.info(f"=== Starting Expired QR Processing (Phase 1) ===")
        logger.info(f"Module: {module_name}")
        logger.info(f"Original QR: {qr_link}")
        
        result = {
            "success": False,
            "original_qr": qr_link,
            "converted_qr": None,
            "qr_image_path": None,
            "message": "",
            "credentials": {
                "username": username,
                "password": password
            }
        }
        
        try:
            # Step 1: Convert expired QR using Gemini
            logger.info("Step 1: Converting expired QR code...")
            converted_qr = self.gemini.convert_expired_qr(qr_link)
            result["converted_qr"] = converted_qr
            logger.info(f"✓ QR converted: {converted_qr}")
            
            # Step 2: Generate QR code image
            logger.info("Step 2: Generating QR code image...")
            qr_image_path = self.qr_gen.generate_qr_code(
                converted_qr,
                label_text=f"{module_name} - Attendance"
            )
            result["qr_image_path"] = qr_image_path
            logger.info(f"✓ QR image generated: {qr_image_path}")
            
            result["success"] = True
            result["message"] = "QR code converted and image generated successfully"
            
            logger.info("=== Phase 1 Complete - QR Ready ===")
            return result
            
        except Exception as e:
            error_msg = f"QR conversion failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["message"] = error_msg
            raise Exception(error_msg)
    
    @log_function_call
    async def mark_attendance_for_qr(
        self,
        converted_qr: str,
        module_name: str,
        original_qr: str,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Phase 2: Mark attendance and save to Airtable
        Called after QR code is displayed to user
        
        Args:
            converted_qr: The converted QR link
            module_name: Module/course name
            original_qr: Original QR link
            username: NSBM login username (optional)
            password: NSBM login password (optional)
            
        Returns:
            Dictionary with attendance confirmation and Airtable record
        """
        
        logger.info(f"=== Starting Attendance Marking (Phase 2) ===")
        logger.info(f"Module: {module_name}")
        logger.info(f"QR to mark: {converted_qr}")
        
        result = {
            "success": False,
            "screenshot_path": None,
            "airtable_record_id": None,
            "message": ""
        }
        
        try:
            # Step 1: Mark attendance via web scraping
            logger.info("Step 1: Marking attendance...")
            attendance_result = self.scraper.mark_attendance(
                converted_qr,
                username=username,
                password=password
            )
            result["screenshot_path"] = attendance_result["screenshot_path"]
            logger.info(f"✓ Attendance marked successfully")
            
            # Step 2: Save to Airtable
            logger.info("Step 2: Saving to Airtable...")
            record_id = self.airtable.create_record(
                module_name=module_name,
                original_qr=original_qr,
                converted_qr=converted_qr,
                status="success"
            )
            result["airtable_record_id"] = record_id
            logger.info(f"✓ Airtable record created: {record_id}")
            
            result["success"] = True
            result["message"] = "Attendance marked successfully"
            
            logger.info("=== Phase 2 Complete - Attendance Marked ===")
            return result
            
        except Exception as e:
            error_msg = f"Attendance marking failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["message"] = error_msg
            
            # Try to save error to Airtable
            try:
                self.airtable.create_record(
                    module_name=module_name,
                    original_qr=original_qr,
                    converted_qr=converted_qr,
                    status="failed"
                )
            except:
                pass
            
            raise Exception(error_msg)
    
    @log_function_call
    async def process_evening_qr(
        self,
        morning_qr_link: str,
        module_name: str,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Phase 1: Create evening QR from morning QR and generate image
        Returns immediately without marking attendance
        
        Args:
            morning_qr_link: Morning session QR link
            module_name: Module/course name
            username: NSBM login username (optional)
            password: NSBM login password (optional)
            
        Returns:
            Dictionary with evening QR code and image
        """
        
        logger.info(f"=== Starting Evening QR Processing (Phase 1) ===")
        logger.info(f"Module: {module_name}")
        logger.info(f"Morning QR: {morning_qr_link}")
        
        result = {
            "success": False,
            "original_qr": morning_qr_link,
            "evening_qr": None,
            "qr_image_path": None,
            "message": "",
            "credentials": {
                "username": username,
                "password": password
            }
        }
        
        try:
            # Step 1: Create evening QR from morning QR
            logger.info("Step 1: Creating evening QR code...")
            evening_qr = self.gemini.create_evening_qr(morning_qr_link)
            result["evening_qr"] = evening_qr
            logger.info(f"✓ Evening QR created: {evening_qr}")
            
            # Step 2: Generate QR code image
            logger.info("Step 2: Generating QR code image...")
            qr_image_path = self.qr_gen.generate_qr_code(
                evening_qr,
                label_text=f"{module_name} - Evening Session"
            )
            result["qr_image_path"] = qr_image_path
            logger.info(f"✓ QR image generated: {qr_image_path}")
            
            result["success"] = True
            result["message"] = "Evening QR code created successfully"
            
            logger.info("=== Phase 1 Complete - Evening QR Ready ===")
            return result
            
        except Exception as e:
            error_msg = f"Evening QR creation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["message"] = error_msg
            raise Exception(error_msg)
    
    @log_function_call
    async def mark_attendance_for_evening_qr(
        self,
        evening_qr: str,
        module_name: str,
        morning_qr: str,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Phase 2: Mark attendance for evening QR and save to Airtable
        
        Args:
            evening_qr: The evening QR link
            module_name: Module/course name
            morning_qr: Original morning QR link
            username: NSBM login username (optional)
            password: NSBM login password (optional)
            
        Returns:
            Dictionary with attendance confirmation
        """
        
        logger.info(f"=== Starting Evening Attendance Marking (Phase 2) ===")
        
        result = {
            "success": False,
            "screenshot_path": None,
            "airtable_record_id": None,
            "message": ""
        }
        
        try:
            # Step 1: Mark attendance
            logger.info("Step 1: Marking evening attendance...")
            attendance_result = self.scraper.mark_attendance(
                evening_qr,
                username=username,
                password=password
            )
            result["screenshot_path"] = attendance_result["screenshot_path"]
            logger.info(f"✓ Attendance marked successfully")
            
            # Step 2: Save to Airtable
            logger.info("Step 2: Saving to Airtable...")
            record_id = self.airtable.create_record(
                module_name=module_name,
                original_qr=morning_qr,
                evening_qr=evening_qr,
                status="success"
            )
            result["airtable_record_id"] = record_id
            logger.info(f"✓ Airtable record created: {record_id}")
            
            result["success"] = True
            result["message"] = "Evening attendance marked successfully"
            
            logger.info("=== Phase 2 Complete ===")
            return result
            
        except Exception as e:
            error_msg = f"Evening attendance marking failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["message"] = error_msg
            
            # Try to save error to Airtable
            try:
                self.airtable.create_record(
                    module_name=module_name,
                    original_qr=morning_qr,
                    evening_qr=evening_qr,
                    status="failed"
                )
            except:
                pass
            
            raise Exception(error_msg)
    
    @log_function_call
    def generate_qr_only(self, url: str, label: str = "QR Code") -> str:
        """
        Generate QR code image only (no attendance marking)
        
        Args:
            url: URL to encode
            label: Label for QR code
            
        Returns:
            Path to generated QR image
        """
        
        logger.info(f"Generating QR code only for: {url}")
        return self.qr_gen.generate_qr_code(url, label_text=label)


# Singleton instance
qr_service = QRService()

__all__ = ["qr_service", "QRService"]