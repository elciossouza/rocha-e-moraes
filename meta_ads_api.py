"""
Módulo de conexão com Meta Ads API (Facebook/Instagram)
Responsável por buscar métricas de campanhas do Meta Ads
"""
import pandas as pd
import requests
import streamlit as st
from datetime import datetime, timedelta
import config

# URL base da API do Meta/Facebook
META_API_BASE_URL = "https://graph.facebook.com/v19.0"


def get_meta_headers() -> dict:
    """
    Retorna headers para requisições à API do Meta
    """
    return {
        "Authorization": f"Bearer {config.META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }


@st.cache_data(ttl=300)  # Cache de 5 minutos
def get_meta_ads_metrics(start_date: str, end_date: str) -> dict:
    """
    Busca métricas agregadas do Meta Ads para um período
    
    Args:
        start_date: Data inicial no formato 'YYYY-MM-DD'
        end_date: Data final no formato 'YYYY-MM-DD'
        
    Returns:
        Dicionário com métricas agregadas
    """
    try:
        account_id = config.META_AD_ACCOUNT_ID
        
        # Endpoint de insights da conta
        url = f"{META_API_BASE_URL}/{account_id}/insights"
        
        params = {
            "access_token": config.META_ACCESS_TOKEN,
            "time_range": f'{{"since":"{start_date}","until":"{end_date}"}}',
            "fields": "spend,impressions,clicks,actions,cost_per_action_type,ctr,cpc",
            "level": "account"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if "data" not in data or len(data["data"]) == 0:
            return get_empty_metrics()
        
        insights = data["data"][0]
        
        # Extrai leads das actions
        leads = 0
        cost_per_lead = 0
        
        if "actions" in insights:
            for action in insights["actions"]:
                if action["action_type"] == "lead":
                    leads = int(action["value"])
                    break
        
        if "cost_per_action_type" in insights:
            for cost_action in insights["cost_per_action_type"]:
                if cost_action["action_type"] == "lead":
                    cost_per_lead = float(cost_action["value"])
                    break
        
        return {
            "cost": float(insights.get("spend", 0)),
            "impressions": int(insights.get("impressions", 0)),
            "clicks": int(insights.get("clicks", 0)),
            "leads": leads,
            "ctr": float(insights.get("ctr", 0)),
            "cpc": float(insights.get("cpc", 0)),
            "cost_per_lead": cost_per_lead
        }
        
    except requests.exceptions.RequestException as e:
        st.error(f"Erro na requisição à API do Meta: {str(e)}")
        return get_empty_metrics()
    except Exception as e:
        st.error(f"Erro ao buscar métricas do Meta Ads: {str(e)}")
        return get_empty_metrics()


@st.cache_data(ttl=300)
def get_meta_ads_campaigns(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Busca métricas por campanha do Meta Ads
    
    Returns:
        DataFrame com métricas por campanha
    """
    try:
        account_id = config.META_AD_ACCOUNT_ID
        
        url = f"{META_API_BASE_URL}/{account_id}/insights"
        
        params = {
            "access_token": config.META_ACCESS_TOKEN,
            "time_range": f'{{"since":"{start_date}","until":"{end_date}"}}',
            "fields": "campaign_id,campaign_name,spend,impressions,clicks,actions",
            "level": "campaign",
            "limit": 100
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if "data" not in data:
            return pd.DataFrame()
        
        campaigns = []
        for row in data["data"]:
            # Extrai leads das actions
            leads = 0
            if "actions" in row:
                for action in row["actions"]:
                    if action["action_type"] == "lead":
                        leads = int(action["value"])
                        break
            
            campaigns.append({
                "id": row.get("campaign_id", ""),
                "campanha": row.get("campaign_name", "Sem nome"),
                "custo": float(row.get("spend", 0)),
                "impressoes": int(row.get("impressions", 0)),
                "cliques": int(row.get("clicks", 0)),
                "leads": leads
            })
        
        df = pd.DataFrame(campaigns)
        
        if not df.empty:
            # Ordena por custo (ascending para gráficos de barras)
            df = df.sort_values('custo', ascending=True)
        
        return df
        
    except requests.exceptions.RequestException as e:
        st.error(f"Erro na requisição à API do Meta: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar campanhas: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_meta_ads_adsets(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Busca métricas por conjunto de anúncios do Meta Ads
    
    Returns:
        DataFrame com métricas por conjunto de anúncios
    """
    try:
        account_id = config.META_AD_ACCOUNT_ID
        
        url = f"{META_API_BASE_URL}/{account_id}/insights"
        
        params = {
            "access_token": config.META_ACCESS_TOKEN,
            "time_range": f'{{"since":"{start_date}","until":"{end_date}"}}',
            "fields": "adset_id,adset_name,spend,impressions,clicks,actions",
            "level": "adset",
            "limit": 100
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if "data" not in data:
            return pd.DataFrame()
        
        adsets = []
        for row in data["data"]:
            leads = 0
            if "actions" in row:
                for action in row["actions"]:
                    if action["action_type"] == "lead":
                        leads = int(action["value"])
                        break
            
            adsets.append({
                "id": row.get("adset_id", ""),
                "conjunto_anuncios": row.get("adset_name", "Sem nome"),
                "custo": float(row.get("spend", 0)),
                "impressoes": int(row.get("impressions", 0)),
                "cliques": int(row.get("clicks", 0)),
                "leads": leads
            })
        
        df = pd.DataFrame(adsets)
        
        if not df.empty:
            df = df.sort_values('custo', ascending=True)
        
        return df
        
    except requests.exceptions.RequestException as e:
        st.error(f"Erro na requisição à API do Meta: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar conjuntos de anúncios: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_meta_ads_daily_metrics(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Busca métricas diárias do Meta Ads
    
    Returns:
        DataFrame com métricas por dia
    """
    try:
        account_id = config.META_AD_ACCOUNT_ID
        
        url = f"{META_API_BASE_URL}/{account_id}/insights"
        
        params = {
            "access_token": config.META_ACCESS_TOKEN,
            "time_range": f'{{"since":"{start_date}","until":"{end_date}"}}',
            "fields": "spend,impressions,clicks,actions",
            "time_increment": 1,  # Diário
            "level": "account"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if "data" not in data:
            return pd.DataFrame()
        
        daily_data = []
        for row in data["data"]:
            leads = 0
            if "actions" in row:
                for action in row["actions"]:
                    if action["action_type"] == "lead":
                        leads = int(action["value"])
                        break
            
            daily_data.append({
                "data": row.get("date_start", ""),
                "custo": float(row.get("spend", 0)),
                "impressoes": int(row.get("impressions", 0)),
                "cliques": int(row.get("clicks", 0)),
                "leads": leads
            })
        
        df = pd.DataFrame(daily_data)
        
        if not df.empty:
            df['data'] = pd.to_datetime(df['data'])
            df = df.sort_values('data', ascending=True)
        
        return df
        
    except requests.exceptions.RequestException as e:
        st.error(f"Erro na requisição à API do Meta: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar métricas diárias: {str(e)}")
        return pd.DataFrame()


def get_empty_metrics() -> dict:
    """
    Retorna estrutura vazia de métricas
    """
    return {
        "cost": 0,
        "impressions": 0,
        "clicks": 0,
        "leads": 0,
        "ctr": 0,
        "cpc": 0,
        "cost_per_lead": 0
    }


# ===========================================
# FUNÇÕES ALTERNATIVAS COM DADOS DE EXEMPLO
# Use estas quando não tiver acesso à API
# ===========================================

def get_meta_ads_metrics_demo(start_date: str, end_date: str) -> dict:
    """
    Retorna métricas de exemplo para demonstração
    """
    return {
        "cost": 3250.45,
        "impressions": 125430,
        "clicks": 4523,
        "leads": 156,
        "ctr": 3.61,
        "cpc": 0.72,
        "cost_per_lead": 20.84
    }


def get_meta_ads_campaigns_demo() -> pd.DataFrame:
    """
    Retorna campanhas de exemplo para demonstração
    """
    data = [
        {"campanha": "Superendividamento", "custo": 1250.50, "impressoes": 45230, "cliques": 1823, "leads": 65},
        {"campanha": "FGTS - Revisão", "custo": 980.25, "impressoes": 38450, "cliques": 1445, "leads": 48},
        {"campanha": "Servidor Público", "custo": 620.70, "impressoes": 22920, "cliques": 812, "leads": 28},
        {"campanha": "Aposentadoria", "custo": 399.00, "impressoes": 18830, "cliques": 443, "leads": 15},
    ]
    df = pd.DataFrame(data)
    df = df.sort_values('custo', ascending=True)
    return df


def get_meta_ads_adsets_demo() -> pd.DataFrame:
    """
    Retorna conjuntos de anúncios de exemplo
    """
    data = [
        {"conjunto_anuncios": "CADASTRO | SERVIDORES | BRASIL", "custo": 850.30, "impressoes": 32150, "cliques": 1245, "leads": 42},
        {"conjunto_anuncios": "LOOKALIKE | 1%", "custo": 720.45, "impressoes": 28430, "cliques": 1023, "leads": 35},
        {"conjunto_anuncios": "INTERESSE | JURÍDICO", "custo": 480.20, "impressoes": 18920, "cliques": 712, "leads": 24},
        {"conjunto_anuncios": "RETARGETING | SITE", "custo": 350.00, "impressoes": 12430, "cliques": 543, "leads": 18},
    ]
    df = pd.DataFrame(data)
    df = df.sort_values('custo', ascending=True)
    return df
