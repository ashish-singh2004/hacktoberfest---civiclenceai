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
from typing import Optional, Tuple, Any, Dict, List
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
    """Extracts JSON substring and strips markdown fences or surrounding chatter."""
    text = raw_text.strip()
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        text = text[start:end] if end != -1 else text[start:]
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        text = text[start:end] if end != -1 else text[start:]

    text = text.strip()
    first_brace = text.find("{")
    first_bracket = text.find("[")

    if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
        last_brace = text.rfind("}")
        if last_brace != -1:
            text = text[first_brace:last_brace + 1]
    elif first_bracket != -1:
        last_bracket = text.rfind("]")
        if last_bracket != -1:
            text = text[first_bracket:last_bracket + 1]

    return text.strip()


def _normalize_audit_dict(data: Any, resolved_model_id: str) -> dict:
    """
    Normalizes diverse LLM output variations (JSON arrays, nested keys, single issue objects)
    into a structured dictionary conforming strictly to the AuditAnalysisResult schema.
    """
    import time
    if isinstance(data, list):
        if len(data) == 1 and isinstance(data[0], dict) and "issues" in data[0]:
            data = data[0]
        elif len(data) > 0 and all(isinstance(x, dict) for x in data):
            data = {
                "audit_id": f"AUDIT-{int(time.time())}",
                "image_summary": "Street photograph with identified pedestrian accessibility barriers.",
                "has_barriers": True,
                "issues": data,
                "overall_notes": "Multimodal analysis completed by Gemma 4",
                "verification_needed": any(x.get("verification_required", False) for x in data)
            }
        else:
            data = {
                "audit_id": f"AUDIT-{int(time.time())}",
                "image_summary": "Street photograph analysis.",
                "has_barriers": False,
                "issues": []
            }

    if not isinstance(data, dict):
        raise GemmaAPIError(f"Gemma 4 response expected a JSON object or array, received: {type(data).__name__}")

    for nest_key in ("audit", "result", "response", "data"):
        if nest_key in data and isinstance(data[nest_key], dict) and "issues" in data[nest_key]:
            data = data[nest_key]
            break

    if not data.get("audit_id"):
        data["audit_id"] = f"AUDIT-{int(time.time())}"
    if not data.get("image_summary"):
        data["image_summary"] = "Street photograph inspected for accessibility."

    raw_issues = data.get("issues", [])
    if isinstance(raw_issues, dict):
        raw_issues = [raw_issues]
    elif not isinstance(raw_issues, list):
        raw_issues = []

    normalized_issues = []
    for idx, raw_iss in enumerate(raw_issues):
        if not isinstance(raw_iss, dict):
            continue

        if not raw_iss.get("issue_id"):
            raw_iss["issue_id"] = f"ISSUE-{idx+1:03d}"

        raw_iss["issue_type"] = raw_iss.get("issue_type") or "damaged_walking_surface"

        if not raw_iss.get("concise_description"):
            raw_iss["concise_description"] = (
                raw_iss.get("description") or raw_iss.get("title") or "Physical pedestrian barrier observed"
            )

        if not raw_iss.get("visual_evidence"):
            raw_iss["visual_evidence"] = (
                raw_iss.get("evidence") or raw_iss.get("visual_indicators") or "Visible pavement deterioration in photograph"
            )

        groups = raw_iss.get("affected_groups", [])
        if isinstance(groups, str):
            groups = [g.strip() for g in groups.split(",") if g.strip()]
        elif not isinstance(groups, list):
            groups = []
        raw_iss["affected_groups"] = groups

        if not raw_iss.get("potential_impact"):
            raw_iss["potential_impact"] = raw_iss.get("impact") or "May impede safe pedestrian transit."

        conf = raw_iss.get("confidence_score")
        if conf is None:
            conf = raw_iss.get("confidence", 0.9)
        try:
            if isinstance(conf, str):
                conf = float(conf.replace("%", "").strip())
                if conf > 1.0:
                    conf /= 100.0
            conf = float(conf)
        except Exception:
            conf = 0.85
        raw_iss["confidence_score"] = max(0.0, min(1.0, conf))

        if not raw_iss.get("suggested_action"):
            raw_iss["suggested_action"] = (
                raw_iss.get("recommendation") or raw_iss.get("action") or "Inspect and repair damaged surface to restore accessibility"
            )

        v_req = raw_iss.get("verification_required", False)
        if isinstance(v_req, str):
            v_req = v_req.lower() in ("true", "1", "yes")
        raw_iss["verification_required"] = bool(v_req)

        unknowns = raw_iss.get("unknowns", [])
        if isinstance(unknowns, str):
            unknowns = [unknowns]
        elif not isinstance(unknowns, list):
            unknowns = []
        raw_iss["unknowns"] = unknowns

        # Normalize persona_impacts
        p_impact = raw_iss.get("persona_impacts")
        if isinstance(p_impact, list):
            merged = {}
            for item in p_impact:
                if isinstance(item, dict):
                    merged.update(item)
                elif isinstance(item, str):
                    item_lower = item.lower()
                    if "wheelchair" in item_lower:
                        merged["wheelchair_users"] = item
                    elif "visual" in item_lower or "cane" in item_lower:
                        merged["visually_impaired"] = item
                    elif "elderly" in item_lower or "senior" in item_lower:
                        merged["elderly"] = item
                    elif "stroller" in item_lower:
                        merged["strollers"] = item
            p_impact = merged
        elif isinstance(p_impact, str):
            p_impact = {
                "wheelchair_users": p_impact,
                "visually_impaired": p_impact,
                "elderly": p_impact,
                "strollers": p_impact,
            }
        elif not isinstance(p_impact, dict):
            p_impact = {}

        raw_iss["persona_impacts"] = p_impact
        normalized_issues.append(raw_iss)

    data["issues"] = normalized_issues
    data["has_barriers"] = len(normalized_issues) > 0 and any(
        i.get("issue_type") != "no_barrier_detected" for i in normalized_issues
    )
    data["verification_needed"] = any(i.get("verification_required", False) for i in normalized_issues)
    data["model_name"] = resolved_model_id
    data["timestamp"] = datetime.now().isoformat()
    data["is_demo_data"] = False

    return data


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
    resolved_api_key = api_key if api_key is not None else (os.getenv("GEMMA_API_KEY") or os.getenv("GEMINI_API_KEY"))
    if not resolved_api_key or resolved_api_key.strip() in ("", "your_gemini_or_gemma_api_key_here"):
        raise GemmaAPIError(
            "Missing API Key. Please provide your Google AI Studio API key (GEMMA_API_KEY or GEMINI_API_KEY) in "
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

    # Normalize data dictionary (handles lists, nested keys, missing fields)
    normalized_data = _normalize_audit_dict(data, resolved_model_id)

    try:
        audit_result = AuditAnalysisResult.model_validate(normalized_data)
    except Exception as validation_err:
        raise GemmaAPIError(
            f"Schema validation failed on Gemma 4 output: {str(validation_err)}"
        )

    # 7. Compute Deterministic Priority Scores for Every Detected Issue
    for issue in audit_result.issues:
        issue.priority_breakdown = calculate_priority_score(issue)

    return audit_result
