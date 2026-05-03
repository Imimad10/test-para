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
import json
import google.generativeai as genai
from PIL import Image as PILImage, ImageOps
from streamlit_extras.colored_header import colored_header
from streamlit_extras.mention import mention
from streamlit_extras.add_vertical_space import add_vertical_space

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
            "bg": "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
            "card_bg": "rgba(255, 255, 255, 0.8)",
            "text": "#1e293b",
            "sidebar_bg": "#ffffff",
            "primary": "#007bff",
            "accent": "#0056b3",
            "sidebar_text": "#1e293b",
            "input_bg": "#ffffff",
            "input_text": "#1e293b"
        },
        "Sombre Élite 🌙": {
            "bg": "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
            "card_bg": "rgba(30, 41, 59, 0.7)",
            "text": "#f8fafc",
            "sidebar_bg": "#0f172a",
            "primary": "#38bdf8",
            "accent": "#0ea5e9",
            "sidebar_text": "#f8fafc",
            "input_bg": "#334155",
            "input_text": "#f8fafc"
        },
        "Émeraude Royal 👑": {
            "bg": "linear-gradient(135deg, #064e3b 0%, #022c22 100%)",
            "card_bg": "rgba(6, 78, 59, 0.6)",
            "text": "#ecfdf5",
            "sidebar_bg": "#022c22",
            "primary": "#fbbf24",
            "accent": "#f59e0b",
            "sidebar_text": "#fbbf24",
            "input_bg": "rgba(255, 255, 255, 0.1)",
            "input_text": "#ffffff"
        },
        "Aurore Boréale 🌌": {
            "bg": "linear-gradient(135deg, #4c1d95 0%, #1e1b4b 100%)",
            "card_bg": "rgba(30, 27, 75, 0.6)",
            "text": "#f5f3ff",
            "sidebar_bg": "#1e1b4b",
            "primary": "#a78bfa",
            "accent": "#8b5cf6",
            "sidebar_text": "#f5f3ff",
            "input_bg": "rgba(255, 255, 255, 0.1)",
            "input_text": "#ffffff"
        },
        "Cyberpunk ⚡": {
            "bg": "linear-gradient(135deg, #000000 0%, #09090b 100%)",
            "card_bg": "rgba(20, 20, 20, 0.9)",
            "text": "#00ff9f",
            "sidebar_bg": "#000000",
            "primary": "#ff003c",
            "accent": "#05d9e8",
            "sidebar_text": "#05d9e8",
            "input_bg": "#111111",
            "input_text": "#00ff9f"
        },
        "Antigravity Dark 🌌": {
            "bg": "linear-gradient(135deg, #020617 0%, #0f172a 100%)",
            "card_bg": "rgba(15, 23, 42, 0.4)",
            "text": "#f8fafc",
            "sidebar_bg": "#020617",
            "primary": "#38bdf8",
            "accent": "#818cf8",
            "sidebar_text": "#38bdf8",
            "input_bg": "#1e293b",
            "input_text": "#f8fafc"
        }
    }
    
    t = themes.get(theme_choice, themes["Clair Modern ❄️"])
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Orbitron:wght@400;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Outfit', 'Segoe UI Emoji', sans-serif;
        }}
        
        {".stApp { font-family: 'Orbitron', 'Segoe UI Emoji', sans-serif !important; }" if theme_choice == "Cyberpunk ⚡" else ""}

        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background: {t['bg']} !important;
            background-attachment: fixed !important;
            color: {t['text']} !important;
        }}
        
        {"""
        h1, h2, h3, .stHeader {
            color: #38bdf8 !important;
            font-weight: 700;
        }
        [data-testid="stMetricValue"] {
            color: #38bdf8 !important;
        }
        """ if theme_choice == "Antigravity Dark 🌌" else ""}
        
        /* Typography Fixes */
        [data-testid="stHeader"] {{
            background: transparent !important;
        }}
        
        label, .stMarkdown p, .stText, .stCaption, [data-testid="stWidgetLabel"] p {{
            color: {t['text']} !important;
            opacity: 1 !important;
        }}
        
        /* Navigation Radio Buttons */
        div[data-testid="stHorizontalRadio"] label p {{
            color: {t['text']} !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
        }}

        /* Promotion Marquee */
        .marquee {{
            width: 100%;
            overflow: hidden;
            background: {t['primary']};
            color: {t['sidebar_bg']};
            padding: 8px 0;
            font-weight: bold;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
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

        /* Glassmorphism for Containers */
        [data-testid="stVerticalBlock"] > div > div > div > div.stColumn, .stContainer, div[data-testid="stExpander"] {{
            border-radius: 15px !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
            background: {t['card_bg']} !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        
        /* Shine Effect on Hover */
        [data-testid="stVerticalBlock"] > div > div > div > div.stColumn::after {{
            content: '';
            position: absolute;
            top: 0; left: -150%;
            width: 50%; height: 100%;
            background: linear-gradient(to right, rgba(255,255,255,0) 0%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0) 100%);
            transform: skewX(-25deg);
            transition: 0.75s;
        }}
        
        [data-testid="stVerticalBlock"] > div > div > div > div.stColumn:hover::after {{
            left: 150%;
        }}

        [data-testid="stVerticalBlock"] > div > div > div > div.stColumn:hover {{
            transform: translateY(-8px) scale(1.02);
            border-color: {t['primary']} !important;
        }}
        
        /* Buttons */
        .stButton > button {{
            border-radius: 12px !important;
            font-weight: 600 !important;
            background-color: {t['primary']} !important;
            color: {t['sidebar_bg']} !important;
            border: none !important;
            padding: 0.6rem 1.2rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stButton > button:hover {{
            background-color: {t['accent']} !important;
            transform: translateY(-2px) scale(1.05) !important;
            box-shadow: 0 8px 15px rgba(0,0,0,0.2) !important;
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {t['sidebar_bg']} !important;
            border-right: 1px solid rgba(255,255,255,0.1);
        }}
        
        /* Inputs & Selects Visibility Fix */
        div[data-baseweb="select"], div[data-baseweb="input"], div[data-baseweb="textarea"] {{
            background-color: {t['input_bg']} !important;
            border-radius: 10px !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
        }}
        
        div[data-baseweb="select"] *, div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {{
            color: {t['input_text']} !important;
        }}

        /* Placeholder visibility */
        input::placeholder, textarea::placeholder {{
            color: {t['input_text']} !important;
            opacity: 0.7 !important;
        }}
        
        /* Metric customization */
        [data-testid="stMetricValue"] {{
            color: {t['primary']} !important;
            font-weight: 700;
            text-shadow: 0 0 10px rgba(0,0,0,0.2);
        }}
        
        /* Fixed Height Cards for Grid only (exclude dialogs) */
        div[data-testid="stVerticalBlock"] > div > div > div > div.stColumn > div:not([data-testid="stDialog"]) {{
             min-height: 420px !important;
             display: flex;
             flex-direction: column;
             justify-content: space-between;
        }}

        /* Default for Catalog: Force uniform height and look */
        [data-testid="column"] img {{
            height: 220px !important;
            width: 100% !important;
            object-fit: contain !important;
            background-color: white !important; /* Standardize background for images with transparency */
            border-radius: 12px !important;
            padding: 10px !important;
            border: 1px solid rgba(0,0,0,0.05) !important;
            transition: transform 0.3s ease !important;
        }}

        [data-testid="column"] img:hover {{
            transform: scale(1.05);
        }}

        /* EXCEPTION for Dialogs (Details): Allow full size */
        [data-testid="stDialog"] img, 
        [data-testid="stDialog"] [data-testid="column"] img {{
            height: auto !important;
            max-height: 70vh !important;
            width: auto !important;
            max-width: 100% !important;
            object-fit: scale-down !important;
            background: transparent !important;
            border: none !important;
            padding: 0px !important;
        }}

        /* Headers */
        h1, h2, h3 {{
            font-weight: 700 !important;
            letter-spacing: -1px;
            color: {t['primary']} !important;
            margin-bottom: 0.5rem !important;
        }}
        
        .stMarkdown p {{
            color: {t['text']} !important;
            margin-bottom: 0px !important;
        }}
        
        /* Custom PDF Button */
        div.stDownloadButton > button {{
            background-color: #e63946 !important;
            color: white !important;
            border: none !important;
        }}
        
        /* Toggle Styling */
        div[data-testid="stToggle"] p {{
            color: {t['text']} !important;
            font-weight: 600 !important;
        }}
        
        /* Selectbox and Input Labels */
        .stSelectbox label p, .stTextInput label p, .stNumberInput label p {{
            color: {t['text']} !important;
            font-weight: 600 !important;
        }}

        /* --- OPTIMISATIONS MOBILE --- */
        @media (max-width: 768px) {{
            [data-testid="stSidebar"] {{
                width: 80vw !important;
            }}
            .stMetric {{
                padding: 10px !important;
            }}
            [data-testid="stMetricValue"] {{
                font-size: 1.5rem !important;
            }}
            h1 {{ font-size: 1.8rem !important; }}
            h2 {{ font-size: 1.4rem !important; }}
            
            /* Ajustement des cartes en mode mobile */
            div[data-testid="stVerticalBlock"] > div > div > div > div.stColumn {{
                min-height: auto !important;
                padding: 1rem !important;
            }}
        }}
        /* Floating WhatsApp Button */
        .whatsapp-float {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background-color: #25d366;
            color: white !important;
            border-radius: 50px;
            text-align: center;
            width: 60px;
            height: 60px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            text-decoration: none;
            transition: all 0.3s ease;
        }}
        .whatsapp-float:hover {{
            transform: scale(1.1);
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
        <svg width="35" height="35" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M12.031 0C5.385 0 0 5.386 0 12.03c0 2.12.551 4.198 1.597 6.02L.031 24l6.105-1.603a11.972 11.972 0 0 0 5.895 1.543h.005c6.645 0 12.03-5.387 12.03-12.032C24.066 5.386 18.679 0 12.031 0zm0 21.968h-.005a9.963 9.963 0 0 1-5.075-1.378l-.364-.216-3.771.99.998-3.676-.237-.377a9.96 9.96 0 0 1-1.526-5.283c0-5.5 4.476-9.975 9.98-9.975 5.503 0 9.978 4.475 9.978 9.975s-4.475 9.975-9.978 9.975zm5.474-7.48c-.3-.15-1.776-.876-2.052-.976-.275-.101-.476-.15-.676.15-.2.302-.776.977-.951 1.177-.175.201-.351.226-.651.076a8.212 8.212 0 0 1-2.417-1.493 9.07 9.07 0 0 1-1.68-2.09c-.176-.301-.019-.464.131-.614.136-.135.301-.351.451-.526.151-.176.2-.301.302-.501.101-.201.05-.376-.025-.526-.075-.15-.676-1.63-.926-2.23-.243-.585-.49-.505-.676-.514-.175-.008-.376-.008-.576-.008s-.526.075-.801.376c-.275.301-1.052 1.028-1.052 2.508 0 1.48 1.077 2.91 1.227 3.111.15.2 2.122 3.238 5.14 4.542.718.309 1.278.494 1.716.632.72.228 1.375.195 1.894.118.58-.086 1.776-.726 2.026-1.428.25-.702.25-1.304.175-1.429-.075-.126-.275-.201-.575-.351z"/></svg>
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
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img = ImageOps.fit(img, size, PILImage.Resampling.LANCZOS)
        if not target_path.lower().endswith('.jpg'):
            target_path = os.path.splitext(target_path)[0] + ".jpg"
        img.save(target_path, "JPEG", quality=85)
        return os.path.basename(target_path)
    except Exception as e:
        st.error(f"Erreur de traitement image : {e}")
        return None

def get_image_base64(filename):
    if not filename or str(filename).lower() in ['nan', '']: return None
    path = os.path.join(IMG_DIR, str(filename).strip())
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
        st.title("🔐 Pharmaciel Pro")
        st.success("👋 Vous êtes client ? Accédez directement à notre catalogue sans identifiant.")
        if st.button("🌐 VOIR LE CATALOGUE PRODUITS", type="primary", use_container_width=True):
            st.session_state.auth, st.session_state.user_role, st.session_state.current_user = True, "Client", "Visiteur"
            add_log("Accès Visiteur")
            st.rerun()
        
        st.divider()
        with st.expander("🔑 Espace Collaborateur (Connexion)", expanded=False):
            with st.form("login_form"):
                u = st.text_input("Identifiant")
                p = st.text_input("Mot de passe", type="password")
                remember = st.checkbox("Rester connecté")
                if st.form_submit_button("Se connecter"):
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
                    else: st.error("Identifiants incorrects.")
        st.stop()

# --- 4. INTERFACE ---
login()
df_para = load_data()

# --- SIDEBAR : NAVIGATION & FILTRES ---
with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.current_user}")
    if st.session_state.user_role != "Client":
        st.write(f"Rôle : **{st.session_state.user_role}**")
    
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
        
        if st.button("🔄 Réinitialiser tous les filtres", use_container_width=True):
            st.session_state.page = 1
            # On peut utiliser st.rerun() pour tout remettre à zéro si on utilise des clés
            # Mais ici on va juste inciter l'utilisateur à vider la recherche
            st.info("Filtres réinitialisés. Veuillez effacer le champ de recherche si nécessaire.")
            st.rerun()
            
        st.divider()
        pdf_buf = generate_pdf_catalogue(df_para)
        st.download_button("📄 PDF Catalogue", pdf_buf, "Catalogue_Pharmaciel.pdf", "application/pdf", use_container_width=True)
        
        # Bouton Flyer Promo
        promo_df = df_para[df_para['Promo'] == True]
        if not promo_df.empty:
            promo_buf = generate_promo_flyer(df_para)
            st.download_button("🔥 Télécharger Flyer PROMO", promo_buf, "Promotions_Pharmaciel.pdf", "application/pdf", use_container_width=True)

    st.divider()

    # Panier Sidebar
    if st.session_state.cart:
        st.subheader("🛒 Votre Panier")
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
            
        st.write(f"**Total : {total_panier} DA**")
        msg_cart = f"Bonjour Pharmaciel, je souhaite commander :\n" + "\n".join([f"- {k} (x{v['qty']})" for k,v in st.session_state.cart.items()])
        st.link_button("🚀 Envoyer WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg_cart)}", use_container_width=True)
        if st.button("🗑️ Vider le panier", use_container_width=True):
            st.session_state.cart = {}
            st.rerun()
        st.divider()

    # Thème & Déconnexion
    with st.expander("🎨 Personnalisation", expanded=False):
        theme_list = ["Clair Modern ❄️", "Sombre Élite 🌙", "Émeraude Royal 👑", "Aurore Boréale 🌌", "Cyberpunk ⚡", "Antigravity Dark 🌌"]
        new_theme = st.selectbox("Changer l'ambiance", 
                                theme_list, 
                                index=theme_list.index(st.session_state.theme))
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()
            
    if st.button("🚪 Déconnexion", type="secondary", use_container_width=True):
        st.session_state.auth = False
        st.session_state.user_role = None
        st.session_state.current_user = None
        st.rerun()

# --- DIALOGUE DÉTAILS ---
@st.dialog("Fiche Produit", width="large")
def show_details(row):
    # Responsive columns for dialog
    n_cols_dialog = 1 if st.session_state.mobile_mode else 2
    cols_dialog = st.columns(n_cols_dialog)
    
    img = get_image_base64(row['image_path'])
    with cols_dialog[0]:
        if img: st.image(img)
        else: st.warning("Image manquante")
    
    # If mobile, we use the same column (cols_dialog[0]), else the second one
    target_col = cols_dialog[0] if st.session_state.mobile_mode else cols_dialog[1]
    
    with target_col:
        st.header(row['Produit'])
        st.write(f"**🔬 Labo :** {row['Laboratoire']}")
        st.write(f"**📅 DDP :** {row['DDP']}")
        if 'Arrivage' in row and row['Arrivage']: st.write(f"**🚚 Arrivage :** {row['Arrivage']}")
        if 'Dépôt' in row and row['Dépôt']: st.write(f"**🏠 Dépôt :** {row['Dépôt']}")
        
        if st.session_state.user_role == "Responsable":
            st.write(f"**📦 Stock :** {row['Quantité']} unités")
            val_tot = float(row['PPA']) * float(row['Quantité'])
            st.write(f"**💰 Valeur Stock :** {val_tot:,.2f} DA")
            st.write(f"**💳 Prix Achat :** {row['Prix_Achat']} DA")
            st.write(f"**📈 Marge :** {(float(row['PPA']) - float(row['Prix_Achat'])):.2f} DA")
        
        st.divider()
        if row['Description']:
            st.info(f"📝 **Description** : {row['Description']}")
            st.divider()
        p_text = f"{row['PPA']} DA" if row['PPA'] > 0 else "Prix sur demande"
        st.metric("Prix Unitaire", p_text)
        msg = urllib.parse.quote(f"Pharmaciel - {row['Produit']} | Prix: {row['PPA']} DA")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" style="background-color:#25D366; color:white; padding:10px; border-radius:5px; text-decoration:none; display:block; text-align:center;">Partager WhatsApp</a>', unsafe_allow_html=True)

        # --- ASSISTANT IA CONSEIL ---
        if settings.get('ai_active', True):
            st.divider()
            with st.expander("🤖 Assistant Expert IA (Conseils)", expanded=True):
                st.chat_message("assistant").write(f"Bonjour ! Je suis votre conseiller **Pharmaciel AI**. Je connais très bien le produit **{row['Produit']}** du laboratoire **{row['Laboratoire']}**. Comment puis-je vous aider ?")
                
                # Récupération de la clé API Gemini depuis les settings
                api_key = settings.get('gemini_key', '')
                
                # Champ de question
                q_key = f"ai_query_{row['Produit']}_{row['Laboratoire']}"
                user_q = st.text_input("Posez votre question ici...", key=q_key, placeholder="Ex: C'est pour quel type de peau ? Routine conseillée ?")
                
                if user_q:
                    with st.spinner("L'expert IA analyse votre demande..."):
                        if api_key:
                            try:
                                api_key = api_key.strip()
                                genai.configure(api_key=api_key)
                                
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
                                
                                # Utilisation du modèle choisi par l'admin ou défaut sur Flash
                                target_model = settings.get('ai_model', 'gemini-1.5-flash')
                                
                                model = genai.GenerativeModel(target_model)
                                response = model.generate_content(prompt)
                                r = response.text
                            except Exception as e:
                                e_str = str(e)
                                if "429" in e_str:
                                    r = "⚠️ **Limite de quota atteinte** : Le service AI est très sollicité ou vous utilisez une clé gratuite limitée. Veuillez patienter 60 secondes ou vérifiez vos quotas sur Google AI Studio."
                                elif "403" in e_str or "API_KEY_INVALID" in e_str:
                                    r = "⚠️ **Clé API Invalide** : La clé configurée dans l'onglet Admin n'est pas reconnue par Google. Assurez-vous qu'elle est correcte."
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
                        
                        st.chat_message("user").write(user_q)
                        st.chat_message("assistant").write(f"✨ **Réponse de l'expert :** {r}")
                        add_log("Question IA", f"Produit: {row['Produit']} | Q: {user_q}")

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
                                img = get_image_base64(row['image_path'])
                                if img: st.image(img, use_container_width=True)
                                
                                # Badges compacts
                                badge_html = ""
                                if st.session_state.user_role != "Client" and row['Quantité'] < 5: 
                                    badge_html += '<span style="background:rgba(255,0,0,0.1); color:red; padding:2px 6px; border-radius:4px; font-size:10px; margin-right:5px;">⚠️ Stock Bas</span>'
                                if row['Promo']: 
                                    badge_html += '<span style="background:rgba(255,165,0,0.1); color:orange; padding:2px 6px; border-radius:4px; font-size:10px;">🔥 PROMO</span>'
                                if badge_html: st.markdown(f'<div style="margin-bottom:5px;">{badge_html}</div>', unsafe_allow_html=True)
                                
                                st.markdown(f"**{row['Produit']}**")
                                p_disp = f"{row['PPA']} DA" if row['PPA'] > 0 else "Prix sur demande"
                                st.markdown(f"### {p_disp}")
                                
                                c_b1, c_b2 = st.columns(2)
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
                                        st.success(f"Image 800x800 liée à {sel_prod}")
                                        st.rerun()
                    with c2:
                        st.info("Recherche rapide")
                        st.link_button("🌐 Chercher sur Google Images", f"https://www.google.com/search?tbm=isch&q={sel_prod.replace(' ','+')}")

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
                        with st.form("form_replace_img", clear_on_submit=True):
                            new_up = st.file_uploader("Nouvelle image (Auto-resize 800x800)", type=['png', 'jpg', 'jpeg'], key="replace_up")
                            if st.form_submit_button("💾 Enregistrer la nouvelle image"):
                                if new_up:
                                    fname = f"{clean_filename(sel_prod)}.jpg"
                                    saved_name = resize_and_save_image(new_up, os.path.join(IMG_DIR, fname))
                                    if saved_name:
                                        df_para.loc[df_para['Produit'] == sel_prod, 'image_path'] = saved_name
                                        save_data(df_para)
                                        st.success("Image mise à jour en 800x800 !")
                                        st.rerun()
            
            else: # IMPORT GROUPÉ
                st.info("💡 **Astuce** : Nommez vos images exactement comme vos produits (ex: `DOLIPRANE.jpg`). Le système les liera automatiquement !")
                with st.form("form_bulk_img", clear_on_submit=True):
                    bulk_files = st.file_uploader("Glissez toutes vos images ici", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
                    
                    if st.form_submit_button(f"🚀 Lier les images sélectionnées"):
                        if bulk_files:
                            count = 0
                            for f in bulk_files:
                                prod_name_guess = f.name.split('.')[0].upper().replace('_', ' ')
                                clean_guess = clean_filename(prod_name_guess)
                                match = df_para[df_para['Produit'].apply(clean_filename) == clean_guess]
                                if not match.empty:
                                    fname = f"{clean_guess}.jpg"
                                    saved_name = resize_and_save_image(f, os.path.join(IMG_DIR, fname))
                                    if saved_name:
                                        df_para.loc[df_para['Produit'].apply(clean_filename) == clean_guess, 'image_path'] = saved_name
                                        count += 1
                            save_data(df_para)
                            st.success(f"✅ {count} images liées automatiquement !")
                            add_log("Import Groupé Images", f"{count} images")
                            st.rerun()
            
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
            st.subheader("🔄 Synchronisation Base de Données")
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
    
    n_cols_stats = 2 if st.session_state.mobile_mode else 4
    c_stats = st.columns(n_cols_stats)
    c_stats[0].metric("Total Produits", total_produits)
    if st.session_state.user_role == "Responsable":
        c_stats[1 % n_cols_stats].metric("Valeur Stock", f"{valeur_stock:,.0f} DA")
    else:
        c_stats[1 % n_cols_stats].metric("Valeur Stock", "---")
    c_stats[2 % n_cols_stats].metric("Taux Images", f"{int((img_ok/total_produits)*100)}%" if total_produits > 0 else "0%")
    c_stats[3 % n_cols_stats].metric("Alertes Stock", stock_bas, delta=-stock_bas, delta_color="inverse")
    
    if st.session_state.user_role == "Responsable":
        st.divider()
        st.subheader("💰 Performance Financière")
        df_sales = pd.read_csv(SALES_DB) if os.path.exists(SALES_DB) else pd.DataFrame()
        if not df_sales.empty:
            ca_total = df_sales['Total'].sum()
            nb_ventes = len(df_sales)
            col_f1, col_f2 = st.columns(2)
            col_f1.metric("Chiffre d'Affaires Cumulé", f"{ca_total:,.0f} DA")
            col_f2.metric("Nombre de Ventes", nb_ventes)
        else:
            st.info("Aucune vente enregistrée pour le moment.")
    
    st.divider()
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("📦 Top 10 Laboratoires")
        labo_counts = df_para['Laboratoire'].value_counts().head(10)
        st.bar_chart(labo_counts)
    with col_chart2:
        st.subheader("🏷️ Répartition par Famille")
        famille_counts = df_para['Famille'].value_counts()
        st.bar_chart(famille_counts)

# --- ONGLET 3 : ADMIN ---
elif menu == "⚙️ Admin":
    st.title("⚙️ Administration & Configuration")
    
    # 1. PARAMÈTRES GLOBAUX (Visible uniquement par Responsable)
    if st.session_state.user_role == "Responsable":
        with st.expander("🌐 Paramètres de l'Application", expanded=True):
            st.subheader("Bandeau & IA")
            new_msg = st.text_area("Message défilant (Marquee)", value=settings.get('marquee', ''))
            
            st.divider()
            st.markdown("### 🤖 Intelligence Artificielle (Google Gemini)")
            st.info("Pour des réponses intelligentes, obtenez une clé gratuite sur [Google AI Studio](https://aistudio.google.com/app/apikey)")
            
            c_ai1, c_ai2 = st.columns([2, 1])
            with c_ai1:
                new_gemini = st.text_input("Clé API Gemini", value=settings.get('gemini_key', ''), type="password")
            with c_ai2:
                ai_active = st.toggle("Activer l'IA", value=settings.get('ai_active', True))
            
            st.write("---")
            st.markdown("#### ⚙️ Choix du Modèle")
            ai_models = {
                "gemini-1.5-flash": "⚡ Flash (Recommandé - Gratuit & Rapide)",
                "gemini-1.5-pro": "🧠 Pro (Avancé - Plus intelligent, Quotas limités)",
                "gemini-1.0-pro": "📦 Legacy (Ancien modèle)"
            }
            curr_model = settings.get('ai_model', 'gemini-1.5-flash')
            # Fallback si le modèle actuel n'est plus dans la liste
            if curr_model not in ai_models: curr_model = "gemini-1.5-flash"
            
            new_model = st.selectbox("Modèle à utiliser", options=list(ai_models.keys()), 
                                    format_func=lambda x: ai_models[x], 
                                    index=list(ai_models.keys()).index(curr_model))
            
            st.caption("💡 **Conseil** : Le modèle **Flash** est parfait pour le conseil client et reste gratuit avec des limites généreuses. Le modèle **Pro** est à utiliser si vous avez besoin d'analyses très complexes.")

            if st.button("💾 Enregistrer les Paramètres IA", use_container_width=True):
                settings['marquee'] = new_msg
                settings['gemini_key'] = new_gemini
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
        st.subheader("☁️ Checkup Pictures & Sauvegarde GitHub")
        st.info("Utilisez ces boutons pour synchroniser vos images avec le dépôt GitHub.")
        col_g1, col_g2, col_g3 = st.columns(3)
        
        if col_g1.button("⬇️ Checkup (Récupérer de GitHub)", use_container_width=True):
            with st.spinner("Vérification des nouvelles images sur GitHub..."):
                import subprocess
                try:
                    res = subprocess.run(["git", "pull"], cwd=BASE_DIR, capture_output=True, text=True)
                    st.success("Checkup terminé ! \n\n" + res.stdout)
                except Exception as e:
                    st.error(f"Erreur : {e}")
                    
        if col_g2.button("⬆️ Sauvegarder vers GitHub", use_container_width=True):
            with st.spinner("Envoi des images et de la base de données vers GitHub..."):
                import subprocess
                try:
                    subprocess.run(["git", "add", "images_stock/", "database_para.csv", "paratest.py"], cwd=BASE_DIR)
                    subprocess.run(["git", "commit", "-m", f"Backup automatique via app le {datetime.now().strftime('%Y-%m-%d %H:%M')}"], cwd=BASE_DIR)
                    res = subprocess.run(["git", "push"], cwd=BASE_DIR, capture_output=True, text=True)
                    if "Everything up-to-date" in res.stdout or "Everything up-to-date" in res.stderr:
                        st.info("Rien de nouveau à sauvegarder. Tout est à jour.")
                    else:
                        st.success("Backup GitHub réussi ! \n\n" + res.stdout + res.stderr)
                except Exception as e:
                    st.error(f"Erreur : {e}")

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
