"""
CivicLens AI - Sample Demo Records Module
Provides realistic, transparently labeled sample datasets for offline presentation
and hackathon demonstration when API connectivity is absent.

NON-NEGOTIABLE COMPLIANCE:
- All records strictly flag `is_demo_data: True`.
- Never presented as live inference.
- Contains verified accessibility scenarios including positive clean walkway controls.
"""

from typing import List, Dict
from datetime import datetime
from schemas import AuditAnalysisResult, AccessibilityIssue, PersonaImpact
from priority_engine import calculate_priority_score


def get_demo_audit_cases() -> List[AuditAnalysisResult]:
    """Returns transparent, pre-configured audit records for demo presentation."""
    now_str = datetime.now().isoformat()

    # Case 1: Broken Concrete Sidewalk with Missing Curb Ramp
    issue_1 = AccessibilityIssue(
        issue_id="DEMO-ISS-001",
        issue_type="broken_footpath",
        concise_description="Fractured concrete sidewalk slab with 9cm vertical lip and missing curb transition",
        visual_evidence="Cracked concrete slab displaced upward by tree root; vertical step measurement estimated at 8-10cm; absence of sloped ramp to road level",
        affected_groups=["wheelchair_users", "elderly", "strollers"],
        potential_impact="May cause manual wheelchairs to tip forward or stop abruptly; forces pedestrians with wheeled devices toward roadway edge",
        confidence_score=0.94,
        suggested_action="Excavate fractured slab, grade root zone, and pour level reinforced concrete paving with integrated curb ramp",
        verification_required=False,
        unknowns=["Underground root network depth and potential future pavement heave"],
        persona_impacts=PersonaImpact(
            wheelchair_users="Vertical lip exceeds maximum allowable threshold for unassisted wheelchair traversal, preventing continuous travel.",
            visually_impaired="Tactile paving missing; abrupt elevation change presents tripping hazard for cane users.",
            elderly="High risk of loss of balance, requiring significant step elevation.",
            strollers="Wheels will wedge in crack, requiring lifting of stroller."
        )
    )
    issue_1.priority_breakdown = calculate_priority_score(issue_1)

    case_1 = AuditAnalysisResult(
        audit_id="DEMO-AUDIT-001",
        image_summary="Residential urban street walkway showing damaged concrete slab and abrupt curb drop.",
        has_barriers=True,
        issues=[issue_1],
        overall_notes="Daylight photograph, clear pedestrian corridor visibility, dry pavement.",
        verification_needed=False,
        model_name="gemma-4-multimodal-it [DEMO RECORD]",
        timestamp=now_str,
        is_demo_data=True
    )

    # Case 2: Open Storm Drain & Cavity Adjacent to Traffic
    issue_2 = AccessibilityIssue(
        issue_id="DEMO-ISS-002",
        issue_type="open_drainage_pothole",
        concise_description="Uncovered storm drain cavity directly on pedestrian walkway adjacent to active road traffic",
        visual_evidence="Rectangular drain opening approximately 40cm x 60cm without protective grill; dark cavity visible; located 0.5m from road curb",
        affected_groups=["wheelchair_users", "visually_impaired", "elderly", "strollers"],
        potential_impact="Direct fall and severe injury hazard; pedestrians forced into active vehicular traffic lane to bypass opening",
        confidence_score=0.97,
        suggested_action="Emergency placement of barricade followed by permanent installation of load-bearing cast iron drain grate",
        verification_required=False,
        unknowns=["Internal depth of drain cavity cannot be measured from photo"],
        persona_impacts=PersonaImpact(
            wheelchair_users="Presents direct fall hazard; bypass requires entering vehicle roadway traffic.",
            visually_impaired="Severe drop-off hazard; white cane may drop into void without warning.",
            elderly="Major falling risk, especially in low-light conditions.",
            strollers="Immediate wheel entrapment and tip-over danger."
        )
    )
    issue_2.priority_breakdown = calculate_priority_score(issue_2)

    case_2 = AuditAnalysisResult(
        audit_id="DEMO-AUDIT-002",
        image_summary="Commercial boulevard pedestrian strip with uncovered drainage cavity and heavy traffic.",
        has_barriers=True,
        issues=[issue_2],
        overall_notes="High pedestrian foot traffic area; critical safety hazard.",
        verification_needed=False,
        model_name="gemma-4-multimodal-it [DEMO RECORD]",
        timestamp=now_str,
        is_demo_data=True
    )

    # Case 3: Clean, Accessible Pedestrian Corridor (Negative Control)
    issue_3 = AccessibilityIssue(
        issue_id="DEMO-ISS-003",
        issue_type="no_barrier_detected",
        concise_description="Clean, level, barrier-free pedestrian corridor with tactile paving and wide clearance",
        visual_evidence="Continuous level pavers, detectable tactile guidance strips, 2.5-meter unobstructed width, gentle grade",
        affected_groups=[],
        potential_impact="No physical impediments detected; supports safe, inclusive pedestrian transit for all demographics.",
        confidence_score=0.99,
        suggested_action="No civic repairs required; continue routine street sweeping and scheduled maintenance.",
        verification_required=False,
        unknowns=[],
        persona_impacts=PersonaImpact(
            wheelchair_users="Smooth surface and sufficient width allow unencumbered two-way wheelchair transit.",
            visually_impaired="Tactile directional guidance strips provide continuous tactile navigation.",
            elderly="Even surface with zero abrupt steps supports stable walking.",
            strollers="Spacious, smooth walkway allows effortless stroller transit."
        )
    )
    issue_3.priority_breakdown = calculate_priority_score(issue_3)

    case_3 = AuditAnalysisResult(
        audit_id="DEMO-AUDIT-003",
        image_summary="Modern pedestrianized avenue with integrated tactile paving and zero barriers.",
        has_barriers=False,
        issues=[issue_3],
        overall_notes="Model successfully identified an accessible environment without false positives.",
        verification_needed=False,
        model_name="gemma-4-multimodal-it [DEMO RECORD]",
        timestamp=now_str,
        is_demo_data=True
    )

    # Case 4: Waterlogging with Ambiguous Depth (Uncertainty & Verification Required)
    issue_4 = AccessibilityIssue(
        issue_id="DEMO-ISS-004",
        issue_type="standing_water",
        concise_description="Extensive stagnant water puddle submerging pedestrian walkway and curb edge",
        visual_evidence="Opaque murky water accumulation spanning the entire 1.8m width of the sidewalk for approximately 4 meters",
        affected_groups=["wheelchair_users", "visually_impaired", "elderly"],
        potential_impact="May submerge hidden potholes or uneven stones; water splash and slip hazard",
        confidence_score=0.82,
        suggested_action="Clear clogged drainage outlet and inspect subsurface paving integrity once drained",
        verification_required=True,
        unknowns=[
            "Exact depth of water accumulation cannot be calculated from surface view",
            "Condition of underlying concrete surface beneath standing water is occluded"
        ],
        persona_impacts=PersonaImpact(
            wheelchair_users="Water could submerge wheelchair motors or hide sharp debris and deep depressions.",
            visually_impaired="Cane sounding provides water feedback but cannot detect underlying pavement cracks.",
            elderly="High slipping risk and impossible to judge footing stability.",
            strollers="Caregivers cannot navigate without wading through standing water."
        )
    )
    issue_4.priority_breakdown = calculate_priority_score(issue_4)

    case_4 = AuditAnalysisResult(
        audit_id="DEMO-AUDIT-004",
        image_summary="Post-rainfall pedestrian sidewalk covered in standing murky water.",
        has_barriers=True,
        issues=[issue_4],
        overall_notes="Lighting is diffused; on-site inspection recommended to evaluate subsurface drainage.",
        verification_needed=True,
        model_name="gemma-4-multimodal-it [DEMO RECORD]",
        timestamp=now_str,
        is_demo_data=True
    )

    return [case_1, case_2, case_3, case_4]
