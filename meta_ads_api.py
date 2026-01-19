"""
Módulo de conexão com Meta Ads API
"""
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import config

META_API_URL = "https://graph.facebook.com/v18.0"


def get_meta_credentials():
    access_token = ""
    ad_account_id = ""
    
    try:
        if hasattr(st, 'secrets'):
            if "META_ACCESS_TOKEN" in st.secrets:
                access_token = str(st.secrets["META_ACCESS_TOKEN"])
            if "META_AD_ACCOUNT_ID" in st.secrets:
                ad_account_id = str(st.secrets["META_AD_ACCOUNT_ID"])
    except Exception as e:
        st.error(f"Erro ao ler secrets: {e}")
    
    if not access_token:
        access_token = getattr(config, 'META_ACCESS_TOKEN', '')
    if not ad_account_id:
        ad_account_id = getattr(config, 'META_AD_ACCOUNT_ID', '')
    
    return access_token, ad_account_id


def is_meta_configured():
    access_token, ad_account_id = get_meta_credentials()
    token_len = len(access_token) if access_token else 0
    account_len = len(ad_account_id) if ad_account_id else 0
    return bool(access_token and ad_account_id and token_len > 10 and account_len > 5)


def debug_meta_connection():
    access_token, ad_account_id = get_meta_credentials()
    
    info = {
        "token_encontrado": bool(access_token),
        "token_tamanho": len(access_token) if access_token else 0,
        "token_inicio": access_token[:10] + "..." if access_token and len(access_token) > 10 else "N/A",
        "account_id": ad_account_id if ad_account_id else "N/A",
        "secrets_disponivel": hasattr(st, 'secrets'),
    }
    
    try:
        if hasattr(st, 'secrets'):
            info["meta_token_in_secrets"] = "META_ACCESS_TOKEN" in st.secrets
            info["meta_account_in_secrets"] = "META_AD_ACCOUNT_ID" in st.secrets
    except:
        pass
    
    return info


@st.cache_data(ttl=300)
def get_meta_campaigns(start_date, end_date):
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
        'level': 'campaign',
        'fields': 'campaign_name,campaign_id,spend,impressions,clicks,reach,actions,cost_per_action_type,ctr,cpc',
        'time_range': f'{{"since":"{start_str}","until":"{end_str}"}}',
        'time_increment': 1,
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
            
            actions = item.get('actions', [])
            leads = 0
            for action in actions:
                if action.get('action_type') in ['lead', 'onsite_conversion.lead_grouped', 'offsite_conversion.fb_pixel_lead']:
                    leads += int(action.get('value', 0))
            campaign['leads'] = leads
            
            if leads > 0:
                campaign['cpl'] = campaign['valor_gasto'] / leads
            else:
                campaign['cpl'] = 0
            
            campaigns.append(campaign)
        
        df = pd.DataFrame(campaigns)
        
        if 'data' in df.columns and not df.empty:
            df['data'] = pd.to_datetime(df['data']).dt.date
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao conectar com Meta Ads: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_meta_adsets(start_date, end_date):
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
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'error' in data:
            st.error(f"Erro Meta API: {data['error'].get('message', 'Erro')}")
            return None
            
        if 'data' not in data or len(data['data']) == 0:
            return None
        
        item = data['data'][0]
        
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
        st.error(f"Erro: {str(e)}")
        return None


def get_campaigns_by_name(df):
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
