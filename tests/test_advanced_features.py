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
