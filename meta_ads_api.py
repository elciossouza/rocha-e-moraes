"""
Módulo de conexão com Meta Ads API
"""
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import config

# Atualizado para versão mais recente da API
META_API_URL = "https://graph.facebook.com/v21.0"


def get_meta_credentials():
    """Obtém as credenciais do Meta Ads dos secrets ou config"""
    access_token = ""
    ad_account_id = ""
    
    # Primeiro tenta ler dos secrets do Streamlit
    try:
        if hasattr(st, 'secrets') and st.secrets is not None:
            try:
                if "META_ACCESS_TOKEN" in st.secrets:
                    access_token = str(st.secrets["META_ACCESS_TOKEN"]).strip()
            except Exception:
                pass
            
            try:
                if "META_AD_ACCOUNT_ID" in st.secrets:
                    ad_account_id = str(st.secrets["META_AD_ACCOUNT_ID"]).strip()
            except Exception:
                pass
    except Exception as e:
        pass
    
    # Se não encontrou nos secrets, tenta no config.py
    if not access_token:
        access_token = getattr(config, 'META_ACCESS_TOKEN', '')
        if access_token:
            access_token = str(access_token).strip()
    
    if not ad_account_id:
        ad_account_id = getattr(config, 'META_AD_ACCOUNT_ID', '')
        if ad_account_id:
            ad_account_id = str(ad_account_id).strip()
    
    # Garantir que o ad_account_id tenha o prefixo 'act_'
    if ad_account_id and not ad_account_id.startswith('act_'):
        ad_account_id = f"act_{ad_account_id}"
    
    return access_token, ad_account_id


def is_meta_configured():
    """Verifica se as credenciais do Meta estão configuradas"""
    access_token, ad_account_id = get_meta_credentials()
    
    # Validações
    token_valid = bool(access_token and len(access_token) > 20)
    account_valid = bool(ad_account_id and len(ad_account_id) > 5)
    
    return token_valid and account_valid


def debug_meta_connection():
    """Retorna informações de debug da conexão Meta"""
    access_token, ad_account_id = get_meta_credentials()
    
    info = {
        "token_encontrado": bool(access_token),
        "token_tamanho": len(access_token) if access_token else 0,
        "token_inicio": access_token[:20] + "..." if access_token and len(access_token) > 20 else "Token muito curto ou vazio",
        "account_id": ad_account_id if ad_account_id else "N/A",
        "account_tem_prefixo_act": ad_account_id.startswith('act_') if ad_account_id else False,
        "secrets_disponivel": hasattr(st, 'secrets'),
        "api_version": META_API_URL,
    }
    
    # Verifica se secrets estão acessíveis
    try:
        if hasattr(st, 'secrets') and st.secrets is not None:
            info["meta_token_in_secrets"] = "META_ACCESS_TOKEN" in st.secrets
            info["meta_account_in_secrets"] = "META_AD_ACCOUNT_ID" in st.secrets
        else:
            info["meta_token_in_secrets"] = False
            info["meta_account_in_secrets"] = False
    except Exception as e:
        info["secrets_error"] = str(e)
    
    # Testa a conexão com a API
    if access_token and ad_account_id:
        info["teste_conexao"] = test_meta_connection(access_token, ad_account_id)
    else:
        info["teste_conexao"] = "Credenciais não configuradas"
    
    return info


def test_meta_connection(access_token, ad_account_id):
    """Testa a conexão com a API do Meta"""
    try:
        url = f"{META_API_URL}/{ad_account_id}"
        params = {
            'access_token': access_token,
            'fields': 'name,account_status'
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'error' in data:
            error_msg = data['error'].get('message', 'Erro desconhecido')
            error_code = data['error'].get('code', 'N/A')
            return f"Erro {error_code}: {error_msg}"
        
        return f"Conectado - Conta: {data.get('name', 'N/A')}"
    except requests.exceptions.Timeout:
        return "Timeout na conexão"
    except Exception as e:
        return f"Erro: {str(e)}"


@st.cache_data(ttl=300)
def get_meta_campaigns(start_date, end_date):
    """Obtém dados das campanhas do Meta Ads"""
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
        'level': 'campaign',
        'fields': 'campaign_name,campaign_id,spend,impressions,clicks,reach,actions,cost_per_action_type,ctr,cpc',
        'time_range': f'{{"since":"{start_str}","until":"{end_str}"}}',
        'time_increment': 1,
        'limit': 500
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'error' in data:
            error_msg = data['error'].get('message', 'Erro desconhecido')
            error_code = data['error'].get('code', 'N/A')
            st.error(f"Erro na API do Meta ({error_code}): {error_msg}")
            return pd.DataFrame()
        
        if 'data' not in data or len(data['data']) == 0:
            return pd.DataFrame()
        
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
            
            # Processa as ações para encontrar leads
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
        
        # Converte a coluna de data
        if 'data' in df.columns and not df.empty:
            df['data'] = pd.to_datetime(df['data']).dt.date
        
        return df
        
    except requests.exceptions.Timeout:
        st.error("Timeout ao conectar com Meta Ads. Tente novamente.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao conectar com Meta Ads: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_meta_adsets(start_date, end_date):
    """Obtém dados dos conjuntos de anúncios do Meta Ads"""
    access_token, ad_account_id = get_meta_credentials()
    
    if not access_token or not ad_account_id:
        return pd.DataFrame()
    
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
        response = requests.get(url, params=params, timeout=30)
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
            
            # Processa leads
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
    """Obtém resumo geral da conta Meta Ads"""
    access_token, ad_account_id = get_meta_credentials()
    
    if not access_token or not ad_account_id:
        return None
    
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
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'error' in data:
            error_msg = data['error'].get('message', 'Erro')
            st.error(f"Erro Meta API: {error_msg}")
            return None
            
        if 'data' not in data or len(data['data']) == 0:
            return None
        
        item = data['data'][0]
        
        # Conta leads
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
        
    except requests.exceptions.Timeout:
        st.error("Timeout ao conectar com Meta Ads")
        return None
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return None


def get_campaigns_by_name(df):
    """Agrupa campanhas por nome"""
    if df.empty:
        return pd.DataFrame()
    
    grouped = df.groupby('campanha').agg({
        'valor_gasto': 'sum',
        'impressoes': 'sum',
        'cliques': 'sum',
        'leads': 'sum'
    }).reset_index()
    
    grouped['cpl'] = grouped.apply(
        lambda row: row['valor_gasto'] / row['leads'] if row['leads'] > 0 else 0, 
        axis=1
    )
    
    grouped = grouped.sort_values('valor_gasto', ascending=True)
    
    return grouped
