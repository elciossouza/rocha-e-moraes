# 📊 Dashboard de Ads - Meta Ads & Google Ads

Dashboard interativo em Streamlit para análise de performance de campanhas de anúncios no Meta Ads (Facebook/Instagram) e Google Ads, com integração de dados de leads via Google Sheets.

![Dashboard Preview](preview.png)

## 🎯 Funcionalidades

- **Visão Geral Consolidada**: Métricas totais de investimento, leads e CPL
- **Análise Meta Ads**: Valor gasto, leads, CPL, performance por campanha e conjunto de anúncios
- **Análise Google Ads**: Valor gasto, leads, CPL, performance por campanha
- **Tabela de Leads**: Visualização completa dos leads com filtros e exportação CSV
- **Modo Demonstração**: Visualize o dashboard com dados de exemplo
- **Filtros de Período**: Seleção flexível de datas

## 📁 Estrutura do Projeto

```
dashboard_ads/
├── app.py                  # Aplicação principal Streamlit
├── config.py               # Configurações e variáveis de ambiente
├── google_sheets.py        # Módulo de conexão com Google Sheets
├── google_ads_api.py       # Módulo de conexão com Google Ads API
├── meta_ads_api.py         # Módulo de conexão com Meta Ads API
├── requirements.txt        # Dependências do projeto
├── .env.example            # Exemplo de variáveis de ambiente
├── .env                    # Suas variáveis de ambiente (criar)
└── credentials.json        # Credenciais da conta de serviço Google (adicionar)
```

## 🚀 Instalação

### 1. Pré-requisitos

- Python 3.9 ou superior
- Conta de serviço Google Cloud com acesso ao Sheets
- (Opcional) Tokens de acesso das APIs Google Ads e Meta Ads

### 2. Clone ou copie os arquivos

```bash
# Crie um diretório para o projeto
mkdir dashboard_ads
cd dashboard_ads

# Copie todos os arquivos do projeto para este diretório
```

### 3. Crie um ambiente virtual (recomendado)

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Configure as variáveis de ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env com suas credenciais
```

### 6. Adicione as credenciais do Google

Coloque o arquivo `credentials.json` da sua conta de serviço na raiz do projeto.

### 7. Execute o dashboard

```bash
streamlit run app.py
```

O dashboard estará disponível em: `http://localhost:8501`

## ⚙️ Configuração Detalhada

### Google Sheets

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto ou use um existente
3. Ative a API do Google Sheets e Google Drive
4. Crie uma conta de serviço
5. Baixe o arquivo JSON de credenciais
6. Compartilhe sua planilha com o email da conta de serviço

**Estrutura esperada da planilha:**

| DATA / HORA | ORIGEM | CAMPANHA | CONJUNTO DE ANÚNCIOS | CRIATIVO | NOME | E-MAIL | TELEFONE | ID DO FACEBOOK |
|-------------|--------|----------|----------------------|----------|------|--------|----------|----------------|
| 2024-06-27T08:31:33.000Z | Busca paga \| Facebook Ads | Superendividamento | CADASTRO \| SERVIDORES | Servidor, médico | João Silva | joao@email.com | 5511999999999 | 17196662526 |

### Google Ads API

1. Crie uma conta de desenvolvedor no [Google Ads API](https://developers.google.com/google-ads/api/docs/first-call/overview)
2. Obtenha o Developer Token
3. Configure OAuth2 e obtenha o Refresh Token
4. Adicione as credenciais no arquivo `.env`

**Variáveis necessárias:**
```
GOOGLE_ADS_DEVELOPER_TOKEN=seu_token
GOOGLE_ADS_CLIENT_ID=seu_client_id
GOOGLE_ADS_CLIENT_SECRET=seu_secret
GOOGLE_ADS_REFRESH_TOKEN=seu_refresh_token
GOOGLE_ADS_CUSTOMER_ID=1234567890
```

### Meta Ads API

1. Crie um app no [Meta for Developers](https://developers.facebook.com/)
2. Configure o Marketing API
3. Gere um Access Token com permissões de leitura
4. Obtenha o ID da conta de anúncios

**Variáveis necessárias:**
```
META_ACCESS_TOKEN=seu_access_token
META_AD_ACCOUNT_ID=act_123456789
```

## 🎨 Personalização

### Alterar cores

Edite o arquivo `config.py`:

```python
COLORS = {
    "primary": "#1a73e8",
    "secondary": "#0668E1",
    "success": "#34A853",
    # ... outras cores
}
```

### Alterar nome da empresa

No arquivo `.env`:
```
COMPANY_NAME=Nome da Sua Empresa
DASHBOARD_TITLE=Título do Dashboard
```

### Mapear colunas da planilha

Se sua planilha tem nomes de colunas diferentes, edite em `config.py`:

```python
COLUMN_MAPPING = {
    "data_hora": "SUA_COLUNA_DATA",
    "origem": "SUA_COLUNA_ORIGEM",
    # ... outras colunas
}
```

## 📊 Métricas Calculadas

| Métrica | Fórmula |
|---------|---------|
| **CPL (Custo por Lead)** | Valor Gasto ÷ Quantidade de Leads |
| **CTR (Taxa de Cliques)** | (Cliques ÷ Impressões) × 100 |
| **CPC (Custo por Clique)** | Valor Gasto ÷ Cliques |
| **Taxa de Conversão** | (Leads ÷ Cliques) × 100 |

## 🔧 Solução de Problemas

### Erro de conexão com Google Sheets

1. Verifique se o arquivo `credentials.json` está na raiz do projeto
2. Confirme que a planilha está compartilhada com o email da conta de serviço
3. Verifique se o `SPREADSHEET_ID` está correto no `.env`

### Erro nas APIs de Ads

1. Confirme que os tokens de acesso estão válidos
2. Verifique as permissões da conta
3. Use o **Modo Demonstração** para testar o dashboard sem APIs

### Cache de dados

O dashboard usa cache de 5 minutos. Para forçar atualização:
- Pressione `Ctrl+Shift+R` no navegador
- Ou reinicie o servidor Streamlit

## 📝 Licença

Este projeto foi desenvolvido para uso interno. Adapte conforme necessário.

## 🤝 Suporte

Para dúvidas ou sugestões, entre em contato com o desenvolvedor.

---

**Desenvolvido com ❤️ usando Streamlit**
