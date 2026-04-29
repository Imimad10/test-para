import google.generativeai as genai
import streamlit as st

def get_ai_response(row, user_q, api_key):
    if not api_key:
        return "Simulation: Le produit {} du labo {} est un excellent choix.".format(row['Produit'], row['Laboratoire'])
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""
        Tu es un expert en parapharmacie pour 'Pharmaciel'. 
        Produit: {row['Produit']} | Labo: {row['Laboratoire']} | Famille: {row['Famille']}
        Question: {user_q}
        Réponds de manière pro et rassurante.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erreur IA : {str(e)}"
