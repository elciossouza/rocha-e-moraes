"""
Módulo de conexão com Meta Ads API
Responsável por buscar dados de campanhas do Facebook/Instagram Ads
"""
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import config

# URL base da API do Meta
META_API_URL = "https://graph.facebook.com/v18.0"


def get_meta_credentials():
    """
    Obtém as credenciais do Meta Ads dos secrets ou variáveis de ambiente
    """
    access_token = None
    ad_account_id = None
    
    try:
        if hasattr(st, 'secrets'):
            access_token = st.secrets.get("META_ACCESS_TOKEN", "")
            ad_account_id = st.secrets.get("META_AD_ACCOUNT_ID", "")
    except:
        pass
    
    if not access_token:
        access_token = config.META_ACCESS_TOKEN
    if not ad_account_id:
        ad_account_id = config.META_AD_ACCOUNT_ID
    
    return access_token, ad_account_id


def is_meta_configured():
    """
    Verifica se as credenciais do Meta estão configuradas
    """
    access_token, ad_account_id = get_meta_credentials()
    return bool(access_token and ad_account_id)


@st.cache_data(ttl=300)
def get_meta_campaigns(start_date, end_date):
    """
    Busca dados de campanhas do Meta Ads
    
    Args:
        start_date: Data inicial (date ou datetime)
        end_date: Data final (date ou datetime)
    
    Returns:
        DataFrame com dados das campanhas
    """
    access_token, ad_account_id = get_meta_credentials()
    
    if not access_token or not ad_account_id:
        return pd.DataFrame()
    
    # Formata as datas
    if hasattr(start_date, 'strftime'):
        start_str = start_date.strftime('%Y-%m-%d')
    else:
        start_str = str(start_date)
    
    if hasattr(end_date, 'strftime'):
        end_str = end_date.strftime('%Y-%m-%d')
    else:
        end_str = str(end_date)
    
    # Endpoint para insights de campanhas
    url = f"{META_API_URL}/{ad_account_id}/insights"
    
    params = {
        'access_token': access_token,
        'level': 'campaign',
        'fields': 'campaign_name,campaign_id,spend,impressions,clicks,reach,actions,cost_per_action_type,ctr,cpc',
        'time_range': f'{{"since":"{start_str}","until":"{end_str}"}}',
        'time_increment': 1,  # Dados diários
        'limit': 500
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'error' in data:
            st.error(f"Erro na API do Meta: {data['error'].get('message', 'Erro desconhecido')}")
            return pd.DataFrame()
        
        if 'data' not in data or len(data['data']) == 0:
            return pd.DataFrame()
        
        # Processa os dados
        campaigns = []
        for item in data['data']:
            campaign = {
                'campanha': item.get('campaign_name', 'N/A'),
                'campaign_id': item.get('campaign_id', ''),
                'data': item.get('date_start', ''),
                'valor_gasto': float(item.get('spend', 0)),
                'impressoes': int(item.get('impressions', 0)),
                'cliques': int(item.get('clicks', 0)),
                'alcance': int(item.get('reach', 0)),
                'ctr': float(item.get('ctr', 0)),
                'cpc': float(item.get('cpc', 0)) if item.get('cpc') else 0,
            }
            
            # Extrai leads das ações
            actions = item.get('actions', [])
            leads = 0
            for action in actions:
                if action.get('action_type') in ['lead', 'onsite_conversion.lead_grouped', 'offsite_conversion.fb_pixel_lead']:
                    leads += int(action.get('value', 0))
            campaign['leads'] = leads
            
            # Calcula CPL
            if leads > 0:
                campaign['cpl'] = campaign['valor_gasto'] / leads
            else:
                campaign['cpl'] = 0
            
            campaigns.append(campaign)
        
        df = pd.DataFrame(campaigns)
        
        # Converte data
        if 'data' in df.columns and not df.empty:
            df['data'] = pd.to_datetime(df['data']).dt.date
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao conectar com Meta Ads: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_meta_adsets(start_date, end_date):
    """
    Busca dados de conjuntos de anúncios do Meta Ads
    """
    access_token, ad_account_id = get_meta_credentials()
    
    if not access_token or not ad_account_id:
        return pd.DataFrame()
    
    # Formata as datas
    if hasattr(start_date, 'strftime'):
        start_str = start_date.strftime('%Y-%m-%d')
    else:
        start_str = str(start_date)
    
    if hasattr(end_date, 'strftime'):
        end_str = end_date.strftime('%Y-%m-%d')
    else:
        end_str = str(end_date)
    
    url = f"{META_API_URL}/{ad_account_id}/insights"
    
    params = {
        'access_token': access_token,
        'level': 'adset',
        'fields': 'adset_name,adset_id,campaign_name,spend,impressions,clicks,actions',
        'time_range': f'{{"since":"{start_str}","until":"{end_str}"}}',
        'limit': 500
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'error' in data or 'data' not in data:
            return pd.DataFrame()
        
        adsets = []
        for item in data['data']:
            adset = {
                'conjunto_anuncios': item.get('adset_name', 'N/A'),
                'campanha': item.get('campaign_name', 'N/A'),
                'valor_gasto': float(item.get('spend', 0)),
                'impressoes': int(item.get('impressions', 0)),
                'cliques': int(item.get('clicks', 0)),
            }
            
            # Extrai leads
            actions = item.get('actions', [])
            leads = 0
            for action in actions:
                if action.get('action_type') in ['lead', 'onsite_conversion.lead_grouped', 'offsite_conversion.fb_pixel_lead']:
                    leads += int(action.get('value', 0))
            adset['leads'] = leads
            
            if leads > 0:
                adset['cpl'] = adset['valor_gasto'] / leads
            else:
                adset['cpl'] = 0
            
            adsets.append(adset)
        
        return pd.DataFrame(adsets)
        
    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_meta_summary(start_date, end_date):
    """
    Retorna resumo dos dados do Meta Ads
    """
    access_token, ad_account_id = get_meta_credentials()
    
    if not access_token or not ad_account_id:
        return None
    
    # Formata as datas
    if hasattr(start_date, 'strftime'):
        start_str = start_date.strftime('%Y-%m-%d')
    else:
        start_str = str(start_date)
    
    if hasattr(end_date, 'strftime'):
        end_str = end_date.strftime('%Y-%m-%d')
    else:
        end_str = str(end_date)
    
    url = f"{META_API_URL}/{ad_account_id}/insights"
    
    params = {
        'access_token': access_token,
        'fields': 'spend,impressions,clicks,reach,actions,ctr,cpc',
        'time_range': f'{{"since":"{start_str}","until":"{end_str}"}}',
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'error' in data or 'data' not in data or len(data['data']) == 0:
            return None
        
        item = data['data'][0]
        
        # Extrai leads
        actions = item.get('actions', [])
        leads = 0
        for action in actions:
            if action.get('action_type') in ['lead', 'onsite_conversion.lead_grouped', 'offsite_conversion.fb_pixel_lead']:
                leads += int(action.get('value', 0))
        
        valor_gasto = float(item.get('spend', 0))
        
        summary = {
            'valor_gasto': valor_gasto,
            'impressoes': int(item.get('impressions', 0)),
            'cliques': int(item.get('clicks', 0)),
            'alcance': int(item.get('reach', 0)),
            'leads': leads,
            'ctr': float(item.get('ctr', 0)),
            'cpc': float(item.get('cpc', 0)) if item.get('cpc') else 0,
            'cpl': valor_gasto / leads if leads > 0 else 0
        }
        
        return summary
        
    except Exception as e:
        return None


def get_campaigns_by_name(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa campanhas por nome
    """
    if df.empty:
        return pd.DataFrame()
    
    grouped = df.groupby('campanha').agg({
        'valor_gasto': 'sum',
        'impressoes': 'sum',
        'cliques': 'sum',
        'leads': 'sum'
    }).reset_index()
    
    # Recalcula CPL
    grouped['cpl'] = grouped.apply(
        lambda row: row['valor_gasto'] / row['leads'] if row['leads'] > 0 else 0, 
        axis=1
    )
    
    grouped = grouped.sort_values('valor_gasto', ascending=True)
    
    return grouped
