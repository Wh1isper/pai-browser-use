"""Test image processing utilities."""

from __future__ import annotations

import io

from PIL import Image
from pydantic_ai import BinaryContent

from pai_browser_use._image_utils import split_image_data


def test_split_image_data_short_image():
    """Test split_image_data with image shorter than max_height."""
    # Create a small test image
    img = Image.new("RGB", (800, 600), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # Split with larger max_height
    segments = split_image_data(img_bytes.getvalue(), max_height=1000)

    # Should return single segment
    assert len(segments) == 1
    assert isinstance(segments[0], BinaryContent)
    assert segments[0].media_type == "image/png"


def test_split_image_data_long_image():
    """Test split_image_data with long image that needs splitting."""
    # Create a tall test image
    img = Image.new("RGB", (800, 8000), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # Split with smaller max_height
    segments = split_image_data(img_bytes.getvalue(), max_height=4096, overlap=50)

    # Should return multiple segments
    assert len(segments) > 1
    assert len(segments) <= 20  # Max segments limit

    for segment in segments:
        assert isinstance(segment, BinaryContent)
        assert segment.media_type == "image/png"

        # Verify each segment is valid image
        seg_img = Image.open(io.BytesIO(segment.data))
        assert seg_img.size[0] == 800
        assert seg_img.size[1] <= 4096


def test_split_image_data_different_formats():
    """Test split_image_data with different image formats."""
    img = Image.new("RGB", (800, 600), color="green")

    for media_type in ["image/png", "image/jpeg", "image/webp"]:
        img_bytes = io.BytesIO()
        format_name = media_type.split("/")[1].upper()
        if format_name == "JPG":
            format_name = "JPEG"
        img.save(img_bytes, format=format_name)
        img_bytes.seek(0)

        segments = split_image_data(img_bytes.getvalue(), media_type=media_type)

        assert len(segments) == 1
        assert segments[0].media_type == media_type


def test_split_image_data_invalid_format():
    """Test split_image_data with invalid media type fallback."""
    img = Image.new("RGB", (800, 600), color="yellow")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # Use invalid media type - should fallback to PNG
    segments = split_image_data(img_bytes.getvalue(), media_type="image/invalid")

    assert len(segments) == 1
    assert isinstance(segments[0], BinaryContent)


def test_split_image_data_with_overlap():
    """Test split_image_data overlap functionality."""
    # Create tall image
    img = Image.new("RGB", (400, 5000), color="purple")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    segments = split_image_data(img_bytes.getvalue(), max_height=2000, overlap=100)

    # Should have multiple segments
    assert len(segments) >= 2
