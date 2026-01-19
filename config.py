"""
Configurações do Dashboard
Carrega variáveis de ambiente e define constantes
Suporta tanto .env local quanto Streamlit Cloud Secrets
"""
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env (para uso local)
load_dotenv()

def get_config(key: str, default: str = "") -> str:
    """
    Obtém configuração do Streamlit Secrets ou variáveis de ambiente
    """
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.getenv(key, default)

# ===========================================
# GOOGLE SHEETS
# ===========================================
GOOGLE_SHEETS_CREDENTIALS_FILE = get_config("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
SPREADSHEET_ID = get_config("SPREADSHEET_ID", "")

# Nomes das abas na planilha
SHEET_NAME_META_LEADS = get_config("SHEET_NAME_META_LEADS", "Meta Ads Leads")
SHEET_NAME_GOOGLE_LEADS = get_config("SHEET_NAME_GOOGLE_LEADS", "Google Ads Leads")

# ===========================================
# GOOGLE ADS API
# ===========================================
GOOGLE_ADS_DEVELOPER_TOKEN = get_config("GOOGLE_ADS_DEVELOPER_TOKEN", "")
GOOGLE_ADS_CLIENT_ID = get_config("GOOGLE_ADS_CLIENT_ID", "")
GOOGLE_ADS_CLIENT_SECRET = get_config("GOOGLE_ADS_CLIENT_SECRET", "")
GOOGLE_ADS_REFRESH_TOKEN = get_config("GOOGLE_ADS_REFRESH_TOKEN", "")
GOOGLE_ADS_CUSTOMER_ID = get_config("GOOGLE_ADS_CUSTOMER_ID", "")

# ===========================================
# META ADS API
# ===========================================
META_ACCESS_TOKEN = get_config("META_ACCESS_TOKEN", "")
META_AD_ACCOUNT_ID = get_config("META_AD_ACCOUNT_ID", "")
META_APP_ID = get_config("META_APP_ID", "")
META_APP_SECRET = get_config("META_APP_SECRET", "")

# ===========================================
# DASHBOARD
# ===========================================
DASHBOARD_TITLE = os.getenv("DASHBOARD_TITLE", "Dashboard de Ads")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Minha Empresa")

# ===========================================
# MAPEAMENTO DE COLUNAS DA PLANILHA
# Ajuste conforme os nomes das suas colunas
# ===========================================
COLUMN_MAPPING = {
    "data_hora": "DATA / HORA",
    "origem": "ORIGEM",
    "campanha": "CAMPANHA",
    "conjunto_anuncios": "CONJUNTO DE ANÚNCIOS",
    "criativo": "CRIATIVO",
    "nome": "NOME",
    "email": "E-MAIL",
    "telefone": "TELEFONE",
    "facebook_id": "ID DO FACEBOOK"
}

# ===========================================
# CORES DO DASHBOARD
# ===========================================
COLORS = {
    "primary": "#1a73e8",      # Azul Google
    "secondary": "#0668E1",     # Azul Meta/Facebook
    "success": "#34A853",       # Verde
    "warning": "#FBBC04",       # Amarelo
    "danger": "#EA4335",        # Vermelho
    "dark": "#202124",          # Cinza escuro
    "light": "#F8F9FA",         # Cinza claro
    "meta": "#0668E1",          # Azul Meta
    "google": "#4285F4"         # Azul Google
}
