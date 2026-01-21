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
        return datetime(datetime.now().year, meses[date_lower], 1)
    
    # Lista de formatos para tentar
    formatos = [
        '%Y-%m-%dT%H:%M:%S.%fZ',  # 2025-08-11T10:57:25.000Z
        '%Y-%m-%dT%H:%M:%SZ',     # 2025-08-11T10:57:25Z
        '%Y-%m-%dT%H:%M:%S',      # 2025-08-11T10:57:25
        '%Y-%m-%d %H:%M:%S',      # 2025-08-13 16:05:10
        '%Y-%m-%d %H:%M',         # 2025-08-13 16:05
        '%Y-%m-%d',               # 2025-08-13
        '%d.%m.%Y %H:%M:%S',      # 14.01.2026 23:23:00
        '%d.%m.%Y %H:%M',         # 14.01.2026 23:23
        '%d.%m.%Y',               # 14.01.2026
        '%d/%m/%Y %H:%M:%S',      # 14/01/2026 23:23:00
        '%d/%m/%Y %H:%M',         # 14/01/2026 23:23
        '%d/%m/%Y',               # 14/01/2026
        '%d-%m-%Y %H:%M:%S',      # 14-01-2026 23:23:00
        '%d-%m-%Y %H:%M',         # 14-01-2026 23:23
        '%d-%m-%Y',               # 14-01-2026
        '%m/%d/%Y',               # 01/14/2026
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


def parse_currency_value(value):
    """
    Converte valores monetários em diferentes formatos para float
    Exemplos: "R$ 1.500,00", "1500.00", "1.500", "1500", etc.
    """
    if pd.isna(value) or value is None:
        return 0.0
    
    value_str = str(value).strip()
    
    if value_str == '' or value_str.lower() == 'n/a':
        return 0.0
    
    # Remove símbolos de moeda e espaços
    value_str = value_str.replace('R$', '').replace('$', '').replace(' ', '')
    
    # Detecta formato brasileiro (1.234,56) vs americano (1,234.56)
    if ',' in value_str and '.' in value_str:
        # Se vírgula vem depois do ponto, é formato brasileiro
        if value_str.rfind(',') > value_str.rfind('.'):
            value_str = value_str.replace('.', '').replace(',', '.')
        else:
            value_str = value_str.replace(',', '')
    elif ',' in value_str:
        # Só tem vírgula - pode ser decimal brasileiro ou separador de milhar
        parts = value_str.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Provavelmente decimal brasileiro (1500,00)
            value_str = value_str.replace(',', '.')
        else:
            # Provavelmente separador de milhar americano
            value_str = value_str.replace(',', '')
    
    try:
        return float(value_str)
    except ValueError:
        return 0.0


@st.cache_data(ttl=300)
def get_sheet_data(sheet_name: str) -> pd.DataFrame:
    """
    Busca dados de uma aba específica da planilha
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
        
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        return df
        
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"Aba '{sheet_name}' não encontrada na planilha.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar dados da aba '{sheet_name}': {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_sheet_data_raw(sheet_name: str) -> pd.DataFrame:
    """
    Busca dados de uma aba específica usando get_all_values (raw)
    Útil quando as colunas não têm cabeçalho ou precisamos de colunas específicas por letra
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
        
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_values()
        
        if len(data) < 2:
            return pd.DataFrame()
        
        # Primeira linha como cabeçalho
        headers = data[0]
        rows = data[1:]
        
        df = pd.DataFrame(rows, columns=headers)
        
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
    
    # Tenta identificar coluna de data (mais opções)
    date_columns = [
        'DATA / HORA', 'DATA/HORA', 'data_hora', 'DATA', 'Data', 'data', 
        'MÊS', 'Mês', 'DATE', 'Date', 'DATETIME', 'Datetime',
        'Data de Criação', 'DATA DE CRIAÇÃO', 'Criado em', 'CRIADO EM'
    ]
    date_col = None
    
    # Primeiro tenta pelo nome
    for col in date_columns:
        if col in df.columns:
            date_col = col
            break
    
    # Se não encontrou, tenta a primeira coluna
    if date_col is None and len(df.columns) > 0:
        first_col = df.columns[0]
        # Verifica se a primeira coluna parece ter datas
        sample = df[first_col].dropna().head(5).tolist()
        for val in sample:
            if parse_date_flexible(val) is not None:
                date_col = first_col
                break
    
    if date_col:
        df['data_parsed'] = df[date_col].apply(parse_date_flexible)
        df['data'] = df['data_parsed'].apply(lambda x: x.date() if x else None)
        df['mes'] = df['data_parsed'].apply(lambda x: x.month if x else None)
        df['ano'] = df['data_parsed'].apply(lambda x: x.year if x else None)
    
    # Identifica a origem (Meta ou Google)
    origem_columns = ['ORIGEM', 'origem', 'Origem', 'FONTE', 'Fonte', 'fonte', 'SOURCE', 'Source']
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


def filter_by_date(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    """
    Filtra DataFrame por período de datas
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Converte para date se necessário
    if hasattr(start_date, 'date'):
        start_date = start_date.date()
    if hasattr(end_date, 'date'):
        end_date = end_date.date()
    
    # Verifica se tem coluna de data processada
    if 'data' not in df.columns:
        # Tenta processar as datas novamente
        df = process_dataframe_dates(df)
    
    if 'data' not in df.columns:
        # Se ainda não tem coluna de data, retorna o dataframe original
        return df
    
    # Remove linhas sem data válida
    df_filtered = df[df['data'].notna()].copy()
    
    if df_filtered.empty:
        return df_filtered
    
    # Aplica o filtro de datas
    mask = (df_filtered['data'] >= start_date) & (df_filtered['data'] <= end_date)
    
    return df_filtered[mask]


@st.cache_data(ttl=300)
def get_all_leads() -> pd.DataFrame:
    """
    Busca todos os leads da aba principal 'Rocha & Moraes | ADVOGADOS'
    Conta todas as linhas preenchidas a partir da linha 2
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
        
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        
        # Tenta encontrar a aba de leads
        sheet_names_to_try = [
            'Rocha & Moraes | ADVOGADOS',
            'Rocha & Moraes | Advogados', 
            'LEADS',
            'Leads',
            getattr(config, 'SHEET_NAME_LEADS', '')
        ]
        
        worksheet = None
        for name in sheet_names_to_try:
            if not name:
                continue
            try:
                worksheet = spreadsheet.worksheet(name)
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if worksheet is None:
            st.warning("Aba de leads não encontrada.")
            return pd.DataFrame()
        
        # Busca todos os valores (raw) para garantir que pegamos tudo
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            return pd.DataFrame()
        
        # Primeira linha como cabeçalho, resto como dados
        headers = all_values[0]
        rows = all_values[1:]  # A partir da linha 2
        
        # Remove linhas completamente vazias
        rows = [row for row in rows if any(cell.strip() for cell in row)]
        
        if not rows:
            return pd.DataFrame()
        
        # Cria DataFrame
        df = pd.DataFrame(rows, columns=headers)
        
        # Processa datas
        df = process_dataframe_dates(df)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao buscar leads: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_leads_qualificados() -> pd.DataFrame:
    """
    Busca leads qualificados
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
        
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        
        # Tenta encontrar a aba
        sheet_names_to_try = [
            'LEADS QUALIFICADOS',
            'Leads Qualificados',
            'QUALIFICADOS',
            'Qualificados',
            getattr(config, 'SHEET_NAME_QUALIFICADOS', '')
        ]
        
        worksheet = None
        for name in sheet_names_to_try:
            if not name:
                continue
            try:
                worksheet = spreadsheet.worksheet(name)
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if worksheet is None:
            return pd.DataFrame()
        
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            return pd.DataFrame()
        
        headers = all_values[0]
        rows = [row for row in all_values[1:] if any(cell.strip() for cell in row)]
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=headers)
        df = process_dataframe_dates(df)
        
        return df
        
    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_leads_desqualificados() -> pd.DataFrame:
    """
    Busca leads desqualificados
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
        
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        
        # Tenta encontrar a aba
        sheet_names_to_try = [
            'LEADS DESQUALIFICADOS',
            'Leads Desqualificados',
            'DESQUALIFICADOS',
            'Desqualificados',
            getattr(config, 'SHEET_NAME_DESQUALIFICADOS', '')
        ]
        
        worksheet = None
        for name in sheet_names_to_try:
            if not name:
                continue
            try:
                worksheet = spreadsheet.worksheet(name)
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if worksheet is None:
            return pd.DataFrame()
        
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            return pd.DataFrame()
        
        headers = all_values[0]
        rows = [row for row in all_values[1:] if any(cell.strip() for cell in row)]
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=headers)
        df = process_dataframe_dates(df)
        
        return df
        
    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_contratos_fechados() -> pd.DataFrame:
    """
    Busca contratos fechados (convertidos)
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
        
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        
        # Tenta encontrar a aba
        sheet_names_to_try = [
            'CONTRATOS FECHADOS',
            'Contratos Fechados',
            'CONVERTIDOS',
            'Convertidos',
            getattr(config, 'SHEET_NAME_CONVERTIDOS', '')
        ]
        
        worksheet = None
        for name in sheet_names_to_try:
            if not name:
                continue
            try:
                worksheet = spreadsheet.worksheet(name)
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if worksheet is None:
            return pd.DataFrame()
        
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            return pd.DataFrame()
        
        headers = all_values[0]
        rows = [row for row in all_values[1:] if any(cell.strip() for cell in row)]
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=headers)
        df = process_dataframe_dates(df)
        
        return df
        
    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_contratos_com_valores() -> pd.DataFrame:
    """
    Busca contratos fechados com valores da aba 'CONTRATOS FECHADOS'
    Coluna A = Data, Coluna Q = Valor do contrato
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
        
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        
        # Tenta encontrar a aba de contratos
        sheet_names_to_try = ['CONTRATOS FECHADOS', 'Contratos Fechados', 'contratos fechados', 'CONTRATOS', 'Contratos']
        
        worksheet = None
        for name in sheet_names_to_try:
            try:
                worksheet = spreadsheet.worksheet(name)
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if worksheet is None:
            # Se não encontrar, tenta usar a aba de convertidos do config
            if hasattr(config, 'SHEET_NAME_CONVERTIDOS'):
                try:
                    worksheet = spreadsheet.worksheet(config.SHEET_NAME_CONVERTIDOS)
                except:
                    return pd.DataFrame()
            else:
                return pd.DataFrame()
        
        # Busca todos os valores
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            return pd.DataFrame()
        
        # Pega os cabeçalhos
        headers = all_values[0]
        rows = all_values[1:]
        
        # Cria DataFrame
        df = pd.DataFrame(rows, columns=headers)
        
        # Identifica a coluna de data (coluna A ou primeira coluna)
        date_col = df.columns[0] if len(df.columns) > 0 else None
        
        # Identifica a coluna de valor (coluna Q = índice 16, ou procura por nome)
        value_col = None
        
        # Primeiro tenta pela posição (coluna Q = índice 16)
        if len(df.columns) > 16:
            value_col = df.columns[16]
        
        # Se não encontrou ou está vazia, procura por nome
        if value_col is None or (value_col and df[value_col].replace('', pd.NA).dropna().empty):
            value_columns = ['VALOR', 'Valor', 'valor', 'VALOR DO CONTRATO', 'Valor do Contrato', 
                           'VALOR CONTRATO', 'Valor Contrato', 'RECEITA', 'Receita', 'TOTAL', 'Total']
            for col in value_columns:
                if col in df.columns:
                    value_col = col
                    break
        
        if date_col is None or value_col is None:
            return pd.DataFrame()
        
        # Cria DataFrame limpo
        df_clean = pd.DataFrame()
        df_clean['data_original'] = df[date_col]
        df_clean['valor_original'] = df[value_col]
        
        # Processa as datas
        df_clean['data_parsed'] = df_clean['data_original'].apply(parse_date_flexible)
        df_clean['data'] = df_clean['data_parsed'].apply(lambda x: x.date() if x else None)
        df_clean['mes'] = df_clean['data_parsed'].apply(lambda x: x.month if x else None)
        df_clean['ano'] = df_clean['data_parsed'].apply(lambda x: x.year if x else None)
        df_clean['mes_ano'] = df_clean['data_parsed'].apply(
            lambda x: x.strftime('%Y-%m') if x else None
        )
        df_clean['mes_ano_label'] = df_clean['data_parsed'].apply(
            lambda x: x.strftime('%b/%Y') if x else None
        )
        
        # Processa os valores
        df_clean['valor_contrato'] = df_clean['valor_original'].apply(parse_currency_value)
        
        # Remove linhas sem data ou valor válido
        df_clean = df_clean[df_clean['data'].notna()]
        df_clean = df_clean[df_clean['valor_contrato'] > 0]
        
        return df_clean
        
    except Exception as e:
        st.error(f"Erro ao buscar contratos com valores: {str(e)}")
        return pd.DataFrame()


def get_receita_por_periodo(start_date=None, end_date=None) -> dict:
    """
    Calcula a receita total e por mês dentro do período
    """
    df = get_contratos_com_valores()
    
    if df.empty:
        return {
            'receita_total': 0,
            'quantidade_contratos': 0,
            'ticket_medio': 0,
            'receita_por_mes': pd.DataFrame()
        }
    
    # Aplica filtro de data se fornecido
    if start_date is not None and end_date is not None:
        df = filter_by_date(df, start_date, end_date)
    
    if df.empty:
        return {
            'receita_total': 0,
            'quantidade_contratos': 0,
            'ticket_medio': 0,
            'receita_por_mes': pd.DataFrame()
        }
    
    # Calcula totais
    receita_total = df['valor_contrato'].sum()
    quantidade = len(df)
    ticket_medio = receita_total / quantidade if quantidade > 0 else 0
    
    # Agrupa por mês
    receita_mes = df.groupby(['mes_ano', 'mes_ano_label']).agg({
        'valor_contrato': 'sum',
        'data': 'count'
    }).reset_index()
    
    receita_mes.columns = ['mes_ano', 'mes_ano_label', 'receita', 'contratos']
    receita_mes = receita_mes.sort_values('mes_ano')
    
    return {
        'receita_total': receita_total,
        'quantidade_contratos': quantidade,
        'ticket_medio': ticket_medio,
        'receita_por_mes': receita_mes,
        'df_contratos': df
    }


def get_funnel_data(start_date=None, end_date=None) -> dict:
    """
    Retorna dados para o funil de conversão
    Com filtro de data opcional
    """
    # Busca dados de todas as abas
    leads_df = get_all_leads()
    qualificados_df = get_leads_qualificados()
    desqualificados_df = get_leads_desqualificados()
    convertidos_df = get_contratos_fechados()
    
    # Conta total ANTES do filtro (para debug)
    total_antes_filtro = len(leads_df)
    
    # Aplica filtro de data se fornecido
    if start_date is not None and end_date is not None:
        leads_df = filter_by_date(leads_df, start_date, end_date)
        qualificados_df = filter_by_date(qualificados_df, start_date, end_date)
        desqualificados_df = filter_by_date(desqualificados_df, start_date, end_date)
        convertidos_df = filter_by_date(convertidos_df, start_date, end_date)
    
    return {
        'total_leads': len(leads_df),
        'qualificados': len(qualificados_df),
        'desqualificados': len(desqualificados_df),
        'convertidos': len(convertidos_df),
        'leads_df': leads_df,
        'qualificados_df': qualificados_df,
        'desqualificados_df': desqualificados_df,
        'convertidos_df': convertidos_df,
        'total_antes_filtro': total_antes_filtro  # Para debug
    }


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
    
    df_valid = df[df['data'].notna()]
    
    if df_valid.empty:
        return pd.DataFrame()
    
    grouped = df_valid.groupby('data').size().reset_index(name='leads')
    grouped = grouped.sort_values('data', ascending=True)
    
    return grouped


@st.cache_data(ttl=300)
def get_investimento_roas(start_date=None, end_date=None) -> dict:
    """
    Busca dados de investimento da aba 'ROAS' da planilha
    Estrutura: Coluna A = Data, Coluna B = Tipo, Coluna C = Valor
    Filtra por período de datas
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return {'meta_ads': 0, 'google_ads': 0, 'total_investido': 0, 'receita_contratos': 0, 'roas': 0}
        
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        
        # Tenta encontrar a aba ROAS
        worksheet = None
        for name in ['ROAS', 'Roas', 'roas']:
            try:
                worksheet = spreadsheet.worksheet(name)
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if worksheet is None:
            return {'meta_ads': 0, 'google_ads': 0, 'total_investido': 0, 'receita_contratos': 0, 'roas': 0}
        
        # Busca todos os valores
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            return {'meta_ads': 0, 'google_ads': 0, 'total_investido': 0, 'receita_contratos': 0, 'roas': 0}
        
        # Converte datas de filtro
        if start_date and hasattr(start_date, 'date'):
            start_date = start_date.date()
        if end_date and hasattr(end_date, 'date'):
            end_date = end_date.date()
        
        # Inicializa resultado
        meta_ads_total = 0
        google_ads_total = 0
        contratos_total = 0
        
        # Processa as linhas (pula cabeçalho)
        for row in all_values[1:]:
            if len(row) < 3:
                continue
            
            data_str = row[0].strip() if row[0] else ''
            tipo = row[1].strip().lower() if row[1] else ''
            valor_str = row[2].strip() if row[2] else ''
            
            # Pula linhas vazias ou de texto
            if not data_str or not tipo or not valor_str:
                continue
            
            # Pula linha de "retorno sobre investimento" e "total investido"
            if 'retorno' in tipo or 'total' in tipo:
                continue
            
            # Pula linha de texto explicativo
            if 'para cada' in tipo.lower():
                continue
            
            # Parseia a data
            data_parsed = parse_date_flexible(data_str)
            if data_parsed is None:
                continue
            
            data_date = data_parsed.date()
            
            # Aplica filtro de datas se fornecido
            if start_date and end_date:
                if data_date < start_date or data_date > end_date:
                    continue
            
            # Converte valor
            valor = parse_currency_value(valor_str)
            
            # Identifica o tipo
            if 'meta' in tipo or 'facebook' in tipo:
                meta_ads_total += valor
            elif 'google' in tipo:
                google_ads_total += valor
            elif 'contrato' in tipo:
                contratos_total += valor
        
        # Calcula totais
        total_investido = meta_ads_total + google_ads_total
        roas = contratos_total / total_investido if total_investido > 0 else 0
        
        return {
            'meta_ads': meta_ads_total,
            'google_ads': google_ads_total,
            'total_investido': total_investido,
            'receita_contratos': contratos_total,
            'roas': roas
        }
        
    except Exception as e:
        st.error(f"Erro ao buscar dados de ROAS: {str(e)}")
        return {'meta_ads': 0, 'google_ads': 0, 'total_investido': 0, 'receita_contratos': 0, 'roas': 0}


@st.cache_data(ttl=300)
def get_investimento_por_mes() -> pd.DataFrame:
    """
    Busca dados de investimento por mês da aba 'ROAS'
    Agrupa por mês baseado na coluna de data
    Estrutura: Coluna A = Data, Coluna B = Tipo, Coluna C = Valor
    """
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
        
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        
        # Tenta encontrar a aba ROAS
        worksheet = None
        for name in ['ROAS', 'Roas', 'roas']:
            try:
                worksheet = spreadsheet.worksheet(name)
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if worksheet is None:
            return pd.DataFrame()
        
        # Busca todos os valores
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            return pd.DataFrame()
        
        # Dicionário para agrupar por mês
        dados_por_mes = {}
        
        # Processa as linhas (pula cabeçalho)
        for row in all_values[1:]:
            if len(row) < 3:
                continue
            
            data_str = row[0].strip() if row[0] else ''
            tipo = row[1].strip().lower() if row[1] else ''
            valor_str = row[2].strip() if row[2] else ''
            
            # Pula linhas vazias ou de texto
            if not data_str or not tipo or not valor_str:
                continue
            
            # Pula linhas que não são de investimento
            if 'retorno' in tipo or 'total' in tipo or 'para cada' in tipo:
                continue
            
            # Parseia a data
            data_parsed = parse_date_flexible(data_str)
            if data_parsed is None:
                continue
            
            # Cria chave do mês (YYYY-MM)
            mes_ano = data_parsed.strftime('%Y-%m')
            mes_label = data_parsed.strftime('%b/%Y')
            
            # Inicializa mês se não existir
            if mes_ano not in dados_por_mes:
                dados_por_mes[mes_ano] = {
                    'mes_ano': mes_ano,
                    'mes': mes_label,
                    'meta_ads': 0,
                    'google_ads': 0,
                    'receita': 0
                }
            
            # Converte valor
            valor = parse_currency_value(valor_str)
            
            # Identifica o tipo
            if 'meta' in tipo or 'facebook' in tipo:
                dados_por_mes[mes_ano]['meta_ads'] += valor
            elif 'google' in tipo:
                dados_por_mes[mes_ano]['google_ads'] += valor
            elif 'contrato' in tipo:
                dados_por_mes[mes_ano]['receita'] += valor
        
        if not dados_por_mes:
            return pd.DataFrame()
        
        # Converte para DataFrame
        df = pd.DataFrame(list(dados_por_mes.values()))
        
        # Calcula totais e ROAS
        df['total_investido'] = df['meta_ads'] + df['google_ads']
        df['roas'] = df.apply(lambda row: row['receita'] / row['total_investido'] if row['total_investido'] > 0 else 0, axis=1)
        
        # Ordena por mês
        df = df.sort_values('mes_ano')
        
        return df
        
    except Exception as e:
        return pd.DataFrame()
