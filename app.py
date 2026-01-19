"""
Dashboard de Análise de Ads - Meta Ads e Google Ads
Com Funil de Conversão, ROAS e Dados da API do Meta
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
    
    # Prepara dados
    df = receita_df.copy()
    
    # Adiciona investimento ao DataFrame
    df['investimento'] = df['mes_ano'].map(investimento_por_mes).fillna(0)
    df['roas'] = df.apply(lambda row: row['receita'] / row['investimento'] if row['investimento'] > 0 else 0, axis=1)
    
    # Cria gráfico de barras agrupadas
    fig = go.Figure()
    
    # Barras de Investimento
    fig.add_trace(go.Bar(
        name='Investimento',
        x=df['mes_ano_label'],
        y=df['investimento'],
        marker_color='#EF4444',
        text=df['investimento'].apply(lambda x: f'R$ {x:,.0f}'.replace(',', '.')),
        textposition='outside'
    ))
    
    # Barras de Receita
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
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
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
    
    # Linha de ROAS
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
    
    # Linha de referência (ROAS = 1)
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
    
    # Status das conexões com DEBUG
    st.markdown("### 🔗 Conexões")
    
    meta_ok = meta.is_meta_configured()
    
    if meta_ok:
        st.success("✅ Meta Ads conectado")
    else:
        st.warning("⚠️ Meta Ads não configurado")
    
    # DEBUG - Mostra informações sobre as credenciais
    with st.expander("🔧 Debug Meta Ads"):
        debug_info = meta.debug_meta_connection()
        for key, value in debug_info.items():
            st.write(f"**{key}:** {value}")
    
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

if demo_mode:
    funnel_data = load_data_demo()
    leads_df = pd.DataFrame()
    meta_summary = None
    meta_campaigns = pd.DataFrame()
    receita_data = {'receita_total': 45000, 'quantidade_contratos': 23, 'ticket_medio': 1956.52, 'receita_por_mes': pd.DataFrame()}
else:
    try:
        funnel_data = gs.get_funnel_data(start_date, end_date)
        leads_df = funnel_data['leads_df']
        
        # Carrega dados de receita/contratos
        receita_data = gs.get_receita_por_periodo(start_date, end_date)
        
        if meta.is_meta_configured():
            meta_summary = meta.get_meta_summary(start_date, end_date)
            meta_campaigns = meta.get_meta_campaigns(start_date, end_date)
        else:
            meta_summary = None
            meta_campaigns = pd.DataFrame()
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        funnel_data = load_data_demo()
        leads_df = pd.DataFrame()
        meta_summary = None
        meta_campaigns = pd.DataFrame()
        receita_data = {'receita_total': 0, 'quantidade_contratos': 0, 'ticket_medio': 0, 'receita_por_mes': pd.DataFrame()}


# ===========================================
# SEÇÃO DE ROAS
# ===========================================

st.markdown("## 💰 Retorno sobre Investimento (ROAS)")

# Calcula valores
receita_total = receita_data.get('receita_total', 0)
quantidade_contratos = receita_data.get('quantidade_contratos', 0)
ticket_medio = receita_data.get('ticket_medio', 0)

# Pega investimento do Meta Ads (ou zero se não configurado)
investimento_total = meta_summary.get('valor_gasto', 0) if meta_summary else 0

# Calcula ROAS
roas = receita_total / investimento_total if investimento_total > 0 else 0

# Cards principais de ROAS
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

# ===========================================
# GRÁFICOS DE ROAS MENSAL
# ===========================================

receita_por_mes = receita_data.get('receita_por_mes', pd.DataFrame())

if not receita_por_mes.empty and not demo_mode:
    # Busca investimento por mês do Meta Ads
    investimento_por_mes = {}
    
    if not meta_campaigns.empty:
        # Agrupa campanhas por mês
        meta_campaigns_copy = meta_campaigns.copy()
        if 'data' in meta_campaigns_copy.columns:
            meta_campaigns_copy['mes_ano'] = pd.to_datetime(meta_campaigns_copy['data']).dt.strftime('%Y-%m')
            investimento_mensal = meta_campaigns_copy.groupby('mes_ano')['valor_gasto'].sum()
            investimento_por_mes = investimento_mensal.to_dict()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_comparativo = create_roas_monthly_chart(receita_por_mes, investimento_por_mes)
        st.plotly_chart(fig_comparativo, use_container_width=True)
    
    with col2:
        fig_roas = create_roas_line_chart(receita_por_mes, investimento_por_mes)
        st.plotly_chart(fig_roas, use_container_width=True)
    
    # Tabela detalhada por mês
    with st.expander("📋 Detalhamento Mensal"):
        df_detalhado = receita_por_mes.copy()
        df_detalhado['investimento'] = df_detalhado['mes_ano'].map(investimento_por_mes).fillna(0)
        df_detalhado['roas'] = df_detalhado.apply(
            lambda row: row['receita'] / row['investimento'] if row['investimento'] > 0 else 0, axis=1
        )
        df_detalhado['lucro'] = df_detalhado['receita'] - df_detalhado['investimento']
        
        # Formata para exibição
        df_exibir = df_detalhado[['mes_ano_label', 'contratos', 'investimento', 'receita', 'lucro', 'roas']].copy()
        df_exibir.columns = ['Mês', 'Contratos', 'Investimento', 'Receita', 'Lucro', 'ROAS']
        
        # Formata valores
        df_exibir['Investimento'] = df_exibir['Investimento'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_exibir['Receita'] = df_exibir['Receita'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_exibir['Lucro'] = df_exibir['Lucro'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_exibir['ROAS'] = df_exibir['ROAS'].apply(lambda x: f"{x:.2f}x")
        
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)

st.markdown("<br>", unsafe_allow_html=True)


# ===========================================
# MÉTRICAS DE INVESTIMENTO (META ADS)
# ===========================================

if meta_summary and not demo_mode:
    st.markdown("## 📘 Métricas Meta Ads")
    
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
    fig = create_funnel_chart(funnel_data)
    st.plotly_chart(fig, use_container_width=True)

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

tab_meta, tab_campanhas, tab_leads, tab_tabela = st.tabs(["📘 Meta Ads", "🎯 Por Campanha", "📊 Visão Geral", "📋 Tabela de Leads"])

with tab_meta:
    if not meta_campaigns.empty and not demo_mode:
        st.markdown("### 📘 Performance Meta Ads")
        campaigns_grouped = meta.get_campaigns_by_name(meta_campaigns)
        
        if not campaigns_grouped.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig = create_bar_chart(campaigns_grouped, 'campanha', 'valor_gasto', '💰 Investimento por Campanha', '#0668E1')
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = create_bar_chart(campaigns_grouped, 'campanha', 'leads', '👥 Leads por Campanha', '#8B5CF6')
                st.plotly_chart(fig, use_container_width=True)
    else:
        if demo_mode:
            st.info("📊 Modo demonstração ativado.")
        elif not meta.is_meta_configured():
            st.warning("⚠️ Meta Ads não configurado. Adicione as credenciais nos Secrets.")
        else:
            st.info("Nenhum dado encontrado para o período.")

with tab_campanhas:
    if not leads_df.empty:
        leads_por_campanha = gs.get_leads_by_campaign(leads_df)
        if not leads_por_campanha.empty:
            st.markdown("### 🎯 Leads por Campanha")
            fig = create_bar_chart(leads_por_campanha, leads_por_campanha.columns[0], 'leads', '📊 Leads por Campanha', '#10B981')
            st.plotly_chart(fig, use_container_width=True)

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
