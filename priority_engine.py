"""
CivicLens AI - Deterministic Priority Engine
Implements an explainable, transparent 0-100 priority scoring model based on:
1. Safety risk (0-40)
2. Accessibility impediment (0-35)
3. Evidence completeness and confidence (0-25)
"""

from typing import Dict, Any, List
from schemas import AccessibilityIssue, PriorityScoreBreakdown


# Baseline scores for standardized issue categories
SAFETY_BASE_MAPPING: Dict[str, float] = {
    "open_drainage_pothole": 32.0,
    "collapsed_slab": 30.0,
    "broken_footpath": 22.0,
    "standing_water": 18.0,
    "damaged_walking_surface": 16.0,
    "encroachment_obstacle": 12.0,
    "missing_ramp": 10.0,
    "waste_overflow": 10.0,
    "vegetation_overgrowth": 8.0,
    "no_barrier_detected": 0.0,
}

ACCESSIBILITY_BASE_MAPPING: Dict[str, float] = {
    "missing_ramp": 28.0,
    "collapsed_slab": 26.0,
    "broken_footpath": 22.0,
    "encroachment_obstacle": 20.0,
    "standing_water": 18.0,
    "damaged_walking_surface": 16.0,
    "open_drainage_pothole": 15.0,
    "waste_overflow": 12.0,
    "vegetation_overgrowth": 10.0,
    "no_barrier_detected": 0.0,
}


def calculate_priority_score(issue: AccessibilityIssue) -> PriorityScoreBreakdown:
    """
    Computes a deterministic, explainable priority score for a detected barrier.

    Formula:
        Total (0-100) = Safety Score (0-40) + Accessibility Score (0-35) + Evidence Score (0-25)

    Returns:
        PriorityScoreBreakdown with itemized components, reasons, and classification tier.
    """
    issue_type = issue.issue_type.lower().strip()
    reasons: List[str] = []

    # If no barrier is present, score is strictly zero
    if issue_type == "no_barrier_detected" or issue.concise_description.lower().startswith("no barrier"):
        return PriorityScoreBreakdown(
            safety_score=0.0,
            accessibility_score=0.0,
            evidence_score=0.0,
            total_score=0.0,
            priority_tier="LOW",
            reasons=["No physical pedestrian barriers or accessibility obstacles were detected in the image."]
        )

    # --------------------------------------------------------------------------
    # 1. Safety Score (0 - 40 points)
    # --------------------------------------------------------------------------
    base_safety = SAFETY_BASE_MAPPING.get(issue_type, 15.0)
    safety_mod = 0.0
    desc_lower = (issue.concise_description + " " + issue.potential_impact).lower()

    if "traffic" in desc_lower or "road" in desc_lower or "vehicular" in desc_lower:
        safety_mod += 8.0
        reasons.append("Pedestrians potentially forced into vehicular roadway (+8.0 safety)")
    if "trip" in desc_lower or "fall" in desc_lower or "injury" in desc_lower:
        safety_mod += 4.0
        reasons.append("Physical tripping or fall risk identified (+4.0 safety)")
    if "open" in desc_lower and ("trench" in desc_lower or "hole" in desc_lower or "drain" in desc_lower):
        safety_mod += 6.0
        reasons.append("Uncovered trench or hazardous void (+6.0 safety)")

    safety_score = max(0.0, min(40.0, round(base_safety + safety_mod, 1)))

    # --------------------------------------------------------------------------
    # 2. Accessibility Score (0 - 35 points)
    # --------------------------------------------------------------------------
    base_access = ACCESSIBILITY_BASE_MAPPING.get(issue_type, 15.0)
    access_mod = 0.0

    # Impact on vulnerable groups
    groups = [g.lower() for g in issue.affected_groups]
    if "wheelchair_users" in groups or "wheelchair" in desc_lower:
        access_mod += 4.0
        reasons.append("Directly prevents or impedes wheelchair passage (+4.0 accessibility)")
    if "visually_impaired" in groups or "blind" in desc_lower or "tactile" in desc_lower:
        access_mod += 4.0
        reasons.append("Disrupts tactile wayfinding or presents drop-off hazard (+4.0 accessibility)")
    if "elderly" in groups:
        access_mod += 2.0
        reasons.append("Heightened hazard for senior citizens with mobility constraints (+2.0 accessibility)")
    if "strollers" in groups:
        access_mod += 2.0
        reasons.append("Impedes wheeled stroller mobility (+2.0 accessibility)")

    if "completely blocked" in desc_lower or "impassable" in desc_lower:
        access_mod += 5.0
        reasons.append("Sidewalk is completely impassable, zero bypass space (+5.0 accessibility)")

    accessibility_score = max(0.0, min(35.0, round(base_access + access_mod, 1)))

    # --------------------------------------------------------------------------
    # 3. Evidence Score (0 - 25 points)
    # --------------------------------------------------------------------------
    # Confidence contributes up to 18 points
    conf = max(0.0, min(1.0, issue.confidence_score))
    evidence_base = conf * 18.0

    evidence_mod = 0.0
    if len(issue.visual_evidence.strip()) >= 30:
        evidence_mod += 4.0
        reasons.append("Clear, concrete visual evidence cited in photograph (+4.0 evidence)")

    if issue.verification_required:
        evidence_mod -= 5.0
        reasons.append("Visual ambiguity or partial occlusion requires on-site verification (-5.0 evidence penalty)")

    if issue.unknowns and len(issue.unknowns) > 0:
        unknown_penalty = min(4.0, len(issue.unknowns) * 1.5)
        evidence_mod -= unknown_penalty
        reasons.append(f"Unverified physical variables noted: {len(issue.unknowns)} unknowns (-{unknown_penalty} evidence penalty)")

    evidence_score = max(0.0, min(25.0, round(evidence_base + evidence_mod, 1)))

    # --------------------------------------------------------------------------
    # Total Score & Tier Classification
    # --------------------------------------------------------------------------
    total_score = max(0.0, min(100.0, round(safety_score + accessibility_score + evidence_score, 1)))

    if total_score >= 80.0:
        tier = "CRITICAL"
    elif total_score >= 60.0:
        tier = "HIGH"
    elif total_score >= 40.0:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    return PriorityScoreBreakdown(
        safety_score=safety_score,
        accessibility_score=accessibility_score,
        evidence_score=evidence_score,
        total_score=total_score,
        priority_tier=tier,
        formula="Total = Safety(0-40) + Accessibility(0-35) + Evidence(0-25)",
        reasons=reasons
    )
