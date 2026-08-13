import pytesseract
from PIL import Image
import logging

logger = logging.getLogger("app.services.ocr_service")


class OcrService:
    @staticmethod
    def extract_text(image_path: str) -> tuple[str | None, str | None, float | None]:
        """
        Runs Tesseract OCR on the image at image_path.
        Returns:
            (raw_text, normalized_text, confidence)
            All returned values are None if OCR fails or text is not found.
        """
        try:
            with Image.open(image_path) as img:
                # Get detailed data including word confidences
                try:
                    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                except pytesseract.TesseractNotFoundError:
                    logger.warning("Tesseract binary not found. OCR is falling back to empty result.")
                    return None, None, None
                except Exception as e:
                    logger.error(f"Pytesseract failed to execute: {str(e)}")
                    return None, None, None

                words = []
                confidences = []
                
                n_items = len(data.get("text", []))
                for i in range(n_items):
                    text_val = data["text"][i].strip()
                    conf_val = data["conf"][i]
                    
                    if text_val:
                        words.append(text_val)
                        # Tesseract uses -1 to represent structural blocks (non-words)
                        try:
                            conf_float = float(conf_val)
                            if conf_float >= 0:
                                confidences.append(conf_float / 100.0)
                        except (ValueError, TypeError):
                            pass

                if not words:
                    return None, None, None

                raw_text = " ".join(words).strip()
                
                # Normalize text: strip whitespace, keep alphanumeric characters, uppercase
                normalized_text = "".join(char for char in raw_text if char.isalnum()).upper()
                
                # Calculate mean confidence of the detected words
                if confidences:
                    avg_confidence = round(sum(confidences) / len(confidences), 2)
                else:
                    avg_confidence = None

                return raw_text, normalized_text, avg_confidence
                
        except Exception as e:
            logger.error(f"Failsafe OCR Service exception: {str(e)}")
            return None, None, None
