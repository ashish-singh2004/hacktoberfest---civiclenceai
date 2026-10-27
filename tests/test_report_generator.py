"""
Unit tests for CivicLens AI Civic Report Generator.
Verifies report drafting, voluntary location handling, disclaimer compliance,
bilingual outputs (English & Hindi), and Markdown/TXT/JSON exports.
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
    assert "NOTICE: This document is an assistive civic draft" in draft.disclaimer


def test_generate_report_draft_hindi(sample_audit):
    draft = generate_report_draft(sample_audit, issue_index=0, user_location="स्टेशन रोड", language="hi")
    assert draft.language == "hi"
    assert draft.user_location == "स्टेशन रोड"
    assert "सहायक मसौदा" in draft.disclaimer


def test_unspecified_location_handling(sample_audit):
    draft = generate_report_draft(sample_audit, issue_index=0, user_location="", language="en")
    assert draft.user_location == "Location not specified by citizen"


def test_export_formats(sample_audit):
    draft = generate_report_draft(sample_audit, issue_index=0, user_location="Sector 14 Market", language="en")
    md = export_report_as_markdown(draft)
    txt = export_report_as_text(draft)
    json_str = export_report_as_json(draft)

    # Markdown checks
    assert "# CIVIC ACCESSIBILITY AUDIT - COMPLAINT DRAFT" in md
    assert "Sector 14 Market" in md

    # Plain text checks
    assert "CIVIC ACCESSIBILITY AUDIT - COMPLAINT DRAFT" in txt
    assert "[DISCLAIMER]:" in txt

    # JSON checks
    parsed = json.loads(json_str)
    assert parsed["report_id"] == draft.report_id
    assert parsed["user_location"] == "Sector 14 Market"
    assert parsed["priority_score"] == draft.priority_score
