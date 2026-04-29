import streamlit as st
import base64
import os
from .config import IMG_DIR

THEMES = {
    "Clair Modern ❄️": {"bg": "#F8FAFC", "sidebar_bg": "#FFFFFF", "text": "#1E293B", "primary": "#3B82F6", "accent": "#60A5FA", "card_bg": "rgba(255,255,255,0.8)", "input_bg": "#F1F5F9", "input_text": "#1E293B"},
    "Sombre Élite 🌙": {"bg": "#0F172A", "sidebar_bg": "#1E293B", "text": "#F8FAFC", "primary": "#38BDF8", "accent": "#7DD3FC", "card_bg": "rgba(30,41,59,0.7)", "input_bg": "#334155", "input_text": "#F8FAFC"},
    "Émeraude Royal 👑": {"bg": "#064E3B", "sidebar_bg": "#065F46", "text": "#ECFDF5", "primary": "#10B981", "accent": "#34D399", "card_bg": "rgba(6,78,59,0.7)", "input_bg": "#065F46", "input_text": "#ECFDF5"},
    "Aurore Boréale 🌌": {"bg": "#1E1B4B", "sidebar_bg": "#312E81", "text": "#EEF2FF", "primary": "#818CF8", "accent": "#A5B4FC", "card_bg": "rgba(49,46,129,0.7)", "input_bg": "#312E81", "input_text": "#EEF2FF"},
    "Cyberpunk ⚡": {"bg": "#000000", "sidebar_bg": "#1A1A1A", "text": "#00FF41", "primary": "#00FF41", "accent": "#008F11", "card_bg": "rgba(20,20,20,0.8)", "input_bg": "#1A1A1A", "input_text": "#00FF41"}
}

def get_image_base64(image_path):
    if not image_path: return None
    full_path = os.path.join(IMG_DIR, image_path)
    if os.path.exists(full_path):
        with open(full_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{data}"
    return None

def apply_custom_theme(theme_name):
    t = THEMES.get(theme_name, THEMES["Émeraude Royal 👑"])
    st.markdown(f"""
    <style>
        .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
        .marquee {{ background: {t['primary']}; color: {t['sidebar_bg']}; padding: 10px; font-weight: bold; }}
        [data-testid="stSidebar"] {{ background-color: {t['sidebar_bg']} !important; }}
        /* Glassmorphism */
        .stContainer, div[data-testid="stExpander"] {{
            border-radius: 15px !important;
            background: {t['card_bg']} !important;
            backdrop-filter: blur(12px);
            padding: 1rem;
        }}
        /* Buttons */
        .stButton > button {{
            background-color: {t['primary']} !important;
            color: {t['sidebar_bg']} !important;
            border-radius: 10px !important;
        }}
    </style>
    """, unsafe_allow_html=True)
