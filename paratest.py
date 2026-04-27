import streamlit as st
import pandas as pd
import os
import re
import base64
import shutil
import urllib.parse
from datetime import datetime

# --- 1. CONFIGURATION & CHEMINS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, 'images_stock')
DB_PATH = os.path.join(BASE_DIR, 'database_para.csv')
USER_DB = os.path.join(BASE_DIR, 'users.csv')

if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

# --- 2. FONCTIONS TECHNIQUES ---

def load_data():
    cols = ['Produit', 'Laboratoire', 'Quantité', 'PPA', 'image_path', 'Famille', 'DDP']
    if not os.path.exists(DB_PATH): return pd.DataFrame(columns=cols)
    try:
        df = pd.read_csv(DB_PATH, encoding='utf-8-sig', dtype={'image_path': str, 'Produit': str, 'DDP': str})
        for c in cols:
            if c not in df.columns: df[c] = ""
        return df.fillna("")
    except: return pd.DataFrame(columns=cols)

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

# --- 3. AUTHENTIFICATION ---
def login():
    if 'auth' not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        st.title("🔐 Accès Pharmaciel Pro")
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
st.set_page_config(page_title="Pharmaciel Pro", layout="wide")
login()

df_para = load_data()
st.sidebar.title(f"👤 {st.session_state.current_user}")
st.sidebar.write(f"Rôle : **{st.session_state.user_role}**")
nav_options = ["📦 Stock & Catalogue", "📊 Statistiques"]
if st.session_state.user_role == "Responsable": nav_options.append("⚙️ Admin")
menu = st.sidebar.radio("Navigation", nav_options)

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
        st.divider()
        st.metric("Prix", f"{row['PPA']} DA")
        msg = urllib.parse.quote(f"Pharmaciel - {row['Produit']} | Prix: {row['PPA']} DA")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" style="background-color:#25D366; color:white; padding:10px; border-radius:5px; text-decoration:none; display:block; text-align:center;">Partager WhatsApp</a>', unsafe_allow_html=True)

# --- ONGLET 1 : CATALOGUE ---
if menu == "📦 Stock & Catalogue":
    st.title("📦 Gestion Dépôt")
    t_tabs_names = ["📋 Catalogue", "🖼️ Images & Web", "🔄 Sync Excel"]
    if st.session_state.user_role == "Responsable": t_tabs_names.extend(["➕ Ajout", "✏️ Modif/Suppr"])
    tabs = st.tabs(t_tabs_names)

    with tabs[0]: # Catalogue
        c1, c2 = st.columns([3, 1])
        search = c1.text_input("🔍 Rechercher un produit...")
        with c2:
            st.write("⚙️ **Filtres**")
            tri_az = st.toggle("Tri alphabétique (A-Z)")
            hide = st.toggle("Images uniquement")
        
        filt = df_para.copy()
        if search: filt = filt[filt['Produit'].str.contains(search, case=False, na=False)]
        if tri_az: filt = filt.sort_values(by='Produit', ascending=True)
        if hide: filt = filt[filt['image_path'].str.len() > 3]
        
        for i in range(0, len(filt), 4):
            cols = st.columns(4)
            for j in range(4):
                if i+j < len(filt):
                    row = filt.iloc[i+j]
                    with cols[j]:
                        with st.container(border=True):
                            img = get_image_base64(row['image_path'])
                            if img: st.image(img, use_container_width=True)
                            st.markdown(f"**{row['Produit']}**")
                            st.markdown(f"💰 **{row['PPA']} DA**")
                            if st.button("Détails", key=f"v_{i+j}"): show_details(row)

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
        st.info("Importez votre fichier Excel (Logipharm) pour mettre à jour les prix et ajouter les nouveaux produits sans supprimer vos images.")
        
        up_excel = st.file_uploader("Choisir le fichier Excel/CSV", type=['xlsx', 'csv'])
        if up_excel:
            try:
                if up_excel.name.endswith('.xlsx'):
                    df_new = pd.read_excel(up_excel)
                else:
                    df_new = pd.read_csv(up_excel)
                
                st.write("Aperçu des données importées :", df_new.head(3))
                
                if st.button("🚀 Lancer la Synchronisation"):
                    df_new['Produit'] = df_new['Produit'].str.upper().str.strip()
                    merged = pd.merge(df_new, df_para[['Produit', 'image_path']], on='Produit', how='left')
                    merged['image_path'] = merged['image_path'].fillna("")
                    save_data(merged)
                    st.success("Synchronisation terminée !")
                    st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de l'import : {e}")

    if "➕ Ajout" in t_tabs_names:
        with tabs[3]: # Ajout Manuel
            with st.form("add_p"):
                n, l, p, d = st.text_input("Désignation"), st.text_input("Labo"), st.number_input("Prix", 0.0), st.text_input("DDP")
                if st.form_submit_button("Enregistrer"):
                    new_row = pd.DataFrame([{"Produit": n.upper(), "Laboratoire": l.upper(), "PPA": p, "DDP": d, "image_path": ""}])
                    save_data(pd.concat([df_para, new_row], ignore_index=True))
                    st.rerun()

        with tabs[4]: # Modif/Suppr
            st.subheader("✏️ Édition du catalogue")
            target = st.selectbox("Produit à modifier/supprimer", df_para['Produit'].unique())
            if st.button("❌ Supprimer définitivement ce produit", type="primary"):
                df_para = df_para[df_para['Produit'] != target]
                save_data(df_para)
                st.rerun()

# --- ONGLET 2 : STATISTIQUES ---
elif menu == "📊 Statistiques":
    st.title("📊 Analyse Pharmaciel")
    total = len(df_para)
    img_ok = df_para[df_para['image_path'].str.len() > 3].shape[0]
    c1, c2 = st.columns(2)
    c1.metric("Total Produits", total)
    c2.metric("Taux d'images", f"{int((img_ok/total)*100)}%" if total > 0 else "0%")

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
