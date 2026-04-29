import pandas as pd
import json
import os
import streamlit as st
from datetime import datetime
from .config import DB_PATH, SETTINGS_FILE, LOGS_FILE, SALES_DB

@st.cache_data
def load_data():
    if os.path.exists(DB_PATH):
        df = pd.read_csv(DB_PATH)
        # Nettoyage et colonnes obligatoires
        required = ['Promo', 'Prix_Achat', 'Description', 'Famille', 'Laboratoire', 'DDP', 'Dépôt', 'Arrivage', 'PPA', 'Quantité', 'image_path']
        for c in required:
            if c not in df.columns:
                if c == 'Promo': df[c] = False
                elif c in ['Prix_Achat', 'PPA', 'Quantité']: df[c] = 0
                else: df[c] = ""
        return df
    return pd.DataFrame(columns=['Produit', 'Laboratoire', 'Quantité', 'PPA', 'image_path', 'Famille', 'DDP', 'Promo', 'Prix_Achat', 'Description', 'Dépôt', 'Arrivage'])

def save_data(df, path=DB_PATH):
    df.to_csv(path, index=False, encoding='utf-8-sig')
    st.cache_data.clear()
    add_log("Mise à jour Base de données", f"Fichier: {os.path.basename(path)}")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"marquee": "Bienvenue sur Pharmaciel Pro", "gemini_key": ""}

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

def save_sale(cart_dict, total, user):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_sales = []
    for k, v in cart_dict.items():
        new_sales.append({"Date": now, "Client": user, "Produit": k, "Qté": v['qty'], "Prix": v['price'], "Total": v['qty'] * v['price']})
    df_new = pd.DataFrame(new_sales)
    if os.path.exists(SALES_DB):
        df_new.to_csv(SALES_DB, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        df_new.to_csv(SALES_DB, index=False, encoding='utf-8-sig')
    add_log("Vente Validée", f"Total: {total} DA")
