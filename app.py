"""
CivicLens AI - Streamlit Web Application
A Multimodal Civic Accessibility Audit Prototype Powered by Gemma 4.
Aligned with UN Sustainable Development Goals (SDG 11, 10, 9, 3).

WINNING HACKATHON ENHANCEMENTS:
- Simple, friendly everyday language (Bilingual English & आसान हिन्दी).
- Visual Grounding / AI Obstacle Overlay (interactive bounding box).
- Voice Accessibility (Audio speech briefing for visually impaired).
- Municipal Department Router with 1-click WhatsApp & Email dispatch.
- Interactive City Walkability Map & Neighborhood Accessibility Index.
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
    build_whatsapp_share_url,
    build_twitter_share_url,
    build_email_mailto_url,
    generate_printable_html_certificate,
    get_responsible_authority,
)
from demo_data import get_demo_audit_cases
from visual_overlay import draw_obstacle_overlay
from audio_service import generate_audio_briefing, build_spoken_summary
from repair_estimator import get_repair_estimate


# ------------------------------------------------------------------------------
# 1. Page Configuration & Enforced Light Theme
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="CivicLens AI — Walkway & Road Accessibility Checker",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Accessible Light CSS Theme
CUSTOM_CSS = """
<style>
    /* Enforce light background & dark text everywhere */
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #1e293b !important;
    }

    .stTextInput input, .stTextArea textarea, .stSelectbox div {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
    }

    [data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
    }

    .main {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Header hero styling */
    .hero-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: white !important;
        padding: 22px 26px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .hero-banner h1 {
        color: white !important;
        font-size: 26px;
        margin: 0 0 6px 0;
        font-weight: 700;
    }
    .hero-banner p {
        color: #dbeafe !important;
        font-size: 14.5px;
        margin: 0;
    }
    
    /* Status Badges */
    .badge-critical {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
        border: 1px solid #f87171;
    }
    .badge-high {
        background-color: #ffedd5;
        color: #9a3412;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
        border: 1px solid #fb923c;
    }
    .badge-medium {
        background-color: #fef9c3;
        color: #854d0e;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 12px;
        border: 1px solid #facc15;
    }
    .badge-low {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 12px;
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
        padding: 12px 14px;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.04);
    }
    .persona-title {
        font-weight: 600;
        font-size: 13.5px;
        color: #1e293b;
        margin-bottom: 4px;
    }
    .persona-desc {
        font-size: 12.5px;
        color: #475569;
        line-height: 1.45;
    }

    /* Privacy Banner */
    .privacy-notice {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        font-size: 13px;
        color: #1e40af;
        margin-bottom: 16px;
    }

    /* Demo Alert */
    .demo-alert {
        background-color: #fffbeb;
        border: 1px solid #fde68a;
        border-left: 5px solid #f59e0b;
        padding: 10px 16px;
        border-radius: 6px;
        color: #92400e;
        font-weight: 500;
        margin-bottom: 16px;
        font-size: 13.5px;
    }

    /* Action Buttons */
    .wa-button {
        display: inline-block;
        background-color: #25d366;
        color: white !important;
        text-decoration: none;
        padding: 9px 16px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 13px;
        text-align: center;
        width: 100%;
        margin-top: 6px;
    }
    .tweet-button {
        display: inline-block;
        background-color: #0284c7;
        color: white !important;
        text-decoration: none;
        padding: 9px 16px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 13px;
        text-align: center;
        width: 100%;
        margin-top: 6px;
    }
    .email-button {
        display: inline-block;
        background-color: #4f46e5;
        color: white !important;
        text-decoration: none;
        padding: 9px 16px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 13px;
        text-align: center;
        width: 100%;
        margin-top: 6px;
    }
    .simple-summary-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 5px solid #16a34a;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 14px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    }
    .estimate-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #2563eb;
        border-radius: 8px;
        padding: 14px 16px;
        margin-top: 12px;
        margin-bottom: 14px;
    }
    .compliance-pill {
        display: inline-block;
        background: #fee2e2;
        color: #991b1b;
        font-size: 11.5px;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        border: 1px solid #f87171;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. Simplified, Everyday Bilingual Vocabulary (English & आसान हिन्दी)
# ------------------------------------------------------------------------------
I18N = {
    "en": {
        "nav_title": "Menu",
        "nav_analyze": "🔍 Check Road / Footpath Photo",
        "nav_dashboard": "📊 City Walkability Map",
        "nav_about": "ℹ️ Project Goal & UN SDG",
        "nav_settings": "⚙️ Settings & Demo Mode",
        "hero_title": "CivicLens AI — Smart Walkway & Road Checker",
        "hero_desc": "AI detects road hazards from street photos, shows who is at risk (wheelchair users, elderly, kids), and drafts 1-click complaint letters for city officials.",
        "lang_select": "Language / भाषा",
        "privacy_warning": "🛡️ **Privacy Guard:** Please do not upload photos showing people's faces, car license plates, or house numbers.",
        "upload_label": "Upload a photo of a street, sidewalk, or road (JPG, PNG)",
        "loc_label": "Where was this photo taken? (Optional Location)",
        "loc_placeholder": "e.g., Near Metro Gate 2, Main Market Road",
        "notes_label": "Any extra notes? (Optional)",
        "notes_placeholder": "e.g., Water stays here after rain, sidewalk broken for 2 weeks",
        "btn_analyze": "🚀 Run AI Accessibility Check",
        "btn_clear": "🗑️ Discard & Reset",
        "empty_state": "Upload a road or footpath photograph above, or turn on Demo Mode to see a sample check.",
        "findings_header": "🔍 What Did AI Find?",
        "persona_header": "👥 Who is Impacted?",
        "priority_header": "⚠️ How Urgent is This?",
        "report_header": "📝 Ready-to-Send Complaint Letter",
        "audio_title": "🔊 Voice Alert for Visually Impaired (Audio)",
        "audio_generating": "Generating spoken voice alert...",
        "overlay_toggle": "👁️ Highlight Detected Obstacle (AI Vision)",
        "btn_copy": "Copy to Clipboard",
        "btn_download_md": "Download Report (.md)",
        "btn_download_txt": "Download Letter (.txt)",
        "btn_download_json": "Export Data (.json)",
        "dash_title": "City Accessibility & Hazard Map",
        "dash_desc": "Live community hazard registry, walkability score, and department routing.",
        "demo_banner": "⚡ **DEMO MODE IS ON:** Showing benchmark sample data. Real Gemma 4 API is not being called.",
    },
    "hi": {
        "nav_title": "मेन्यू",
        "nav_analyze": "🔍 सड़क/फुटपाथ फोटो की जांच करें",
        "nav_dashboard": "📊 शहर का सुगमता नक्शा (Map)",
        "nav_about": "ℹ️ प्रोजेक्ट विवरण एवं SDG",
        "nav_settings": "⚙️ सेटिंग्स एवं डेमो मोड",
        "hero_title": "सिविकलेंस AI — सुरक्षित सड़क और फुटपाथ जांच",
        "hero_desc": "AI सड़क और फुटपाथ के गड्ढों व रुकावटों को पहचानता है, दिव्यांगों व बुजुर्गों की सुरक्षा जांचता है, और नगर निगम के लिए 1-क्लिक शिकायत पत्र बनाता है।",
        "lang_select": "भाषा / Language",
        "privacy_warning": "🛡️ **गोपनीयता सुरक्षा:** कृपया ऐसी फोटो अपलोड न करें जिसमें किसी का चेहरा, गाड़ी की नंबर प्लेट या घर का नंबर दिखे।",
        "upload_label": "सड़क या फुटपाथ की फोटो अपलोड करें (JPG, PNG)",
        "loc_label": "यह फोटो किस जगह की है? (स्थान दर्ज करें - वैकल्पिक)",
        "loc_placeholder": "उदा. मेट्रो गेट 2 के पास, मुख्य बाजार रोड",
        "notes_label": "कोई अन्य जानकारी? (वैकल्पिक)",
        "notes_placeholder": "उदा. बारिश में यहां पानी भर जाता है, 2 हफ्ते से टूटा है",
        "btn_analyze": "🚀 AI द्वारा जांच शुरू करें",
        "btn_clear": "🗑️ फोटो हटाएं और रीसेट करें",
        "empty_state": "कृपया ऊपर एक फोटो अपलोड करें या डेमो मोड ऑन करके नमूना परिणाम देखें।",
        "findings_header": "🔍 AI को रास्ते पर क्या समस्या मिली?",
        "persona_header": "👥 किन लोगों को आने-जाने में परेशानी होगी?",
        "priority_header": "⚠️ समस्या कितनी गंभीर है?",
        "report_header": "📝 नगर निगम को भेजने हेतु तैयार शिकायत पत्र",
        "audio_title": "🔊 दृष्टिबाधित साथियों के लिए ऑडियो अलर्ट (आवाज में सुनें)",
        "audio_generating": "आवाज तैयार की जा रही है...",
        "overlay_toggle": "👁️ फोटो पर समस्या को हाइलाइट करें (AI Vision)",
        "btn_copy": "कॉपी करें",
        "btn_download_md": "रिपोर्ट डाउनलोड करें (.md)",
        "btn_download_txt": "शिकायत पत्र डाउनलोड करें (.txt)",
        "btn_download_json": "डेटा डाउनलोड करें (.json)",
        "dash_title": "शहरी सुगमता एवं खतरा नक्शा (Hazard Map)",
        "dash_desc": "सामुदायिक रिपोर्ट, शहर का वॉकेबिलिटी स्कोर और संबंधित सरकारी विभाग।",
        "demo_banner": "⚡ **डेमो मोड सक्रिय है:** नमूना बेंचमार्क डेटा दिखाया जा रहा है। लाइव API कॉल नहीं हो रहा है।",
    }
}

# ------------------------------------------------------------------------------
# 3. Session State Initialization
# ------------------------------------------------------------------------------
if "current_audit" not in st.session_state:
    st.session_state["current_audit"] = None

if "saved_reports" not in st.session_state:
    st.session_state["saved_reports"] = get_demo_audit_cases()

if "demo_mode" not in st.session_state:
    st.session_state["demo_mode"] = os.getenv("ENABLE_DEMO_MODE", "false").lower() == "true"

if "api_key" not in st.session_state:
    st.session_state["api_key"] = os.getenv("GEMMA_API_KEY", "")

if "model_id" not in st.session_state:
    st.session_state["model_id"] = os.getenv("GEMMA_MODEL_ID", DEFAULT_MODEL_ID)

if "lang" not in st.session_state:
    st.session_state["lang"] = os.getenv("DEFAULT_LANGUAGE", "en")

if "show_overlay" not in st.session_state:
    st.session_state["show_overlay"] = True

# ------------------------------------------------------------------------------
# 4. Sidebar Controls
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏙️ CivicLens AI")
    st.caption("Multimodal Accessibility Prototype | Gemma 4")

    # Language Selector
    current_lang = st.radio(
        "🌐 Language / भाषा",
        options=["English", "हिन्दी"],
        index=0 if st.session_state["lang"] == "en" else 1,
        horizontal=True
    )
    st.session_state["lang"] = "en" if current_lang == "English" else "hi"
    txt = I18N[st.session_state["lang"]]

    st.markdown("---")

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

    # Mode Indicator
    if st.session_state["demo_mode"]:
        st.warning("⚡ **Demo Mode ON**\nSample benchmark records active.")
    else:
        st.success("🟢 **Live Inference ON**\nConnected to Gemma 4 API.")

    st.markdown("#### 🎯 UN SDG Alignment")
    st.markdown("""
    - **SDG 11:** Safe Cities & Walkable Streets
    - **SDG 10:** Disability & Wheelchair Rights
    - **SDG 9:** Better Urban Infrastructure
    - **SDG 3:** Pedestrian Road Safety
    """)

# ------------------------------------------------------------------------------
# 5. Helper Rendering Functions
# ------------------------------------------------------------------------------
def render_tier_badge(tier: str, lang: str = "en") -> str:
    tier_upper = tier.upper()
    if lang == "hi":
        names = {
            "CRITICAL": "🔴 अति-गंभीर (आपातकालीन सुधार)",
            "HIGH": "🟠 गंभीर (जल्द सुधार आवश्यक)",
            "MEDIUM": "🟡 मध्यम (नियमित मरम्मत)",
            "LOW": "🟢 सामान्य / सुरक्षित रास्ता"
        }
    else:
        names = {
            "CRITICAL": "🔴 CRITICAL (Immediate Hazard)",
            "HIGH": "🟠 HIGH (Urgent Fix Needed)",
            "MEDIUM": "🟡 MEDIUM (Routine Maintenance)",
            "LOW": "🟢 LOW / SAFE WALKWAY"
        }
    cls_name = f"badge-{tier_upper.lower()}"
    label = names.get(tier_upper, tier_upper)
    return f'<span class="{cls_name}">{label}</span>'


# ------------------------------------------------------------------------------
# 6. Page View: 🔍 Analyze Street Photo
# ------------------------------------------------------------------------------
if menu_selection == txt["nav_analyze"]:
    st.markdown(f"""
    <div class="hero-banner">
        <h1>{txt['hero_title']}</h1>
        <p>{txt['hero_desc']}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state["demo_mode"]:
        st.markdown(f'<div class="demo-alert">{txt["demo_banner"]}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="privacy-notice">{txt["privacy_warning"]}</div>', unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("📷 1. " + ("फोटो अपलोड करें" if st.session_state["lang"] == "hi" else "Upload Photograph"))
        uploaded_file = st.file_uploader(
            txt["upload_label"],
            type=["jpg", "jpeg", "png"],
            help="Take or upload a clear picture of a pothole, broken sidewalk, or street obstacle."
        )

        user_loc = st.text_input(
            txt["loc_label"],
            placeholder=txt["loc_placeholder"]
        )

        citizen_context = st.text_area(
            txt["notes_label"],
            placeholder=txt["notes_placeholder"],
            height=65
        )

        btn_col1, btn_col2 = st.columns([1, 1])
        with btn_col1:
            run_btn = st.button(txt["btn_analyze"], type="primary", use_container_width=True)
        with btn_col2:
            clear_btn = st.button(txt["btn_clear"], use_container_width=True)

        if clear_btn:
            st.session_state["current_audit"] = None
            st.rerun()

        # Image Ingestion & Visual Grounding Preview
        if uploaded_file is not None:
            try:
                pil_image = Image.open(uploaded_file)
                st.session_state["last_uploaded_image"] = pil_image

                # AI Overlay Toggle
                show_box = st.checkbox(txt["overlay_toggle"], value=True)

                current_audit = st.session_state.get("current_audit")
                if show_box and current_audit and current_audit.issues:
                    first_iss = current_audit.issues[0]
                    tier = first_iss.priority_breakdown.priority_tier if first_iss.priority_breakdown else "HIGH"
                    annotated_img = draw_obstacle_overlay(
                        pil_image,
                        issue_type=first_iss.issue_type,
                        label=first_iss.concise_description[:30],
                        tier=tier
                    )
                    st.image(annotated_img, caption="AI Vision Highlighted Obstacle", use_container_width=True)
                else:
                    st.image(pil_image, caption=f"Uploaded Photo ({pil_image.width}x{pil_image.height} px)", use_container_width=True)

            except Exception as e:
                st.error(f"Could not load image: {str(e)}")
                pil_image = None
        else:
            pil_image = None

    # Analysis Action
    if run_btn:
        if pil_image is None and not st.session_state["demo_mode"]:
            st.error("Please upload an image first, or toggle Demo Mode in Settings.")
        else:
            with st.spinner("🤖 Gemma 4 is scanning the street photograph for accessibility barriers..."):
                try:
                    audit_res = analyze_street_image(
                        image=pil_image,
                        citizen_notes=citizen_context,
                        api_key=st.session_state["api_key"],
                        model_id=st.session_state["model_id"],
                        force_demo_mode=st.session_state["demo_mode"]
                    )
                    st.session_state["current_audit"] = audit_res
                    st.session_state["saved_reports"].insert(0, audit_res)
                    st.success("✅ Analysis Complete!")
                    st.rerun()
                except GemmaAPIError as api_err:
                    st.error(f"⚠️ Gemma 4 API Error: {str(api_err)}")
                    st.info("💡 You can switch to **Demo Mode** in Settings to test without internet or quota.")
                except ImageValidationError as img_err:
                    st.error(f"⚠️ Image Error: {str(img_err)}")
                except Exception as ex:
                    st.error(f"Unexpected error during analysis: {str(ex)}")

    # Audit Findings Panel
    with col_right:
        st.subheader("📋 2. " + txt["findings_header"])
        current_audit: AuditAnalysisResult = st.session_state.get("current_audit")

        if current_audit is None:
            st.markdown(f"""
            <div style="background-color: #f1f5f9; padding: 40px 20px; border-radius: 8px; text-align: center; color: #64748b;">
                <p style="font-size: 15px; margin: 0;">{txt['empty_state']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"**Scene Overview:** {current_audit.image_summary}")
            st.caption(f"Ref: `{current_audit.audit_id}` | Model: `{current_audit.model_name}`")

            if not current_audit.has_barriers:
                st.success("✅ **Clean Walkway:** No major physical barriers detected. Safe for pedestrians.")

            for idx, issue in enumerate(current_audit.issues):
                priority = issue.priority_breakdown
                tier_badge = render_tier_badge(priority.priority_tier if priority else "LOW", st.session_state["lang"])
                est = get_repair_estimate(issue.issue_type, priority.priority_tier if priority else "HIGH", st.session_state["lang"])

                with st.expander(f"⚠️ {issue.concise_description}", expanded=True):
                    st.markdown(f"**Urgency / स्तर:** {tier_badge} | **Confidence:** `{int(issue.confidence_score * 100)}%`", unsafe_allow_html=True)

                    dept = get_responsible_authority(issue.issue_type, st.session_state["lang"])

                    # 1. SIMPLE PLAIN CITIZEN SUMMARY (आसान भाषा में सारांश)
                    if st.session_state["lang"] == "hi":
                        st.markdown(f"""
                        <div class="simple-summary-card">
                            <h4 style="margin: 0 0 8px 0; color: #166534;">💡 आसान सारांश (Citizen Quick Summary)</h4>
                            <p style="margin: 0 0 4px 0;">🛑 <strong>समस्या:</strong> {issue.concise_description}</p>
                            <p style="margin: 0 0 4px 0;">⚠️ <strong>खतरा:</strong> {issue.potential_impact}</p>
                            <p style="margin: 0 0 4px 0;">🛠️ <strong>तुरंत क्या करें:</strong> {issue.suggested_action}</p>
                            <p style="margin: 0;">🏛️ <strong>किसे शिकायत भेजें:</strong> <strong>{dept}</strong></p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="simple-summary-card">
                            <h4 style="margin: 0 0 8px 0; color: #166534;">💡 Simple Citizen Summary (In Plain Words)</h4>
                            <p style="margin: 0 0 4px 0;">🛑 <strong>The Issue:</strong> {issue.concise_description}</p>
                            <p style="margin: 0 0 4px 0;">⚠️ <strong>Why It's Dangerous:</strong> {issue.potential_impact}</p>
                            <p style="margin: 0 0 4px 0;">🛠️ <strong>Recommended Fix:</strong> {issue.suggested_action}</p>
                            <p style="margin: 0;">🏛️ <strong>Responsible Authority:</strong> <strong>{dept}</strong></p>
                        </div>
                        """, unsafe_allow_html=True)

                    # 2. MUNICIPAL REPAIR COST & SLA ESTIMATOR (CPWD Schedule of Rates)
                    st.markdown(f"""
                    <div class="estimate-box">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <strong style="color: #1e3a8a; font-size: 14px;">🏗️ {'स्मार्ट मरम्मत अनुमान (Civil Repair Estimate)' if st.session_state['lang'] == 'hi' else 'Smart Civil Repair & Cost Estimate'}</strong>
                            <span class="compliance-pill">{'RPwD अधिनियम 2016 उल्लंघन' if st.session_state['lang'] == 'hi' else 'RPwD Act 2016 Non-Compliant'}</span>
                        </div>
                        <div style="font-size: 13px; line-height: 1.6; color: #334155;">
                            <div>💵 <strong>{'अनुमानित खर्च:' if st.session_state['lang'] == 'hi' else 'Estimated Budget:'}</strong> {est['cost']}</div>
                            <div>⏱️ <strong>{'समाधान समय (SLA):' if st.session_state['lang'] == 'hi' else 'Resolution Timeframe:'}</strong> {est['sla']}</div>
                            <div>🛠️ <strong>{'जरूरी सामग्री:' if st.session_state['lang'] == 'hi' else 'Materials Needed:'}</strong> {', '.join(est['materials'])}</div>
                            <div>👷 <strong>{'जिम्मेदार दल:' if st.session_state['lang'] == 'hi' else 'Maintenance Crew:'}</strong> {est['crew']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 3. AUDIO NARRATION FOR BLIND / VISUALLY IMPAIRED
                    st.markdown(f"#### {txt['audio_title']}")
                    spoken_text = build_spoken_summary(issue.concise_description, issue.potential_impact, st.session_state["lang"])
                    audio_bytes = generate_audio_briefing(spoken_text, st.session_state["lang"])
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")
                    else:
                        st.caption("Audio narration ready. (Internet required for voice synthesis)")

                    # 4. PERSONA IMPACT CARDS
                    st.markdown("#### " + txt["persona_header"])
                    p = issue.persona_impacts
                    p_col1, p_col2 = st.columns(2)
                    with p_col1:
                        st.markdown(f"""
                        <div class="persona-card">
                            <div class="persona-title">♿ Wheelchair Users / व्हीलचेयर</div>
                            <div class="persona-desc">{p.wheelchair_users if p and p.wheelchair_users else "No direct blockage reported."}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="persona-card">
                            <div class="persona-title">🧓 Elderly People / बुजुर्ग</div>
                            <div class="persona-desc">{p.elderly if p and p.elderly else "No direct tripping risk reported."}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with p_col2:
                        st.markdown(f"""
                        <div class="persona-card">
                            <div class="persona-title">🦯 Visually Impaired / दृष्टिबाधित</div>
                            <div class="persona-desc">{p.visually_impaired if p and p.visually_impaired else "No direct tactile hazard reported."}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="persona-card">
                            <div class="persona-title">👶 Strollers / बच्चों की गाड़ी</div>
                            <div class="persona-desc">{p.strollers if p and p.strollers else "No direct wheel wedge reported."}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # 5. EXPLAINABLE PRIORITY SCORE METER
                    if priority:
                        st.markdown("#### " + txt["priority_header"])
                        st.progress(int(priority.total_score), text=f"Priority Score: {priority.total_score} / 100")

                        s_col1, s_col2, s_col3 = st.columns(3)
                        with s_col1:
                            st.metric("Safety Danger (0-40)", f"{priority.safety_score}")
                        with s_col2:
                            st.metric("Walkway Block (0-35)", f"{priority.accessibility_score}")
                        with s_col3:
                            st.metric("Photo Clarity (0-25)", f"{priority.evidence_score}")

    # SECTION 3: 1-CLICK COMPLAINT LETTER & MULTI-CHANNEL SHARING
    if current_audit and current_audit.issues:
        st.markdown("---")
        st.subheader("📝 3. " + txt["report_header"])

        draft = generate_report_draft(
            audit=current_audit,
            issue_index=0,
            user_location=user_loc,
            language=st.session_state["lang"]
        )

        md_content = export_report_as_markdown(draft)
        txt_content = export_report_as_text(draft)
        json_content = export_report_as_json(draft)
        wa_url = build_whatsapp_share_url(draft)
        tw_url = build_twitter_share_url(draft)
        mail_url = build_email_mailto_url(draft)
        cert_html = generate_printable_html_certificate(draft)

        col_rep1, col_rep2 = st.columns([3, 2], gap="large")

        with col_rep1:
            editable_report = st.text_area(
                "Editable Complaint Text (Feel free to edit before sending):",
                value=txt_content,
                height=320
            )

        with col_rep2:
            st.markdown("#### 🚀 1-Click Citizen Action")
            st.caption("Send this issue directly to authorities or social media for prompt action:")

            # Multi-channel dispatch buttons
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-button">📲 Share on WhatsApp (वॉट्सऐप पर भेजें)</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="{tw_url}" target="_blank" class="tweet-button">🐦 Post Alert on Twitter / X (ट्विटर पर पोस्ट करें)</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="{mail_url}" target="_blank" class="email-button">✉️ Email Ward Official (अधिकारी को ईमेल करें)</a>', unsafe_allow_html=True)

            st.markdown("---")
            st.caption("📥 Download Official Copies:")

            st.download_button(
                label="🖨️ Download Printable Inspection Certificate (.html)",
                data=cert_html,
                file_name=f"Certificate_{draft.report_id}.html",
                mime="text/html",
                use_container_width=True
            )
            st.download_button(
                label=txt["btn_download_txt"],
                data=editable_report,
                file_name=f"Complaint_{draft.report_id}.txt",
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



# ------------------------------------------------------------------------------
# 7. Page View: 📊 City Walkability Map & Dashboard
# ------------------------------------------------------------------------------
elif menu_selection == txt["nav_dashboard"]:
    st.title("📊 " + txt["dash_title"])
    st.markdown(txt["dash_desc"])

    reports: List[AuditAnalysisResult] = st.session_state.get("saved_reports", [])

    all_issues = []
    # Synthetic coordinates around Delhi/NCR for rich demo map visualization
    sample_coords = [
        {"lat": 28.6139, "lon": 77.2090, "area": "Connaught Place"},
        {"lat": 28.6328, "lon": 77.2197, "area": "Barakhamba Road"},
        {"lat": 28.5494, "lon": 77.2001, "area": "Hauz Khas Walkway"},
        {"lat": 28.7041, "lon": 77.1025, "area": "Pitampura Sector 9"},
        {"lat": 28.5921, "lon": 77.0460, "area": "Dwarka Sector 12"},
    ]

    for idx, r in enumerate(reports):
        for iss in r.issues:
            iss_dict = iss.model_dump()
            iss_dict["audit_id"] = r.audit_id
            iss_dict["is_demo"] = r.is_demo_data
            coord = sample_coords[idx % len(sample_coords)]
            iss_dict["lat"] = coord["lat"]
            iss_dict["lon"] = coord["lon"]
            iss_dict["area"] = coord["area"]

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
        st.metric("Total Audits Recorded", len(reports))
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

    # INTERACTIVE HAZARD MAP
    st.subheader("🗺️ City Walkability & Street Hazard Map")
    if all_issues:
        map_df = []
        for i in all_issues:
            map_df.append({
                "lat": i.get("lat"),
                "lon": i.get("lon"),
                "Area": i.get("area"),
                "Issue": i.get("concise_description")[:40],
                "Tier": i.get("tier"),
                "Score": i.get("score")
            })

        colors = {"CRITICAL": "red", "HIGH": "orange", "MEDIUM": "gold", "LOW": "green"}
        fig_map = px.scatter_mapbox(
            map_df,
            lat="lat",
            lon="lon",
            color="Tier",
            hover_name="Area",
            hover_data=["Issue", "Score"],
            zoom=10,
            color_discrete_map=colors,
            mapbox_style="carto-positron"
        )
        fig_map.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=380)
        st.plotly_chart(fig_map, use_container_width=True)

    # Chart Section
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
            fig_cat.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=280)
            st.plotly_chart(fig_cat, use_container_width=True)

    with chart_col2:
        st.subheader("Urgency Level Breakdown")
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
        fig_tier.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=280)
        st.plotly_chart(fig_tier, use_container_width=True)


# ------------------------------------------------------------------------------
# 8. Page View: ℹ️ About & SDG Alignment
# ------------------------------------------------------------------------------
elif menu_selection == txt["nav_about"]:
    st.title("ℹ️ About CivicLens AI & UN SDG Alignment")

    st.markdown("""
    ### 🎯 Direct United Nations Sustainable Development Goals Alignment
    CivicLens AI uses Gemma 4 Multimodal Vision to inspect pedestrian walkways and eliminate street barriers.
    """)

    sdg_col1, sdg_col2 = st.columns(2)
    with sdg_col1:
        st.markdown("""
        #### 🏙️ SDG 11: Sustainable Cities & Communities
        - **Target 11.2 & 11.7:** Universal access to safe, inclusive, accessible streets for women, children, the elderly, and persons with disabilities.
        - **CivicLens Impact:** Turns ordinary street photos into actionable municipal repair orders.
        """)
        st.markdown("""
        #### ⚖️ SDG 10: Reduced Inequalities
        - **Target 10.2:** Equal mobility rights for persons with disabilities.
        - **CivicLens Impact:** Direct human-impact perspectives for wheelchair and white-cane users.
        """)

    with sdg_col2:
        st.markdown("""
        #### 🏗️ SDG 9: Resilient Infrastructure
        - **Target 9.1:** Reliable and safe civil infrastructure.
        - **CivicLens Impact:** Bridges the gap between ground-level road hazards and city municipal maintenance.
        """)
        st.markdown("""
        #### ❤️ SDG 3: Good Health & Well-being
        - **Target 3.6:** Halve road traffic casualties.
        - **CivicLens Impact:** Prevents pedestrians from being forced into fast vehicle lanes due to blocked sidewalks.
        """)


# ------------------------------------------------------------------------------
# 9. Page View: ⚙️ Settings & Demo Mode
# ------------------------------------------------------------------------------
elif menu_selection == txt["nav_settings"]:
    st.title("⚙️ System Settings & Demo Configuration")

    with st.form("settings_form"):
        new_key = st.text_input(
            "Gemma 4 / Google GenAI API Key",
            value=st.session_state["api_key"],
            type="password"
        )

        new_model = st.text_input(
            "Model Identifier",
            value=st.session_state["model_id"]
        )

        enable_demo = st.checkbox(
            "Enable Explicit Demo Mode (Showcase sample benchmark data offline)",
            value=st.session_state["demo_mode"]
        )

        submitted = st.form_submit_button("Save Configuration", type="primary")
        if submitted:
            st.session_state["api_key"] = new_key.strip()
            st.session_state["model_id"] = new_model.strip()
            st.session_state["demo_mode"] = enable_demo
            st.success("Settings saved successfully!")
            st.rerun()
