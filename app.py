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

def get_ws(name):
    try: return sh.worksheet(name)
    except: 
        ws = sh.add_worksheet(title=name, rows="1000", cols="10")
        if name == "HISTORICO": ws.append_row(["DATA", "GESTOR", "CATEGORIA", "ACAO", "PONTOS", "TIPO", "OBS"])
        return ws

ws_gestores = get_ws("GESTORES")
ws_historico = get_ws("HISTORICO")

# 4. Regras de Negócio (Matriz que você definiu)
MATRIZ = {
    "1️⃣ Gestão Operacional": {
        "Pedido fora do prazo": -200, "Retrabalho por erro gestão": -300, 
        "Falta material planejamento": -250, "Atraso cronograma interno": -100
    },
    "2️⃣ Gestão de Pessoas": {
        "Conflito não resolvido": -200, "Alta rotatividade": -300, 
        "Falta não gerenciada": -100, "Reclamação formal": -200
    },
    "3️⃣ Processos e Organização": {
        "Processo não seguido": -150, "Falta documentação": -100, 
        "Erro informação entre setores": -150, "Falta reunião obrigatória": -100
    },
    "4️⃣ Resultado do Setor": {
        "Meta produtividade não atingida": -400, "Desperdício acima limite": -250, 
        "Falha qualidade cliente": -500
    },
    "🚀 Recuperação / Extra": {
        "Redução de desperdício": 200, "Melhoria de processo": 300, "Meta superada": 400
    }
}

def calcular_faixa_bonus(pontos):
    if pontos >= 9500: return "100%"
    elif pontos >= 9000: return "90%"
    elif pontos >= 8500: return "80%"
    elif pontos >= 8000: return "70%"
    elif pontos >= 7500: return "60%"
    else: return "0% (Sem Bônus)"

# --- INTERFACE ---
st.title("🛠️ Sistema de Performance Marcenaria")

tab1, tab2 = st.tabs(["📝 Lançamentos", "📊 Dashboard de Bônus"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        gestores = [r[0] for r in ws_gestores.get_all_values() if r]
        g_sel = st.selectbox("Selecione o Gestor", gestores if gestores else ["Cadastre na lateral"])
    
    with col2:
        cat_sel = st.selectbox("Categoria", list(MATRIZ.keys()))
        acao_sel = st.selectbox("Ação/Ocorrência", list(MATRIZ[cat_sel].keys()))
    
    pontos_acao = MATRIZ[cat_sel][acao_sel]
    tipo = "🔴 Penalidade" if pontos_acao < 0 else "🟢 Recuperação"
    st.info(f"Impacto: {pontos_acao} pontos ({tipo})")
    
    obs = st.text_area("Observações (Obrigatório)")
    
    if st.button("Confirmar Registro", type="primary"):
        if g_sel != "Cadastre na lateral" and obs:
            data = datetime.now().strftime("%d/%m/%Y %H:%M")
            ws_historico.append_row([data, g_sel, cat_sel, acao_sel, pontos_acao, tipo, obs])
            st.success("Salvo com sucesso!")
            st.balloons()
        else:
            st.error("Preencha o nome do gestor e a observação!")

with tab2:
    hist = ws_historico.get_all_records()
    if hist:
        df = pd.DataFrame(hist)
        resumo = []
        for g in gestores:
            total_pontos = 10000 + df[df['GESTOR'] == g]['PONTOS'].astype(int).sum()
            total_pontos = min(10000, total_pontos) # Limite máximo é 10k
            resumo.append({
                "Gestor": g,
                "Pontuação Final": total_pontos,
                "Bônus Pago": calcular_faixa_bonus(total_pontos)
            })
        st.table(pd.DataFrame(resumo))
        st.write("### Últimos Lançamentos")
        st.dataframe(df.tail(10))
    else:
        st.info("Nenhum dado registrado ainda.")

with st.sidebar:
    st.header("Admin")
    novo_g = st.text_input("Cadastrar Novo Gestor")
    if st.button("Salvar"):
        ws_gestores.append_row([novo_g])
        st.rerun()
