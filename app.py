import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Sistema de Bônus - Marcenaria", layout="wide")

st.title("🛠️ Gestão de Pontuação e Bônus")
st.markdown("---")

# Simulando a base de dados (No futuro, conectamos ao Google Sheets)
# Aqui o sistema "aprende" quem são os gestores e quais os motivos
if 'gestores' not in st.session_state:
    st.session_state.gestores = ["João Silva", "Maria Oliveira", "Carlos Souza"]

if 'motivos' not in st.session_state:
    st.session_state.motivos = {
        "Atraso na Entrega": 500,
        "Erro de Medição": 1000,
        "Desperdício de Material": 300,
        "Falta de EPI": 200
    }

if 'historico' not in st.session_state:
    st.session_state.historico = []

# --- MENU LATERAL PARA CADASTROS ---
with st.sidebar:
    st.header("⚙️ Configurações do Sistema")
    
    # Cadastro de Novo Gestor
    new_gestor = st.text_input("Cadastrar Novo Gestor")
    if st.button("Adicionar Gestor"):
        if new_gestor and new_gestor not in st.session_state.gestores:
            st.session_state.gestores.append(new_gestor)
            st.success(f"{new_gestor} cadastrado!")

    st.markdown("---")
    
    # Cadastro de Novo Motivo
    new_motivo = st.text_input("Descrição do Novo Motivo")
    new_pontos = st.number_input("Pontuação Negativa", min_value=0, step=50)
    if st.button("Adicionar Motivo"):
        if new_motivo:
            st.session_state.motivos[new_motivo] = new_pontos
            st.success("Motivo adicionado!")

# --- ÁREA PRINCIPAL: LANÇAMENTO DE OCORRÊNCIAS ---
st.subheader("📝 Registrar Situação Negativa")
col1, col2, col3 = st.columns(3)

with col1:
    gestor_selecionado = st.selectbox("Selecione o Gestor", st.session_state.gestores)
with col2:
    motivo_selecionado = st.selectbox("Motivo da Perda", list(st.session_state.motivos.keys()))
with col3:
    data_evento = st.date_input("Data do Ocorrido", datetime.now())

obs = st.text_area("Observações Adicionais")

if st.button("Confirmar Perda de Pontos", type="primary"):
    pontos_perder = st.session_state.motivos[motivo_selecionado]
    novo_registro = {
        "Data": data_evento,
        "Gestor": gestor_selecionado,
        "Motivo": motivo_selecionado,
        "Pontos Perdidos": pontos_perder,
        "Observação": obs
    }
    st.session_state.historico.append(novo_registro)
    st.warning(f"Dedução de {pontos_perder} pontos registrada para {gestor_selecionado}!")

# --- DASHBOARD DE RESULTADOS ---
st.markdown("---")
st.subheader("📊 Painel de Performance e Bônus")

if st.session_state.historico:
    df = pd.DataFrame(st.session_state.historico)
    
    # Cálculo por Gestor
    resumo = []
    for g in st.session_state.gestores:
        perda_total = df[df['Gestor'] == g]['Pontos Perdidos'].sum()
        saldo_atual = 10000 - perda_total
        percentual = (saldo_atual / 10000) * 100
        resumo.append({
            "Gestor": g,
            "Saldo Inicial": 10000,
            "Total Perdido": perda_total,
            "Saldo Atual": saldo_atual,
            "Bônus %": f"{max(0, percentual):.1f}%"
        })
    
    st.table(pd.DataFrame(resumo))
    
    st.write("### Histórico Detalhado")
    st.dataframe(df)
else:
    st.info("Nenhum registro de perda até o momento. Todos os gestores estão com 100%!")
