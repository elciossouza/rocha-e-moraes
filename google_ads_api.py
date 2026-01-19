"""
Módulo de conexão com Google Ads API
Responsável por buscar métricas de campanhas do Google Ads
"""
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import config


def get_google_ads_client():
    """
    Cria e retorna um cliente autenticado do Google Ads
    """
    try:
        # Configuração do cliente
        credentials = {
            "developer_token": config.GOOGLE_ADS_DEVELOPER_TOKEN,
            "client_id": config.GOOGLE_ADS_CLIENT_ID,
            "client_secret": config.GOOGLE_ADS_CLIENT_SECRET,
            "refresh_token": config.GOOGLE_ADS_REFRESH_TOKEN,
            "use_proto_plus": True
        }
        
        client = GoogleAdsClient.load_from_dict(credentials)
        return client
        
    except Exception as e:
        st.error(f"Erro ao conectar com Google Ads: {str(e)}")
        return None


@st.cache_data(ttl=300)  # Cache de 5 minutos
def get_google_ads_metrics(start_date: str, end_date: str) -> dict:
    """
    Busca métricas agregadas do Google Ads para um período
    
    Args:
        start_date: Data inicial no formato 'YYYY-MM-DD'
        end_date: Data final no formato 'YYYY-MM-DD'
        
    Returns:
        Dicionário com métricas agregadas
    """
    try:
        client = get_google_ads_client()
        if client is None:
            return get_empty_metrics()
        
        ga_service = client.get_service("GoogleAdsService")
        customer_id = config.GOOGLE_ADS_CUSTOMER_ID.replace("-", "")
        
        # Query para buscar métricas agregadas
        query = f"""
            SELECT
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.cost_per_conversion
            FROM campaign
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
        """
        
        response = ga_service.search_stream(
            customer_id=customer_id,
            query=query
        )
        
        # Agrega métricas
        total_cost = 0
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0
        
        for batch in response:
            for row in batch.results:
                total_cost += row.metrics.cost_micros / 1_000_000
                total_impressions += row.metrics.impressions
                total_clicks += row.metrics.clicks
                total_conversions += row.metrics.conversions
        
        # Calcula métricas derivadas
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
        
        return {
            "cost": round(total_cost, 2),
            "impressions": total_impressions,
            "clicks": total_clicks,
            "conversions": int(total_conversions),
            "ctr": round(ctr, 2),
            "cpc": round(cpc, 2)
        }
        
    except GoogleAdsException as ex:
        st.error(f"Erro na API do Google Ads: {ex.failure.errors[0].message}")
        return get_empty_metrics()
    except Exception as e:
        st.error(f"Erro ao buscar métricas do Google Ads: {str(e)}")
        return get_empty_metrics()


@st.cache_data(ttl=300)
def get_google_ads_campaigns(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Busca métricas por campanha do Google Ads
    
    Returns:
        DataFrame com métricas por campanha
    """
    try:
        client = get_google_ads_client()
        if client is None:
            return pd.DataFrame()
        
        ga_service = client.get_service("GoogleAdsService")
        customer_id = config.GOOGLE_ADS_CUSTOMER_ID.replace("-", "")
        
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions
            FROM campaign
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
        """
        
        response = ga_service.search_stream(
            customer_id=customer_id,
            query=query
        )
        
        campaigns = []
        for batch in response:
            for row in batch.results:
                cost = row.metrics.cost_micros / 1_000_000
                campaigns.append({
                    "id": row.campaign.id,
                    "campanha": row.campaign.name,
                    "status": row.campaign.status.name,
                    "custo": round(cost, 2),
                    "impressoes": row.metrics.impressions,
                    "cliques": row.metrics.clicks,
                    "conversoes": int(row.metrics.conversions)
                })
        
        df = pd.DataFrame(campaigns)
        
        # Agrupa por campanha (caso tenha múltiplas linhas por dia)
        if not df.empty:
            df = df.groupby(['id', 'campanha', 'status']).agg({
                'custo': 'sum',
                'impressoes': 'sum',
                'cliques': 'sum',
                'conversoes': 'sum'
            }).reset_index()
            
            # Ordena por custo (ascending para gráficos de barras)
            df = df.sort_values('custo', ascending=True)
        
        return df
        
    except GoogleAdsException as ex:
        st.error(f"Erro na API do Google Ads: {ex.failure.errors[0].message}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar campanhas: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_google_ads_daily_metrics(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Busca métricas diárias do Google Ads
    
    Returns:
        DataFrame com métricas por dia
    """
    try:
        client = get_google_ads_client()
        if client is None:
            return pd.DataFrame()
        
        ga_service = client.get_service("GoogleAdsService")
        customer_id = config.GOOGLE_ADS_CUSTOMER_ID.replace("-", "")
        
        query = f"""
            SELECT
                segments.date,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions
            FROM campaign
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
        """
        
        response = ga_service.search_stream(
            customer_id=customer_id,
            query=query
        )
        
        daily_data = {}
        for batch in response:
            for row in batch.results:
                date = row.segments.date
                if date not in daily_data:
                    daily_data[date] = {
                        "data": date,
                        "custo": 0,
                        "impressoes": 0,
                        "cliques": 0,
                        "conversoes": 0
                    }
                
                daily_data[date]["custo"] += row.metrics.cost_micros / 1_000_000
                daily_data[date]["impressoes"] += row.metrics.impressions
                daily_data[date]["cliques"] += row.metrics.clicks
                daily_data[date]["conversoes"] += row.metrics.conversions
        
        df = pd.DataFrame(list(daily_data.values()))
        
        if not df.empty:
            df['data'] = pd.to_datetime(df['data'])
            df = df.sort_values('data', ascending=True)
            df['custo'] = df['custo'].round(2)
        
        return df
        
    except GoogleAdsException as ex:
        st.error(f"Erro na API do Google Ads: {ex.failure.errors[0].message}")
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
        "conversions": 0,
        "ctr": 0,
        "cpc": 0
    }


# ===========================================
# FUNÇÕES ALTERNATIVAS COM DADOS DE EXEMPLO
# Use estas quando não tiver acesso à API
# ===========================================

def get_google_ads_metrics_demo(start_date: str, end_date: str) -> dict:
    """
    Retorna métricas de exemplo para demonstração
    """
    return {
        "cost": 2450.75,
        "impressions": 45230,
        "clicks": 1523,
        "conversions": 89,
        "ctr": 3.37,
        "cpc": 1.61
    }


def get_google_ads_campaigns_demo() -> pd.DataFrame:
    """
    Retorna campanhas de exemplo para demonstração
    """
    data = [
        {"campanha": "Advogado Trabalhista", "custo": 850.50, "impressoes": 15230, "cliques": 523, "conversoes": 32},
        {"campanha": "Direito Previdenciário", "custo": 720.25, "impressoes": 12450, "cliques": 445, "conversoes": 28},
        {"campanha": "Revisão FGTS", "custo": 480.00, "impressoes": 8920, "cliques": 312, "conversoes": 18},
        {"campanha": "Ação Trabalhista", "custo": 400.00, "impressoes": 8630, "cliques": 243, "conversoes": 11},
    ]
    df = pd.DataFrame(data)
    df = df.sort_values('custo', ascending=True)
    return df
