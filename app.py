import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 1. Configuração da página
st.set_page_config(page_title="Gestão de Bônus Marcenaria", layout="wide")

# Esconder menus para privacidade total
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

# 2. Sistema de Login
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.title("🔐 Acesso Restrito - Marcenaria")
    senha = st.text_input("Senha de Acesso", type="password")
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

# 4. Funções de Cálculo de Bônus (Sua Matriz de Faixas)
def calcular_faixa_bonus(pontos):
    if pontos >= 9500: return "100%"
    elif pontos >= 9000: return "90%"
    elif pontos >= 8500: return "80%"
    elif pontos >= 8000: return "70%"
    elif pontos >= 7500: return "60%"
    else: return "0% (Sem Bônus)"

# 5. MATRIZ TÉCNICA COMPLETA (Sem resumos)
MATRIZ_COMPLETA = [
    ["1️⃣ Gestão Operacional", "Pedido entregue fora do prazo sem justificativa", -200],
    ["1️⃣ Gestão Operacional", "Retrabalho causado por erro de gestão", -300],
    ["1️⃣ Gestão Operacional", "Falta de material por falha de planejamento", -250],
    ["1️⃣ Gestão Operacional", "Atraso em cronograma interno", -100],
    ["2️⃣ Gestão de Pessoas", "Conflito de equipe não resolvido", -200],
    ["2️⃣ Gestão de Pessoas", "Alta rotatividade no setor (acima da meta)", -300],
    ["2️⃣ Gestão de Pessoas", "Falta injustificada de colaborador não gerenciada", -100],
    ["2️⃣ Gestão de Pessoas", "Reclamação formal de colaborador confirmada", -200],
    ["3️⃣ Processos e Organização", "Processo não seguido", -150],
    ["3️⃣ Processos e Organização", "Falta de registro ou documentação", -100],
    ["3️⃣ Processos e Organização", "Informação repassada errada entre setores", -150],
    ["3️⃣ Processos e Organização", "Não participação em reuniões obrigatórias", -100],
    ["4️⃣ Resultado do Setor", "Meta de produtividade não atingida", -400],
    ["4️⃣ Resultado do Setor", "Desperdício acima do limite", -250],
    ["4️⃣ Resultado do Setor", "Falha de qualidade detectada pelo cliente", -500],
    ["🚀 Recuperação / Extra", "Redução de desperdício", 200],
    ["🚀 Recuperação / Extra", "Melhoria de processo", 300],
    ["🚀 Recuperação / Extra", "Meta superada", 400]
]

# Verificar se a aba PARAMETROS precisa ser alimentada (força se houver menos de 10 itens)
dados_params = ws_parametros.get_all_records()
if len(dados_params) < 10:
    ws_parametros.clear()
    ws_parametros.append_row(["CATEGORIA", "SITUACAO", "PONTOS"])
    ws_parametros.append_rows(MATRIZ_COMPLETA)
    dados_params = ws_parametros.get_all_records()

df_params = pd.DataFrame(dados_params)

# --- INTERFACE ---
st.title("🛠️ Sistema de Performance Marcenaria")

tab1, tab2, tab3 = st.tabs(["📝 Lançar Ocorrência", "📊 Dashboard de Bônus", "📜 Matriz de Transparência"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        gestores = [r[0] for r in ws_gestores.get_all_values() if r]
        g_sel = st.selectbox("Selecione o Gestor", gestores if gestores else ["Nenhum gestor cadastrado"])
    
    with col2:
        categorias = df_params['CATEGORIA'].unique()
        cat_sel = st.selectbox("Selecione a Categoria", categorias)
        
        situacoes_filtradas = df_params[df_params['CATEGORIA'] == cat_sel]
        acao_sel = st.selectbox("Selecione a Situação Específica", situacoes_filtradas['SITUACAO'].tolist())
    
    # Busca o ponto exato da situação escolhida
    try:
        pontos_acao = int(df_params[df_params['SITUACAO'] == acao_sel]['PONTOS'].values[0])
        tipo = "🔴 Penalidade" if pontos_acao < 0 else "🟢 Recuperação"
        st.info(f"**Impacto Financeiro:** {pontos_acao} pontos | **Tipo:** {tipo}")
    except:
        st.warning("Selecione uma situação para ver o impacto.")
    
    obs = st.text_area("Descreva o motivo detalhado (Justificativa)")
    
    if st.button("Gravar Registro na Planilha", type="primary"):
        if g_sel != "Nenhum gestor cadastrado" and obs:
            data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
            ws_historico.append_row([data_hora, g_sel, cat_sel, acao_sel, pontos_acao, tipo, obs])
            st.success("✅ Registro realizado com sucesso!")
        else:
            st.error("Por favor, selecione um gestor e preencha a justificativa.")

with tab2:
    try:
        hist_total = ws_historico.get_all_records()
        if hist_total:
            df_h = pd.DataFrame(hist_total)
            
            # --- ÁREA DE RESUMO GERAL ---
            st.subheader("🏆 Resumo de Pontuação")
            resumo_final = []
            for g in gestores:
                soma_pontos = df_h[df_h['GESTOR'] == g]['PONTOS'].astype(int).sum()
                pontuacao_final = 10000 + soma_pontos
                pontuacao_final = max(0, min(10000, pontuacao_final))
                
                resumo_final.append({
                    "Gestor": g,
                    "Pontuação Atual": pontuacao_final,
                    "Faixa de Bônus": calcular_faixa_bonus(pontuacao_final)
                })
            
            st.table(pd.DataFrame(resumo_final))
            
            st.markdown("---")
            
            # --- FILTRO DE HISTÓRICO ---
            st.subheader("🔍 Filtrar Histórico Detalhado")
            gestor_filtro = st.selectbox("Filtrar por Gestor para ver detalhes:", ["Todos"] + gestores)
            
            if gestor_filtro == "Todos":
                df_filtrado = df_h
            else:
                df_filtrado = df_h[df_h['GESTOR'] == gestor_filtro]
            
            st.write(f"Exibindo {len(df_filtrado)} registros:")
            st.dataframe(df_filtrado.sort_index(ascending=False), use_container_width=True)
            
        else:
            st.info("Nenhum registro de pontuação foi encontrado.")
    except Exception as e:
        st.error(f"Erro ao processar dados. Erro: {e}")

with tab3:
    st.subheader("Parâmetros de Pontuação (Transparência Total)")
    st.write("Estes são os critérios acordados para a bonificação anual da Marcenaria.")
    st.dataframe(df_params, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("➕ Adicionar Novo Critério ou Situação")
    with st.form("form_novos_params"):
        n_cat = st.selectbox("Categoria do Novo Critério", ["1️⃣ Gestão Operacional", "2️⃣ Gestão de Pessoas", "3️⃣ Processos e Organização", "4️⃣ Resultado do Setor", "🚀 Recuperação / Extra"])
        n_sit = st.text_input("Descrição da Situação")
        n_pts = st.number_input("Valor da Pontuação (Use sinal de - para penalidades)", step=50)
        if st.form_submit_button("Salvar Novo Parâmetro"):
            if n_sit:
                ws_parametros.append_row([n_cat, n_sit, n_pts])
                st.success("Novo parâmetro salvo! Reinicie o app para atualizar a lista.")
            else:
                st.error("A descrição não pode estar vazia.")

with st.sidebar:
    st.header("Gestão de Acesso")
    novo_gestor_nome = st.text_input("Cadastrar Nome do Gestor")
    if st.button("Salvar Gestor"):
        if novo_gestor_nome:
            ws_gestores.append_row([novo_gestor_nome])
            st.rerun()
