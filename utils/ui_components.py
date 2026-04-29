import streamlit as st
import urllib.parse
from .styles import get_image_base64
from .database import add_log
from .ai_core import get_ai_response

def show_product_details(row, settings):
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
        
        st.divider()
        p_text = f"{row['PPA']} DA" if row['PPA'] > 0 else "Prix sur demande"
        st.metric("Prix Unitaire", p_text)
        
        msg = urllib.parse.quote(f"Pharmaciel - {row['Produit']} | Prix: {row['PPA']} DA")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank" style="background-color:#25D366; color:white; padding:10px; border-radius:5px; text-decoration:none; display:block; text-align:center;">Partager WhatsApp</a>', unsafe_allow_html=True)

    # Assistant IA
    st.divider()
    with st.expander("🤖 Assistant Expert IA", expanded=True):
        st.chat_message("assistant").write(f"Bonjour ! Que souhaitez-vous savoir sur le **{row['Produit']}** ?")
        q = st.text_input("Votre question...", key=f"ai_{row['Produit']}")
        if q:
            resp = get_ai_response(row, q, settings.get('gemini_key', ''))
            st.chat_message("user").write(q)
            st.chat_message("assistant").write(resp)
            add_log("Question IA", f"{row['Produit']}: {q}")
