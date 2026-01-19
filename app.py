"""
Dashboard de Análise de Ads - Meta Ads e Google Ads
Com Funil de Conversão, ROAS e Dados das APIs
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Importa módulos locais
import config
import google_sheets as gs
import meta_ads_api as meta
import google_ads_api as gads

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
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    .main { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        border: 1px solid #e9ecef;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        text-transform: uppercase;
        margin-top: 8px;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        padding: 32px;
        border-radius: 20px;
        margin-bottom: 32px;
    }
    
    .main-header h1 { margin: 0; font-size: 2rem; }
    .main-header p { margin: 8px 0 0 0; opacity: 0.8; }
    
    .funnel-card {
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        color: white;
    }
    
    .funnel-value { font-size: 2.5rem; font-weight: 700; }
    .funnel-label { font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; }
    .funnel-percent { font-size: 1rem; opacity: 0.8; margin-top: 8px; }
    
    .roas-card {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        border-radius: 20px;
        padding: 32px;
        text-align: center;
        color: white;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3);
    }
    
    .roas-value {
        font-size: 3.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .roas-label {
        font-size: 1rem;
        opacity: 0.9;
        text-transform: uppercase;
        margin-top: 8px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ===========================================
# FUNÇÕES AUXILIARES
# ===========================================

def format_number(value):
    return f"{value:,}".replace(",", ".")

def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_percentage(value):
    return f"{value:.1f}%"

def format_roas(value):
    return f"{value:.2f}x"

def create_metric_card(label, value, icon=""):
    return f"""
    <div class="metric-card">
        <p class="metric-value">{icon} {value}</p>
        <p class="metric-label">{label}</p>
    </div>
    """

def create_colored_metric_card(label, value, icon, bg_color):
    return f"""
    <div style="background: {bg_color}; color: white; border-radius: 16px; padding: 24px;">
        <p style="font-size: 2rem; font-weight: 700; margin: 0;">{icon} {value}</p>
        <p style="font-size: 0.85rem; opacity: 0.9; text-transform: uppercase; margin-top: 8px;">{label}</p>
    </div>
    """

def create_roas_card(roas_value, receita, investimento):
    color = "#10B981" if roas_value >= 1 else "#EF4444"
    return f"""
    <div class="roas-card" style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%);">
        <p class="roas-value">{format_roas(roas_value)}</p>
        <p class="roas-label">ROAS (Return on Ad Spend)</p>
        <p style="font-size: 0.9rem; opacity: 0.8; margin-top: 16px;">
            Receita: {format_currency(receita)} / Investimento: {format_currency(investimento)}
        </p>
    </div>
    """

def create_funnel_card(label, value, percent, color):
    return f"""
    <div class="funnel-card" style="background: {color};">
        <p class="funnel-value">{format_number(value)}</p>
        <p class="funnel-label">{label}</p>
        <p class="funnel-percent">{format_percentage(percent)} do total</p>
    </div>
    """

def create_funnel_chart(funnel_data):
    stages = ['Total de Leads', 'Qualificados', 'Convertidos']
    values = [funnel_data['total_leads'], funnel_data['qualificados'], funnel_data['convertidos']]
    colors = ['#3B82F6', '#8B5CF6', '#10B981']
    
    fig = go.Figure(go.Funnel(
        y=stages, x=values,
        textposition="inside", textinfo="value+percent initial",
        marker=dict(color=colors),
        connector=dict(line=dict(color="#e9ecef", width=2))
    ))
    
    fig.update_layout(
        font=dict(family="Plus Jakarta Sans", size=14),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20), height=300
    )
    return fig

def create_bar_chart(df, x, y, title, color):
    if df.empty:
        return go.Figure()
    
    fig = px.bar(df.sort_values(y, ascending=True), x=y, y=x, orientation='h', title=title, color_discrete_sequence=[color])
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans", size=12),
        margin=dict(l=20, r=20, t=50, b=20), height=400
    )
    return fig

def create_line_chart(df, x, y, title, color):
    if df.empty:
        return go.Figure()
    
    fig = px.line(df, x=x, y=y, title=title, color_discrete_sequence=[color], markers=True)
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans", size=12),
        margin=dict(l=20, r=20, t=50, b=20), height=350
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    return fig


def create_roas_monthly_chart(receita_df, investimento_por_mes):
    """
    Cria gráfico comparativo de Receita vs Investimento por mês
    """
    if receita_df.empty:
        return go.Figure()
    
    df = receita_df.copy()
    df['investimento'] = df['mes_ano'].map(investimento_por_mes).fillna(0)
    df['roas'] = df.apply(lambda row: row['receita'] / row['investimento'] if row['investimento'] > 0 else 0, axis=1)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Investimento',
        x=df['mes_ano_label'],
        y=df['investimento'],
        marker_color='#EF4444',
        text=df['investimento'].apply(lambda x: f'R$ {x:,.0f}'.replace(',', '.')),
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Receita',
        x=df['mes_ano_label'],
        y=df['receita'],
        marker_color='#10B981',
        text=df['receita'].apply(lambda x: f'R$ {x:,.0f}'.replace(',', '.')),
        textposition='outside'
    ))
    
    fig.update_layout(
        title='📊 Investimento vs Receita por Mês',
        barmode='group',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans", size=12),
        margin=dict(l=20, r=20, t=60, b=20),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(tickformat=',.0f', tickprefix='R$ ')
    )
    
    return fig


def create_roas_line_chart(receita_df, investimento_por_mes):
    """
    Cria gráfico de linha do ROAS por mês
    """
    if receita_df.empty:
        return go.Figure()
    
    df = receita_df.copy()
    df['investimento'] = df['mes_ano'].map(investimento_por_mes).fillna(0)
    df['roas'] = df.apply(lambda row: row['receita'] / row['investimento'] if row['investimento'] > 0 else 0, axis=1)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['mes_ano_label'],
        y=df['roas'],
        mode='lines+markers+text',
        name='ROAS',
        line=dict(color='#8B5CF6', width=3),
        marker=dict(size=12, color='#8B5CF6'),
        text=df['roas'].apply(lambda x: f'{x:.2f}x'),
        textposition='top center'
    ))
    
    fig.add_hline(y=1, line_dash="dash", line_color="#6c757d", 
                  annotation_text="Break-even (1.0x)", annotation_position="right")
    
    fig.update_layout(
        title='📈 ROAS Mensal',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans", size=12),
        margin=dict(l=20, r=20, t=60, b=20),
        height=350,
        yaxis=dict(ticksuffix='x')
    )
    
    return fig


# ===========================================
# FUNÇÕES PARA VERIFICAR CONEXÕES
# ===========================================

def is_google_ads_configured():
    """Verifica se o Google Ads está configurado"""
    try:
        return bool(
            hasattr(config, 'GOOGLE_ADS_DEVELOPER_TOKEN') and config.GOOGLE_ADS_DEVELOPER_TOKEN and
            hasattr(config, 'GOOGLE_ADS_CLIENT_ID') and config.GOOGLE_ADS_CLIENT_ID and
            hasattr(config, 'GOOGLE_ADS_CLIENT_SECRET') and config.GOOGLE_ADS_CLIENT_SECRET and
            hasattr(config, 'GOOGLE_ADS_REFRESH_TOKEN') and config.GOOGLE_ADS_REFRESH_TOKEN and
            hasattr(config, 'GOOGLE_ADS_CUSTOMER_ID') and config.GOOGLE_ADS_CUSTOMER_ID
        )
    except:
        return False


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
    
    st.markdown("### 📅 Período")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Data Inicial", value=datetime.now() - timedelta(days=30), format="DD/MM/YYYY")
    with col2:
        end_date = st.date_input("Data Final", value=datetime.now(), format="DD/MM/YYYY")
    
    st.markdown("**Atalhos:**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Últimos 7 dias", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("Últimos 30 dias", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Status das conexões
    st.markdown("### 🔗 Conexões")
    
    meta_ok = meta.is_meta_configured()
    google_ok = is_google_ads_configured()
    
    if meta_ok:
        st.success("✅ Meta Ads conectado")
    else:
        st.warning("⚠️ Meta Ads não configurado")
    
    if google_ok:
        st.success("✅ Google Ads conectado")
    else:
        st.warning("⚠️ Google Ads não configurado")
    
    # DEBUG - Meta Ads
    with st.expander("🔧 Debug Meta Ads"):
        debug_info = meta.debug_meta_connection()
        for key, value in debug_info.items():
            st.write(f"**{key}:** {value}")
    
    # DEBUG - Google Ads
    with st.expander("🔧 Debug Google Ads"):
        st.write(f"**developer_token:** {'✅' if hasattr(config, 'GOOGLE_ADS_DEVELOPER_TOKEN') and config.GOOGLE_ADS_DEVELOPER_TOKEN else '❌'}")
        st.write(f"**client_id:** {'✅' if hasattr(config, 'GOOGLE_ADS_CLIENT_ID') and config.GOOGLE_ADS_CLIENT_ID else '❌'}")
        st.write(f"**client_secret:** {'✅' if hasattr(config, 'GOOGLE_ADS_CLIENT_SECRET') and config.GOOGLE_ADS_CLIENT_SECRET else '❌'}")
        st.write(f"**refresh_token:** {'✅' if hasattr(config, 'GOOGLE_ADS_REFRESH_TOKEN') and config.GOOGLE_ADS_REFRESH_TOKEN else '❌'}")
        st.write(f"**customer_id:** {getattr(config, 'GOOGLE_ADS_CUSTOMER_ID', 'N/A')}")
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Configurações")
    demo_mode = st.toggle("Modo Demonstração", value=False)


# ===========================================
# CONTEÚDO PRINCIPAL
# ===========================================

st.markdown(f"""
<div class="main-header">
    <h1>📊 Dashboard de Performance de Anúncios</h1>
    <p>Análise de campanhas Meta Ads e Google Ads • {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}</p>
</div>
""", unsafe_allow_html=True)


# ===========================================
# CARREGAR DADOS
# ===========================================

def load_data_demo():
    return {
        'total_leads': 245, 'qualificados': 89, 'desqualificados': 56, 'convertidos': 23,
        'leads_df': pd.DataFrame(), 'qualificados_df': pd.DataFrame(),
        'desqualificados_df': pd.DataFrame(), 'convertidos_df': pd.DataFrame()
    }

start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

if demo_mode:
    funnel_data = load_data_demo()
    leads_df = pd.DataFrame()
    meta_summary = {'valor_gasto': 5000, 'leads': 120, 'cpl': 41.67, 'cliques': 2500, 'impressoes': 85000, 'alcance': 45000, 'ctr': 2.94, 'cpc': 2.0}
    meta_campaigns = pd.DataFrame()
    google_summary = {'cost': 3500, 'clicks': 1800, 'impressions': 55000, 'conversions': 85, 'ctr': 3.27, 'cpc': 1.94}
    google_campaigns = pd.DataFrame()
    receita_data = {'receita_total': 45000, 'quantidade_contratos': 23, 'ticket_medio': 1956.52, 'receita_por_mes': pd.DataFrame()}
else:
    try:
        funnel_data = gs.get_funnel_data(start_date, end_date)
        leads_df = funnel_data['leads_df']
        receita_data = gs.get_receita_por_periodo(start_date, end_date)
        
        # Meta Ads
        if meta.is_meta_configured():
            meta_summary = meta.get_meta_summary(start_date, end_date)
            meta_campaigns = meta.get_meta_campaigns(start_date, end_date)
        else:
            meta_summary = None
            meta_campaigns = pd.DataFrame()
        
        # Google Ads
        if is_google_ads_configured():
            google_summary = gads.get_google_ads_metrics(start_date_str, end_date_str)
            google_campaigns = gads.get_google_ads_campaigns(start_date_str, end_date_str)
        else:
            google_summary = None
            google_campaigns = pd.DataFrame()
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        funnel_data = load_data_demo()
        leads_df = pd.DataFrame()
        meta_summary = None
        meta_campaigns = pd.DataFrame()
        google_summary = None
        google_campaigns = pd.DataFrame()
        receita_data = {'receita_total': 0, 'quantidade_contratos': 0, 'ticket_medio': 0, 'receita_por_mes': pd.DataFrame()}


# ===========================================
# SEÇÃO DE ROAS
# ===========================================

st.markdown("## 💰 Retorno sobre Investimento (ROAS)")

receita_total = receita_data.get('receita_total', 0)
quantidade_contratos = receita_data.get('quantidade_contratos', 0)
ticket_medio = receita_data.get('ticket_medio', 0)

# Investimentos
investimento_meta = meta_summary.get('valor_gasto', 0) if meta_summary else 0
investimento_google = google_summary.get('cost', 0) if google_summary else 0
investimento_total = investimento_meta + investimento_google

# ROAS
roas = receita_total / investimento_total if investimento_total > 0 else 0

# Cards principais
col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])

with col1:
    st.markdown(create_roas_card(roas, receita_total, investimento_total), unsafe_allow_html=True)
with col2:
    st.markdown(create_colored_metric_card("Receita Total", format_currency(receita_total), "💵", "#10B981"), unsafe_allow_html=True)
with col3:
    st.markdown(create_colored_metric_card("Contratos Fechados", format_number(quantidade_contratos), "📝", "#8B5CF6"), unsafe_allow_html=True)
with col4:
    st.markdown(create_colored_metric_card("Ticket Médio", format_currency(ticket_medio), "🎫", "#F59E0B"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Breakdown investimento
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(create_colored_metric_card("Investimento Total", format_currency(investimento_total), "💰", "#1a1a2e"), unsafe_allow_html=True)
with col2:
    st.markdown(create_colored_metric_card("Meta Ads", format_currency(investimento_meta), "📘", "#0668E1"), unsafe_allow_html=True)
with col3:
    st.markdown(create_colored_metric_card("Google Ads", format_currency(investimento_google), "🔍", "#34A853"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Gráficos ROAS Mensal
receita_por_mes = receita_data.get('receita_por_mes', pd.DataFrame())

if not receita_por_mes.empty and not demo_mode:
    investimento_por_mes = {}
    
    # Meta por mês
    if not meta_campaigns.empty and 'data' in meta_campaigns.columns:
        meta_campaigns_copy = meta_campaigns.copy()
        meta_campaigns_copy['mes_ano'] = pd.to_datetime(meta_campaigns_copy['data']).dt.strftime('%Y-%m')
        for mes, valor in meta_campaigns_copy.groupby('mes_ano')['valor_gasto'].sum().items():
            investimento_por_mes[mes] = investimento_por_mes.get(mes, 0) + valor
    
    # Google por mês (proporcional)
    if investimento_google > 0:
        dias_periodo = (end_date - start_date).days + 1
        valor_diario_google = investimento_google / dias_periodo
        for mes_ano in receita_por_mes['mes_ano'].unique():
            if mes_ano:
                try:
                    ano, mes = mes_ano.split('-')
                    from calendar import monthrange
                    dias_mes = monthrange(int(ano), int(mes))[1]
                    investimento_por_mes[mes_ano] = investimento_por_mes.get(mes_ano, 0) + (valor_diario_google * dias_mes)
                except:
                    pass
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(create_roas_monthly_chart(receita_por_mes, investimento_por_mes), use_container_width=True)
    
    with col2:
        st.plotly_chart(create_roas_line_chart(receita_por_mes, investimento_por_mes), use_container_width=True)
    
    with st.expander("📋 Detalhamento Mensal"):
        df_det = receita_por_mes.copy()
        df_det['investimento'] = df_det['mes_ano'].map(investimento_por_mes).fillna(0)
        df_det['roas'] = df_det.apply(lambda r: r['receita'] / r['investimento'] if r['investimento'] > 0 else 0, axis=1)
        df_det['lucro'] = df_det['receita'] - df_det['investimento']
        
        df_show = df_det[['mes_ano_label', 'contratos', 'investimento', 'receita', 'lucro', 'roas']].copy()
        df_show.columns = ['Mês', 'Contratos', 'Investimento', 'Receita', 'Lucro', 'ROAS']
        df_show['Investimento'] = df_show['Investimento'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_show['Receita'] = df_show['Receita'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_show['Lucro'] = df_show['Lucro'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_show['ROAS'] = df_show['ROAS'].apply(lambda x: f"{x:.2f}x")
        
        st.dataframe(df_show, use_container_width=True, hide_index=True)

st.markdown("<br>", unsafe_allow_html=True)


# ===========================================
# FUNIL DE CONVERSÃO
# ===========================================

st.markdown("## 🎯 Funil de Conversão")

col1, col2, col3, col4 = st.columns(4)
total = funnel_data['total_leads'] if funnel_data['total_leads'] > 0 else 1

with col1:
    st.markdown(create_funnel_card("Total de Leads", funnel_data['total_leads'], 100, "#3B82F6"), unsafe_allow_html=True)
with col2:
    st.markdown(create_funnel_card("Qualificados", funnel_data['qualificados'], (funnel_data['qualificados'] / total * 100), "#8B5CF6"), unsafe_allow_html=True)
with col3:
    st.markdown(create_funnel_card("Convertidos", funnel_data['convertidos'], (funnel_data['convertidos'] / total * 100), "#10B981"), unsafe_allow_html=True)
with col4:
    st.markdown(create_funnel_card("Desqualificados", funnel_data['desqualificados'], (funnel_data['desqualificados'] / total * 100), "#EF4444"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📊 Visualização do Funil")
    st.plotly_chart(create_funnel_chart(funnel_data), use_container_width=True)

with col2:
    st.markdown("### 📈 Taxas de Conversão")
    
    if funnel_data['total_leads'] > 0:
        taxa_qualificacao = funnel_data['qualificados'] / funnel_data['total_leads'] * 100
        taxa_conversao = funnel_data['convertidos'] / funnel_data['total_leads'] * 100
        taxa_desqualificacao = funnel_data['desqualificados'] / funnel_data['total_leads'] * 100
        taxa_fechamento = funnel_data['convertidos'] / funnel_data['qualificados'] * 100 if funnel_data['qualificados'] > 0 else 0
    else:
        taxa_qualificacao = taxa_conversao = taxa_desqualificacao = taxa_fechamento = 0
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Taxa de Qualificação", f"{taxa_qualificacao:.1f}%")
        st.metric("Taxa de Conversão", f"{taxa_conversao:.1f}%")
    with col_b:
        st.metric("Taxa de Fechamento", f"{taxa_fechamento:.1f}%")
        st.metric("Taxa de Desqualificação", f"{taxa_desqualificacao:.1f}%")


# ===========================================
# ABAS
# ===========================================

st.markdown("---")

tab_meta, tab_google, tab_campanhas, tab_leads, tab_tabela = st.tabs(["📘 Meta Ads", "🔍 Google Ads", "🎯 Por Campanha", "📊 Visão Geral", "📋 Tabela de Leads"])

# ABA META ADS
with tab_meta:
    if meta_summary and not demo_mode:
        st.markdown("### 📘 Performance Meta Ads")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(create_colored_metric_card("Valor Investido", format_currency(meta_summary['valor_gasto']), "💰", "#0668E1"), unsafe_allow_html=True)
        with col2:
            st.markdown(create_colored_metric_card("Leads Gerados", format_number(meta_summary['leads']), "👥", "#8B5CF6"), unsafe_allow_html=True)
        with col3:
            st.markdown(create_colored_metric_card("Custo por Lead", format_currency(meta_summary['cpl']), "💵", "#10B981"), unsafe_allow_html=True)
        with col4:
            st.markdown(create_colored_metric_card("Cliques", format_number(meta_summary['cliques']), "👆", "#F59E0B"), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(create_metric_card("Impressões", format_number(meta_summary['impressoes']), "👁️"), unsafe_allow_html=True)
        with col2:
            st.markdown(create_metric_card("Alcance", format_number(meta_summary['alcance']), "📢"), unsafe_allow_html=True)
        with col3:
            st.markdown(create_metric_card("CTR", format_percentage(meta_summary['ctr']), "📊"), unsafe_allow_html=True)
        with col4:
            st.markdown(create_metric_card("CPC", format_currency(meta_summary['cpc']), "💳"), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not meta_campaigns.empty:
            campaigns_grouped = meta.get_campaigns_by_name(meta_campaigns)
            if not campaigns_grouped.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(create_bar_chart(campaigns_grouped, 'campanha', 'valor_gasto', '💰 Investimento por Campanha', '#0668E1'), use_container_width=True)
                with col2:
                    st.plotly_chart(create_bar_chart(campaigns_grouped, 'campanha', 'leads', '👥 Leads por Campanha', '#8B5CF6'), use_container_width=True)
    elif demo_mode:
        st.info("📊 Modo demonstração ativado.")
    else:
        st.warning("⚠️ Meta Ads não configurado. Adicione as credenciais nos Secrets.")

# ABA GOOGLE ADS
with tab_google:
    if google_summary and not demo_mode:
        st.markdown("### 🔍 Performance Google Ads")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(create_colored_metric_card("Valor Investido", format_currency(google_summary['cost']), "💰", "#34A853"), unsafe_allow_html=True)
        with col2:
            st.markdown(create_colored_metric_card("Conversões", format_number(google_summary['conversions']), "🎯", "#4285F4"), unsafe_allow_html=True)
        with col3:
            cpa = google_summary['cost'] / google_summary['conversions'] if google_summary['conversions'] > 0 else 0
            st.markdown(create_colored_metric_card("CPA", format_currency(cpa), "💵", "#EA4335"), unsafe_allow_html=True)
        with col4:
            st.markdown(create_colored_metric_card("Cliques", format_number(google_summary['clicks']), "👆", "#FBBC05"), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(create_metric_card("Impressões", format_number(google_summary['impressions']), "👁️"), unsafe_allow_html=True)
        with col2:
            st.markdown(create_metric_card("CTR", format_percentage(google_summary['ctr']), "📊"), unsafe_allow_html=True)
        with col3:
            st.markdown(create_metric_card("CPC", format_currency(google_summary['cpc']), "💳"), unsafe_allow_html=True)
        with col4:
            taxa_conv = (google_summary['conversions'] / google_summary['clicks'] * 100) if google_summary['clicks'] > 0 else 0
            st.markdown(create_metric_card("Taxa Conv.", format_percentage(taxa_conv), "📈"), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not google_campaigns.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_bar_chart(google_campaigns, 'campanha', 'custo', '💰 Investimento por Campanha', '#34A853'), use_container_width=True)
            with col2:
                st.plotly_chart(create_bar_chart(google_campaigns, 'campanha', 'conversoes', '🎯 Conversões por Campanha', '#4285F4'), use_container_width=True)
            
            with st.expander("📋 Detalhamento por Campanha"):
                df_g = google_campaigns.copy()
                df_g['CPA'] = df_g.apply(lambda r: r['custo'] / r['conversoes'] if r['conversoes'] > 0 else 0, axis=1)
                df_g['CTR'] = df_g.apply(lambda r: r['cliques'] / r['impressoes'] * 100 if r['impressoes'] > 0 else 0, axis=1)
                
                df_show = df_g[['campanha', 'custo', 'impressoes', 'cliques', 'conversoes', 'CTR', 'CPA']].copy()
                df_show.columns = ['Campanha', 'Custo', 'Impressões', 'Cliques', 'Conversões', 'CTR', 'CPA']
                df_show['Custo'] = df_show['Custo'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                df_show['Impressões'] = df_show['Impressões'].apply(lambda x: f"{x:,}".replace(",", "."))
                df_show['CTR'] = df_show['CTR'].apply(lambda x: f"{x:.2f}%")
                df_show['CPA'] = df_show['CPA'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                st.dataframe(df_show, use_container_width=True, hide_index=True)
    
    elif demo_mode:
        st.markdown("### 🔍 Performance Google Ads (Demo)")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(create_colored_metric_card("Valor Investido", format_currency(3500), "💰", "#34A853"), unsafe_allow_html=True)
        with col2:
            st.markdown(create_colored_metric_card("Conversões", format_number(85), "🎯", "#4285F4"), unsafe_allow_html=True)
        with col3:
            st.markdown(create_colored_metric_card("CPA", format_currency(41.18), "💵", "#EA4335"), unsafe_allow_html=True)
        with col4:
            st.markdown(create_colored_metric_card("Cliques", format_number(1800), "👆", "#FBBC05"), unsafe_allow_html=True)
        st.info("📊 Modo demonstração ativado.")
    else:
        st.warning("⚠️ Google Ads não configurado.")
        st.markdown("""
        **Para configurar, adicione no `config.py` ou Secrets:**
        ```python
        GOOGLE_ADS_DEVELOPER_TOKEN = "seu_token"
        GOOGLE_ADS_CLIENT_ID = "seu_client_id"
        GOOGLE_ADS_CLIENT_SECRET = "seu_secret"
        GOOGLE_ADS_REFRESH_TOKEN = "seu_refresh_token"
        GOOGLE_ADS_CUSTOMER_ID = "1234567890"
        ```
        """)

with tab_campanhas:
    if not leads_df.empty:
        leads_por_campanha = gs.get_leads_by_campaign(leads_df)
        if not leads_por_campanha.empty:
            st.markdown("### 🎯 Leads por Campanha")
            st.plotly_chart(create_bar_chart(leads_por_campanha, leads_por_campanha.columns[0], 'leads', '📊 Leads por Campanha', '#10B981'), use_container_width=True)

with tab_leads:
    if not leads_df.empty:
        st.markdown("### 📱 Leads por Plataforma")
        if 'plataforma' in leads_df.columns:
            meta_leads = len(leads_df[leads_df['plataforma'] == 'Meta Ads'])
            google_leads = len(leads_df[leads_df['plataforma'] == 'Google Ads'])
            outros_leads = len(leads_df[leads_df['plataforma'] == 'Outro'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(create_metric_card("Meta Ads", format_number(meta_leads), "📘"), unsafe_allow_html=True)
            with col2:
                st.markdown(create_metric_card("Google Ads", format_number(google_leads), "🔍"), unsafe_allow_html=True)
            with col3:
                st.markdown(create_metric_card("Outros", format_number(outros_leads), "📌"), unsafe_allow_html=True)

with tab_tabela:
    if not leads_df.empty:
        st.markdown("### 📋 Todos os Leads")
        st.dataframe(leads_df, use_container_width=True, hide_index=True, height=500)


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
