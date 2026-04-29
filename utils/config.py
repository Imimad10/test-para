import os

# Chemins de base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, 'images')
DB_PATH = os.path.join(BASE_DIR, 'database_para.csv')
USER_DB = os.path.join(BASE_DIR, 'users.csv')
SALES_DB = os.path.join(BASE_DIR, 'ventes.csv')
LOGS_FILE = os.path.join(BASE_DIR, 'activity_logs.csv')
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')
SESSION_FILE = os.path.join(BASE_DIR, 'session.json')

# Création des dossiers si nécessaire
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)
