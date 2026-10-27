"""
CivicLens AI - Civic Complaint Report Draft Generator
Formats audit observations into formal, evidence-backed civic complaint drafts
intended for voluntary citizen review and submission to municipal authorities.

NON-NEGOTIABLE PRINCIPLES:
- Never claim the complaint has been submitted to authorities. Draft only.
- Never invent GPS coordinates, street addresses, or legal statutes.
- User-provided location is labeled transparently.
- Supports bilingual English & Hindi formatting.
- Exportable to clean Markdown, TXT, and JSON.
"""

import json
from datetime import datetime
from typing import Optional, Dict
from schemas import AuditAnalysisResult, AccessibilityIssue, CivicReportDraft


# Bilingual template dictionaries
TEMPLATES: Dict[str, Dict[str, str]] = {
    "en": {
        "header": "CIVIC ACCESSIBILITY AUDIT - COMPLAINT DRAFT",
        "sub_header": "Prepared via CivicLens AI (Evidence-Based Assistive Audit)",
        "disclaimer": (
            "NOTICE: This document is an assistive civic draft intended for review and voluntary submission "
            "by a resident. It does NOT constitute a legally binding inspection, an official municipal citation, "
            "or an automated government filing. No personal identities or biometric profiles are included."
        ),
        "location_label": "Reported Location (Citizen-Provided)",
        "issue_label": "Identified Barrier Category",
        "condition_label": "Observed Physical Condition",
        "evidence_label": "Photographic Visual Evidence",
        "impact_label": "Possible Pedestrian & Mobility Impact",
        "remediation_label": "Recommended Civic Action",
        "priority_label": "Suggested Priority Rating",
        "uncertainties_label": "Uncertainties & On-Site Verification Requirements",
        "audit_meta_label": "Audit Session Reference",
    },
    "hi": {
        "header": "नागरिक सुगमता ऑडिट - शिकायत मसौदा",
        "sub_header": "CivicLens AI द्वारा तैयार (साक्ष्य-आधारित सहायक ऑडिट)",
        "disclaimer": (
            "सूचना: यह दस्तावेज़ नागरिक द्वारा समीक्षा और स्वैच्छिक शिकायत दर्ज करने हेतु एक सहायक मसौदा है। "
            "यह कोई आधिकारिक सरकारी नोटिस या स्वतः जमा की गई शिकायत नहीं है। इसमें किसी व्यक्ति की पहचान या "
            "बायोमेट्रिक डेटा शामिल नहीं है।"
        ),
        "location_label": "दर्ज किया गया स्थान (नागरिक द्वारा प्रदत्त)",
        "issue_label": "पहचाने गए अवरोध की श्रेणी",
        "condition_label": "प्रत्यक्ष भौतिक स्थिति",
        "evidence_label": "तस्वीर से प्राप्त दृश्य साक्ष्य",
        "impact_label": "पैदल यात्रियों और दिव्यांगजनों पर संभावित प्रभाव",
        "remediation_label": "सुझाया गया सुधारात्मक कार्य",
        "priority_label": "प्रस्तावित प्राथमिकता स्तर",
        "uncertainties_label": "अनिश्चितताएं एवं भौतिक सत्यापन आवश्यकताएं",
        "audit_meta_label": "ऑडिट सत्र संदर्भ",
    }
}


def generate_report_draft(
    audit: AuditAnalysisResult,
    issue_index: int = 0,
    user_location: Optional[str] = None,
    language: str = "en"
) -> CivicReportDraft:
    """
    Creates a validated CivicReportDraft object from an AuditAnalysisResult.
    """
    lang = language if language in ("en", "hi") else "en"
    t = TEMPLATES[lang]

    if not audit.issues or issue_index >= len(audit.issues):
        issue = AccessibilityIssue(
            issue_id="ISSUE-NONE",
            issue_type="no_barrier_detected",
            concise_description="Clean, level pedestrian corridor",
            visual_evidence="No visible obstruction in photograph",
            potential_impact="Walkway is accessible for pedestrians",
            confidence_score=0.99,
            suggested_action="Routine cleaning and scheduled inspection",
            verification_required=False,
        )
    else:
        issue = audit.issues[issue_index]

    loc = user_location.strip() if user_location and user_location.strip() else "Location not specified by citizen"
    priority = issue.priority_breakdown
    priority_tier = priority.priority_tier if priority else "MEDIUM"
    priority_score = priority.total_score if priority else 50.0
    priority_explanation = (
        f"Safety: {priority.safety_score}/40 | Accessibility: {priority.accessibility_score}/35 | Evidence: {priority.evidence_score}/25"
        if priority else "Standard baseline score"
    )

    report_id = f"REP-{datetime.now().strftime('%Y%m%d')}-{issue.issue_id}"

    return CivicReportDraft(
        report_id=report_id,
        audit_id=audit.audit_id,
        issue_title=f"Civic Audit: {issue.concise_description}",
        user_location=loc,
        observed_condition=issue.concise_description,
        supporting_visual_evidence=issue.visual_evidence,
        possible_impact=issue.potential_impact,
        suggested_remediation=issue.suggested_action,
        priority_tier=priority_tier,
        priority_score=priority_score,
        priority_explanation=priority_explanation,
        uncertainties_and_unknowns=issue.unknowns,
        disclaimer=t["disclaimer"],
        created_at=datetime.now().isoformat(),
        language=lang
    )


def export_report_as_markdown(report: CivicReportDraft) -> str:
    """Formats the report into clean, readable GitHub-flavored Markdown."""
    t = TEMPLATES.get(report.language, TEMPLATES["en"])
    unknowns_str = (
        "\n".join([f"- {u}" for u in report.uncertainties_and_unknowns])
        if report.uncertainties_and_unknowns
        else "- None noted. Physical evidence was clear in photograph."
    )

    return f"""# {t['header']}
*_{t['sub_header']}_*

---

> ⚠️ **{t['disclaimer']}**

---

### 📍 {t['location_label']}
**{report.user_location}**

### ⚠️ {t['issue_label']}
**{report.issue_title}**

### 🔍 {t['condition_label']}
{report.observed_condition}

### 📸 {t['evidence_label']}
{report.supporting_visual_evidence}

### 👥 {t['impact_label']}
{report.possible_impact}

### 🛠️ {t['remediation_label']}
{report.suggested_remediation}

### 📊 {t['priority_label']}
- **Tier:** `{report.priority_tier}`
- **Score:** `{report.priority_score} / 100`
- **Breakdown:** {report.priority_explanation}

### ❓ {t['uncertainties_label']}
{unknowns_str}

---
*{t['audit_meta_label']}:* `{report.audit_id}` | *Report Reference:* `{report.report_id}` | *Timestamp:* `{report.created_at}`
"""


def export_report_as_text(report: CivicReportDraft) -> str:
    """Formats the report into plain text suitable for copying into municipal web forms or emails."""
    t = TEMPLATES.get(report.language, TEMPLATES["en"])
    unknowns_str = (
        ", ".join(report.uncertainties_and_unknowns)
        if report.uncertainties_and_unknowns
        else "None noted"
    )

    lines = [
        "================================================================================",
        t["header"],
        t["sub_header"],
        "================================================================================",
        "",
        f"[DISCLAIMER]: {report.disclaimer}",
        "",
        f"{t['location_label']}: {report.user_location}",
        f"Subject / Barrier: {report.issue_title}",
        f"{t['condition_label']}: {report.observed_condition}",
        f"{t['evidence_label']}: {report.supporting_visual_evidence}",
        f"{t['impact_label']}: {report.possible_impact}",
        f"{t['remediation_label']}: {report.suggested_remediation}",
        f"{t['priority_label']}: {report.priority_tier} ({report.priority_score}/100)",
        f"Scoring Breakdown: {report.priority_explanation}",
        f"{t['uncertainties_label']}: {unknowns_str}",
        "",
        f"Audit Reference: {report.audit_id} | Report ID: {report.report_id}",
        f"Date: {report.created_at}",
        "================================================================================",
    ]
    return "\n".join(lines)


def export_report_as_json(report: CivicReportDraft) -> str:
    """Exports the report as structured JSON."""
    return report.model_dump_json(indent=2)
