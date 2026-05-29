import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import date, timedelta

DB_NAME = "financeiro_zoy.db"
IMPOSTO_PERCENTUAL = 0.175

st.set_page_config(
    page_title="Financeiro Zoy",
    page_icon="💰",
    layout="wide"
)

# =========================
# ESTILO
# =========================

st.markdown("""
<style>
.metric-card {
    padding: 22px;
    border-radius: 18px;
    background: white;
    border: 1px solid #e8e8e8;
    box-shadow: 0 4px 18px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}
.metric-title {
    font-size: 15px;
    color: #4b5563;
    margin-bottom: 8px;
}
.metric-value {
    font-size: 30px;
    font-weight: 800;
    color: #111827;
}
.card-blue { border-left: 7px solid #2563eb; }
.card-green { border-left: 7px solid #16a34a; }
.card-orange { border-left: 7px solid #f97316; }
.card-purple { border-left: 7px solid #7c3aed; }
.card-yellow { border-left: 7px solid #eab308; }
.card-red { border-left: 7px solid #ef4444; }
</style>
""", unsafe_allow_html=True)

# =========================
# FUNÇÕES
# =========================

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
            influenciador TEXT,
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

    cursor.execute("PRAGMA table_info(nfs)")
    colunas = [col[1] for col in cursor.fetchall()]

    if "influenciador" not in colunas:
        cursor.execute("ALTER TABLE nfs ADD COLUMN influenciador TEXT")

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

def salvar_nf(cliente, campanha, influenciador, numero_nf, data_emissao, data_recebimento,
              valor_faturado, cache_influ, comissao_zoy, imposto, liquido_zoy,
              status, observacao):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO nfs (
            cliente, campanha, influenciador, numero_nf, data_emissao, data_recebimento,
            valor_faturado, cache_influ, comissao_zoy, imposto, liquido_zoy,
            status, observacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cliente, campanha, influenciador, numero_nf, str(data_emissao), str(data_recebimento),
        valor_faturado, cache_influ, comissao_zoy, imposto, liquido_zoy,
        status, observacao
    ))

    conn.commit()
    conn.close()

def atualizar_nf(id_nf, cliente, campanha, influenciador, numero_nf, data_emissao, data_recebimento,
                 valor_faturado, cache_influ, comissao_zoy, imposto, liquido_zoy,
                 status, observacao):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE nfs SET
            cliente = ?,
            campanha = ?,
            influenciador = ?,
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
        cliente, campanha, influenciador, numero_nf, str(data_emissao), str(data_recebimento),
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

def card(titulo, valor, cor):
    st.markdown(f"""
    <div class="metric-card {cor}">
        <div class="metric-title">{titulo}</div>
        <div class="metric-value">{valor}</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# INÍCIO
# =========================

criar_tabela()
df = carregar_nfs()

if not df.empty:
    df["status_real"] = df.apply(status_real, axis=1)

st.title("💰 Financeiro Zoy")
st.caption("Controle de faturamento, comissão e previsão de recebimentos")

aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "Dashboard",
    "Cadastrar NF",
    "NFs",
    "Previsão",
    "Clientes"
])

# =========================
# DASHBOARD
# =========================

with aba1:
    st.header("Dashboard")

    if df.empty:
        total_faturado = comissao_total = imposto_total = liquido_total = 0
        recebido = a_receber = atrasado = 0
        qtd_nfs = 0
    else:
        total_faturado = df["valor_faturado"].sum()
        comissao_total = df["comissao_zoy"].sum()
        imposto_total = df["imposto"].sum()
        liquido_total = df["liquido_zoy"].sum()
        recebido = df[df["status_real"] == "Recebido"]["valor_faturado"].sum()
        a_receber = df[df["status_real"] == "Pendente"]["valor_faturado"].sum()
        atrasado = df[df["status_real"] == "Atrasado"]["valor_faturado"].sum()
        qtd_nfs = len(df)

    col1, col2, col3, col4 = st.columns(4)
    with col1: card("Total Faturado", moeda(total_faturado), "card-blue")
    with col2: card("Comissão Zoy", moeda(comissao_total), "card-green")
    with col3: card("Imposto 17,5%", moeda(imposto_total), "card-orange")
    with col4: card("Líquido Zoy", moeda(liquido_total), "card-purple")

    col5, col6, col7, col8 = st.columns(4)
    with col5: card("Recebido Cliente", moeda(recebido), "card-green")
    with col6: card("A Receber", moeda(a_receber), "card-yellow")
    with col7: card("Em Atraso", moeda(atrasado), "card-red")
    with col8: card("Qtd. NFs", qtd_nfs, "card-blue")

    st.divider()

    st.subheader("Previsão dos próximos recebimentos")

    if df.empty:
        st.info("Nenhuma NF cadastrada ainda.")
    else:
        previsao = df[df["status_real"] != "Recebido"].copy()

        if previsao.empty:
            st.success("Todas as NFs cadastradas já foram recebidas.")
        else:
            previsao["Mês"] = pd.to_datetime(previsao["data_recebimento"]).dt.strftime("%b/%Y")

            resumo = (
                previsao
                .groupby("Mês", as_index=False)["valor_faturado"]
                .sum()
                .rename(columns={"valor_faturado": "Total Previsto"})
            )

            resumo["Valor Formatado"] = resumo["Total Previsto"].apply(moeda)

            fig = px.bar(
                resumo,
                x="Mês",
                y="Total Previsto",
                text="Valor Formatado"
            )

            fig.update_traces(textposition="outside")
            fig.update_layout(
                height=430,
                yaxis_title="Valor previsto",
                xaxis_title="Mês de recebimento",
                showlegend=False,
                margin=dict(l=20, r=20, t=30, b=20)
            )

            st.plotly_chart(fig, use_container_width=True)

            col30, col60, col90 = st.columns(3)

            hoje = date.today()
            prox_30 = previsao[
                (previsao["data_recebimento"] >= hoje) &
                (previsao["data_recebimento"] <= hoje + timedelta(days=30))
            ]["valor_faturado"].sum()

            prox_60 = previsao[
                (previsao["data_recebimento"] >= hoje) &
                (previsao["data_recebimento"] <= hoje + timedelta(days=60))
            ]["valor_faturado"].sum()

            prox_90 = previsao[
                (previsao["data_recebimento"] >= hoje) &
                (previsao["data_recebimento"] <= hoje + timedelta(days=90))
            ]["valor_faturado"].sum()

            with col30: card("Próximos 30 dias", moeda(prox_30), "card-green")
            with col60: card("Próximos 60 dias", moeda(prox_60), "card-yellow")
            with col90: card("Próximos 90 dias", moeda(prox_90), "card-purple")

            st.subheader("Próximos recebimentos")

            proximos = previsao.sort_values("data_recebimento").head(8)

            st.dataframe(
                proximos[[
                    "cliente",
                    "campanha",
                    "influenciador",
                    "data_recebimento",
                    "valor_faturado",
                    "status_real"
                ]].rename(columns={
                    "cliente": "Cliente",
                    "campanha": "Campanha",
                    "influenciador": "@ Influenciador",
                    "data_recebimento": "Previsão",
                    "valor_faturado": "Valor",
                    "status_real": "Status"
                }),
                use_container_width=True
            )

# =========================
# CADASTRAR NF
# =========================

with aba2:
    st.header("Cadastrar NF")

    with st.form("form_cadastro_nf"):
        col1, col2 = st.columns(2)

        with col1:
            cliente = st.text_input("Cliente")
            campanha = st.text_input("Campanha")
            influenciador = st.text_input("@ do Influenciador")
            numero_nf = st.text_input("Número da NF")

        with col2:
            data_emissao = st.date_input("Data de Emissão")
            data_recebimento = st.date_input("Data Prevista de Recebimento")
            valor_faturado = st.number_input("Valor Total Faturado", min_value=0.0, step=100.0)
            cache_influ = st.number_input("Cachê Influenciador", min_value=0.0, step=100.0)

        comissao_zoy = valor_faturado - cache_influ
        imposto = comissao_zoy * IMPOSTO_PERCENTUAL
        liquido_zoy = comissao_zoy - imposto

        col3, col4, col5 = st.columns(3)
        col3.info(f"Comissão Zoy: {moeda(comissao_zoy)}")
        col4.info(f"Imposto 17,5%: {moeda(imposto)}")
        col5.success(f"Líquido Zoy: {moeda(liquido_zoy)}")

        status = st.selectbox("Status", ["Pendente", "Recebido"])
        observacao = st.text_area("Observação")

        salvar = st.form_submit_button("Salvar NF")

        if salvar:
            salvar_nf(
                cliente, campanha, influenciador, numero_nf, data_emissao, data_recebimento,
                valor_faturado, cache_influ, comissao_zoy, imposto, liquido_zoy,
                status, observacao
            )
            st.success("NF cadastrada com sucesso.")
            st.rerun()

# =========================
# NFS
# =========================

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
            df_filtrado = df_filtrado[pd.to_datetime(df_filtrado["data_recebimento"]).dt.year == filtro_ano]

        tabela = df_filtrado[[
            "id", "cliente", "campanha", "influenciador", "numero_nf",
            "data_emissao", "data_recebimento", "valor_faturado",
            "cache_influ", "comissao_zoy", "imposto", "liquido_zoy",
            "status_real", "observacao"
        ]].rename(columns={
            "id": "ID",
            "cliente": "Cliente",
            "campanha": "Campanha",
            "influenciador": "@ Influenciador",
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
                    influenciador_edit = st.text_input(
                        "@ do Influenciador",
                        value=nf_edit["influenciador"] if pd.notna(nf_edit["influenciador"]) else ""
                    )
                    numero_nf_edit = st.text_input("Número da NF", value=nf_edit["numero_nf"])

                with col2:
                    data_emissao_edit = st.date_input("Data de Emissão", value=nf_edit["data_emissao"])
                    data_recebimento_edit = st.date_input("Data Prevista de Recebimento", value=nf_edit["data_recebimento"])
                    valor_faturado_edit = st.number_input("Valor Total Faturado", min_value=0.0, step=100.0, value=float(nf_edit["valor_faturado"]))
                    cache_influ_edit = st.number_input("Cachê Influenciador", min_value=0.0, step=100.0, value=float(nf_edit["cache_influ"]))

                comissao_zoy_edit = valor_faturado_edit - cache_influ_edit
                imposto_edit = comissao_zoy_edit * IMPOSTO_PERCENTUAL
                liquido_zoy_edit = comissao_zoy_edit - imposto_edit

                col3, col4, col5 = st.columns(3)
                col3.info(f"Comissão Zoy: {moeda(comissao_zoy_edit)}")
                col4.info(f"Imposto 17,5%: {moeda(imposto_edit)}")
                col5.success(f"Líquido Zoy: {moeda(liquido_zoy_edit)}")

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
                        id_escolhido, cliente_edit, campanha_edit, influenciador_edit,
                        numero_nf_edit, data_emissao_edit, data_recebimento_edit,
                        valor_faturado_edit, cache_influ_edit, comissao_zoy_edit,
                        imposto_edit, liquido_zoy_edit, status_edit, observacao_edit
                    )
                    st.success("NF atualizada com sucesso.")
                    st.rerun()

                if excluir:
                    excluir_nf(id_escolhido)
                    st.success("NF excluída com sucesso.")
                    st.rerun()

# =========================
# PREVISÃO
# =========================

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
        }).rename(columns={
            "valor_faturado": "Total Faturado Previsto",
            "comissao_zoy": "Comissão Zoy",
            "imposto": "Imposto",
            "liquido_zoy": "Líquido Zoy"
        })

        st.dataframe(resumo, use_container_width=True)

        fig = px.bar(
            resumo,
            x="Mês",
            y="Total Faturado Previsto",
            text=resumo["Total Faturado Previsto"].apply(moeda)
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(height=430, showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

# =========================
# CLIENTES
# =========================

with aba5:
    st.header("Clientes")

    if df.empty:
        st.info("Nenhuma NF cadastrada ainda.")
    else:
        clientes_resumo = df.groupby("cliente", as_index=False).agg({
            "valor_faturado": "sum",
            "comissao_zoy": "sum",
            "liquido_zoy": "sum"
        }).sort_values("valor_faturado", ascending=False)

        clientes_resumo = clientes_resumo.rename(columns={
            "cliente": "Cliente",
            "valor_faturado": "Total Faturado",
            "comissao_zoy": "Comissão Zoy",
            "liquido_zoy": "Líquido Zoy"
        })

        st.dataframe(clientes_resumo, use_container_width=True)

        fig_clientes = px.bar(
            clientes_resumo,
            x="Cliente",
            y="Total Faturado",
            text=clientes_resumo["Total Faturado"].apply(moeda)
        )
        fig_clientes.update_traces(textposition="outside")
        fig_clientes.update_layout(height=430, showlegend=False)

        st.plotly_chart(fig_clientes, use_container_width=True)
