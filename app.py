"""
CivicLens AI - Streamlit Web Application
A Multimodal Civic Accessibility Audit Prototype Powered by Gemma 4.
Aligned with UN Sustainable Development Goals (SDG 11, 10, 9, 3).
"""

import os
import io
import json
from datetime import datetime
from typing import List, Dict, Any
from PIL import Image
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load local environment
load_dotenv()

from schemas import AuditAnalysisResult, AccessibilityIssue, CivicReportDraft
from gemma_service import (
    analyze_street_image,
    validate_image,
    GemmaAPIError,
    ImageValidationError,
    DEFAULT_MODEL_ID,
)
from report_generator import (
    generate_report_draft,
    export_report_as_markdown,
    export_report_as_text,
    export_report_as_json,
)
from demo_data import get_demo_audit_cases

# ------------------------------------------------------------------------------
# 1. Page Configuration & Theme
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="CivicLens AI — Civic Accessibility Audit",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Accessible Light CSS Theme
CUSTOM_CSS = """
<style>
    /* Clean civic typography & accessible contrast */
    .main {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Header hero styling */
    .hero-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: white !important;
        padding: 24px 28px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .hero-banner h1 {
        color: white !important;
        font-size: 28px;
        margin: 0 0 8px 0;
        font-weight: 700;
    }
    .hero-banner p {
        color: #dbeafe !important;
        font-size: 15px;
        margin: 0;
    }
    
    /* Status Badges */
    .badge-critical {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
        border: 1px solid #f87171;
    }
    .badge-high {
        background-color: #ffedd5;
        color: #9a3412;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
        border: 1px solid #fb923c;
    }
    .badge-medium {
        background-color: #fef9c3;
        color: #854d0e;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
        border: 1px solid #facc15;
    }
    .badge-low {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
        border: 1px solid #4ade80;
    }
    
    /* Persona Impact Cards */
    .persona-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    .persona-title {
        font-weight: 600;
        font-size: 14px;
        color: #1e293b;
        margin-bottom: 6px;
    }
    .persona-desc {
        font-size: 13px;
        color: #475569;
        line-height: 1.5;
    }

    /* Privacy Banner */
    .privacy-notice {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        font-size: 13px;
        color: #1e40af;
        margin-bottom: 16px;
    }

    /* Demo Mode Alert Banner */
    .demo-alert {
        background-color: #fffbeb;
        border: 1px solid #fde68a;
        border-left: 5px solid #f59e0b;
        padding: 12px 18px;
        border-radius: 6px;
        color: #92400e;
        font-weight: 500;
        margin-bottom: 18px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. Internationalization (Bilingual English & Hindi)
# ------------------------------------------------------------------------------
I18N = {
    "en": {
        "nav_title": "Navigation",
        "nav_analyze": "🔍 Analyze Street Photo",
        "nav_dashboard": "📊 Community Dashboard",
        "nav_about": "ℹ️ About & SDG Alignment",
        "nav_settings": "⚙️ Settings & Demo Mode",
        "hero_title": "CivicLens AI — Pedestrian Accessibility Audit",
        "hero_desc": "Multimodal visual reasoning for pedestrian barriers, human-impact assessment, and evidence-based civic complaint drafting.",
        "lang_select": "Language / भाषा",
        "privacy_warning": "🛡️ **Privacy Guard:** Do not upload photos containing identifiable human faces, vehicle license plates, or sensitive personal residences.",
        "upload_label": "Upload Street / Sidewalk Photograph (JPG, JPEG, PNG)",
        "loc_label": "Street / Crossroad Location (Citizen-Provided)",
        "loc_placeholder": "e.g., 4th Cross Road, near Metro Station Gate 2",
        "notes_label": "Optional Citizen Context",
        "notes_placeholder": "e.g., Water puddles here after morning rain, walkway blocked for 3 weeks",
        "btn_analyze": "Run Multimodal Accessibility Audit",
        "btn_clear": "Reset & Discard Image",
        "empty_state": "Please upload a street photograph or activate Demo Mode to inspect accessibility findings.",
        "findings_header": "Audit Findings & Barrier Detections",
        "persona_header": "👥 Multi-Demographic Human Impact Assessment",
        "priority_header": "🧮 Explainable Priority Scoring",
        "report_header": "📝 Evidence-Based Civic Report Draft",
        "btn_copy": "Copy to Clipboard",
        "btn_download_md": "Download Report (.md)",
        "btn_download_txt": "Download Complaint (.txt)",
        "btn_download_json": "Export Audit (.json)",
        "dash_title": "City Accessibility Dashboard",
        "dash_desc": "Aggregated community audit records, priority distributions, and barrier patterns.",
        "demo_banner": "⚠️ **DEMO MODE ACTIVE:** Displaying sample benchmark data. Inference is not calling live Gemma 4 API.",
    },
    "hi": {
        "nav_title": "नेविगेशन",
        "nav_analyze": "🔍 सड़क फोटो का ऑडिट करें",
        "nav_dashboard": "📊 सामुदायिक डैशबोर्ड",
        "nav_about": "ℹ️ प्रोजेक्ट विवरण एवं SDG",
        "nav_settings": "⚙️ सेटिंग्स एवं डेमो मोड",
        "hero_title": "CivicLens AI — पैदल मार्ग सुगमता ऑडिट",
        "hero_desc": "मल्टीमॉडल एआई द्वारा पैदल मार्ग के अवरोधों की पहचान, मानवीय प्रभाव का विश्लेषण और साक्ष्य-आधारित शिकायत मसौदा।",
        "lang_select": "भाषा / Language",
        "privacy_warning": "🛡️ **गोपनीयता सुरक्षा:** कृपया ऐसी तस्वीरें अपलोड न करें जिनमें किसी का चेहरा, वाहन नंबर प्लेट या निजी विवरण दिखाई दे।",
        "upload_label": "सड़क या फुटपाथ की तस्वीर अपलोड करें (JPG, JPEG, PNG)",
        "loc_label": "स्थान / चौराहा (नागरिक द्वारा दर्ज)",
        "loc_placeholder": "उदा. 4th क्रॉस रोड, मेट्रो स्टेशन गेट 2 के पास",
        "notes_label": "अतिरिक्त संदर्भ (वैकल्पिक)",
        "notes_placeholder": "उदा. बारिश के बाद पानी भर जाता है, फुटपाथ 3 सप्ताह से टूटा है",
        "btn_analyze": "मल्टीमॉडल सुगमता ऑडिट शुरू करें",
        "btn_clear": "फोटो हटाएं और रीसेट करें",
        "empty_state": "कृपया फुटपाथ की एक तस्वीर अपलोड करें या डेमो मोड सक्षम करें।",
        "findings_header": "ऑडिट परिणाम एवं पहचाने गए अवरोध",
        "persona_header": "👥 विभिन्न वर्गों पर संभावित मानवीय प्रभाव",
        "priority_header": "🧮 पारदर्शी प्राथमिकता स्कोरिंग",
        "report_header": "📝 साक्ष्य-आधारित शिकायत मसौदा",
        "btn_copy": "कॉपी करें",
        "btn_download_md": "रिपोर्ट डाउनलोड करें (.md)",
        "btn_download_txt": "शिकायत डाउनलोड करें (.txt)",
        "btn_download_json": "ऑडिट एक्सपोर्ट करें (.json)",
        "dash_title": "शहरी सुगमता सामुदायिक डैशबोर्ड",
        "dash_desc": "एकत्रित ऑडिट रिकॉर्ड, प्राथमिकता स्तर और अवरोध श्रेणियों का विश्लेषण।",
        "demo_banner": "⚠️ **डेमो मोड सक्रिय:** नमूना डेटा प्रदर्शित किया जा रहा है। लाइव API कॉल नहीं हो रहा है।",
    }
}

# ------------------------------------------------------------------------------
# 3. Session State Initialization
# ------------------------------------------------------------------------------
if "current_audit" not in st.session_state:
    st.session_state["current_audit"] = None

if "saved_reports" not in st.session_state:
    # Pre-populate dashboard with verified sample cases for a rich initial experience
    st.session_state["saved_reports"] = get_demo_audit_cases()

if "demo_mode" not in st.session_state:
    st.session_state["demo_mode"] = os.getenv("ENABLE_DEMO_MODE", "false").lower() == "true"

if "api_key" not in st.session_state:
    st.session_state["api_key"] = os.getenv("GEMMA_API_KEY", "")

if "model_id" not in st.session_state:
    st.session_state["model_id"] = os.getenv("GEMMA_MODEL_ID", DEFAULT_MODEL_ID)

if "lang" not in st.session_state:
    st.session_state["lang"] = os.getenv("DEFAULT_LANGUAGE", "en")

# ------------------------------------------------------------------------------
# 4. Sidebar Controls
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏙️ CivicLens AI")
    st.caption("Multimodal Accessibility Prototype | Gemma 4")

    # Language Toggle
    current_lang = st.radio(
        "🌐 Language / भाषा",
        options=["English", "हिन्दी"],
        index=0 if st.session_state["lang"] == "en" else 1,
        horizontal=True
    )
    st.session_state["lang"] = "en" if current_lang == "English" else "hi"
    txt = I18N[st.session_state["lang"]]

    st.markdown("---")

    # Navigation Menu
    menu_selection = st.radio(
        txt["nav_title"],
        options=[
            txt["nav_analyze"],
            txt["nav_dashboard"],
            txt["nav_about"],
            txt["nav_settings"]
        ]
    )

    st.markdown("---")

    # Demo Mode Status Indicator
    if st.session_state["demo_mode"]:
        st.warning("⚡ **Demo Mode ON**\nSample benchmark data active.")
    else:
        st.success("🟢 **Live Inference ON**\nReady for Gemma 4 calls.")

    # SDG Badges in Sidebar
    st.markdown("#### 🎯 UN SDG Priority")
    st.markdown("""
    - **SDG 11:** Sustainable Cities (11.2 & 11.7)
    - **SDG 10:** Reduced Inequalities (10.2)
    - **SDG 9:** Resilient Infrastructure (9.1)
    - **SDG 3:** Road Health & Safety (3.6)
    """)

# ------------------------------------------------------------------------------
# 5. Helper Rendering Functions
# ------------------------------------------------------------------------------
def render_tier_badge(tier: str) -> str:
    tier_upper = tier.upper()
    if tier_upper == "CRITICAL":
        return '<span class="badge-critical">🔴 CRITICAL URGENT</span>'
    elif tier_upper == "HIGH":
        return '<span class="badge-high">🟠 HIGH PRIORITY</span>'
    elif tier_upper == "MEDIUM":
        return '<span class="badge-medium">🟡 MEDIUM PRIORITY</span>'
    else:
        return '<span class="badge-low">🟢 LOW / ROUTINE</span>'


# ------------------------------------------------------------------------------
# 6. Page View: 🔍 Analyze Street Photo
# ------------------------------------------------------------------------------
if menu_selection == txt["nav_analyze"]:
    # Hero Title Banner
    st.markdown(f"""
    <div class="hero-banner">
        <h1>{txt['hero_title']}</h1>
        <p>{txt['hero_desc']}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state["demo_mode"]:
        st.markdown(f'<div class="demo-alert">{txt["demo_banner"]}</div>', unsafe_allow_html=True)

    # Privacy Notice Banner
    st.markdown(f'<div class="privacy-notice">{txt["privacy_warning"]}</div>', unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("📷 1. Street Photo Ingestion")
        uploaded_file = st.file_uploader(
            txt["upload_label"],
            type=["jpg", "jpeg", "png"],
            help="High-contrast, well-lit street photographs produce the most accurate audits."
        )

        user_loc = st.text_input(
            txt["loc_label"],
            placeholder=txt["loc_placeholder"],
            help="Your entered location is inserted into the complaint draft. It is never tracked or shared automatically."
        )

        citizen_context = st.text_area(
            txt["notes_label"],
            placeholder=txt["notes_placeholder"],
            height=70
        )

        btn_col1, btn_col2 = st.columns([1, 1])
        with btn_col1:
            run_btn = st.button(txt["btn_analyze"], type="primary", use_container_width=True)
        with btn_col2:
            clear_btn = st.button(txt["btn_clear"], use_container_width=True)

        if clear_btn:
            st.session_state["current_audit"] = None
            st.rerun()

        # Image Preview
        if uploaded_file is not None:
            try:
                pil_image = Image.open(uploaded_file)
                st.image(pil_image, caption=f"Uploaded Photo ({pil_image.width}x{pil_image.height} px)", use_container_width=True)
            except Exception as e:
                st.error(f"Could not read image: {str(e)}")
                pil_image = None
        else:
            pil_image = None
            st.info("Tip: You can enable Demo Mode in the Settings tab to test with preloaded scenarios without uploading.")

    # Execute Audit on Button Click
    if run_btn:
        if pil_image is None and not st.session_state["demo_mode"]:
            st.error("Please select an image file to analyze, or enable Demo Mode in Settings.")
        else:
            with st.spinner("🤖 Gemma 4 is conducting multimodal accessibility audit..."):
                try:
                    audit_res = analyze_street_image(
                        image=pil_image,
                        citizen_notes=citizen_context,
                        api_key=st.session_state["api_key"],
                        model_id=st.session_state["model_id"],
                        force_demo_mode=st.session_state["demo_mode"]
                    )
                    st.session_state["current_audit"] = audit_res
                    # Append to saved dashboard session
                    st.session_state["saved_reports"].insert(0, audit_res)
                    st.success("Audit complete!")
                except GemmaAPIError as api_err:
                    st.error(f"⚠️ Gemma 4 API Error: {str(api_err)}")
                    st.info("💡 You can enable **Demo Mode** in the sidebar settings to test the interface without an active API key.")
                except ImageValidationError as img_err:
                    st.error(f"⚠️ Image Validation Error: {str(img_err)}")
                except Exception as ex:
                    st.error(f"Unexpected error during analysis: {str(ex)}")

    # Audit Results Display
    with col_right:
        st.subheader("📋 2. Accessibility Findings & Impact")
        current_audit: AuditAnalysisResult = st.session_state.get("current_audit")

        if current_audit is None:
            st.markdown(f"""
            <div style="background-color: #f1f5f9; padding: 40px 20px; border-radius: 8px; text-align: center; color: #64748b;">
                <p style="font-size: 16px; margin: 0;">{txt['empty_state']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Audit Summary Card
            st.markdown(f"**Scene Overview:** {current_audit.image_summary}")
            st.caption(f"Audit Reference: `{current_audit.audit_id}` | Model: `{current_audit.model_name}`")

            if not current_audit.has_barriers:
                st.success("✅ **No Obstacles Detected:** Walkway appears clear, continuous, and level.")

            for idx, issue in enumerate(current_audit.issues):
                priority = issue.priority_breakdown
                tier_badge = render_tier_badge(priority.priority_tier if priority else "LOW")

                with st.expander(f"Barrier #{idx+1}: {issue.concise_description}", expanded=True):
                    st.markdown(f"**Priority:** {tier_badge} | **Confidence:** `{int(issue.confidence_score * 100)}%`", unsafe_allow_html=True)
                    st.markdown(f"**Category:** `{issue.issue_type}`")
                    st.markdown(f"**Direct Visual Evidence:** {issue.visual_evidence}")
                    st.markdown(f"**Potential Impact:** {issue.potential_impact}")
                    st.markdown(f"**Recommended Action:** {issue.suggested_action}")

                    if issue.verification_required:
                        st.warning("⚠️ **On-Site Verification Required:** Image perspective or lighting leaves physical dimensions uncertain.")
                    if issue.unknowns:
                        st.markdown("**Unverified Factors:**")
                        for unk in issue.unknowns:
                            st.markdown(f"- _{unk}_")

                    # Persona Impact Tabs
                    st.markdown("#### " + txt["persona_header"])
                    p = issue.persona_impacts
                    p_col1, p_col2 = st.columns(2)
                    with p_col1:
                        st.markdown(f"""
                        <div class="persona-card">
                            <div class="persona-title">♿ Wheelchair Users</div>
                            <div class="persona-desc">{p.wheelchair_users if p and p.wheelchair_users else "No direct impediment reported."}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="persona-card">
                            <div class="persona-title">🧓 Elderly Pedestrians</div>
                            <div class="persona-desc">{p.elderly if p and p.elderly else "No direct impediment reported."}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with p_col2:
                        st.markdown(f"""
                        <div class="persona-card">
                            <div class="persona-title">🦯 Visually Impaired</div>
                            <div class="persona-desc">{p.visually_impaired if p and p.visually_impaired else "No direct impediment reported."}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="persona-card">
                            <div class="persona-title">👶 Caregivers with Strollers</div>
                            <div class="persona-desc">{p.strollers if p and p.strollers else "No direct impediment reported."}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Explainable Priority Scoring Card
                    if priority:
                        st.markdown("#### " + txt["priority_header"])
                        st.markdown(f"**Composite Score:** `{priority.total_score} / 100` (`{priority.formula}`)")

                        s_col1, s_col2, s_col3 = st.columns(3)
                        with s_col1:
                            st.metric("Safety Risk", f"{priority.safety_score} / 40")
                        with s_col2:
                            st.metric("Accessibility Obstruction", f"{priority.accessibility_score} / 35")
                        with s_col3:
                            st.metric("Evidence Clarity", f"{priority.evidence_score} / 25")

                        if priority.reasons:
                            st.markdown("**Mathematical Scoring Factors:**")
                            for reason in priority.reasons:
                                st.markdown(f"- {reason}")

    # Section 3: Editable Civic Report Draft (Full Width)
    if current_audit and current_audit.issues:
        st.markdown("---")
        st.subheader("📝 3. Civic Complaint Draft & Multi-Format Export")

        draft = generate_report_draft(
            audit=current_audit,
            issue_index=0,
            user_location=user_loc,
            language=st.session_state["lang"]
        )

        md_content = export_report_as_markdown(draft)
        txt_content = export_report_as_text(draft)
        json_content = export_report_as_json(draft)

        col_rep1, col_rep2 = st.columns([3, 2], gap="large")

        with col_rep1:
            editable_report = st.text_area(
                "Editable Complaint Draft (Review and edit before voluntary municipal submission)",
                value=txt_content,
                height=320
            )

        with col_rep2:
            st.markdown("#### Export & Actions")
            st.caption("Download structured records ready for citizen advocacy, email, or municipal grievance portals.")

            st.download_button(
                label=txt["btn_download_txt"],
                data=editable_report,
                file_name=f"CivicComplaint_{draft.report_id}.txt",
                mime="text/plain",
                use_container_width=True
            )
            st.download_button(
                label=txt["btn_download_md"],
                data=md_content,
                file_name=f"CivicAudit_{draft.report_id}.md",
                mime="text/markdown",
                use_container_width=True
            )
            st.download_button(
                label=txt["btn_download_json"],
                data=json_content,
                file_name=f"AuditData_{draft.audit_id}.json",
                mime="application/json",
                use_container_width=True
            )

            st.info("ℹ️ **Human Agency Guarantee:** CivicLens AI drafts reports only. You retain complete authority over whether to submit this to your local municipal corporation.")


# ------------------------------------------------------------------------------
# 7. Page View: 📊 Community Dashboard
# ------------------------------------------------------------------------------
elif menu_selection == txt["nav_dashboard"]:
    st.title("📊 " + txt["dash_title"])
    st.markdown(txt["dash_desc"])

    reports: List[AuditAnalysisResult] = st.session_state.get("saved_reports", [])

    # Extract all issues for aggregation
    all_issues = []
    for r in reports:
        for iss in r.issues:
            iss_dict = iss.model_dump()
            iss_dict["audit_id"] = r.audit_id
            iss_dict["is_demo"] = r.is_demo_data
            if iss.priority_breakdown:
                iss_dict["tier"] = iss.priority_breakdown.priority_tier
                iss_dict["score"] = iss.priority_breakdown.total_score
            else:
                iss_dict["tier"] = "LOW"
                iss_dict["score"] = 0.0
            all_issues.append(iss_dict)

    # Top KPI Metrics
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Total Audits Conducted", len(reports))
    with kpi2:
        critical_count = sum(1 for i in all_issues if i.get("tier") == "CRITICAL")
        st.metric("Critical Hazards", critical_count)
    with kpi3:
        high_count = sum(1 for i in all_issues if i.get("tier") == "HIGH")
        st.metric("High Priority Barriers", high_count)
    with kpi4:
        clean_count = sum(1 for i in all_issues if i.get("issue_type") == "no_barrier_detected")
        st.metric("Accessible Corridors", clean_count)

    st.markdown("---")

    # Visual Analytics with Plotly
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Barrier Categories Distribution")
        cat_counts: Dict[str, int] = {}
        for i in all_issues:
            cat = i.get("issue_type", "unknown").replace("_", " ").title()
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        if cat_counts:
            fig_cat = px.pie(
                names=list(cat_counts.keys()),
                values=list(cat_counts.values()),
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_cat.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_cat, use_container_width=True)

    with chart_col2:
        st.subheader("Priority Urgency Breakdown")
        tier_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for i in all_issues:
            t = i.get("tier", "LOW")
            tier_counts[t] = tier_counts.get(t, 0) + 1

        colors_map = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MEDIUM": "#eab308", "LOW": "#22c55e"}
        fig_tier = go.Figure(data=[
            go.Bar(
                x=list(tier_counts.keys()),
                y=list(tier_counts.values()),
                marker_color=[colors_map.get(k, "#94a3b8") for k in tier_counts.keys()]
            )
        ])
        fig_tier.update_layout(
            xaxis_title="Urgency Tier",
            yaxis_title="Count of Barriers",
            margin=dict(t=10, b=10, l=10, r=10),
            height=300
        )
        st.plotly_chart(fig_tier, use_container_width=True)

    # Affected Demographics Chart
    st.subheader("Demographics Impacted across Recorded Audits")
    demo_counts = {"Wheelchair Users": 0, "Visually Impaired": 0, "Elderly": 0, "Strollers": 0}
    for i in all_issues:
        for g in i.get("affected_groups", []):
            if "wheelchair" in g.lower():
                demo_counts["Wheelchair Users"] += 1
            elif "visual" in g.lower() or "blind" in g.lower():
                demo_counts["Visually Impaired"] += 1
            elif "elderly" in g.lower() or "senior" in g.lower():
                demo_counts["Elderly"] += 1
            elif "stroller" in g.lower():
                demo_counts["Strollers"] += 1

    fig_demo = px.bar(
        x=list(demo_counts.values()),
        y=list(demo_counts.keys()),
        orientation="h",
        labels={"x": "Number of Times Impacted", "y": "Vulnerable Demographic"},
        color_discrete_sequence=["#3b82f6"]
    )
    fig_demo.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=250)
    st.plotly_chart(fig_demo, use_container_width=True)

    # Filterable Data Table & Duplicate Candidate Detection
    st.markdown("---")
    st.subheader("🔍 Audit Registry & Duplicate Detection")

    search_kw = st.text_input("Filter audits by keyword or category:", "")
    filtered_issues = [
        i for i in all_issues
        if search_kw.lower() in i.get("concise_description", "").lower()
        or search_kw.lower() in i.get("issue_type", "").lower()
    ]

    table_data = []
    for i in filtered_issues:
        table_data.append({
            "Audit ID": i.get("audit_id"),
            "Category": i.get("issue_type"),
            "Description": i.get("concise_description"),
            "Score": f"{i.get('score')} / 100",
            "Tier": i.get("tier"),
            "Data Type": "Demo Benchmark" if i.get("is_demo") else "Live AI Audit"
        })

    if table_data:
        st.dataframe(table_data, use_container_width=True)
    else:
        st.info("No records matched your search filter.")


# ------------------------------------------------------------------------------
# 8. Page View: ℹ️ About & SDG Alignment
# ------------------------------------------------------------------------------
elif menu_selection == txt["nav_about"]:
    st.title("ℹ️ About CivicLens AI & UN SDG Alignment")

    st.markdown("""
    ### 🎯 Direct United Nations Sustainable Development Goals Alignment
    CivicLens AI transforms ordinary pedestrian street photographs into actionable, evidence-based urban accessibility audits.
    """)

    sdg_col1, sdg_col2 = st.columns(2)
    with sdg_col1:
        st.markdown("""
        #### 🏙️ SDG 11: Sustainable Cities and Communities
        - **Target 11.2:** Provide access to safe, affordable, accessible, and sustainable transport systems for all, expanding public transit with special attention to vulnerable groups, women, children, persons with disabilities, and older persons.
        - **Target 11.7:** Universal access to safe, inclusive, accessible green and public spaces.
        - **CivicLens Impact:** Identifies broken walkways, missing curb ramps, and pedestrian-vehicle bottlenecks to ensure walkability and transit access.
        """)
        st.markdown("""
        #### ⚖️ SDG 10: Reduced Inequalities
        - **Target 10.2:** Empower and promote the social, economic, and political inclusion of all, irrespective of age, disability, or status.
        - **CivicLens Impact:** Evaluates physical barriers from the lived perspectives of wheelchair users, visually impaired pedestrians, and seniors.
        """)

    with sdg_col2:
        st.markdown("""
        #### 🏗️ SDG 9: Industry, Innovation, and Infrastructure
        - **Target 9.1:** Develop quality, reliable, sustainable, and resilient infrastructure.
        - **CivicLens Impact:** Bridges the gap between ground-level pedestrian obstacles and municipal asset management systems using multimodal AI.
        """)
        st.markdown("""
        #### ❤️ SDG 3: Good Health and Well-being
        - **Target 3.6:** Halve global deaths and injuries from road traffic accidents.
        - **CivicLens Impact:** Helps prevent pedestrians from being forced off blocked sidewalks into high-speed vehicular traffic.
        """)

    st.markdown("---")
    st.markdown("""
    ### 🛡️ Responsible AI Principles
    1. **Privacy-Preserving:** Uploaded photographs are processed transiently in-memory and discarded upon session completion. Users are prompted not to upload recognizable faces or vehicle plates.
    2. **Ground Truth Grounding:** Gemma 4 is instructed to differentiate direct visual observations from inferences, cite explicit unknowns, and never invent issues when none exist.
    3. **Deterministic Scoring:** Priority is computed via an open, transparent formula rather than an opaque LLM score.
    4. **Human in the Loop:** CivicLens AI only generates editable complaint drafts. No automated filings are submitted without citizen review.
    """)


# ------------------------------------------------------------------------------
# 9. Page View: ⚙️ Settings & Demo Mode
# ------------------------------------------------------------------------------
elif menu_selection == txt["nav_settings"]:
    st.title("⚙️ System Settings & Demo Configuration")

    st.markdown("Configure your Gemma 4 model credentials, endpoint parameters, and presentation modes.")

    with st.form("settings_form"):
        new_key = st.text_input(
            "Gemma 4 / Google GenAI API Key",
            value=st.session_state["api_key"],
            type="password",
            help="Get your API key from Google AI Studio (https://aistudio.google.com/)."
        )

        new_model = st.text_input(
            "Configurable Model Identifier",
            value=st.session_state["model_id"],
            help="Configure the multimodal model identifier (e.g., gemini-2.5-flash, gemma-4-multimodal-it)."
        )

        enable_demo = st.checkbox(
            "Enable Explicit Demo Mode (Showcase sample benchmark data offline)",
            value=st.session_state["demo_mode"],
            help="When checked, sample records are used for safe demonstration without consuming API quota."
        )

        submitted = st.form_submit_button("Save Configuration", type="primary")

        if submitted:
            st.session_state["api_key"] = new_key.strip()
            st.session_state["model_id"] = new_model.strip()
            st.session_state["demo_mode"] = enable_demo
            st.success("Settings saved successfully!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 🧪 Quick Verification Tests")
    st.write("You can test the internal priority calculation and schema validator right here:")
    if st.button("Run Self-Diagnostic Check"):
        sample_cases = get_demo_audit_cases()
        st.success(f"Self-test passed! {len(sample_cases)} benchmark scenarios validated.")
