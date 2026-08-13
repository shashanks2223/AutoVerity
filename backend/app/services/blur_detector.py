import cv2
import logging
from app.config import settings

logger = logging.getLogger("app.services.blur_detector")


class BlurDetector:
    @staticmethod
    def analyze(image_path: str) -> tuple[float, bool]:
        """
        Computes the variance of the Laplacian operator on the image to measure blur.
        Returns:
            (blur_score, is_blurry)
        """
        try:
            # Read image as grayscale
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                logger.error(f"Failed to read image for blur analysis: {image_path}")
                return 0.0, True

            # Calculate Laplacian variance
            score = cv2.Laplacian(img, cv2.CV_64F).var()
            
            # If the score is less than the threshold, the image is blurry
            is_blurry = bool(score < settings.BLUR_THRESHOLD)
            
            return round(score, 2), is_blurry
        except Exception as e:
            logger.error(f"Error during blur detection on {image_path}: {str(e)}")
            return 0.0, True
