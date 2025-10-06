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
            
            # Create QR code instance with better settings
            qr = qrcode.QRCode(
                version=None,  # Auto-determine version based on data length
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=12,  # Increased from 10 for better clarity
                border=6,  # Increased border for better scanning
            )
            
            qr.add_data(url)
            qr.make(fit=True)  # Let it auto-fit to the data
            
            # Generate QR code image
            qr_image = qr.make_image(
                fill_color="black", 
                back_color="white"
            )
            
            # Convert to RGB mode to ensure compatibility
            if qr_image.mode != 'RGB':
                qr_image = qr_image.convert('RGB')
            
            logger.info(f"QR code size: {qr_image.size}")
            
            # Add label if requested
            if add_label:
                qr_image = self._add_label_to_qr(qr_image, label_text or "NSBM Attendance QR")
            
            # Save image with high quality
            qr_image.save(str(output_path), format='PNG', optimize=False)
            
            logger.info(f"QR code generated successfully: {output_path}")
            logger.info(f"Final image size: {qr_image.size}")
            
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
            # Ensure QR image is in RGB mode
            if qr_image.mode != 'RGB':
                qr_image = qr_image.convert('RGB')
            
            # Create new image with extra space for label
            label_height = 80  # Increased for better spacing
            padding = 20  # Top padding
            new_height = qr_image.height + label_height + padding
            new_width = qr_image.width
            
            # Create new image with white background
            new_image = Image.new('RGB', (new_width, new_height), color='white')
            
            # Paste QR code with padding at top
            new_image.paste(qr_image, (0, padding))
            
            # Add label text
            draw = ImageDraw.Draw(new_image)
            
            # Try to use a nice font, fall back to default if not available
            try:
                # Try multiple font options
                font = None
                font_paths = [
                    "/System/Library/Fonts/Supplemental/Arial.ttf",  # macOS
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                    "C:\\Windows\\Fonts\\arial.ttf",  # Windows
                    "arial.ttf"
                ]
                
                for font_path in font_paths:
                    try:
                        font = ImageFont.truetype(font_path, 24)
                        break
                    except:
                        continue
                
                if font is None:
                    font = ImageFont.load_default()
                    
            except Exception as e:
                logger.warning(f"Could not load custom font: {e}")
                font = ImageFont.load_default()
            
            # Calculate text position (centered)
            # Use textbbox for accurate text dimensions
            bbox = draw.textbbox((0, 0), label_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = (new_width - text_width) // 2
            text_y = qr_image.height + padding + 15
            
            # Draw text shadow for better visibility
            shadow_offset = 2
            draw.text(
                (text_x + shadow_offset, text_y + shadow_offset), 
                label_text, 
                fill='#cccccc', 
                font=font
            )
            
            # Draw main text
            draw.text((text_x, text_y), label_text, fill='black', font=font)
            
            logger.info(f"Label added to QR code: '{label_text}'")
            
            return new_image
            
        except Exception as e:
            logger.warning(f"Failed to add label to QR code: {str(e)}")
            # Return original QR image if label addition fails
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
    
    @log_function_call
    def verify_qr_readable(self, image_path: str) -> bool:
        """
        Verify that generated QR code is readable
        
        Args:
            image_path: Path to QR code image
            
        Returns:
            True if QR code is readable, False otherwise
        """
        try:
            from pyzbar.pyzbar import decode
            
            img = Image.open(image_path)
            decoded_objects = decode(img)
            
            if decoded_objects:
                logger.info(f"QR code verified as readable: {image_path}")
                return True
            else:
                logger.warning(f"QR code could not be decoded: {image_path}")
                return False
                
        except ImportError:
            logger.warning("pyzbar not installed, skipping QR verification")
            return True  # Assume success if can't verify
        except Exception as e:
            logger.error(f"QR verification failed: {str(e)}")
            return False


# Singleton instance
qr_generator_service = QRGeneratorService()

__all__ = ["qr_generator_service", "QRGeneratorService"]