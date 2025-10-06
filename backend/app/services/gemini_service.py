"""
Gemini AI Service
Handles QR code conversion using Gemini 2.0 Flash model
"""

import os
import re
import random
from typing import Optional, Tuple
from google import genai
from ..config import settings
from ..logging_config import logger, log_function_call


class GeminiService:
    """Service for interacting with Gemini AI model"""
    
    def __init__(self):
        """Initialize Gemini client"""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL
        logger.info(f"Gemini Service initialized with model: {self.model}")
    
    @log_function_call
    def convert_expired_qr(self, qr_link: str) -> str:
        """
        Convert expired QR code by modifying the last digit before underscore
        Uses DIRECT digit manipulation instead of AI to ensure accuracy
        
        Args:
            qr_link: Original QR code link
            
        Returns:
            Converted QR code link
            
        Raises:
            ValueError: If QR link format is invalid
        """
        
        logger.info(f"Converting expired QR code: {qr_link}")
        
        # Extract ID from URL
        match = re.search(r'id=([^&]+)', qr_link)
        if not match:
            raise ValueError("Invalid QR link format - no ID found")
        
        original_id = match.group(1)
        logger.debug(f"Extracted ID: {original_id}")
        
        # Parse ID components
        parts = original_id.split('_')
        if len(parts) != 2:
            raise ValueError("Invalid ID format - expected format: XXXXX_YYYYY")
        
        first_part, second_part = parts
        
        # Validate that first_part is numeric
        if not first_part.isdigit():
            raise ValueError(f"Invalid first part - must be numeric: {first_part}")
        
        # Get the last digit before underscore
        last_digit = int(first_part[-1])
        logger.info(f"Current last digit before underscore: {last_digit}")
        
        # Generate a different random digit (0-9, but not the current digit)
        available_digits = [d for d in range(10) if d != last_digit]
        new_last_digit = random.choice(available_digits)
        
        logger.info(f"Changing last digit from {last_digit} to {new_last_digit}")
        
        # Construct new ID by replacing only the last digit
        new_first_part = first_part[:-1] + str(new_last_digit)
        new_id = f"{new_first_part}_{second_part}"
        
        # Construct new QR link
        converted_link = f"https://students.nsbm.ac.lk/attendence/index.php?id={new_id}"
        
        logger.info(f"Successfully converted QR:")
        logger.info(f"  Original ID: {original_id}")
        logger.info(f"  New ID:      {new_id}")
        logger.info(f"  Changed:     {first_part} → {new_first_part}")
        logger.info(f"  Link:        {converted_link}")
        
        return converted_link
    
    @log_function_call
    def convert_expired_qr_with_ai(self, qr_link: str) -> str:
        """
        ALTERNATIVE: Convert expired QR using AI (less reliable)
        This method is kept for reference but not used by default
        
        Args:
            qr_link: Original QR code link
            
        Returns:
            Converted QR code link
        """
        
        logger.info(f"Converting expired QR code using AI: {qr_link}")
        
        # Extract ID from URL
        match = re.search(r'id=([^&]+)', qr_link)
        if not match:
            raise ValueError("Invalid QR link format - no ID found")
        
        original_id = match.group(1)
        parts = original_id.split('_')
        
        if len(parts) != 2:
            raise ValueError("Invalid ID format - expected format: XXXXX_YYYYY")
        
        first_part, second_part = parts
        last_digit = first_part[-1]
        
        # Use direct method first, then optionally validate with AI
        direct_result = self.convert_expired_qr(qr_link)
        
        # Create AI prompt for validation/alternative
        prompt = f"""Generate a valid NSBM attendance QR code by changing ONLY the last digit before the underscore.

Original: {qr_link}
Original ID: {original_id}

Rules:
1. Change ONLY the digit at position {len(first_part)-1} (currently: {last_digit})
2. Change it to a different digit (0-9, but not {last_digit})
3. Keep everything else EXACTLY the same
4. Suffix after underscore stays: {second_part}

Output ONLY the complete URL, nothing else."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            ai_result = response.text.strip()
            
            # Extract URL from response
            url_match = re.search(r'https://students\.nsbm\.ac\.lk/attendence/index\.php\?id=[0-9_]+', ai_result)
            if url_match:
                ai_result = url_match.group(0)
            
            logger.info(f"AI suggested: {ai_result}")
            logger.info(f"Direct method: {direct_result}")
            
            # Use direct method as it's more reliable
            return direct_result
            
        except Exception as e:
            logger.warning(f"AI validation failed: {str(e)}")
            # Return direct method result anyway
            return direct_result
    
    @log_function_call
    def convert_expired_qr_specific_digit(self, qr_link: str, new_digit: int) -> str:
        """
        Convert expired QR code to a specific digit
        Useful for testing or when you know the exact digit needed
        
        Args:
            qr_link: Original QR code link
            new_digit: Specific digit to use (0-9)
            
        Returns:
            Converted QR code link
        """
        
        if not 0 <= new_digit <= 9:
            raise ValueError("new_digit must be between 0 and 9")
        
        logger.info(f"Converting QR to specific digit: {new_digit}")
        
        # Extract ID
        match = re.search(r'id=([^&]+)', qr_link)
        if not match:
            raise ValueError("Invalid QR link format")
        
        original_id = match.group(1)
        parts = original_id.split('_')
        
        if len(parts) != 2:
            raise ValueError("Invalid ID format")
        
        first_part, second_part = parts
        
        # Replace last digit with specific digit
        new_first_part = first_part[:-1] + str(new_digit)
        new_id = f"{new_first_part}_{second_part}"
        converted_link = f"https://students.nsbm.ac.lk/attendence/index.php?id={new_id}"
        
        logger.info(f"Converted to specific digit: {original_id} → {new_id}")
        
        return converted_link
    
    @log_function_call
    def convert_expired_qr_multiple(self, qr_link: str, count: int = 5) -> list:
        """
        Generate multiple variations by changing the last digit
        Useful for trying different QR codes if one doesn't work
        
        Args:
            qr_link: Original QR code link
            count: Number of variations to generate (max 9)
            
        Returns:
            List of converted QR code links
        """
        
        count = min(count, 9)  # Maximum 9 variations (0-9 excluding original)
        
        logger.info(f"Generating {count} QR code variations")
        
        # Extract ID
        match = re.search(r'id=([^&]+)', qr_link)
        if not match:
            raise ValueError("Invalid QR link format")
        
        original_id = match.group(1)
        parts = original_id.split('_')
        
        if len(parts) != 2:
            raise ValueError("Invalid ID format")
        
        first_part, second_part = parts
        original_last_digit = int(first_part[-1])
        
        # Generate all possible digits except original
        available_digits = [d for d in range(10) if d != original_last_digit]
        random.shuffle(available_digits)
        selected_digits = available_digits[:count]
        
        variations = []
        for digit in selected_digits:
            new_first_part = first_part[:-1] + str(digit)
            new_id = f"{new_first_part}_{second_part}"
            converted_link = f"https://students.nsbm.ac.lk/attendence/index.php?id={new_id}"
            variations.append(converted_link)
        
        logger.info(f"Generated {len(variations)} variations")
        for i, var in enumerate(variations, 1):
            logger.debug(f"  Variation {i}: {var}")
        
        return variations
    
    @log_function_call
    def create_evening_qr(self, morning_qr_link: str) -> str:
        """
        Create evening session QR code from morning session QR code
        
        Args:
            morning_qr_link: Morning session QR link
            
        Returns:
            Evening session QR link
            
        Raises:
            ValueError: If QR link format is invalid
        """
        
        logger.info(f"Creating evening QR from morning QR: {morning_qr_link}")
        
        # Extract ID from URL
        match = re.search(r'id=([^&]+)', morning_qr_link)
        if not match:
            raise ValueError("Invalid QR link format - no ID found")
        
        original_id = match.group(1)
        parts = original_id.split('_')
        
        if len(parts) != 2:
            raise ValueError("Invalid ID format - expected format: XXXXX_YYYYY")
        
        first_part, second_part = parts
        
        try:
            # Add the evening offset to the first part
            morning_number = int(first_part)
            evening_number = morning_number + settings.EVENING_OFFSET
            
            # Construct evening QR link
            evening_id = f"{evening_number}_{second_part}"
            evening_qr_link = f"https://students.nsbm.ac.lk/attendence/index.php?id={evening_id}"
            
            logger.info(f"Evening QR created: {original_id} -> {evening_id}")
            logger.info(f"Applied offset: +{settings.EVENING_OFFSET}")
            
            return evening_qr_link
            
        except ValueError as e:
            logger.error(f"Failed to parse QR ID numbers: {str(e)}")
            raise ValueError(f"Invalid QR ID format - first part must be numeric: {first_part}")
        except Exception as e:
            logger.error(f"Evening QR creation failed: {str(e)}", exc_info=True)
            raise Exception(f"Failed to create evening QR: {str(e)}")


# Singleton instance
gemini_service = GeminiService()

__all__ = ["gemini_service", "GeminiService"]