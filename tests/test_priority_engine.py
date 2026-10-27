"""
Unit tests for CivicLens AI Priority Engine.
Verifies deterministic calculation, mathematical formulas, boundary conditions,
tier classifications, and uncertainty discounts.
"""

import pytest
from schemas import AccessibilityIssue
from priority_engine import calculate_priority_score


def test_no_barrier_detected_scores_zero():
    clean_issue = AccessibilityIssue(
        issue_id="ISSUE-000",
        issue_type="no_barrier_detected",
        concise_description="No barrier visible, smooth and wide pedestrian walkway",
        visual_evidence="Clean concrete walkway with level paving and zero obstructions",
        confidence_score=0.98,
        suggested_action="No remediation needed, maintain current condition",
        verification_required=False,
    )
    result = calculate_priority_score(clean_issue)
    assert result.total_score == 0.0
    assert result.safety_score == 0.0
    assert result.accessibility_score == 0.0
    assert result.evidence_score == 0.0
    assert result.priority_tier == "LOW"


def test_high_hazard_issue_scoring():
    hazard_issue = AccessibilityIssue(
        issue_id="ISSUE-101",
        issue_type="open_drainage_pothole",
        concise_description="Uncovered open storm drain forcing pedestrians into vehicular traffic",
        visual_evidence="Deep open hole in concrete sidewalk with exposed iron bars and dark void",
        affected_groups=["wheelchair_users", "visually_impaired", "elderly"],
        potential_impact="Severe fall and tripping injury hazard; completely impassable for wheelchair users",
        confidence_score=0.95,
        suggested_action="Cover drain immediately with secure heavy-duty metal grate",
        verification_required=False,
        unknowns=[],
    )
    result = calculate_priority_score(hazard_issue)
    assert result.safety_score > 30.0
    assert result.accessibility_score > 20.0
    assert result.evidence_score > 15.0
    assert result.total_score >= 70.0
    assert result.priority_tier in ["HIGH", "CRITICAL"]
    assert any("traffic" in r.lower() or "trench" in r.lower() for r in result.reasons)


def test_score_boundaries_are_strictly_enforced():
    # Extreme edge case: many keywords and high values
    extreme_issue = AccessibilityIssue(
        issue_id="ISSUE-999",
        issue_type="open_drainage_pothole",
        concise_description="Open trench hole drain in road traffic vehicular trip fall injury completely blocked impassable",
        visual_evidence="Detailed visual observation with more than thirty characters describing the scene accurately in high resolution",
        affected_groups=["wheelchair_users", "visually_impaired", "elderly", "strollers"],
        potential_impact="Severe injury hazard completely blocked path",
        confidence_score=1.0,
        suggested_action="Fix immediately",
        verification_required=False,
        unknowns=[],
    )
    result = calculate_priority_score(extreme_issue)
    assert 0.0 <= result.safety_score <= 40.0
    assert 0.0 <= result.accessibility_score <= 35.0
    assert 0.0 <= result.evidence_score <= 25.0
    assert 0.0 <= result.total_score <= 100.0


def test_verification_penalty_reduces_evidence_score():
    base_issue = AccessibilityIssue(
        issue_id="ISSUE-201",
        issue_type="standing_water",
        concise_description="Waterlogged section of sidewalk",
        visual_evidence="Submerged sidewalk section with reflection of sky",
        affected_groups=["wheelchair_users"],
        potential_impact="Water could hide underlying potholes",
        confidence_score=0.8,
        suggested_action="Clear water and check pavement",
        verification_required=False,
        unknowns=[],
    )
    unverified_issue = AccessibilityIssue(
        issue_id="ISSUE-202",
        issue_type="standing_water",
        concise_description="Waterlogged section of sidewalk",
        visual_evidence="Submerged sidewalk section with reflection of sky",
        affected_groups=["wheelchair_users"],
        potential_impact="Water could hide underlying potholes",
        confidence_score=0.8,
        suggested_action="Clear water and check pavement",
        verification_required=True,
        unknowns=["Depth of water cannot be measured", "Surface condition under water unknown"],
    )
    res_base = calculate_priority_score(base_issue)
    res_unverified = calculate_priority_score(unverified_issue)

    assert res_unverified.evidence_score < res_base.evidence_score
    assert any("verification" in r.lower() for r in res_unverified.reasons)
