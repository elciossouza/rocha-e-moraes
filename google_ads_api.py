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


def get_google_ads_credentials():
    """
    Obtém as credenciais do Google Ads dos secrets ou config
    """
    credentials = {
        'developer_token': '',
        'client_id': '',
        'client_secret': '',
        'refresh_token': '',
        'customer_id': ''
    }
    
    # Primeiro tenta ler dos secrets do Streamlit
    try:
        if hasattr(st, 'secrets') and st.secrets is not None:
            # Developer Token
            if "GOOGLE_ADS_DEVELOPER_TOKEN" in st.secrets:
                credentials['developer_token'] = str(st.secrets["GOOGLE_ADS_DEVELOPER_TOKEN"]).strip()
            
            # Client ID
            if "GOOGLE_ADS_CLIENT_ID" in st.secrets:
                credentials['client_id'] = str(st.secrets["GOOGLE_ADS_CLIENT_ID"]).strip()
            
            # Client Secret
            if "GOOGLE_ADS_CLIENT_SECRET" in st.secrets:
                credentials['client_secret'] = str(st.secrets["GOOGLE_ADS_CLIENT_SECRET"]).strip()
            
            # Refresh Token
            if "GOOGLE_ADS_REFRESH_TOKEN" in st.secrets:
                credentials['refresh_token'] = str(st.secrets["GOOGLE_ADS_REFRESH_TOKEN"]).strip()
            
            # Customer ID
            if "GOOGLE_ADS_CUSTOMER_ID" in st.secrets:
                credentials['customer_id'] = str(st.secrets["GOOGLE_ADS_CUSTOMER_ID"]).strip().replace("-", "")
    except Exception as e:
        pass
    
    # Fallback para config.py
    if not credentials['developer_token']:
        credentials['developer_token'] = getattr(config, 'GOOGLE_ADS_DEVELOPER_TOKEN', '')
    if not credentials['client_id']:
        credentials['client_id'] = getattr(config, 'GOOGLE_ADS_CLIENT_ID', '')
    if not credentials['client_secret']:
        credentials['client_secret'] = getattr(config, 'GOOGLE_ADS_CLIENT_SECRET', '')
    if not credentials['refresh_token']:
        credentials['refresh_token'] = getattr(config, 'GOOGLE_ADS_REFRESH_TOKEN', '')
    if not credentials['customer_id']:
        customer_id = getattr(config, 'GOOGLE_ADS_CUSTOMER_ID', '')
        credentials['customer_id'] = str(customer_id).replace("-", "") if customer_id else ''
    
    return credentials


def is_google_ads_configured():
    """
    Verifica se as credenciais do Google Ads estão configuradas
    """
    creds = get_google_ads_credentials()
    return bool(
        creds['developer_token'] and
        creds['client_id'] and
        creds['client_secret'] and
        creds['refresh_token'] and
        creds['customer_id']
    )


def debug_google_ads_connection():
    """
    Retorna informações de debug da conexão Google Ads
    """
    creds = get_google_ads_credentials()
    
    info = {
        "developer_token": "✅ Configurado" if creds['developer_token'] else "❌ Não configurado",
        "developer_token_inicio": creds['developer_token'][:10] + "..." if creds['developer_token'] and len(creds['developer_token']) > 10 else "N/A",
        "client_id": "✅ Configurado" if creds['client_id'] else "❌ Não configurado",
        "client_secret": "✅ Configurado" if creds['client_secret'] else "❌ Não configurado",
        "refresh_token": "✅ Configurado" if creds['refresh_token'] else "❌ Não configurado",
        "customer_id": creds['customer_id'] if creds['customer_id'] else "N/A",
        "secrets_disponivel": hasattr(st, 'secrets'),
    }
    
    # Verifica se secrets estão acessíveis
    try:
        if hasattr(st, 'secrets') and st.secrets is not None:
            info["gads_in_secrets"] = "GOOGLE_ADS_DEVELOPER_TOKEN" in st.secrets
    except Exception as e:
        info["secrets_error"] = str(e)
    
    # Testa a conexão
    if is_google_ads_configured():
        info["teste_conexao"] = test_google_ads_connection()
    else:
        info["teste_conexao"] = "Credenciais não configuradas"
    
    return info


def test_google_ads_connection():
    """
    Testa a conexão com a API do Google Ads
    """
    try:
        client = get_google_ads_client()
        if client is None:
            return "Erro ao criar cliente"
        
        creds = get_google_ads_credentials()
        customer_id = creds['customer_id']
        
        ga_service = client.get_service("GoogleAdsService")
        
        # Query simples para testar conexão
        query = "SELECT customer.id, customer.descriptive_name FROM customer LIMIT 1"
        
        response = ga_service.search_stream(
            customer_id=customer_id,
            query=query
        )
        
        for batch in response:
            for row in batch.results:
                return f"✅ Conectado - Conta: {row.customer.descriptive_name}"
        
        return "✅ Conectado"
        
    except GoogleAdsException as ex:
        error_msg = ex.failure.errors[0].message if ex.failure.errors else "Erro desconhecido"
        return f"❌ Erro: {error_msg}"
    except Exception as e:
        return f"❌ Erro: {str(e)}"


def get_google_ads_client():
    """
    Cria e retorna um cliente autenticado do Google Ads
    """
    try:
        creds = get_google_ads_credentials()
        
        if not all([creds['developer_token'], creds['client_id'], creds['client_secret'], creds['refresh_token']]):
            return None
        
        # Configuração do cliente
        credentials = {
            "developer_token": creds['developer_token'],
            "client_id": creds['client_id'],
            "client_secret": creds['client_secret'],
            "refresh_token": creds['refresh_token'],
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
        
        creds = get_google_ads_credentials()
        customer_id = creds['customer_id']
        
        ga_service = client.get_service("GoogleAdsService")
        
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
        error_msg = ex.failure.errors[0].message if ex.failure.errors else "Erro desconhecido"
        st.error(f"Erro na API do Google Ads: {error_msg}")
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
        
        creds = get_google_ads_credentials()
        customer_id = creds['customer_id']
        
        ga_service = client.get_service("GoogleAdsService")
        
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
        error_msg = ex.failure.errors[0].message if ex.failure.errors else "Erro desconhecido"
        st.error(f"Erro na API do Google Ads: {error_msg}")
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
        
        creds = get_google_ads_credentials()
        customer_id = creds['customer_id']
        
        ga_service = client.get_service("GoogleAdsService")
        
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
        error_msg = ex.failure.errors[0].message if ex.failure.errors else "Erro desconhecido"
        st.error(f"Erro na API do Google Ads: {error_msg}")
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
