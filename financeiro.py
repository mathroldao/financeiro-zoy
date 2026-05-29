import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime

DB_NAME = "financeiro_zoy.db"
IMPOSTO_PERCENTUAL = 0.175

st.set_page_config(
    page_title="Financeiro Zoy",
    page_icon="💰",
    layout="wide"
)

def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def conectar():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nfs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            campanha TEXT,
            numero_nf TEXT,
            data_emissao TEXT,
            data_recebimento TEXT,
            valor_faturado REAL,
            cache_influ REAL,
            comissao_zoy REAL,
            imposto REAL,
            liquido_zoy REAL,
            status TEXT,
            observacao TEXT
        )
    """)
    conn.commit()
    conn.close()

def carregar_nfs():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM nfs ORDER BY data_recebimento ASC", conn)
    conn.close()

    if not df.empty:
        df["data_emissao"] = pd.to_datetime(df["data_emissao"]).dt.date
        df["data_recebimento"] = pd.to_datetime(df["data_recebimento"]).dt.date

    return df

def salvar_nf(cliente, campanha, numero_nf, data_emissao, data_recebimento,
              valor_faturado, cache_influ, comissao_zoy, imposto, liquido_zoy,
              status, observacao):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO nfs (
            cliente, campanha, numero_nf, data_emissao, data_recebimento,
            valor_faturado, cache_influ, comissao_zoy, imposto, liquido_zoy,
            status, observacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cliente, campanha, numero_nf, str(data_emissao), str(data_recebimento),
        valor_faturado, cache_influ, comissao_zoy, imposto, liquido_zoy,
        status, observacao
    ))
    conn.commit()
    conn.close()

def atualizar_nf(id_nf, cliente, campanha, numero_nf, data_emissao, data_recebimento,
                 valor_faturado, cache_influ, comissao_zoy, imposto, liquido_zoy,
                 status, observacao):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE nfs SET
            cliente = ?,
            campanha = ?,
            numero_nf = ?,
            data_emissao = ?,
            data_recebimento = ?,
            valor_faturado = ?,
            cache_influ = ?,
            comissao_zoy = ?,
            imposto = ?,
            liquido_zoy = ?,
            status = ?,
            observacao = ?
        WHERE id = ?
    """, (
        cliente, campanha, numero_nf, str(data_emissao), str(data_recebimento),
        valor_faturado, cache_influ, comissao_zoy, imposto, liquido_zoy,
        status, observacao, id_nf
    ))
    conn.commit()
    conn.close()

def excluir_nf(id_nf):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM nfs WHERE id = ?", (id_nf,))
    conn.commit()
    conn.close()

def status_real(row):
    if row["status"] == "Recebido":
        return "Recebido"
    if row["data_recebimento"] < date.today():
        return "Atrasado"
    return "Pendente"

criar_tabela()
df = carregar_nfs()

st.title("Financeiro Zoy")
st.caption("Controle de faturamento, comissão e previsão de recebimentos")

aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "Dashboard",
    "Cadastrar NF",
    "NFs",
    "Previsão",
    "Clientes"
])

if not df.empty:
    df["status_real"] = df.apply(status_real, axis=1)

with aba1:
    st.header("Dashboard")

    if df.empty:
        total_faturado = comissao_total = imposto_total = liquido_total = 0
        recebido = a_receber = atrasado = 0
    else:
        total_faturado = df["valor_faturado"].sum()
        comissao_total = df["comissao_zoy"].sum()
        imposto_total = df["imposto"].sum()
        liquido_total = df["liquido_zoy"].sum()

        recebido = df[df["status_real"] == "Recebido"]["valor_faturado"].sum()
        a_receber = df[df["status_real"] == "Pendente"]["valor_faturado"].sum()
        atrasado = df[df["status_real"] == "Atrasado"]["valor_faturado"].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Faturado", moeda(total_faturado))
    col2.metric("Comissão Zoy", moeda(comissao_total))
    col3.metric("Imposto", moeda(imposto_total))
    col4.metric("Líquido Zoy", moeda(liquido_total))

    st.divider()

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Recebido Cliente", moeda(recebido))
    col6.metric("A Receber", moeda(a_receber))
    col7.metric("Em Atraso", moeda(atrasado))
    col8.metric("Qtd. NFs", len(df))

    st.divider()

    st.subheader("Previsão dos próximos recebimentos")

    if df.empty:
        st.info("Nenhuma NF cadastrada ainda.")
    else:
        previsao = df[df["status_real"] != "Recebido"].copy()
        previsao["Mês"] = pd.to_datetime(previsao["data_recebimento"]).dt.strftime("%m/%Y")

        resumo = previsao.groupby("Mês", as_index=False)["valor_faturado"].sum()
        resumo = resumo.rename(columns={"valor_faturado": "Total Previsto"})

        if resumo.empty:
            st.success("Todas as NFs cadastradas já foram recebidas.")
        else:
            st.bar_chart(resumo.set_index("Mês"))

with aba2:
    st.header("Cadastrar NF")

    with st.form("form_cadastro_nf"):
        col1, col2 = st.columns(2)

        with col1:
            cliente = st.text_input("Cliente")
            campanha = st.text_input("Campanha")
            numero_nf = st.text_input("Número da NF")
            data_emissao = st.date_input("Data de Emissão")

        with col2:
            data_recebimento = st.date_input("Data Prevista de Recebimento")
            valor_faturado = st.number_input("Valor Total Faturado", min_value=0.0, step=100.0)
            cache_influ = st.number_input("Cachê Influenciador", min_value=0.0, step=100.0)
            comissao_zoy = st.number_input("Comissão Zoy", min_value=0.0, step=100.0)

        imposto = comissao_zoy * IMPOSTO_PERCENTUAL
        liquido_zoy = comissao_zoy - imposto

        col3, col4 = st.columns(2)
        col3.info(f"Imposto 17,5%: {moeda(imposto)}")
        col4.success(f"Líquido Zoy: {moeda(liquido_zoy)}")

        status = st.selectbox("Status", ["Pendente", "Recebido"])
        observacao = st.text_area("Observação")

        salvar = st.form_submit_button("Salvar NF")

        if salvar:
            salvar_nf(
                cliente, campanha, numero_nf, data_emissao, data_recebimento,
                valor_faturado, cache_influ, comissao_zoy, imposto, liquido_zoy,
                status, observacao
            )
            st.success("NF cadastrada com sucesso.")
            st.rerun()

with aba3:
    st.header("NFs Cadastradas")

    if df.empty:
        st.info("Nenhuma NF cadastrada ainda.")
    else:
        col1, col2, col3 = st.columns(3)

        clientes = ["Todos"] + sorted(df["cliente"].dropna().unique().tolist())
        status_opcoes = ["Todos", "Pendente", "Recebido", "Atrasado"]

        with col1:
            filtro_cliente = st.selectbox("Filtrar por cliente", clientes)

        with col2:
            filtro_status = st.selectbox("Filtrar por status", status_opcoes)

        with col3:
            anos = ["Todos"] + sorted(pd.to_datetime(df["data_recebimento"]).dt.year.unique().tolist())
            filtro_ano = st.selectbox("Filtrar por ano", anos)

        df_filtrado = df.copy()

        if filtro_cliente != "Todos":
            df_filtrado = df_filtrado[df_filtrado["cliente"] == filtro_cliente]

        if filtro_status != "Todos":
            df_filtrado = df_filtrado[df_filtrado["status_real"] == filtro_status]

        if filtro_ano != "Todos":
            df_filtrado = df_filtrado[
                pd.to_datetime(df_filtrado["data_recebimento"]).dt.year == filtro_ano
            ]

        tabela = df_filtrado[[
            "id",
            "cliente",
            "campanha",
            "numero_nf",
            "data_emissao",
            "data_recebimento",
            "valor_faturado",
            "cache_influ",
            "comissao_zoy",
            "imposto",
            "liquido_zoy",
            "status_real",
            "observacao"
        ]].copy()

        tabela = tabela.rename(columns={
            "id": "ID",
            "cliente": "Cliente",
            "campanha": "Campanha",
            "numero_nf": "NF",
            "data_emissao": "Data Emissão",
            "data_recebimento": "Previsão Recebimento",
            "valor_faturado": "Valor Faturado",
            "cache_influ": "Cachê Influ",
            "comissao_zoy": "Comissão Zoy",
            "imposto": "Imposto",
            "liquido_zoy": "Líquido Zoy",
            "status_real": "Status",
            "observacao": "Observação"
        })

        st.dataframe(tabela, use_container_width=True)

        st.divider()
        st.subheader("Editar ou excluir NF")

        ids = df_filtrado["id"].tolist()

        if ids:
            id_escolhido = st.selectbox("Selecione o ID da NF", ids)

            nf_edit = df[df["id"] == id_escolhido].iloc[0]

            with st.form("form_editar_nf"):
                col1, col2 = st.columns(2)

                with col1:
                    cliente_edit = st.text_input("Cliente", value=nf_edit["cliente"])
                    campanha_edit = st.text_input("Campanha", value=nf_edit["campanha"])
                    numero_nf_edit = st.text_input("Número da NF", value=nf_edit["numero_nf"])
                    data_emissao_edit = st.date_input("Data de Emissão", value=nf_edit["data_emissao"])

                with col2:
                    data_recebimento_edit = st.date_input(
                        "Data Prevista de Recebimento",
                        value=nf_edit["data_recebimento"]
                    )
                    valor_faturado_edit = st.number_input(
                        "Valor Total Faturado",
                        min_value=0.0,
                        step=100.0,
                        value=float(nf_edit["valor_faturado"])
                    )
                    cache_influ_edit = st.number_input(
                        "Cachê Influenciador",
                        min_value=0.0,
                        step=100.0,
                        value=float(nf_edit["cache_influ"])
                    )
                    comissao_zoy_edit = st.number_input(
                        "Comissão Zoy",
                        min_value=0.0,
                        step=100.0,
                        value=float(nf_edit["comissao_zoy"])
                    )

                imposto_edit = comissao_zoy_edit * IMPOSTO_PERCENTUAL
                liquido_zoy_edit = comissao_zoy_edit - imposto_edit

                col3, col4 = st.columns(2)
                col3.info(f"Imposto 17,5%: {moeda(imposto_edit)}")
                col4.success(f"Líquido Zoy: {moeda(liquido_zoy_edit)}")

                status_edit = st.selectbox(
                    "Status",
                    ["Pendente", "Recebido"],
                    index=["Pendente", "Recebido"].index(nf_edit["status"])
                )

                observacao_edit = st.text_area(
                    "Observação",
                    value=nf_edit["observacao"] if nf_edit["observacao"] else ""
                )

                col_salvar, col_excluir = st.columns(2)

                salvar_edicao = col_salvar.form_submit_button("Salvar alterações")
                excluir = col_excluir.form_submit_button("Excluir NF")

                if salvar_edicao:
                    atualizar_nf(
                        id_escolhido,
                        cliente_edit,
                        campanha_edit,
                        numero_nf_edit,
                        data_emissao_edit,
                        data_recebimento_edit,
                        valor_faturado_edit,
                        cache_influ_edit,
                        comissao_zoy_edit,
                        imposto_edit,
                        liquido_zoy_edit,
                        status_edit,
                        observacao_edit
                    )
                    st.success("NF atualizada com sucesso.")
                    st.rerun()

                if excluir:
                    excluir_nf(id_escolhido)
                    st.success("NF excluída com sucesso.")
                    st.rerun()

with aba4:
    st.header("Previsão Mensal")

    if df.empty:
        st.info("Nenhuma NF cadastrada ainda.")
    else:
        previsao = df.copy()
        previsao["Mês"] = pd.to_datetime(previsao["data_recebimento"]).dt.strftime("%m/%Y")

        resumo = previsao.groupby("Mês", as_index=False).agg({
            "valor_faturado": "sum",
            "comissao_zoy": "sum",
            "imposto": "sum",
            "liquido_zoy": "sum"
        })

        resumo = resumo.rename(columns={
            "valor_faturado": "Total Faturado Previsto",
            "comissao_zoy": "Comissão Zoy",
            "imposto": "Imposto",
            "liquido_zoy": "Líquido Zoy"
        })

        st.dataframe(resumo, use_container_width=True)
        st.bar_chart(resumo.set_index("Mês")["Total Faturado Previsto"])

with aba5:
    st.header("Clientes")

    if df.empty:
        st.info("Nenhuma NF cadastrada ainda.")
    else:
        clientes_resumo = df.groupby("cliente", as_index=False).agg({
            "valor_faturado": "sum",
            "comissao_zoy": "sum",
            "liquido_zoy": "sum"
        })

        clientes_resumo = clientes_resumo.sort_values("valor_faturado", ascending=False)

        clientes_resumo = clientes_resumo.rename(columns={
            "cliente": "Cliente",
            "valor_faturado": "Total Faturado",
            "comissao_zoy": "Comissão Zoy",
            "liquido_zoy": "Líquido Zoy"
        })

        st.dataframe(clientes_resumo, use_container_width=True)
        st.bar_chart(clientes_resumo.set_index("Cliente")["Total Faturado"])
