import cv2
import logging
from app.config import settings

logger = logging.getLogger("app.services.brightness_detector")


class BrightnessDetector:
    @staticmethod
    def analyze(image_path: str) -> tuple[float, bool]:
        """
        Calculates the mean pixel brightness of the image in grayscale (0 to 255).
        Returns:
            (average_brightness, is_low_light)
        """
        try:
            # Read image as grayscale
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                logger.error(f"Failed to read image for brightness analysis: {image_path}")
                return 0.0, True

            # Calculate average pixel intensity
            average_brightness = float(img.mean())
            
            # If the average brightness is less than the threshold, it is low light
            is_low_light = bool(average_brightness < settings.BRIGHTNESS_THRESHOLD)
            
            return round(average_brightness, 2), is_low_light
        except Exception as e:
            logger.error(f"Error during brightness detection on {image_path}: {str(e)}")
            return 0.0, True
