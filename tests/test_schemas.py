"""
Unit tests for CivicLens AI Pydantic Schemas.
"""

import pytest
from pydantic import ValidationError
from schemas import (
    AccessibilityIssue,
    AuditAnalysisResult,
    PersonaImpact,
    PriorityScoreBreakdown,
    CivicReportDraft,
)


def test_valid_accessibility_issue():
    issue = AccessibilityIssue(
        issue_id="ISSUE-001",
        issue_type="broken_footpath",
        concise_description="Cracked concrete sidewalk slab",
        visual_evidence="Multiple longitudinal fractures extending 1.5 meters across pavement",
        affected_groups=["wheelchair_users", "elderly"],
        potential_impact="May cause tipping hazard for wheelchair wheels",
        confidence_score=0.92,
        suggested_action="Repave damaged slab and level curb joint",
        verification_required=False,
        unknowns=["Sub-base soil compaction under fractured slab"],
    )
    assert issue.issue_id == "ISSUE-001"
    assert issue.confidence_score == 0.92
    assert "wheelchair_users" in issue.affected_groups


def test_confidence_score_clamping():
    # Test valid float rounding
    issue = AccessibilityIssue(
        issue_id="ISSUE-002",
        issue_type="standing_water",
        concise_description="Puddle blocking curb",
        visual_evidence="Dark water covering walkway",
        potential_impact="Pedestrians might slip",
        confidence_score=0.854,
        suggested_action="Clear storm drain",
    )
    assert issue.confidence_score == 0.85


def test_audit_analysis_result_serialization():
    issue = AccessibilityIssue(
        issue_id="ISSUE-003",
        issue_type="missing_ramp",
        concise_description="No curb ramp at intersection",
        visual_evidence="Standard 15cm vertical curb with no incline transition",
        affected_groups=["wheelchair_users", "strollers"],
        potential_impact="Complete barrier for wheelchair access",
        confidence_score=0.95,
        suggested_action="Install ADA compliant tactile curb ramp",
    )
    audit = AuditAnalysisResult(
        audit_id="AUDIT-2026-TEST",
        image_summary="Urban intersection sidewalk",
        has_barriers=True,
        issues=[issue],
        overall_notes="Daytime lighting, clear visibility",
        verification_needed=False,
        model_name="gemma-4-multimodal-it",
        timestamp="2026-10-27T10:00:00Z",
    )
    data = audit.model_dump()
    assert data["has_barriers"] is True
    assert len(data["issues"]) == 1
    assert data["issues"][0]["issue_type"] == "missing_ramp"


def test_civic_report_draft():
    draft = CivicReportDraft(
        report_id="REP-001",
        audit_id="AUDIT-001",
        issue_title="Severe Footpath Fracture",
        user_location="Corner of 5th Ave and Main St",
        observed_condition="Concrete slab broken and raised 8cm",
        supporting_visual_evidence="Fractured pavement with exposed gravel",
        possible_impact="May cause trips for pedestrians",
        suggested_remediation="Level and repave concrete surface",
        priority_tier="HIGH",
        priority_score=68.5,
        priority_explanation="Safety: 24, Accessibility: 26, Evidence: 18.5",
        uncertainties_and_unknowns=["Underground pipe status unverified"],
        disclaimer="Draft report for citizen review only. Not an official municipal complaint.",
        created_at="2026-10-27T10:00:00Z",
    )
    assert draft.priority_score == 68.5
    assert "Draft report" in draft.disclaimer
