"""
Unit tests for Gemma 4 Multimodal Service.
Tests image validation, error handling on missing credentials, JSON cleanup,
and isolated demo mode execution.
"""

import pytest
from PIL import Image
from gemma_service import (
    validate_image,
    _clean_json_response,
    analyze_street_image,
    GemmaAPIError,
    ImageValidationError,
)
from demo_data import get_demo_audit_cases


def test_validate_image_valid():
    img = Image.new("RGB", (640, 480), color="gray")
    is_valid, err = validate_image(img)
    assert is_valid is True
    assert err is None


def test_validate_image_too_small():
    tiny_img = Image.new("RGB", (50, 50), color="blue")
    is_valid, err = validate_image(tiny_img)
    assert is_valid is False
    assert "too small" in err


def test_clean_json_response():
    raw_markdown = "```json\n{\"test\": 123}\n```"
    cleaned = _clean_json_response(raw_markdown)
    assert cleaned == '{"test": 123}'


def test_missing_api_key_raises_error():
    img = Image.new("RGB", (400, 300), color="white")
    with pytest.raises(GemmaAPIError) as exc_info:
        analyze_street_image(img, api_key="", force_demo_mode=False)
    assert "Missing API Key" in str(exc_info.value)


def test_force_demo_mode_returns_labeled_demo_result():
    img = Image.new("RGB", (400, 300), color="white")
    result = analyze_street_image(img, force_demo_mode=True)
    assert result.is_demo_data is True
    assert len(result.issues) > 0
    assert result.issues[0].priority_breakdown is not None
    assert 0.0 <= result.issues[0].priority_breakdown.total_score <= 100.0


def test_demo_audit_cases_structure():
    cases = get_demo_audit_cases()
    assert len(cases) == 4
    for c in cases:
        assert c.is_demo_data is True
        for iss in c.issues:
            assert iss.priority_breakdown is not None


def test_normalize_audit_dict_with_list_of_issues():
    from gemma_service import _normalize_audit_dict
    raw_list = [
        {
            "issue_id": "ISS-01",
            "issue_type": "open_drainage_pothole",
            "concise_description": "Pothole in asphalt",
            "visual_evidence": "Dark hole in pavement",
            "potential_impact": "Tripping risk",
            "confidence_score": "0.92",
            "affected_groups": "wheelchair_users, elderly",
            "unknowns": "True depth unknown",
            "persona_impacts": [
                {"wheelchair_users": "Cannot traverse safely"}
            ]
        }
    ]
    norm = _normalize_audit_dict(raw_list, "gemma-4-26b-a4b-it")
    assert isinstance(norm, dict)
    assert norm["has_barriers"] is True
    assert len(norm["issues"]) == 1
    iss = norm["issues"][0]
    assert iss["issue_id"] == "ISS-01"
    assert iss["confidence_score"] == 0.92
    assert "wheelchair_users" in iss["affected_groups"]
    assert iss["unknowns"] == ["True depth unknown"]
    assert iss["persona_impacts"]["wheelchair_users"] == "Cannot traverse safely"

