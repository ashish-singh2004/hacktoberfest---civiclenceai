"""
CivicLens AI - Visual Grounding & AI Detection Overlay
Renders intuitive bounding box highlights, safety badges, and visual tags
directly onto user-uploaded street photographs.
"""

from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


# Color palette for urgency tiers
TIER_COLORS = {
    "CRITICAL": (239, 68, 68),    # Red
    "HIGH": (249, 115, 22),       # Orange
    "MEDIUM": (234, 179, 8),      # Amber/Yellow
    "LOW": (34, 197, 94),         # Green
}


def draw_obstacle_overlay(
    image: Image.Image,
    issue_type: str,
    label: str,
    tier: str = "HIGH",
    box: Optional[Tuple[int, int, int, int]] = None
) -> Image.Image:
    """
    Overlays a highlighted bounding box, corner brackets, and an information badge
    onto the street photograph to show exactly where the barrier was detected.
    """
    img = image.convert("RGBA")
    width, height = img.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    color_rgb = TIER_COLORS.get(tier.upper(), (249, 115, 22))
    outline_color = (*color_rgb, 240)
    fill_color = (*color_rgb, 45)  # Soft translucent tint

    # If no specific coordinates supplied, highlight the focal lower-middle region
    if box is None:
        left = int(width * 0.15)
        top = int(height * 0.35)
        right = int(width * 0.85)
        bottom = int(height * 0.85)
    else:
        left, top, right, bottom = box

    # Draw rounded rectangle highlight
    draw.rectangle([left, top, right, bottom], outline=outline_color, width=4, fill=fill_color)

    # Draw corner brackets for tech aesthetic
    corner_len = min(30, int(width * 0.05))
    bracket_color = (*color_rgb, 255)
    # Top-Left
    draw.line([(left, top), (left + corner_len, top)], fill=bracket_color, width=6)
    draw.line([(left, top), (left, top + corner_len)], fill=bracket_color, width=6)
    # Top-Right
    draw.line([(right, top), (right - corner_len, top)], fill=bracket_color, width=6)
    draw.line([(right, top), (right, top + corner_len)], fill=bracket_color, width=6)
    # Bottom-Left
    draw.line([(left, bottom), (left + corner_len, bottom)], fill=bracket_color, width=6)
    draw.line([(left, bottom), (left, bottom - corner_len)], fill=bracket_color, width=6)
    # Bottom-Right
    draw.line([(right, bottom), (right - corner_len, bottom)], fill=bracket_color, width=6)
    draw.line([(right, bottom), (right, bottom - corner_len)], fill=bracket_color, width=6)

    # Render top label pill banner
    badge_text = f" AI DETECTED: {label.upper()} ({tier.upper()}) "
    try:
        # Load default font
        font = ImageFont.load_default()
    except Exception:
        font = None

    badge_top = max(10, top - 32)
    badge_right = min(width - 10, left + len(badge_text) * 8 + 20)
    draw.rectangle([left, badge_top, badge_right, badge_top + 24], fill=(*color_rgb, 230))
    draw.text((left + 8, badge_top + 5), badge_text, fill=(255, 255, 255, 255), font=font)

    # Alpha composite
    annotated = Image.alpha_composite(img, overlay)
    return annotated.convert("RGB")
