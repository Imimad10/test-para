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

if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

# --- 2. DESIGN SYSTEM (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Card Premium Style */
    [data-testid="stVerticalBlock"] > div > div > div > div.stColumn {
        transition: transform 0.3s ease;
    }
    
    .stContainer {
        border-radius: 15px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
        background: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(10px);
    }
    
    .stContainer:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1) !important;
    }
    
    /* Custom Buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button:hover {
        background-color: #007bff !important;
        color: white !important;
        border-color: #007bff !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. FONCTIONS TECHNIQUES ---

def load_data():
    cols = ['Produit', 'Laboratoire', 'Quantité', 'PPA', 'image_path', 'Famille', 'DDP', 'Promo']
    if not os.path.exists(DB_PATH): return pd.DataFrame(columns=cols)
    try:
        df = pd.read_csv(DB_PATH, encoding='utf-8-sig')
        # Renommage flexible
        df = df.rename(columns={'Quantité  Dépot': 'Quantité', 'Fournisseur': 'Famille'})
        
        # Gestion des colonnes dupliquées (ex: deux colonnes 'Quantité')
        df = df.loc[:, ~df.columns.duplicated()]
        
        for c in cols:
            if c not in df.columns: 
                df[c] = False if c == 'Promo' else ""
            
        # Nettoyage numérique
        df['PPA'] = pd.to_numeric(df['PPA'], errors='coerce').fillna(0)
        df['Quantité'] = pd.to_numeric(df['Quantité'], errors='coerce').fillna(0)
        df['Promo'] = df['Promo'].astype(bool)
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

def generate_pdf_catalogue(df):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Titre
    elements.append(Paragraph(f"<b>CATALOGUE PRODUITS - PHARMACIEL</b>", styles['Title']))
    elements.append(Paragraph(f"Date : {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Table de données
    data = [["Produit", "Laboratoire", "Famille", "Prix (DA)"]]
    for _, row in df.iterrows():
        data.append([row['Produit'], row['Laboratoire'], row['Famille'], f"{row['PPA']}"])
        
    t = Table(data, colWidths=[200, 120, 100, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.cadetblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(t)
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
st.set_page_config(page_title="Pharmaciel Pro", layout="wide")
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
        c_p1.write(f"**{p_name}**\n{details['qty']} x {details['price']} DA")
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
        
        if st.session_state.user_role == "Responsable":
            st.write(f"**📦 Stock :** {row['Quantité']} unités")
            val_tot = float(row['PPA']) * float(row['Quantité'])
            st.write(f"**💰 Valeur Stock :** {val_tot:,.2f} DA")
            
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
                c_a1, c_a2 = st.columns(2)
                n = c_a1.text_input("Désignation")
                l = c_a2.text_input("Labo")
                p = c_a1.number_input("Prix (PPA)", 0.0)
                q = c_a2.number_input("Quantité", 0)
                d = c_a1.text_input("DDP (MM/YY)")
                f = c_a2.text_input("Famille")
                promo = st.checkbox("Mettre en promotion")
                if st.form_submit_button("Enregistrer le produit"):
                    new_row = pd.DataFrame([{"Produit": n.upper(), "Laboratoire": l.upper(), "PPA": p, "Quantité": q, "DDP": d, "Famille": f, "image_path": "", "Promo": promo}])
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
                    new_q = c2.number_input("Quantité en stock", value=int(p_data['Quantité']))
                    new_d = c1.text_input("DDP", value=p_data['DDP'])
                    new_f = c2.text_input("Famille", value=p_data['Famille'])
                    new_promo = st.checkbox("Produit en PROMO", value=bool(p_data['Promo']))
                    
                    col_btn1, col_btn2 = st.columns(2)
                    if col_btn1.form_submit_button("💾 Enregistrer les modifications", use_container_width=True):
                        df_para.at[p_idx, 'Produit'] = new_n.upper()
                        df_para.at[p_idx, 'Laboratoire'] = new_l.upper()
                        df_para.at[p_idx, 'PPA'] = new_p
                        df_para.at[p_idx, 'Quantité'] = new_q
                        df_para.at[p_idx, 'DDP'] = new_d
                        df_para.at[p_idx, 'Famille'] = new_f
                        df_para.at[p_idx, 'Promo'] = new_promo
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
    st.title("🛒 Gestion du Panier")
    if not st.session_state.cart:
        st.info("Le panier est vide.")
    else:
        df_cart = pd.DataFrame([
            {"Produit": k, "Prix Unitaire": v['price'], "Quantité": v['qty'], "Total": v['price'] * v['qty']}
            for k, v in st.session_state.cart.items()
        ])
        st.table(df_cart)
        st.subheader(f"Total Commande : {df_cart['Total'].sum()} DA")
        
        c1, c2 = st.columns(2)
        if c1.button("🗑️ Vider tout le panier", type="primary"):
            st.session_state.cart = {}
            st.rerun()
        
        msg_cart = f"Bonjour Pharmaciel, voici ma commande :\n" + "\n".join([f"- {k} (x{v['qty']}) : {v['price']*v['qty']} DA" for k,v in st.session_state.cart.items()])
        c2.link_button("✅ Confirmer & Envoyer WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg_cart)}", use_container_width=True)

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
