"""
Módulo de conexão com Google Sheets
Responsável por ler os dados de leads da planilha
"""
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime
import re
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


def parse_date_flexible(date_value):
    """
    Converte diferentes formatos de data para datetime
    Suporta formatos como:
    - 2025-12-02T03:52:08.000Z (ISO)
    - 2025-09-19 09:10:28
    - NOVEMBRO, Novembro, novembro
    - 21:06:14.000Z (apenas hora)
    - Vazio ou None
    """
    if pd.isna(date_value) or date_value is None or str(date_value).strip() == '':
        return None
    
    date_str = str(date_value).strip()
    
    # Se for apenas um mês escrito (NOVEMBRO, Dezembro, etc.)
    meses = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    
    date_lower = date_str.lower()
    if date_lower in meses:
        # Retorna o primeiro dia do mês no ano atual
        return datetime(datetime.now().year, meses[date_lower], 1)
    
    # Lista de formatos para tentar
    formatos = [
        '%Y-%m-%dT%H:%M:%S.%fZ',  # 2025-12-02T03:52:08.000Z
        '%Y-%m-%dT%H:%M:%SZ',     # 2025-12-02T03:52:08Z
        '%Y-%m-%dT%H:%M:%S',      # 2025-12-02T03:52:08
        '%Y-%m-%d %H:%M:%S',      # 2025-12-02 03:52:08
        '%Y-%m-%d',               # 2025-12-02
        '%d/%m/%Y %H:%M:%S',      # 02/12/2025 03:52:08
        '%d/%m/%Y %H:%M',         # 02/12/2025 03:52
        '%d/%m/%Y',               # 02/12/2025
        '%d-%m-%Y',               # 02-12-2025
        '%m/%d/%Y',               # 12/02/2025
    ]
    
    for formato in formatos:
        try:
            return datetime.strptime(date_str, formato)
        except ValueError:
            continue
    
    # Se começa com hora (21:06:14.000Z), ignora
    if re.match(r'^\d{1,2}:\d{2}', date_str):
        return None
    
    # Última tentativa: pandas
    try:
        return pd.to_datetime(date_str)
    except:
        return None


@st.cache_data(ttl=300)  # Cache de 5 minutos
def get_sheet_data(sheet_name: str) -> pd.DataFrame:
    """
    Busca dados de uma aba específica da planilha
    
    Args:
        sheet_name: Nome da aba na planilha
        
    Returns:
        DataFrame com os dados
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
        st.error(f"Erro ao buscar dados da aba '{sheet_name}': {str(e)}")
        return pd.DataFrame()


def process_dataframe_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processa e padroniza as datas do DataFrame
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Tenta identificar coluna de data
    date_columns = ['DATA / HORA', 'data_hora', 'DATA', 'Data', 'data', 'MÊS']
    date_col = None
    
    for col in date_columns:
        if col in df.columns:
            date_col = col
            break
    
    if date_col:
        # Aplica a função de parse flexível
        df['data_parsed'] = df[date_col].apply(parse_date_flexible)
        df['data'] = df['data_parsed'].apply(lambda x: x.date() if x else None)
        df['mes'] = df['data_parsed'].apply(lambda x: x.month if x else None)
        df['ano'] = df['data_parsed'].apply(lambda x: x.year if x else None)
    
    # Identifica a origem (Meta ou Google)
    origem_columns = ['ORIGEM', 'origem', 'Origem']
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
    elif any(x in origem_lower for x in ['google', 'gads', 'adwords', 'pesquisa']):
        return 'Google Ads'
    else:
        return 'Outro'


@st.cache_data(ttl=300)
def get_all_leads() -> pd.DataFrame:
    """
    Busca todos os leads da aba principal
    """
    df = get_sheet_data(config.SHEET_NAME_LEADS)
    df = process_dataframe_dates(df)
    return df


@st.cache_data(ttl=300)
def get_leads_qualificados() -> pd.DataFrame:
    """
    Busca leads qualificados
    """
    df = get_sheet_data(config.SHEET_NAME_QUALIFICADOS)
    df = process_dataframe_dates(df)
    return df


@st.cache_data(ttl=300)
def get_leads_desqualificados() -> pd.DataFrame:
    """
    Busca leads desqualificados
    """
    df = get_sheet_data(config.SHEET_NAME_DESQUALIFICADOS)
    df = process_dataframe_dates(df)
    return df


@st.cache_data(ttl=300)
def get_contratos_fechados() -> pd.DataFrame:
    """
    Busca contratos fechados (convertidos)
    """
    df = get_sheet_data(config.SHEET_NAME_CONVERTIDOS)
    df = process_dataframe_dates(df)
    return df


@st.cache_data(ttl=300)
def get_funnel_data() -> dict:
    """
    Retorna dados para o funil de conversão
    """
    leads_df = get_all_leads()
    qualificados_df = get_leads_qualificados()
    desqualificados_df = get_leads_desqualificados()
    convertidos_df = get_contratos_fechados()
    
    return {
        'total_leads': len(leads_df),
        'qualificados': len(qualificados_df),
        'desqualificados': len(desqualificados_df),
        'convertidos': len(convertidos_df),
        'leads_df': leads_df,
        'qualificados_df': qualificados_df,
        'desqualificados_df': desqualificados_df,
        'convertidos_df': convertidos_df
    }


def filter_by_date(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    """
    Filtra DataFrame por período de datas
    """
    if df.empty or 'data' not in df.columns:
        return df
    
    df = df.copy()
    
    # Remove linhas sem data válida
    df = df[df['data'].notna()]
    
    # Converte para date se necessário
    if hasattr(start_date, 'date'):
        start_date = start_date.date()
    if hasattr(end_date, 'date'):
        end_date = end_date.date()
    
    mask = (df['data'] >= start_date) & (df['data'] <= end_date)
    
    return df[mask]


def filter_by_platform(df: pd.DataFrame, platform: str) -> pd.DataFrame:
    """
    Filtra leads por plataforma
    """
    if df.empty or 'plataforma' not in df.columns:
        return df
    
    if platform == 'Todos':
        return df
    
    return df[df['plataforma'] == platform]


def get_leads_by_campaign(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa leads por campanha
    """
    if df.empty:
        return pd.DataFrame()
    
    camp_columns = ['CAMPANHA', 'campanha', 'Campanha']
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


def get_leads_by_origin(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa leads por origem
    """
    if df.empty:
        return pd.DataFrame()
    
    origem_columns = ['ORIGEM', 'origem', 'Origem']
    origem_col = None
    
    for col in origem_columns:
        if col in df.columns:
            origem_col = col
            break
    
    if origem_col is None:
        return pd.DataFrame()
    
    grouped = df.groupby(origem_col).size().reset_index(name='leads')
    grouped = grouped.sort_values('leads', ascending=True)
    
    return grouped


def get_leads_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa leads por data
    """
    if df.empty or 'data' not in df.columns:
        return pd.DataFrame()
    
    # Remove linhas sem data
    df_valid = df[df['data'].notna()]
    
    if df_valid.empty:
        return pd.DataFrame()
    
    grouped = df_valid.groupby('data').size().reset_index(name='leads')
    grouped = grouped.sort_values('data', ascending=True)
    
    return grouped
