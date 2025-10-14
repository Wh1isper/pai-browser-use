"""Image processing utilities for browser screenshots."""

from __future__ import annotations

import io
from typing import Literal

from PIL import Image
from pydantic_ai import BinaryContent

from pai_browser_use._logger import logger

ImageMediaType = Literal["image/png", "image/jpeg", "image/webp"]

# Media type to PIL format mapping
MEDIA_TYPE_TO_FORMAT: dict[str, str] = {
    "image/png": "PNG",
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/webp": "WEBP",
}


def split_image_data(
    image_bytes: bytes,
    max_height: int = 4096,
    overlap: int = 50,
    media_type: ImageMediaType = "image/png",
) -> list[BinaryContent]:
    """Split a long image into multiple segments for better model understanding.

    Args:
        image_bytes: Original image bytes data
        max_height: Maximum height for each segment (default: 4096px)
        overlap: Overlap pixels between adjacent segments (default: 50px)
        media_type: Image media type

    Returns:
        List of BinaryContent objects, each containing an image segment
    """
    try:
        # Load image from bytes
        with Image.open(io.BytesIO(image_bytes)) as image:
            width, height = image.size

            # If image is not too tall, return as single BinaryContent
            if height <= max_height:
                return [BinaryContent(data=image_bytes, media_type=media_type)]

            segments = []
            step = max_height - overlap
            current_y = 0
            segment_index = 0

            while current_y < height:
                # Calculate segment boundaries
                y_start = current_y
                y_end = min(current_y + max_height, height)

                # Crop the segment
                segment = image.crop((0, y_start, width, y_end))

                # Convert segment to bytes
                segment_bytes = io.BytesIO()

                # Safe format extraction with fallback
                segment_format = MEDIA_TYPE_TO_FORMAT.get(media_type)
                if not segment_format:  # pragma: no cover
                    # Fallback to splitting approach with error handling
                    try:
                        segment_format = media_type.split("/")[1].upper()
                    except (IndexError, AttributeError):  # pragma: no cover
                        segment_format = "PNG"  # Safe default
                        logger.warning(f"Invalid media_type '{media_type}', using PNG as fallback")

                segment.save(segment_bytes, format=segment_format, optimize=True)
                segment_bytes.seek(0)

                # Create BinaryContent for this segment
                segment_content = BinaryContent(data=segment_bytes.getvalue(), media_type=media_type)
                segments.append(segment_content)

                segment_index += 1
                current_y += step

                # Break if we've reached the end
                if y_end >= height:
                    break

            logger.info(f"Split image into {len(segments)} segments (original: {width}x{height}px)")
            return segments

    except Exception as e:  # pragma: no cover
        logger.warning(f"Failed to split image: {e}, returning original image")
        # Return original as fallback
        return [BinaryContent(data=image_bytes, media_type="image/png")]
