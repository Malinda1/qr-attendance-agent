"""
QR Code Generator Service
Creates QR code images from URLs
"""

import qrcode
from pathlib import Path
from datetime import datetime
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from ..config import settings
from ..logging_config import logger, log_function_call


class QRGeneratorService:
    """Service for generating QR code images"""
    
    def __init__(self):
        """Initialize QR Generator"""
        self.output_dir = settings.QR_CODE_DIR
        logger.info(f"QR Generator initialized - Output dir: {self.output_dir}")
    
    @log_function_call
    def generate_qr_code(
        self,
        url: str,
        filename: Optional[str] = None,
        add_label: bool = True,
        label_text: Optional[str] = None
    ) -> str:
        """
        Generate QR code image from URL
        
        Args:
            url: URL to encode in QR code
            filename: Custom filename (optional, auto-generated if not provided)
            add_label: Whether to add a label below the QR code
            label_text: Custom label text (optional)
            
        Returns:
            Path to generated QR code image
            
        Raises:
            Exception: If QR code generation fails
        """
        
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"qr_code_{timestamp}.png"
            
            # Ensure .png extension
            if not filename.endswith('.png'):
                filename += '.png'
            
            output_path = self.output_dir / filename
            
            logger.info(f"Generating QR code for URL: {url}")
            logger.debug(f"Output path: {output_path}")
            
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            
            qr.add_data(url)
            qr.make(fit=True)
            
            # Generate QR code image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Add label if requested
            if add_label:
                qr_image = self._add_label_to_qr(qr_image, label_text or "NSBM Attendance QR")
            
            # Save image
            qr_image.save(str(output_path))
            
            logger.info(f"QR code generated successfully: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"QR code generation failed: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate QR code: {str(e)}")
    
    def _add_label_to_qr(self, qr_image: Image.Image, label_text: str) -> Image.Image:
        """
        Add text label below QR code
        
        Args:
            qr_image: QR code image
            label_text: Text to add as label
            
        Returns:
            Image with label
        """
        
        try:
            # Create new image with extra space for label
            label_height = 60
            new_height = qr_image.height + label_height
            new_image = Image.new('RGB', (qr_image.width, new_height), 'white')
            
            # Paste QR code
            new_image.paste(qr_image, (0, 0))
            
            # Add label text
            draw = ImageDraw.Draw(new_image)
            
            # Try to use a nice font, fall back to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position (centered)
            bbox = draw.textbbox((0, 0), label_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (qr_image.width - text_width) // 2
            text_y = qr_image.height + 20
            
            # Draw text
            draw.text((text_x, text_y), label_text, fill='black', font=font)
            
            return new_image
            
        except Exception as e:
            logger.warning(f"Failed to add label to QR code: {str(e)}")
            return qr_image
    
    @log_function_call
    def generate_batch_qr_codes(self, urls: list, prefix: str = "qr") -> list:
        """
        Generate multiple QR codes at once
        
        Args:
            urls: List of URLs to generate QR codes for
            prefix: Filename prefix for generated codes
            
        Returns:
            List of paths to generated QR code images
        """
        
        generated_paths = []
        
        for idx, url in enumerate(urls, 1):
            try:
                filename = f"{prefix}_{idx}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                path = self.generate_qr_code(url, filename=filename)
                generated_paths.append(path)
            except Exception as e:
                logger.error(f"Failed to generate QR code {idx}: {str(e)}")
                continue
        
        logger.info(f"Batch generation complete: {len(generated_paths)}/{len(urls)} successful")
        return generated_paths


# Singleton instance
qr_generator_service = QRGeneratorService()

__all__ = ["qr_generator_service", "QRGeneratorService"]