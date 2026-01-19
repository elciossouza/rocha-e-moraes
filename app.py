"""
Dashboard de Análise de Ads - Meta Ads e Google Ads
Com Funil de Conversão Completo e Filtro de Data
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Importa módulos locais
import config
import google_sheets as gs

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
    
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        padding: 32px;
        border-radius: 20px;
        margin-bottom: 32px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
    }
    
    .main-header h1 { margin: 0; font-size: 2rem; font-weight: 700; }
    .main-header p { margin: 8px 0 0 0; opacity: 0.8; font-size: 1rem; }
    
    .funnel-card {
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    .funnel-value { font-size: 2.5rem; font-weight: 700; }
    .funnel-label { font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; }
    .funnel-percent { font-size: 1rem; opacity: 0.8; margin-top: 8px; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ===========================================
# FUNÇÕES AUXILIARES
# ===========================================

def format_number(value: int) -> str:
    return f"{value:,}".replace(",", ".")

def format_percentage(value: float) -> str:
    return f"{value:.1f}%"

def create_metric_card(label: str, value: str, icon: str = "") -> str:
    return f"""
    <div class="metric-card">
        <p class="metric-value">{icon} {value}</p>
        <p class="metric-label">{label}</p>
    </div>
    """

def create_funnel_card(label: str, value: int, percent: float, color: str) -> str:
    return f"""
    <div class="funnel-card" style="background: {color};">
        <p class="funnel-value">{format_number(value)}</p>
        <p class="funnel-label">{label}</p>
        <p class="funnel-percent">{format_percentage(percent)} do total</p>
    </div>
    """

def create_funnel_chart(funnel_data: dict) -> go.Figure:
    """Cria gráfico de funil"""
    
    stages = ['Total de Leads', 'Qualificados', 'Convertidos']
    values = [
        funnel_data['total_leads'],
        funnel_data['qualificados'],
        funnel_data['convertidos']
    ]
    colors = ['#3B82F6', '#8B5CF6', '#10B981']
    
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textposition="inside",
        textinfo="value+percent initial",
        marker=dict(color=colors),
        connector=dict(line=dict(color="#e9ecef", width=2))
    ))
    
    fig.update_layout(
        font=dict(family="Plus Jakarta Sans", size=14),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=300
    )
    
    return fig

def create_bar_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str) -> go.Figure:
    """Cria gráfico de barras horizontal"""
    
    fig = px.bar(
        df.sort_values(y, ascending=True),
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
    """Cria gráfico de linha"""
    
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
    
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    
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
    
    st.markdown("**Atalhos:**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Últimos 7 dias", use_container_width=True):
            st.session_state['start_date'] = datetime.now().date() - timedelta(days=7)
            st.session_state['end_date'] = datetime.now().date()
            st.rerun()
    with col2:
        if st.button("Últimos 30 dias", use_container_width=True):
            st.session_state['start_date'] = datetime.now().date() - timedelta(days=30)
            st.session_state['end_date'] = datetime.now().date()
            st.rerun()
    
    st.markdown("---")
    
    # Modo Demo
    st.markdown("### ⚙️ Configurações")
    demo_mode = st.toggle("Modo Demonstração", value=False, help="Usa dados de exemplo quando ativado")
    
    st.markdown("---")
    
    st.markdown("""
    <div style="padding: 16px; background: #f8f9fa; border-radius: 12px; font-size: 0.85rem;">
        <p style="margin: 0; color: #6c757d;">
            <strong>💡 Dica:</strong> Desative o modo demonstração para ver os dados reais da planilha.
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


# ===========================================
# CARREGAR DADOS
# ===========================================

def load_data_demo():
    """Dados de demonstração"""
    return {
        'total_leads': 245,
        'qualificados': 89,
        'desqualificados': 56,
        'convertidos': 23,
        'leads_df': pd.DataFrame(),
        'qualificados_df': pd.DataFrame(),
        'desqualificados_df': pd.DataFrame(),
        'convertidos_df': pd.DataFrame()
    }

# Carrega dados COM FILTRO DE DATA
if demo_mode:
    funnel_data = load_data_demo()
    leads_df = pd.DataFrame()
else:
    try:
        # PASSA AS DATAS PARA O FILTRO
        funnel_data = gs.get_funnel_data(start_date, end_date)
        leads_df = funnel_data['leads_df']
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        st.info("Ativando modo demonstração...")
        funnel_data = load_data_demo()
        leads_df = pd.DataFrame()


# ===========================================
# FUNIL DE CONVERSÃO
# ===========================================

st.markdown("## 🎯 Funil de Conversão")

col1, col2, col3, col4 = st.columns(4)

total = funnel_data['total_leads'] if funnel_data['total_leads'] > 0 else 1

with col1:
    st.markdown(create_funnel_card(
        "Total de Leads",
        funnel_data['total_leads'],
        100,
        "#3B82F6"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(create_funnel_card(
        "Qualificados",
        funnel_data['qualificados'],
        (funnel_data['qualificados'] / total * 100),
        "#8B5CF6"
    ), unsafe_allow_html=True)

with col3:
    st.markdown(create_funnel_card(
        "Convertidos",
        funnel_data['convertidos'],
        (funnel_data['convertidos'] / total * 100),
        "#10B981"
    ), unsafe_allow_html=True)

with col4:
    st.markdown(create_funnel_card(
        "Desqualificados",
        funnel_data['desqualificados'],
        (funnel_data['desqualificados'] / total * 100),
        "#EF4444"
    ), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Gráfico de funil
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
        
        if funnel_data['qualificados'] > 0:
            taxa_fechamento = funnel_data['convertidos'] / funnel_data['qualificados'] * 100
        else:
            taxa_fechamento = 0
    else:
        taxa_qualificacao = 0
        taxa_conversao = 0
        taxa_desqualificacao = 0
        taxa_fechamento = 0
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Taxa de Qualificação", f"{taxa_qualificacao:.1f}%", help="Leads → Qualificados")
        st.metric("Taxa de Conversão", f"{taxa_conversao:.1f}%", help="Leads → Convertidos")
    with col_b:
        st.metric("Taxa de Fechamento", f"{taxa_fechamento:.1f}%", help="Qualificados → Convertidos")
        st.metric("Taxa de Desqualificação", f"{taxa_desqualificacao:.1f}%", help="Leads → Desqualificados")


# ===========================================
# ABAS: ANÁLISE DETALHADA
# ===========================================

st.markdown("---")

tab_leads, tab_campanhas, tab_tabela = st.tabs(["📊 Visão Geral", "🎯 Por Campanha", "📋 Tabela de Leads"])


# ===========================================
# ABA VISÃO GERAL
# ===========================================
with tab_leads:
    if not leads_df.empty:
        
        # Métricas por plataforma
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
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráfico de leads por data
        col1, col2 = st.columns(2)
        
        with col1:
            leads_por_data = gs.get_leads_by_date(leads_df)
            if not leads_por_data.empty:
                fig = create_line_chart(leads_por_data, 'data', 'leads', '📈 Leads por Dia', '#3B82F6')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            leads_por_origem = gs.get_leads_by_origin(leads_df)
            if not leads_por_origem.empty:
                fig = create_bar_chart(leads_por_origem, leads_por_origem.columns[0], 'leads', '📊 Leads por Origem', '#8B5CF6')
                st.plotly_chart(fig, use_container_width=True)
    else:
        if demo_mode:
            st.info("📊 Modo demonstração ativado. Desative para ver os dados reais.")
        else:
            st.warning("Nenhum lead encontrado para o período selecionado.")


# ===========================================
# ABA POR CAMPANHA
# ===========================================
with tab_campanhas:
    if not leads_df.empty:
        leads_por_campanha = gs.get_leads_by_campaign(leads_df)
        
        if not leads_por_campanha.empty:
            st.markdown("### 🎯 Performance por Campanha")
            
            fig = create_bar_chart(
                leads_por_campanha,
                leads_por_campanha.columns[0],
                'leads',
                '📊 Leads por Campanha',
                '#10B981'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela de campanhas
            st.markdown("### 📋 Detalhamento")
            st.dataframe(
                leads_por_campanha.sort_values('leads', ascending=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Sem dados de campanha disponíveis.")
    else:
        st.info("Carregue os dados para ver análise por campanha.")


# ===========================================
# ABA TABELA DE LEADS
# ===========================================
with tab_tabela:
    if not leads_df.empty:
        st.markdown("### 📋 Todos os Leads")
        
        # Filtro de plataforma
        if 'plataforma' in leads_df.columns:
            platform_filter = st.selectbox(
                "Filtrar por plataforma:",
                ["Todos", "Meta Ads", "Google Ads", "Outro"]
            )
            
            if platform_filter != "Todos":
                display_df = leads_df[leads_df['plataforma'] == platform_filter]
            else:
                display_df = leads_df
        else:
            display_df = leads_df
        
        # Seleciona colunas relevantes
        cols_to_show = []
        possible_cols = ['DATA / HORA', 'ORIGEM', 'CAMPANHA', 'NOME', 'TELEFONE', 'E-MAIL', 'plataforma']
        
        for col in possible_cols:
            if col in display_df.columns:
                cols_to_show.append(col)
        
        if cols_to_show:
            display_df = display_df[cols_to_show]
        
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
            file_name=f"leads_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    else:
        if demo_mode:
            st.info("📊 Modo demonstração ativado. Desative para ver os dados reais.")
        else:
            st.warning("Nenhum lead encontrado.")


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
