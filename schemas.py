"""
CivicLens AI - Data Schemas
Defines Pydantic models for structured multimodal accessibility audit analysis,
human-impact perspectives, deterministic priority scores, and civic reports.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator


class PersonaImpact(BaseModel):
    """Possible impact descriptions tailored to vulnerable mobility groups."""
    wheelchair_users: Optional[str] = Field(
        default=None,
        description="Possible impact on individuals using manual or motorized wheelchairs."
    )
    visually_impaired: Optional[str] = Field(
        default=None,
        description="Possible impact on pedestrians with low vision or using white canes."
    )
    elderly: Optional[str] = Field(
        default=None,
        description="Possible impact on senior citizens or individuals with balance constraints."
    )
    strollers: Optional[str] = Field(
        default=None,
        description="Possible impact on caregivers pushing baby strollers or wheeled carts."
    )


class PriorityScoreBreakdown(BaseModel):
    """Deterministic explainable priority score breakdown (0 to 100)."""
    safety_score: float = Field(
        ge=0.0, le=40.0,
        description="Potential safety and physical injury risk (0-40)."
    )
    accessibility_score: float = Field(
        ge=0.0, le=35.0,
        description="Severity of accessibility impediment for mobility devices (0-35)."
    )
    evidence_score: float = Field(
        ge=0.0, le=25.0,
        description="Completeness, clarity, and certainty of visual evidence (0-25)."
    )
    total_score: float = Field(
        ge=0.0, le=100.0,
        description="Composite priority score = safety + accessibility + evidence (0-100)."
    )
    priority_tier: str = Field(
        description="Priority classification: CRITICAL, HIGH, MEDIUM, or LOW."
    )
    formula: str = Field(
        default="Total = Safety(0-40) + Accessibility(0-35) + Evidence(0-25)",
        description="Mathematical formula used for calculation."
    )
    reasons: List[str] = Field(
        default_factory=list,
        description="Itemized explanations for each score component."
    )


class AccessibilityIssue(BaseModel):
    """Single detected or audited pedestrian accessibility barrier."""
    issue_id: str = Field(
        description="Unique identifier for the issue (e.g. 'ISSUE-001')."
    )
    issue_type: str = Field(
        description="Standardized barrier category (e.g., 'broken_footpath', 'missing_ramp', 'standing_water', 'encroachment')."
    )
    concise_description: str = Field(
        description="Brief summary of the physical barrier."
    )
    visual_evidence: str = Field(
        description="Direct visual observation anchoring the detection (what is visibly seen in pixels)."
    )
    affected_groups: List[str] = Field(
        default_factory=list,
        description="List of impacted groups (e.g., ['wheelchair_users', 'visually_impaired'])."
    )
    potential_impact: str = Field(
        default="No significant pedestrian impediment identified.",
        description="Carefully framed potential impact narrative (avoiding absolute certainty of harm)."
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Model-reported visual confidence level (0.0 to 1.0)."
    )
    suggested_action: str = Field(
        description="Recommended civic remediation or maintenance task."
    )
    verification_required: bool = Field(
        default=False,
        description="Whether on-site physical verification is required due to angle or visual ambiguity."
    )
    unknowns: List[str] = Field(
        default_factory=list,
        description="List of factors that cannot be confirmed from the 2D photograph alone."
    )
    persona_impacts: Optional[PersonaImpact] = Field(
        default=None,
        description="Detailed multi-persona impact breakdown."
    )
    priority_breakdown: Optional[PriorityScoreBreakdown] = Field(
        default=None,
        description="Calculated deterministic priority scoring."
    )

    @field_validator("confidence_score")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, round(v, 2)))


class AuditAnalysisResult(BaseModel):
    """Complete multimodal audit result for an uploaded image."""
    audit_id: str = Field(
        description="Unique identifier for the audit session."
    )
    image_summary: str = Field(
        description="Objective description of the scene depicted in the image."
    )
    has_barriers: bool = Field(
        description="Whether any pedestrian or accessibility barriers were visibly identified."
    )
    issues: List[AccessibilityIssue] = Field(
        default_factory=list,
        description="List of verified or candidate issues detected."
    )
    overall_notes: str = Field(
        default="",
        description="General context, lighting notes, or scene observations."
    )
    verification_needed: bool = Field(
        default=False,
        description="True if any issues require on-site confirmation."
    )
    model_name: str = Field(
        default="gemma-4-multimodal",
        description="Model identifier that produced the analysis."
    )
    timestamp: str = Field(
        description="ISO 8601 timestamp of analysis."
    )
    is_demo_data: bool = Field(
        default=False,
        description="Indicates whether this record is sample demo data or live model output."
    )


class CivicReportDraft(BaseModel):
    """Editable civic complaint report draft generated from an audit."""
    report_id: str
    audit_id: str
    issue_title: str
    user_location: str = Field(
        default="Not specified by user",
        description="Voluntary location entered by the citizen (never auto-fabricated)."
    )
    observed_condition: str
    supporting_visual_evidence: str
    possible_impact: str
    suggested_remediation: str
    priority_tier: str
    priority_score: float
    priority_explanation: str
    uncertainties_and_unknowns: List[str]
    responsible_authority: str = "Public Works Department (PWD) / Municipal Maintenance"
    disclaimer: str
    created_at: str
    language: str = "en"
