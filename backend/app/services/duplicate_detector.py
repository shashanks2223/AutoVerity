import imagehash
from PIL import Image
from sqlalchemy.orm import Session
import logging

from app import models
from app.config import settings

logger = logging.getLogger("app.services.duplicate_detector")


class DuplicateDetector:
    @staticmethod
    def compute_hash(image_path: str) -> str:
        """
        Computes the perceptual hash (pHash) of an image.
        pHash is resilient to resizing, compression changes, and minor color adjustments.
        """
        try:
            with Image.open(image_path) as img:
                h = imagehash.phash(img)
                return str(h)
        except Exception as e:
            logger.error(f"Failed to compute perceptual hash for {image_path}: {str(e)}")
            raise e

    @staticmethod
    def find_duplicate(
        db: Session,
        current_job_id: str,
        current_hash_str: str
    ) -> tuple[str | None, float]:
        """
        Compares the current job's pHash with all completed jobs in the database.
        Returns:
            (duplicate_job_id, hamming_distance) if duplicate found, else (None, 0.0)
            
        Limitations of pHash:
            1. It is not a cryptographic hash (like MD5/SHA256). Two identical looking images with different metadata 
               or slight noise will have the same or very close pHash.
            2. Collisions are theoretically possible but rare. High similarity (low Hamming distance) means 
               the images are visually near-identical.
            3. Heavy cropping or rotating will significantly alter the pHash and might bypass detection.
        """
        if not current_hash_str:
            return None, 0.0

        try:
            current_hash = imagehash.hex_to_hash(current_hash_str)
        except Exception as e:
            logger.error(f"Invalid current hash string: {current_hash_str}. Error: {str(e)}")
            return None, 0.0

        # Query all completed jobs that have an image hash, excluding the current job itself
        jobs = db.query(models.ImageProcessingJob).filter(
            models.ImageProcessingJob.status == "completed",
            models.ImageProcessingJob.image_hash.isnot(None),
            models.ImageProcessingJob.id != current_job_id
        ).all()

        for job in jobs:
            try:
                db_hash = imagehash.hex_to_hash(job.image_hash)
                # Hamming distance subtraction computes the number of differing bits
                distance = current_hash - db_hash
                
                # If distance is within the threshold, treat as a duplicate
                if distance <= settings.DUPLICATE_THRESHOLD:
                    logger.info(f"Duplicate found! Job {current_job_id} matches Job {job.id} with distance {distance}")
                    return str(job.id), float(distance)
            except Exception as e:
                logger.warning(f"Failed to compare hash for job {job.id}: {str(e)}")
                continue

        return None, 0.0
