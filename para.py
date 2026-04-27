import streamlit as st
import pandas as pd
from tinydb import TinyDB, Query
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Pharmaciel Pro", layout="wide", page_icon="🚚")
db = TinyDB('db_pharmaciel.json')
table_livreurs = db.table('livreurs')
table_pointage = db.table('pointages')

# --- FONCTION GÉNÉRATION PDF ---
def generer_pdf(df_valide, nom_livreur, region):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Titre et Infos
    date_heure = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"<b>BORDEREAU DE REMISE - PHARMACIEL</b>", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Livreur :</b> {nom_livreur}", styles['Normal']))
    elements.append(Paragraph(f"<b>Région :</b> {region}", styles['Normal']))
    elements.append(Paragraph(f"<b>Date d'édition :</b> {date_heure}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Préparation des données pour le tableau PDF
    # On ajoute une colonne vide pour la validation au stylo
    data = [["N° Facture", "Client", "Validation (Stylo)"]]
    for _, row in df_valide.iterrows():
        data.append([row['Référence'], row['Client'], ""])

    # Style du tableau
    t = Table(data, colWidths=[100, 300, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- LOGIQUE DE L'APP ---
st.sidebar.title("📦 Pharmaciel Pro")
menu = st.sidebar.radio("Navigation", ["Pointage Factures", "Administration"])

if menu == "Administration":
    st.header("⚙️ Gestion des Livreurs")
    nouveau_nom = st.text_input("Nom du livreur")
    if st.button("Ajouter"):
        if nouveau_nom and not table_livreurs.search(Query().nom == nouveau_nom.upper()):
            table_livreurs.insert({'nom': nouveau_nom.upper()})
            st.success("Ajouté !")
            st.rerun()

elif menu == "Pointage Factures":
    st.header("📝 Pointage des Factures")
    uploaded_file = st.file_uploader("Importer l'export Excel", type=['xlsx'])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        if all(c in df.columns for c in ['Client', 'Référence', 'Région']):
            col_a, col_b = st.columns(2)
            with col_a:
                region_sel = st.selectbox("📍 Région", sorted(df['Région'].unique()))
            with col_b:
                livreurs = [l['nom'] for l in table_livreurs.all()]
                livreur_sel = st.selectbox("🚚 Livreur", livreurs)

            if livreur_sel:
                df_filtre = df[df['Région'] == region_sel].copy()
                df_filtre.insert(0, "Reçu", False)

                edited_df = st.data_editor(df_filtre, hide_index=True, use_container_width=True)

                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("💾 Enregistrer en Base"):
                        factures_ok = edited_df[edited_df['Reçu'] == True]
                        for _, row in factures_ok.iterrows():
                            table_pointage.insert({
                                'date': datetime.now().strftime("%d/%m/%Y %H:%M"),
                                'livreur': livreur_sel,
                                'ref': row['Référence'],
                                'client': row['Client']
                            })
                        st.success("Enregistré !")

                with col_btn2:
                    # Génération du PDF pour les factures cochées
                    factures_pour_pdf = edited_df[edited_df['Reçu'] == True]
                    if not factures_pour_pdf.empty:
                        pdf_file = generer_pdf(factures_pour_pdf, livreur_sel, region_sel)
                        st.download_button(
                            label="📄 Télécharger Bordereau PDF",
                            data=pdf_file,
                            file_name=f"Bordereau_{livreur_sel}_{region_sel}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.info("Cochez des factures pour générer un PDF.")
        else:
            st.error("Colonnes 'Client', 'Référence', 'Région' introuvables.")
