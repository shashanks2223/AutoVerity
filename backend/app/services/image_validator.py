from PIL import Image
import logging

logger = logging.getLogger("app.services.image_validator")


class ImageValidator:
    @staticmethod
    def validate(image_path: str) -> tuple[int, int, bool]:
        """
        Reads the image dimensions and validates if they meet basic sanity requirements.
        Returns:
            (width, height, is_valid)
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Check minimum dimensions (e.g. at least 200x200 pixels)
                if width < 200 or height < 200:
                    logger.warning(f"Image dimensions too small: {width}x{height}")
                    return width, height, False

                # Check for extremely skewed aspect ratios (width/height ratio)
                aspect_ratio = width / height
                if aspect_ratio < 0.2 or aspect_ratio > 5.0:
                    logger.warning(f"Extreme aspect ratio: {aspect_ratio:.2f} ({width}x{height})")
                    return width, height, False
                
                return width, height, True
        except Exception as e:
            logger.error(f"Image validation exception for {image_path}: {str(e)}")
            return 0, 0, False
