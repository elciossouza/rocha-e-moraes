# 🚀 Guia Completo: Dashboard de Ads

Este guia detalha **todos os passos** para configurar e publicar seu dashboard, desde a criação do repositório no GitHub até o deploy no Streamlit Cloud.

---

## 📋 Índice

1. [Preparação do GitHub](#1-preparação-do-github)
2. [Configuração Local](#2-configuração-local)
3. [Configuração do Google Cloud](#3-configuração-do-google-cloud)
4. [Configuração da Planilha](#4-configuração-da-planilha)
5. [Teste Local](#5-teste-local)
6. [Deploy no Streamlit Cloud](#6-deploy-no-streamlit-cloud)
7. [Configuração das APIs de Ads (Opcional)](#7-configuração-das-apis-de-ads-opcional)

---

## 1. Preparação do GitHub

### 1.1 Criar Repositório

1. Acesse [github.com](https://github.com) e faça login
2. Clique no botão **"+"** no canto superior direito → **"New repository"**
3. Configure:
   - **Repository name:** `dashboard-ads-cliente` (ou nome de sua preferência)
   - **Description:** Dashboard de análise de campanhas Meta Ads e Google Ads
   - **Visibility:** Private (recomendado para projetos de clientes)
   - ✅ Marque **"Add a README file"**
   - ✅ Marque **"Add .gitignore"** → selecione **Python**
4. Clique em **"Create repository"**

### 1.2 Clonar Repositório

Abra o terminal (CMD, PowerShell ou Terminal) e execute:

```bash
# Navegue até a pasta onde quer salvar o projeto
cd ~/Documentos

# Clone o repositório (substitua pelo seu usuário)
git clone https://github.com/SEU_USUARIO/dashboard-ads-cliente.git

# Entre na pasta
cd dashboard-ads-cliente
```

### 1.3 Adicionar Arquivos do Dashboard

1. Extraia o arquivo `dashboard_ads.zip` que você baixou
2. Copie **todos os arquivos** para a pasta do repositório clonado
3. A estrutura deve ficar assim:

```
dashboard-ads-cliente/
├── .streamlit/
│   └── config.toml
├── app.py
├── config.py
├── google_sheets.py
├── google_ads_api.py
├── meta_ads_api.py
├── requirements.txt
├── .env.example
├── README.md
└── GUIA_COMPLETO.md
```

### 1.4 Configurar .gitignore

Edite o arquivo `.gitignore` e adicione estas linhas para **proteger suas credenciais**:

```gitignore
# Credenciais - NUNCA enviar para o GitHub
.env
credentials.json
*.json
!package.json

# Python
__pycache__/
*.py[cod]
*$py.class
.Python
venv/
env/
.venv/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

### 1.5 Enviar para o GitHub

```bash
# Adicionar todos os arquivos
git add .

# Criar commit
git commit -m "feat: adiciona dashboard de ads"

# Enviar para o GitHub
git push origin main
```

---

## 2. Configuração Local

### 2.1 Instalar Python

Se ainda não tem Python instalado:

**Windows:**
1. Acesse [python.org/downloads](https://www.python.org/downloads/)
2. Baixe a versão mais recente (3.11 ou 3.12)
3. Execute o instalador
4. ⚠️ **IMPORTANTE:** Marque a opção **"Add Python to PATH"**
5. Clique em "Install Now"

**Verificar instalação:**
```bash
python --version
# Deve mostrar: Python 3.11.x ou similar
```

### 2.2 Criar Ambiente Virtual

```bash
# Navegue até a pasta do projeto
cd ~/Documentos/dashboard-ads-cliente

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows (CMD):
venv\Scripts\activate

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux/Mac:
source venv/bin/activate
```

Quando ativado, você verá `(venv)` no início da linha do terminal.

### 2.3 Instalar Dependências

```bash
# Com o ambiente virtual ativado
pip install -r requirements.txt
```

Aguarde a instalação de todos os pacotes (pode levar alguns minutos).

### 2.4 Criar Arquivo .env

```bash
# Copiar o arquivo de exemplo
# Windows:
copy .env.example .env

# Linux/Mac:
cp .env.example .env
```

---

## 3. Configuração do Google Cloud

### 3.1 Criar Projeto no Google Cloud

1. Acesse [console.cloud.google.com](https://console.cloud.google.com/)
2. Faça login com sua conta Google
3. No topo da página, clique no seletor de projetos
4. Clique em **"NOVO PROJETO"**
5. Configure:
   - **Nome do projeto:** `dashboard-ads` (ou outro nome)
   - **Local:** deixe o padrão
6. Clique em **"CRIAR"**
7. Aguarde a criação e selecione o projeto

### 3.2 Ativar APIs Necessárias

1. No menu lateral, vá em **"APIs e serviços"** → **"Biblioteca"**
2. Pesquise e ative cada uma destas APIs:
   - **Google Sheets API** → Clique → **"ATIVAR"**
   - **Google Drive API** → Clique → **"ATIVAR"**

### 3.3 Criar Conta de Serviço

1. No menu lateral, vá em **"APIs e serviços"** → **"Credenciais"**
2. Clique em **"+ CRIAR CREDENCIAIS"** → **"Conta de serviço"**
3. Configure:
   - **Nome da conta de serviço:** `dashboard-sheets`
   - **ID da conta de serviço:** será preenchido automaticamente
   - **Descrição:** Acesso ao Google Sheets para dashboard
4. Clique em **"CRIAR E CONTINUAR"**
5. Em "Conceder acesso", pode pular → Clique em **"CONTINUAR"**
6. Clique em **"CONCLUÍDO"**

### 3.4 Gerar Chave JSON

1. Na lista de contas de serviço, clique na conta que você criou
2. Vá na aba **"CHAVES"**
3. Clique em **"ADICIONAR CHAVE"** → **"Criar nova chave"**
4. Selecione **"JSON"** → Clique em **"CRIAR"**
5. O arquivo será baixado automaticamente (ex: `dashboard-ads-xxxxx.json`)
6. **Renomeie** o arquivo para `credentials.json`
7. **Mova** o arquivo para a pasta do projeto

### 3.5 Copiar Email da Conta de Serviço

1. Ainda na página da conta de serviço, copie o **Email** 
   - Formato: `dashboard-sheets@dashboard-ads-xxxxx.iam.gserviceaccount.com`
2. Guarde este email, você vai precisar no próximo passo

---

## 4. Configuração da Planilha

### 4.1 Compartilhar Planilha com a Conta de Serviço

1. Abra sua planilha do Google Sheets com os leads
2. Clique no botão **"Compartilhar"** (canto superior direito)
3. No campo de email, cole o **email da conta de serviço** que você copiou
4. Selecione permissão **"Leitor"** (ou "Editor" se precisar escrever)
5. Desmarque "Notificar pessoas"
6. Clique em **"Compartilhar"**

### 4.2 Obter ID da Planilha

O ID da planilha está na URL:

```
https://docs.google.com/spreadsheets/d/ESTE_E_O_ID_DA_PLANILHA/edit
```

Copie apenas a parte entre `/d/` e `/edit`.

**Exemplo:**
- URL: `https://docs.google.com/spreadsheets/d/1ABC123def456GHI789/edit`
- ID: `1ABC123def456GHI789`

### 4.3 Configurar Arquivo .env

Abra o arquivo `.env` com um editor de texto e configure:

```env
# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
SPREADSHEET_ID=COLE_O_ID_DA_SUA_PLANILHA_AQUI

# Nome da aba principal (verifique o nome exato na sua planilha)
SHEET_NAME_META_LEADS=Página1

# Configurações do Dashboard
DASHBOARD_TITLE=Rocha & Moraes | Dashboard de Ads
COMPANY_NAME=Rocha & Moraes Advogados
```

---

## 5. Teste Local

### 5.1 Executar o Dashboard

```bash
# Certifique-se de estar na pasta do projeto com venv ativado
cd ~/Documentos/dashboard-ads-cliente

# Ativar ambiente virtual (se não estiver)
# Windows:
venv\Scripts\activate

# Executar Streamlit
streamlit run app.py
```

### 5.2 Acessar o Dashboard

O terminal mostrará:
```
  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Abra o navegador e acesse: **http://localhost:8501**

### 5.3 Testar Funcionamento

1. O dashboard abrirá com o **Modo Demonstração** ativado
2. Desative o toggle "Modo Demonstração" no sidebar para usar dados reais
3. Se tudo estiver configurado corretamente, você verá os dados da planilha

### 5.4 Resolver Problemas Comuns

**Erro: "Arquivo credentials.json não encontrado"**
- Verifique se o arquivo está na pasta raiz do projeto
- Verifique se o nome está exatamente `credentials.json`

**Erro: "Planilha não encontrada"**
- Verifique se o SPREADSHEET_ID está correto no .env
- Verifique se compartilhou a planilha com a conta de serviço

**Erro: "Aba não encontrada"**
- Verifique o nome exato da aba na planilha
- Atualize SHEET_NAME_META_LEADS no .env

---

## 6. Deploy no Streamlit Cloud

O Streamlit Cloud é **gratuito** e hospeda seu dashboard online!

### 6.1 Criar Conta no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io/)
2. Clique em **"Sign up"**
3. Conecte com sua **conta do GitHub**
4. Autorize o acesso

### 6.2 Criar Novo App

1. No dashboard do Streamlit Cloud, clique em **"New app"**
2. Configure:
   - **Repository:** selecione `dashboard-ads-cliente`
   - **Branch:** `main`
   - **Main file path:** `app.py`
3. Clique em **"Advanced settings"**

### 6.3 Configurar Secrets (Credenciais)

⚠️ **IMPORTANTE:** No Streamlit Cloud, as credenciais ficam em "Secrets", não em arquivos.

1. Em "Advanced settings", vá na aba **"Secrets"**
2. Cole o seguinte conteúdo (ajustando com suas informações):

```toml
# Configurações Gerais
SPREADSHEET_ID = "COLE_O_ID_DA_SUA_PLANILHA"
SHEET_NAME_META_LEADS = "Página1"
DASHBOARD_TITLE = "Rocha & Moraes | Dashboard de Ads"
COMPANY_NAME = "Rocha & Moraes Advogados"

# Credenciais do Google (cole o conteúdo do credentials.json)
[gcp_service_account]
type = "service_account"
project_id = "seu-projeto-id"
private_key_id = "sua-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE_PRIVADA_AQUI\n-----END PRIVATE KEY-----\n"
client_email = "dashboard-sheets@seu-projeto.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

**Para preencher [gcp_service_account]:**
1. Abra o arquivo `credentials.json` com um editor de texto
2. Copie cada campo para o formato acima
3. ⚠️ A `private_key` deve manter as quebras de linha como `\n`

### 6.4 Atualizar Código para Streamlit Cloud

Precisamos ajustar o código para ler credenciais dos Secrets. Atualize o arquivo `google_sheets.py`:

```python
# Adicione no início do arquivo, após os imports:
import streamlit as st

def get_google_sheets_client():
    """
    Cria e retorna um cliente autenticado do Google Sheets
    Funciona tanto local (credentials.json) quanto no Streamlit Cloud (secrets)
    """
    try:
        # Tenta usar secrets do Streamlit Cloud primeiro
        if "gcp_service_account" in st.secrets:
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=SCOPES
            )
        else:
            # Fallback para arquivo local
            credentials = Credentials.from_service_account_file(
                config.GOOGLE_SHEETS_CREDENTIALS_FILE,
                scopes=SCOPES
            )
        
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets: {str(e)}")
        return None
```

### 6.5 Deploy

1. Clique em **"Deploy!"**
2. Aguarde o deploy (pode levar 2-5 minutos)
3. Quando concluído, você terá uma URL como:
   - `https://seu-usuario-dashboard-ads-cliente-app-xxxxx.streamlit.app`

### 6.6 Compartilhar com Cliente

A URL do Streamlit Cloud é pública por padrão. Para restringir acesso:

1. Vá em **"Settings"** do seu app
2. Em **"Sharing"**, selecione **"This app is private"**
3. Adicione os emails autorizados a acessar

---

## 7. Configuração das APIs de Ads (Opcional)

Para ter métricas de gastos em tempo real das plataformas de ads.

### 7.1 Meta Ads API

1. Acesse [developers.facebook.com](https://developers.facebook.com/)
2. Crie um novo app ou use existente
3. Adicione o produto **"Marketing API"**
4. Em **"Ferramentas"** → **"Graph API Explorer"**:
   - Selecione seu app
   - Gere um token com permissões: `ads_read`, `ads_management`
5. Para token de longa duração, use o Access Token Debugger
6. Obtenha o ID da conta de anúncios (formato: `act_123456789`)

Adicione no `.env` ou Secrets:
```
META_ACCESS_TOKEN=seu_token_aqui
META_AD_ACCOUNT_ID=act_123456789
```

### 7.2 Google Ads API

1. Crie conta em [Google Ads API](https://developers.google.com/google-ads/api/docs/first-call/overview)
2. Solicite Developer Token (pode levar alguns dias para aprovação)
3. Configure OAuth2 no Google Cloud Console
4. Use a ferramenta de autenticação para gerar Refresh Token

Adicione no `.env` ou Secrets:
```
GOOGLE_ADS_DEVELOPER_TOKEN=seu_token
GOOGLE_ADS_CLIENT_ID=seu_client_id
GOOGLE_ADS_CLIENT_SECRET=seu_secret
GOOGLE_ADS_REFRESH_TOKEN=seu_refresh_token
GOOGLE_ADS_CUSTOMER_ID=1234567890
```

---

## 📝 Resumo dos Comandos

```bash
# Clonar repositório
git clone https://github.com/SEU_USUARIO/dashboard-ads-cliente.git
cd dashboard-ads-cliente

# Criar e ativar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Criar arquivo de configuração
copy .env.example .env  # Windows
cp .env.example .env  # Linux/Mac

# Executar dashboard
streamlit run app.py

# Enviar alterações para GitHub
git add .
git commit -m "sua mensagem"
git push origin main
```

---

## ❓ Dúvidas Frequentes

**P: Posso usar o dashboard sem as APIs do Meta e Google Ads?**
R: Sim! O dashboard funciona apenas com a planilha de leads. As APIs são opcionais para ter métricas de gastos em tempo real.

**P: O Streamlit Cloud é realmente gratuito?**
R: Sim, para apps públicos e privados com uso moderado. Veja limites em [streamlit.io/cloud](https://streamlit.io/cloud)

**P: Como atualizo o dashboard depois de publicar?**
R: Basta fazer commit e push no GitHub. O Streamlit Cloud atualiza automaticamente.

**P: Posso usar domínio personalizado?**
R: Sim, no plano Teams do Streamlit Cloud ou hospedando em servidor próprio.

---

**Desenvolvido com ❤️ para simplificar sua análise de Ads**
