"""
Unit tests for CivicLens AI Civic Report Generator.
Verifies report drafting, voluntary location handling, disclaimer compliance,
bilingual outputs (English & Hindi), department routing, WhatsApp share link, and exports.
"""

import json
import pytest
from schemas import AuditAnalysisResult, AccessibilityIssue
from priority_engine import calculate_priority_score
from report_generator import (
    generate_report_draft,
    export_report_as_markdown,
    export_report_as_text,
    export_report_as_json,
    build_whatsapp_share_url,
    get_responsible_authority,
)


@pytest.fixture
def sample_audit():
    issue = AccessibilityIssue(
        issue_id="ISS-TEST-99",
        issue_type="broken_footpath",
        concise_description="Broken sidewalk slab with exposed gravel",
        visual_evidence="Concrete fractured across 2 meters width with loose stones",
        affected_groups=["wheelchair_users", "elderly"],
        potential_impact="May cause trips or wheelchair stall",
        confidence_score=0.91,
        suggested_action="Reconstruct concrete walkway section",
        verification_required=False,
        unknowns=["Underground pipe status"],
    )
    issue.priority_breakdown = calculate_priority_score(issue)
    return AuditAnalysisResult(
        audit_id="AUDIT-TEST-99",
        image_summary="City sidewalk with fractured surface",
        has_barriers=True,
        issues=[issue],
        timestamp="2026-10-27T10:00:00Z",
    )


def test_generate_report_draft_english(sample_audit):
    draft = generate_report_draft(sample_audit, issue_index=0, user_location="Corner of 4th St", language="en")
    assert draft.language == "en"
    assert draft.user_location == "Corner of 4th St"
    assert "Broken sidewalk slab" in draft.observed_condition
    assert "editable citizen complaint letter" in draft.disclaimer
    assert "Footpath & Pedestrian Infrastructure" in draft.responsible_authority


def test_generate_report_draft_hindi(sample_audit):
    draft = generate_report_draft(sample_audit, issue_index=0, user_location="स्टेशन रोड", language="hi")
    assert draft.language == "hi"
    assert draft.user_location == "स्टेशन रोड"
    assert "तैयार शिकायत पत्र" in draft.disclaimer
    assert "नगर निगम" in draft.responsible_authority


def test_unspecified_location_handling(sample_audit):
    draft = generate_report_draft(sample_audit, issue_index=0, user_location="", language="en")
    assert draft.user_location == "Location not specified by citizen"


def test_export_formats_and_whatsapp_link(sample_audit):
    draft = generate_report_draft(sample_audit, issue_index=0, user_location="Sector 14 Market", language="en")
    md = export_report_as_markdown(draft)
    txt = export_report_as_text(draft)
    json_str = export_report_as_json(draft)
    wa_url = build_whatsapp_share_url(draft)

    # Markdown checks
    assert "# CIVIC ROAD & FOOTPATH REPAIR REQUEST" in md
    assert "Sector 14 Market" in md

    # Plain text checks
    assert "CIVIC ROAD & FOOTPATH REPAIR REQUEST" in txt
    assert "[DISCLAIMER / सूचना]:" in txt

    # JSON checks
    parsed = json.loads(json_str)
    assert parsed["report_id"] == draft.report_id
    assert parsed["user_location"] == "Sector 14 Market"
    assert parsed["priority_score"] == draft.priority_score

    # WhatsApp Link
    assert "https://api.whatsapp.com/send?text=" in wa_url
    assert "Sector%2014%20Market" in wa_url


def test_department_routing_logic():
    pothole_dept = get_responsible_authority("open_drainage_pothole", "en")
    water_dept = get_responsible_authority("standing_water", "hi")
    assert "Public Works Department" in pothole_dept
    assert "जल बोर्ड" in water_dept
