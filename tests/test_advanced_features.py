"""
Unit tests for Advanced Hackathon Winning Features:
- Visual Grounding / AI Obstacle Overlay
- Audio Accessibility Narration (gTTS)
- Municipal Department Router & Quick Share Links
"""

import pytest
from PIL import Image
from visual_overlay import draw_obstacle_overlay
from audio_service import build_spoken_summary, generate_audio_briefing
from report_generator import get_responsible_authority


def test_draw_obstacle_overlay():
    img = Image.new("RGB", (640, 480), color=(120, 120, 120))
    annotated = draw_obstacle_overlay(
        image=img,
        issue_type="open_drainage_pothole",
        label="Deep Pothole",
        tier="CRITICAL",
        box=(50, 100, 550, 400)
    )
    assert annotated is not None
    assert annotated.size == (640, 480)
    assert annotated.mode == "RGB"


def test_draw_obstacle_overlay_default_box():
    img = Image.new("RGB", (400, 300), color=(100, 100, 100))
    annotated = draw_obstacle_overlay(
        image=img,
        issue_type="broken_footpath",
        label="Broken Slab",
        tier="HIGH",
        box=None
    )
    assert annotated.size == (400, 300)


def test_build_spoken_summary():
    hi_summary = build_spoken_summary("सड़क पर गड्ढा", "व्हीलचेयर गिर सकती है", lang="hi")
    en_summary = build_spoken_summary("Deep Pothole", "Wheelchair may tip over", lang="en")
    assert "सुगमता सूचना" in hi_summary
    assert "Accessibility alert" in en_summary


def test_generate_audio_briefing_non_empty():
    audio = generate_audio_briefing("Test audio warning", lang="en")
    # May be bytes if online or None if network restricted
    if audio is not None:
        assert isinstance(audio, bytes)
        assert len(audio) > 100


def test_department_routing_all_keys():
    keys = ["open_drainage_pothole", "broken_footpath", "standing_water", "waste_overflow", "missing_ramp"]
    for k in keys:
        dept_en = get_responsible_authority(k, "en")
        dept_hi = get_responsible_authority(k, "hi")
        assert len(dept_en) > 5
        assert len(dept_hi) > 5


def test_repair_estimator():
    from repair_estimator import get_repair_estimate
    est_en = get_repair_estimate("open_drainage_pothole", "CRITICAL", "en")
    assert "₹" in est_en["cost"]
    assert "Within" in est_en["sla"]
    assert len(est_en["materials"]) > 0

    est_hi = get_repair_estimate("broken_footpath", "HIGH", "hi")
    assert "घंटे के अंदर" in est_hi["sla"]
    assert "पेवर ब्लॉक" in ", ".join(est_hi["materials"])


def test_share_channels_and_html_certificate():
    from schemas import CivicReportDraft
    from report_generator import build_twitter_share_url, build_email_mailto_url, generate_printable_html_certificate

    draft = CivicReportDraft(
        report_id="REP-TEST-123",
        audit_id="AUD-TEST-123",
        issue_title="Deep Pothole on Main Road",
        user_location="Sector 14 Metro",
        observed_condition="Severe 40cm cavity",
        supporting_visual_evidence="Cavity with asphalt debris",
        possible_impact="Tripping hazard for elderly",
        suggested_remediation="Bitumen patch",
        responsible_authority="Public Works Department",
        priority_tier="CRITICAL",
        priority_score=88.0,
        priority_explanation="High risk",
        uncertainties_and_unknowns=[],
        disclaimer="Draft only",
        created_at="2026-10-27T12:00:00Z",
        language="en"
    )

    tw = build_twitter_share_url(draft)
    assert "twitter.com/intent/tweet" in tw
    assert "CivicLensAI" in tw

    email = build_email_mailto_url(draft)
    assert "mailto:commissioner@mcd.gov.in" in email
    assert "Sector%2014%20Metro" in email

    html_cert = generate_printable_html_certificate(draft)
    assert "<!DOCTYPE html>" in html_cert
    assert "Civic Inspection Certificate" in html_cert
    assert "REP-TEST-123" in html_cert

