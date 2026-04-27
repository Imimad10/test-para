import streamlit as st
import pandas as pd
import os
import base64
import re
import urllib.parse

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, 'images_stock')
DB_PATH = os.path.join(BASE_DIR, 'database_para.csv')

if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

st.set_page_config(page_title="Pharmaciel Pro", layout="wide", page_icon="🌿")

if 'show_price' not in st.session_state:
    st.session_state.show_price = True

# --- STYLE VISUEL ---
st.markdown("""
    <style>
    .img-card { border-radius:10px; border:1px solid #f0f0f0; padding:8px; transition: transform 0.2s; background: white; text-align: center; }
    .img-card:hover { transform: translateY(-5px); border-color: #2ecc71; }
    .product-img { width:100%; height:150px; object-fit:contain; border-bottom: 1px solid #eee; margin-bottom:5px; }
    .stButton>button { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS ---
@st.cache_data(show_spinner=False)
def get_image_base64(filename):
    if not filename or filename == "": return False
    path = os.path.join(IMG_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return False

def clean_filename(name):
    clean = re.sub(r'[^a-zA-Z0-9]', '_', str(name))
    return f"{clean[:50]}.png"

def load_data():
    if os.path.exists(DB_PATH):
        df = pd.read_csv(DB_PATH, dtype=str).fillna("")
        cols = ['Produit', 'Laboratoire', 'Quantité', 'DDP', 'PPA', 'image_path']
        for col in cols:
            if col not in df.columns: df[col] = "0" if col in ['Quantité', 'PPA'] else ""
        return df
    return pd.DataFrame(columns=['Produit', 'Laboratoire', 'Quantité', 'DDP', 'PPA', 'image_path'])

def save_data(df):
    df.to_csv(DB_PATH, index=False)
    st.cache_data.clear()

# --- FENÊTRE DE PARTAGE OPTIMISÉE ---
@st.dialog("📲 Envoi Rapide au Client")
def show_preview(row, img_b64):
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.image(f"data:image/png;base64,{img_b64}", use_container_width=True)
        st.success("☝️ Étape 1 : Faites un clic-droit sur l'image et 'Copier l'image'")
    
    with c2:
        st.subheader(row['Produit'])
        msg = f"📦 *{row['Produit']}*\n🏷️ Labo: {row['Laboratoire']}\n💰 Prix: {row['PPA']} DA\n📅 DDP: {row['DDP']}"
        
        st.text_area("Texte prêt :", value=msg, height=130, help="Le texte est déjà prêt ici")
        st.info("✌️ Étape 2 : Collez dans WhatsApp ou Viber !")
        
        st.divider()
        st.download_button("📥 Télécharger la photo", base64.b64decode(img_b64), 
                           file_name=f"{row['Produit']}.png", use_container_width=True)

# --- INTERFACE PRINCIPALE ---
df_para = load_data()
tabs = st.tabs(["📋 Catalogue", "📈 Stock", "⚙️ Administration"])

# --- 1. CATALOGUE ---
with tabs[0]:
    search = st.text_input("🔍 Rechercher un produit...")
    mask = df_para['Produit'].str.contains(search, case=False) | df_para['Laboratoire'].str.contains(search, case=False)
    display_df = df_para[mask] if search else df_para
    
    grid = st.columns(5)
    for i, (idx, row) in enumerate(display_df.iterrows()):
        with grid[i % 5]:
            img_b64 = get_image_base64(row['image_path'])
            with st.container(border=True):
                if img_b64:
                    st.markdown(f'<div class="img-card"><img src="data:image/png;base64,{img_b64}" class="product-img"></div>', unsafe_allow_html=True)
                    if st.button("📲 Envoyer", key=f"z_{idx}", use_container_width=True): 
                        show_preview(row, img_b64)
                else: st.caption("📷 Pas d'image")
                
                st.markdown(f"**{row['Produit'][:22]}**")
                if st.session_state.show_price:
                    st.markdown(f"<span style='color:#2ecc71; font-weight:bold;'>{row['PPA']} DA</span>", unsafe_allow_html=True)

# --- 2. ANALYSE ---
with tabs[1]:
    st.header("📈 Rapport Rapide")
    calc_df = df_para.copy()
    calc_df['Q'] = pd.to_numeric(calc_df['Quantité'], errors='coerce').fillna(0)
    calc_df['P'] = pd.to_numeric(calc_df['PPA'], errors='coerce').fillna(0)
    
    col1, col2 = st.columns(2)
    col1.metric("Produits", len(calc_df))
    col2.metric("Valeur Totale", f"{(calc_df['Q'] * calc_df['P']).sum():,.2f} DA")
    
    st.subheader("⚠️ Alertes Ruptures")
    st.dataframe(calc_df[calc_df['Q'] < 10][['Produit', 'Laboratoire', 'Quantité']], use_container_width=True)

# --- 3. ADMINISTRATION ---
with tabs[2]:
    st.title("⚙️ Administration Pharmaciel")
    st.session_state.show_price = st.toggle("👁️ Afficher les prix aux agents", value=st.session_state.show_price)
    
    if st.button("🔄 Réparer les liens d'images", use_container_width=True):
        existing = os.listdir(IMG_DIR)
        count = 0
        for i, r in df_para.iterrows():
            pot = clean_filename(r['Produit'])
            if pot in existing and not r['image_path']:
                df_para.at[i, 'image_path'] = pot
                count += 1
        save_data(df_para); st.success(f"{count} images liées !"); st.rerun()

    admin_tabs = st.tabs(["📸 Photos", "➕ Manuel", "📥 Import LogiPharm", "🗑️ Nettoyage"])
    
    with admin_tabs[0]: # PHOTOS
        sel = st.selectbox("Produit :", df_para['Produit'].unique())
        mode = st.radio("Source :", ["Fichier", "Webcam"], horizontal=True)
        if mode == "Fichier":
            f = st.file_uploader("Image", type=['png', 'jpg'])
            if f and st.button("Enregistrer l'image"):
                name = clean_filename(sel)
                with open(os.path.join(IMG_DIR, name), "wb") as img_f: img_f.write(f.getbuffer())
                df_para.loc[df_para['Produit'] == sel, 'image_path'] = name
                save_data(df_para); st.rerun()
        else:
            cam = st.camera_input("Prendre photo")
            if cam and st.button("Lier photo"):
                name = clean_filename(sel)
                with open(os.path.join(IMG_DIR, name), "wb") as img_f: img_f.write(cam.getbuffer())
                df_para.loc[df_para['Produit'] == sel, 'image_path'] = name
                save_data(df_para); st.rerun()

    with admin_tabs[1]: # MANUEL
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Nom du produit")
            lab = c2.text_input("Labo")
            ppa = c1.text_input("PPA")
            qty = c2.text_input("Quantité")
            ddp = c1.text_input("DDP")
            if st.form_submit_button("Ajouter"):
                new = {'Produit':name, 'Laboratoire':lab, 'PPA':ppa, 'Quantité':qty, 'DDP':ddp, 'image_path':''}
                df_para = pd.concat([df_para, pd.DataFrame([new])], ignore_index=True)
                save_data(df_para); st.rerun()

    with admin_tabs[2]: # IMPORT LOGIPHARM (Synchronisation)
        st.subheader("Charger l'Excel de LogiPharm")
        excel = st.file_uploader("Fichier .xlsx", type=['xlsx'])
        if excel and st.button("Synchroniser"):
            try:
                new_df = pd.read_excel(excel)
                for i, row in new_df.iterrows():
                    p_name = str(row.get('Produit', ''))
                    if p_name in df_para['Produit'].values:
                        idx = df_para[df_para['Produit'] == p_name].index[0]
                        df_para.at[idx, 'Quantité'] = str(row.get('Quantité', '0'))
                        df_para.at[idx, 'PPA'] = str(row.get('PPA', '0'))
                        df_para.at[idx, 'DDP'] = str(row.get('DDP', ''))
                    else:
                        row['image_path'] = ""
                        df_para = pd.concat([df_para, pd.DataFrame([row])], ignore_index=True)
                save_data(df_para); st.success("Base mise à jour !"); st.rerun()
            except Exception as e: st.error(f"Erreur : {e}")

    with admin_tabs[3]: # NETTOYAGE
        to_del = st.selectbox("Supprimer :", df_para['Produit'].unique())
        if st.button("🗑️ Supprimer"):
            df_para = df_para[df_para['Produit'] != to_del]
            save_data(df_para); st.rerun()
