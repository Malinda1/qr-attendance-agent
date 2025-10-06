"""
Airtable Service
Handles all interactions with Airtable database
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pyairtable import Api
from ..config import settings
from ..logging_config import logger, log_function_call


class AirtableService:
    """Service for interacting with Airtable"""
    
    def __init__(self):
        """Initialize Airtable API client"""
        self.api = Api(settings.AIRTABLE_API_KEY)
        self.table = self.api.table(settings.AIRTABLE_BASE_ID, settings.AIRTABLE_TABLE_NAME)
        logger.info(f"Airtable Service initialized - Base: {settings.AIRTABLE_BASE_ID}")
    
    @log_function_call
    def create_record(
        self,
        module_name: str,
        original_qr: str,
        converted_qr: Optional[str] = None,
        evening_qr: Optional[str] = None,
        status: str = "success"
    ) -> str:
        """
        Create a new record in Airtable
        
        Args:
            module_name: Name of the module/course
            original_qr: Original QR code link
            converted_qr: Converted QR code link (optional)
            evening_qr: Evening session QR code link (optional)
            status: Status of the operation
            
        Returns:
            Record ID from Airtable
            
        Raises:
            Exception: If record creation fails
        """
        
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            record_data = {
                "Module Name": module_name,
                "Original QR Link": original_qr,
                "Date": current_date,
                "Timestamp": current_timestamp,
                "Status": status
            }
            
            if converted_qr:
                record_data["Converted QR Link"] = converted_qr
            
            if evening_qr:
                record_data["Evening QR Link"] = evening_qr
            
            logger.info(f"Creating Airtable record for module: {module_name}")
            logger.debug(f"Record data: {record_data}")
            
            record = self.table.create(record_data)
            record_id = record['id']
            
            logger.info(f"Airtable record created successfully - ID: {record_id}")
            return record_id
            
        except Exception as e:
            logger.error(f"Failed to create Airtable record: {str(e)}", exc_info=True)
            raise Exception(f"Airtable record creation failed: {str(e)}")
    
    @log_function_call
    def update_record(self, record_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing Airtable record
        
        Args:
            record_id: Airtable record ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated record data
            
        Raises:
            Exception: If update fails
        """
        
        try:
            logger.info(f"Updating Airtable record: {record_id}")
            logger.debug(f"Update data: {updates}")
            
            record = self.table.update(record_id, updates)
            
            logger.info(f"Airtable record updated successfully")
            return record
            
        except Exception as e:
            logger.error(f"Failed to update Airtable record: {str(e)}", exc_info=True)
            raise Exception(f"Airtable record update failed: {str(e)}")
    
    @log_function_call
    def get_record(self, record_id: str) -> Dict[str, Any]:
        """
        Retrieve a record from Airtable
        
        Args:
            record_id: Airtable record ID
            
        Returns:
            Record data
            
        Raises:
            Exception: If retrieval fails
        """
        
        try:
            logger.info(f"Retrieving Airtable record: {record_id}")
            record = self.table.get(record_id)
            return record
            
        except Exception as e:
            logger.error(f"Failed to retrieve Airtable record: {str(e)}", exc_info=True)
            raise Exception(f"Airtable record retrieval failed: {str(e)}")
    
    @log_function_call
    def search_records(self, module_name: str) -> list:
        """
        Search records by module name
        
        Args:
            module_name: Module name to search for
            
        Returns:
            List of matching records
        """
        
        try:
            logger.info(f"Searching Airtable records for module: {module_name}")
            
            formula = f"{{Module Name}} = '{module_name}'"
            records = self.table.all(formula=formula)
            
            logger.info(f"Found {len(records)} records for module: {module_name}")
            return records
            
        except Exception as e:
            logger.error(f"Airtable search failed: {str(e)}", exc_info=True)
            return []
    
    @log_function_call
    def get_today_records(self) -> list:
        """
        Get all records created today
        
        Returns:
            List of today's records
        """
        
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            logger.info(f"Retrieving records for date: {today}")
            
            formula = f"{{Date}} = '{today}'"
            records = self.table.all(formula=formula)
            
            logger.info(f"Found {len(records)} records for today")
            return records
            
        except Exception as e:
            logger.error(f"Failed to retrieve today's records: {str(e)}", exc_info=True)
            return []


# Singleton instance
airtable_service = AirtableService()

__all__ = ["airtable_service", "AirtableService"]