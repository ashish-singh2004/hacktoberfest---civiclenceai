"""
CivicLens AI - Gemma 4 Multimodal Service
Connects to Google GenAI / Gemma 4 multimodal API to inspect street photographs,
detect pedestrian accessibility obstacles, enforce structured JSON schemas,
and compute deterministic priority scores.

NON-NEGOTIABLE PRINCIPLES:
- No synthetic hallucinations: uses real model inference.
- Never silently fall back to fake output.
- Bounded retries and explicit error propagation.
- Output strictly validated via Pydantic.
"""

import os
import json
import time
import logging
from typing import Optional, Tuple
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv

# Load local environment variables from .env
load_dotenv()

from schemas import AuditAnalysisResult, AccessibilityIssue
from prompts import SYSTEM_AUDIT_PROMPT, build_audit_prompt
from priority_engine import calculate_priority_score
from demo_data import get_demo_audit_cases

logger = logging.getLogger("civiclens.gemma_service")

# Default configurations
DEFAULT_MODEL_ID = os.getenv("GEMMA_MODEL_ID", "gemini-2.5-flash")
MAX_RETRIES = int(os.getenv("GEMMA_MAX_RETRIES", "3"))
TIMEOUT_SECONDS = int(os.getenv("GEMMA_TIMEOUT_SECONDS", "45"))


class GemmaAPIError(Exception):
    """Raised when the Gemma 4 / GenAI API encounters an error."""
    pass


class ImageValidationError(Exception):
    """Raised when an uploaded image fails validation."""
    pass


def validate_image(image: Image.Image) -> Tuple[bool, Optional[str]]:
    """
    Validates an uploaded image for accessibility audit requirements:
    - Minimum and maximum dimensions
    - Valid color mode
    - Readability check
    """
    if image is None:
        return False, "No image provided."

    width, height = image.size
    if width < 150 or height < 150:
        return False, f"Image dimensions ({width}x{height}) are too small for visual audit. Minimum is 150x150."

    if width > 10000 or height > 10000:
        return False, f"Image dimensions ({width}x{height}) exceed maximum allowed 10000x10000."

    # Convert to RGB if needed (e.g. RGBA or P mode)
    if image.mode not in ("RGB", "RGBA", "L"):
        return False, f"Unsupported image color mode '{image.mode}'. Please upload JPG, JPEG, or PNG."

    return True, None


def _clean_json_response(raw_text: str) -> str:
    """Strips markdown fences or preamble from model output to ensure clean JSON."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def analyze_street_image(
    image: Image.Image,
    citizen_notes: str = "",
    api_key: Optional[str] = None,
    model_id: Optional[str] = None,
    force_demo_mode: bool = False
) -> AuditAnalysisResult:
    """
    Sends a street photograph to Gemma 4 for multimodal pedestrian accessibility audit.

    Args:
        image: PIL Image instance of the street/sidewalk scene.
        citizen_notes: Optional user-entered context about the location.
        api_key: Optional override for GEMMA_API_KEY.
        model_id: Optional override for GEMMA_MODEL_ID.
        force_demo_mode: If True, returns an explicitly labeled sample record.

    Returns:
        AuditAnalysisResult containing validated issues, impacts, and priority scores.

    Raises:
        GemmaAPIError: On credential missing, API failure, or unparseable output.
        ImageValidationError: If the image fails dimension or mode checks.
    """
    # 1. Explicit Demo Mode Handshake
    if force_demo_mode:
        demo_cases = get_demo_audit_cases()
        # Return representative demo case (Case 1: broken sidewalk & curb ramp)
        return demo_cases[0]

    # 2. Image Validation
    is_valid, err_msg = validate_image(image)
    if not is_valid:
        raise ImageValidationError(err_msg)

    # Ensure RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    # 3. Resolve API Key & Model
    resolved_api_key = api_key or os.getenv("GEMMA_API_KEY")
    if not resolved_api_key or resolved_api_key.strip() in ("", "your_gemini_or_gemma_api_key_here"):
        raise GemmaAPIError(
            "Missing GEMMA_API_KEY. Please provide a valid Google AI Studio / Gemma API key in "
            "the sidebar settings or in your local .env file."
        )

    resolved_model_id = model_id or os.getenv("GEMMA_MODEL_ID") or DEFAULT_MODEL_ID

    # 4. Initialize GenAI Client
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=resolved_api_key.strip())
    except ImportError:
        raise GemmaAPIError("The 'google-genai' SDK is not installed. Please run: pip install google-genai")
    except Exception as e:
        raise GemmaAPIError(f"Failed to initialize Google GenAI Client: {str(e)}")

    prompt_text = build_audit_prompt(citizen_notes)

    # 5. Execute API Call with Bounded Retries
    raw_response_text = None
    last_exception = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_AUDIT_PROMPT,
                temperature=0.1,  # Low temperature for factual, grounded visual analysis
                response_mime_type="application/json",
            )

            response = client.models.generate_content(
                model=resolved_model_id,
                contents=[image, prompt_text],
                config=config
            )

            if response and response.text:
                raw_response_text = response.text
                break
            else:
                raise GemmaAPIError("Empty response returned by Gemma 4 model.")

        except Exception as exc:
            last_exception = exc
            logger.warning("Gemma API attempt %d/%d failed: %s", attempt, MAX_RETRIES, str(exc))
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * attempt)  # Exponential backoff

    if not raw_response_text:
        raise GemmaAPIError(
            f"Gemma 4 Multimodal inference failed after {MAX_RETRIES} attempts. Reason: {str(last_exception)}"
        )

    # 6. Parse and Validate JSON Schema
    clean_json = _clean_json_response(raw_response_text)
    try:
        data = json.loads(clean_json)
    except json.JSONDecodeError as json_err:
        logger.error("Malformed JSON received from Gemma 4: %s", clean_json)
        raise GemmaAPIError(
            f"Gemma 4 returned an unparseable response. JSON Error: {str(json_err)}"
        )

    # Fill metadata defaults if missing from raw model output
    if "audit_id" not in data or not data["audit_id"]:
        data["audit_id"] = f"AUDIT-{int(time.time())}"
    data["model_name"] = resolved_model_id
    data["timestamp"] = datetime.now().isoformat()
    data["is_demo_data"] = False

    try:
        audit_result = AuditAnalysisResult.model_validate(data)
    except Exception as validation_err:
        raise GemmaAPIError(
            f"Schema validation failed on Gemma 4 output: {str(validation_err)}"
        )

    # 7. Compute Deterministic Priority Scores for Every Detected Issue
    for issue in audit_result.issues:
        issue.priority_breakdown = calculate_priority_score(issue)

    return audit_result
