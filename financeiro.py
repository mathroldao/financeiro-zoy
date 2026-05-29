import streamlit as st

st.set_page_config(
    page_title="Financeiro Zoy",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Financeiro Zoy")
st.markdown("Controle de faturamento e previsão de recebimentos")

aba1, aba2, aba3, aba4 = st.tabs([
    "Dashboard",
    "Cadastrar NF",
    "NFs",
    "Previsão"
])

with aba1:
    st.header("Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Faturado", "R$ 0,00")

    with col2:
        st.metric("Comissão Zoy", "R$ 0,00")

    with col3:
        st.metric("Imposto", "R$ 0,00")

    with col4:
        st.metric("Líquido Zoy", "R$ 0,00")

    st.divider()

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.metric("Recebido Cliente", "R$ 0,00")

    with col6:
        st.metric("Pago Influ", "R$ 0,00")

    with col7:
        st.metric("Reserva", "R$ 0,00")

    with col8:
        st.metric("Em Atraso", "R$ 0,00")

with aba2:
    st.header("Cadastrar NF")

    cliente = st.text_input("Cliente")
    campanha = st.text_input("Campanha")
    numero_nf = st.text_input("Número da NF")

    col1, col2 = st.columns(2)

    with col1:
        data_emissao = st.date_input("Data de Emissão")

    with col2:
        data_recebimento = st.date_input("Data Prevista de Recebimento")

    valor_faturado = st.number_input(
        "Valor Faturado",
        min_value=0.0,
        step=100.0
    )

    comissao_zoy = st.number_input(
        "Comissão Zoy",
        min_value=0.0,
        step=100.0
    )

    imposto = comissao_zoy * 0.175
    liquido = comissao_zoy - imposto

    st.info(f"Imposto (17,5%): R$ {imposto:,.2f}")
    st.success(f"Líquido Zoy: R$ {liquido:,.2f}")

    if st.button("Salvar NF"):
        st.success("NF cadastrada com sucesso!")

with aba3:
    st.header("NFs Cadastradas")
    st.info("Tabela será conectada ao banco de dados na próxima etapa.")

with aba4:
    st.header("Previsão de Recebimentos")
    st.info("Gráfico de previsão mensal será criado na próxima etapa.")
