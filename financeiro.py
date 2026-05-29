import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Financeiro Zoy",
    page_icon="💰",
    layout="wide"
)

# ==========================
# BANCO DE DADOS SIMPLES
# ==========================

if "nfs" not in st.session_state:
    st.session_state.nfs = pd.DataFrame(columns=[
        "Cliente",
        "Campanha",
        "NF",
        "Data Emissão",
        "Data Recebimento",
        "Valor Faturado",
        "Comissão Zoy",
        "Imposto",
        "Líquido Zoy",
        "Status"
    ])

df = st.session_state.nfs

# ==========================
# CÁLCULOS
# ==========================

total_faturado = df["Valor Faturado"].sum() if not df.empty else 0
total_comissao = df["Comissão Zoy"].sum() if not df.empty else 0
total_imposto = df["Imposto"].sum() if not df.empty else 0
total_liquido = df["Líquido Zoy"].sum() if not df.empty else 0

recebido_cliente = df[df["Status"] == "Recebido"]["Valor Faturado"].sum() if not df.empty else 0

a_receber = df[df["Status"] == "Pendente"]["Valor Faturado"].sum() if not df.empty else 0

# ==========================
# CABEÇALHO
# ==========================

st.title("💰 Financeiro Zoy")
st.caption("Controle de faturamento e previsão de recebimentos")

aba1, aba2, aba3, aba4 = st.tabs([
    "Dashboard",
    "Cadastrar NF",
    "NFs",
    "Previsão"
])

# ==========================
# DASHBOARD
# ==========================

with aba1:

    st.header("Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Faturado",
            f"R$ {total_faturado:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
        )

    with col2:
        st.metric(
            "Comissão Zoy",
            f"R$ {total_comissao:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
        )

    with col3:
        st.metric(
            "Imposto",
            f"R$ {total_imposto:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
        )

    with col4:
        st.metric(
            "Líquido Zoy",
            f"R$ {total_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
        )

    st.divider()

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.metric(
            "Recebido Cliente",
            f"R$ {recebido_cliente:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
        )

    with col6:
        st.metric(
            "A Receber",
            f"R$ {a_receber:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
        )

    with col7:
        st.metric(
            "Qtd NFs",
            len(df)
        )

    with col8:
        st.metric(
            "Imposto Médio",
            "17,5%"
        )

# ==========================
# CADASTRAR NF
# ==========================

with aba2:

    st.header("Cadastrar NF")

    cliente = st.text_input("Cliente")

    campanha = st.text_input("Campanha")

    nf = st.text_input("Número da NF")

    col1, col2 = st.columns(2)

    with col1:
        data_emissao = st.date_input(
            "Data Emissão"
        )

    with col2:
        data_recebimento = st.date_input(
            "Data Prevista Recebimento"
        )

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

    st.info(
        f"Imposto: R$ {imposto:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
    )

    st.success(
        f"Líquido Zoy: R$ {liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
    )

    status = st.selectbox(
        "Status",
        [
            "Pendente",
            "Recebido"
        ]
    )

    if st.button("Salvar NF"):

        nova_linha = pd.DataFrame([{
            "Cliente": cliente,
            "Campanha": campanha,
            "NF": nf,
            "Data Emissão": data_emissao,
            "Data Recebimento": data_recebimento,
            "Valor Faturado": valor_faturado,
            "Comissão Zoy": comissao_zoy,
            "Imposto": imposto,
            "Líquido Zoy": liquido,
            "Status": status
        }])

        st.session_state.nfs = pd.concat(
            [st.session_state.nfs, nova_linha],
            ignore_index=True
        )

        st.success("NF cadastrada com sucesso!")

# ==========================
# LISTA DE NFS
# ==========================

with aba3:

    st.header("NFs Cadastradas")

    if st.session_state.nfs.empty:
        st.info("Nenhuma NF cadastrada.")
    else:
        st.dataframe(
            st.session_state.nfs,
            use_container_width=True
        )

# ==========================
# PREVISÃO
# ==========================

with aba4:

    st.header("Previsão de Recebimentos")

    if st.session_state.nfs.empty:
        st.info("Nenhuma NF cadastrada.")
    else:

        previsao = st.session_state.nfs.copy()

        previsao["Mês"] = pd.to_datetime(
            previsao["Data Recebimento"]
        ).dt.strftime("%m/%Y")

        resumo = (
            previsao
            .groupby("Mês")["Valor Faturado"]
            .sum()
            .reset_index()
        )

        st.dataframe(
            resumo,
            use_container_width=True
        )

        st.bar_chart(
            resumo.set_index("Mês")
        )
