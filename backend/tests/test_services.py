import os
import pytest
from PIL import Image, ImageDraw
from unittest.mock import MagicMock

from app.services.image_validator import ImageValidator
from app.services.blur_detector import BlurDetector
from app.services.brightness_detector import BrightnessDetector
from app.services.plate_validator import PlateValidator
from app.services.duplicate_detector import DuplicateDetector
from app.services.ocr_service import OcrService


@pytest.fixture
def temp_images(tmp_path):
    """Fixture to generate temporary test images."""
    # 1. Standard sharp white image
    sharp_path = os.path.join(tmp_path, "sharp.jpg")
    img_sharp = Image.new("RGB", (300, 300), "white")
    draw = ImageDraw.Draw(img_sharp)
    # Draw high contrast checkerboard pattern
    for i in range(0, 300, 30):
        for j in range(0, 300, 30):
            if (i // 30 + j // 30) % 2 == 0:
                draw.rectangle([i, j, i + 30, j + 30], fill="black")
    img_sharp.save(sharp_path)

    # 2. Solid blurry image (variance of solid color is 0)
    blurry_path = os.path.join(tmp_path, "blurry.jpg")
    img_blurry = Image.new("RGB", (300, 300), "gray")
    img_blurry.save(blurry_path)

    # 3. Dark image
    dark_path = os.path.join(tmp_path, "dark.jpg")
    img_dark = Image.new("RGB", (300, 300), "black")
    img_dark.save(dark_path)

    # 4. Small image
    small_path = os.path.join(tmp_path, "small.jpg")
    img_small = Image.new("RGB", (50, 50), "white")
    img_small.save(small_path)

    # 5. Skewed aspect ratio image
    skewed_path = os.path.join(tmp_path, "skewed.jpg")
    img_skewed = Image.new("RGB", (600, 50), "white")
    img_skewed.save(skewed_path)

    return {
        "sharp": sharp_path,
        "blurry": blurry_path,
        "dark": dark_path,
        "small": small_path,
        "skewed": skewed_path
    }


def test_image_validator(temp_images):
    # Test valid image
    w, h, valid = ImageValidator.validate(temp_images["sharp"])
    assert w == 300
    assert h == 300
    assert valid is True

    # Test small image
    w, h, valid = ImageValidator.validate(temp_images["small"])
    assert valid is False

    # Test skewed ratio image
    w, h, valid = ImageValidator.validate(temp_images["skewed"])
    assert valid is False


def test_blur_detector(temp_images):
    # Sharp checkerboard should have high variance
    score, is_blurry = BlurDetector.analyze(temp_images["sharp"])
    assert score > 100
    assert is_blurry is False

    # Solid color should have 0 variance (blurry)
    score, is_blurry = BlurDetector.analyze(temp_images["blurry"])
    assert score == 0.0
    assert is_blurry is True


def test_brightness_detector(temp_images):
    # White checkerboard should have high average brightness
    avg, is_low = BrightnessDetector.analyze(temp_images["sharp"])
    assert avg > 70
    assert is_low is False

    # Black image should have 0 brightness (low light)
    avg, is_low = BrightnessDetector.analyze(temp_images["dark"])
    assert avg == 0.0
    assert is_low is True


def test_plate_validator():
    # Test valid standard plates
    num, valid, conf = PlateValidator.validate("KA 01 AB 1234", "KA01AB1234", 0.9)
    assert num == "KA01AB1234"
    assert valid is True
    assert conf == 0.9

    num, valid, conf = PlateValidator.validate("DL-3C-A-1234", "DL3CA1234", 0.8)
    assert num == "DL3CA1234"
    assert valid is True
    assert conf == 0.8

    # Test valid BH plate
    num, valid, conf = PlateValidator.validate("22 BH 8765 AB", "22BH8765AB", 0.95)
    assert num == "22BH8765AB"
    assert valid is True
    assert conf == 0.95

    # Test invalid format (returns clean text but format_valid=False)
    num, valid, conf = PlateValidator.validate("XYZ 1234", "XYZ1234", 0.5)
    assert num == "XYZ1234"
    assert valid is False


def test_duplicate_detector(temp_images, db):
    # Compute hashes
    hash1 = DuplicateDetector.compute_hash(temp_images["sharp"])
    hash2 = DuplicateDetector.compute_hash(temp_images["blurry"])
    
    assert hash1 is not None
    assert hash2 is not None
    
    # Identical files should match
    hash1_again = DuplicateDetector.compute_hash(temp_images["sharp"])
    assert hash1 == hash1_again


def test_ocr_service_mocked(temp_images, monkeypatch):
    # Mock pytesseract.image_to_data
    mock_data = {
        "text": ["", "KA", "01", "", "AB", "1234", ""],
        "conf": [-1, 90, 85, -1, 95, 80, -1]
    }
    monkeypatch.setattr(
        "pytesseract.image_to_data",
        lambda img, output_type=None: mock_data
    )

    raw, norm, conf = OcrService.extract_text(temp_images["sharp"])
    assert raw == "KA 01 AB 1234"
    assert norm == "KA01AB1234"
    assert conf == 0.88  # Average of 0.90, 0.85, 0.95, 0.80
