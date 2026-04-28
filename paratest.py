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

# --- 1. CONFIGURATION & CHEMINS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, 'images_stock')
DB_PATH = os.path.join(BASE_DIR, 'database_para.csv')
USER_DB = os.path.join(BASE_DIR, 'users.csv')
SALES_DB = os.path.join(BASE_DIR, 'ventes.csv')

if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

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

        .stApp {{
            background: {t['bg']};
            background-attachment: fixed;
            color: {t['text']} !important;
        }}
        
        /* Typography Fixes */
        [data-testid="stHeader"] {{
            background: transparent !important;
        }}
        
        label, .stMarkdown p, .stText, .stCaption {{
            color: {t['text']} !important;
        }}
        
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown p {{
            color: {t['sidebar_text']} !important;
            font-weight: 600 !important;
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
    </style>
    """, unsafe_allow_html=True)
    
    # Marquee banner if there are promos
    st.markdown(f"""
    <div class="marquee">
        <div>🚀 BIENVENUE SUR PHARMACIEL PRO - LES MEILLEURES OFFRES SONT ICI ! ✨ LIVRAISON RAPIDE DISPONIBLE ✨ -10% SUR LA GAMME COSMÉTIQUE CE MOIS-CI ! 🚀</div>
    </div>
    """, unsafe_allow_html=True)

# Initialisation du thème dans la session
if 'theme' not in st.session_state:
    st.session_state.theme = "Émeraude Royal 👑"

# Sélecteur de thème en haut de la sidebar
with st.sidebar:
    st.markdown("### 🎨 Personnalisation")
    new_theme = st.selectbox("Choisir l'ambiance", 
                            ["Clair Modern ❄️", "Sombre Élite 🌙", "Émeraude Royal 👑", "Aurore Boréale 🌌", "Cyberpunk ⚡"], 
                            index=["Clair Modern ❄️", "Sombre Élite 🌙", "Émeraude Royal 👑", "Aurore Boréale 🌌", "Cyberpunk ⚡"].index(st.session_state.theme))
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

apply_custom_theme(st.session_state.theme)

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

# --- 3. AUTHENTIFICATION ---
def login():
    if 'auth' not in st.session_state: st.session_state.auth = False
    if 'cart' not in st.session_state: st.session_state.cart = {}
    if not st.session_state.auth:
        st.title("🔐 Pharmaciel Pro")
        
        # SECTION CLIENT (Très visible)
        st.success("👋 Vous êtes client ? Accédez directement à notre catalogue sans identifiant.")
        if st.button("🌐 VOIR LE CATALOGUE PRODUITS", type="primary", use_container_width=True):
            st.session_state.auth, st.session_state.user_role, st.session_state.current_user = True, "Client", "Visiteur"
            st.rerun()
        
        st.divider()
        
        # SECTION CONNEXION (Staff)
        with st.expander("🔑 Espace Collaborateur (Connexion)", expanded=False):
            with st.form("login_form"):
                u = st.text_input("Identifiant")
                p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("Se connecter"):
                    if u == "admin" and p == "1992":
                        st.session_state.auth, st.session_state.user_role, st.session_state.current_user = True, "Responsable", "Admin Suprême"
                        st.rerun()
                    users = load_users()
                    match = users[(users['user'] == u) & (users['pw'].astype(str) == p)]
                    if not match.empty:
                        st.session_state.auth, st.session_state.user_role, st.session_state.current_user = True, match['role'].values[0], u
                        st.rerun()
                    else: st.error("Identifiants incorrects.")
        st.stop()

# --- 4. INTERFACE ---
login()

df_para = load_data()
st.sidebar.title(f"👤 {st.session_state.current_user}")
if st.session_state.user_role != "Client":
    st.sidebar.write(f"Rôle : **{st.session_state.user_role}**")

st.sidebar.divider()

# --- FILTRES DE NAVIGATION ---
with st.sidebar.expander("🎯 Filtres & Recherche", expanded=True):
    f_famille = st.selectbox("Famille", ["Toutes"] + sorted([f for f in df_para['Famille'].unique() if f]))
    f_labo = st.selectbox("Laboratoire", ["Tous"] + sorted([l for l in df_para['Laboratoire'].unique() if l]))
    f_alerte = st.selectbox("Alertes Stock/DDP", ["Aucune", "Stock Bas (<5)", "Péremption Proche"])

if st.session_state.user_role == "Client":
    nav_options = ["📦 Catalogue", "🛒 Mon Panier"]
else:
    nav_options = ["📦 Stock & Catalogue", "🛒 Commandes Client", "📊 Statistiques"]
    if st.session_state.user_role == "Responsable": nav_options.append("⚙️ Admin")

menu = st.sidebar.radio("Navigation", nav_options)

# --- PANIER (SIDEBAR) ---
if st.session_state.cart:
    st.sidebar.divider()
    st.sidebar.subheader("🛒 Votre Panier")
    total_panier = 0
    items_to_remove = []
    for p_name, details in st.session_state.cart.items():
        c_p1, c_p2 = st.sidebar.columns([3, 1])
        # Petit champ numérique pour la sidebar
        c_p1.number_input(f"{p_name} ({details['price']} DA)", min_value=1, value=details['qty'], key=f"q_side_{p_name}", on_change=update_cart_qty, args=(p_name, f"q_side_{p_name}"))
        
        if c_p2.button("❌", key=f"del_{p_name}"):
            items_to_remove.append(p_name)
        total_panier += details['qty'] * details['price']
    
    for item in items_to_remove:
        del st.session_state.cart[item]
        st.rerun()
        
    st.sidebar.write(f"**Total : {total_panier} DA**")
    
    msg_cart = f"Bonjour Pharmaciel, je souhaite commander :\n" + "\n".join([f"- {k} (x{v['qty']})" for k,v in st.session_state.cart.items()])
    st.sidebar.link_button("🚀 Envoyer Commande WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg_cart)}", use_container_width=True)
    if st.sidebar.button("🗑️ Vider le panier", use_container_width=True):
        st.session_state.cart = {}
        st.rerun()

st.sidebar.divider()
if st.sidebar.button("🚪 Déconnexion", type="secondary", use_container_width=True):
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
        
        c1, c2, c3 = st.columns([3, 1, 1])
        # Liste des suggestions (Produits uniques)
        suggestions = sorted(df_para['Produit'].unique())
        with c1:
            search = st.selectbox("🔍 Rechercher un produit...", options=suggestions, index=None, placeholder="Tapez le nom d'un produit...")
        with c2:
            st.write("")
            pdf_buf = generate_pdf_catalogue(df_para)
            st.download_button("📄 PDF Catalogue", pdf_buf, "Catalogue_Pharmaciel.pdf", "application/pdf", use_container_width=True)
        with c3:
            st.write("⚙️ **Filtres**")
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
        
        for i in range(0, len(filt), 4):
            cols = st.columns(4)
            for j in range(4):
                if i+j < len(filt):
                    row = filt.iloc[i+j]
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
                            if c_b1.button("Détails", key=f"v_{i+j}", use_container_width=True): show_details(row)
                            if c_b2.button("🛒", key=f"add_{i+j}", use_container_width=True):
                                if row['Produit'] in st.session_state.cart:
                                    st.session_state.cart[row['Produit']]['qty'] += 1
                                else:
                                    st.session_state.cart[row['Produit']] = {'price': row['PPA'], 'qty': 1}
                                st.toast(f"Ajouté : {row['Produit']}")
                                st.rerun()

    with tabs[1]: # Images & Web
        st.subheader("🖼️ Gestion des visuels")
        
        # Filtre pour ne garder que les produits sans image dans la liste déroulante
        df_sans_image = df_para[
            (df_para['image_path'].isna()) | 
            (df_para['image_path'] == "") | 
            (df_para['image_path'].str.len() < 3)
        ]
        
        if df_sans_image.empty:
            st.success("🎉 Tous les produits ont déjà une photo !")
        else:
            liste_produits = sorted(df_sans_image['Produit'].unique())
            sel_prod = st.selectbox("Sélectionner un produit (sans photo)", liste_produits)
            
            c1, c2 = st.columns(2)
            with c1:
                uploaded_file = st.file_uploader("Charger une photo", type=['png', 'jpg', 'jpeg'])
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

    with tabs[2]: # 🔄 SYNC EXCEL
        st.subheader("🔄 Synchronisation Base de Données")
        st.info("Importez votre fichier Excel (format Dépôt, Produit, Quantité Dépot, DDP, PPA, Labo, Arrivage).")
        
        up_excel = st.file_uploader("Choisir le fichier Excel/CSV", type=['xlsx', 'csv'])
        if up_excel:
            try:
                if up_excel.name.endswith('.xlsx'):
                    df_new = pd.read_excel(up_excel)
                else:
                    df_new = pd.read_csv(up_excel)
                
                st.write("🔍 Aperçu des données importées :", df_new.head(3))
                
                if st.button("🚀 Lancer la Synchronisation"):
                    # Normalisation des noms de colonnes
                    df_new = df_new.rename(columns={
                        'Quantité  Dépot': 'Quantité', 
                        'Quantité Dépot': 'Quantité',
                        'Quantité Dépôt': 'Quantité',
                        'Fournisseur': 'Famille',
                        'Labo': 'Laboratoire'
                    })
                    
                    df_new['Produit'] = df_new['Produit'].astype(str).str.upper().str.strip()
                    
                    # Nettoyage PPA (gestion du format "DZD 1,780.00")
                    if 'PPA' in df_new.columns:
                        df_new['PPA'] = df_new['PPA'].astype(str).str.replace('DZD', '', regex=False).str.replace(',', '', regex=False).str.strip()
                        df_new['PPA'] = pd.to_numeric(df_new['PPA'], errors='coerce').fillna(0)

                    # On fusionne avec les images existantes pour ne pas les perdre
                    # On garde une seule entrée d'image par nom de produit
                    df_img = df_para[['Produit', 'image_path']].drop_duplicates('Produit')
                    merged = pd.merge(df_new, df_img, on='Produit', how='left')
                    merged['image_path'] = merged['image_path'].fillna("")
                    
                    # S'assurer que toutes les colonnes requises existent
                    for c in ['Promo', 'Prix_Achat', 'Description', 'Famille', 'Laboratoire', 'DDP', 'Dépôt', 'Arrivage']:
                        if c not in merged.columns:
                            if c == 'Promo': merged[c] = False
                            elif c == 'Prix_Achat': merged[c] = 0
                            else: merged[c] = ""
                    
                    save_data(merged)
                    st.success("✅ Synchronisation terminée avec succès !")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur lors de l'import : {e}")

    if "➕ Ajout" in t_tabs_names:
        with tabs[3]: # Ajout Manuel
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

        with tabs[4]: # Gestion du Stock (Modif/Suppr)
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
    st.title("⚙️ Administration (Accès Maître)")
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
