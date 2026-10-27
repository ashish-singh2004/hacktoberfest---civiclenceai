"""
Integration tests verifying app module imports, demo data integration,
and end-to-end report generation pipeline.
"""

import pytest
from schemas import AuditAnalysisResult
from demo_data import get_demo_audit_cases
from report_generator import generate_report_draft, export_report_as_text
from priority_engine import calculate_priority_score


def test_demo_cases_integration():
    cases = get_demo_audit_cases()
    assert len(cases) >= 3

    for audit in cases:
        assert isinstance(audit, AuditAnalysisResult)
        assert audit.is_demo_data is True
        assert len(audit.issues) >= 1

        for issue in audit.issues:
            assert issue.priority_breakdown is not None
            assert 0.0 <= issue.priority_breakdown.total_score <= 100.0

            # Test generating draft report from this case
            draft = generate_report_draft(audit, issue_index=0, user_location="Test Location", language="en")
            assert draft.report_id.startswith("REP-")
            assert draft.priority_score == issue.priority_breakdown.total_score

            txt = export_report_as_text(draft)
            assert "CIVIC ACCESSIBILITY AUDIT" in txt
            assert "Test Location" in txt
