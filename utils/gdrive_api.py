import os
import io
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from utils.config import BASE_DIR, IMG_DIR, DB_PATH, USER_DB

# Scopes pour Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

# ID du dossier racine Google Drive (PARAPHARM)
GDRIVE_FOLDER_ID = st.secrets.get("GDRIVE_FOLDER_ID", "1XalJubOiIDdpUIwCy6NFZeu3UliUU4Fb")

@st.cache_resource
def get_gdrive_service():
    """Initialise et retourne le service Google Drive."""
    creds_dict = None
    if "gsheets" in st.secrets:
        creds_dict = st.secrets["gsheets"]
    elif "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        creds_dict = st.secrets["connections"]["gsheets"]
        
    creds = None
    if creds_dict:
        try:
            # Correction des sauts de ligne si nécessaire
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        except Exception as e:
            st.error(f"Erreur d'authentification Google Drive (secrets) : {e}")
            return None
    elif os.path.exists("google_creds.json"):
        try:
            creds = Credentials.from_service_account_file("google_creds.json", scopes=SCOPES)
        except Exception as e:
            st.error(f"Erreur d'authentification Google Drive (fichier local) : {e}")
            return None
    else:
        # Essayer le répertoire parent (Pharmaciel)
        parent_creds = os.path.join(os.path.dirname(BASE_DIR), "pharmaciel", "google_creds.json")
        if os.path.exists(parent_creds):
            try:
                creds = Credentials.from_service_account_file(parent_creds, scopes=SCOPES)
            except Exception as e:
                pass
                
    if not creds:
        st.error("Aucun identifiant Google Drive trouvé (ni dans st.secrets, ni 'google_creds.json').")
        return None
        
    try:
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        st.error(f"Erreur d'initialisation du service GDrive : {e}")
        return None

def find_or_create_folder(service, folder_name, parent_id=None):
    """Cherche un dossier par nom, s'il n'existe pas, le crée."""
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
        
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    
    if not items:
        # Création du dossier
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
    else:
        return items[0].get('id')

def get_remote_file_id(service, file_name, parent_id):
    """Récupère l'ID d'un fichier dans un dossier spécifique."""
    query = f"name='{file_name}' and '{parent_id}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    if items:
        return items[0].get('id')
    return None

def upload_file_to_gdrive(service, file_path, parent_id, file_name=None):
    """Upload un fichier vers Google Drive."""
    if not file_name:
        file_name = os.path.basename(file_path)
        
    file_id = get_remote_file_id(service, file_name, parent_id)
    
    # Détermination du type MIME
    mime_type = 'application/octet-stream'
    if file_name.endswith('.csv'): mime_type = 'text/csv'
    elif file_name.endswith('.json'): mime_type = 'application/json'
    elif file_name.endswith('.jpg') or file_name.endswith('.jpeg'): mime_type = 'image/jpeg'
    elif file_name.endswith('.png'): mime_type = 'image/png'
    
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    
    if file_id:
        # Update existing
        service.files().update(fileId=file_id, media_body=media).execute()
    else:
        # Create new
        file_metadata = {'name': file_name, 'parents': [parent_id]}
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()

def download_file_from_gdrive(service, file_id, dest_path):
    """Télécharge un fichier depuis Google Drive."""
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.close()

def sync_to_gdrive(message=""):
    """Synchronise les données locales vers Google Drive."""
    service = get_gdrive_service()
    if not service: return False, "Service GDrive non initialisé."
    
    try:
        # Vérifier l'accès au dossier racine
        main_folder_id = GDRIVE_FOLDER_ID
        try:
            service.files().get(fileId=main_folder_id, fields='id').execute()
        except Exception as e:
            if "404" in str(e):
                return False, f"❌ Dossier racine introuvable ou accès refusé. Vérifiez que vous avez partagé le dossier GDrive avec l'email : `{service.auth.signer_email if hasattr(service.auth, 'signer_email') else 'votre bot Google'}`"
            return False, f"❌ Erreur accès GDrive : {e}"
            
        if main_folder_id == "VOTRE_ID_DE_DOSSIER_GDRIVE_ICI":
            main_folder_id = find_or_create_folder(service, "Test_Para_Data")
            
        # Trouver ou créer le dossier Images
        images_folder_id = find_or_create_folder(service, "image_stock", parent_id=main_folder_id)
        
        # 1. Upload Database et Users
        if os.path.exists(DB_PATH):
            upload_file_to_gdrive(service, DB_PATH, main_folder_id)
        if os.path.exists(USER_DB):
            upload_file_to_gdrive(service, USER_DB, main_folder_id)
            
        # 2. Upload Images
        if os.path.exists(IMG_DIR):
            for img_name in os.listdir(IMG_DIR):
                img_path = os.path.join(IMG_DIR, img_name)
                if os.path.isfile(img_path):
                    upload_file_to_gdrive(service, img_path, images_folder_id, img_name)
                    
        return True, "✅ Synchronisation vers Google Drive réussie !"
    except Exception as e:
        return False, f"❌ Erreur lors de la synchronisation vers GDrive : {e}"

def restore_from_gdrive():
    """Restaure les données depuis Google Drive vers le local."""
    service = get_gdrive_service()
    if not service: return False, "Service GDrive non initialisé."
    
    try:
        main_folder_id = GDRIVE_FOLDER_ID
        try:
            service.files().get(fileId=main_folder_id, fields='id').execute()
        except Exception as e:
            if "404" in str(e):
                return False, f"❌ Dossier racine introuvable ou accès refusé. Vérifiez que vous avez partagé le dossier GDrive avec l'email : `{service.auth.signer_email if hasattr(service.auth, 'signer_email') else 'votre bot Google'}`"
            return False, f"❌ Erreur accès GDrive : {e}"
            
        if main_folder_id == "VOTRE_ID_DE_DOSSIER_GDRIVE_ICI":
            # On cherche le dossier par nom
            query = f"mimeType='application/vnd.google-apps.folder' and name='Test_Para_Data' and trashed=false"
            results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])
            if not items:
                return False, "Le dossier Test_Para_Data est introuvable sur GDrive."
            main_folder_id = items[0].get('id')
            
        # Télécharger la base de données et utilisateurs
        db_id = get_remote_file_id(service, os.path.basename(DB_PATH), main_folder_id)
        if db_id: download_file_from_gdrive(service, db_id, DB_PATH)
        
        user_db_id = get_remote_file_id(service, os.path.basename(USER_DB), main_folder_id)
        if user_db_id: download_file_from_gdrive(service, user_db_id, USER_DB)
        
        # Télécharger les images
        images_folder_id = get_remote_file_id(service, "image_stock", main_folder_id)
        if images_folder_id:
            query = f"'{images_folder_id}' in parents and trashed=false"
            results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            img_items = results.get('files', [])
            
            if not os.path.exists(IMG_DIR):
                os.makedirs(IMG_DIR)
                
            for item in img_items:
                dest_path = os.path.join(IMG_DIR, item['name'])
                download_file_from_gdrive(service, item['id'], dest_path)
                
        # Effacer le cache Streamlit car les fichiers ont changé
        st.cache_data.clear()
        return True, "✅ Restauration depuis Google Drive réussie !"
    except Exception as e:
        return False, f"❌ Erreur lors de la restauration depuis GDrive : {e}"
