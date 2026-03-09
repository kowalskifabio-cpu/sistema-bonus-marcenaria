import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 1. Configuração da página
st.set_page_config(page_title="Gestão de Bônus Marcenaria", layout="wide")

# Esconder menus
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

# 2. Login
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.title("🔐 Acesso Restrito")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if senha == st.secrets["general"]["password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# 3. Conexão Google Sheets
@st.cache_resource
def conectar():
    info = {
        "type": st.secrets["gspread"]["type"],
        "project_id": st.secrets["gspread"]["project_id"],
        "private_key_id": st.secrets["gspread"]["private_key_id"],
        "private_key": st.secrets["gspread"]["private_key"],
        "client_email": st.secrets["gspread"]["client_email"],
        "client_id": st.secrets["gspread"]["client_id"],
        "auth_uri": st.secrets["gspread"]["auth_uri"],
        "token_uri": st.secrets["gspread"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gspread"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gspread"]["client_x509_cert_url"],
    }
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds).open_by_key(st.secrets["general"]["spreadsheet_id"])

sh = conectar()

def get_ws(name, headers=None):
    try:
        return sh.worksheet(name)
    except:
        ws = sh.add_worksheet(title=name, rows="1000", cols="10")
        if headers:
            ws.append_row(headers)
        return ws

ws_gestores = get_ws("GESTORES")
ws_historico = get_ws("HISTORICO", ["DATA", "GESTOR", "CATEGORIA", "ACAO", "PONTOS", "TIPO", "OBS"])
ws_parametros = get_ws("PARAMETROS", ["CATEGORIA", "SITUACAO", "PONTOS"])

# 4. Funções de Apoio
def calcular_faixa_bonus(pontos):
    if pontos >= 9500: return "100%"
    elif pontos >= 9000: return "90%"
    elif pontos >= 8500: return "80%"
    elif pontos >= 8000: return "70%"
    elif pontos >= 7500: return "60%"
    else: return "0% (Sem Bônus)"

# --- CARREGAR PARAMETROS DA PLANILHA ---
dados_params = ws_parametros.get_all_records()
if not dados_params:
    # Se estiver vazio, carrega o padrão inicial que você definiu
    padrao = [
        ["1️⃣ Gestão Operacional", "Pedido fora do prazo", -200],
        ["2️⃣ Gestão de Pessoas", "Conflito não resolvido", -200],
        ["🚀 Recuperação / Extra", "Redução de desperdício", 200]
    ]
    for p in padrao: ws_parametros.append_row(p)
    dados_params = ws_parametros.get_all_records()

df_params = pd.DataFrame(dados_params)

# --- INTERFACE ---
st.title("🛠️ Sistema de Performance Marcenaria")

tab1, tab2, tab3 = st.tabs(["📝 Lançamentos", "📊 Dashboard", "📜 Parâmetros Transparentes"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        gestores = [r[0] for r in ws_gestores.get_all_values() if r]
        g_sel = st.selectbox("Gestor", gestores if gestores else ["Cadastre na lateral"])
    
    with col2:
        categorias = df_params['CATEGORIA'].unique()
        cat_sel = st.selectbox("Categoria", categorias)
        
        situacoes_filtradas = df_params[df_params['CATEGORIA'] == cat_sel]
        acao_sel = st.selectbox("Situação", situacoes_filtradas['SITUACAO'].tolist())
    
    pontos_acao = int(df_params[df_params['SITUACAO'] == acao_sel]['PONTOS'].values[0])
    tipo = "🔴 Penalidade" if pontos_acao < 0 else "🟢 Recuperação"
    st.info(f"Impacto: {pontos_acao} pontos ({tipo})")
    
    obs = st.text_area("Observações")
    
    if st.button("Confirmar Registro", type="primary"):
        if g_sel != "Cadastre na lateral" and obs:
            data = datetime.now().strftime("%d/%m/%Y %H:%M")
            ws_historico.append_row([data, g_sel, cat_sel, acao_sel, pontos_acao, tipo, obs])
            st.success("✅ Registro realizado com sucesso!")
        else:
            st.error("Preencha todos os campos!")

with tab2:
    try:
        hist = ws_historico.get_all_records()
        if hist:
            df_h = pd.DataFrame(hist)
            resumo = []
            for g in gestores:
                pontos_perdi = df_h[df_h['GESTOR'] == g]['PONTOS'].astype(int).sum()
                saldo = min(10000, 10000 + pontos_perdi)
                resumo.append({"Gestor": g, "Pontuação": saldo, "Bônus": calcular_faixa_bonus(saldo)})
            st.table(pd.DataFrame(resumo))
        else:
            st.info("Sem histórico registrado.")
    except:
        st.error("Erro ao ler histórico. Verifique os cabeçalhos da planilha.")

with tab3:
    st.subheader("Transparência: Regras de Pontuação")
    st.dataframe(df_params, use_container_width=True)
    
    st.markdown("---")
    st.subheader("➕ Cadastrar Nova Regra/Situação")
    with st.expander("Clique para expandir"):
        new_cat = st.selectbox("Nova Categoria", ["1️⃣ Gestão Operacional", "2️⃣ Gestão de Pessoas", "3️⃣ Processos e Organização", "4️⃣ Resultado do Setor", "🚀 Recuperação / Extra"])
        new_sit = st.text_input("Nome da Situação (Ex: Atraso de entrega)")
        new_pts = st.number_input("Pontuação (Negativo para perda, Positivo para ganho)", step=50)
        if st.button("Salvar Nova Regra"):
            ws_parametros.append_row([new_cat, new_sit, new_pts])
            st.success("Regra cadastrada! Atualize a página.")

with st.sidebar:
    st.header("Admin")
    novo_g = st.text_input("Novo Gestor")
    if st.button("Salvar Gestor"):
        ws_gestores.append_row([novo_g])
        st.rerun()
