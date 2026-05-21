import streamlit as st
import pandas as pd
import os
import re
import base64
import shutil
import urllib.parse
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io
import google.generativeai as genai
import requests
import json
from PIL import Image as PILImage, ImageOps
from streamlit_extras.colored_header import colored_header
from streamlit_extras.mention import mention
from streamlit_extras.add_vertical_space import add_vertical_space
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURATION & CHEMINS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, 'images_stock')
DB_PATH = os.path.join(BASE_DIR, 'database_para.csv')
USER_DB = os.path.join(BASE_DIR, 'users.csv')
SALES_DB = os.path.join(BASE_DIR, 'ventes.csv')
LOGS_FILE = os.path.join(BASE_DIR, 'activity_logs.csv')
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')
SESSION_FILE = os.path.join(BASE_DIR, 'session.json')

if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {"marquee": "🚀 BIENVENUE SUR PHARMACIEL PRO - LES MEILLEURES OFFRES SONT ICI ! ✨ LIVRAISON RAPIDE DISPONIBLE ✨"}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def sync_data_permanent(msg="Mise à jour automatique"):
    """Envoie les données et images vers Google Drive pour la persistance."""
    try:
        from utils.gdrive_api import sync_to_gdrive
        success, res = sync_to_gdrive(msg)
        return success, res
    except Exception as e:
        return False, str(e)

def restore_data_permanent():
    """Récupère les données depuis Google Drive."""
    try:
        from utils.gdrive_api import restore_from_gdrive
        success, res = restore_from_gdrive()
        return success, res
    except Exception as e:
        return False, str(e)

def add_log(action, details=""):
    user = st.session_state.get('current_user', 'Système')
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame([{"Date": now, "Utilisateur": user, "Action": action, "Détails": details}])
    if os.path.exists(LOGS_FILE):
        new_log.to_csv(LOGS_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        new_log.to_csv(LOGS_FILE, index=False, encoding='utf-8-sig')

# --- 2. CONFIGURATION DE PAGE ---
st.set_page_config(page_title="Pharmaciel Pro", layout="wide", page_icon="💊")

# --- 3. FONCTIONS UTILISATEURS ---
def load_users():
    cols = ['user', 'pw', 'role', 'whatsapp', 'display_name']
    if not os.path.exists(USER_DB):
        df_init = pd.DataFrame([{"user": "admin", "pw": "1992", "role": "Responsable", "whatsapp": "213550000000", "display_name": "Admin Principal"}])
        df_init.to_csv(USER_DB, index=False)
        return df_init
    try:
        df = pd.read_csv(USER_DB, dtype=str)
        for c in cols:
            if c not in df.columns:
                if c == 'display_name': df[c] = "Agent Commercial"
                else: df[c] = ""
        return df
    except:
        return pd.DataFrame([{"user": "admin", "pw": "1992", "role": "Responsable", "whatsapp": "", "display_name": "Admin"}])

# --- 4. DESIGN SYSTEM DYNAMIQUE (THEMES) ---
def apply_custom_theme(theme_choice):
    themes = {
        "Clair Modern ❄️": {
            "bg": "linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)",
            "card_bg": "rgba(255, 255, 255, 0.85)",
            "text": "#0f172a",
            "sidebar_bg": "#ffffff",
            "primary": "#0284c7",
            "primary_grad": "linear-gradient(90deg, #0284c7, #3b82f6)",
            "accent": "#0369a1",
            "sidebar_text": "#0f172a",
            "input_bg": "#ffffff",
            "input_text": "#0f172a",
            "border": "rgba(15, 23, 42, 0.08)",
            "glow": "rgba(2, 132, 199, 0.15)",
            "shadow": "0 10px 30px rgba(15, 23, 42, 0.05)"
        },
        "Sombre Élite 🌙": {
            "bg": "linear-gradient(135deg, #0b0f19 0%, #111827 50%, #030712 100%)",
            "card_bg": "rgba(22, 28, 45, 0.65)",
            "text": "#f3f4f6",
            "sidebar_bg": "#090d16",
            "primary": "#d97706",
            "primary_grad": "linear-gradient(90deg, #d97706, #f59e0b)",
            "accent": "#b45309",
            "sidebar_text": "#f3f4f6",
            "input_bg": "#1f2937",
            "input_text": "#f3f4f6",
            "border": "rgba(255, 255, 255, 0.07)",
            "glow": "rgba(245, 158, 11, 0.2)",
            "shadow": "0 10px 35px rgba(0, 0, 0, 0.3)"
        },
        "Émeraude Royal 👑": {
            "bg": "linear-gradient(135deg, #021e17 0%, #053327 50%, #010c08 100%)",
            "card_bg": "rgba(8, 48, 39, 0.7)",
            "text": "#ecfdf5",
            "sidebar_bg": "#01140f",
            "primary": "#10b981",
            "primary_grad": "linear-gradient(90deg, #059669, #10b981)",
            "accent": "#047857",
            "sidebar_text": "#ecfdf5",
            "input_bg": "#03271f",
            "input_text": "#ecfdf5",
            "border": "rgba(16, 185, 129, 0.12)",
            "glow": "rgba(16, 185, 129, 0.25)",
            "shadow": "0 10px 35px rgba(0, 0, 0, 0.3)"
        },
        "Aurore Boréale 🌌": {
            "bg": "linear-gradient(135deg, #0d0a1b 0%, #171032 50%, #06040d 100%)",
            "card_bg": "rgba(29, 21, 56, 0.65)",
            "text": "#fdf4ff",
            "sidebar_bg": "#0a0715",
            "primary": "#c084fc",
            "primary_grad": "linear-gradient(90deg, #a855f7, #c084fc)",
            "accent": "#9333ea",
            "sidebar_text": "#fdf4ff",
            "input_bg": "rgba(29, 21, 56, 0.4)",
            "input_text": "#fdf4ff",
            "border": "rgba(192, 132, 252, 0.15)",
            "glow": "rgba(192, 132, 252, 0.3)",
            "shadow": "0 10px 35px rgba(0, 0, 0, 0.35)"
        },
        "Cyberpunk ⚡": {
            "bg": "linear-gradient(135deg, #000000 0%, #0c0a0f 100%)",
            "card_bg": "rgba(15, 12, 20, 0.85)",
            "text": "#00ff9f",
            "sidebar_bg": "#000000",
            "primary": "#ff0055",
            "primary_grad": "linear-gradient(90deg, #ff0055, #ff0077)",
            "accent": "#ff0055",
            "sidebar_text": "#00ff9f",
            "input_bg": "#100d14",
            "input_text": "#00ff9f",
            "border": "rgba(0, 255, 159, 0.25)",
            "glow": "rgba(255, 0, 85, 0.45)",
            "shadow": "0 0 25px rgba(0, 255, 159, 0.05)"
        },
        "Antigravity Dark 🌌": {
            "bg": "radial-gradient(circle at 50% 0%, rgba(14, 165, 233, 0.12) 0%, transparent 60%), linear-gradient(135deg, #020617 0%, #0b0f19 100%)",
            "card_bg": "rgba(17, 24, 39, 0.6)",
            "text": "#f8fafc",
            "sidebar_bg": "#030712",
            "primary": "#38bdf8",
            "primary_grad": "linear-gradient(90deg, #0ea5e9, #38bdf8)",
            "accent": "#0284c7",
            "sidebar_text": "#38bdf8",
            "input_bg": "#1e293b",
            "input_text": "#f8fafc",
            "border": "rgba(56, 189, 248, 0.15)",
            "glow": "rgba(56, 189, 248, 0.3)",
            "shadow": "0 10px 35px rgba(0, 0, 0, 0.3)"
        },
        "Pharmaciel Premium 🧪": {
            "bg": "linear-gradient(135deg, #f0fdfa 0%, #e0f2f1 50%, #ffffff 100%)",
            "card_bg": "rgba(255, 255, 255, 0.9)",
            "text": "#0f3c36",
            "sidebar_bg": "#0a443b",
            "primary": "#0d9488",
            "primary_grad": "linear-gradient(90deg, #0d9488, #14b8a6)",
            "accent": "#0f766e",
            "sidebar_text": "#e0f2f1",
            "input_bg": "#ffffff",
            "input_text": "#0f3c36",
            "border": "rgba(13, 148, 136, 0.12)",
            "glow": "rgba(13, 148, 136, 0.2)",
            "shadow": "0 10px 30px rgba(13, 148, 136, 0.05)"
        }
    }
    
    t = themes.get(theme_choice, themes["Clair Modern ❄️"])
    
    # CSS variables definition
    css_vars = f"""
    :root {{
        --bg-val: {t['bg']};
        --card-bg: {t['card_bg']};
        --text-color: {t['text']};
        --sidebar-bg: {t['sidebar_bg']};
        --sidebar-text: {t['sidebar_text']};
        --primary-color: {t['primary']};
        --primary-gradient: {t['primary_grad']};
        --accent-color: {t['accent']};
        --input-bg: {t['input_bg']};
        --input-text: {t['input_text']};
        --border-color: {t['border']};
        --glow-color: {t['glow']};
        --shadow-val: {t['shadow']};
    }}
    """
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=Orbitron:wght@400;700&display=swap');
        
        {css_vars}
        
        /* Global Base Override */
        html, body, [class*="css"] {{
            font-family: 'Plus Jakarta Sans', sans-serif;
        }}
        
        {".stApp { font-family: 'Orbitron', 'Segoe UI Emoji', sans-serif !important; }" if theme_choice == "Cyberpunk ⚡" else ""}
        
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background: var(--bg-val) !important;
            background-attachment: fixed !important;
            color: var(--text-color) !important;
            transition: all 0.4s ease;
        }}
        
        /* Clean up header and footers */
        [data-testid="stHeader"] {{
            background: transparent !important;
            backdrop-filter: none !important;
        }}
        footer {{
            visibility: hidden !important;
            display: none !important;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700 !important;
            letter-spacing: -0.03em !important;
            color: var(--text-color) !important;
        }}
        
        h1 {{
            font-size: 2.2rem !important;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.8rem !important;
        }}
        
        label, .stMarkdown p, .stText, .stCaption, [data-testid="stWidgetLabel"] p {{
            color: var(--text-color) !important;
            opacity: 1 !important;
        }}
        
        /* Sidebar Relooking */
        [data-testid="stSidebar"] {{
            background-color: var(--sidebar-bg) !important;
            border-right: 1px solid var(--border-color) !important;
            box-shadow: 10px 0 30px rgba(0, 0, 0, 0.15);
        }}
        
        [data-testid="stSidebar"] h2, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{
            color: var(--sidebar-text) !important;
        }}
        
        /* Horizontal Navigation Buttons / Sidebar items */
        div[data-testid="stSidebar"] div[data-testid="stRadio"] label p {{
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.2px;
            padding: 8px 12px;
            border-radius: 8px;
            transition: all 0.3s ease;
        }}
        
        div[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover p {{
            background: rgba(255, 255, 255, 0.05);
            color: var(--primary-color) !important;
            transform: translateX(4px);
        }}
        
        /* Modern Glass Ticker (Marquee) */
        .marquee {{
            width: 100%;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid var(--border-color) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            color: var(--text-color) !important;
            padding: 10px 0;
            font-weight: 600;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: var(--shadow-val);
            position: relative;
        }}
        
        .marquee::before {{
            content: '';
            position: absolute;
            bottom: 0; left: 0; right: 0;
            height: 2px;
            background: var(--primary-gradient);
            box-shadow: 0 0 10px var(--glow-color);
        }}
        
        .marquee div {{
            display: inline-block;
            white-space: nowrap;
            animation: marquee 25s linear infinite;
        }}
        
        @keyframes marquee {{
            0% {{ transform: translateX(100%); }}
            100% {{ transform: translateX(-100%); }}
        }}
        
        /* Expander & Expandable Cards */
        div[data-testid="stExpander"] {{
            border-radius: 16px !important;
            border: 1px solid var(--border-color) !important;
            background: var(--card-bg) !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            box-shadow: var(--shadow-val) !important;
            margin-bottom: 1.2rem !important;
            transition: all 0.3s ease;
        }}
        
        div[data-testid="stExpander"]:hover {{
            border-color: var(--primary-color) !important;
        }}
        
        /* Glassmorphic Container for Products (Streamlit 1.30+) */
        div[data-testid="stContainerBorder"] {{
            border-radius: 20px !important;
            border: 1px solid var(--border-color) !important;
            background: var(--card-bg) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            box-shadow: var(--shadow-val) !important;
            padding: 20px !important;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
            overflow: visible !important;
        }}
        
        div[data-testid="stContainerBorder"]:hover {{
            transform: translateY(-6px) !important;
            border-color: var(--primary-color) !important;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3), 0 0 20px var(--glow-color) !important;
        }}
        
        /* Tabs Styling */
        div[data-testid="stTabBar"] {{
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 12px;
            padding: 6px !important;
            gap: 8px !important;
            margin-bottom: 20px !important;
        }}
        
        button[data-testid="stTab"] {{
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            color: var(--text-color) !important;
            opacity: 0.7;
            padding: 8px 16px !important;
            border: none !important;
            background: transparent !important;
            transition: all 0.3s ease !important;
        }}
        
        button[data-testid="stTab"][aria-selected="true"] {{
            opacity: 1 !important;
            background: var(--primary-gradient) !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px var(--glow-color) !important;
        }}
        
        /* Modern Inputs Override */
        div[data-baseweb="select"], div[data-baseweb="input"], div[data-baseweb="textarea"] {{
            background-color: var(--input-bg) !important;
            border-radius: 12px !important;
            border: 1px solid var(--border-color) !important;
            transition: all 0.3s ease !important;
        }}
        
        div[data-baseweb="select"]:focus-within, div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within {{
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 10px var(--glow-color) !important;
        }}
        
        div[data-baseweb="select"] *, div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {{
            color: var(--input-text) !important;
        }}
        
        input::placeholder, textarea::placeholder {{
            color: var(--input-text) !important;
            opacity: 0.5 !important;
        }}
        
        /* Buttons Redesign */
        .stButton > button {{
            border-radius: 12px !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            letter-spacing: 0.5px;
            background: var(--primary-gradient) !important;
            color: #ffffff !important;
            border: none !important;
            padding: 0.7rem 1.4rem !important;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15) !important;
            text-transform: uppercase;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px var(--glow-color) !important;
            opacity: 0.95;
        }}
        
        .stButton > button:active {{
            transform: translateY(1px) !important;
        }}
        
        /* Secondary / Details buttons mapping */
        .stButton > button[data-testid="baseButton-secondary"] {{
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid var(--border-color) !important;
            color: var(--text-color) !important;
            box-shadow: none !important;
        }}
        
        .stButton > button[data-testid="baseButton-secondary"]:hover {{
            background: var(--primary-gradient) !important;
            color: #ffffff !important;
            border-color: transparent !important;
            box-shadow: 0 8px 20px var(--glow-color) !important;
        }}
        
        /* Red PDF Action Buttons override */
        div.stDownloadButton > button {{
            background: linear-gradient(90deg, #ef4444, #dc2626) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.25) !important;
        }}
        
        div.stDownloadButton > button:hover {{
            box-shadow: 0 8px 20px rgba(239, 68, 68, 0.4) !important;
        }}
        
        /* Metrics Styling */
        div[data-testid="stMetric"] {{
            border: 1px solid var(--border-color) !important;
            border-radius: 16px !important;
            background: rgba(255, 255, 255, 0.02) !important;
            backdrop-filter: blur(8px) !important;
            -webkit-backdrop-filter: blur(8px) !important;
            padding: 16px !important;
            box-shadow: var(--shadow-val) !important;
        }}
        
        [data-testid="stMetricValue"] {{
            color: var(--primary-color) !important;
            font-weight: 700;
            font-size: 2.1rem !important;
            text-shadow: 0 0 10px var(--glow-color);
        }}
        
        [data-testid="stMetricLabel"] {{
            font-weight: 600 !important;
            opacity: 0.7 !important;
        }}
        
        /* Card Image Styling */
        [data-testid="column"] img {{
            height: 200px !important;
            width: 100% !important;
            object-fit: contain !important;
            background-color: #ffffff !important;
            border-radius: 12px !important;
            padding: 8px !important;
            border: 1px solid rgba(255,255,255,0.05) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
            transition: all 0.3s ease !important;
        }}
        
        [data-testid="column"] img:hover {{
            transform: scale(1.04);
        }}
        
        /* Product visual structure */
        .product-card-body {{
            display: flex;
            flex-direction: column;
            padding: 8px 0;
            flex-grow: 1;
        }}
        .product-labo {{
            font-size: 0.78rem;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 1px;
            opacity: 0.5;
            margin-bottom: 4px;
        }}
        .product-title {{
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.3;
            margin-bottom: 8px;
            height: 2.6rem;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }}
        .product-price {{
            font-size: 1.45rem;
            font-weight: 800;
            color: var(--primary-color);
            margin-top: auto;
            margin-bottom: 12px;
            display: flex;
            align-items: baseline;
        }}
        .currency {{
            font-size: 0.8rem;
            font-weight: 600;
            opacity: 0.7;
            margin-left: 3px;
        }}
        
        .card-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin-bottom: 10px;
            height: 22px;
        }}
        .card-badges-empty {{
            height: 22px;
            margin-bottom: 10px;
        }}
        
        /* Dialog Custom Specs Card */
        .detail-item {{
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 10px 14px;
            display: flex;
            flex-direction: column;
        }}
        .detail-icon {{
            font-size: 1.2rem;
            margin-bottom: 4px;
        }}
        .detail-label {{
            font-size: 0.75rem;
            opacity: 0.5;
            text-transform: uppercase;
            font-weight: 600;
        }}
        .detail-value {{
            font-size: 0.95rem;
            font-weight: 700;
        }}
        
        .internal-stats-card {{
            background: rgba(217, 119, 6, 0.05);
            border: 1px solid rgba(217, 119, 6, 0.2);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 15px;
        }}
        .stats-card-title {{
            font-size: 0.85rem;
            text-transform: uppercase;
            font-weight: 700;
            color: #f59e0b;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
        }}
        .admin-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }}
        .admin-stat-item {{
            display: flex;
            flex-direction: column;
        }}
        .admin-stat-label {{
            font-size: 0.75rem;
            opacity: 0.6;
        }}
        .admin-stat-val {{
            font-size: 1.05rem;
            font-weight: 700;
        }}
        
        /* Login screen premium additions */
        .login-container {{
            background: var(--card-bg) !important;
            border: 1px solid var(--border-color) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border-radius: 24px !important;
            padding: 40px !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3) !important;
            text-align: center;
        }}
        .login-header {{
            margin-bottom: 30px;
        }}
        .login-title {{
            font-size: 2.4rem !important;
            margin-bottom: 8px !important;
        }}
        .login-subtitle {{
            font-size: 0.95rem;
            opacity: 0.6;
            line-height: 1.4;
        }}
        .client-portal-card {{
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 16px !important;
            padding: 24px !important;
            text-align: left;
            margin-bottom: 20px;
        }}
        .portal-info h3 {{
            margin-bottom: 6px !important;
            font-size: 1.2rem !important;
        }}
        .portal-info p {{
            font-size: 0.85rem;
            opacity: 0.7;
            margin-bottom: 16px;
        }}
        
        /* Placeholder for No Image products */
        .no-image-placeholder {{
            height: 200px;
            border-radius: 12px;
            background: linear-gradient(135deg, rgba(255,255,255,0.01) 0%, rgba(255,255,255,0.05) 100%);
            border: 1px dashed var(--border-color);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            margin-bottom: 12px;
            text-align: center;
        }}
        .placeholder-icon {{
            font-size: 2.2rem;
            margin-bottom: 6px;
            filter: drop-shadow(0 0 8px var(--glow-color));
        }}
        .placeholder-text {{
            font-size: 0.75rem;
            opacity: 0.4;
            font-weight: 600;
        }}
        
        /* WhatsApp Floating Button */
        .whatsapp-float {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: linear-gradient(135deg, #25d366 0%, #128c7e 100%);
            color: white !important;
            border-radius: 50px;
            text-align: center;
            width: 56px;
            height: 56px;
            box-shadow: 0px 8px 24px rgba(18, 140, 126, 0.4);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }}
        .whatsapp-float:hover {{
            transform: scale(1.1) translateY(-2px);
            box-shadow: 0px 12px 30px rgba(18, 140, 126, 0.6);
            color: white !important;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Bouton WhatsApp Dynamique (Premier numéro trouvé)
    u_db = load_users()
    agents = u_db[u_db['whatsapp'].str.len() > 5]
    primary_wa = agents.iloc[0]['whatsapp'] if not agents.empty else "213550000000"
    
    st.markdown(f"""
    <a href="https://wa.me/{primary_wa}" class="whatsapp-float" target="_blank">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M12.031 0C5.385 0 0 5.386 0 12.03c0 2.12.551 4.198 1.597 6.02L.031 24l6.105-1.603a11.972 11.972 0 0 0 5.895 1.543h.005c6.645 0 12.03-5.387 12.03-12.032C24.066 5.386 18.679 0 12.031 0zm0 21.968h-.005a9.963 9.963 0 0 1-5.075-1.378l-.364-.216-3.771.99.998-3.676-.237-.377a9.96 9.96 0 0 1-1.526-5.283c0-5.5 4.476-9.975 9.98-9.975 5.503 0 9.978 4.475 9.978 9.975s-4.475 9.975-9.978 9.975zm5.474-7.48c-.3-.15-1.776-.876-2.052-.976-.275-.101-.476-.15-.676.15-.2.302-.776.977-.951 1.177-.175.201-.351.226-.651.076a8.212 8.212 0 0 1-2.417-1.493 9.07 9.07 0 0 1-1.68-2.09c-.176-.301-.019-.464.131-.614.136-.135.301-.351.451-.526.151-.176.2-.301.302-.501.101-.201.05-.376-.025-.526-.075-.15-.676-1.63-.926-2.23-.243-.585-.49-.505-.676-.514-.175-.008-.376-.008-.576-.008s-.526.075-.801.376c-.275.301-1.052 1.028-1.052 2.508 0 1.48 1.077 2.91 1.227 3.111.15.2 2.122 3.238 5.14 4.542.718.309 1.278.494 1.716.632.72.228 1.375.195 1.894.118.58-.086 1.776-.726 2.026-1.428.25-.702.25-1.304.175-1.429-.075-.126-.275-.201-.575-.351z"/></svg>
    </a>
    """, unsafe_allow_html=True)

# Initialisation du thème et des réglages
settings = load_settings()
if 'theme' not in st.session_state:
    st.session_state.theme = "Clair Modern ❄️"

apply_custom_theme(st.session_state.theme)

# Affichage du Marquee Dynamique
st.markdown(f"""
<div class="marquee">
    <div>{settings.get('marquee', '')}</div>
</div>
""", unsafe_allow_html=True)


# --- 3. FONCTIONS TECHNIQUES ---

def clean_num(val):
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    # Nettoyage de chaîne
    s = str(val).upper().replace('DZD', '').replace('DA', '').replace(' ', '').strip()
    if not s: return 0.0
    # Gestion intelligente des séparateurs : si on a une virgule et pas de point, c'est probablement la décimale (format FR/DZ)
    if ',' in s and '.' not in s:
        s = s.replace(',', '.')
    # Sinon si on a les deux, on retire la virgule (format US milliers)
    elif ',' in s and '.' in s:
        s = s.replace(',', '')
    
    # Garder uniquement chiffres et point
    s = "".join(c for c in s if c.isdigit() or c == '.')
    try:
        return float(s)
    except:
        return 0.0

def load_data():
    cols = ['Produit', 'Laboratoire', 'Quantité', 'PPA', 'image_path', 'Famille', 'DDP', 'Promo', 'Prix_Achat', 'Description', 'Dépôt', 'Arrivage']
    if not os.path.exists(DB_PATH): return pd.DataFrame(columns=cols)
    try:
        df = pd.read_csv(DB_PATH, encoding='utf-8-sig')
        
        # Renommage flexible
        rename_map = {
            'Quantité  Dépot': 'Quantité', 
            'Quantité Dépot': 'Quantité',
            'Quantité Dépôt': 'Quantité',
            'Fournisseur': 'Famille',
            'Prix': 'PPA',
            'LABO': 'Laboratoire'
        }
        df = df.rename(columns=rename_map)
        
        # Gestion des colonnes dupliquées (crucial après renommage)
        df = df.loc[:, ~df.columns.duplicated()]
        
        for c in cols:
            if c not in df.columns: 
                if c == 'Promo': df[c] = False
                elif c in ['Prix_Achat', 'PPA', 'Quantité']: df[c] = 0.0
                else: df[c] = ""
            
        # Nettoyage numérique Robuste
        df['PPA'] = df['PPA'].apply(clean_num)
        df['Prix_Achat'] = df['Prix_Achat'].apply(clean_num)
        df['Quantité'] = df['Quantité'].apply(clean_num)
        df['Promo'] = df['Promo'].astype(bool)
        
        # --- REGROUPEMENT ---
        agg_rules = {c: 'first' for c in df.columns if c not in ['Produit', 'PPA', 'Quantité']}
        agg_rules['Quantité'] = 'sum'
        agg_rules['image_path'] = 'max'
        df = df.groupby(['Produit', 'PPA'], as_index=False).agg(agg_rules)
        
        return df.fillna("")
    except: return pd.DataFrame(columns=cols)

def save_sale(cart_dict, total_val, user):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sale_data = []
    for k, v in cart_dict.items():
        sale_data.append({
            "Date": now,
            "Client": user,
            "Produit": k,
            "Prix": v['price'],
            "Qty": v['qty'],
            "Total": v['price'] * v['qty']
        })
    df_sales = pd.DataFrame(sale_data)
    if os.path.exists(SALES_DB):
        df_sales.to_csv(SALES_DB, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        df_sales.to_csv(SALES_DB, index=False, encoding='utf-8-sig')



def save_data(df, path=DB_PATH):
    df.to_csv(path, index=False, encoding='utf-8-sig')
    st.cache_data.clear()
    add_log("Mise à jour Base de données", f"Fichier: {os.path.basename(path)}")

def update_cart_qty(p_name, key):
    if key in st.session_state:
        st.session_state.cart[p_name]['qty'] = st.session_state[key]

def clean_filename(text):
    if pd.isna(text): return ""
    return re.sub(r'\W+', '_', str(text).strip()).upper()

def resize_and_save_image(uploaded_file, target_path, size=(800, 800)):
    try:
        from PIL import Image as PILImage, ImageOps
        img = PILImage.open(uploaded_file)
        
        # 1. Conversion en RGBA pour gérer la transparence proprement
        img = img.convert("RGBA")
        
        # 2. Redimensionnement proportionnel (pour tenir dans le cadre)
        img.thumbnail(size, PILImage.Resampling.LANCZOS)
        
        # 3. Création du fond blanc 800x800
        new_img = PILImage.new("RGB", size, (255, 255, 255))
        
        # 4. Centrage
        offset = ((size[0] - img.size[0]) // 2, (size[1] - img.size[1]) // 2)
        new_img.paste(img, offset, img) # Utilise le canal alpha pour le collage
        
        # 5. Sauvegarde en JPEG
        if not target_path.lower().endswith('.jpg'):
            target_path = os.path.splitext(target_path)[0] + ".jpg"
        new_img.save(target_path, "JPEG", quality=90)
        return os.path.basename(target_path)
    except Exception as e:
        st.error(f"Erreur de traitement image : {e}")
        return None

def get_image_base64(filename):
    if not filename or str(filename).lower() in ['nan', '']: return None
    path = os.path.join(IMG_DIR, str(filename).strip())
    
    # 1. Vérification locale
    if not os.path.isfile(path):
        # 2. Fallback GDrive : Si l'image manque, on tente de la télécharger
        try:
            from utils.gdrive_api import get_gdrive_service, get_remote_file_id, download_file_from_gdrive, GDRIVE_FOLDER_ID
            service = get_gdrive_service()
            if service:
                # Trouver le dossier image_stock sur Drive
                img_folder_id = get_remote_file_id(service, "image_stock", GDRIVE_FOLDER_ID)
                if img_folder_id:
                    file_id = get_remote_file_id(service, str(filename).strip(), img_folder_id)
                    if file_id:
                        download_file_from_gdrive(service, file_id, path)
        except:
            pass # On ignore les erreurs de téléchargement silencieusement
            
    if os.path.isfile(path):
        try:
            with open(path, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
        except: return None
    return None

def generate_pdf_catalogue(df):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Style personnalisé pour le tableau
    style_p = styles["Normal"]
    style_p.fontSize = 8
    style_p.leading = 10
    
    # Titre
    elements.append(Paragraph(f"<b>CATALOGUE PRODUITS - PHARMACIEL</b>", styles['Title']))
    elements.append(Paragraph(f"Date : {datetime.now().strftime('%d/%m/%Y')} | Total : {len(df)} produits", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Table de données
    data = [[Paragraph("<b>Produit</b>", style_p), Paragraph("<b>Labo</b>", style_p), Paragraph("<b>Famille</b>", style_p), Paragraph("<b>Prix</b>", style_p)]]
    for _, row in df.iterrows():
        p_name = Paragraph(str(row['Produit']), style_p)
        p_labo = Paragraph(str(row['Laboratoire']), style_p)
        p_fam = Paragraph(str(row['Famille']), style_p)
        p_price = Paragraph(f"<b>{row['PPA']} DA</b>", style_p)
        data.append([p_name, p_labo, p_fam, p_price])
        
    # Ajustement des largeurs (Total ~535 pour A4 avec marges)
    t = Table(data, colWidths=[230, 110, 110, 85])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.cadetblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_invoice(cart_dict, total_val):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("<b>FACTURE PROFORMA - PHARMACIEL PRO</b>", styles['Title']))
    elements.append(Paragraph(f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    data = [["Désignation", "Prix Unitaire", "Qté", "Total"]]
    for k, v in cart_dict.items():
        data.append([k, f"{v['price']} DA", v['qty'], f"{v['price']*v['qty']} DA"])
    
    data.append(["", "", "<b>TOTAL</b>", f"<b>{total_val} DA</b>"])
    
    t = Table(data, colWidths=[250, 100, 50, 100])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("<i>Merci de votre confiance.</i>", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_promo_flyer(df):
    df_promo = df[df['Promo'] == True]
    if df_promo.empty: return None
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = styles['Title']
    title_style.textColor = colors.red
    title_style.fontSize = 24
    
    elements.append(Paragraph(f"<b>🔥 OFFRES SPÉCIALES PROMO 🔥</b>", title_style))
    elements.append(Paragraph(f"PHARMACIEL PRO - Profitez de nos meilleures remises !", styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Date : {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    style_p = styles["Normal"]
    style_p.fontSize = 11
    
    data = [[Paragraph("<b>Produit</b>", style_p), Paragraph("<b>Laboratoire</b>", style_p), Paragraph("<b>Prix PROMO</b>", style_p)]]
    for _, row in df_promo.iterrows():
        p_name = Paragraph(f"<b>{row['Produit']}</b>", style_p)
        p_lab = Paragraph(str(row['Laboratoire']), style_p)
        p_price = Paragraph(f"<font color='red' size=12><b>{row['PPA']} DA</b></font>", style_p)
        data.append([p_name, p_lab, p_price])
        
    t = Table(data, colWidths=[250, 150, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.red),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 1, colors.red),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<i>* Offres valables dans la limite des stocks disponibles.</i>", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- 3. AUTHENTIFICATION ---
def login():
    if 'auth' not in st.session_state: st.session_state.auth = False
    if 'cart' not in st.session_state: st.session_state.cart = {}
    
    # Tentative de reconnexion automatique
    if not st.session_state.auth and os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                sess = json.load(f)
                st.session_state.auth = True
                st.session_state.user_role = sess['role']
                st.session_state.current_user = sess['user']
                add_log("Connexion Automatique")
        except: pass

    if not st.session_state.auth:
        # Premium centered login layout
        _, col_login, _ = st.columns([1, 2, 1])
        with col_login:
            # Hero branding header
            if os.path.exists("logo.png"):
                st.image("logo.png", width=120)
            st.markdown("""
            <div class="login-header">
                <div class="login-title">💊 Pharmaciel Pro</div>
                <div class="login-subtitle">Votre espace parapharmacie professionnel.<br>Accès client immédiat — aucun identifiant requis.</div>
            </div>
            """, unsafe_allow_html=True)

            # Client access card
            st.markdown("""
            <div class="client-portal-card">
                <div class="portal-info">
                    <h3>🌐 Accès Visiteur Libre</h3>
                    <p>Parcourez notre catalogue de produits, consultez les fiches détaillées et passez commande via WhatsApp — sans compte nécessaire.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🛍️ ACCÉDER AU CATALOGUE", type="primary", use_container_width=True):
                st.session_state.auth, st.session_state.user_role, st.session_state.current_user = True, "Client", "Visiteur"
                add_log("Accès Visiteur")
                st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            # Employee login expander
            with st.expander("🔑 Espace Collaborateur", expanded=False):
                with st.form("login_form"):
                    u = st.text_input("Identifiant", placeholder="Votre identifiant")
                    p = st.text_input("Mot de passe", type="password", placeholder="••••••••")
                    remember = st.checkbox("Rester connecté")
                    if st.form_submit_button("Se connecter", use_container_width=True):
                        role = None
                        if u == "admin" and p == "1992":
                            role, user_name = "Responsable", "Admin Suprême"
                        else:
                            users = load_users()
                            match = users[(users['user'] == u) & (users['pw'].astype(str) == p)]
                            if not match.empty:
                                role, user_name = match['role'].values[0], u
                        
                        if role:
                            st.session_state.auth, st.session_state.user_role, st.session_state.current_user = True, role, user_name
                            if remember:
                                with open(SESSION_FILE, 'w') as f: json.dump({"user": user_name, "role": role}, f)
                            add_log("Connexion Manuelle")
                            st.rerun()
                        else:
                            st.error("❌ Identifiants incorrects. Vérifiez et réessayez.")
        st.stop()

# --- 4. INTERFACE ---
login()
df_para = load_data()

# --- SIDEBAR : NAVIGATION & FILTRES ---
with st.sidebar:
    # Premium logo + user profile strip
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    
    role_icons = {"Responsable": "👑", "Commercial": "💼", "Client": "🌐", "Visiteur": "👁️"}
    role_icon = role_icons.get(st.session_state.user_role, "👤")
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%); 
                border: 1px solid var(--border-color); border-radius: 14px; padding: 14px 16px; margin-bottom: 16px;">
        <div style="font-size: 1.05rem; font-weight: 700; color: var(--primary-color);">{role_icon} {st.session_state.current_user}</div>
        <div style="font-size: 0.75rem; opacity: 0.55; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 3px;">{st.session_state.user_role}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Toggle Vue Mobile
    if 'mobile_mode' not in st.session_state:
        st.session_state.mobile_mode = False
    st.session_state.mobile_mode = st.toggle("📱 Mode Mobile", value=st.session_state.mobile_mode)
    
    st.divider()
    
    # Navigation
    if st.session_state.user_role == "Client":
        nav_options = ["📦 Boutique"]
    else:
        nav_options = ["📦 Gestion & Boutique", "📊 Statistiques"]
        if st.session_state.user_role in ["Responsable", "Commercial"]: nav_options.append("⚙️ Admin")
    
    menu = st.radio("Navigation", nav_options)
    
    st.divider()
    
    # Filtres
    with st.expander("🎯 Filtres & Recherche", expanded=True):
        f_famille = st.selectbox("Famille", ["Toutes"] + sorted([f for f in df_para['Famille'].unique() if f]))
        f_labo = st.selectbox("Laboratoire", ["Tous"] + sorted([l for l in df_para['Laboratoire'].unique() if l]))
        f_alerte = st.selectbox("Alertes Stock/DDP", ["Aucune", "Stock Bas (<5)", "Péremption Proche"])
        
        if st.button("🔄 Réinitialiser filtres", use_container_width=True):
            st.session_state.page = 1
            st.rerun()
            
        st.divider()
        pdf_buf = generate_pdf_catalogue(df_para)
        st.download_button("📄 PDF Catalogue", pdf_buf, "Catalogue_Pharmaciel.pdf", "application/pdf", use_container_width=True)
        
        # Bouton Flyer Promo
        promo_df = df_para[df_para['Promo'] == True]
        if not promo_df.empty:
            promo_buf = generate_promo_flyer(df_para)
            st.download_button("🔥 Flyer PROMO", promo_buf, "Promotions_Pharmaciel.pdf", "application/pdf", use_container_width=True)

    st.divider()

    # Panier Sidebar
    if st.session_state.cart:
        st.markdown("### 🛒 Votre Panier")
        total_panier = 0
        items_to_remove = []
        for p_name, details in st.session_state.cart.items():
            c_p1, c_p2 = st.columns([3, 1])
            new_qty = c_p1.number_input(f"{p_name}", min_value=1, value=details['qty'], key=f"q_side_{p_name}")
            st.session_state.cart[p_name]['qty'] = new_qty
            if c_p2.button("❌", key=f"del_{p_name}"):
                items_to_remove.append(p_name)
            total_panier += st.session_state.cart[p_name]['qty'] * details['price']
        
        for item in items_to_remove:
            del st.session_state.cart[item]
            st.rerun()
        
        st.markdown(f"<div style='font-size:1.1rem; font-weight:700; color:var(--primary-color); margin:10px 0;'>Total : {total_panier:,.0f} DA</div>", unsafe_allow_html=True)
        msg_cart = "Bonjour Pharmaciel, je souhaite commander :\n" + "\n".join([f"- {k} (x{v['qty']})" for k,v in st.session_state.cart.items()])
        st.link_button("🚀 Commander via WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg_cart)}", use_container_width=True)
        if st.button("🗑️ Vider le panier", use_container_width=True):
            st.session_state.cart = {}
            st.rerun()
        st.divider()

    # Thème & Déconnexion
    with st.expander("🎨 Personnalisation", expanded=False):
        theme_list = ["Pharmaciel Premium 🧪", "Clair Modern ❄️", "Sombre Élite 🌙", "Émeraude Royal 👑", "Aurore Boréale 🌌", "Cyberpunk ⚡", "Antigravity Dark 🌌"]
        new_theme = st.selectbox("Changer l'ambiance", 
                                theme_list, 
                                index=theme_list.index(st.session_state.theme))
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Déconnexion", type="secondary", use_container_width=True):
        st.session_state.auth = False
        st.session_state.user_role = None
        st.session_state.current_user = None
        st.rerun()

# --- DIALOGUE DÉTAILS ---
@st.dialog("📸 Ajouter une Photo")
def add_photo_dialog(product_name):
    st.write(f"Ajouter une image pour : **{product_name}**")
    
    tab1, tab2 = st.tabs(["📤 Upload", "☁️ Depuis GDrive"])
    
    with tab1:
        up = st.file_uploader("Choisir une image (800x800 auto)", type=['png','jpg','jpeg'], key=f"up_{product_name}")
        if st.button("💾 Enregistrer l'image (Upload)", use_container_width=True):
            if up:
                fname = f"{clean_filename(product_name)}.jpg"
                saved_name = resize_and_save_image(up, os.path.join(IMG_DIR, fname))
                if saved_name:
                    df_temp = load_data()
                    df_temp.loc[df_temp['Produit'] == product_name, 'image_path'] = saved_name
                    save_data(df_temp)
                    st.success("Image liée avec succès !")
                    st.rerun()
            else: st.error("Veuillez sélectionner un fichier.")
            
    with tab2:
        st.write("🔍 Rechercher sur votre Google Drive")
        try:
            from utils.gdrive_api import get_gdrive_service, get_main_folder_id, get_remote_file_id, download_file_from_gdrive
            service = get_gdrive_service()
            main_id = get_main_folder_id()
            if service and main_id:
                img_folder_id = get_remote_file_id(service, "image_stock", main_id)
                if img_folder_id:
                    # On liste les fichiers du dossier image_stock
                    query = f"'{img_folder_id}' in parents and trashed=false"
                    results = service.files().list(q=query, fields='files(id, name)').execute()
                    files = results.get('files', [])
                    if files:
                        file_options = {f['name']: f['id'] for f in files}
                        # Recherche intelligente : pré-sélectionner si match partiel
                        match_options = [n for n in file_options.keys() if clean_filename(product_name) in clean_filename(n)]
                        sel_file_name = st.selectbox("Sélectionner un fichier sur Drive", options=list(file_options.keys()), index=0 if not match_options else list(file_options.keys()).index(match_options[0]))
                        
                        if st.button("📥 Récupérer cette image depuis Drive", use_container_width=True):
                            with st.spinner("Récupération..."):
                                file_id = file_options[sel_file_name]
                                fname = f"{clean_filename(product_name)}.jpg"
                                target_path = os.path.join(IMG_DIR, fname)
                                download_file_from_gdrive(service, file_id, target_path)
                                
                                df_temp = load_data()
                                df_temp.loc[df_temp['Produit'] == product_name, 'image_path'] = fname
                                save_data(df_temp)
                                st.success(f"Image récupérée depuis Drive pour {product_name} !")
                                st.rerun()
                    else: st.warning("Aucun fichier trouvé dans 'image_stock' sur Drive.")
        except Exception as e:
            st.error(f"Erreur GDrive : {e}")

@st.dialog("Fiche Produit", width="large")
def show_details(row):
    # Responsive columns for dialog
    n_cols_dialog = 1 if st.session_state.mobile_mode else 2
    cols_dialog = st.columns(n_cols_dialog)
    
    img = get_image_base64(row['image_path'])
    with cols_dialog[0]:
        if img: 
            st.image(img)
        else: 
            st.markdown("""
            <div class="no-image-placeholder" style="height:350px;">
                <div class="placeholder-icon" style="font-size:4rem;">💊</div>
                <div class="placeholder-text" style="font-size:1rem;">Visuel Indisponible</div>
            </div>
            """, unsafe_allow_html=True)
    
    # If mobile, we use the same column (cols_dialog[0]), else the second one
    target_col = cols_dialog[0] if st.session_state.mobile_mode else cols_dialog[1]
    
    with target_col:
        st.header(row['Produit'])
        
        # Elegant HTML Specs Grid
        specs_html = f"""
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px; margin-top: 15px;">
            <div class="detail-item">
                <span class="detail-icon">🔬</span>
                <span class="detail-label">Laboratoire</span>
                <span class="detail-value">{row['Laboratoire']}</span>
            </div>
            <div class="detail-item">
                <span class="detail-icon">📅</span>
                <span class="detail-label">Date Péremption</span>
                <span class="detail-value">{row['DDP']}</span>
            </div>
        """
        if 'Arrivage' in row and row['Arrivage']:
            specs_html += f"""
            <div class="detail-item">
                <span class="detail-icon">🚚</span>
                <span class="detail-label">Arrivage</span>
                <span class="detail-value">{row['Arrivage']}</span>
            </div>
            """
        if 'Dépôt' in row and row['Dépôt']:
            specs_html += f"""
            <div class="detail-item">
                <span class="detail-icon">🏠</span>
                <span class="detail-label">Dépôt</span>
                <span class="detail-value">{row['Dépôt']}</span>
            </div>
            """
        specs_html += "</div>"
        st.markdown(specs_html, unsafe_allow_html=True)
        
        # Admin / Manager Panel
        if st.session_state.user_role == "Responsable":
            ppa_val = float(row['PPA']) if row['PPA'] > 0 else 0.0
            achat_val = float(row['Prix_Achat']) if row['Prix_Achat'] > 0 else 0.0
            qty_val = float(row['Quantité']) if row['Quantité'] > 0 else 0.0
            val_tot = ppa_val * qty_val
            marge = ppa_val - achat_val
            marge_pct = (marge / ppa_val * 100) if ppa_val > 0 else 0.0
            
            st.markdown(f"""
            <div class="internal-stats-card">
                <div class="stats-card-title">🔑 Données Administrateur</div>
                <div class="admin-grid">
                    <div class="admin-stat-item">
                        <span class="admin-stat-label">Stock en Dépôt</span>
                        <span class="admin-stat-val">{int(qty_val)} unités</span>
                    </div>
                    <div class="admin-stat-item">
                        <span class="admin-stat-label">Valeur du Stock</span>
                        <span class="admin-stat-val">{val_tot:,.0f} DA</span>
                    </div>
                    <div class="admin-stat-item">
                        <span class="admin-stat-label">Prix d'Achat</span>
                        <span class="admin-stat-val">{achat_val:,.0f} DA</span>
                    </div>
                    <div class="admin-stat-item">
                        <span class="admin-stat-label">Marge Estimée</span>
                        <span class="admin-stat-val" style="color:#10b981;">+{marge:,.0f} DA ({marge_pct:.1f}%)</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if row['Description']:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.02); border:1px solid var(--border-color); border-radius:12px; padding:12px 16px; margin-bottom:15px;">
                <div style="font-size:0.75rem; text-transform:uppercase; opacity:0.5; font-weight:600; margin-bottom:6px;">📝 Description</div>
                <div style="font-size:0.9rem; line-height:1.4;">{row['Description']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        p_text = f"{row['PPA']:,.0f} DA" if row['PPA'] > 0 else "Prix sur demande"
        st.metric("Prix Unitaire", p_text)
        
        msg = urllib.parse.quote(f"Pharmaciel - {row['Produit']} | Prix: {row['PPA']} DA")
        st.markdown(f"""
        <a href="https://wa.me/?text={msg}" target="_blank" style="background: linear-gradient(95deg, #25D366, #128c7e); color:white; padding:12px; border-radius:12px; text-decoration:none; display:flex; align-items:center; justify-content:center; gap:8px; text-align:center; font-weight:600; box-shadow: 0 4px 15px rgba(37,211,102,0.25); text-transform:uppercase; letter-spacing:0.5px; transition:all 0.3s ease; margin-bottom: 20px;">
            <svg width="18" height="18" fill="white" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle; margin-right:4px;"><path d="M12.031 0C5.385 0 0 5.386 0 12.03c0 2.12.551 4.198 1.597 6.02L.031 24l6.105-1.603a11.972 11.972 0 0 0 5.895 1.543h.005c6.645 0 12.03-5.387 12.03-12.032C24.066 5.386 18.679 0 12.031 0zm0 21.968h-.005a9.963 9.963 0 0 1-5.075-1.378l-.364-.216-3.771.99.998-3.676-.237-.377a9.96 9.96 0 0 1-1.526-5.283c0-5.5 4.476-9.975 9.98-9.975 5.503 0 9.978 4.475 9.978 9.975s-4.475 9.975-9.978 9.975zm5.474-7.48c-.3-.15-1.776-.876-2.052-.976-.275-.101-.476-.15-.676.15-.2.302-.776.977-.951 1.177-.175.201-.351.226-.651.076a8.212 8.212 0 0 1-2.417-1.493 9.07 9.07 0 0 1-1.68-2.09c-.176-.301-.019-.464.131-.614.136-.135.301-.351.451-.526.151-.176.2-.301.302-.501.101-.201.05-.376-.025-.526-.075-.15-.676-1.63-.926-2.23-.243-.585-.49-.505-.676-.514-.175-.008-.376-.008-.576-.008s-.526.075-.801.376c-.275.301-1.052 1.028-1.052 2.508 0 1.48 1.077 2.91 1.227 3.111.15.2 2.122 3.238 5.14 4.542.718.309 1.278.494 1.716.632.72.228 1.375.195 1.894.118.58-.086 1.776-.726 2.026-1.428.25-.702.25-1.304.175-1.429-.075-.126-.275-.201-.575-.351z"/></svg>
            PARTAGER SUR WHATSAPP
        </a>
        """, unsafe_allow_html=True)

        # --- ASSISTANT IA CONSEIL ---
        if settings.get('ai_active', True):
            st.divider()
            with st.expander("🤖 Assistant Expert IA (Conseils)", expanded=True):
                st.chat_message("assistant").write(f"Bonjour ! Je suis votre conseiller **Pharmaciel AI**. Je connais très bien le produit **{row['Produit']}** du laboratoire **{row['Laboratoire']}**. Comment puis-je vous aider ?")
                
                # Champ de question
                q_key = f"ai_query_{row['Produit']}_{row['Laboratoire']}"
                user_q = st.text_input("Posez votre question ici...", key=q_key, placeholder="Ex: C'est pour quel type de peau ? Routine conseillée ?")
                
                if user_q:
                    with st.spinner("L'expert IA analyse votre demande..."):
                        # On récupère les deux clés
                        gem_key = settings.get('gemini_key', '').strip()
                        or_key = settings.get('openrouter_key', '').strip()
                        ai_provider = settings.get('ai_provider', 'Google Gemini')
                        
                        if (ai_provider == "Google Gemini" and gem_key) or (ai_provider == "OpenRouter" and or_key):
                            try:
                                r = ""
                                if ai_provider == "OpenRouter":
                                    # Logic OpenRouter
                                    or_key = settings.get('openrouter_key').strip()
                                    headers = {
                                        "Authorization": f"Bearer {or_key}",
                                        "Content-Type": "application/json",
                                        "HTTP-Referer": "https://pharmaciel.dz",
                                        "X-Title": "Pharmaciel Pro"
                                    }
                                    
                                    # Map models for OpenRouter
                                    model_map = {
                                        "gemini-1.5-flash": "google/gemini-flash-1.5",
                                        "gemini-1.5-pro": "google/gemini-pro-1.5",
                                        "gemini-1.0-pro": "google/gemini-pro",
                                        "gpt-4o-mini": "openai/gpt-4o-mini",
                                        "claude-3-haiku": "anthropic/claude-3-haiku"
                                    }
                                    or_model = model_map.get(settings.get('ai_model', 'gemini-1.5-flash'), "google/gemini-flash-1.5")
                                    
                                    payload = {
                                        "model": or_model,
                                        "messages": [
                                            {"role": "system", "content": "Tu es un expert en parapharmacie pour le magasin 'Pharmaciel'."},
                                            {"role": "user", "content": f"Produit: {row['Produit']}\nLabo: {row['Laboratoire']}\nFamille: {row['Famille']}\nDescription: {row['Description']}\n\nQuestion: {user_q}"}
                                        ]
                                    }
                                    
                                    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                                    if response.status_code == 200:
                                        r = response.json()['choices'][0]['message']['content']
                                    else:
                                        r = f"⚠️ Erreur OpenRouter ({response.status_code}): {response.text}"
                                    add_log("Question IA", f"Produit: {row['Produit']} | Q: {user_q}")
                                elif ai_provider == "Google Gemini" and settings.get('gemini_key'):
                                    # Logic Gemini Direct
                                    gem_key = settings.get('gemini_key').strip()
                                    genai.configure(api_key=gem_key)
                                    prompt = f"""
                                    Tu es un expert en parapharmacie pour le magasin 'Pharmaciel'. 
                                    Aide le client pour le produit suivant :
                                    Nom: {row['Produit']}
                                    Laboratoire: {row['Laboratoire']}
                                    Famille: {row['Famille']}
                                    Description actuelle: {row['Description']}
                                    
                                    Question du client: {user_q}
                                    
                                    Réponds de manière professionnelle, rassurante et précise. Si tu ne connais pas le produit, donne des conseils généraux basés sur sa famille ({row['Famille']}).
                                    """
                                    target_model = settings.get('ai_model', 'gemini-1.5-flash')
                                    model = genai.GenerativeModel(target_model)
                                    response = model.generate_content(prompt)
                                    r = response.text
                                    add_log("Question IA", f"Produit: {row['Produit']} | Q: {user_q}")
                                else:
                                    r = "⚠️ Clé API non configurée pour le fournisseur sélectionné."
                            except Exception as e:
                                e_str = str(e)
                                if "429" in e_str:
                                    r = "⚠️ **Limite de quota atteinte** : Le service AI est très sollicité ou vous utilisez une clé gratuite limitée. Veuillez patienter 60 secondes ou vérifiez vos quotas."
                                elif "403" in e_str or "API_KEY_INVALID" in e_str:
                                    r = "⚠️ **Clé API Invalide** : La clé configurée dans l'onglet Admin n'est pas reconnue."
                                else:
                                    r = f"Erreur IA : {e_str} (Vérifiez votre clé API dans l'onglet Admin)."
                        else:
                            # Logique de secours améliorée
                            u_q = user_q.lower()
                            if "utiliser" in u_q or "comment" in u_q:
                                r = f"Le **{row['Produit']}** s'utilise généralement selon les besoins quotidiens. Étant de la famille **{row['Famille']}**, il est conseillé de suivre les indications de **{row['Laboratoire']}**."
                            elif "prix" in u_q:
                                r = f"Le prix est de **{row['PPA']} DA**. C'est un excellent rapport qualité-prix."
                            else:
                                r = f"C'est un produit très demandé de la catégorie **{row['Famille']}**. Pour un conseil expert, veuillez configurer la clé API Gemini dans les réglages."
                            add_log("Question IA (Secours)", f"Produit: {row['Produit']} | Q: {user_q}")
                        
                        st.chat_message("user").write(user_q)
                        st.chat_message("assistant").write(f"✨ **Réponse de l'expert :** {r}")

# --- ONGLET 1 : CATALOGUE & PANIER ---
if menu in ["📦 Gestion & Boutique", "📦 Boutique"]:
    st.title("📦 Espace Commercial")
    
    if st.session_state.user_role == "Client":
        t_tabs_names = ["📋 Catalogue", "🛒 Mon Panier", "🤝 Support & Avis"]
    else:
        t_tabs_names = ["📋 Catalogue", "🛒 Commandes Client", "🖼️ Images & Web", "🔄 Sync Excel", "🤝 Support Client"]
        if st.session_state.user_role == "Responsable": t_tabs_names.extend(["➕ Ajout", "✏️ Modif/Suppr"])
    
    tabs = st.tabs(t_tabs_names)

    with tabs[0]: # Catalogue
        # --- SECTION NOUVEAUTÉS ---
        with st.expander("✨ Nouveautés & Promotions", expanded=False):
            new_items = df_para.tail(5) # Les 5 derniers ajoutés
            n_cols_news = 2 if st.session_state.mobile_mode else 5
            c_new = st.columns(n_cols_news)
            for idx, n_row in enumerate(new_items.to_dict('records')):
                with c_new[idx % n_cols_news]:
                    img_n = get_image_base64(n_row['image_path'])
                    if img_n: st.image(img_n, use_container_width=True)
                    st.caption(f"**{n_row['Produit']}**")
                    p_new = f"{n_row['PPA']} DA" if n_row['PPA'] > 0 else "Prix NC"
                    st.write(f"**{p_new}**")
        
        n_cols_search = 1 if st.session_state.mobile_mode else 2
        c_search = st.columns([7, 3] if not st.session_state.mobile_mode else [1])
        c1 = c_search[0]
        c2 = c_search[0] if st.session_state.mobile_mode else c_search[1]
        
        # Liste des suggestions (Produits uniques)
        suggestions = sorted(df_para['Produit'].unique())
        with c1:
            search = st.selectbox("🔍 Rechercher un produit...", options=suggestions, index=None, placeholder="Tapez le nom d'un produit...")
        with c2:
            st.write("⚙️ **Options**")
            tri_az = st.toggle("Tri A-Z", value=True)
            hide = st.toggle("Photos")
        
        filt = df_para.copy()
        # Application des filtres sidebar
        if f_famille != "Toutes": filt = filt[filt['Famille'] == f_famille]
        if f_labo != "Tous": filt = filt[filt['Laboratoire'] == f_labo]
        if f_alerte == "Stock Bas (<5)": filt = filt[filt['Quantité'] < 5]
        if f_alerte == "Péremption Proche": 
            # Logique simplifiée : contient 2024 ou 2025
            filt = filt[filt['DDP'].str.contains('2024|2025', na=False)]
            
        if search: 
            # Utilisation de regex=False pour éviter les bugs avec les caractères spéciaux comme '+' (SPF50+)
            filt = filt[filt['Produit'].str.contains(search, case=False, na=False, regex=False)]
        if tri_az: filt = filt.sort_values(by='Produit', ascending=True)
        if hide: filt = filt[filt['image_path'].str.len() > 3]
        
        if filt.empty: 
            st.warning("⚠️ Aucun produit ne correspond à ces critères.")
            
            # Diagnostic des filtres
            active_filters = []
            if f_famille != "Toutes": active_filters.append(f"Famille: {f_famille}")
            if f_labo != "Tous": active_filters.append(f"Labo: {f_labo}")
            if f_alerte != "Aucune": active_filters.append(f"Alerte: {f_alerte}")
            if search: active_filters.append(f"Recherche: '{search}'")
            if hide: active_filters.append("Option 'Photos' (affiche uniquement les produits avec images)")
            
            if active_filters:
                st.info("💡 **Filtres actifs détectés :**\n- " + "\n- ".join(active_filters))
                if st.button("🔄 Réinitialiser tous les filtres", type="primary", use_container_width=True):
                    # On réinitialise les états via session_state si possible, ou on force un rerun sans filtres
                    st.session_state.page = 1
                    # Pour un reset complet, on peut vider les clés de widgets si elles existent
                    # Ici on va juste suggérer d'utiliser le bouton de la sidebar ou rafraîchir
                    st.rerun()
            else:
                st.error("🚨 La base de données semble vide ou n'a pas pu être chargée correctement.")
        else:
            # --- PAGINATION ---
            items_per_page = 12
            num_pages = max(1, (len(filt) - 1) // items_per_page + 1)
            
            if 'page' not in st.session_state: st.session_state.page = 1
            if st.session_state.page > num_pages: st.session_state.page = 1
            
            col_page_1, col_page_2, col_page_3 = st.columns([1, 3, 1])
            if col_page_1.button("⬅️ Précédent", disabled=st.session_state.page <= 1, use_container_width=True):
                st.session_state.page -= 1
                st.rerun()
            
            col_page_2.markdown(f"<p style='text-align:center;'>Page <b>{st.session_state.page}</b> / {num_pages} ({len(filt)} produits)</p>", unsafe_allow_html=True)
            
            if col_page_3.button("Suivant ➡️", disabled=st.session_state.page >= num_pages, use_container_width=True):
                st.session_state.page += 1
                st.rerun()
                
            start_idx = (st.session_state.page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_items = filt.iloc[start_idx:end_idx]
            
            n_cols_grid = 1 if st.session_state.mobile_mode else 4
            for i in range(0, len(page_items), n_cols_grid):
                cols = st.columns(n_cols_grid)
                for j in range(n_cols_grid):
                    if i+j < len(page_items):
                        row = page_items.iloc[i+j]
                        with cols[j]:
                            with st.container(border=True):
                                # Smart Match : si image_path vide, on tente le nom du produit
                                img_path = row['image_path']
                                if not img_path or str(img_path).lower() in ['nan', '']:
                                    img_path = f"{clean_filename(row['Produit'])}.jpg"
                                    
                                img = get_image_base64(img_path)
                                if img: 
                                    st.image(img, use_container_width=True)
                                else:
                                    if st.session_state.user_role != "Client":
                                        st.markdown("""
                                        <div class="no-image-placeholder">
                                            <div class="placeholder-icon">📸</div>
                                            <div class="placeholder-text">Administrateur</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        if st.button("Ajouter Photo", key=f"btn_add_img_{start_idx+i+j}", use_container_width=True):
                                            add_photo_dialog(row['Produit'])
                                    else:
                                        st.markdown("""
                                        <div class="no-image-placeholder">
                                            <div class="placeholder-icon">💊</div>
                                            <div class="placeholder-text">Visuel Pharmaciel</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                
                                # Badges compacts
                                badge_html = ""
                                if st.session_state.user_role != "Client" and row['Quantité'] < 5: 
                                    badge_html += '<span style="background:linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(239, 68, 68, 0.05) 100%); color:#ef4444; border:1px solid rgba(239, 68, 68, 0.25); padding:3px 8px; border-radius:12px; font-size:9px; font-weight:600; text-transform:uppercase; margin-right:4px;">⚠️ Stock Bas</span>'
                                if row['Promo']: 
                                    badge_html += '<span style="background:linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%); color:#f59e0b; border:1px solid rgba(245, 158, 11, 0.25); padding:3px 8px; border-radius:12px; font-size:9px; font-weight:600; text-transform:uppercase;">🔥 PROMO</span>'
                                
                                if badge_html: 
                                    st.markdown(f'<div class="card-badges">{badge_html}</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown('<div class="card-badges-empty"></div>', unsafe_allow_html=True)
                                
                                # Elegant HTML styling for Product card body
                                p_disp = f"{row['PPA']:,.0f}" if row['PPA'] > 0 else "Sur demande"
                                currency_span = '<span class="currency">DA</span>' if row['PPA'] > 0 else ""
                                st.markdown(f"""
                                <div class="product-card-body">
                                    <div class="product-labo">{row['Laboratoire']}</div>
                                    <div class="product-title" title="{row['Produit']}">{row['Produit']}</div>
                                    <div class="product-price">{p_disp}{currency_span}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                c_b1, c_b2 = st.columns([3, 2])
                                if c_b1.button("Détails", key=f"v_{start_idx+i+j}", use_container_width=True): show_details(row)
                                if c_b2.button("🛒", key=f"add_{start_idx+i+j}", use_container_width=True):
                                    if row['Produit'] in st.session_state.cart:
                                        st.session_state.cart[row['Produit']]['qty'] += 1
                                    else:
                                        st.session_state.cart[row['Produit']] = {'price': row['PPA'], 'qty': 1}
                                    st.toast(f"Ajouté : {row['Produit']}")
                                    st.rerun()
            
            # --- PAGINATION BAS DE PAGE ---
            st.divider()
            col_page_b1, col_page_b2, col_page_b3 = st.columns([1, 3, 1])
            if col_page_b1.button("⬅️ Précédent", key="p_prev_bot", disabled=st.session_state.page <= 1, use_container_width=True):
                st.session_state.page -= 1
                st.rerun()
            col_page_b2.markdown(f"<p style='text-align:center;'>Page <b>{st.session_state.page}</b> / {num_pages}</p>", unsafe_allow_html=True)
            if col_page_b3.button("Suivant ➡️", key="p_next_bot", disabled=st.session_state.page >= num_pages, use_container_width=True):
                st.session_state.page += 1
                st.rerun()

    if "🖼️ Images & Web" in t_tabs_names:
        with tabs[t_tabs_names.index("🖼️ Images & Web")]:
            st.subheader("🖼️ Gestion des visuels")
            
            mode_img = st.radio("Mode d'action", ["Un par un (Nouveaux)", "🖼️ Modifier / Supprimer", "⚡ Importation Groupée"], horizontal=True)
            
            if mode_img == "Un par un (Nouveaux)":
                df_sans_image = df_para[
                    (df_para['image_path'].isna()) | 
                    (df_para['image_path'] == "") | 
                    (df_para['image_path'].str.len() < 3)
                ]
                
                if df_sans_image.empty:
                    st.success("🎉 Tous les produits ont déjà une photo !")
                else:
                    liste_produits = sorted(df_sans_image['Produit'].unique())
                    sel_prod = st.selectbox("Sélectionner un produit sans image", liste_produits)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        with st.form("form_single_img", clear_on_submit=True):
                            uploaded_file = st.file_uploader("Charger une photo (Sera redimensionnée 800x800)", type=['png', 'jpg', 'jpeg'], key="single_up")
                            if st.form_submit_button("💾 Lier cette image"):
                                if uploaded_file:
                                    fname = f"{clean_filename(sel_prod)}.jpg"
                                    saved_name = resize_and_save_image(uploaded_file, os.path.join(IMG_DIR, fname))
                                    if saved_name:
                                        df_para.loc[df_para['Produit'] == sel_prod, 'image_path'] = saved_name
                                        save_data(df_para)
                                        # Auto-sync GDrive
                                        sync_data_permanent(f"Ajout image: {sel_prod}")
                                        st.success(f"Image 800x800 liée à {sel_prod} (Sauvegardée sur GDrive ✨)")
                                        st.rerun()
                    with c2:
                        st.markdown("### 🤖 Assistant Recherche IA")
                        
                        if st.button("🔍 Demander à l'IA d'analyser le produit", use_container_width=True):
                            with st.spinner("Analyse du produit par l'IA..."):
                                # Utiliser l'IA configurée
                                or_key = settings.get('openrouter_key', '').strip()
                                gem_key = settings.get('gemini_key', '').strip()
                                ai_provider = settings.get('ai_provider', 'Google Gemini')
                                
                                prompt = f"Produit: {sel_prod}\nDonne moi les 3 meilleurs mots clés de recherche pour trouver l'image de ce produit parapharmaceutique sur Google. Réponds court."
                                advice = "Cherche sur Google Images."
                                
                                try:
                                    if ai_provider == "OpenRouter" and or_key:
                                        headers = {"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"}
                                        payload = {"model": "google/gemini-flash-1.5", "messages": [{"role": "user", "content": prompt}]}
                                        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                                        advice = res.json()['choices'][0]['message']['content']
                                    elif ai_provider == "Google Gemini" and gem_key:
                                        genai.configure(api_key=gem_key)
                                        model = genai.GenerativeModel("gemini-1.5-flash")
                                        advice = model.generate_content(prompt).text
                                except: pass
                                
                                st.success(f"💡 Conseil IA : {advice}")
                                st.link_button("🚀 Lancer la recherche optimisée", f"https://www.google.com/search?tbm=isch&q={urllib.parse.quote(advice)}")

                        st.divider()
                        st.markdown("### 🔗 Importer via URL")
                        img_url = st.text_input("Coller l'URL de l'image ici", placeholder="https://example.com/image.jpg")
                        if st.button("📥 Télécharger et Traiter (800x800 White)"):
                            if img_url:
                                try:
                                    response = requests.get(img_url, stream=True, timeout=10)
                                    if response.status_code == 200:
                                        fname = f"{clean_filename(sel_prod)}.jpg"
                                        target_path = os.path.join(IMG_DIR, fname)
                                        # Utiliser resize_and_save_image sur le flux
                                        img_data = io.BytesIO(response.content)
                                        saved_name = resize_and_save_image(img_data, target_path)
                                        if saved_name:
                                            df_para.loc[df_para['Produit'] == sel_prod, 'image_path'] = saved_name
                                            save_data(df_para)
                                            # Auto-sync GDrive
                                            sync_data_permanent(f"Import URL image: {sel_prod}")
                                            st.success(f"Image importée et formatée pour {sel_prod} (Sauvegardée ✨)")
                                            st.rerun()
                                    else: st.error("Impossible de télécharger l'image depuis cette URL.")
                                except Exception as e: st.error(f"Erreur : {e}")

            elif mode_img == "🖼️ Modifier / Supprimer":
                df_avec_image = df_para[df_para['image_path'].str.len() > 3]
                if df_avec_image.empty:
                    st.info("Aucun produit n'a d'image actuellement.")
                else:
                    liste_prod_all = sorted(df_para['Produit'].unique())
                    sel_prod = st.selectbox("Choisir le produit à modifier", liste_prod_all)
                    
                    prod_row = df_para[df_para['Produit'] == sel_prod].iloc[0]
                    curr_img = get_image_base64(prod_row['image_path'])
                    
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        if curr_img:
                            st.image(curr_img, caption="Image Actuelle", width=200)
                            if st.button("🗑️ Supprimer l'image actuelle", type="secondary"):
                                df_para.loc[df_para['Produit'] == sel_prod, 'image_path'] = ""
                                save_data(df_para)
                                st.success("Lien image supprimé !")
                                st.rerun()
                        else:
                            st.warning("Ce produit n'a pas encore d'image.")
                    
                    with col_m2:
                        st.write("📤 Remplacer / Ajouter")
                        
                        # Assistant IA ici aussi
                        if st.button("🤖 Aide IA Recherche", key="ai_help_replace", use_container_width=True):
                             st.info(f"💡 Suggestion : `{sel_prod} parapharmacie algerie`")
                             st.link_button("🔍 Chercher", f"https://www.google.com/search?tbm=isch&q={sel_prod.replace(' ','+')}+parapharmacie+algerie")
                        
                        with st.form("form_replace_img", clear_on_submit=True):
                            new_up = st.file_uploader("Nouvelle image (Auto-resize 800x800)", type=['png', 'jpg', 'jpeg'], key="replace_up")
                            if st.form_submit_button("💾 Enregistrer la nouvelle image"):
                                if new_up:
                                    fname = f"{clean_filename(sel_prod)}.jpg"
                                    saved_name = resize_and_save_image(new_up, os.path.join(IMG_DIR, fname))
                                    if saved_name:
                                        df_para.loc[df_para['Produit'] == sel_prod, 'image_path'] = saved_name
                                        save_data(df_para)
                                        # Auto-sync GDrive
                                        sync_data_permanent(f"Modif image: {sel_prod}")
                                        st.success("Image mise à jour en 800x800 et sauvegardée ! ✨")
                                        st.rerun()
            
            else: # LIAISON EXPRESS GDRIVE
                st.subheader("🪄 Liaison Express GDrive")
                st.markdown("Cette méthode permet de lier rapidement des dizaines de produits à vos photos sur Google Drive.")
                
                try:
                    from utils.gdrive_api import get_gdrive_service, get_main_folder_id, get_remote_file_id, download_file_from_gdrive
                    service = get_gdrive_service()
                    main_id = get_main_folder_id()
                    if service and main_id:
                        img_folder_id = get_remote_file_id(service, "image_stock", main_id)
                        if img_folder_id:
                            # 1. Lister les fichiers sur Drive
                            results = service.files().list(q=f"'{img_folder_id}' in parents and trashed=false", fields='files(id, name)').execute()
                            drive_files = results.get('files', [])
                            
                            if not drive_files:
                                st.warning("Aucune photo trouvée dans 'image_stock' sur Drive.")
                            else:
                                # 2. Produits sans images
                                df_empty = df_para[df_para['image_path'].str.len() < 3].copy()
                                if df_empty.empty:
                                    st.success("🎉 Tous vos produits ont déjà une image !")
                                else:
                                    st.info(f"💡 {len(df_empty)} produits n'ont pas encore d'image. Tentative de correspondance automatique...")
                                    
                                    # Préparer les suggestions
                                    suggestions = []
                                    drive_dict = {f['name']: f['id'] for f in drive_files}
                                    
                                    for idx, row in df_empty.head(10).iterrows(): # On traite par packs de 10
                                        p_name = row['Produit']
                                        p_clean = clean_filename(p_name)
                                        # Match fuzzy
                                        best_match = None
                                        for d_name in drive_dict.keys():
                                            if p_clean in clean_filename(d_name):
                                                best_match = d_name
                                                break
                                        suggestions.append({'id': idx, 'prod': p_name, 'match': best_match})
                                    
                                    # Affichage de l'interface de revue
                                    for s in suggestions:
                                        with st.container(border=True):
                                            c1, c2, c3 = st.columns([2, 2, 1])
                                            c1.write(f"**{s['prod']}**")
                                            if s['match']:
                                                c2.success(f"📎 Trouvé : {s['match']}")
                                                if c3.button("Lier ✅", key=f"bulk_ok_{s['id']}"):
                                                    file_id = drive_dict[s['match']]
                                                    fname = f"{clean_filename(s['prod'])}.jpg"
                                                    download_file_from_gdrive(service, file_id, os.path.join(IMG_DIR, fname))
                                                    df_para.at[s['id'], 'image_path'] = fname
                                                    save_data(df_para)
                                                    st.rerun()
                                            else:
                                                c2.warning("Non trouvé")
                                                if c3.button("🔍 Choisir", key=f"bulk_sel_{s['id']}"):
                                                    add_photo_dialog(s['prod'])
                                    
                                    if len(df_empty) > 10:
                                        st.write(f"... et {len(df_empty)-10} autres produits.")
                except Exception as e:
                    st.error(f"Erreur GDrive : {e}")
            
            st.divider()
            if st.button("🧹 Optimiseur : Supprimer les images inutilisées"):
                files_in_dir = set(os.listdir(IMG_DIR))
                files_in_db = set(df_para['image_path'].dropna().unique())
                to_delete = files_in_dir - files_in_db
                for f in to_delete:
                    try: os.remove(os.path.join(IMG_DIR, f))
                    except: pass
                st.success(f"Nettoyage terminé : {len(to_delete)} fichiers supprimés.")
                add_log("Nettoyage Visuels", f"{len(to_delete)} fichiers")

    if "🔄 Sync Excel" in t_tabs_names:
        with tabs[t_tabs_names.index("🔄 Sync Excel")]:
            st.subheader("🔄 Synchronisation & Persistance")
            
            # --- NOUVEAU : BOUTON DE SAUVEGARDE GDRIVE ---
            st.markdown("### 💾 Sauvegarde Permanente (Google Drive)")
            st.warning("⚠️ Sur Streamlit Cloud, vos modifications (images, produits) sont perdues si l'app redémarre. Cliquez ci-dessous pour les enregistrer sur Google Drive.")
            if st.button("🚀 SAUVEGARDER TOUT SUR GDRIVE (Permanent)", type="primary", use_container_width=True):
                with st.spinner("Synchronisation avec Google Drive en cours..."):
                    from utils.gdrive_api import sync_to_gdrive
                    success, msg = sync_to_gdrive("Sauvegarde manuelle utilisateur")
                    if success: st.success(msg)
                    else: st.error(msg)
            
            if st.button("🔄 RESTAURER DEPUIS GDRIVE (Récupérer les données)", type="secondary", use_container_width=True):
                with st.spinner("Restauration en cours..."):
                    from utils.gdrive_api import restore_from_gdrive
                    success, msg = restore_from_gdrive()
                    if success: 
                        st.success(msg)
                        st.rerun()
                    else: st.error(msg)
            
            st.divider()
            st.info("Importez votre fichier Excel (format Dépôt, Produit, Quantité Dépot, DDP, PPA, Labo, Arrivage).")
            
            up_excel = st.file_uploader("Choisir le fichier Excel/CSV", type=['xlsx', 'csv'])
            if up_excel:
                try:
                    if up_excel.name.endswith('.xlsx'):
                        xl = pd.ExcelFile(up_excel)
                        df_new = pd.read_excel(up_excel, sheet_name=0)
                        if df_new.empty or 'Produit' not in df_new.columns:
                            for sheet in xl.sheet_names:
                                temp_df = pd.read_excel(up_excel, sheet_name=sheet)
                                if 'Produit' in temp_df.columns:
                                    df_new = temp_df
                                    break
                    else:
                        df_new = pd.read_csv(up_excel)
                    
                    if 'Produit' in df_new.columns:
                        df_new = df_new.dropna(subset=['Produit'])
                    
                    st.write("🔍 Aperçu des données détectées :", df_new.head(5))
                    
                    if df_new.empty:
                        st.warning("⚠️ Aucune donnée valide trouvée. Vérifiez que la colonne 'Produit' existe et n'est pas vide.")
                    
                    if st.button("🚀 Lancer la Synchronisation", disabled=df_new.empty):
                        df_new = df_new.rename(columns={
                            'Quantité  Dépot': 'Quantité', 'Quantité Dépot': 'Quantité', 'Quantité Dépôt': 'Quantité',
                            'Fournisseur': 'Famille', 'Labo': 'Laboratoire', 'Prix': 'PPA', 'LABO': 'Laboratoire'
                        })
                        # Nettoyer les doublons de colonnes après renommage
                        df_new = df_new.loc[:, ~df_new.columns.duplicated()]
                        
                        df_new['Produit'] = df_new['Produit'].astype(str).str.upper().str.strip()
                        
                        # Utiliser le nettoyeur robuste pour PPA
                        if 'PPA' in df_new.columns:
                            df_new['PPA'] = df_new['PPA'].apply(clean_num)

                        # Éviter d'écraser les images/descriptions par des colonnes vides de l'Excel
                        cols_to_drop = [c for c in ['image_path', 'image', 'photo'] if c in df_new.columns]
                        if cols_to_drop: df_new = df_new.drop(columns=cols_to_drop)

                        df_img = df_para[['Produit', 'image_path']].sort_values('image_path', ascending=False).drop_duplicates('Produit')
                        merged = pd.merge(df_new, df_img, on='Produit', how='left')
                        merged['image_path'] = merged['image_path'].fillna("")
                        
                        required_cols = ['Promo', 'Prix_Achat', 'Description', 'Famille', 'Laboratoire', 'DDP', 'Dépôt', 'Arrivage', 'PPA']
                        for c in required_cols:
                            if c not in merged.columns:
                                if c == 'Promo': merged[c] = False
                                elif c in ['Prix_Achat', 'PPA']: merged[c] = 0
                                else: merged[c] = ""
                        
                        save_data(merged)
                        st.success("✅ Synchronisation terminée avec succès !")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'import : {e}")

    if "➕ Ajout" in t_tabs_names:
        with tabs[t_tabs_names.index("➕ Ajout")]:
            with st.form("add_p"):
                c_a1, c_a2 = st.columns(2)
                n = c_a1.text_input("Désignation")
                l = c_a2.text_input("Labo")
                p = c_a1.number_input("Prix (PPA)", 0.0)
                pa = c_a2.number_input("Prix d'Achat", 0.0)
                q = c_a2.number_input("Quantité", 0)
                d = c_a1.text_input("DDP (MM/YY)")
                f = c_a2.text_input("Famille")
                desc = st.text_area("Description du produit")
                promo = st.checkbox("Mettre en promotion")
                if st.form_submit_button("Enregistrer le produit"):
                    new_row = pd.DataFrame([{"Produit": n.upper(), "Laboratoire": l.upper(), "PPA": p, "Prix_Achat": pa, "Quantité": q, "DDP": d, "Famille": f, "image_path": "", "Promo": promo, "Description": desc}])
                    save_data(pd.concat([df_para, new_row], ignore_index=True))
                    st.success(f"Produit {n} ajouté !")
                    st.rerun()

    if "✏️ Modif/Suppr" in t_tabs_names:
        with tabs[t_tabs_names.index("✏️ Modif/Suppr")]:
            st.subheader("⚙️ Gestion & Modification")
            target = st.selectbox("Sélectionner un produit à modifier", sorted(df_para['Produit'].unique()))
            
            if target:
                p_idx = df_para[df_para['Produit'] == target].index[0]
                p_data = df_para.loc[p_idx]
                
                with st.form(f"edit_{target}"):
                    c1, c2 = st.columns(2)
                    new_n = c1.text_input("Désignation", value=p_data['Produit'])
                    new_l = c2.text_input("Laboratoire", value=p_data['Laboratoire'])
                    new_p = c1.number_input("Prix (PPA)", value=float(p_data['PPA']))
                    new_pa = c2.number_input("Prix d'Achat", value=float(p_data['Prix_Achat']))
                    new_q = c2.number_input("Quantité en stock", value=int(p_data['Quantité']))
                    new_d = c1.text_input("DDP", value=p_data['DDP'])
                    new_f = c2.text_input("Famille", value=p_data['Famille'])
                    new_desc = st.text_area("Description", value=p_data['Description'])
                    new_promo = st.checkbox("Produit en PROMO", value=bool(p_data['Promo']))
                    
                    col_btn1, col_btn2 = st.columns(2)
                    if col_btn1.form_submit_button("💾 Enregistrer les modifications", use_container_width=True):
                        df_para.at[p_idx, 'Produit'] = new_n.upper()
                        df_para.at[p_idx, 'Laboratoire'] = new_l.upper()
                        df_para.at[p_idx, 'PPA'] = new_p
                        df_para.at[p_idx, 'Prix_Achat'] = new_pa
                        df_para.at[p_idx, 'Quantité'] = new_q
                        df_para.at[p_idx, 'DDP'] = new_d
                        df_para.at[p_idx, 'Famille'] = new_f
                        df_para.at[p_idx, 'Promo'] = new_promo
                        df_para.at[p_idx, 'Description'] = new_desc
                        save_data(df_para)
                        st.success("Modifications enregistrées !")
                        st.rerun()

                    if col_btn2.form_submit_button("❌ Supprimer le produit", use_container_width=True):
                        df_para = df_para.drop(p_idx)
                        save_data(df_para)
                        st.warning("Produit supprimé.")
                        st.rerun()

    # --- ONGLET : PANIER / COMMANDES ---
    if "🛒 Mon Panier" in t_tabs_names or "🛒 Commandes Client" in t_tabs_names:
        idx_p = t_tabs_names.index("🛒 Mon Panier") if "🛒 Mon Panier" in t_tabs_names else t_tabs_names.index("🛒 Commandes Client")
        with tabs[idx_p]:
            st.subheader("🛒 Gestion du Panier & Proforma")
            if not st.session_state.cart:
                st.info("Le panier est vide.")
            else:
                st.subheader("Articles dans votre panier")
                items_to_del = []
                total_cmd = 0
                for k, v in st.session_state.cart.items():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    col1.write(f"**{k}**")
                    col2.number_input("Quantité", min_value=1, value=v['qty'], key=f"edit_q_{k}", on_change=update_cart_qty, args=(k, f"edit_q_{k}"))
                    line_total = v['price'] * v['qty']
                    col3.write(f"{line_total:,.2f} DA")
                    total_cmd += line_total
                    if col4.button("🗑️", key=f"del_v_{k}"): items_to_del.append(k)
                for item in items_to_del:
                    del st.session_state.cart[item]
                    st.rerun()
                st.divider()
                st.subheader(f"Total Proforma : {total_cmd:,.2f} DA")
                c1, c2, c3 = st.columns(3)
                if c1.button("🗑️ Vider le panier", type="primary", key="clear_cart_tab", use_container_width=True):
                    st.session_state.cart = {}
                    st.rerun()
                inv_pdf = generate_invoice(st.session_state.cart, total_cmd)
                c2.download_button("📄 Facture Proforma PDF", inv_pdf, f"Proforma_{datetime.now().strftime('%Y%m%d')}.pdf", "application/pdf", use_container_width=True)
                msg_cart = f"Bonjour Pharmaciel, voici ma commande (Proforma) :\n" + "\n".join([f"- {k} (x{v['qty']}) : {v['price']*v['qty']} DA" for k,v in st.session_state.cart.items()])
                if c3.button("✅ Valider & WhatsApp", key="whatsapp_tab", use_container_width=True):
                    st.balloons()
                    save_sale(st.session_state.cart, total_cmd, st.session_state.current_user)
                    st.success("🚀 Commande validée avec succès !")
                    st.link_button("Ouvrir WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg_cart)}")

    # --- ONGLET : ENGAGEMENT & SUPPORT ---
    support_label = next((n for n in t_tabs_names if "🤝" in n), None)
    if support_label:
        with tabs[t_tabs_names.index(support_label)]:
            colored_header(label="🤝 Engagement & Support", description="Nous sommes à votre écoute", color_name="blue-70")
            c_s1, c_s2 = st.columns([2, 1])
            with c_s1:
                st.subheader("❓ FAQ")
                with st.expander("🛡️ Authenticité des produits", expanded=True):
                    st.write("Tous nos produits proviennent directement des laboratoires officiels. Nous garantissons 100% d'authenticité.")
                with st.expander("🚚 Livraison & Délais"):
                    st.write("Livraison nationale disponible dans les 58 Wilayas via nos partenaires logistiques.")
                with st.expander("💳 Modes de paiement"):
                    st.write("Espèces à la livraison, BaridiMob ou Virement bancaire.")
                
                st.divider()
                st.subheader("⭐ Avis Clients")
                avis_data = [
                    {"n": "Amine B.", "v": "⭐⭐⭐⭐⭐", "t": "Service très professionnel et rapide."},
                    {"n": "Sarah M.", "v": "⭐⭐⭐⭐⭐", "t": "Produits conformes et bien emballés."}
                ]
                for a in avis_data:
                    with st.container(border=True):
                        st.markdown(f"**{a['n']}** {a['v']}")
                        st.write(f"_{a['t']}_")
            
            with c_s2:
                st.subheader("📞 Contact Direct")
                st.info("Besoin d'un conseil santé ? Nos agents sont à votre écoute :")
                
                # Charger les agents WhatsApp depuis la DB
                u_db = load_users()
                agents = u_db[u_db['whatsapp'].str.len() > 5] # Filtre les numéros valides
                
                if not agents.empty:
                    for _, agent in agents.iterrows():
                        st.link_button(f"💬 {agent['display_name']}", f"https://wa.me/{agent['whatsapp']}", use_container_width=True)
                else:
                    st.warning("Aucun agent n'est disponible pour le moment.")
                
                st.divider()
                st.write("**Horaires :**")
                st.write("Samedi - Jeudi : 08:30 - 18:00")
                
                st.divider()
                st.markdown("### 💊 Pharmaciel Pro")
                st.caption("© 2026 - Tous droits réservés")



# --- ONGLET 2 : STATISTIQUES ---
elif menu == "📊 Statistiques":
    st.title("📊 Analyse Pharmaciel")
    total_produits = len(df_para)
    img_ok = df_para[df_para['image_path'].str.len() > 3].shape[0]
    valeur_stock = (df_para['PPA'] * df_para['Quantité']).sum()
    stock_bas = df_para[df_para['Quantité'] < 5].shape[0]
    promos = df_para[df_para['Promo'] == True].shape[0]
    
    n_cols_stats = 2 if st.session_state.mobile_mode else 4
    c_stats = st.columns(n_cols_stats)
    c_stats[0].metric("📦 Total Produits", total_produits)
    if st.session_state.user_role == "Responsable":
        c_stats[1 % n_cols_stats].metric("💰 Valeur Stock", f"{valeur_stock:,.0f} DA")
    else:
        c_stats[1 % n_cols_stats].metric("💰 Valeur Stock", "---")
    c_stats[2 % n_cols_stats].metric("🖼️ Taux Images", f"{int((img_ok/total_produits)*100)}%" if total_produits > 0 else "0%")
    c_stats[3 % n_cols_stats].metric("⚠️ Alertes Stock", stock_bas, delta=-stock_bas, delta_color="inverse")

    if st.session_state.user_role == "Responsable":
        st.divider()
        st.subheader("💰 Performance Financière")
        df_sales = pd.read_csv(SALES_DB) if os.path.exists(SALES_DB) else pd.DataFrame()
        if not df_sales.empty:
            ca_total = df_sales['Total'].sum()
            nb_ventes = len(df_sales)
            col_f1, col_f2 = st.columns(2)
            col_f1.metric("🏧 Chiffre d'Affaires Cumulé", f"{ca_total:,.0f} DA")
            col_f2.metric("🧾 Nombre de Ventes", nb_ventes)
        else:
            st.info("Aucune vente enregistrée pour le moment.")
    
    st.divider()
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📦 Top 10 Laboratoires")
        labo_counts = df_para['Laboratoire'].value_counts().head(10).sort_values()
        fig_labo = go.Figure(go.Bar(
            x=labo_counts.values,
            y=labo_counts.index,
            orientation='h',
            marker=dict(
                color=labo_counts.values,
                colorscale=[[0, 'rgba(56,189,248,0.3)'], [1, 'rgba(56,189,248,1)']],
                line=dict(color='rgba(56,189,248,0.5)', width=1)
            ),
            text=labo_counts.values,
            textposition='outside',
            textfont=dict(size=11)
        ))
        fig_labo.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=30, t=10, b=10),
            height=320,
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', showticklabels=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=11)),
            font=dict(color='rgba(200,210,230,0.9)')
        )
        st.plotly_chart(fig_labo, use_container_width=True)

    with col_chart2:
        st.subheader("🏷️ Répartition par Famille")
        famille_counts = df_para['Famille'].value_counts().head(8)
        colors_donut = ['#38bdf8','#c084fc','#10b981','#f59e0b','#ef4444','#a78bfa','#34d399','#fb7185']
        fig_famille = go.Figure(go.Pie(
            labels=famille_counts.index,
            values=famille_counts.values,
            hole=0.55,
            marker=dict(
                colors=colors_donut,
                line=dict(color='rgba(0,0,0,0.3)', width=2)
            ),
            textfont=dict(size=11),
            hovertemplate='<b>%{label}</b><br>%{value} produits (%{percent})<extra></extra>'
        ))
        fig_famille.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            height=320,
            legend=dict(
                font=dict(size=10, color='rgba(200,210,230,0.9)'),
                bgcolor='rgba(0,0,0,0)'
            ),
            annotations=[dict(
                text=f'<b>{total_produits}</b><br>produits',
                x=0.5, y=0.5, font_size=14,
                showarrow=False,
                font=dict(color='rgba(200,210,230,0.9)')
            )]
        )
        st.plotly_chart(fig_famille, use_container_width=True)
    
    # Stock health bar chart
    st.divider()
    st.subheader("📉 Santé des Stocks par Famille")
    stock_by_famille = df_para.groupby('Famille')['Quantité'].sum().sort_values(ascending=False).head(10)
    fig_stock = go.Figure(go.Bar(
        x=stock_by_famille.index,
        y=stock_by_famille.values,
        marker=dict(
            color=stock_by_famille.values,
            colorscale=[[0, 'rgba(239,68,68,0.7)'], [0.5, 'rgba(245,158,11,0.7)'], [1, 'rgba(16,185,129,0.9)']],
            line=dict(color='rgba(255,255,255,0.1)', width=1)
        ),
        text=stock_by_famille.values,
        textposition='outside',
    ))
    fig_stock.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=10, b=80),
        height=300,
        xaxis=dict(showgrid=False, tickangle=-30, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)'),
        font=dict(color='rgba(200,210,230,0.9)')
    )
    st.plotly_chart(fig_stock, use_container_width=True)

# --- ONGLET 3 : ADMIN ---
elif menu == "⚙️ Admin":
    st.title("⚙️ Administration & Configuration")
    
    # 1. PARAMÈTRES GLOBAUX (Visible uniquement par Responsable)
    if st.session_state.user_role == "Responsable":
        with st.expander("🌐 Paramètres de l'Application", expanded=True):
            st.subheader("Bandeau & IA")
            new_msg = st.text_area("Message défilant (Marquee)", value=settings.get('marquee', ''))
            
            st.divider()
            st.markdown("### 🤖 Configuration de l'Intelligence Artificielle")
            
            ai_provider = st.radio("Fournisseur AI Actif", ["Google Gemini", "OpenRouter"], 
                                   index=0 if settings.get('ai_provider', 'Google Gemini') == "Google Gemini" else 1,
                                   horizontal=True)
            
            col_keys1, col_keys2 = st.columns(2)
            with col_keys1:
                new_gemini = st.text_input("Clé Google Gemini (AI Studio)", value=settings.get('gemini_key', ''), type="password")
            with col_keys2:
                new_openrouter = st.text_input("Clé OpenRouter (sk-or-...)", value=settings.get('openrouter_key', ''), type="password")
            
            ai_active = st.toggle("Activer l'assistant IA pour les clients", value=settings.get('ai_active', True))
            
            st.write("---")
            st.markdown("#### ⚙️ Choix du Modèle")
            ai_models = {
                "gemini-1.5-flash": "⚡ Gemini Flash (Rapide & Gratuit)",
                "gemini-1.5-pro": "🧠 Gemini Pro (Plus intelligent)",
                "gpt-4o-mini": "🚀 GPT-4o Mini (OpenRouter uniquement)",
                "claude-3-haiku": "🎨 Claude Haiku (OpenRouter uniquement)"
            }
            curr_model = settings.get('ai_model', 'gemini-1.5-flash')
            if curr_model not in ai_models: curr_model = "gemini-1.5-flash"
            
            new_model = st.selectbox("Modèle à utiliser", options=list(ai_models.keys()), 
                                    format_func=lambda x: ai_models[x], 
                                    index=list(ai_models.keys()).index(curr_model))
            
            if st.button("💾 Enregistrer la Configuration AI", use_container_width=True):
                settings['marquee'] = new_msg
                settings['gemini_key'] = new_gemini
                settings['openrouter_key'] = new_openrouter
                settings['ai_provider'] = ai_provider
                settings['ai_active'] = ai_active
                settings['ai_model'] = new_model
                save_settings(settings)
                st.success("Paramètres IA mis à jour !")
                st.rerun()

    # 2. GESTION ÉQUIPE / MON PROFIL
    u_db = load_users()
    
    if st.session_state.user_role == "Responsable":
        st.subheader("👥 Gestion de l'équipe")
        for index, row in u_db.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([1.5, 1.5, 2, 2, 1])
                with c1: nu = st.text_input("User", value=str(row['user']), key=f"u_{index}")
                with c2: 
                    roles = ["Responsable", "Stock", "Préparateur", "Commercial"]
                    nr = st.selectbox("Rôle", roles, index=roles.index(row['role']) if row['role'] in roles else 1, key=f"r_{index}")
                with c3: nw = st.text_input("WhatsApp", value=str(row.get('whatsapp', '')), placeholder="213...", key=f"w_{index}")
                with c4: ndn = st.text_input("Nom Public", value=str(row.get('display_name', 'Agent Commercial')), key=f"dn_{index}")
                with c5:
                    st.write("")
                    if st.button("💾", key=f"s_{index}"):
                        u_db.at[index, 'user'], u_db.at[index, 'role'], u_db.at[index, 'whatsapp'], u_db.at[index, 'display_name'] = nu, nr, nw, ndn
                        save_data(u_db, USER_DB)
                        st.success("Mis à jour !")
                        st.rerun()
                    if str(row['user']) != "admin":
                        if st.button("🗑️", key=f"d_{index}"):
                            u_db = u_db.drop(index)
                            save_data(u_db, USER_DB)
                            st.rerun()

        with st.expander("➕ Ajouter un collaborateur"):
            with st.form("new_u", clear_on_submit=True):
                nu, np, nr = st.text_input("Nom"), st.text_input("MDP", type="password"), st.selectbox("Rôle", ["Stock", "Préparateur", "Commercial", "Responsable"])
                if st.form_submit_button("Créer"):
                    new_user = pd.DataFrame([{"user": nu, "pw": np, "role": nr, "whatsapp": "", "display_name": "Agent Commercial"}])
                    u_db = pd.concat([u_db, new_user], ignore_index=True)
                    save_data(u_db, USER_DB)
                    st.rerun()
                    
    elif st.session_state.user_role == "Commercial":
        st.subheader("📱 Mon Profil WhatsApp")
        # Trouver la ligne de l'utilisateur actuel
        curr_user = st.session_state.current_user
        idx = u_db[u_db['user'] == curr_user].index
        if not idx.empty:
            index = idx[0]
            row = u_db.loc[index]
            with st.form("my_profile"):
                st.info("Configurez ici votre numéro WhatsApp pour que les clients puissent vous contacter directement.")
                new_w = st.text_input("Mon Numéro WhatsApp (Format: 213550000000)", value=str(row.get('whatsapp', '')))
                new_dn = st.text_input("Mon Nom Public (ex: Agent Commercial 1)", value=str(row.get('display_name', 'Agent Commercial')))
                if st.form_submit_button("Enregistrer mon profil"):
                    u_db.at[index, 'whatsapp'] = new_w
                    u_db.at[index, 'display_name'] = new_dn
                    save_data(u_db, USER_DB)
                    st.success("Profil mis à jour !")
                    st.rerun()

    if st.session_state.user_role == "Responsable":
        st.divider()
        st.subheader("📢 Communication")
        with st.form("settings_form"):
            new_marquee = st.text_input("Message de bienvenue (Bandeau défilant)", value=settings.get('marquee', ''))
            if st.form_submit_button("💾 Enregistrer le message"):
                settings['marquee'] = new_marquee
                save_settings(settings)
                st.success("Message mis à jour !")
                st.rerun()

        st.divider()
        st.subheader("🛠️ Maintenance & Backups")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("💾 Sauvegarder Produits"):
                ts = datetime.now().strftime("%Y%m%d_%H%M")
                shutil.copy(DB_PATH, f"backup_para_{ts}.csv")
                st.success(f"Sauvegardé : backup_para_{ts}.csv")
            if st.button("👥 Sauvegarder Utilisateurs"):
                ts = datetime.now().strftime("%Y%m%d_%H%M")
                shutil.copy(USER_DB, f"backup_users_{ts}.csv")
                st.success("Utilisateurs sauvegardés.")
        with col_b2:
            up_py = st.file_uploader("🚀 Upgrade Système (.py)", type="py")
            if up_py:
                with open(__file__, "wb") as f: f.write(up_py.getbuffer())
                st.success("Système mis à jour !")
        
        st.divider()
        st.subheader("☁️ Checkup Pictures & Sauvegarde Google Drive")
        
        # --- Diagnostic GDrive ---
        try:
            from utils.gdrive_api import get_gdrive_service, get_main_folder_id, get_remote_file_id
            service = get_gdrive_service()
            main_id = get_main_folder_id()
            if service and main_id:
                img_folder_id = get_remote_file_id(service, "image_stock", main_id)
                if img_folder_id:
                    query = f"'{img_folder_id}' in parents and trashed=false"
                    results = service.files().list(q=query, fields='files(id)').execute()
                    nb_drive = len(results.get('files', []))
                    nb_local = len(os.listdir(IMG_DIR)) if os.path.exists(IMG_DIR) else 0
                    
                    c_d1, c_d2 = st.columns(2)
                    c_d1.metric("Photos sur GDrive", nb_drive)
                    c_d2.metric("Photos locales", nb_local)
                    
                    if nb_drive == 0:
                        st.warning("⚠️ Aucune photo trouvée dans le dossier 'image_stock' de Google Drive. Vérifiez le nom du dossier et le contenu.")
                    elif nb_drive > nb_local:
                        st.info(f"💡 Il y a {nb_drive - nb_local} nouvelles photos sur Drive. Cliquez sur 'Checkup' pour les récupérer.")
        except:
            st.error("Impossible de lire les statistiques GDrive pour le moment.")
            
        st.info("Utilisez ces boutons pour synchroniser vos images et données avec le compte Google Drive de l'entreprise.")
        col_g1, col_g2, col_g3 = st.columns(3)
        
        if col_g1.button("⬇️ Checkup (Récupérer de GDrive)", use_container_width=True):
            with st.spinner("Vérification et téléchargement depuis Google Drive..."):
                from utils.gdrive_api import restore_from_gdrive
                success, msg = restore_from_gdrive()
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
                    
        if col_g2.button("⬆️ Sauvegarder vers GDrive", use_container_width=True):
            with st.spinner("Envoi des images et de la base de données vers Google Drive..."):
                from utils.gdrive_api import sync_to_gdrive
                success, msg = sync_to_gdrive()
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

        if col_g3.button("📦 Créer un ZIP (Images)", use_container_width=True):
            with st.spinner("Création de l'archive ZIP..."):
                import shutil
                ts = datetime.now().strftime("%Y%m%d_%H%M")
                zip_name = f"images_backup_{ts}"
                zip_path = os.path.join(BASE_DIR, zip_name)
                shutil.make_archive(zip_path, 'zip', IMG_DIR)
                st.success(f"Archive créée : {zip_name}.zip")
                
                # Option to download the ZIP file directly
                with open(f"{zip_path}.zip", "rb") as fp:
                    st.download_button(
                        label="⬇️ Télécharger le ZIP",
                        data=fp,
                        file_name=f"{zip_name}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
