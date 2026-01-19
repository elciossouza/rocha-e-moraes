"""
Módulo de conexão com Google Sheets
Responsável por ler os dados de leads da planilha
"""
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime
import config

# Escopos necessários para acessar Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]


def get_google_sheets_client():
    """
    Cria e retorna um cliente autenticado do Google Sheets
    Funciona tanto local (credentials.json) quanto no Streamlit Cloud (secrets)
    """
    try:
        # Tenta usar secrets do Streamlit Cloud primeiro
        if hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
            credentials = Credentials.from_service_account_info(
                dict(st.secrets["gcp_service_account"]),
                scopes=SCOPES
            )
        else:
            # Fallback para arquivo local
            credentials = Credentials.from_service_account_file(
                config.GOOGLE_SHEETS_CREDENTIALS_FILE,
                scopes=SCOPES
            )
        
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets: {str(e)}")
        return None


@st.cache_data(ttl=300)  # Cache de 5 minutos
def get_leads_data(sheet_name: str) -> pd.DataFrame:
    """
    Busca dados de leads de uma aba específica da planilha
    
    Args:
        sheet_name: Nome da aba na planilha
        
    Returns:
        DataFrame com os dados dos leads
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
        
        # Abre a planilha pelo ID
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        
        # Abre a aba específica
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Obtém todos os dados
        data = worksheet.get_all_records()
        
        # Converte para DataFrame
        df = pd.DataFrame(data)
        
        return df
        
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"Aba '{sheet_name}' não encontrada na planilha.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar dados: {str(e)}")
        return pd.DataFrame()


def get_all_leads() -> pd.DataFrame:
    """
    Busca todos os leads da primeira aba da planilha
    (baseado na estrutura mostrada na imagem)
    
    Returns:
        DataFrame com todos os leads
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
        
        # Abre a planilha pelo ID
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        
        # Pega a primeira aba (ou a aba principal de leads)
        worksheet = spreadsheet.sheet1
        
        # Obtém todos os dados
        data = worksheet.get_all_records()
        
        # Converte para DataFrame
        df = pd.DataFrame(data)
        
        # Padroniza nomes das colunas
        df = standardize_columns(df)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao buscar dados: {str(e)}")
        return pd.DataFrame()


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza os nomes das colunas do DataFrame
    """
    if df.empty:
        return df
    
    # Mapeamento reverso para padronização
    column_rename = {}
    for std_name, original_name in config.COLUMN_MAPPING.items():
        if original_name in df.columns:
            column_rename[original_name] = std_name
    
    df = df.rename(columns=column_rename)
    
    return df


def process_leads_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processa o DataFrame de leads:
    - Converte datas
    - Limpa dados
    - Adiciona colunas auxiliares
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Tenta identificar e converter coluna de data
    date_columns = ['data_hora', 'DATA / HORA', 'data', 'Data', 'DATA']
    date_col = None
    
    for col in date_columns:
        if col in df.columns:
            date_col = col
            break
    
    if date_col:
        try:
            # Tenta diferentes formatos de data
            df['data_hora_parsed'] = pd.to_datetime(df[date_col], errors='coerce')
            df['data'] = df['data_hora_parsed'].dt.date
            df['hora'] = df['data_hora_parsed'].dt.time
            df['dia_semana'] = df['data_hora_parsed'].dt.day_name()
            df['mes'] = df['data_hora_parsed'].dt.month
            df['ano'] = df['data_hora_parsed'].dt.year
        except Exception:
            pass
    
    # Identifica a origem (Meta ou Google)
    origem_columns = ['origem', 'ORIGEM', 'Origem', 'source']
    origem_col = None
    
    for col in origem_columns:
        if col in df.columns:
            origem_col = col
            break
    
    if origem_col:
        df['plataforma'] = df[origem_col].apply(identify_platform)
    
    return df


def identify_platform(origem: str) -> str:
    """
    Identifica a plataforma de origem do lead
    """
    if pd.isna(origem):
        return 'Desconhecido'
    
    origem_lower = str(origem).lower()
    
    if any(x in origem_lower for x in ['facebook', 'meta', 'instagram', 'fb']):
        return 'Meta Ads'
    elif any(x in origem_lower for x in ['google', 'gads', 'adwords', 'busca paga']):
        return 'Google Ads'
    else:
        return 'Outro'


def filter_leads_by_date(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    """
    Filtra leads por período de datas
    """
    if df.empty or 'data' not in df.columns:
        return df
    
    df = df.copy()
    
    # Converte para date se necessário
    if not isinstance(start_date, datetime):
        start_date = pd.to_datetime(start_date).date()
    if not isinstance(end_date, datetime):
        end_date = pd.to_datetime(end_date).date()
    
    mask = (df['data'] >= start_date) & (df['data'] <= end_date)
    
    return df[mask]


def filter_leads_by_platform(df: pd.DataFrame, platform: str) -> pd.DataFrame:
    """
    Filtra leads por plataforma
    """
    if df.empty or 'plataforma' not in df.columns:
        return df
    
    if platform == 'Todos':
        return df
    
    return df[df['plataforma'] == platform]


def get_leads_count_by_campaign(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa leads por campanha
    """
    if df.empty:
        return pd.DataFrame()
    
    # Tenta encontrar coluna de campanha
    camp_columns = ['campanha', 'CAMPANHA', 'Campanha', 'campaign']
    camp_col = None
    
    for col in camp_columns:
        if col in df.columns:
            camp_col = col
            break
    
    if camp_col is None:
        return pd.DataFrame()
    
    grouped = df.groupby(camp_col).size().reset_index(name='leads')
    grouped = grouped.sort_values('leads', ascending=True)
    
    return grouped


def get_leads_count_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa leads por data
    """
    if df.empty or 'data' not in df.columns:
        return pd.DataFrame()
    
    grouped = df.groupby('data').size().reset_index(name='leads')
    grouped = grouped.sort_values('data', ascending=True)
    
    return grouped


def get_leads_count_by_ad_set(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa leads por conjunto de anúncios
    """
    if df.empty:
        return pd.DataFrame()
    
    # Tenta encontrar coluna de conjunto de anúncios
    adset_columns = ['conjunto_anuncios', 'CONJUNTO DE ANÚNCIOS', 'ad_set', 'adset']
    adset_col = None
    
    for col in adset_columns:
        if col in df.columns:
            adset_col = col
            break
    
    if adset_col is None:
        return pd.DataFrame()
    
    grouped = df.groupby(adset_col).size().reset_index(name='leads')
    grouped = grouped.sort_values('leads', ascending=True)
    
    return grouped
