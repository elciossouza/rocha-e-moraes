"""
Dashboard de Análise de Ads - Meta Ads e Google Ads
Aplicação principal Streamlit
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional

# Importa módulos locais
import config
import google_sheets as gs
import google_ads_api as gads
import meta_ads_api as meta

# ===========================================
# CONFIGURAÇÃO DA PÁGINA
# ===========================================
st.set_page_config(
    page_title=config.DASHBOARD_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===========================================
# ESTILOS CSS CUSTOMIZADOS
# ===========================================
st.markdown("""
<style>
    /* Reset e fonte base */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    .main {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Cards de métricas */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        border: 1px solid #e9ecef;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0;
        line-height: 1.2;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 8px;
        font-weight: 500;
    }
    
    /* Cabeçalho da plataforma */
    .platform-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 2px solid #e9ecef;
    }
    
    .platform-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .meta-color { color: #0668E1; }
    .google-color { color: #4285F4; }
    
    /* Estilo das abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8f9fa;
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        padding: 32px;
        border-radius: 20px;
        margin-bottom: 32px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 8px 0 0 0;
        opacity: 0.8;
        font-size: 1rem;
    }
    
    /* Tabelas */
    .dataframe {
        border-radius: 12px !important;
        overflow: hidden;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    /* Esconde elementos padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Cards coloridos para CPL */
    .cpl-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
    }
    
    .cpl-value {
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .cpl-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)


# ===========================================
# FUNÇÕES AUXILIARES
# ===========================================

def format_currency(value: float, currency: str = "R$") -> str:
    """Formata valor como moeda"""
    return f"{currency} {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_number(value: int) -> str:
    """Formata número com separador de milhar"""
    return f"{value:,}".replace(",", ".")


def format_percentage(value: float) -> str:
    """Formata percentual"""
    return f"{value:.2f}%"


def calculate_cpl(cost: float, leads: int) -> float:
    """Calcula Custo por Lead"""
    if leads == 0:
        return 0
    return round(cost / leads, 2)


def create_metric_card(label: str, value: str, icon: str = "") -> str:
    """Cria HTML de card de métrica"""
    return f"""
    <div class="metric-card">
        <p class="metric-value">{icon} {value}</p>
        <p class="metric-label">{label}</p>
    </div>
    """


def create_bar_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str) -> go.Figure:
    """Cria gráfico de barras horizontal padronizado"""
    fig = px.bar(
        df.sort_values(y, ascending=True),  # Ascending para melhor visualização
        x=y,
        y=x,
        orientation='h',
        title=title,
        color_discrete_sequence=[color]
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans", size=12),
        title=dict(font=dict(size=16, color='#1a1a2e')),
        xaxis=dict(showgrid=True, gridcolor='#e9ecef'),
        yaxis=dict(showgrid=False),
        margin=dict(l=20, r=20, t=50, b=20),
        height=350
    )
    
    return fig


def create_line_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str) -> go.Figure:
    """Cria gráfico de linha padronizado"""
    fig = px.line(
        df,
        x=x,
        y=y,
        title=title,
        color_discrete_sequence=[color],
        markers=True
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans", size=12),
        title=dict(font=dict(size=16, color='#1a1a2e')),
        xaxis=dict(showgrid=True, gridcolor='#e9ecef'),
        yaxis=dict(showgrid=True, gridcolor='#e9ecef'),
        margin=dict(l=20, r=20, t=50, b=20),
        height=350
    )
    
    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=8)
    )
    
    return fig


# ===========================================
# SIDEBAR - FILTROS
# ===========================================

with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="margin: 0; color: #1a1a2e;">📊 {config.COMPANY_NAME}</h2>
        <p style="color: #6c757d; font-size: 0.9rem;">Dashboard de Ads</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Seletor de período
    st.markdown("### 📅 Período")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Data Inicial",
            value=datetime.now() - timedelta(days=30),
            format="DD/MM/YYYY"
        )
    with col2:
        end_date = st.date_input(
            "Data Final",
            value=datetime.now(),
            format="DD/MM/YYYY"
        )
    
    # Atalhos de período
    st.markdown("**Atalhos:**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Últimos 7 dias", use_container_width=True):
            start_date = datetime.now().date() - timedelta(days=7)
            end_date = datetime.now().date()
    with col2:
        if st.button("Últimos 30 dias", use_container_width=True):
            start_date = datetime.now().date() - timedelta(days=30)
            end_date = datetime.now().date()
    
    st.markdown("---")
    
    # Modo Demo
    st.markdown("### ⚙️ Configurações")
    demo_mode = st.toggle("Modo Demonstração", value=True, help="Usa dados de exemplo quando ativado")
    
    st.markdown("---")
    
    # Informações
    st.markdown("""
    <div style="padding: 16px; background: #f8f9fa; border-radius: 12px; font-size: 0.85rem;">
        <p style="margin: 0; color: #6c757d;">
            <strong>💡 Dica:</strong> Ative o modo demonstração para visualizar o dashboard com dados de exemplo.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ===========================================
# CONTEÚDO PRINCIPAL
# ===========================================

# Header
st.markdown(f"""
<div class="main-header">
    <h1>📊 Dashboard de Performance de Anúncios</h1>
    <p>Análise de campanhas Meta Ads e Google Ads • {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}</p>
</div>
""", unsafe_allow_html=True)

# Converte datas para string
start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')


# ===========================================
# BUSCA DADOS
# ===========================================

# Dados da planilha de leads
@st.cache_data(ttl=300)
def load_leads_data():
    """Carrega dados de leads da planilha"""
    if demo_mode:
        # Dados de demonstração
        return create_demo_leads_data()
    else:
        df = gs.get_all_leads()
        df = gs.process_leads_dataframe(df)
        return df


def create_demo_leads_data():
    """Cria DataFrame de demonstração com leads"""
    import random
    from datetime import datetime, timedelta
    
    campanhas_meta = ["Superendividamento", "FGTS - Revisão", "Servidor Público"]
    conjuntos = ["CADASTRO | SERVIDORES | BRASIL", "LOOKALIKE | 1%", "INTERESSE | JURÍDICO"]
    
    campanhas_google = ["Advogado Trabalhista", "Direito Previdenciário", "Revisão FGTS"]
    
    leads = []
    base_date = datetime.now() - timedelta(days=30)
    
    # Leads Meta Ads
    for i in range(156):
        data = base_date + timedelta(days=random.randint(0, 30), hours=random.randint(8, 20))
        leads.append({
            "DATA / HORA": data.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "ORIGEM": "Busca paga | Facebook Ads",
            "CAMPANHA": random.choice(campanhas_meta),
            "CONJUNTO DE ANÚNCIOS": random.choice(conjuntos),
            "CRIATIVO": "Servidor, médico",
            "NOME": f"Lead {i+1}",
            "E-MAIL": f"lead{i+1}@email.com",
            "TELEFONE": f"5511999{random.randint(100000, 999999)}",
            "ID DO FACEBOOK": str(random.randint(10000000000, 99999999999))
        })
    
    # Leads Google Ads
    for i in range(89):
        data = base_date + timedelta(days=random.randint(0, 30), hours=random.randint(8, 20))
        leads.append({
            "DATA / HORA": data.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "ORIGEM": "Busca paga | Google Ads",
            "CAMPANHA": random.choice(campanhas_google),
            "CONJUNTO DE ANÚNCIOS": "",
            "CRIATIVO": "",
            "NOME": f"Lead Google {i+1}",
            "E-MAIL": f"leadgoogle{i+1}@email.com",
            "TELEFONE": f"5511998{random.randint(100000, 999999)}",
            "ID DO FACEBOOK": ""
        })
    
    df = pd.DataFrame(leads)
    df = gs.process_leads_dataframe(df)
    return df


# Carrega dados
leads_df = load_leads_data()

# Filtra por data se possível
if not leads_df.empty and 'data' in leads_df.columns:
    leads_df = gs.filter_leads_by_date(leads_df, start_date, end_date)

# Separa leads por plataforma
if not leads_df.empty and 'plataforma' in leads_df.columns:
    meta_leads_df = leads_df[leads_df['plataforma'] == 'Meta Ads']
    google_leads_df = leads_df[leads_df['plataforma'] == 'Google Ads']
else:
    meta_leads_df = pd.DataFrame()
    google_leads_df = pd.DataFrame()


# Busca métricas das APIs
if demo_mode:
    meta_metrics = meta.get_meta_ads_metrics_demo(start_date_str, end_date_str)
    google_metrics = gads.get_google_ads_metrics_demo(start_date_str, end_date_str)
    meta_campaigns = meta.get_meta_ads_campaigns_demo()
    google_campaigns = gads.get_google_ads_campaigns_demo()
    meta_adsets = meta.get_meta_ads_adsets_demo()
else:
    meta_metrics = meta.get_meta_ads_metrics(start_date_str, end_date_str)
    google_metrics = gads.get_google_ads_metrics(start_date_str, end_date_str)
    meta_campaigns = meta.get_meta_ads_campaigns(start_date_str, end_date_str)
    google_campaigns = gads.get_google_ads_campaigns(start_date_str, end_date_str)
    meta_adsets = meta.get_meta_ads_adsets(start_date_str, end_date_str)


# ===========================================
# VISÃO GERAL
# ===========================================

st.markdown("## 📈 Visão Geral")

# Totais consolidados
total_cost = meta_metrics['cost'] + google_metrics['cost']
total_leads_meta = len(meta_leads_df) if not meta_leads_df.empty else meta_metrics.get('leads', 0)
total_leads_google = len(google_leads_df) if not google_leads_df.empty else google_metrics.get('conversions', 0)
total_leads = total_leads_meta + total_leads_google
total_cpl = calculate_cpl(total_cost, total_leads)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(create_metric_card(
        "Investimento Total",
        format_currency(total_cost),
        "💰"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(create_metric_card(
        "Total de Leads",
        format_number(total_leads),
        "👥"
    ), unsafe_allow_html=True)

with col3:
    st.markdown(create_metric_card(
        "Custo por Lead (CPL)",
        format_currency(total_cpl),
        "📊"
    ), unsafe_allow_html=True)

with col4:
    st.markdown(create_metric_card(
        "Taxa de Conversão",
        format_percentage((total_leads / (meta_metrics['clicks'] + google_metrics['clicks']) * 100) if (meta_metrics['clicks'] + google_metrics['clicks']) > 0 else 0),
        "🎯"
    ), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ===========================================
# ABAS: META ADS E GOOGLE ADS
# ===========================================

tab_meta, tab_google, tab_leads = st.tabs(["🔵 Meta Ads", "🔴 Google Ads", "📋 Tabela de Leads"])


# ===========================================
# ABA META ADS
# ===========================================
with tab_meta:
    st.markdown("""
    <div class="platform-header">
        <h2 class="platform-title meta-color">📘 Meta Ads (Facebook/Instagram)</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas Meta Ads
    meta_leads_count = len(meta_leads_df) if not meta_leads_df.empty else meta_metrics.get('leads', 0)
    meta_cpl = calculate_cpl(meta_metrics['cost'], meta_leads_count)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(create_metric_card(
            "Valor Gasto",
            format_currency(meta_metrics['cost']),
            "💵"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card(
            "Leads Gerados",
            format_number(meta_leads_count),
            "👥"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(create_metric_card(
            "Custo por Lead",
            format_currency(meta_cpl),
            "💰"
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(create_metric_card(
            "Cliques",
            format_number(meta_metrics['clicks']),
            "👆"
        ), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gráficos Meta Ads
    col1, col2 = st.columns(2)
    
    with col1:
        if not meta_campaigns.empty:
            fig = create_bar_chart(
                meta_campaigns,
                'campanha',
                'custo',
                '💰 Investimento por Campanha',
                config.COLORS['meta']
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de campanhas disponíveis")
    
    with col2:
        if not meta_campaigns.empty:
            fig = create_bar_chart(
                meta_campaigns,
                'campanha',
                'leads',
                '👥 Leads por Campanha',
                config.COLORS['success']
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de leads por campanha")
    
    # Tabela de Conjuntos de Anúncios
    st.markdown("### 📋 Performance por Conjunto de Anúncios")
    
    if not meta_adsets.empty:
        # Calcula CPL por adset
        meta_adsets_display = meta_adsets.copy()
        meta_adsets_display['cpl'] = meta_adsets_display.apply(
            lambda row: calculate_cpl(row['custo'], row['leads']), axis=1
        )
        
        # Formata para exibição
        meta_adsets_display = meta_adsets_display[['conjunto_anuncios', 'custo', 'impressoes', 'cliques', 'leads', 'cpl']]
        meta_adsets_display.columns = ['Conjunto de Anúncios', 'Custo (R$)', 'Impressões', 'Cliques', 'Leads', 'CPL (R$)']
        
        st.dataframe(
            meta_adsets_display.sort_values('Custo (R$)', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Sem dados de conjuntos de anúncios disponíveis")


# ===========================================
# ABA GOOGLE ADS
# ===========================================
with tab_google:
    st.markdown("""
    <div class="platform-header">
        <h2 class="platform-title google-color">🔍 Google Ads</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas Google Ads
    google_leads_count = len(google_leads_df) if not google_leads_df.empty else google_metrics.get('conversions', 0)
    google_cpl = calculate_cpl(google_metrics['cost'], google_leads_count)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(create_metric_card(
            "Valor Gasto",
            format_currency(google_metrics['cost']),
            "💵"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card(
            "Leads Gerados",
            format_number(google_leads_count),
            "👥"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(create_metric_card(
            "Custo por Lead",
            format_currency(google_cpl),
            "💰"
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(create_metric_card(
            "Cliques",
            format_number(google_metrics['clicks']),
            "👆"
        ), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gráficos Google Ads
    col1, col2 = st.columns(2)
    
    with col1:
        if not google_campaigns.empty:
            fig = create_bar_chart(
                google_campaigns,
                'campanha',
                'custo',
                '💰 Investimento por Campanha',
                config.COLORS['google']
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de campanhas disponíveis")
    
    with col2:
        if not google_campaigns.empty:
            fig = create_bar_chart(
                google_campaigns,
                'campanha',
                'conversoes',
                '👥 Conversões por Campanha',
                config.COLORS['success']
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de conversões por campanha")
    
    # Tabela de Campanhas
    st.markdown("### 📋 Performance por Campanha")
    
    if not google_campaigns.empty:
        google_campaigns_display = google_campaigns.copy()
        google_campaigns_display['cpl'] = google_campaigns_display.apply(
            lambda row: calculate_cpl(row['custo'], row['conversoes']), axis=1
        )
        
        google_campaigns_display = google_campaigns_display[['campanha', 'custo', 'impressoes', 'cliques', 'conversoes', 'cpl']]
        google_campaigns_display.columns = ['Campanha', 'Custo (R$)', 'Impressões', 'Cliques', 'Conversões', 'CPL (R$)']
        
        st.dataframe(
            google_campaigns_display.sort_values('Custo (R$)', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Sem dados de campanhas disponíveis")


# ===========================================
# ABA TABELA DE LEADS
# ===========================================
with tab_leads:
    st.markdown("""
    <div class="platform-header">
        <h2 class="platform-title">📋 Tabela Completa de Leads</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtro de plataforma
    platform_filter = st.selectbox(
        "Filtrar por plataforma:",
        ["Todos", "Meta Ads", "Google Ads"]
    )
    
    if not leads_df.empty:
        display_df = leads_df.copy()
        
        if platform_filter != "Todos" and 'plataforma' in display_df.columns:
            display_df = display_df[display_df['plataforma'] == platform_filter]
        
        # Seleciona colunas relevantes para exibição
        columns_to_show = []
        possible_columns = [
            ('DATA / HORA', 'Data/Hora'),
            ('data_hora', 'Data/Hora'),
            ('ORIGEM', 'Origem'),
            ('origem', 'Origem'),
            ('CAMPANHA', 'Campanha'),
            ('campanha', 'Campanha'),
            ('CONJUNTO DE ANÚNCIOS', 'Conjunto de Anúncios'),
            ('conjunto_anuncios', 'Conjunto de Anúncios'),
            ('NOME', 'Nome'),
            ('nome', 'Nome'),
            ('TELEFONE', 'Telefone'),
            ('telefone', 'Telefone'),
            ('plataforma', 'Plataforma')
        ]
        
        for col, display_name in possible_columns:
            if col in display_df.columns and col not in [c[0] for c in columns_to_show]:
                columns_to_show.append((col, display_name))
        
        if columns_to_show:
            cols_to_display = [c[0] for c in columns_to_show]
            display_df = display_df[cols_to_display]
            display_df.columns = [c[1] for c in columns_to_show]
        
        st.markdown(f"**Total de leads exibidos:** {len(display_df)}")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=500
        )
        
        # Botão de download
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar CSV",
            data=csv,
            file_name=f"leads_{start_date_str}_{end_date_str}.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhum lead encontrado para o período selecionado.")


# ===========================================
# RODAPÉ
# ===========================================
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #6c757d; padding: 20px;">
    <p>Dashboard desenvolvido para {config.COMPANY_NAME}</p>
    <p style="font-size: 0.8rem;">Dados atualizados em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
</div>
""", unsafe_allow_html=True)
