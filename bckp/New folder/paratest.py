import streamlit as st
import pandas as pd
import os
import base64
import re
import hashlib

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, 'images_stock')
DB_PATH = os.path.join(BASE_DIR, 'database_para.csv')
USER_DB = os.path.join(BASE_DIR, 'users.csv')

if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

# --- FONCTIONS ---
def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['Produit', 'Laboratoire', 'Quantité', 'DDP', 'PPA', 'image_path'])
    df = pd.read_csv(DB_PATH, dtype=str).fillna("")
    df['Quantité'] = pd.to_numeric(df['Quantité'], errors='coerce').fillna(0).astype(int)
    df['PPA'] = pd.to_numeric(df['PPA'], errors='coerce').fillna(0.0)
    return df

def save_data(df):
    df.to_csv(DB_PATH, index=False)
    st.cache_data.clear()

@st.cache_data(show_spinner=False)
def get_image_base64(filename):
    if not filename or str(filename).strip() == "": return None
    path = os.path.join(IMG_DIR, str(filename))
    if os.path.isfile(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

# --- UI CONFIG ---
st.set_page_config(page_title="Pharmaciel Pro", layout="wide")

# --- AUTHENTIFICATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Connexion Pharmaciel")
    u, p = st.text_input("Utilisateur"), st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        st.session_state.logged_in = True
        st.session_state.role = 'Admin'
        st.session_state.username = u
        st.rerun()
    st.stop()

df_para = load_data()

# --- NAVIGATION ---
tabs = st.tabs(["📋 Catalogue", "📈 Stock", "⚙️ Administration"])

# --- 1. CATALOGUE ---
with tabs[0]:
    search = st.text_input("🔍 Rechercher un produit...")
    
    # FILTRE : Uniquement les produits avec image
    filtered = df_para[df_para['image_path'].astype(str).str.strip() != ""]
    
    # FILTRE : Recherche (si active)
    if search:
        filtered = filtered[filtered['Produit'].str.contains(search, case=False, na=False)]
    
    grid = st.columns(4)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with grid[i % 4]:
            with st.container(border=True):
                img = get_image_base64(row['image_path'])
                # L'image est garantie ici par le filtre
                if img: st.image(f"data:image/png;base64,{img}", use_container_width=True)
                st.write(f"**{row['Produit']}**")
                st.write(f"💰 {row['PPA']} DA")
                
                with st.popover("Agrandir", use_container_width=True):
                    st.subheader(row['Produit'])
                    if img: st.image(f"data:image/png;base64,{img}")
                    st.write(f"**Labo :** {row['Laboratoire']}")
                    st.write(f"**Prix :** {row['PPA']} DA")
                    st.write(f"**Stock :** {row['Quantité']}")
                    st.write(f"**DDP :** {row['DDP']}")

# --- 2. STOCK ---
with tabs[1]:
    st.subheader("📈 État du Stock")
    
    # Statistiques
    total = len(df_para)
    avec_img = len(df_para[df_para['image_path'] != ""])
    sans_img = total - avec_img
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total produits", total)
    c2.metric("Avec images", avec_img)
    c3.metric("Sans images", sans_img)

    with st.expander("➕ Ajouter un nouveau produit manuellement"):
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nom du Produit")
            l = c2.text_input("Laboratoire")
            c3, c4, c5 = st.columns(3)
            p = c3.text_input("PPA (Prix)")
            q = c4.text_input("Qté")
            d = c5.text_input("DDP (Date)")
            
            if st.form_submit_button("Ajouter au catalogue"):
                new_row = pd.DataFrame([{'Produit': n, 'Laboratoire': l, 'PPA': p, 'Quantité': q, 'DDP': d, 'image_path': ''}])
                save_data(pd.concat([df_para, new_row], ignore_index=True))
                st.success(f"Produit '{n}' ajouté !")
                st.rerun()
                
    st.dataframe(df_para, use_container_width=True)

# --- 3. ADMINISTRATION ---
with tabs[2]:
    admin_tabs = ["📸 Photos", "📥 Synchro", "🗑️ Nettoyage"]
    if st.session_state.role == 'Admin': admin_tabs.append("👥 Utilisateurs")
    
    sub = st.tabs(admin_tabs)
    
    with sub[0]: # PHOTOS
        prod = st.selectbox("Produit :", df_para['Produit'].unique())
        f = st.file_uploader("Image", type=['png', 'jpg'])
        if f and st.button("Enregistrer la photo"):
            name = f"{re.sub(r'[^a-zA-Z0-9]', '_', str(prod))}.png"
            with open(os.path.join(IMG_DIR, name), "wb") as img_f: img_f.write(f.getbuffer())
            df_para.loc[df_para['Produit'] == prod, 'image_path'] = name
            save_data(df_para); st.rerun()
            
    with sub[1]: # SYNCHRO
        st.subheader("📥 Synchronisation Excel")
        up = st.file_uploader("Fichier Excel", type=['xlsx'])
        if up and st.button("Fusionner les données"):
            save_data(pd.read_excel(up))
            st.success("Synchronisation effectuée !")
            st.rerun()

    with sub[2]: # NETTOYAGE
        t = st.selectbox("Supprimer ?", df_para['Produit'].unique())
        if st.button("Confirmer suppression"): 
            save_data(df_para[df_para['Produit'] != t]); st.rerun()

    if st.session_state.role == 'Admin':
        with sub[3]:
            st.dataframe(pd.read_csv(USER_DB) if os.path.exists(USER_DB) else pd.DataFrame())