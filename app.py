import streamlit as st
import pandas as pd
from gspread_streamlit import gspread_connect
from datetime import datetime

# Configuração da página (deve ser o primeiro comando Streamlit)
st.set_page_config(page_title="Gestão de Bônus - Marcenaria", layout="wide")

# Esconder menus do Streamlit para privacidade total
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE LOGIN ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔐 Acesso Restrito")
        senha_digitada = st.text_input("Digite a senha da Marcenaria", type="password")
        if st.button("Entrar"):
            if senha_digitada == st.secrets["general"]["password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
        return False
    return True

if check_password():
    # --- CONEXÃO COM GOOGLE SHEETS ---
    # Usando o segredo que configuramos
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    gc = gspread_connect(st.secrets["gspread"])
    sh = gc.open_by_key(st.secrets["general"]["spreadsheet_id"])

    # Selecionar ou Criar abas se não existirem
    def get_sheet(name):
        try:
            return sh.worksheet(name)
        except:
            return sh.add_worksheet(title=name, rows="100", cols="20")

    ws_gestores = get_sheet("GESTORES")
    ws_motivos = get_sheet("MOTIVOS")
    ws_historico = get_sheet("HISTORICO")

    st.title("🛠️ Sistema de Controle de Bônus")

    # --- ABA DE CADASTROS (Sidebar) ---
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Cadastro de Gestores
        novo_g = st.text_input("Novo Gestor")
        if st.button("Cadastrar Gestor"):
            ws_gestores.append_row([novo_g])
            st.success("Gestor salvo!")

        st.markdown("---")
        
        # Cadastro de Motivos
        novo_m = st.text_input("Novo Motivo")
        pontos_m = st.number_input("Pontos Negativos", step=100)
        if st.button("Cadastrar Motivo"):
            ws_motivos.append_row([novo_m, pontos_m])
            st.success("Motivo salvo!")

    # --- BUSCA DE DADOS ---
    lista_gestores = [item for sublist in ws_gestores.get_all_values() for item in sublist]
    lista_motivos_raw = ws_motivos.get_all_values()
    dict_motivos = {row[0]: int(row[1]) for row in lista_motivos_raw if len(row) > 1}

    # --- LANÇAMENTO ---
    st.subheader("📝 Registrar Perda de Pontos")
    c1, c2 = st.columns(2)
    with c1:
        g_sel = st.selectbox("Selecione o Gestor", lista_gestores if lista_gestores else ["Nenhum cadastrado"])
    with c2:
        m_sel = st.selectbox("Selecione o Motivo", list(dict_motivos.keys()) if dict_motivos else ["Nenhum cadastrado"])
    
    obs = st.text_area("Observação detalhada")
    
    if st.button("Salvar na Planilha", type="primary"):
        if g_sel and m_sel in dict_motivos:
            data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
            pontos = dict_motivos[m_sel]
            ws_historico.append_row([data_hoje, g_sel, m_sel, pontos, obs])
            st.warning(f"Dedução de {pontos} pontos registrada para {g_sel}!")
        else:
            st.error("Cadastre gestores e motivos primeiro!")

    # --- DASHBOARD ---
    st.markdown("---")
    st.subheader("📊 Saldo de Bônus (Final de Ano)")
    
    dados_hist = ws_historico.get_all_records()
    if dados_hist:
        df = pd.DataFrame(dados_hist)
        
        resumo = []
        for g in lista_gestores:
            perda = df[df['GESTOR'] == g]['PONTOS_PERDIDOS'].astype(int).sum() if 'GESTOR' in df.columns else 0
            saldo = 10000 - perda
            perc = (saldo / 10000) * 100
            resumo.append({
                "Gestor": g,
                "Saldo Atual": saldo,
                "Bônus %": f"{max(0, perc):.1f}%"
            })
        
        st.table(pd.DataFrame(resumo))
    else:
        st.info("Nenhum registro no histórico. Todos os gestores possuem 100%.")
