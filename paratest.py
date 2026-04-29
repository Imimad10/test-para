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

# --- 3. DESIGN SYSTEM DYNAMIQUE (THEMES) ---
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
        }
    }
    
    t = themes.get(theme_choice, themes["Clair Modern ❄️"])
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Orbitron:wght@400;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Outfit', sans-serif;
        }}
        
        {".stApp { font-family: 'Orbitron', sans-serif !important; }" if theme_choice == "Cyberpunk ⚡" else ""}

        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background: {t['bg']} !important;
            background-attachment: fixed !important;
            color: {t['text']} !important;
        }}
        
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
        
        /* Headers */
        h1, h2, h3 {{
            font-weight: 700 !important;
            letter-spacing: -1px;
            background: linear-gradient(90deg, {t['primary']}, {t['accent']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .stMarkdown p {{
            color: {t['text']} !important;
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
    </style>
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

def load_data():
    cols = ['Produit', 'Laboratoire', 'Quantité', 'PPA', 'image_path', 'Famille', 'DDP', 'Promo', 'Prix_Achat', 'Description', 'Dépôt', 'Arrivage']
    if not os.path.exists(DB_PATH): return pd.DataFrame(columns=cols)
    try:
        df = pd.read_csv(DB_PATH, encoding='utf-8-sig')
        
        # Renommage flexible pour supporter plusieurs formats d'export
        rename_map = {
            'Quantité  Dépot': 'Quantité', 
            'Quantité Dépot': 'Quantité',
            'Quantité Dépôt': 'Quantité',
            'Fournisseur': 'Famille',
            'Prix': 'PPA'
        }
        df = df.rename(columns=rename_map)
        
        # Gestion des colonnes dupliquées
        df = df.loc[:, ~df.columns.duplicated()]
        
        for c in cols:
            if c not in df.columns: 
                if c == 'Promo': df[c] = False
                elif c in ['Prix_Achat', 'PPA', 'Quantité']: df[c] = 0
                else: df[c] = ""
            
        # Nettoyage numérique
        df['PPA'] = pd.to_numeric(df['PPA'], errors='coerce').fillna(0)
        df['Prix_Achat'] = pd.to_numeric(df['Prix_Achat'], errors='coerce').fillna(0)
        df['Quantité'] = pd.to_numeric(df['Quantité'], errors='coerce').fillna(0)
        df['Promo'] = df['Promo'].astype(bool)
        
        # --- REGROUPEMENT INTELLIGENT ---
        # On groupe par Produit et PPA pour sommer les quantités
        # On garde la DDP la plus proche ou la première rencontrée
        agg_rules = {c: 'first' for c in df.columns if c not in ['Produit', 'PPA', 'Quantité']}
        agg_rules['Quantité'] = 'sum'
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

def load_users():
    if not os.path.exists(USER_DB):
        df_init = pd.DataFrame([{"user": "admin", "pw": "1992", "role": "Responsable"}])
        df_init.to_csv(USER_DB, index=False)
        return df_init
    try:
        return pd.read_csv(USER_DB, dtype={'user': str, 'pw': str, 'role': str})
    except:
        return pd.DataFrame([{"user": "admin", "pw": "1992", "role": "Responsable"}])

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
    
    st.divider()
    
    # Navigation
    if st.session_state.user_role == "Client":
        nav_options = ["📦 Catalogue", "🛒 Mon Panier"]
    else:
        nav_options = ["📦 Stock & Catalogue", "🛒 Commandes Client", "📊 Statistiques"]
        if st.session_state.user_role == "Responsable": nav_options.append("⚙️ Admin")
    
    menu = st.radio("Navigation", nav_options)
    
    st.divider()
    
    # Filtres
    with st.expander("🎯 Filtres & Recherche", expanded=True):
        f_famille = st.selectbox("Famille", ["Toutes"] + sorted([f for f in df_para['Famille'].unique() if f]))
        f_labo = st.selectbox("Laboratoire", ["Tous"] + sorted([l for l in df_para['Laboratoire'].unique() if l]))
        f_alerte = st.selectbox("Alertes Stock/DDP", ["Aucune", "Stock Bas (<5)", "Péremption Proche"])
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
        new_theme = st.selectbox("Changer l'ambiance", 
                                ["Clair Modern ❄️", "Sombre Élite 🌙", "Émeraude Royal 👑", "Aurore Boréale 🌌", "Cyberpunk ⚡"], 
                                index=["Clair Modern ❄️", "Sombre Élite 🌙", "Émeraude Royal 👑", "Aurore Boréale 🌌", "Cyberpunk ⚡"].index(st.session_state.theme))
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
    c1, c2 = st.columns(2)
    img = get_image_base64(row['image_path'])
    with c1:
        if img: st.image(img, use_container_width=True)
        else: st.warning("Image manquante")
    with c2:
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
                            genai.configure(api_key=api_key)
                            model = genai.GenerativeModel('gemini-pro')
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
                            response = model.generate_content(prompt)
                            r = response.text
                        except:
                            r = f"Désolé, une erreur technique est survenue avec l'IA. (Vérifiez votre clé API dans l'onglet Admin)."
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

# --- ONGLET 1 : CATALOGUE ---
if menu in ["📦 Stock & Catalogue", "📦 Catalogue"]:
    st.title("📦 Catalogue Produits" if st.session_state.user_role == "Client" else "📦 Gestion Dépôt")
    
    if st.session_state.user_role == "Client":
        t_tabs_names = ["📋 Catalogue"]
    else:
        t_tabs_names = ["📋 Catalogue", "🖼️ Images & Web", "🔄 Sync Excel"]
        if st.session_state.user_role == "Responsable": t_tabs_names.extend(["➕ Ajout", "✏️ Modif/Suppr"])
    
    tabs = st.tabs(t_tabs_names)

    with tabs[0]: # Catalogue
        # --- SECTION NOUVEAUTÉS ---
        with st.expander("✨ Nouveautés & Promotions", expanded=False):
            new_items = df_para.tail(5) # Les 5 derniers ajoutés
            c_new = st.columns(5)
            for idx, n_row in enumerate(new_items.to_dict('records')):
                with c_new[idx]:
                    img_n = get_image_base64(n_row['image_path'])
                    if img_n: st.image(img_n, use_container_width=True)
                    st.caption(f"**{n_row['Produit']}**")
                    p_new = f"{n_row['PPA']} DA" if n_row['PPA'] > 0 else "Prix NC"
                    st.write(f"**{p_new}**")
        
        c1, c2 = st.columns([7, 3])
        # Liste des suggestions (Produits uniques)
        suggestions = sorted(df_para['Produit'].unique())
        with c1:
            search = st.selectbox("🔍 Rechercher un produit...", options=suggestions, index=None, placeholder="Tapez le nom d'un produit...")
        with c2:
            st.write("⚙️ **Options**")
            tri_az = st.toggle("Tri A-Z")
            hide = st.toggle("Photos")
        
        filt = df_para.copy()
        # Application des filtres sidebar
        if f_famille != "Toutes": filt = filt[filt['Famille'] == f_famille]
        if f_labo != "Tous": filt = filt[filt['Laboratoire'] == f_labo]
        if f_alerte == "Stock Bas (<5)": filt = filt[filt['Quantité'] < 5]
        if f_alerte == "Péremption Proche": 
            # Logique simplifiée : contient 2024 ou 2025
            filt = filt[filt['DDP'].str.contains('2024|2025', na=False)]
            
        if search: filt = filt[filt['Produit'].str.contains(search, case=False, na=False)]
        if tri_az: filt = filt.sort_values(by='Produit', ascending=True)
        if hide: filt = filt[filt['image_path'].str.len() > 3]
        
        if filt.empty: st.warning("Aucun produit ne correspond à ces critères.")
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
            
            for i in range(0, len(page_items), 4):
                cols = st.columns(4)
                for j in range(4):
                    if i+j < len(page_items):
                        row = page_items.iloc[i+j]
                        with cols[j]:
                            with st.container(border=True):
                                img = get_image_base64(row['image_path'])
                                if img: st.image(img, use_container_width=True)
                                
                                # Badges
                                badge_cols = st.columns(2)
                                if st.session_state.user_role != "Client" and row['Quantité'] < 5: 
                                    badge_cols[0].caption("🔴 Stock Faible")
                                if row['Promo']: badge_cols[1].markdown("🔥 **PROMO**")
                                
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

    if "🖼️ Images & Web" in t_tabs_names:
        with tabs[t_tabs_names.index("🖼️ Images & Web")]:
            st.subheader("🖼️ Gestion des visuels")
            
            mode_img = st.radio("Mode d'ajout", ["Un par un", "⚡ Importation Groupée (Rapide)"], horizontal=True)
            
            if mode_img == "Un par un":
                df_sans_image = df_para[
                    (df_para['image_path'].isna()) | 
                    (df_para['image_path'] == "") | 
                    (df_para['image_path'].str.len() < 3)
                ]
                
                if df_sans_image.empty:
                    st.success("🎉 Tous les produits ont déjà une photo !")
                else:
                    liste_produits = sorted(df_sans_image['Produit'].unique())
                    sel_prod = st.selectbox("Sélectionner un produit", liste_produits)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        uploaded_file = st.file_uploader("Charger une photo", type=['png', 'jpg', 'jpeg'], key="single_up")
                        if uploaded_file and st.button("💾 Lier cette image"):
                            fname = f"{clean_filename(sel_prod)}.{uploaded_file.name.split('.')[-1]}"
                            with open(os.path.join(IMG_DIR, fname), "wb") as f: f.write(uploaded_file.getbuffer())
                            df_para.loc[df_para['Produit'] == sel_prod, 'image_path'] = fname
                            save_data(df_para)
                            st.success(f"Image liée à {sel_prod}")
                            st.rerun()
                    with c2:
                        st.info("Recherche rapide")
                        st.link_button("🌐 Chercher sur Google Images", f"https://www.google.com/search?tbm=isch&q={sel_prod.replace(' ','+')}")
            
            else: # IMPORT GROUPÉ
                st.info("💡 **Astuce** : Nommez vos images exactement comme vos produits (ex: `DOLIPRANE.jpg`). Le système les liera automatiquement !")
                bulk_files = st.file_uploader("Glissez toutes vos images ici", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
                
                if bulk_files and st.button(f"🚀 Lier {len(bulk_files)} images"):
                    count = 0
                    for f in bulk_files:
                        prod_name_guess = f.name.split('.')[0].upper().replace('_', ' ')
                        clean_guess = clean_filename(prod_name_guess)
                        match = df_para[df_para['Produit'].apply(clean_filename) == clean_guess]
                        if not match.empty:
                            fname = f"{clean_guess}.{f.name.split('.')[-1]}"
                            with open(os.path.join(IMG_DIR, fname), "wb") as out: out.write(f.getbuffer())
                            df_para.loc[df_para['Produit'].apply(clean_filename) == clean_guess, 'image_path'] = fname
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
                            'Fournisseur': 'Famille', 'Labo': 'Laboratoire', 'Prix': 'PPA'
                        })
                        df_new['Produit'] = df_new['Produit'].astype(str).str.upper().str.strip()
                        if 'PPA' in df_new.columns:
                            df_new['PPA'] = df_new['PPA'].astype(str).str.replace('DZD', '', regex=False).str.replace(',', '', regex=False).str.strip()
                            df_new['PPA'] = pd.to_numeric(df_new['PPA'], errors='coerce').fillna(0)

                        df_img = df_para[['Produit', 'image_path']].drop_duplicates('Produit')
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

# --- ONGLET 2 : STATISTIQUES ---
elif menu == "📊 Statistiques":
    st.title("📊 Analyse Pharmaciel")
    
    total_produits = len(df_para)
    img_ok = df_para[df_para['image_path'].str.len() > 3].shape[0]
    valeur_stock = (df_para['PPA'] * df_para['Quantité']).sum()
    stock_bas = df_para[df_para['Quantité'] < 5].shape[0]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Produits", total_produits)
    if st.session_state.user_role == "Responsable":
        c2.metric("Valeur Stock", f"{valeur_stock:,.0f} DA")
    else:
        c2.metric("Valeur Stock", "---")
    c3.metric("Taux Images", f"{int((img_ok/total_produits)*100)}%" if total_produits > 0 else "0%")
    c4.metric("Alertes Stock", stock_bas, delta=-stock_bas, delta_color="inverse")
    
    if st.session_state.user_role == "Responsable":
        # Analyse Financière
        st.divider()
        st.subheader("💰 Performance Financière")
        df_sales = pd.read_csv(SALES_DB) if os.path.exists(SALES_DB) else pd.DataFrame()
        if not df_sales.empty:
            ca_total = df_sales['Total'].sum()
            nb_ventes = len(df_sales)
            col_f1, col_f2 = st.columns(2)
            col_f1.metric("Chiffre d'Affaires Cumulé", f"{ca_total:,.0f} DA")
            col_f2.metric("Nombre de Ventes", nb_ventes)
            
            st.write("**Évolution des Ventes (CA)**")
            df_sales['Date'] = pd.to_datetime(df_sales['Date'])
            df_sales_daily = df_sales.set_index('Date').resample('D')['Total'].sum()
            st.line_chart(df_sales_daily)
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

# --- ONGLET 3 : PANIER CLIENT (VUE DÉTAILLÉE) ---
elif menu in ["🛒 Mon Panier", "🛒 Commandes Client"]:
    st.title("🛒 Gestion du Panier & Proforma")
    if not st.session_state.cart:
        st.info("Le panier est vide.")
    else:
        # Interface de modification des quantités
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
            
            if col4.button("🗑️", key=f"del_v_{k}"):
                items_to_del.append(k)
        
        for item in items_to_del:
            del st.session_state.cart[item]
            st.rerun()
            
        st.divider()
        st.subheader(f"Total Proforma : {total_cmd:,.2f} DA")
        
        c1, c2, c3 = st.columns(3)
        if c1.button("🗑️ Vider le panier", type="primary", use_container_width=True):
            st.session_state.cart = {}
            st.rerun()
        
        inv_pdf = generate_invoice(st.session_state.cart, total_cmd)
        c2.download_button("📄 Facture Proforma PDF", inv_pdf, f"Proforma_{datetime.now().strftime('%Y%m%d')}.pdf", "application/pdf", use_container_width=True)
        
        msg_cart = f"Bonjour Pharmaciel, voici ma commande (Proforma) :\n" + "\n".join([f"- {k} (x{v['qty']}) : {v['price']*v['qty']} DA" for k,v in st.session_state.cart.items()])
        if c3.button("✅ Valider & WhatsApp", use_container_width=True):
            st.balloons()
            save_sale(st.session_state.cart, total_cmd, st.session_state.current_user)
            st.success("🚀 Commande validée avec succès !")
            st.link_button("Ouvrir WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg_cart)}")

# --- ONGLET 3 : ADMIN ---
elif menu == "⚙️ Admin":
    st.title("⚙️ Administration & Configuration")
    
    # 1. PARAMÈTRES GLOBAUX
    with st.expander("🌐 Paramètres de l'Application", expanded=True):
        st.subheader("Bandeau & IA")
        new_msg = st.text_area("Message défilant (Marquee)", value=settings.get('marquee', ''))
        
        st.divider()
        st.markdown("### 🤖 Intelligence Artificielle (Google Gemini)")
        st.info("Pour des réponses intelligentes, obtenez une clé gratuite sur [Google AI Studio](https://aistudio.google.com/app/apikey)")
        new_gemini = st.text_input("Clé API Gemini", value=settings.get('gemini_key', ''), type="password")
        
        if st.button("💾 Enregistrer les Paramètres", use_container_width=True):
            settings['marquee'] = new_msg
            settings['gemini_key'] = new_gemini
            save_settings(settings)
            st.success("Paramètres enregistrés !")
            st.rerun()

    st.divider()
    
    # 2. GESTION ÉQUIPE
    u_db = load_users()
    st.subheader("👥 Gestion de l'équipe")
    for index, row in u_db.iterrows():
        c_u, c_r, c_p, c_a = st.columns([2, 2, 2, 2])
        with c_u: new_username = st.text_input("User", value=str(row['user']), key=f"u_{index}")
        with c_r: 
            roles = ["Responsable", "Stock", "Préparateur", "Commercial"]
            new_role = st.selectbox("Rôle", roles, index=roles.index(row['role']) if row['role'] in roles else 1, key=f"r_{index}")
        with c_p: new_password = st.text_input("Nouveau MDP", placeholder="Changer ?", type="password", key=f"p_{index}")
        with c_a:
            st.write("")
            cs, cd = st.columns(2)
            if cs.button("💾", key=f"s_{index}"):
                u_db.at[index, 'user'], u_db.at[index, 'role'] = str(new_username), str(new_role)
                if new_password: u_db.at[index, 'pw'] = str(new_password)
                save_data(u_db, USER_DB)
                st.rerun()
            if str(row['user']) != "admin" and cd.button("🗑️", key=f"d_{index}"):
                u_db = u_db.drop(index)
                save_data(u_db, USER_DB)
                st.rerun()

    with st.expander("➕ Ajouter un collaborateur"):
        with st.form("new_u", clear_on_submit=True):
            nu, np, nr = st.text_input("Nom"), st.text_input("MDP", type="password"), st.selectbox("Rôle", ["Stock", "Préparateur", "Commercial", "Responsable"])
            if st.form_submit_button("Créer"):
                u_db = pd.concat([u_db, pd.DataFrame([{"user": str(nu), "pw": str(np), "role": str(nr)}])], ignore_index=True)
                save_data(u_db, USER_DB)
                st.rerun()

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
