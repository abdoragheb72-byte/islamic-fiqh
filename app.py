import os
import re
import html
import time
import json
import random
import csv
import io
import urllib.request
import streamlit as st
import google.generativeai as genai
import copy
from fractions import Fraction

# 1. إعداد الصفحة وتكوين الواجهة
st.set_page_config(
    page_title="الموسوعة الفقهية والحديثية الذكية",
    page_icon="🕌",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# إدارة سمة المظهر والخلفية المختارة
if "app_theme" not in st.session_state:
    st.session_state["app_theme"] = "الزمردي الإمبراطوري (Emerald Deep)"

if "app_bg_image" not in st.session_state:
    st.session_state["app_bg_image"] = "محراب وثريات المسجد التاريخي"

# مكتبة صور إسلامية نقية بعد استبدال الخلفيات غير الملائمة بخلفيات معمارية واضحة
BG_IMAGES_CONFIG = {
    "أروقة جامع الشيخ زايد الكريستالية": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1280&q=70",

    "محراب وثريات المسجد التاريخي": "https://images.unsplash.com/photo-1564769625905-50e93615e769?auto=format&fit=crop&w=1280&q=70",
    "مقرنصات ونقوش العمارة الأندلسية": "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?auto=format&fit=crop&w=1280&q=70",
    "عمارة القباب والمآذن العثمانية": "https://images.unsplash.com/photo-1541432901042-2d8bd64b4a9b?auto=format&fit=crop&w=1280&q=70"
}

# سمات لونية موسعة ومتباينة تماماً وخالية كلياً من الأصفر والذهبي
THEME_CONFIGS = {
      "الأرجواني القرطبي (Cordoba Purple)": {
        "primary": "#9333ea",
        "secondary": "#c084fc",
        "highlight": "#d8b4fe",
        "bg_gradient": "linear-gradient(rgba(24, 10, 38, 0.75), rgba(2, 6, 23, 0.88))",
        "btn_gradient": "linear-gradient(135deg, #9333ea 0%, #7e22ce 60%, #581c87 100%)",
        "hero_gradient": "linear-gradient(135deg, rgba(126, 34, 206, 0.88), rgba(15, 23, 42, 0.94))",
        "border_color": "rgba(192, 132, 252, 0.45)",
        "badge_bg": "rgba(147, 51, 234, 0.25)",
    },
    "الزمردي الإمبراطوري (Emerald Deep)": {
        "primary": "#10b981",
        "secondary": "#34d399",
        "highlight": "#6ee7b7",
        "bg_gradient": "linear-gradient(rgba(2, 6, 23, 0.75), rgba(2, 6, 23, 0.88))",
        "btn_gradient": "linear-gradient(135deg, #059669 0%, #0d9488 60%, #0f766e 100%)",
        "hero_gradient": "linear-gradient(135deg, rgba(6, 78, 59, 0.88), rgba(15, 23, 42, 0.94))",
        "border_color": "rgba(16, 185, 129, 0.45)",
        "badge_bg": "rgba(16, 185, 129, 0.25)",
    },
    "النيلي الملكي (Royal Sapphire)": {
        "primary": "#0284c7",
        "secondary": "#38bdf8",
        "highlight": "#7dd3fc",
        "bg_gradient": "linear-gradient(rgba(10, 15, 30, 0.75), rgba(2, 6, 23, 0.88))",
        "btn_gradient": "linear-gradient(135deg, #0284c7 0%, #0369a1 60%, #1e3a8a 100%)",
        "hero_gradient": "linear-gradient(135deg, rgba(30, 58, 138, 0.88), rgba(15, 23, 42, 0.94))",
        "border_color": "rgba(56, 189, 248, 0.45)",
        "badge_bg": "rgba(2, 132, 199, 0.25)",
    },
    "الياقوتي الدمشقي (Crimson Ruby)": {
        "primary": "#e11d48",
        "secondary": "#fb7185",
        "highlight": "#fda4af",
        "bg_gradient": "linear-gradient(rgba(30, 10, 18, 0.75), rgba(2, 6, 23, 0.88))",
        "btn_gradient": "linear-gradient(135deg, #e11d48 0%, #be123c 60%, #881337 100%)",
        "hero_gradient": "linear-gradient(135deg, rgba(159, 18, 57, 0.88), rgba(15, 23, 42, 0.94))",
        "border_color": "rgba(251, 113, 133, 0.45)",
        "badge_bg": "rgba(225, 29, 72, 0.25)",
    },

    "الفيروزي القاهري (Cairo Turquoise)": {
        "primary": "#0d9488",
        "secondary": "#2dd4bf",
        "highlight": "#5eead4",
        "bg_gradient": "linear-gradient(rgba(4, 28, 30, 0.75), rgba(2, 6, 23, 0.88))",
        "btn_gradient": "linear-gradient(135deg, #0d9488 0%, #0f766e 60%, #115e59 100%)",
        "hero_gradient": "linear-gradient(135deg, rgba(13, 148, 136, 0.88), rgba(15, 23, 42, 0.94))",
        "border_color": "rgba(45, 212, 191, 0.45)",
        "badge_bg": "rgba(13, 148, 136, 0.25)",
    },
    "الفحمي الفضي (Silver Obsidian)": {
        "primary": "#64748b",
        "secondary": "#94a3b8",
        "highlight": "#cbd5e1",
        "bg_gradient": "linear-gradient(rgba(15, 23, 42, 0.78), rgba(2, 6, 23, 0.90))",
        "btn_gradient": "linear-gradient(135deg, #475569 0%, #334155 60%, #1e293b 100%)",
        "hero_gradient": "linear-gradient(135deg, rgba(51, 65, 85, 0.88), rgba(15, 23, 42, 0.94))",
        "border_color": "rgba(148, 163, 184, 0.45)",
        "badge_bg": "rgba(100, 116, 139, 0.25)",
    }
}

current_theme = THEME_CONFIGS[st.session_state["app_theme"]]
current_bg_url = BG_IMAGES_CONFIG[st.session_state["app_bg_image"]]

# 2. تخصيص واجهة المستخدم بخط المصحف العثماني بلون زمردي ناصع وفواصل المذاهب
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri+Quran&family=Amiri:ital,wght@0,400;0,700;1,400&family=Aref+Ruqaa:wght@700&family=Cairo:wght@400;600;700;800;900&display=swap');
    
    * {{
        font-family: 'Cairo', sans-serif;
        box-sizing: border-box !important;
    }}

    #scroll-progress-bar {{
        position: fixed;
        top: 0;
        left: 0;
        height: 3.5px;
        background: linear-gradient(90deg, {current_theme['primary']}, {current_theme['secondary']});
        width: 100%;
        z-index: 10000;
        box-shadow: 0 0 12px {current_theme['primary']};
    }}

    html, body, .stApp {{
        background-color: #020617 !important;
        background: 
            {current_theme['bg_gradient']},
            url('{current_bg_url}') no-repeat center center fixed !important;
        background-size: cover !important;
        color: #f8fafc !important;
        direction: rtl !important;
        overflow-x: hidden !important;
        border: 1.5px solid {current_theme['border_color']} !important;
    }}

    /* تمييز خط الآيات القرآنية بلون نعناعي زمردي ناصع ومستقل عن نصوص الواجهة */
    .quran-ayah {{
        font-family: 'Amiri Quran', 'Amiri', serif !important;
        font-size: 1.65rem !important;
        font-weight: 400 !important;
        color: #34d399 !important;
        line-height: 2.3 !important;
        display: inline-block;
        padding: 5px 16px;
        background: rgba(6, 78, 59, 0.45);
        border-radius: 12px;
        border-right: 4px solid #10b981;
        border-left: 1px solid rgba(52, 211, 153, 0.3);
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.5);
        margin: 8px 0;
        text-align: center;
        letter-spacing: 0.5px;
        text-shadow: 0 0 10px rgba(52, 211, 153, 0.35);
    }}

    /* فاصل إسلامي هندسي بارز بين أقوال المذاهب الأربعة */
    .madhab-divider {{
        position: relative;
        text-align: center;
        margin: 2.2rem 0 1.6rem 0;
    }}
    .madhab-divider::before {{
        content: "";
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(to right, transparent, {current_theme['secondary']}, transparent);
        z-index: 1;
    }}
    .madhab-divider span {{
        position: relative;
        z-index: 2;
        background: #020617;
        color: {current_theme['secondary']};
        padding: 4px 18px;
        font-size: 1.05rem;
        font-weight: 800;
        border: 1.5px solid {current_theme['border_color']};
        border-radius: 22px;
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.8);
    }}

    .stApp::before {{
        content: "❖";
        position: fixed;
        top: 12px;
        right: 16px;
        font-size: 1.25rem;
        color: {current_theme['secondary']};
        opacity: 0.65;
        pointer-events: none;
        z-index: 999;
    }}
    .stApp::after {{
        content: "❖";
        position: fixed;
        top: 12px;
        left: 16px;
        font-size: 1.25rem;
        color: {current_theme['secondary']};
        opacity: 0.65;
        pointer-events: none;
        z-index: 999;
    }}

    hr {{
        border: 0 !important;
        height: 1.5px !important;
        background-image: linear-gradient(to right, transparent, {current_theme['secondary']}, transparent) !important;
        margin: 1.8rem 0 !important;
        opacity: 0.75 !important;
    }}

    [data-testid="stSidebar"], [data-testid="collapsedControl"] {{
        display: none !important;
    }}

    .main .block-container {{
        padding: 0.8rem 0.8rem 2.8rem 0.8rem !important;
        max-width: 650px !important;
    }}
    
    .dhikr-card {{
        background: rgba(15, 23, 42, 0.82) !important;
        border: 1.5px solid {current_theme['border_color']} !important;
        border-radius: 18px;
        padding: 0.85rem 1rem;
        margin-bottom: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.55);
    }}
    
    .dhikr-text {{
        font-family: 'Amiri', serif !important;
        font-size: 1.2rem;
        font-weight: 700;
        color: {current_theme['highlight']};
        margin: 0;
        line-height: 1.7;
    }}

    .daily-card, .quiz-card, .stat-card {{
        background: rgba(15, 23, 42, 0.82) !important;
        border: 1.5px solid {current_theme['border_color']} !important;
        border-radius: 16px;
        padding: 1.1rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    }}

    .daily-badge {{
        background: {current_theme['badge_bg']};
        color: {current_theme['secondary']};
        border: 1px solid {current_theme['primary']};
        padding: 2px 8px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 800;
        display: inline-block;
        margin-bottom: 0.5rem;
    }}
    
    .royal-hero {{
        background: {current_theme['hero_gradient']} !important;
        border: 1.5px solid {current_theme['primary']} !important;
        border-radius: 20px;
        padding: 1.6rem 1rem;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.65);
    }}
    
    .royal-hero h1 {{
        font-family: 'Aref Ruqaa', serif !important;
        color: {current_theme['secondary']};
        font-size: 1.95rem;
        margin-bottom: 0.35rem;
        line-height: 1.3;
    }}
    
    .royal-hero p {{
        color: {current_theme['highlight']};
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 0;
    }}

    .circle-icon-badge {{
        width: 65px;
        height: 65px;
        line-height: 65px;
        border-radius: 50%;
        background: rgba(15, 23, 42, 0.88);
        border: 2px solid {current_theme['primary']};
        font-size: 1.8rem;
        margin: 0 auto 0.6rem auto;
        text-align: center;
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.55);
    }}

    .circle-card-title {{
        color: #f8fafc;
        font-weight: 800;
        font-size: 1rem;
        margin-bottom: 0.2rem;
    }}

    .circle-card-desc {{
        color: #94a3b8;
        font-size: 0.8rem;
        line-height: 1.4;
    }}

    .hub-grid-btn>button {{
        background: rgba(15, 23, 42, 0.85) !important;
        border: 1.5px solid {current_theme['border_color']} !important;
        border-radius: 18px !important;
        padding: 1.1rem 0.6rem !important;
        height: 100% !important;
        min-height: 140px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.45) !important;
        transition: transform 0.15s ease !important;
    }}

    .hub-grid-btn>button:hover {{
        transform: translateY(-3px) !important;
        border-color: {current_theme['secondary']} !important;
    }}

    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input {{
        background: rgba(15, 23, 42, 0.94) !important;
        color: #ffffff !important;
        border: 1.5px solid {current_theme['border_color']} !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }}

    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {{
        border-color: {current_theme['secondary']} !important;
    }}

    .stRadio label, .stSelectbox label, .stMultiSelect label, .stSlider label {{
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        color: {current_theme['secondary']} !important;
    }}

    .action-submit-btn>button {{
        background: {current_theme['btn_gradient']} !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        border: 1px solid {current_theme['border_color']} !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.2rem !important;
        width: 100%;
        margin-top: 0.5rem;
    }}

    .back-nav-btn>button {{
        background: rgba(15, 23, 42, 0.9) !important;
        border: 1.5px solid {current_theme['border_color']} !important;
        color: {current_theme['secondary']} !important;
        margin-bottom: 1.2rem !important;
        border-radius: 12px !important;
        padding: 0.6rem 1rem !important;
        font-size: 1rem !important;
    }}
    
    .stMarkdown {{
        font-size: 1.05rem !important;
        line-height: 1.9 !important;
        color: #f8fafc !important;
    }}

    .stMarkdown h1 {{
        font-family: 'Amiri', serif !important;
        color: {current_theme['secondary']} !important;
        font-size: 1.45rem !important;
        border-bottom: 1px solid {current_theme['border_color']} !important;
        padding-bottom: 0.4rem !important;
        margin-top: 1.2rem !important;
    }}
    
    .stMarkdown h2, .stMarkdown h3 {{
        font-family: 'Amiri', serif !important;
        color: #38bdf8 !important;
        font-size: 1.25rem !important;
    }}

    table {{
        width: 100% !important;
        display: block !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        border-collapse: collapse !important;
        margin: 1rem 0 !important;
    }}

    th, td {{
        border: 1px solid {current_theme['border_color']} !important;
        padding: 8px 12px !important;
    }}

    .summary-pill-card {{
        background: rgba(15, 23, 42, 0.9);
        border: 1.5px solid {current_theme['primary']};
        border-radius: 14px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 1rem;
    }}

    .social-share-card {{
        background: rgba(15, 23, 42, 0.94);
        border: 1px solid {current_theme['primary']};
        border-radius: 14px;
        padding: 1.2rem;
        margin: 1rem 0;
        border-right: 5px solid {current_theme['secondary']};
    }}

    .tasbeeh-counter-box {{
        background: rgba(15, 23, 42, 0.92);
        border: 2px solid {current_theme['primary']};
        border-radius: 50%;
        width: 125px;
        height: 125px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 1rem auto;
    }}

    .tree-card-fard {{
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid {current_theme['primary']};
        border-radius: 12px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
    }}

    .tree-card-asaba {{
        background: rgba(6, 182, 212, 0.15);
        border: 1px solid #06b6d4;
        border-radius: 12px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
    }}

    .badge-tier-card {{
        background: rgba(15, 23, 42, 0.92);
        border: 1.5px solid {current_theme['primary']};
        border-radius: 14px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
    }}
    
    .stat-number {{
        font-size: 1.85rem;
        font-weight: 900;
        color: {current_theme['secondary']};
    }}
    .stat-title {{
        color: #94a3b8;
        font-size: 0.9rem;
        font-weight: 700;
    }}

    .social-link-btn {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.45rem 0.9rem;
        margin: 0.25rem;
        border-radius: 10px;
        color: #ffffff !important;
        text-decoration: none !important;
        font-size: 0.9rem;
        font-weight: 700;
        border: 1px solid {current_theme['border_color']};
        background: rgba(15, 23, 42, 0.82);
    }}

    .royal-footer {{
        margin-top: 3rem;
        padding: 1.6rem 1rem;
        border-top: 1px solid {current_theme['border_color']};
        background: rgba(2, 6, 23, 0.96);
        border-radius: 16px 16px 0 0;
        text-align: center;
        font-size: 0.95rem;
    }}
    
    .dev-badge {{
        display: inline-block;
        background: {current_theme['badge_bg']};
        border: 1px solid {current_theme['primary']};
        padding: 0.3rem 0.9rem;
        border-radius: 12px;
        color: {current_theme['secondary']};
        font-weight: 800;
        font-size: 0.95rem;
    }}

    @media only screen and (max-width: 600px) {{
        .royal-hero h1 {{ font-size: 1.45rem !important; }}
        .circle-icon-badge {{ width: 55px; height: 55px; line-height: 55px; font-size: 1.5rem; }}
    }}
</style>
<div id="scroll-progress-bar"></div>
""", unsafe_allow_html=True)

# 3. بنك المسائل والأذكار والأسئلة والتحديات
DAILY_FIQH_SNIPPETS = [
    {"topic": "حكم سجود السهو للمأموم إذا سها إمامه", "text": "إذا سها الإمام وسجد للسهو، وجب على المأموم متابعته سواء سجد قبل السلام أو بعده، لقوله ﷺ: «إنما جُعل الإمام ليؤتم به فلا تختلفوا عليه»."},
    {"topic": "قضاء صيام التطوع إذا قطعه الصائم", "text": "ذهب جمهور العلماء (الشافعية والحنابلة) إلى أن صيام التطوع لا يجب قضاؤه إذا أفطر الصائم، لقوله ﷺ: «الصائم المتطوع أمير نفسه إن شاء صام وإن شاء أفطر»."},
    {"topic": "حكم بيع الذهب القديم بجديد مع دفع الفرق", "text": "لا يجوز بيع ذهب بذهب مع دفع الفارق؛ بل الواجب شرعاً بيع الذهب القديم وقبض ثمنه نقداً، ثم شراء الذهب الجديد بصفقة منفصلة منعاً للوقوع في ربا الفضل."},
    {"topic": "حكم قراءة القرآن من الهاتف بغير وضوء", "text": "يجوز لمس شاشة الهاتف وقراءة القرآن منه بغير وضوء، لأن شاشة الهاتف لا تأخذ حكم المصحف الورقي الذي يحرم مسه للمحدث."}
]

DAILY_CHALLENGE_BANK = [
    {"question": "ما حكم إخراج القيمة نقداً في زكاة الفطر عند الحنفية؟", "options": ["يجوز وتجزئ", "لا يجوز مطلقاً", "يجوز للضرورة فقط"], "correct": "يجوز وتجزئ", "proof": "ذهب الإمام أبو حنيفة إلى جواز إخراجها نقداً تيسيراً على الفقراء وقضاءً لحوائجهم."},
    {"question": "ما أقل مدة للمكث في الاعتكاف عند جمهور العلماء؟", "options": ["لحظة أو ساعة بشرط النية", "يوم وليلة كاملين", "عشرة أيام"], "correct": "لحظة أو ساعة بشرط النية", "proof": "ذهب الشافعية والحنابلة إلى أن الاعتكاف يصح بمكث يسير في المسجد مع النية."},
    {"question": "ما حكم الاستعانة بالغير في الوضوء لغير عاجز؟", "options": ["مكروه مع صحة الوضوء", "محرم ويبطل الوضوء", "سنة مستحبة"], "correct": "مكروه مع صحة الوضوء", "proof": "يكره لغير العاجز أن يستعين بمن يصب عليه الماء لما فيه من الترفه والتكبر."}
]

ATHKAR_LIST = [
    {"title": "سيد الاستغفار", "text": "اللَّهُمَّ أَنْتَ رَبِّي لاَ إِلَهَ إِلاَّ أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ، وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ، أَعُوذُ بِكَ مِنْ شَرِّ مَا صَنَعْتُ، أَبُوءُ لَكَ بِنِعْمَتِكَ عَلَيَّ، وَأَبُوءُ لَكَ بِذَنْبِي فَاغْفِرْ لِي فَإِنَّهُ لاَ يَغْفِرُ الذُّنُوبَ إِلاَّ أَنْتَ.", "virtue": "من قالها موقناً بها حين يمسي فمات دخل الجنة (صحيح البخاري)."},
    {"title": "الصلاة الإبراهيمية", "text": "اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وَعَلَى آلِ مُحَمَّدٍ، كَمَا صَلَّيْتَ عَلَى إِبْرَاهِيمَ وَعَلَى آلِ إِبْرَاهِيمَ، إِنَّكَ حَمِيدٌ مَجِيدٌ.", "virtue": "من صلى عليّ صلاة صلى الله عليه بها عشراً (صحيح مسلم)."},
    {"title": "الحوقلة (كنز من كنوز الجنة)", "text": "لا حَوْلَ وَلا قُوَّةَ إِلا بِاللَّهِ الْعَلِيِّ الْعَظِيمِ", "virtue": "كنز من كنوز الجنة ودواء لتسعة وتسعين داء (متفق عليه)."},
    {"title": "التسبيح والتحميد المأثور", "text": "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ ، سُبْحَانَ اللَّهِ الْعَظِيمِ", "virtue": "كلمتان خفيفتان على اللسان ثقيلتان في الميزان (صحيح البخاري)."}
]

EXPANDED_QUIZ_DATABASE = {
    "المستوى الأول: المبتدئ (فقه العبادات الأساسي) 🟢": [
        {"question": "ما حكم قراءة سورة الفاتحة للإمام والمنفرد في الصلاة المفروضة؟", "options": ["ركن لا تصح الصلاة إلا به", "سنة مستحبة وتصح الصلاة بدونها", "واجب يجبره سجود السهو"], "correct": "ركن لا تصح الصلاة إلا به", "proof": "لقول النبي ﷺ: «لا صلاةَ لمَن لم يقرَأْ بفاتحةِ الكتابِ» (متفق عليه)."},
        {"question": "ما هو الحد الأدنى لنصاب الذهب الذي تجب فيه الزكاة بالجرامات؟", "options": ["85 جراماً من الذهب الخالص", "50 جراماً", "120 جراماً"], "correct": "85 جراماً من الذهب الخالص", "proof": "النصاب الشرعي للذهب عشرون ديناراً، وتساوي 85 جراماً من الذهب عيار 24."},
        {"question": "ما حكم صيام يومي عيدي الفطر والأضحى؟", "options": ["محرم باتفاق العلماء", "مكروه كراهة تنزيه", "مباح لمن كان عليه قضاء"], "correct": "محرم باتفاق العلماء", "proof": "نهى رسول الله ﷺ عن صيام يومين: يوم الفطر، ويوم النحر (صحيح البخاري)."},
        {"question": "ما الحكم إذا نوى المسلم الصيام المفروض بعد طلوع الفجر؟", "options": ["لا يصح صومه ويجب تبييت النية من الليل", "يصح صومه كصيام التطوع", "يصح وعليه كفارة"], "correct": "لا يصح صومه ويجب تبييت النية من الليل", "proof": "لقوله ﷺ: «من لم يُبيّتِ الصيامَ قبلَ الفجرِ، فلا صيامَ له» (رواه أصحاب السنن)."}
    ],
    "المستوى الثاني: المتوسط (فقه المعاملات ودقائق العبادات) 🟡": [
        {"question": "ما حكم سجود السهو إذا سلّم المصلي عن نقص في صلاته وتذكر بعد لحظات يسيرة؟", "options": ["يأتي بما فاته ثم يسجد للسهو ويسلم", "تبطل صلاته ويعيدها كاملة", "يسجد للسهو فقط وتجزئه"], "correct": "يأتي بما فاته ثم يسجد للسهو ويسلم", "proof": "لحديث ذي اليدين؛ حيث أتم النبي ﷺ الركعتين ثم سلم، ثم سجد سجدتي السهو وسلّم."},
        {"question": "ما هو بيع العينة المنهي عنه شرعاً؟", "options": ["أن يبيع سلعة بثمن مؤجل ثم يشتريها نقداً بأقل", "بيع الثمار قبل بدو صلاحها", "بيع ما لا يملك الإنسان"], "correct": "أن يبيع سلعة بثمن مؤجل ثم يشتريها نقداً بأقل", "proof": "لقوله ﷺ: «إذا تبايعتُم بالعِينَةِ... سلَّطَ اللهُ عليكُمْ ذُلاً» (رواه أبو داود)."}
    ],
    "المستوى الثالث: المتقدم (أصول الفقه ومصطلح الحديث) 🔴": [
        {"question": "ما هو الحديث المرسل عند جمهور المحدثين؟", "options": ["ما سقط من إسناده الصحابي ورفعه التابعي مباشرة", "ما سقط من وسط سنده راويان على التوالي", "الحديث الذي انفرد بروايته شخص واحد"], "correct": "ما سقط من إسناده الصحابي ورفعه التابعي مباشرة", "proof": "المرسل هو قول التابعي صغيراً كان أو كبيراً: قال رسول الله ﷺ كذا."},
        {"question": "ما الفرق بين 'الفرض' و'الواجب' عند السادة الحنفية؟", "options": ["الفرض ما ثبت بدليل قطعي، والواجب ما ثبت بدليل ظني", "الفرض والواجب مترادفان تماماً", "الواجب آكد من الفرض في العقيدة"], "correct": "الفرض ما ثبت بدليل قطعي، والواجب ما ثبت بدليل ظني", "proof": "يميز الحنفية بين الفرض (كالصلاة بالدليل القطعي) والواجب (كالوتر بالدليل الظني)."}
    ]
}

# 4. إعداد محرك Google Gemini API
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"].strip()
except Exception:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

if GEMINI_API_KEY:
     genai.configure(api_key=GEMINI_API_KEY, transport="rest")
# 5. دوال التنسيق والتنفيذ السريع بـ Gemini وجلب أسعار الذهب
def format_quranic_text(text: str) -> str:
    if not text:
        return ""
    # تحويل الآيات القرآنية إلى رسم المصحف العثماني بالخط Amiri Quran ولون مستقل
    # (تُدمج الأسطر داخل الآية الواحدة حتى لا ينكسر وسم HTML في Markdown)
    formatted = re.sub(
        r'«([^»]+)»',
        lambda m: '<span class="quran-ayah">﴿ ' + re.sub(r'\s*\n\s*', ' ', m.group(1)).strip() + ' ﴾</span>',
        text
    )
    # فاصل بارز مخصص بين المذاهب الأربعة
    formatted = re.sub(
        r'(\n|^)###?\s*(المذهب\s+[^\n:]+|قول\s+[^\n:]+|الحنفي|المالكي|الشافعي|الحنبلي)',
        r'\1\n<div class="madhab-divider"><span>❖ \2 ❖</span></div>\n',
        formatted
    )
    return formatted

def sanitize_user_input(text: str, max_chars: int = 500) -> str:
    if not text:
        return ""
    cleaned = re.sub(r'<[^>]*?>', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # القص قبل التهريب حتى لا تنقطع كيانات HTML (مثل &quot;) من المنتصف
    return html.escape(cleaned[:max_chars])

# ---------- أسعار الذهب والفضة والدولار (تحديث تلقائي) ----------
_GOLD_FALLBACK_PRICES = {"24": 4685.0, "21": 4100.0, "18": 3514.0}
_SILVER_FALLBACK_PER_GRAM = 52.0
_USD_EGP_FALLBACK = 49.5
_HTTP_TIMEOUT = 6
_PRICE_REFRESH_SEC = 300  # تحديث الأسعار كل 5 دقائق

def _cairo_now_text() -> str:
    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime
        return datetime.now(ZoneInfo("Africa/Cairo")).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return time.strftime("%Y-%m-%d %H:%M", time.gmtime(time.time() + 2 * 3600))

def _http_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _fetch_usd_egp():
    """سعر الدولار مقابل الجنيه من مصدرين احتياطيين."""
    for url in ("https://open.er-api.com/v6/latest/USD",
                "https://api.exchangerate-api.com/v4/latest/USD"):
        try:
            rate = float(_http_json(url)["rates"]["EGP"])
            if 5 < rate < 500:
                return rate
        except Exception:
            continue
    return None

def _fetch_metal_usd_per_ounce(symbol: str):
    try:
        price = float(_http_json(f"https://api.gold-api.com/price/{symbol}").get("price", 0) or 0)
        return price if price > 0 else None
    except Exception:
        return None

@st.cache_data(ttl=_PRICE_REFRESH_SEC - 60, show_spinner=False)
def _fetch_market_data_cached():
    # نرفع استثناءً عند الفشل حتى لا يُخزَّن الفشل في الكاش
    xau = _fetch_metal_usd_per_ounce("XAU")
    if not xau:
        raise RuntimeError("gold price unavailable")
    xag = _fetch_metal_usd_per_ounce("XAG")
    fx = _fetch_usd_egp()
    rate = fx or _USD_EGP_FALLBACK
    g24 = round(xau / 31.1035 * rate, 2)
    return {
        "gold24": g24,
        "gold21": round(g24 * 21 / 24, 2),
        "gold18": round(g24 * 18 / 24, 2),
        "silver_g": round(xag / 31.1035 * rate, 2) if xag else None,
        "usd_egp": round(rate, 2),
        "fx_live": fx is not None,
        "updated": _cairo_now_text(),
    }

def get_market_data():
    """يرجع أحدث الأسعار؛ وعند تعذر الاتصال يرجع آخر سعر ناجح أو قيماً تقديرية."""
    try:
        data = dict(_fetch_market_data_cached())
        data["live"] = True
        st.session_state["_last_good_market"] = data
        return data
    except Exception:
        last = st.session_state.get("_last_good_market")
        if last:
            data = dict(last)
            data["live"] = False
            return data
        return {
            "gold24": _GOLD_FALLBACK_PRICES["24"], "gold21": _GOLD_FALLBACK_PRICES["21"],
            "gold18": _GOLD_FALLBACK_PRICES["18"], "silver_g": None,
            "usd_egp": _USD_EGP_FALLBACK, "fx_live": False, "live": False, "updated": "—",
        }

def fetch_egypt_gold_prices():
    d = get_market_data()
    return {"24": d["gold24"], "21": d["gold21"], "18": d["gold18"]}

def _render_price_banner_body():
    md = get_market_data()
    last = st.session_state.get("_last_gold24")
    st.session_state["_last_gold24"] = md["gold24"]
    status = "🟢 أسعار مباشرة" if md["live"] else "🟠 أسعار تقديرية (تعذر الاتصال بمصدر الأسعار، سيُعاد المحاولة تلقائياً)"
    silver = f"{md['silver_g']:,.2f}" if md.get("silver_g") else "—"
    st.caption(
        f"{status} • عيار 24: {md['gold24']:,.0f} • عيار 21: {md['gold21']:,.0f} • عيار 18: {md['gold18']:,.0f} ج.م/جم"
        f" • الفضة: {silver} ج.م/جم • الدولار: {md['usd_egp']:.2f} ج.م • آخر تحديث: {md['updated']}"
    )
    if last is not None and abs(last - md["gold24"]) >= 0.5:
        st.rerun()  # السعر تغيّر: نعيد رسم الصفحة ليتحدث حد النصاب وقيم الحقول

if hasattr(st, "fragment"):
    live_price_banner = st.fragment(run_every=_PRICE_REFRESH_SEC)(_render_price_banner_body)
else:
    live_price_banner = _render_price_banner_body

# ---------- محرك Gemini ----------
# نبدأ بالأسماء المستعارة (-latest) لأن Google تحدّثها تلقائياً وتبقى صالحة بعد إيقاف النماذج القديمة
_PREFERRED_MODELS = [
    "gemini-flash-latest", "gemini-2.5-flash", "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-2.0-flash-lite",
]
_EXCLUDED_MODEL_WORDS = (
    "image", "tts", "live", "audio", "embedding", "aqa", "vision", "robotics",
    "computer-use", "learnlm", "gemma", "imagen", "veo", "thinking", "exp",
)
_MAX_MODEL_ATTEMPTS = 5
_REQUEST_TIMEOUT_SEC = 60
_FATAL_ERROR_MARKERS = (
    "api key not valid", "api_key_invalid", "api key expired",
    "user location is not supported",
)
_SAFETY_SETTINGS = {  # الأسئلة الفقهية (مواريث، نكاح...) كانت تُحجب خطأً بالإعداد الافتراضي
    "HARASSMENT": "BLOCK_ONLY_HIGH", "HATE": "BLOCK_ONLY_HIGH",
    "SEXUAL": "BLOCK_ONLY_HIGH", "DANGEROUS": "BLOCK_ONLY_HIGH",
}

def _rank_models(models):
    """يستبعد النماذج غير المناسبة للنص (صور/صوت/تضمين...) ويرتب الأسرع أولاً."""
    clean = []
    for name in models:
        short = name.split("/")[-1].lower()
        if "gemini" not in short or any(w in short for w in _EXCLUDED_MODEL_WORDS):
            continue
        clean.append(name)

    def score(name):
        short = name.split("/")[-1].lower()
        if short in _PREFERRED_MODELS:
            return (0, _PREFERRED_MODELS.index(short))
        if "flash" in short and "lite" not in short and "preview" not in short:
            return (1, 0)
        if "flash" in short and "lite" in short:
            return (2, 0)
        if "flash" in short:
            return (3, 0)
        return (4, 0)

    return sorted(clean, key=score)

@st.cache_resource(ttl=3600, show_spinner=False)
def get_supported_gemini_models():
    # الاستثناء لا يُحفظ في الكاش فتتكرر المحاولة لاحقاً
    try:
        listing = genai.list_models(request_options={"timeout": 15})
    except TypeError:
        listing = genai.list_models()
    models = [
        m.name for m in listing
        if "generateContent" in getattr(m, "supported_generation_methods", [])
    ]
    ranked = _rank_models(models)
    if not ranked:
        raise RuntimeError("no usable models listed")
    return ranked

@st.cache_resource(show_spinner=False)
def _best_model_holder():
    return {"name": None}

def get_best_model_name():
    try:
        models = list(get_supported_gemini_models())
    except Exception:
        models = list(_PREFERRED_MODELS)
    best = _best_model_holder()["name"]
    if best:
        models = [best] + [m for m in models if m != best]
    return models[:_MAX_MODEL_ATTEMPTS]

def _remember_model(model_name):
    _best_model_holder()["name"] = model_name

def _forget_model(model_name):
    holder = _best_model_holder()
    if holder["name"] == model_name:
        holder["name"] = None

def _is_fatal_error(message: str) -> bool:
    low = (message or "").lower()
    return any(marker in low for marker in _FATAL_ERROR_MARKERS)

def _is_model_specific_error(message: str) -> bool:
    low = (message or "").lower()
    return any(k in low for k in ("404", "not found", "429", "quota", "resource_exhausted",
                                  "not supported", "deprecated", "no longer available"))

def _friendly_error(errors, last_raw: str = "") -> str:
    blob = " ".join(errors).lower() + " " + (last_raw or "").lower()
    if "api key not valid" in blob or "api_key_invalid" in blob or "api key expired" in blob:
        head = "مفتاح GEMINI_API_KEY غير صالح أو منتهي. أنشئ مفتاحاً جديداً من https://aistudio.google.com/apikey وضعه في ملف .streamlit/secrets.toml"
    elif "user location is not supported" in blob:
        head = "خدمة Gemini غير متاحة في موقعك الحالي (جرّب VPN أو نشر التطبيق على Streamlit Cloud)."
    elif "429" in blob or "quota" in blob or "resource_exhausted" in blob:
        head = "تم تجاوز حصة الاستخدام المجانية لمفتاح Gemini. انتظر دقيقة ثم أعد المحاولة، أو فعّل الفوترة لمفتاحك."
    elif "timeout" in blob or "deadline" in blob or "timed out" in blob:
        head = "انتهت مهلة الاتصال بخدمة Gemini. تحقق من الإنترنت ثم أعد المحاولة."
    elif "محجوب" in blob:
        head = "حجب Gemini الإجابة لأسباب تتعلق بالمحتوى. أعد صياغة السؤال بشكل مختلف."
    else:
        head = "تعذر الحصول على رد من Gemini."
    details = " | ".join(e[:160] for e in errors[-3:])
    return f"⚠️ {head}\n\nتفاصيل تقنية: {details}" if details else f"⚠️ {head}"

def _make_model(model_name, system_inst):
    try:
        return genai.GenerativeModel(model_name=model_name, system_instruction=system_inst,
                                     safety_settings=_SAFETY_SETTINGS)
    except Exception:
        return genai.GenerativeModel(model_name=model_name, system_instruction=system_inst)

def _chunk_text(chunk) -> str:
    # chunk.text يرمي استثناءً إذا كانت القطعة فارغة/محجوبة؛ نتجاهلها بدل إسقاط الإجابة كلها
    try:
        return chunk.text or ""
    except Exception:
        return ""

def _response_text(response) -> str:
    try:
        return (response.text or "").strip()
    except Exception:
        parts = []
        for cand in getattr(response, "candidates", None) or []:
            for part in getattr(getattr(cand, "content", None), "parts", None) or []:
                parts.append(getattr(part, "text", "") or "")
        return "".join(parts).strip()

def _block_reason(response) -> str:
    try:
        fb = response.prompt_feedback
        return str(fb.block_reason) if fb and fb.block_reason else ""
    except Exception:
        return ""

def _stream_to_container(response, output_container):
    full_text = ""
    last_paint = 0.0
    for chunk in response:
        piece = _chunk_text(chunk)
        if not piece:
            continue
        full_text += piece
        now = time.time()
        if now - last_paint >= 0.12:
            output_container.markdown(f"<br>{full_text}▌", unsafe_allow_html=True)
            last_paint = now
    return full_text

def _call_model(model_name, system_inst, user_text, history, stream):
    model = _make_model(model_name, system_inst)
    opts = {"timeout": _REQUEST_TIMEOUT_SEC}
    if history:
        return model.start_chat(history=history).send_message(user_text, stream=stream, request_options=opts)
    return model.generate_content(user_text, stream=stream, request_options=opts)

def _generate_text(system_inst, user_text, history=None, output_container=None):
    """يجرّب النماذج بالترتيب: بث مباشر ثم طلب عادي عند الرد الفارغ. يرجع (النص، قائمة الأخطاء)."""
    errors = []
    for model_name in get_best_model_name():
        for stream in ((True, False) if output_container is not None else (False,)):
            try:
                resp = _call_model(model_name, system_inst, user_text, history, stream)
                if stream:
                    text = _stream_to_container(resp, output_container)
                else:
                    text = _response_text(resp)
                if text.strip():
                    _remember_model(model_name)
                    return text.strip(), errors
                reason = _block_reason(resp)
                errors.append(f"{model_name}: رد فارغ" + (f" (محجوب: {reason})" if reason else ""))
                continue  # جرّب الطلب العادي على نفس النموذج
            except Exception as e:
                msg = str(e)
                errors.append(f"{model_name}: {msg[:200]}")
                if _is_fatal_error(msg):
                    return None, errors
                _forget_model(model_name)
                break  # انتقل للنموذج التالي
    return None, errors

def execute_gemini_prompt(prompt, system_inst, output_container=None):
    if not GEMINI_API_KEY:
        if output_container:
            output_container.error("⚠️ مفتاح GEMINI_API_KEY غير موجود. ضعه في .streamlit/secrets.toml بصيغة: GEMINI_API_KEY = \"مفتاحك\"")
        return None

    guarded_system_prompt = f"""{system_inst}\n[ضوابط]: التزم باللغة العربية الفصحى فقط. ضع الآيات الكريمة بدقة بين « ... » ليتم تمييزها برسم المصحف الشريف."""
    text, errors = _generate_text(guarded_system_prompt, html.unescape(prompt), None, output_container)
    if text:
        if output_container:
            output_container.markdown(f"<br>{format_quranic_text(text)}", unsafe_allow_html=True)
        return text
    if output_container:
        output_container.error(_friendly_error(errors))
    return None

def _build_gemini_history(messages):
    """يبني سجل محادثة صالحاً لـ Gemini: يبدأ بمستخدم ويتناوب الدور دون تكرار."""
    history = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        content = html.unescape(msg["content"])
        if not history and role != "user":
            continue
        if history and history[-1]["role"] == role:
            history[-1]["parts"] = [history[-1]["parts"][0] + "\n" + content]
        else:
            history.append({"role": role, "parts": [content]})
    while history and history[-1]["role"] != "model":
        history.pop()
    return history

def execute_gemini_chat(messages_history, system_inst, output_container):
    if not GEMINI_API_KEY:
        output_container.error("⚠️ مفتاح GEMINI_API_KEY غير موجود. ضعه في .streamlit/secrets.toml بصيغة: GEMINI_API_KEY = \"مفتاحك\"")
        return None

    guarded_system_prompt = f"""{system_inst}\n[ضوابط]: أنت محاور فقهي ومستشار شرعي رصين باللغة العربية الفصحى فقط. ضع أي آية قرآنية بين علامتي « ... » لتمييزها برسم المصحف الشريف."""
    gemini_history = _build_gemini_history(messages_history[-5:-1])
    last_user_msg = html.unescape(messages_history[-1]["content"])

    text, errors = _generate_text(guarded_system_prompt, last_user_msg, gemini_history, output_container)
    if text:
        output_container.markdown(f"<br>{format_quranic_text(text)}", unsafe_allow_html=True)
        return text
    output_container.error(_friendly_error(errors))
    return None

_QUIZ_LINE_PREFIX = re.compile(r'^\s*(?:[-*•]+|\(?\d+[\.\)\-:])\s*')

def generate_dynamic_quiz_questions(level_name):
    if not GEMINI_API_KEY:
        return []

    sys_prompt = """أنت محرك فقهي ومحدث محقق. ولد 10 أسئلة شرعية جديدة اختيار من متعدد بالعربية.
اكتب كل سؤال في سطر منفصل بالضبط وفق هذا النموذج مستخدماً الرمز ||| للفصل:
نص السؤال ||| الإجابة الصحيحة ||| الخيار الخطأ الأول ||| الخيار الخطأ الثاني ||| الدليل والتخريج الشرعي"""

    content, _errors = _generate_text(sys_prompt, f"ولد 10 أسئلة شرعية جديدة للمستوى: {level_name}")
    if not content:
        return []
    parsed_questions = []
    for line in content.split("\n"):
        line = line.strip()
        if "|||" in line:
            line = _QUIZ_LINE_PREFIX.sub("", line).replace("**", "")
            parts = [p.strip() for p in line.split("|||")]
            if len(parts) >= 5:
                options = [parts[1], parts[2], parts[3]]
                # نتجاهل الأسئلة المشوهة (خيارات فارغة أو مكررة) لأنها تعطل الاختيار
                if parts[0] and all(options) and len(set(options)) == 3:
                    parsed_questions.append({
                        "question": parts[0], "correct": parts[1],
                        "options": options, "proof": parts[4]
                    })
    return parsed_questions

# 6. محرك المواريث والزكاة الحسابي القطعي
_FRACTION_LABELS = {
    Fraction(1, 2): "1/2 (النصف)", Fraction(1, 4): "1/4 (الربع)", Fraction(1, 8): "1/8 (الثمن)",
    Fraction(1, 3): "1/3 (الثلث)", Fraction(1, 6): "1/6 (السدس)", Fraction(2, 3): "2/3 (الثلثان)",
}

def _frac_text(fr: Fraction) -> str:
    return f"{fr.numerator}/{fr.denominator}"

def calculate_inheritance_engine(estate, deceased_gender, has_spouse, sons, daughters, has_father, has_mother):
    sons = int(sons or 0)
    daughters = int(daughters or 0)
    has_children = (sons + daughters) > 0

    # أصحاب الفروض (بكسور دقيقة لتفادي أخطاء الفاصلة العائمة)
    fixed = []
    spouse_frac = Fraction(0)

    if has_spouse:
        if deceased_gender.startswith("رجل"):
            name = "الزوجة"
            frac = Fraction(1, 8) if has_children else Fraction(1, 4)
        else:
            name = "الزوج"
            frac = Fraction(1, 4) if has_children else Fraction(1, 2)
        note = "لوجود الفرع الوارث (الأولاد)" if has_children else "لعدم وجود فرع وارث"
        fixed.append({"key": name, "frac": frac, "label": _FRACTION_LABELS[frac], "note": note, "spouse": True})
        spouse_frac = frac

    if has_mother:
        if has_children:
            frac, label = Fraction(1, 6), "1/6 (السدس)"
            note = "لوجود الفرع الوارث أو جمع من الإخوة"
        elif has_father and has_spouse:
            # العمريتان: للأم ثلث الباقي بعد فرض الزوج/الزوجة عند اجتماعها مع الأب
            frac = (1 - spouse_frac) / 3
            label = f"{_frac_text(frac)} (ثلث الباقي)"
            note = "ثلث الباقي بعد نصيب الزوج/الزوجة لاجتماعها مع الأب (العمريتان)"
        else:
            frac, label = Fraction(1, 3), "1/3 (الثلث)"
            note = "لعدم وجود فرع وارث"
        fixed.append({"key": "الأم", "frac": frac, "label": label, "note": note, "spouse": False})

    if has_father:
        if sons > 0:
            fixed.append({"key": "الأب", "frac": Fraction(1, 6), "label": "1/6 (السدس فرضاً)",
                          "note": "السدس فرضاً لوجود ابن ذكر", "spouse": False})
        elif daughters > 0:
            fixed.append({"key": "الأب (فرضاً)", "frac": Fraction(1, 6), "label": "1/6 (السدس)",
                          "note": "السدس فرضاً لوجود بنات", "spouse": False})

    if sons == 0 and daughters > 0:
        if daughters == 1:
            fixed.append({"key": "البنت الواحدة", "frac": Fraction(1, 2), "label": "1/2 (النصف)",
                          "note": "النصف فرضاً لانفرادها وعدم وجود عاصب", "spouse": False})
        else:
            fixed.append({"key": f"البنات ({daughters})", "frac": Fraction(2, 3), "label": "2/3 (الثلثان)",
                          "note": "الثلثان فرضاً يوزع بينهن بالتساوي", "spouse": False})

    shares = {}
    total_fixed = sum((f["frac"] for f in fixed), Fraction(0))

    # العول: إذا زادت الفروض عن أصل المسألة تُنقص الأنصبة بنسبة واحدة
    if total_fixed > 1:
        for f in fixed:
            new_frac = f["frac"] / total_fixed
            shares[f["key"]] = {
                "fraction": f"{f['label']} ← بعد العول {_frac_text(new_frac)}",
                "value": estate * float(new_frac),
                "note": f"{f['note']} • عالت المسألة (مجموع الفروض {_frac_text(total_fixed)} أكبر من الواحد)"
            }
        return shares

    remainder_frac = 1 - total_fixed
    has_asaba = sons > 0 or has_father  # الابن أو الأب (عند عدم وجود ابن) يأخذ الباقي تعصيباً

    if remainder_frac > 0 and not has_asaba:
        # الرد: يعود الباقي على أصحاب الفروض غير الزوجين بنسبة أنصبتهم
        eligible = [f for f in fixed if not f["spouse"]]
        if eligible:
            base = sum((f["frac"] for f in eligible), Fraction(0))
            for f in eligible:
                f["new_frac"] = f["frac"] + remainder_frac * (f["frac"] / base)
                f["note"] = f"{f['note']} • رُدّ عليه الباقي لعدم وجود عاصب"
                f["label"] = f"{f['label']} ← بعد الرد {_frac_text(f['new_frac'])}"
        elif fixed:
            sp = fixed[0]
            sp["new_frac"] = Fraction(1)
            sp["note"] = f"{sp['note']} • رُدّ الباقي عليه لعدم وجود وارث غيره (يُراجَع في ذلك المختصّ)"
            sp["label"] = f"{sp['label']} ← بعد الرد 1/1"
        remainder_frac = Fraction(0)

    for f in fixed:
        frac = f.get("new_frac", f["frac"])
        shares[f["key"]] = {"fraction": f["label"], "value": estate * float(frac), "note": f["note"]}

    if remainder_frac > 0:
        remainder = estate * float(remainder_frac)
        if sons > 0:
            total_parts = (sons * 2) + daughters
            part_value = remainder / total_parts
            shares[f"الأبناء الذكور ({sons})"] = {
                "fraction": "عصبة بالنفس (الباقي)",
                "value": part_value * 2 * sons,
                "note": f"نصيب كل ابن: {(part_value * 2):,.2f} ج.م"
            }
            if daughters > 0:
                shares[f"البنات ({daughters})"] = {
                    "fraction": "عصبة بالغير (للذكر مثل حظ الأنثيين)",
                    "value": part_value * daughters,
                    "note": f"نصيب كل بنت: {part_value:,.2f} ج.م"
                }
        elif has_father and daughters > 0:
            shares["الأب (تعصيباً)"] = {"fraction": "باقي التركة تعصيباً", "value": remainder,
                                         "note": "يرث الباقي تعصيباً بعد أصحاب الفروض"}
        elif has_father:
            shares["الأب"] = {"fraction": "عصبة بالنفس", "value": remainder,
                              "note": "يحوز باقي التركة تعصيباً لانعدام الفرع الوارث"}

    return shares

# 7. دوال التصدير والطباعة وشهادات الإنجاز
def create_printable_html(title: str, content: str) -> str:
    # تهريب النصوص حتى لا تكسر أي رموز < > الوثيقة المطبوعة (الآيات «» والفواصل تُنسّق بعد التهريب)
    title = html.escape(html.unescape(title or ""))
    formatted_content = format_quranic_text(html.escape(content or "", quote=False))
    return f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Amiri+Quran&family=Amiri:wght@400;700&family=Cairo:wght@600;800&display=swap');
            body {{ font-family: 'Cairo', sans-serif; margin: 40px; color: #1e293b; line-height: 1.8; }}
            .quran-ayah {{ font-family: 'Amiri Quran', 'Amiri', serif !important; font-size: 1.55rem !important; color: #059669 !important; background: #ecfdf5; padding: 4px 14px; border-radius: 8px; border-right: 4px solid #10b981; }}
            .madhab-divider {{ text-align: center; margin: 25px 0; border-top: 2px dashed #cbd5e1; padding-top: 10px; font-weight: bold; color: #0f766e; }}
            .header {{ text-align: center; border-bottom: 2px solid #0d9488; padding-bottom: 15px; margin-bottom: 25px; }}
            .header h1 {{ font-family: 'Amiri', serif; color: #0d9488; margin: 0; }}
            .content {{ font-size: 1.1rem; white-space: pre-wrap; }}
            .footer {{ margin-top: 40px; text-align: center; border-top: 1px solid #cbd5e1; padding-top: 15px; font-size: 0.9rem; color: #64748b; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🕌 الموسوعة الفقهية والحديثية الذكية</h1>
            <p>وثيقة استخراج وتوثيق شرعي معتمد</p>
        </div>
        <div class="content">{formatted_content}</div>
        <div class="footer">Developed by Eng. Abdelfttah Ragheb © 2026</div>
        <script>window.print();</script>
    </body>
    </html>
    """

def generate_certificate_html(user_name: str, tier_name: str, score: int, total: int) -> str:
    user_name = html.escape((user_name or "").strip() or "طالب العلم الفاضل")
    return f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <title>شهادة اجتياز وتفوق علمي</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@700&family=Aref+Ruqaa:wght@700&family=Cairo:wght@600;800;900&display=swap');
            body {{ font-family: 'Cairo', sans-serif; background: #020617; color: #f8fafc; padding: 30px; text-align: center; }}
            .cert-box {{ border: 4px solid #10b981; border-radius: 24px; padding: 40px 30px; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #064e3b 0%, #020617 100%); box-shadow: 0 0 35px rgba(16,185,129,0.3); }}
            h1 {{ font-family: 'Aref Ruqaa', serif; color: #34d399; font-size: 2.3rem; margin-bottom: 0.5rem; }}
            h2 {{ font-family: 'Amiri', serif; color: #6ee7b7; font-size: 1.8rem; margin: 15px 0; }}
            .desc {{ font-size: 1.2rem; color: #cbd5e1; line-height: 1.9; margin: 20px 0; }}
            .badge-highlight {{ color: #34d399; font-weight: 900; font-size: 1.4rem; }}
            .footer {{ margin-top: 35px; border-top: 1px solid rgba(16,185,129,0.3); padding-top: 20px; font-size: 0.95rem; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="cert-box">
            <h1>🕌 إجازة واجتياز علمي شرعي 🕌</h1>
            <p style="color:#34d399; font-size:1.1rem;">الموسوعة الفقهية والحديثية الذكية</p>
            <div class="desc">
                تشهد إدارة المنصة بأن الأخ / الباحث الفاضل:
                <br>
                <h2>✨ {user_name} ✨</h2>
                قد أتم بنجاح الاختبارات الفقهية والتأصيلية بنسبة إتقان رفيعة،<br>
                محققاً رصيداً علمياً قدره <strong>({score} إجابة صحيحة من {total})</strong>،<br>
                واستحق بموجب ذلك نيل الرتبة العلمية:
                <br><br>
                <span class="badge-highlight">📜 {tier_name} 📜</span>
            </div>
            <div class="footer">
                صدرت في: {time.strftime('%Y-%m-%d')} م • توثيق المنظومة الذكية<br>
                إشراف وتطوير: Eng. Abdelfttah Ragheb
            </div>
        </div>
        <script>window.print();</script>
    </body>
    </html>
    """

def generate_estate_csv(estate_total, shares_dict):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["الوارث الشرعي", "الفرض / الحالة الشرعية", "النصيب المستحق (ج.م)", "تفصيل وسند التوزيع"])
    for k, v in shares_dict.items():
        writer.writerow([k, v['fraction'], f"{v['value']:.2f}", v['note']])
    writer.writerow([])
    writer.writerow(["إجمالي التركة المالية", "", f"{estate_total:.2f} ج.م", ""])
    return output.getvalue().encode('utf-8-sig')

def get_user_mastery_tier(score, total_answered):
    if total_answered < 5:
        return "🌱 طالب علم مبتدئ", "#94a3b8"
    accuracy = (score / total_answered) * 100 if total_answered > 0 else 0
    if accuracy >= 80 and total_answered >= 10:
        return "👑 مفتٍ ومحقق معتمد", current_theme["secondary"]
    elif accuracy >= 65:
        return "📜 باحث فقهي متمكن", "#38bdf8"
    else:
        return "📖 مجتهد في طلب العلم", "#34d399"

# 8. إدارة حالة الجلسة والتنقل
if "active_view" not in st.session_state:
    st.session_state["active_view"] = "home"

if "stats" not in st.session_state:
    st.session_state["stats"] = {
        "fiqh_queries": 0, "hadith_queries": 0, "dict_queries": 0,
        "quran_queries": 0, "quiz_total_answered": 0, "quiz_correct_answered": 0
    }

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

if "bookmarks" not in st.session_state:
    st.session_state["bookmarks"] = []

if "tasbeeh_count" not in st.session_state:
    st.session_state["tasbeeh_count"] = 0

if "hadith_result" not in st.session_state:
    st.session_state["hadith_result"] = ""
if "hadith_query_saved" not in st.session_state:
    st.session_state["hadith_query_saved"] = ""

if "dict_result" not in st.session_state:
    st.session_state["dict_result"] = ""
if "dict_query_saved" not in st.session_state:
    st.session_state["dict_query_saved"] = ""

if "quran_result" not in st.session_state:
    st.session_state["quran_result"] = ""
if "quran_query_saved" not in st.session_state:
    st.session_state["quran_query_saved"] = ""

if "zakah_pdf_doc" not in st.session_state:
    st.session_state["zakah_pdf_doc"] = ""

if "estate_pdf_doc" not in st.session_state:
    st.session_state["estate_pdf_doc"] = ""
if "estate_csv_data" not in st.session_state:
    st.session_state["estate_csv_data"] = None
if "estate_results_cache" not in st.session_state:
    st.session_state["estate_results_cache"] = None

if "zakah_view" not in st.session_state:
    st.session_state["zakah_view"] = None
if "quiz_round_id" not in st.session_state:
    st.session_state["quiz_round_id"] = 0
if "quiz_balloons_shown" not in st.session_state:
    st.session_state["quiz_balloons_shown"] = False
if "last_imported_backup" not in st.session_state:
    st.session_state["last_imported_backup"] = None

if "quiz_pool" not in st.session_state:
    st.session_state["quiz_pool"] = copy.deepcopy(EXPANDED_QUIZ_DATABASE)
if "quiz_level" not in st.session_state:
    st.session_state["quiz_level"] = list(EXPANDED_QUIZ_DATABASE.keys())[0]
if "seen_questions" not in st.session_state:
    st.session_state["seen_questions"] = set()
if "current_round_questions" not in st.session_state:
    st.session_state["current_round_questions"] = []
if "quiz_idx" not in st.session_state:
    st.session_state["quiz_idx"] = 0
if "quiz_score" not in st.session_state:
    st.session_state["quiz_score"] = 0
if "quiz_answered" not in st.session_state:
    st.session_state["quiz_answered"] = False
if "quiz_feedback" not in st.session_state:
    st.session_state["quiz_feedback"] = None
if "shuffled_options" not in st.session_state:
    st.session_state["shuffled_options"] = []

if "daily_challenge_done" not in st.session_state:
    st.session_state["daily_challenge_done"] = False
if "daily_challenge_score" not in st.session_state:
    st.session_state["daily_challenge_score"] = 0

def prepare_new_round(level):
    pool = st.session_state["quiz_pool"][level]
    unseen = [q for q in pool if q["question"] not in st.session_state["seen_questions"]]
    if len(unseen) < 4:
        st.session_state["seen_questions"] = set()
        unseen = list(pool)  # نسخة حتى لا نخلط قائمة البنك الأصلية في مكانها
    random.shuffle(unseen)
    selected_round = unseen[:8]
    for q in selected_round:
        st.session_state["seen_questions"].add(q["question"])
    st.session_state["current_round_questions"] = selected_round
    st.session_state["quiz_round_id"] += 1
    st.session_state["quiz_balloons_shown"] = False
    st.session_state["quiz_idx"] = 0
    st.session_state["quiz_score"] = 0
    st.session_state["quiz_answered"] = False
    st.session_state["quiz_feedback"] = None
    st.session_state["shuffled_options"] = []

if not st.session_state["current_round_questions"]:
    prepare_new_round(st.session_state["quiz_level"])

# شريط اختيارات التخصيص العلوي
# الاختيار مربوط مباشرة بمفتاح الجلسة (key) فتُطبَّق السمة في نفس الدورة دون st.rerun() إضافي
col_top_theme, col_top_bg = st.columns(2)
with col_top_theme:
    st.selectbox("🎨 سمة الألوان المتنوعة:", list(THEME_CONFIGS.keys()), key="app_theme")

with col_top_bg:
    st.selectbox("🕌 المعلم المعماري بالخلفية:", list(BG_IMAGES_CONFIG.keys()), key="app_bg_image")

# بطاقة الذكر اليومي
st.markdown(f"""
<div class="dhikr-card">
    <p class="dhikr-text">✨ سُبْحَانَ اللَّهِ وَبِحَمْدِهِ ، سُبْحَانَ اللَّهِ الْعَظِيمِ • اللَّهُمَّ صَلِّ وَسَلِّمْ عَلَىٰ نَبِيِّنَا مُحَمَّدٍ ✨</p>
</div>
""", unsafe_allow_html=True)

# ----------------- الشاشة الرئيسية -----------------
if st.session_state["active_view"] == "home":
    st.markdown(f"""
    <div class="royal-hero">
        <h1>🕌 الموسوعة الفقهية والحديثية</h1>
        <p>البوابة الرقمية الشاملة للأحكام الشرعية وتخريج السنة النبوية</p>
    </div>
    """, unsafe_allow_html=True)

    st.info("⚠️ **تنبيه مهم:** الإجابات مُولَّدة بالذكاء الاصطناعي للاسترشاد والتعلم فقط، وليست فتوى رسمية. قد تحتمل الخطأ، فيُرجع في المسائل المهمة إلى أهل العلم الثقات ودور الإفتاء المعتمدة.")

    today_snippet = DAILY_FIQH_SNIPPETS[int(time.time() / 86400) % len(DAILY_FIQH_SNIPPETS)]
    st.markdown(f"""
    <div class="daily-card">
        <span class="daily-badge">💡 مسألة اليوم الفقهية</span>
        <h4 style="color:{current_theme['secondary']}; margin:0.3rem 0; font-size:1.1rem;">{today_snippet['topic']}</h4>
        <p style="color:#e2e8f0; font-size:0.95rem; margin:0; line-height:1.7;">{format_quranic_text(today_snippet['text'])}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='circle-icon-badge'>🏛️</div><div style='text-align:center;'><div class='circle-card-title'>المحاور الفقهي</div><div class='circle-card-desc'>فتاوى ومقارنة المذاهب</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='hub-grid-btn'>", unsafe_allow_html=True)
        if st.button("دخول القسم الفقهي", key="btn_hub_fiqh", use_container_width=True):
            st.session_state["active_view"] = "fiqh"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='circle-icon-badge'>📜</div><div style='text-align:center;'><div class='circle-card-title'>التحقيق الحديثي</div><div class='circle-card-desc'>تخريج ومعجم الألفاظ</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='hub-grid-btn'>", unsafe_allow_html=True)
        if st.button("دخول قسم الحديث", key="btn_hub_hadith", use_container_width=True):
            st.session_state["active_view"] = "hadith"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("<div class='circle-icon-badge'>📖</div><div style='text-align:center;'><div class='circle-card-title'>القرآن والتفسير</div><div class='circle-card-desc'>استخراج موضوعي بالمعنى</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='hub-grid-btn'>", unsafe_allow_html=True)
        if st.button("دخول قسم القرآن", key="btn_hub_quran", use_container_width=True):
            st.session_state["active_view"] = "quran"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col4:
        st.markdown("<div class='circle-icon-badge'>⚖️</div><div style='text-align:center;'><div class='circle-card-title'>الزكاة والأسهم والتركات</div><div class='circle-card-desc'>حساب الأسهم والمواريث</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='hub-grid-btn'>", unsafe_allow_html=True)
        if st.button("دخول قسم الفرائض والمالية", key="btn_hub_calc", use_container_width=True):
            st.session_state["active_view"] = "calc"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    col5, col6 = st.columns(2)
    with col5:
        st.markdown("<div class='circle-icon-badge'>📿</div><div style='text-align:center;'><div class='circle-card-title'>السبحة والأذكار</div><div class='circle-card-desc'>أذكار محققة وعداد</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='hub-grid-btn'>", unsafe_allow_html=True)
        if st.button("دخول السبحة والأذكار", key="btn_hub_tasbeeh", use_container_width=True):
            st.session_state["active_view"] = "tasbeeh"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col6:
        st.markdown("<div class='circle-icon-badge'>⭐</div><div style='text-align:center;'><div class='circle-card-title'>المفضلة والنسخ</div><div class='circle-card-desc'>تصدير ومزامنة JSON</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='hub-grid-btn'>", unsafe_allow_html=True)
        if st.button("دخول المفضلة والنسخ", key="btn_hub_bookmarks", use_container_width=True):
            st.session_state["active_view"] = "bookmarks"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='circle-icon-badge'>🏆</div><div style='text-align:center;'><div class='circle-card-title'>المسابقات والشهادات العلمية</div><div class='circle-card-desc'>تحديات يومية ورتب وإجازات</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='hub-grid-btn'>", unsafe_allow_html=True)
    if st.button("دخول بنك المسابقات والتحدي اليومي", key="btn_hub_quiz", use_container_width=True):
        st.session_state["active_view"] = "quiz"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- 1. شاشة الفقه والاستفتاء -----------------
elif st.session_state["active_view"] == "fiqh":
    st.markdown("<div class='back-nav-btn'>", unsafe_allow_html=True)
    if st.button("⬅️ العودة للرئيسية", use_container_width=True):
        st.session_state["active_view"] = "home"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="royal-hero">
        <h1>🏛️ المحاور الفقهي المباشر</h1>
        <p>استعراض الفتاوى • فواصل مقارنة المذاهب الأربعة • بطاقات مشاركة سريعة</p>
    </div>
    """, unsafe_allow_html=True)

    selected_madhab = st.selectbox("المذهب الفقهي:", [
        "مقارنة المذاهب الأربعة كاملة (الحنفي، المالكي، الشافعي، الحنبلي)", "المذهب الحنفي فقط", "المذهب المالكي فقط", "المذهب الشافعي فقط", "المذهب الحنبلي فقط"
    ])
    depth_level = st.selectbox("مستوى التفصيل:", ["موجز ميسر", "متوسط وتأصيلي", "بحث فقهي موسع"], index=1)

    if st.session_state["chat_messages"]:
        if st.button("🗑️ مسح المحادثة وبدء جلسة جديدة"):
            st.session_state["chat_messages"] = []
            st.rerun()

    for msg in st.session_state["chat_messages"]:
        if msg["role"] == "user":
            st.markdown(f"<div style='background:rgba(30,58,138,0.35); border:1px solid rgba(59,130,246,0.4); border-radius:14px; padding:0.9rem; margin-bottom:0.7rem;'>👤 <strong>السؤال:</strong> {msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:rgba(15,23,42,0.9); border:1.5px solid {current_theme['border_color']}; border-radius:14px; padding:1.1rem; margin-bottom:1.1rem;'>🕌 <strong>البيان الفقهي:</strong><br>{format_quranic_text(msg['content'])}</div>", unsafe_allow_html=True)

    chat_input = st.text_input("اكتب استفسارك الفقهي هنا:", placeholder="مثال: حكم صلاة الوتر وصفتها؟ وهل تجوز بركعة واحدة؟...", key="chat_fiqh_input")
    
    col_fbtn1, col_fbtn2 = st.columns([3, 2])
    with col_fbtn1:
        st.markdown("<div class='action-submit-btn'>", unsafe_allow_html=True)
        send_fiqh = st.button("💬 إرسال واستفتاء", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_fbtn2:
        st.markdown("<div class='action-submit-btn'>", unsafe_allow_html=True)
        send_matrix = st.button("⚖️ مقارنة المذاهب الأربعة بفواصل", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if send_fiqh or send_matrix:
        cleaned_chat_query = sanitize_user_input(chat_input, max_chars=400)
        if not cleaned_chat_query:
            st.warning("⚠️ يرجى كتابة الاستفسار أولاً.")
        else:
            st.session_state["chat_messages"].append({"role": "user", "content": cleaned_chat_query})
            chat_out = st.empty()
            
            if send_matrix:
                chat_sys = """أنت محقق فقهي مقارن رصين. اعرض حكم المسألة بدقة تامة بين المذاهب الأربعة.
افصل بين كل مذهب بعنوان صريح في سطر منفصل بالضبط هكذا:
### المذهب الحنفي
(اكتب تفصيل مذهب الحنفية ودليلهم)

### المذهب المالكي
(اكتب تفصيل مذهب المالكية ودليلهم)

### المذهب الشافعي
(اكتب تفصيل مذهب الشافعية ودليلهم)

### المذهب الحنبلي
(اكتب تفصيل مذهب الحنابلة ودليلهم)

وضع نصوص الآيات الكريمة بدقة بين علامتي « ... » بالعربية الفصحى فقط."""
            else:
                chat_sys = f"""
أنت مفتٍ ومحاور فقهي ومحدث محقق.
المذهب المطلوب: {selected_madhab}
مستوى التفصيل: {depth_level}

هيكل الإجابة المطلوب بالعربية الفصحى فقط:
# 📌 خلاصة الحكم الشرعي المباشر
# 📖 الاستدلال من القرآن الكريم والسنة النبوية (ضع الآيات بين « ... »)
# 🏛️ أقوال الأئمة والمذاهب المعتمدة
# 💡 توجيه وإرشاد تطبيقي
"""
            ans = execute_gemini_chat(st.session_state["chat_messages"], chat_sys, chat_out)
            if ans:
                st.session_state["chat_messages"].append({"role": "assistant", "content": ans})
                st.session_state["stats"]["fiqh_queries"] += 1
                st.rerun()
            else:
                # فشل الرد: نزيل السؤال حتى لا يبقى سجل المحادثة مكسوراً (سؤالان متتاليان بلا جواب)
                st.session_state["chat_messages"].pop()

    if st.session_state["chat_messages"] and st.session_state["chat_messages"][-1]["role"] == "assistant":
        last_q = [m["content"] for m in st.session_state["chat_messages"] if m["role"] == "user"][-1]
        last_a = st.session_state["chat_messages"][-1]["content"]
        
        st.markdown("---")
        with st.expander("📲 بطاقة المشاركة السريعة لشبكات التواصل (WhatsApp / Facebook)", expanded=False):
            st.markdown(f"""
            <div class="social-share-card">
                <div style="color:{current_theme['secondary']}; font-weight:800; font-size:1.1rem; margin-bottom:0.4rem;">🕌 فتوى شرعية مستخرجة</div>
                <div style="color:#ffffff; font-weight:700; margin-bottom:0.6rem;">❓ المسألة: {last_q}</div>
                <div style="color:#e2e8f0; font-size:0.95rem; line-height:1.7;">{format_quranic_text(last_a[:350])}...</div>
                <div style="color:#94a3b8; font-size:0.8rem; margin-top:0.8rem; border-top:1px dashed {current_theme['border_color']}; padding-top:0.4rem;">الموسوعة الفقهية والحديثية الذكية • إشراف: Eng. Abdelfttah Ragheb</div>
            </div>
            """, unsafe_allow_html=True)
            st.code(f"مسألة: {last_q}\n\nالجواب: {last_a[:400]}...\n\n(الموسوعة الفقهية والحديثية الذكية)", language="text")

        chosen_tag = st.selectbox("🏷️ اختر وسم الفتوى للحفظ:", ["#عبادات_وصلاة", "#معاملات_ومال", "#صيام_وزكاة", "#أحوال_شخصية", "#فقه_عام"])
        col_fb1, col_fb2 = st.columns(2)
        with col_fb1:
            if st.button("⭐ حفظ في المفضلة", use_container_width=True):
                st.session_state["bookmarks"].append({"question": last_q, "answer": last_a, "tag": chosen_tag, "date": time.strftime("%Y-%m-%d %H:%M")})
                st.success("✅ تم الحفظ بنجاح في هاتفك!")
        with col_fb2:
            st.download_button(
                label="📄 طباعة وحفظ الفتوى (PDF)",
                data=create_printable_html(last_q, last_a),
                file_name="fatwa_document.html",
                mime="text/html",
                use_container_width=True
            )

# ----------------- 2. شاشة الحديث ومعجم الألفاظ -----------------
elif st.session_state["active_view"] == "hadith":
    st.markdown("<div class='back-nav-btn'>", unsafe_allow_html=True)
    if st.button("⬅️ العودة للرئيسية", use_container_width=True):
        st.session_state["active_view"] = "home"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="royal-hero">
        <h1>📜 تخريج الحديث ومعجم الألفاظ</h1>
        <p>التحقق من صحة الأحاديث • الرواة والمصادر • بيان الألفاظ الغريبة</p>
    </div>
    """, unsafe_allow_html=True)

    hadith_input = st.text_input("اكتب نص الحديث أو جزءاً منه:", max_chars=350, placeholder="مثال: إنما الأعمال بالنيات...")
    st.markdown("<div class='action-submit-btn'>", unsafe_allow_html=True)
    hadith_clicked = st.button("🔍 تخريج وتحقيق الحديث", use_container_width=True)
    h_output = st.empty()
    if hadith_clicked:
        cleaned_hadith = sanitize_user_input(hadith_input, max_chars=350)
        if not cleaned_hadith:
            st.warning("⚠️ يرجى إدخال نص الحديث أولاً.")
        else:
            h_sys = """
أنت عالم ومحدث محقق في علوم الحديث والجرح والتعديل.
قم بتخريج الحديث باللغة العربية الفصحى حصراً وبدون أي كلمة أجنبية (ضع الآيات والحديث الشريف بين « ... »):
# 📜 بطاقة تخريج الحديث النبوي
- **نص المتن الصحيح**: «النص مع الضبط»
- 👤 **الصحابي راوي الحديث**:
- 📚 **المصادر ورقم الحديث والباب**: (مثال: صحيح البخاري، كتاب بدء الوحي، باب كيف كان بدء الوحي، رقم 1)
- ⚖️ **حكم المحدثين ورتبته الدقيقة**: (صحيح / حسن / ضعيف مع بيان كلام الأئمة)
- 💡 **الفوائد الفقهية والعملية المستنبطة**:
"""
            h_res = execute_gemini_prompt(cleaned_hadith, h_sys, h_output)
            if h_res:
                st.session_state["hadith_result"] = h_res
                st.session_state["hadith_query_saved"] = cleaned_hadith
                st.session_state["stats"]["hadith_queries"] += 1
    elif st.session_state["hadith_result"]:
        # إبقاء النتيجة ظاهرة بعد أي تفاعل آخر (مثل تحميل الملف) بدل أن تختفي
        h_output.markdown(f"<br>{format_quranic_text(st.session_state['hadith_result'])}", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state["hadith_result"]:
        st.download_button(
            label="📄 تصدير / طباعة تحقيق الحديث (PDF)",
            data=create_printable_html(f"تحقيق حديث: {st.session_state['hadith_query_saved']}", st.session_state["hadith_result"]),
            file_name="hadith_verification.html",
            mime="text/html",
            use_container_width=True
        )

    st.markdown("---")
    term_input = st.text_input("اكتب اللفظ أو المصطلح الشرعي المراد تفسيره:", max_chars=100, placeholder="مثال: الصاع، العول، الكلالة، القسامة...")
    st.markdown("<div class='action-submit-btn'>", unsafe_allow_html=True)
    term_clicked = st.button("📖 شرح وتفسير المصطلح", use_container_width=True)
    t_output = st.empty()
    if term_clicked:
        cleaned_term = sanitize_user_input(term_input, max_chars=100)
        if not cleaned_term:
            st.warning("⚠️ يرجى كتابة المصطلح أولاً.")
        else:
            t_sys = """
أنت معجمي وفقهي محقق.
اشرح المصطلح الشرعي باللغة العربية الفصحى فقط وبشكل دقيق (ضع الآيات بين « ... »):
# 📖 بيان المصطلح الشرعي
- **المعنى اللغوي والاصطلاحي**:
- **المقدار المعاصر (إن وجد)**:
- **أمثلة وتطبيقات فقهية**:
"""
            t_res = execute_gemini_prompt(cleaned_term, t_sys, t_output)
            if t_res:
                st.session_state["dict_result"] = t_res
                st.session_state["dict_query_saved"] = cleaned_term
                st.session_state["stats"]["dict_queries"] += 1
    elif st.session_state["dict_result"]:
        t_output.markdown(f"<br>{format_quranic_text(st.session_state['dict_result'])}", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state["dict_result"]:
        st.download_button(
            label="📄 تصدير / طباعة بيان المصطلح (PDF)",
            data=create_printable_html(f"بيان مصطلح: {st.session_state['dict_query_saved']}", st.session_state["dict_result"]),
            file_name="term_explanation.html",
            mime="text/html",
            use_container_width=True
        )

# ----------------- 3. شاشة القرآن والتفسير -----------------
elif st.session_state["active_view"] == "quran":
    st.markdown("<div class='back-nav-btn'>", unsafe_allow_html=True)
    if st.button("⬅️ العودة للرئيسية", use_container_width=True):
        st.session_state["active_view"] = "home"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="royal-hero">
        <h1>📖 قسم القرآن والتفسير الموضوعي</h1>
        <p>استخراج الآيات بالمفهوم والمعنى • أسباب النزول • الاستنباطات الفقهية</p>
    </div>
    """, unsafe_allow_html=True)

    quran_topic = st.text_input("اكتب الموضوع أو الفكرة القرآنية:", placeholder="مثال: البر بالوالدين، الإنفاق والصدقة، الصبر، أكل أموال الناس بالباطل...")
    st.markdown("<div class='action-submit-btn'>", unsafe_allow_html=True)
    quran_clicked = st.button("📖 استخراج الآيات والتفسير الموضوعي", use_container_width=True)
    q_output = st.empty()
    if quran_clicked:
        cleaned_qtopic = sanitize_user_input(quran_topic, max_chars=200)
        if not cleaned_qtopic:
            st.warning("⚠️ يرجى كتابة الموضوع أولاً.")
        else:
            q_sys = """
أنت عالم مفسر ومحقق في التفسير الموضوعي وعلوم القرآن.
استخرج الآيات واشرحها باللغة العربية الفصحى فقط وضع نصوص الآيات بدقة بين علامتي « ... » ليتم عرضها برسم المصحف الشريف:
# 📖 الآيات القرآنية ذات الصلة بالموضوع
- «نص الآية الكريمة كاملة مع التشكيل» [السورة: رقم الآية]

# 💡 التفسير الميسر وأسباب النزول
(اعتماداً على تفسير ابن كثير والسعدي)

# ⚖️ الاستنباطات والفوائد الفقهية والعملية
"""
            q_res = execute_gemini_prompt(cleaned_qtopic, q_sys, q_output)
            if q_res:
                st.session_state["quran_result"] = q_res
                st.session_state["quran_query_saved"] = cleaned_qtopic
                st.session_state["stats"]["quran_queries"] += 1
    elif st.session_state["quran_result"]:
        q_output.markdown(f"<br>{format_quranic_text(st.session_state['quran_result'])}", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state["quran_result"]:
        st.download_button(
            label="📄 تصدير / طباعة التفسير القرآني (PDF)",
            data=create_printable_html(f"التفسير الموضوعي: {st.session_state['quran_query_saved']}", st.session_state["quran_result"]),
            file_name="quran_interpretation.html",
            mime="text/html",
            use_container_width=True
        )

# ----------------- 4. شاشة الزكاة والأسهم والمواريث (محدثة بالأسعار التلقائية) -----------------
elif st.session_state["active_view"] == "calc":
    st.markdown("<div class='back-nav-btn'>", unsafe_allow_html=True)
    if st.button("⬅️ العودة للرئيسية", use_container_width=True):
        st.session_state["active_view"] = "home"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="royal-hero">
        <h1>⚖️ حاسبة الزكاة والأسهم والمواريث (ج.م)</h1>
        <p>أسعار الذهب المباشرة • زكاة الأسهم والمحافظ • شجرة المواريث وتصدير Excel</p>
    </div>
    """, unsafe_allow_html=True)

    calc_sub_type = st.radio("اختر العملية الحسابية:", [
        "💰 زكاة الأموال والذهب والفضة",
        "📈 زكاة الأسهم والمحافظ الاستثمارية",
        "👨‍👩‍👧‍👦 توزيع التركات وشجرة المواريث"
    ], horizontal=True)

    if calc_sub_type.startswith("💰"):
        live_price_banner()
        market_data = get_market_data()
        market_gold_prices = {"24": market_data["gold24"], "21": market_data["gold21"], "18": market_data["gold18"]}

        col_g1, col_g2 = st.columns([2, 1])
        with col_g1:
            selected_karat = st.selectbox(
                "عيار الذهب المتوفر لديك:",
                ["عيار 21 (الأكثر تداولاً)", "عيار 24 (الذهب الخالص)", "عيار 18"]
            )
        with col_g2:
            if st.button("🔄 تحديث السعر"):
                st.cache_data.clear()
                st.rerun()

        if "24" in selected_karat:
            auto_price = market_gold_prices.get("24", 4685.0)
        elif "21" in selected_karat:
            auto_price = market_gold_prices.get("21", 4100.0)
        else:
            auto_price = market_gold_prices.get("18", 3514.0)

        gold_price_input = st.number_input(
            f"سعر جرام الذهب في السوق ({selected_karat}):",
            min_value=1.0,
            value=float(auto_price),
            step=10.0,
            help="تم جلب السعر تلقائياً من السوق المالي، ويمكنك تعديله يدوياً إذا اختلف السعر الفعلي لديك."
        )

        gold_weight_input = st.number_input("وزن الذهب المدخر بالجرام:", min_value=0.0, value=0.0, step=1.0)
        cash_amount = st.number_input("السيولة النقدية / الودائع والتجارة (بالجنيه المصري):", min_value=0.0, value=0.0, step=1000.0)
        silver_weight = st.number_input("وزن الفضة المدخرة بالجرام (إن وجد):", min_value=0.0, value=0.0, step=10.0)
        silver_price = st.number_input(
            "سعر جرام الفضة اليوم (بالجنيه المصري):", min_value=1.0,
            value=float(market_data.get("silver_g") or _SILVER_FALLBACK_PER_GRAM), step=2.0,
            help="يُجلب تلقائياً من السوق العالمي ويتحدث كل 5 دقائق، ويمكنك تعديله يدوياً."
        )
            
        st.markdown("<div class='action-submit-btn'>", unsafe_allow_html=True)
        if st.button("🧮 احتساب تفاصيل الزكاة الشرعية", use_container_width=True):
            if "24" in selected_karat:
                price_24 = gold_price_input
                karat_nisab = 85.0
            elif "21" in selected_karat:
                price_24 = gold_price_input * (24 / 21)
                karat_nisab = 85.0 * (24 / 21)
            else:
                price_24 = gold_price_input * (24 / 18)
                karat_nisab = 85.0 * (24 / 18)
                
            nisab_in_egp = 85.0 * price_24
            gold_val_egp = gold_weight_input * gold_price_input
            silver_val_egp = silver_weight * silver_price
            total_wealth_egp = cash_amount + gold_val_egp + silver_val_egp
            
            is_nisab_reached = total_wealth_egp >= nisab_in_egp
            zakah_due_egp = total_wealth_egp * 0.025 if is_nisab_reached else 0.0

            z_table = f"""
| البند المالي الشرعي | القيمة / المقدار | البيان والتفصيل |
| :--- | :--- | :--- |
| **قيمة الذهب المدخر** | `{gold_val_egp:,.2f} ج.م` | وزن `{gold_weight_input} جم` ({selected_karat}) بسعر `{gold_price_input:,.2f} ج.م` |
| **السيولة النقدية والتجارة** | `{cash_amount:,.2f} ج.م` | الأموال النقدية والمدخرات البنكية |
| **قيمة الفضة المدخرة** | `{silver_val_egp:,.2f} ج.م` | وزن `{silver_weight} جم` |
| **إجمالي الوعاء الزكوي** | **`{total_wealth_egp:,.2f} ج.م`** | مجموع الأموال المتاحة للزكاة |
| **حد النصاب الشرعي** | **`{nisab_in_egp:,.2f} ج.م`** | يعادل `85 جرام ذهب عيار 24` (أو `{karat_nisab:.2f} جم` لـ {selected_karat}) |
| **حالة بلوغ النصاب** | **{'بلغ النصاب الشرعي ✅' if is_nisab_reached else 'لم يبلغ النصاب بعد ❌'}** | يشترط مرور حول كامل (سنة هجرية) |
| **مقدار الزكاة الواجبة فوراً** | **`{zakah_due_egp:,.2f} ج.م`** | **نسبة 2.5% (ربع العشر)** |
"""
            status_text = f"الواجب إخراجه شرعاً: {zakah_due_egp:,.2f} جنيه مصري" if is_nisab_reached else "المال لم يبلغ النصاب الشرعي بعد"
            st.session_state["zakah_pdf_doc"] = f"تقرير احتساب الزكاة الشرعية\n\nإجمالي الوعاء: {total_wealth_egp:,.2f} ج.م\nحد النصاب: {nisab_in_egp:,.2f} ج.م\nالنتيجة: {status_text}\n\nنسبة الزكاة المقررة: 2.5% (ربع العشر)."

            if is_nisab_reached:
                verdict = ("success", f"✅ **تجب الزكاة شرعاً:** الواجب إخراجه هو **`{zakah_due_egp:,.2f} جنيه مصري`** تُدفع لمصارف الزكاة.")
            else:
                shortage = nisab_in_egp - total_wealth_egp
                verdict = ("info", f"ℹ️ **لا تجب الزكاة حالياً:** ينقص مالك مبلغ **`{shortage:,.2f} جنيه مصري`** ليصل إلى النصاب.")
            # نحفظ النتيجة في الجلسة كي لا تختفي عند الضغط على زر التحميل أو أي تفاعل آخر
            st.session_state["zakah_view"] = {"table": z_table, "verdict": verdict}
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state["zakah_view"]:
            st.markdown("### 📊 جدول البيان المالي للزكاة:")
            st.markdown(st.session_state["zakah_view"]["table"])
            v_kind, v_msg = st.session_state["zakah_view"]["verdict"]
            if v_kind == "success":
                st.success(v_msg)
            else:
                st.info(v_msg)

        if st.session_state["zakah_pdf_doc"]:
            st.download_button(
                label="📄 تصدير / طباعة بيان الزكاة (PDF)",
                data=create_printable_html("تقرير حساب الزكاة الشرعية", st.session_state["zakah_pdf_doc"]),
                file_name="zakah_report.html",
                mime="text/html",
                use_container_width=True
            )

    elif calc_sub_type.startswith("📈"):
        st.markdown("### 📈 حاسبة زكاة الأسهم والمحافظ الاستثمارية:")
        stock_intent = st.selectbox(
            "الغرض من ملكية الأسهم:",
            ["أسهم مضاربة وتجارة (بيع وشراء قصير الأجل)", "أسهم استثمار طويل الأجل (لأجل العوائد والأرباح)"]
        )
        live_price_banner()
        market_gold = fetch_egypt_gold_prices()
        default_gold24 = market_gold.get("24", 4685.0)
        gold_ref_price = st.number_input("سعر جرام الذهب عيار 24 لتحديد النصاب (ج.م):", min_value=1.0, value=float(default_gold24), step=25.0)
        nisab_stock_val = gold_ref_price * 85.0

        if "مضاربة" in stock_intent:
            st.info("💡 **الحكم الشرعي لأسهم المضاربة:** تُعامل معاملة عروض التجارة، وتُحسب الزكاة بنسبة **2.5%** من القيمة السوقية الإجمالية للأسهم في يوم تمام الحول.")
            portfolio_market_val = st.number_input("القيمة السوقية الحالية لجميع الأسهم (ج.م):", min_value=0.0, value=200000.0, step=5000.0)
            cash_in_broker = st.number_input("السيولة النقدية المتبقية في محفظة التداول (ج.م):", min_value=0.0, value=15000.0, step=1000.0)
            
            st.markdown("<div class='action-submit-btn'>", unsafe_allow_html=True)
            if st.button("🧮 احتساب زكاة أسهم المضاربة", use_container_width=True):
                total_stock_wealth = portfolio_market_val + cash_in_broker
                reaches_n = total_stock_wealth >= nisab_stock_val
                due_zakah = total_stock_wealth * 0.025 if reaches_n else 0.0
                
                st.markdown(f"""
                | البند | القيمة |
                | :--- | :--- |
                | إجمالي القيمة السوقية والسيولة | **`{total_stock_wealth:,.2f} ج.م`** |
                | نصاب الذهب الشرعي (85 جم عيار 24) | `{nisab_stock_val:,.2f} ج.م` |
                | حالة بلوغ النصاب | **{'بلغ النصاب الشرعي ✅' if reaches_n else 'دون النصاب ❌'}** |
                | **الزكاة الواجبة فوراً (2.5%)** | **`{due_zakah:,.2f} ج.م`** |
                """)
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.info("💡 **الحكم الشرعي لأسهم الاستثمار:** الزكاة تجب على الأصول الزكوية للشركة (السيولة والمخزون)، أو تخرج الزكاة على الأرباح الموزعة بنسبة **2.5%** عند قبضها ومرور الحول عليها إن لم تتيسر ميزانية الشركة.")
            dividends_amount = st.number_input("إجمالي الأرباح النقدية الموزعة المقبوضة (ج.م):", min_value=0.0, value=30000.0, step=1000.0)
            other_savings = st.number_input("الأموال والمدخرات الأخرى المضمومة إليها (ج.م):", min_value=0.0, value=0.0, step=1000.0)
            
            st.markdown("<div class='action-submit-btn'>", unsafe_allow_html=True)
            if st.button("🧮 احتساب زكاة أرباح الأسهم", use_container_width=True):
                total_div_wealth = dividends_amount + other_savings
                reaches_n = total_div_wealth >= nisab_stock_val
                due_div_zakah = total_div_wealth * 0.025 if reaches_n else 0.0
                
                st.markdown(f"""
                | البند | القيمة |
                | :--- | :--- |
                | إجمالي الأرباح والمدخرات | **`{total_div_wealth:,.2f} ج.م`** |
                | نصاب الذهب الشرعي | `{nisab_stock_val:,.2f} ج.م` |
                | حالة النصاب | **{'بلغ النصاب الشرعي ✅' if reaches_n else 'دون النصاب ❌'}** |
                | **الزكاة الواجبة على الأرباح (2.5%)** | **`{due_div_zakah:,.2f} ج.م`** |
                """)
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        estate_val = st.number_input("إجمالي قيمة التركة المالية (بالجنيه المصري):", min_value=100.0, value=500000.0, step=10000.0)
        deceased_gender = st.radio("المتوفى:", ["رجل (ترك زوجة/أولاد)", "امرأة (تركت زوج/أولاد)"], horizontal=True)
        has_spouse = st.checkbox("يوجد الزوج / الزوجة على قيد الحياة", value=True)
        sons_count = st.number_input("عدد الأبناء (ذكور):", min_value=0, max_value=20, value=2)
        daughters_count = st.number_input("عدد البنات (إناث):", min_value=0, max_value=20, value=2)
        has_father = st.checkbox("الأب حي", value=False)
        has_mother = st.checkbox("الأم حية", value=True)
            
        st.markdown("<div class='action-submit-btn'>", unsafe_allow_html=True)
        estate_clicked = st.button("⚖️ احتساب التوزيع الشرعي والأدلة", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if estate_clicked:
            new_results = calculate_inheritance_engine(estate_val, deceased_gender, has_spouse, sons_count, daughters_count, has_father, has_mother)
            if not new_results:
                st.session_state["estate_results_cache"] = None
                st.session_state["estate_csv_data"] = None
                st.session_state["estate_pdf_doc"] = ""
                st.warning("⚠️ يرجى تحديد وارث واحد على الأقل لإجراء القسمة.")
            else:
                st.session_state["estate_results_cache"] = {"results": new_results, "estate_val": estate_val, "ai_text": ""}
                st.session_state["estate_csv_data"] = generate_estate_csv(estate_val, new_results)

        # النتائج محفوظة في الجلسة فلا تختفي عند الضغط على أزرار التصدير
        estate_cache = st.session_state["estate_results_cache"]
        if estate_cache:
            results = estate_cache["results"]
            estate_total = estate_cache["estate_val"]

            st.markdown("### 🌳 شجرة توزيع الميراث البصرية:")
            col_tree1, col_tree2 = st.columns(2)
            with col_tree1:
                st.markdown(f"<p style='color:{current_theme['secondary']}; font-weight:bold;'>👑 أصحاب الفروض المقدرة:</p>", unsafe_allow_html=True)
                for k, v in results.items():
                    if "عصبة" not in v['fraction'] and "تعصيباً" not in v['fraction']:
                        st.markdown(f"<div class='tree-card-fard'><strong>{k}</strong>: {v['fraction']}<br><span style='color:{current_theme['secondary']}; font-weight:800;'>{v['value']:,.2f} ج.م</span></div>", unsafe_allow_html=True)
            with col_tree2:
                st.markdown("<p style='color:#38bdf8; font-weight:bold;'>⚔️ العصبات والأنصبة الباقية:</p>", unsafe_allow_html=True)
                for k, v in results.items():
                    if "عصبة" in v['fraction'] or "تعصيباً" in v['fraction']:
                        st.markdown(f"<div class='tree-card-asaba'><strong>{k}</strong>: {v['fraction']}<br><span style='color:#38bdf8; font-weight:800;'>{v['value']:,.2f} ج.م</span></div>", unsafe_allow_html=True)

            st.markdown("### 📊 جدول القسمة الشرعية وتوزيع الأنصبة (بالجنيه المصري):")
            table_md = "| الوارث | الفرض / الحالة الشرعية | النصيب المالي المستحق | تفصيل وسند التوزيع |\n| :--- | :--- | :--- | :--- |\n"
            text_summary = f"تقرير قسمة التركات والمواريث\nقيمة التركة الإجمالية: {estate_total:,.2f} ج.م\n\nتوزيع الأنصبة:\n"
            for k, v in results.items():
                table_md += f"| **{k}** | `{v['fraction']}` | **`{v['value']:,.2f} ج.م`** | {v['note']} |\n"
                text_summary += f"- {k}: {v['value']:,.2f} ج.م ({v['fraction']}) - {v['note']}\n"
            st.markdown(table_md)

            ai_slot = st.empty()
            if estate_clicked:
                estate_prompt = f"""
المتوفى: {deceased_gender}
قيمة التركة: {estate_total:,.2f} جنيه مصري
الورثة المستحقون:
- الزوج/الزوجة: {'نعم' if has_spouse else 'لا'}
- الأبناء الذكور: {sons_count}
- البنات: {daughters_count}
- الأب: {'نعم' if has_father else 'لا'}
- الأم: {'نعم' if has_mother else 'لا'}

قم بذكر الآيات القرآنية من سورة النساء الصريحة في قسمة هذه التركة، وبيان حالات الحجب بقواعد علم الفرائض باللغة العربية الفصحى فقط (ضع الآيات بين « ... »).
"""
                estate_sys = """أنت فقيه ومحقق في علم الفرائض. اذكر نصوص الآيات من سورة النساء التي استندت إليها هذه المسألة وبيان سبب حجب الحواشي بالعربية فقط."""
                res_fiqh = execute_gemini_prompt(estate_prompt, estate_sys, ai_slot)
                if res_fiqh:
                    estate_cache["ai_text"] = res_fiqh
            elif estate_cache["ai_text"]:
                ai_slot.markdown(f"<br>{format_quranic_text(estate_cache['ai_text'])}", unsafe_allow_html=True)

            # يُصدَّر التقرير دائماً (حتى لو تعذّر الذكاء الاصطناعي) ويُلحق به التأصيل إن وُجد
            st.session_state["estate_pdf_doc"] = text_summary
            if estate_cache["ai_text"]:
                st.session_state["estate_pdf_doc"] += f"\nالتأصيل الفقهي والقرآني:\n{estate_cache['ai_text']}"

        if st.session_state["estate_pdf_doc"]:
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                st.download_button(
                    label="📄 تصدير تقرير (PDF)",
                    data=create_printable_html("وثيقة توزيع المواريث والفرائض", st.session_state["estate_pdf_doc"]),
                    file_name="inheritance_document.html",
                    mime="text/html",
                    use_container_width=True
                )
            with col_exp2:
                if st.session_state["estate_csv_data"]:
                    st.download_button(
                        label="📊 تصدير جدول (Excel/CSV)",
                        data=st.session_state["estate_csv_data"],
                        file_name="inheritance_table.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

# ----------------- 5. شاشة السبحة الإلكترونية والأذكار -----------------
elif st.session_state["active_view"] == "tasbeeh":
    st.markdown("<div class='back-nav-btn'>", unsafe_allow_html=True)
    if st.button("⬅️ العودة للرئيسية", use_container_width=True):
        st.session_state["active_view"] = "home"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="royal-hero">
        <h1>📿 السبحة الإلكترونية ومكتبة الأذكار</h1>
        <p>عداد تسبيح تفاعلي • أذكار وأدعية مأثورة مع بيان فضلها وصحتها</p>
    </div>
    """, unsafe_allow_html=True)

    selected_dhikr_obj = st.selectbox("📿 اختر الذكر للتسبيح:", [d["title"] for d in ATHKAR_LIST])
    curr_d = next(item for item in ATHKAR_LIST if item["title"] == selected_dhikr_obj)

    st.markdown(f"""
    <div class="daily-card" style="text-align:center;">
        <h3 style="color:{current_theme['secondary']}; margin-bottom:0.6rem;">{curr_d['title']}</h3>
        <p style="font-family:'Amiri', serif; font-size:1.3rem; color:{current_theme['highlight']}; line-height:1.8;">« {curr_d['text']} »</p>
        <div style="color:#94a3b8; font-size:0.85rem; margin-top:0.6rem;">✨ <strong>فضل الذكر:</strong> {curr_d['virtue']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="tasbeeh-counter-box">
        <div style="color:#94a3b8; font-size:0.8rem;">عدد المرات</div>
        <div style="font-size:2.2rem; font-weight:900; color:{current_theme['secondary']};">{st.session_state['tasbeeh_count']}</div>
    </div>
    """, unsafe_allow_html=True)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("<div class='action-submit-btn'>", unsafe_allow_html=True)
        if st.button("➕ تسبيح (ضغطة)", use_container_width=True):
            st.session_state["tasbeeh_count"] += 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col_t2:
        if st.button("🔄 إعادة ضبط العداد", use_container_width=True):
            st.session_state["tasbeeh_count"] = 0
            st.rerun()

# ----------------- 6. شاشة المسابقات والتحدي اليومي والشهادات -----------------
elif st.session_state["active_view"] == "quiz":
    st.markdown("<div class='back-nav-btn'>", unsafe_allow_html=True)
    if st.button("⬅️ العودة للرئيسية", use_container_width=True):
        st.session_state["active_view"] = "home"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="royal-hero">
        <h1>🏆 بنك المسابقات والتحدي اليومي</h1>
        <p>تحديات يومية موحدة • مستويات تدريجية • استخراج شهادة إنجاز معتمدة</p>
    </div>
    """, unsafe_allow_html=True)

    tier_title, tier_color = get_user_mastery_tier(st.session_state["stats"]["quiz_correct_answered"], st.session_state["stats"]["quiz_total_answered"])
    st.markdown(f"""
    <div class="badge-tier-card">
        <div style="font-size:0.9rem; color:#94a3b8;">رتبتك العلمية الحالية:</div>
        <div style="font-size:1.35rem; font-weight:900; color:{tier_color}; margin-top:0.2rem;">{tier_title}</div>
    </div>
    """, unsafe_allow_html=True)

    if "مفتٍ" in tier_title or "باحث" in tier_title:
        with st.expander("🎓 استخراج إجازة واجتياز علمي (شهادة تقدير رسمية)", expanded=False):
            u_name = st.text_input("اكتب اسمك الكامل للشهادة:", value="طالب العلم الفاضل")
            cert_data = generate_certificate_html(
                u_name, tier_title,
                st.session_state["stats"]["quiz_correct_answered"],
                st.session_state["stats"]["quiz_total_answered"]
            )
            st.download_button(
                label="📜 تحميل وطباعة شهادة الإنجاز (PDF/HTML)",
                data=cert_data,
                file_name="fiqh_certificate.html",
                mime="text/html",
                use_container_width=True
            )

    with st.expander("⚡ التحدي الفقهي اليومي (3 أسئلة موحدة)", expanded=not st.session_state["daily_challenge_done"]):
        if not st.session_state["daily_challenge_done"]:
            st.markdown(f"<p style='color:{current_theme['secondary']}; font-weight:bold;'>أجب عن التحدي اليومي لاختبار يقظتك الفقهية:</p>", unsafe_allow_html=True)
            d_ans_count = 0
            for idx, q_item in enumerate(DAILY_CHALLENGE_BANK):
                st.markdown(f"**س{idx+1}: {q_item['question']}**")
                chosen_opt = st.radio(f"خيارات س{idx+1}:", q_item["options"], key=f"daily_q_{idx}", label_visibility="collapsed")
                if chosen_opt == q_item["correct"]:
                    d_ans_count += 1
            if st.button("تأكيد نتيجة التحدي اليومي", use_container_width=True):
                st.session_state["daily_challenge_done"] = True
                st.session_state["daily_challenge_score"] = d_ans_count
                st.session_state["stats"]["quiz_total_answered"] += 3
                st.session_state["stats"]["quiz_correct_answered"] += d_ans_count
                st.rerun()
        else:
            st.success(f"🎉 أحسنت! أنجزت تحدي اليوم وحققت **{st.session_state['daily_challenge_score']} من 3** درجات.")

    st.markdown("---")
    selected_level = st.selectbox(
        "🎯 حدد مستوى التحدي الشامل:",
        list(st.session_state["quiz_pool"].keys()),
        index=list(st.session_state["quiz_pool"].keys()).index(st.session_state["quiz_level"])
    )
    if selected_level != st.session_state["quiz_level"]:
        st.session_state["quiz_level"] = selected_level
        prepare_new_round(selected_level)
        st.rerun()

    st.markdown("<div class='action-submit-btn'>", unsafe_allow_html=True)
    if st.button("⚡ توليد أسئلة جديدة بالذكاء الاصطناعي", use_container_width=True):
        with st.spinner("جاري استحضار أسئلة فقهية جديدة..."):
            new_q = generate_dynamic_quiz_questions(st.session_state["quiz_level"])
            if new_q and len(new_q) > 0:
                existing_q = {q["question"] for q in st.session_state["quiz_pool"][st.session_state["quiz_level"]]}
                new_q = [q for q in new_q if q["question"] not in existing_q]
            if new_q and len(new_q) > 0:
                st.session_state["quiz_pool"][st.session_state["quiz_level"]].extend(new_q)
                prepare_new_round(st.session_state["quiz_level"])
                st.success(f"🎉 تم توليد وإضافة {len(new_q)} أسئلة فقهية جديدة بنجاح!")
                st.rerun()
            else:
                prepare_new_round(st.session_state["quiz_level"])
                st.info("🔄 تم تجديد الأسئلة وبدء جولة غير مكررة من بنك الأسئلة!")
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    questions = st.session_state["current_round_questions"]
    current_idx = st.session_state["quiz_idx"]
    total_q = len(questions)

    if total_q == 0:
        st.info("لا توجد أسئلة حالياً. اضغط على زر التوليد لجلب أسئلة جديدة.")
    elif current_idx < total_q:
        q_data = questions[current_idx]
        if not st.session_state["shuffled_options"]:
            opts = list(q_data["options"])
            random.shuffle(opts)
            st.session_state["shuffled_options"] = opts
        
        progress_val = current_idx / total_q
        st.progress(progress_val)
        st.write(f"📌 **السؤال {current_idx + 1} من {total_q}** | ⭐ **النقاط: {st.session_state['quiz_score']}/{total_q}**")

        st.markdown(f"""
        <div class="quiz-card">
            <h3 style="color:#ffffff; line-height:1.6; font-size:1.15rem;">{q_data['question']}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        chosen_answer = st.radio(
            "اختر الإجابة الصحيحة:",
            st.session_state["shuffled_options"],
            index=None,
            key=f"radio_{st.session_state['quiz_level']}_{st.session_state['quiz_round_id']}_{current_idx}"
        )
        
        col_qbtn1, col_qbtn2 = st.columns(2)
        with col_qbtn1:
            st.markdown("<div class='action-submit-btn'>", unsafe_allow_html=True)
            check_btn = st.button("✅ تأكيد الإجابة", use_container_width=True, disabled=st.session_state["quiz_answered"])
            st.markdown("</div>", unsafe_allow_html=True)
        with col_qbtn2:
            next_btn = st.button("➡️ السؤال التالي", use_container_width=True, disabled=not st.session_state["quiz_answered"])
            
        if check_btn:
            if chosen_answer is None:
                st.warning("⚠️ يرجى اختيار إحدى الإجابات أولاً.")
            else:
                st.session_state["quiz_answered"] = True
                st.session_state["stats"]["quiz_total_answered"] += 1
                if chosen_answer == q_data["correct"]:
                    st.session_state["quiz_score"] += 1
                    st.session_state["stats"]["quiz_correct_answered"] += 1
                    st.session_state["quiz_feedback"] = {"status": "success", "msg": f"🎉 **إجابة صحيحة وموفقة!**\n\n📖 **الدليل والتحقيق:** {format_quranic_text(q_data['proof'])}"}
                else:
                    st.session_state["quiz_feedback"] = {"status": "error", "msg": f"❌ **إجابة غير صحيحة.**\n\n📌 **الصواب هو:** {q_data['correct']}\n\n📖 **الدليل:** {format_quranic_text(q_data['proof'])}"}
                st.rerun()
                
        if st.session_state["quiz_feedback"]:
            if st.session_state["quiz_feedback"]["status"] == "success":
                st.success(st.session_state["quiz_feedback"]["msg"])
            else:
                st.error(st.session_state["quiz_feedback"]["msg"])
                
        if next_btn:
            st.session_state["quiz_idx"] += 1
            st.session_state["quiz_answered"] = False
            st.session_state["quiz_feedback"] = None
            st.session_state["shuffled_options"] = []
            st.rerun()
    else:
        if not st.session_state["quiz_balloons_shown"]:
            st.balloons()  # مرة واحدة لكل جولة بدل تكرارها مع كل تفاعل
            st.session_state["quiz_balloons_shown"] = True
        st.markdown(f"""
        <div class="quiz-card" style="text-align:center;">
            <h2 style="color:{current_theme['secondary']}; font-size:1.4rem;">🎉 بارك الله فيك! أكملت هذه الجولة</h2>
            <p style="font-size:1.15rem; color:#ffffff; margin: 0.8rem 0;">النتيجة النهائية: <strong>{st.session_state['quiz_score']} من {total_q}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        col_end1, col_end2 = st.columns(2)
        with col_end1:
            if st.button("🚀 جولة جديدة بأسئلة غير مكررة", use_container_width=True):
                prepare_new_round(st.session_state["quiz_level"])
                st.rerun()
        with col_end2:
            st.markdown("<div class='action-submit-btn'>", unsafe_allow_html=True)
            if st.button("⚡ توليد أسئلة بالذكاء الاصطناعي", use_container_width=True):
                with st.spinner("جاري استحضار تحديات فقهية جديدة..."):
                    new_q = generate_dynamic_quiz_questions(st.session_state["quiz_level"])
                    if new_q and len(new_q) > 0:
                        existing_q = {q["question"] for q in st.session_state["quiz_pool"][st.session_state["quiz_level"]]}
                        st.session_state["quiz_pool"][st.session_state["quiz_level"]].extend(
                            [q for q in new_q if q["question"] not in existing_q]
                        )
                    prepare_new_round(st.session_state["quiz_level"])
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ----------------- 7. شاشة المفضلة والنسخ الاحتياطي (JSON Backup) -----------------
elif st.session_state["active_view"] == "bookmarks":
    st.markdown("<div class='back-nav-btn'>", unsafe_allow_html=True)
    if st.button("⬅️ العودة للرئيسية", use_container_width=True):
        st.session_state["active_view"] = "home"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="royal-hero">
        <h1>⭐ الفتاوى المحفوظة والنسخ الاحتياطي</h1>
        <p>سجل الفتاوى • النسخ الاحتياطي والمزامنة عبر JSON • إحصائيات التفاعل</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔄 النسخ الاحتياطي ونقل البيانات (JSON Sync)", expanded=False):
        st.markdown("<p style='color:#94a3b8; font-size:0.9rem;'>يمكنك تحميل نسخة احتياطية من كل فتاواك المحفوظة وإحصائياتك ونقلها لأي جهاز آخر بسهولة:</p>", unsafe_allow_html=True)
        backup_dict = {
            "bookmarks": st.session_state["bookmarks"],
            "stats": st.session_state["stats"],
            "export_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        json_backup_str = json.dumps(backup_dict, ensure_ascii=False, indent=2)
        
        col_sync1, col_sync2 = st.columns(2)
        with col_sync1:
            st.download_button(
                label="📥 تصدير نسخة احتياطية (JSON)",
                data=json_backup_str,
                file_name="fiqh_encyclopedia_backup.json",
                mime="application/json",
                use_container_width=True
            )
        with col_sync2:
            uploaded_file = st.file_uploader("استيراد نسخة احتياطية:", type=["json"], label_visibility="collapsed")
            if uploaded_file is not None:
                # كان الاستيراد يتكرر مع كل إعادة تشغيل (st.rerun + sleep) فيدخل الصفحة في حلقة لا تنتهي؛
                # الآن يُنفَّذ مرة واحدة فقط لكل ملف.
                file_signature = (uploaded_file.name, uploaded_file.size)
                last_import = st.session_state["last_imported_backup"]
                if last_import is None or last_import[0] != file_signature:
                    try:
                        imported_data = json.load(uploaded_file)
                        if not isinstance(imported_data, dict):
                            raise ValueError("invalid backup structure")
                        if isinstance(imported_data.get("bookmarks"), list):
                            clean_bookmarks = []
                            for b in imported_data["bookmarks"]:
                                if isinstance(b, dict) and b.get("question") and b.get("answer"):
                                    clean_bookmarks.append({
                                        "question": str(b["question"]),
                                        "answer": str(b["answer"]),
                                        "tag": str(b.get("tag", "#فقه_عام")),
                                        "date": str(b.get("date", "")),
                                    })
                            st.session_state["bookmarks"] = clean_bookmarks
                        if isinstance(imported_data.get("stats"), dict):
                            # دمج مع القيم الافتراضية حتى لا تنهار الصفحة إذا نقص مفتاح في الملف
                            for stat_key in st.session_state["stats"]:
                                value = imported_data["stats"].get(stat_key)
                                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                                    st.session_state["stats"][stat_key] = value
                        st.session_state["last_imported_backup"] = (file_signature, True)
                        import_succeeded = True
                    except Exception:
                        st.session_state["last_imported_backup"] = (file_signature, False)
                        import_succeeded = False
                    if import_succeeded:
                        st.rerun()
                    else:
                        st.error("⚠️ ملف النسخة الاحتياطية غير صالح.")
                elif last_import[1]:
                    st.success("✅ تم استيراد البيانات والمفضلة بنجاح!")
                else:
                    st.error("⚠️ ملف النسخة الاحتياطية غير صالح.")

    st.markdown("---")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{st.session_state['stats']['fiqh_queries']}</div>
            <div class="stat-title">استشارات فقهية مستخرجة</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{st.session_state['stats']['quran_queries']}</div>
            <div class="stat-title">بحوث قرآنية موضوعية</div>
        </div>
        """, unsafe_allow_html=True)
    with col_s2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{st.session_state['stats']['hadith_queries']}</div>
            <div class="stat-title">أحاديث محققة ومخرجة</div>
        </div>
        """, unsafe_allow_html=True)
        total_ans = st.session_state['stats']['quiz_total_answered']
        corr_ans = st.session_state['stats']['quiz_correct_answered']
        acc = int((corr_ans / total_ans * 100)) if total_ans > 0 else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{acc}%</div>
            <div class="stat-title">دقة إجابات المسابقات</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📌 الفتاوى المحفوظة في المفضلة:")
    if not st.session_state["bookmarks"]:
        st.info("ℹ️ لم تقم بحفظ أي فتاوى في المفضلة بعد. يمكنك حفظ أي فتوى من قسم الفقه.")
    else:
        tags_list = ["الكل"] + sorted(set(b["tag"] for b in st.session_state["bookmarks"]))
        selected_filter_tag = st.selectbox("🔍 تصفية حسب الوسم:", tags_list)
        filtered_bmarks = st.session_state["bookmarks"] if selected_filter_tag == "الكل" else [b for b in st.session_state["bookmarks"] if b["tag"] == selected_filter_tag]
        
        for idx, bmark in enumerate(filtered_bmarks):
            with st.expander(f"📌 {bmark['question']} ({bmark['tag']}) - {bmark['date']}"):
                st.markdown(f"<span style='background:{current_theme['badge_bg']}; color:{current_theme['secondary']}; border:1px solid {current_theme['primary']}; border-radius:8px; padding:2px 8px; font-weight:bold;'>{bmark['tag']}</span>", unsafe_allow_html=True)
                st.markdown(format_quranic_text(bmark["answer"]), unsafe_allow_html=True)
                st.download_button(
                    label="📄 تحميل هذه الفتوى (PDF)",
                    data=create_printable_html(bmark['question'], bmark['answer']),
                    file_name=f"fatwa_{idx}.html",
                    mime="text/html",
                    key=f"dl_bmark_{idx}"
                )

# 9. التذييل مع روابط التواصل الاجتماعي
st.markdown(f"""
<div class="royal-footer">
    <div style="color: #9ca3af; margin-bottom: 0.6rem;">نظام فقهي استدلالي وتوثيقي مقارن مبني بنماذج الذكاء الاصطناعي المتقدمة</div>
    <div style="margin-bottom: 0.9rem;">
        Developed by <span class="dev-badge">Eng. Abdelfttah Ragheb</span> © 2026
    </div>
    <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 6px;">
        <a href="https://instagram.com/3bdo_ragheb_?igshid=ZDdkNTZiNTM%3D" target="_blank" class="social-link-btn">
            📸 Instagram
        </a>
        <a href="https://www.facebook.com/share/1DP6ShDfxz/" target="_blank" class="social-link-btn">
            🌐 Facebook
        </a>
        <a href="https://wa.me/201153735189" target="_blank" class="social-link-btn">
            💬 WhatsApp
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.caption("⚠️ المحتوى مُولَّد بالذكاء الاصطناعي للاسترشاد وليس فتوى رسمية؛ يُرجع في المسائل المهمة إلى أهل العلم ودور الإفتاء المعتمدة.")