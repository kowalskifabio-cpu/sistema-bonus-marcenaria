import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 1. Configuração da página
st.set_page_config(page_title="Bônus Marcenaria", layout="wide")

# Esconder menus para privacidade
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

# 2. Sistema de Login
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.title("🔐 Acesso Restrito - Marcenaria")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if senha == st.secrets["general"]["password"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
        return False
    return True

if check_password():
    # 3. Conexão Segura com Google Sheets
    @st.cache_resource
    def conectar_planilha():
        # Transforma os segredos do Streamlit em credenciais do Google
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
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["general"]["spreadsheet_id"])

    try:
        sh = conectar_planilha()
        
        # Funções para pegar as abas
        def get_worksheet(name):
            try:
                return sh.worksheet(name)
            except:
                # Se a aba não existir, ele cria com cabeçalhos
                new_ws = sh.add_worksheet(title=name, rows="1000", cols="10")
                if name == "HISTORICO":
                    new_ws.append_row(["DATA", "GESTOR", "MOTIVO", "PONTOS_PERDIDOS", "OBSERVACAO"])
                return new_ws

        ws_gestores = get_worksheet("GESTORES")
        ws_motivos = get_worksheet("MOTIVOS")
        ws_historico = get_worksheet("HISTORICO")

        st.title("🛠️ Controle de Pontuação de Gestores")

        # --- SIDEBAR: CADASTROS ---
        with st.sidebar:
            st.header("⚙️ Configurações")
            novo_g = st.text_input("Nome do Gestor")
            if st.button("Cadastrar Gestor") and novo_g:
                ws_gestores.append_row([novo_g])
                st.success(f"{novo_g} cadastrado!")
            
            st.markdown("---")
            novo_m = st.text_input("Novo Motivo")
            pontos_m = st.number_input("Pontos a perder", step=100)
            if st.button("Cadastrar Motivo") and novo_m:
                ws_motivos.append_row([novo_m, pontos_m])
                st.success("Motivo salvo!")

        # --- LANÇAMENTO ---
        # Carrega dados atuais
        gestores = [r[0] for r in ws_gestores.get_all_values() if r]
        motivos_data = ws_motivos.get_all_values()
        motivos_dict = {r[0]: int(r[1]) for r in motivos_data if len(r) > 1}

        st.subheader("📝 Registrar Nova Ocorrência")
        c1, c2 = st.columns(2)
        with c1:
            g_sel = st.selectbox("Quem perdeu pontos?", gestores if gestores else ["Nenhum cadastrado"])
        with c2:
            m_sel = st.selectbox("Qual o motivo?", list(motivos_dict.keys()) if motivos_dict else ["Nenhum cadastrado"])
        
        obs = st.text_area("Detalhes do ocorrido")
        
        if st.button("Salvar Registro", type="primary"):
            if g_sel != "Nenhum cadastrado" and m_sel != "Nenhum cadastrado":
                data_agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                ws_historico.append_row([data_agora, g_sel, m_sel, motivos_dict[m_sel], obs])
                st.balloons()
                st.success("Registrado com sucesso!")
            else:
                st.error("Erro: Cadastre gestores e motivos primeiro.")

        # --- DASHBOARD ---
        st.markdown("---")
        st.subheader("📊 Ranking de Bônus")
        
        todos_registros = ws_historico.get_all_records()
        df = pd.DataFrame(todos_registros)
        
        ranking = []
        for g in gestores:
            perda = 0
            if not df.empty and 'GESTOR' in df.columns:
                perda = df[df['GESTOR'] == g]['PONTOS_PERDIDOS'].sum()
            
            saldo = 10000 - perda
            perc = (saldo / 10000) * 100
            ranking.append({"Gestor": g, "Saldo": saldo, "Bônus %": f"{max(0, perc):.1f}%"})
        
        st.table(pd.DataFrame(ranking))

    except Exception as e:
        st.error(f"Erro de conexão: Verifique se compartilhou a planilha com o e-mail do JSON. {e}")
