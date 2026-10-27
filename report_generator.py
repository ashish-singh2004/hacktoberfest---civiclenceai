"""
CivicLens AI - Civic Complaint Report Draft Generator
Formats audit observations into simple, citizen-friendly complaint drafts
with automated municipal department routing and 1-click WhatsApp/Email sharing.

NON-NEGOTIABLE PRINCIPLES:
- Never claim the complaint has been submitted to authorities. Draft only.
- Never invent GPS coordinates, street addresses, or legal statutes.
- User-provided location is labeled transparently.
- Plain, conversational, jargon-free English and Hindi.
- Exportable to clean Markdown, TXT, and JSON.
"""

import json
import urllib.parse
from datetime import datetime
from typing import Optional, Dict
from schemas import AuditAnalysisResult, AccessibilityIssue, CivicReportDraft


# Department routing map
DEPARTMENT_ROUTING = {
    "open_drainage_pothole": {
        "en": "Public Works Department (PWD) / Municipal Road Maintenance Division",
        "hi": "लोक निर्माण विभाग (PWD) / सड़क मरम्मत शाखा"
    },
    "collapsed_slab": {
        "en": "Public Works Department (PWD) / Civil Infrastructure Wing",
        "hi": "लोक निर्माण विभाग (PWD) / सिविल निर्माण शाखा"
    },
    "broken_footpath": {
        "en": "Municipal Corporation - Footpath & Pedestrian Infrastructure Cell",
        "hi": "नगर निगम - फुटपाथ एवं पैदल मार्ग सुधार शाखा"
    },
    "standing_water": {
        "en": "City Jal Board & Stormwater Drainage Department",
        "hi": "जल बोर्ड एवं जल-निकासी (ड्रेनेज) विभाग"
    },
    "damaged_walking_surface": {
        "en": "Ward Maintenance Engineer / Municipal Corporation",
        "hi": "वार्ड अनुरक्षण इंजीनियर / नगर पालिका परिषद"
    },
    "encroachment_obstacle": {
        "en": "Municipal Encroachment Cell & Traffic Police",
        "hi": "अतिक्रमण निरोधक दस्ता एवं यातायात पुलिस"
    },
    "missing_ramp": {
        "en": "Urban Development Authority - Barrier-Free Accessibility Division",
        "hi": "शहरी विकास प्राधिकरण - सुगम भारत / दिव्यांगजन सेल"
    },
    "waste_overflow": {
        "en": "Solid Waste Management & Sanitation Department",
        "hi": "ठोस अपशिष्ट प्रबंधन एवं स्वच्छता विभाग"
    },
    "vegetation_overgrowth": {
        "en": "Municipal Horticulture Department",
        "hi": "उद्यान एवं बागवानी विभाग"
    },
    "no_barrier_detected": {
        "en": "Municipal Maintenance Wing (Routine Sweeping)",
        "hi": "नियमित सफाई एवं रखरखाव शाखा"
    }
}

# Simplified Bilingual Template Dictionaries
TEMPLATES: Dict[str, Dict[str, str]] = {
    "en": {
        "header": "CIVIC ROAD & FOOTPATH REPAIR REQUEST",
        "sub_header": "Prepared via CivicLens AI (Citizen Accessibility Audit)",
        "disclaimer": (
            "NOTE: This is an editable citizen complaint letter prepared for your review and voluntary submission "
            "to your local ward office, municipal corporation, or PWD. No personal faces or private data are recorded."
        ),
        "location_label": "Problem Location",
        "issue_label": "Identified Hazard",
        "condition_label": "What is the problem on the street?",
        "evidence_label": "What was seen in the photo?",
        "impact_label": "Who is impacted? (Wheelchair, Elderly, Children)",
        "remediation_label": "What action is requested?",
        "authority_label": "Responsible Municipal Department",
        "priority_label": "Urgency Level",
        "uncertainties_label": "Things needing in-person check",
        "audit_meta_label": "Audit ID",
    },
    "hi": {
        "header": "नागरिक सड़क एवं फुटपाथ मरम्मत अनुरोध पत्र",
        "sub_header": "CivicLens AI द्वारा तैयार (नागरिक सुगमता रिपोर्ट)",
        "disclaimer": (
            "नोट: यह एक तैयार शिकायत पत्र है जिसे आप अपने वार्ड पार्षद, नगर निगम या PWD अधिकारी को भेज सकते हैं। "
            "इसमें किसी व्यक्ति की फोटो या निजी जानकारी शामिल नहीं है।"
        ),
        "location_label": "समस्या का स्थान",
        "issue_label": "सड़क/फुटपाथ की समस्या",
        "condition_label": "रास्ते पर क्या खराबी है?",
        "evidence_label": "तस्वीर में क्या दिखा?",
        "impact_label": "किन लोगों को आने-जाने में परेशानी होगी?",
        "remediation_label": "प्रशासन से क्या सुधार अनुरोध है?",
        "authority_label": "जिम्मेदार सरकारी विभाग",
        "priority_label": "खतरे की गंभीरता (Priority)",
        "uncertainties_label": "मौके पर जांच करने योग्य बातें",
        "audit_meta_label": "ऑडिट संदर्भ संख्या",
    }
}


def get_responsible_authority(issue_type: str, language: str = "en") -> str:
    """Returns the most appropriate municipal department for an issue."""
    key = issue_type.lower().strip()
    lang = "hi" if language == "hi" else "en"
    dept_info = DEPARTMENT_ROUTING.get(key, DEPARTMENT_ROUTING["damaged_walking_surface"])
    return dept_info.get(lang, dept_info["en"])


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

    loc = user_location.strip() if user_location and user_location.strip() else ("स्थान दर्ज नहीं किया गया" if lang == "hi" else "Location not specified by citizen")
    priority = issue.priority_breakdown
    priority_tier = priority.priority_tier if priority else "MEDIUM"
    priority_score = priority.total_score if priority else 50.0
    
    if lang == "hi":
        priority_explanation = f"खतरा: {priority.safety_score if priority else 20}/40 | रुकावट: {priority.accessibility_score if priority else 15}/35 | स्पष्टता: {priority.evidence_score if priority else 15}/25"
    else:
        priority_explanation = f"Safety Risk: {priority.safety_score if priority else 20}/40 | Obstruction: {priority.accessibility_score if priority else 15}/35 | Clarity: {priority.evidence_score if priority else 15}/25"

    dept = get_responsible_authority(issue.issue_type, lang)
    report_id = f"REP-{datetime.now().strftime('%Y%m%d')}-{issue.issue_id}"

    return CivicReportDraft(
        report_id=report_id,
        audit_id=audit.audit_id,
        issue_title=issue.concise_description,
        user_location=loc,
        observed_condition=issue.concise_description,
        supporting_visual_evidence=issue.visual_evidence,
        possible_impact=issue.potential_impact,
        suggested_remediation=issue.suggested_action,
        responsible_authority=dept,
        priority_tier=priority_tier,
        priority_score=priority_score,
        priority_explanation=priority_explanation,
        uncertainties_and_unknowns=issue.unknowns,
        disclaimer=t["disclaimer"],
        created_at=datetime.now().isoformat(),
        language=lang
    )


def export_report_as_markdown(report: CivicReportDraft) -> str:
    """Formats the report into clean, readable Markdown."""
    t = TEMPLATES.get(report.language, TEMPLATES["en"])
    unknowns_str = (
        "\n".join([f"- {u}" for u in report.uncertainties_and_unknowns])
        if report.uncertainties_and_unknowns
        else ("- कोई अस्पष्टता नहीं मिली।" if report.language == "hi" else "- None noted. Visual evidence was clear.")
    )

    return f"""# {t['header']}
*_{t['sub_header']}_*

---

> ⚠️ **{t['disclaimer']}**

---

### 📍 {t['location_label']}
**{report.user_location}**

### 🏛️ {t['authority_label']}
**{report.responsible_authority}**

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
*{t['audit_meta_label']}:* `{report.audit_id}` | *Report Reference:* `{report.report_id}` | *Date:* `{report.created_at[:10]}`
"""


def export_report_as_text(report: CivicReportDraft) -> str:
    """Formats the report into plain text suitable for copying into municipal web forms or WhatsApp."""
    t = TEMPLATES.get(report.language, TEMPLATES["en"])
    unknowns_str = (
        ", ".join(report.uncertainties_and_unknowns)
        if report.uncertainties_and_unknowns
        else ("कोई नहीं" if report.language == "hi" else "None noted")
    )

    lines = [
        "================================================================================",
        t["header"],
        t["sub_header"],
        "================================================================================",
        "",
        f"[DISCLAIMER / सूचना]: {report.disclaimer}",
        "",
        f"📍 {t['location_label']}: {report.user_location}",
        f"🏛️ {t['authority_label']}: {report.responsible_authority}",
        f"⚠️ {t['issue_label']}: {report.issue_title}",
        f"🔍 {t['condition_label']}: {report.observed_condition}",
        f"📸 {t['evidence_label']}: {report.supporting_visual_evidence}",
        f"👥 {t['impact_label']}: {report.possible_impact}",
        f"🛠️ {t['remediation_label']}: {report.suggested_remediation}",
        f"📊 {t['priority_label']}: {report.priority_tier} ({report.priority_score}/100)",
        f"Scoring / विवरण: {report.priority_explanation}",
        f"❓ {t['uncertainties_label']}: {unknowns_str}",
        "",
        f"Audit Reference: {report.audit_id} | Report ID: {report.report_id}",
        "================================================================================",
    ]
    return "\n".join(lines)


def export_report_as_json(report: CivicReportDraft) -> str:
    """Exports the report as structured JSON."""
    return report.model_dump_json(indent=2)


def build_whatsapp_share_url(report: CivicReportDraft) -> str:
    """Builds a WhatsApp click-to-chat URL with pre-filled civic report summary."""
    text = (
        f"🚨 *Civic Issue Report via CivicLens AI*\n\n"
        f"📍 *Location:* {report.user_location}\n"
        f"⚠️ *Problem:* {report.issue_title}\n"
        f"🏛️ *Dept:* {report.responsible_authority}\n"
        f"👥 *Impact:* {report.possible_impact}\n"
        f"🛠️ *Requested Fix:* {report.suggested_remediation}\n"
        f"📊 *Priority:* {report.priority_tier} ({report.priority_score}/100)\n\n"
        f"_Kindly address this pedestrian hazard._"
    )
    encoded = urllib.parse.quote(text)
    return f"https://api.whatsapp.com/send?text={encoded}"
