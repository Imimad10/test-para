import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime

# Import des modules locaux
from utils.config import IMG_DIR, DB_PATH
from utils.database import load_data, save_data, load_settings, save_settings, add_log, save_sale
from utils.auth import login, logout, load_users
from utils.styles import apply_custom_theme, get_image_base64
from utils.pdf_engine import generate_pdf_catalogue, generate_invoice, generate_promo_flyer
from utils.ui_components import show_product_details

# --- INITIALISATION ---
st.set_page_config(page_title="Pharmaciel Pro", layout="wide", page_icon="💊")
login()

df_para = load_data()
settings = load_settings()

if 'theme' not in st.session_state: st.session_state.theme = "Émeraude Royal 👑"
apply_custom_theme(st.session_state.theme)

# Marquee
st.markdown(f'<div class="marquee">{settings.get("marquee", "")}</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"## 👤 {st.session_state.current_user}")
    st.caption(f"Rôle: {st.session_state.user_role}")
    
    if st.session_state.user_role == "Client":
        nav = ["📦 Catalogue", "🛒 Mon Panier"]
    else:
        nav = ["📦 Catalogue", "🛒 Commandes", "📊 Statistiques", "⚙️ Admin"]
    
    menu = st.radio("Navigation", nav)
    st.divider()
    
    # Filtres & PDF
    with st.expander("🎯 Filtres & Outils", expanded=True):
        f_famille = st.selectbox("Famille", ["Toutes"] + sorted([f for f in df_para['Famille'].unique() if f]))
        f_labo = st.selectbox("Laboratoire", ["Tous"] + sorted([l for l in df_para['Laboratoire'].unique() if l]))
        
        st.divider()
        pdf_buf = generate_pdf_catalogue(df_para)
        st.download_button("📄 PDF Catalogue", pdf_buf, "Catalogue.pdf", use_container_width=True)
        
        promo_df = df_para[df_para['Promo'] == True]
        if not promo_df.empty:
            p_flyer = generate_promo_flyer(df_para)
            st.download_button("🔥 Flyer PROMO", p_flyer, "Promotions.pdf", use_container_width=True)

    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True): logout()

# --- PAGES ---

if menu == "📦 Catalogue":
    st.title("📦 Catalogue Produits")
    
    # Tabs pour Admin
    if st.session_state.user_role != "Client":
        t_names = ["📋 Vue", "🖼️ Images", "🔄 Sync", "➕ Ajout", "✏️ Modif"]
    else:
        t_names = ["📋 Vue"]
    
    tabs = st.tabs(t_names)
    
    with tabs[0]: # Vue Catalogue
        c1, c2 = st.columns([7, 3])
        search = c1.selectbox("🔍 Rechercher...", options=sorted(df_para['Produit'].unique()), index=None)
        with c2:
            st.write("Options")
            tri = st.toggle("Tri A-Z")
            hide = st.toggle("Sans Photo")
        
        # Filtrage
        filt = df_para.copy()
        if f_famille != "Toutes": filt = filt[filt['Famille'] == f_famille]
        if f_labo != "Tous": filt = filt[filt['Laboratoire'] == f_labo]
        if search: filt = filt[filt['Produit'] == search]
        if tri: filt = filt.sort_values('Produit')
        
        # Pagination & Grid
        items_per_page = 12
        page = st.number_input("Page", 1, max(1, len(filt)//items_per_page + 1), 1)
        start = (page-1)*items_per_page
        end = start + items_per_page
        
        for i in range(start, min(end, len(filt)), 4):
            cols = st.columns(4)
            for j in range(4):
                if i+j < len(filt):
                    row = filt.iloc[i+j]
                    with cols[j]:
                        with st.container(border=True):
                            img = get_image_base64(row['image_path'])
                            if img: st.image(img, use_container_width=True)
                            st.markdown(f"**{row['Produit']}**")
                            st.caption(row['Laboratoire'])
                            st.subheader(f"{row['PPA']} DA")
                            if st.button("Détails", key=f"d_{row['Produit']}"):
                                @st.dialog("Fiche Produit", width="large")
                                def dialog_details(r): show_product_details(r, settings)
                                dialog_details(row)
                            if st.button("🛒", key=f"a_{row['Produit']}", use_container_width=True):
                                if row['Produit'] in st.session_state.cart: st.session_state.cart[row['Produit']]['qty'] += 1
                                else: st.session_state.cart[row['Produit']] = {'price': row['PPA'], 'qty': 1}
                                st.toast("Ajouté !")

    if st.session_state.user_role != "Client":
        with tabs[1]: # Images
            st.subheader("🖼️ Gestion des visuels")
            mode_img = st.radio("Mode d'ajout", ["Un par un", "⚡ Importation Groupée (Rapide)"], horizontal=True)
            if mode_img == "Un par un":
                liste_p = sorted(df_para['Produit'].unique())
                sel_p = st.selectbox("Produit", liste_p)
                up = st.file_uploader("Image", type=['png', 'jpg', 'jpeg'])
                if up and st.button("💾 Lier"):
                    fname = f"{sel_p.replace(' ','_')}.{up.name.split('.')[-1]}"
                    with open(os.path.join(IMG_DIR, fname), "wb") as f: f.write(up.getbuffer())
                    df_para.loc[df_para['Produit'] == sel_p, 'image_path'] = fname
                    save_data(df_para)
                    st.success("Lié !")
            else:
                up_bulk = st.file_uploader("Images multiples", accept_multiple_files=True)
                if up_bulk and st.button(f"🚀 Lier {len(up_bulk)} images"):
                    for f in up_bulk:
                        guess = f.name.split('.')[0].upper()
                        if guess in df_para['Produit'].values:
                            with open(os.path.join(IMG_DIR, f.name), "wb") as out: out.write(f.getbuffer())
                            df_para.loc[df_para['Produit'] == guess, 'image_path'] = f.name
                    save_data(df_para)
                    st.success("Import groupé terminé.")

        with tabs[2]: # Sync Excel
            st.subheader("🔄 Synchronisation")
            up_xl = st.file_uploader("Fichier Excel/CSV", type=['xlsx', 'csv'])
            if up_xl and st.button("🚀 Lancer la Sync"):
                df_new = pd.read_excel(up_xl) if up_xl.name.endswith('.xlsx') else pd.read_csv(up_xl)
                df_new = df_new.rename(columns={'Quantité  Dépot': 'Quantité', 'Labo': 'Laboratoire', 'Prix': 'PPA'})
                # Fusion avec images existantes
                df_img = df_para[['Produit', 'image_path']].drop_duplicates('Produit')
                merged = pd.merge(df_new, df_img, on='Produit', how='left').fillna("")
                save_data(merged)
                st.success("Synchronisation réussie !")
                st.rerun()

        with tabs[3]: # Ajout
            with st.form("add"):
                n = st.text_input("Nom")
                l = st.text_input("Labo")
                p = st.number_input("Prix", 0.0)
                if st.form_submit_button("Ajouter"):
                    new = pd.DataFrame([{"Produit": n.upper(), "Laboratoire": l.upper(), "PPA": p, "Quantité": 0, "image_path": "", "Promo": False}])
                    save_data(pd.concat([df_para, new], ignore_index=True))
                    st.success("Ajouté !")

        with tabs[4]: # Modif
            target = st.selectbox("Modifier", sorted(df_para['Produit'].unique()))
            if target:
                idx = df_para[df_para['Produit'] == target].index[0]
                with st.form(f"ed_{target}"):
                    new_p = st.number_input("Nouveau Prix", value=float(df_para.loc[idx, 'PPA']))
                    if st.form_submit_button("Enregistrer"):
                        df_para.at[idx, 'PPA'] = new_p
                        save_data(df_para)
                        st.success("Modifié !")

elif menu == "📊 Statistiques":
    st.title("📊 Statistiques")
    c1, c2, c3 = st.columns(3)
    c1.metric("Produits", len(df_para))
    c2.metric("Valeur Stock", f"{(df_para['PPA']*df_para['Quantité']).sum():,.0f} DA")
    st.bar_chart(df_para['Laboratoire'].value_counts().head(10))

elif menu == "🛒 Commandes":
    st.title("🛒 Panier & Commandes")
    if not st.session_state.cart:
        st.info("Vide.")
    else:
        total = 0
        for k, v in st.session_state.cart.items():
            total += v['price'] * v['qty']
            st.write(f"**{k}** x {v['qty']} = {v['price']*v['qty']} DA")
        st.subheader(f"Total : {total} DA")
        if st.button("Valider la vente"):
            save_sale(st.session_state.cart, total, st.session_state.current_user)
            st.session_state.cart = {}
            st.success("Vente enregistrée !")
            st.rerun()

elif menu == "⚙️ Admin":
    st.title("⚙️ Paramètres")
    with st.expander("Configuration Globale"):
        new_m = st.text_input("Marquee", settings.get('marquee', ''))
        new_k = st.text_input("Gemini API Key", settings.get('gemini_key', ''), type="password")
        if st.button("Enregistrer"):
            settings['marquee'] = new_m
            settings['gemini_key'] = new_k
            save_settings(settings)
            st.success("Ok !")
            st.rerun()
    
    st.divider()
    st.write("Historique des actions (Logs)")
    if os.path.exists("activity_logs.csv"):
        st.dataframe(pd.read_csv("activity_logs.csv").tail(50))
