import streamlit as st
import pandas as pd
import os
import json
from .config import USER_DB, SESSION_FILE
from .database import add_log

def load_users():
    if os.path.exists(USER_DB):
        return pd.read_csv(USER_DB)
    df = pd.DataFrame([{"user": "admin", "pw": "1992", "role": "Responsable"}])
    df.to_csv(USER_DB, index=False)
    return df

def login():
    if 'auth' not in st.session_state: st.session_state.auth = False
    if 'cart' not in st.session_state: st.session_state.cart = {}
    
    # Auto-login
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
        st.success("👋 Vous êtes client ? Accédez directement à notre catalogue.")
        if st.button("🌐 VOIR LE CATALOGUE PRODUITS", type="primary", use_container_width=True):
            st.session_state.auth, st.session_state.user_role, st.session_state.current_user = True, "Client", "Visiteur"
            add_log("Accès Visiteur")
            st.rerun()
        
        st.divider()
        with st.expander("🔑 Espace Collaborateur", expanded=False):
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

def logout():
    if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
    st.session_state.auth = False
    st.session_state.user_role = None
    st.session_state.current_user = None
    st.rerun()
