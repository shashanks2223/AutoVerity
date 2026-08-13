import re
import logging

logger = logging.getLogger("app.services.plate_validator")

# Regex for standard state-based Indian registration formats
# Examples: KA01AB1234, DL3CA1234, MH12AB1234, AP21A1234
# Breakdown: 
#   [A-Z]{2} : State code (e.g. KA)
#   [0-9]{1,2} : District code (e.g. 01, 3)
#   [A-Z]{1,3} : Running letters (e.g. AB, C, AA)
#   [0-9]{1,4} : Unique code number (e.g. 1234, 5)
STATE_PLATE_REGEX = re.compile(r'[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{1,4}')

# Regex for Bharat (BH) series registration formats
# Examples: 21BH1234A, 22BH8765AB
# Breakdown:
#   [0-9]{2} : Year of registration (e.g. 21)
#   BH : Bharat series identifier
#   [0-9]{4} : 4 digit number
#   [A-Z]{1,2} : 1 or 2 letters
BH_PLATE_REGEX = re.compile(r'[0-9]{2}BH[0-9]{4}[A-Z]{1,2}')


class PlateValidator:
    @staticmethod
    def validate(
        raw_text: str | None,
        normalized_text: str | None,
        confidence: float | None
    ) -> tuple[str | None, bool, float | None]:
        """
        Extracts and validates Indian vehicle registration plate formats from OCR output.
        NOTE: This only checks structural compliance with Indian plate formatting rules.
        It does NOT contact RTO/VAHAN APIs to verify if the vehicle actually exists.
        
        Returns:
            (detected_number, format_valid, confidence)
        """
        if not normalized_text:
            return None, False, None

        # Clean string from common misread OCR noise, ensuring uppercase
        clean_text = "".join(char for char in normalized_text if char.isalnum()).upper()

        # Check for Standard State Plate match
        state_match = STATE_PLATE_REGEX.search(clean_text)
        if state_match:
            detected_number = state_match.group(0)
            logger.info(f"Matched Indian state registration format: {detected_number}")
            return detected_number, True, confidence

        # Check for BH Series match
        bh_match = BH_PLATE_REGEX.search(clean_text)
        if bh_match:
            detected_number = bh_match.group(0)
            logger.info(f"Matched Indian BH-series registration format: {detected_number}")
            return detected_number, True, confidence

        # If no format matched, return the cleaned normalized string up to a reasonable length
        logger.info(f"OCR text '{clean_text}' does not match Indian registration format rules.")
        return clean_text[:15], False, confidence
