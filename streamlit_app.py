import os
import numpy as np
import pandas as pd
import streamlit as st

# -------------------------------------------------------------
# Configuração da página
# -------------------------------------------------------------
st.set_page_config(
    page_title="CanalCerto - Protótipo",
    layout="wide",
    page_icon="📊",
)

st.title("CanalCerto 📊")
st.subheader("Protótipo analítico dos canais de agendamento")

st.markdown(
    """
Este protótipo em **Streamlit** simula a visão analítica do CanalCerto,
permitindo analisar **volume**, **conversão**, **cancelamentos**, **retorno financeiro**
e **perfil dos pacientes por canal de agendamento**.
"""
)

# -------------------------------------------------------------
# 1. Carregar base de dados (arquivo local)
# -------------------------------------------------------------
DATA_PATH = os.path.join("data", "dataset_canalcerto.csv")
# Se o seu arquivo tiver outro nome, ajuste a linha acima, por exemplo:
# DATA_PATH = os.path.join("data", "dataset_canalcerto_10000_completo.csv")

st.sidebar.header("1. Carregar base de dados")
st.sidebar.success(f"Usando arquivo local:\n`{DATA_PATH}`")


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Garantir que a coluna de data esteja em datetime
    df["data_atendimento"] = pd.to_datetime(df["data_atendimento"])
    return df


try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(f"Arquivo não encontrado em `{DATA_PATH}`. Verifique o caminho e o nome do arquivo.")
    st.stop()

st.info(f"Base carregada com **{len(df):,}** atendimentos.".replace(",", "."))

# -------------------------------------------------------------
# Mapeamento fixo das colunas (dataset padronizado)
# -------------------------------------------------------------
col_id = "id_atendimento"
col_data = "data_atendimento"
col_mes = "mes_referencia"
col_paciente = "paciente_id"
col_sexo = "sexo_paciente"
col_idade = "idade_paciente"
col_canal = "canal_atendimento"
col_tipo = "tipo_atendimento"
col_especialidade = "especialidade"
col_status = "status_atendimento"
col_valor_bruto = "valor_bruto"
col_custo = "custo_operacional"
col_lucro = "lucro_liquido"
col_retorno_positivo = "retorno_positivo"

# -------------------------------------------------------------
# 2. Filtros na sidebar
# -------------------------------------------------------------
st.sidebar.header("2. Filtros")

# Período
min_date = df[col_data].min()
max_date = df[col_data].max()

periodo = st.sidebar.date_input(
    "Período de agendamento",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(periodo, tuple):
    data_inicio, data_fim = periodo
else:
    data_inicio, data_fim = min_date, max_date

# Canal
canais = sorted(df[col_canal].dropna().unique().tolist())
canais_sel = st.sidebar.multiselect(
    "Canais de agendamento",
    options=canais,
    default=canais,
)

# Status
status_opts = sorted(df[col_status].dropna().unique().tolist())
status_sel = st.sidebar.multiselect(
    "Status do atendimento",
    options=status_opts,
    default=status_opts,
)

# Sexo
sexos = sorted(df[col_sexo].dropna().unique().tolist())
sexo_sel = st.sidebar.multiselect(
    "Sexo do paciente",
    options=sexos,
    default=sexos,
)

# Faixa etária (slider apenas informativo)
idade_min = int(df[col_idade].min())
idade_max = int(df[col_idade].max())
faixa_idade = st.sidebar.slider(
    "Faixa de idade",
    min_value=idade_min,
    max_value=idade_max,
    value=(idade_min, idade_max),
)

# -------------------------------------------------------------
# Aplicando filtros
# -------------------------------------------------------------
mask = (
    (df[col_data].dt.date >= data_inicio)
    & (df[col_data].dt.date <= data_fim)
    & (df[col_canal].isin(canais_sel))
    & (df[col_status].isin(status_sel))
    & (df[col_sexo].isin(sexo_sel))
    & (df[col_idade].between(faixa_idade[0], faixa_idade[1]))
)

df_filt = df.loc[mask].copy()

st.markdown("### Visão geral dos atendimentos filtrados")
st.write(f"Registros após filtros: **{len(df_filt):,}**".replace(",", "."))

if df_filt.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
    st.stop()

# -------------------------------------------------------------
# 3. KPIs principais
# -------------------------------------------------------------
total_atend = len(df_filt)
realizados = (df_filt[col_status] == "Realizado").sum()
cancelados = (df_filt[col_status] == "Cancelado").sum()
nao_compareceu = (df_filt[col_status] == "Não compareceu").sum()

faturamento_total = df_filt[col_valor_bruto].sum()
lucro_total = df_filt[col_lucro].sum()

ticket_medio = df_filt.loc[df_filt[col_status] == "Realizado", col_valor_bruto].mean()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total de atendimentos", f"{total_atend:,}".replace(",", "."))
with col2:
    perc_real = realizados / total_atend * 100 if total_atend > 0 else 0
    st.metric("Taxa de realização", f"{perc_real:.1f}%")
with col3:
    perc_canc = cancelados / total_atend * 100 if total_atend > 0 else 0
    st.metric("Taxa de cancelamento", f"{perc_canc:.1f}%")
with col4:
    st.metric("Ticket médio (realizados)", f"R$ {ticket_medio:,.2f}" if not np.isnan(ticket_medio) else "R$ 0,00".replace(",", "."))

col5, col6 = st.columns(2)

with col5:
    st.metric("Faturamento total (bruto)", f"R$ {faturamento_total:,.2f}".replace(",", "."))
with col6:
    st.metric("Lucro total (estimado)", f"R$ {lucro_total:,.2f}".replace(",", "."))

st.markdown("---")

# -------------------------------------------------------------
# 4. Análises por canal
# -------------------------------------------------------------
st.markdown("## Desempenho por canal de agendamento")

grupo_canal = (
    df_filt
    .groupby(col_canal)
    .agg(
        atendimentos=(col_id, "count"),
        realizados=(col_status, lambda x: (x == "Realizado").sum()),
        cancelados=(col_status, lambda x: (x == "Cancelado").sum()),
        nao_compareceu=(col_status, lambda x: (x == "Não compareceu").sum()),
        faturamento=(col_valor_bruto, "sum"),
        lucro=(col_lucro, "sum"),
    )
)

grupo_canal["taxa_conversao"] = (
    grupo_canal["realizados"] / grupo_canal["atendimentos"] * 100
).round(1)

grupo_canal["taxa_cancelamento"] = (
    grupo_canal["cancelados"] / grupo_canal["atendimentos"] * 100
).round(1)

grupo_canal["ticket_medio"] = (
    grupo_canal["faturamento"] / grupo_canal["realizados"]
).replace([np.inf, -np.inf], np.nan).round(2)

# Ordenar por faturamento
grupo_canal = grupo_canal.sort_values("faturamento", ascending=False)

st.markdown("### Tabela resumo por canal")
st.dataframe(
    grupo_canal.style.format(
        {
            "faturamento": "R$ {:,.2f}".format,
            "lucro": "R$ {:,.2f}".format,
            "ticket_medio": "R$ {:,.2f}".format,
        }
    ),
    use_container_width=True,
)

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("#### Atendimentos por canal")
    st.bar_chart(grupo_canal["atendimentos"])

with col_g2:
    st.markdown("#### Faturamento por canal")
    st.bar_chart(grupo_canal["faturamento"])

col_g3, col_g4 = st.columns(2)

with col_g3:
    st.markdown("#### Taxa de conversão (%) por canal")
    st.bar_chart(grupo_canal["taxa_conversao"])

with col_g4:
    st.markdown("#### Taxa de cancelamento (%) por canal")
    st.bar_chart(grupo_canal["taxa_cancelamento"])

st.markdown("---")

# -------------------------------------------------------------
# 5. Perfil dos pacientes (idade, sexo e canais)
# -------------------------------------------------------------
st.markdown("## Perfil dos pacientes")

# Criar faixas etárias padrão
df_filt["faixa_idade"] = pd.cut(
    df_filt[col_idade],
    bins=[0, 17, 25, 35, 45, 60, 200],
    labels=["0-17", "18-25", "26-35", "36-45", "46-60", "60+"],
    right=True,
)

col_p1, col_p2 = st.columns(2)

with col_p1:
    st.markdown("#### Distribuição por faixa etária")
    idade_grp = df_filt["faixa_idade"].value_counts().sort_index()
    st.bar_chart(idade_grp)

with col_p2:
    st.markdown("#### Distribuição por sexo")
    sexo_grp = df_filt[col_sexo].value_counts()
    st.bar_chart(sexo_grp)

st.markdown("### Conversão e uso de canais por faixa etária")

col_p3, col_p4 = st.columns(2)

# Conversão por faixa etária
with col_p3:
    conv_idade = (
        df_filt
        .groupby("faixa_idade")
        .agg(
            atendimentos=(col_id, "count"),
            realizados=(col_status, lambda x: (x == "Realizado").sum()),
        )
    )
    conv_idade["taxa_conversao"] = (
        conv_idade["realizados"] / conv_idade["atendimentos"] * 100
    ).round(1)

    st.markdown("#### Taxa de conversão (%) por faixa etária")
    st.bar_chart(conv_idade["taxa_conversao"])

# Uso de canal por faixa etária
with col_p4:
    uso_canal_faixa = (
        df_filt
        .groupby(["faixa_idade", col_canal])[col_id]
        .count()
        .unstack(fill_value=0)
        .sort_index()
    )

    st.markdown("#### Uso dos canais por faixa etária (nº de atendimentos)")
    st.bar_chart(uso_canal_faixa)

# -------------------------------------------------------------
# 6. Insights automáticos
# -------------------------------------------------------------
st.markdown("## Insights automáticos")

# 6.1 – Insights por canal
st.markdown("### 📌 Canais de agendamento")

# Canal com maior conversão
canal_top_conv = grupo_canal.sort_values("taxa_conversao", ascending=False).head(1)
if not canal_top_conv.empty:
    nome = canal_top_conv.index[0]
    conv = canal_top_conv["taxa_conversao"].iloc[0]
    st.info(
        f"🔹 **Melhor canal em conversão:** {nome} — taxa de conversão de **{conv:.1f}%** "
        f"sobre os atendimentos filtrados."
    )

# Canal com maior faturamento
canal_top_fat = grupo_canal.sort_values("faturamento", ascending=False).head(1)
if not canal_top_fat.empty:
    nome = canal_top_fat.index[0]
    fat = canal_top_fat["faturamento"].iloc[0]
    st.info(
        f"💰 **Canal com maior faturamento:** {nome} — faturamento bruto de "
        f"**R$ {fat:,.2f}** no período selecionado.".replace(",", ".")
    )

# Canal com maior lucro
canal_top_lucro = grupo_canal.sort_values("lucro", ascending=False).head(1)
if not canal_top_lucro.empty:
    nome = canal_top_lucro.index[0]
    luc = canal_top_lucro["lucro"].iloc[0]
    st.info(
        f"📈 **Canal com maior lucro estimado:** {nome} — lucro aproximado de "
        f"**R$ {luc:,.2f}** para os atendimentos filtrados.".replace(",", ".")
    )

# Canal com maior taxa de cancelamento
canal_top_cancel = grupo_canal.sort_values("taxa_cancelamento", ascending=False).head(1)
if not canal_top_cancel.empty:
    nome = canal_top_cancel.index[0]
    canc = canal_top_cancel["taxa_cancelamento"].iloc[0]
    st.warning(
        f"⚠️ **Canal com maior taxa de cancelamento:** {nome} — "
        f"**{canc:.1f}%** dos atendimentos são cancelados."
    )

# Canal com pior conversão (considerando pelo menos 50 atendimentos para evitar ruído)
grupo_canal_maior_amostra = grupo_canal[grupo_canal["atendimentos"] >= 50]
if not grupo_canal_maior_amostra.empty:
    canal_pior_conv = grupo_canal_maior_amostra.sort_values("taxa_conversao", ascending=True).head(1)
    nome = canal_pior_conv.index[0]
    conv = canal_pior_conv["taxa_conversao"].iloc[0]
    st.warning(
        f"🚨 **Canal com pior conversão (amostra ≥ 50 atendimentos):** {nome} — "
        f"taxa de conversão de apenas **{conv:.1f}%**."
    )

st.markdown("---")

# 6.2 – Insights por faixa etária
st.markdown("### 👥 Faixa etária dos pacientes")

# Garante faixas de idade (caso não tenham sido criadas antes)
if "faixa_idade" not in df_filt.columns:
    df_filt["faixa_idade"] = pd.cut(
        df_filt[col_idade],
        bins=[0, 17, 25, 35, 45, 60, 200],
        labels=["0-17", "18-25", "26-35", "36-45", "46-60", "60+"],
        right=True,
    )

conv_idade = (
    df_filt
    .groupby("faixa_idade")
    .agg(
        atendimentos=(col_id, "count"),
        realizados=(col_status, lambda x: (x == "Realizado").sum()),
    )
)

conv_idade["taxa_conversao"] = (
    conv_idade["realizados"] / conv_idade["atendimentos"] * 100
).round(1)

conv_idade = conv_idade[conv_idade["atendimentos"] > 0]

if not conv_idade.empty:
    faixa_top_conv = conv_idade.sort_values("taxa_conversao", ascending=False).head(1)
    faixa = faixa_top_conv.index[0]
    tx = faixa_top_conv["taxa_conversao"].iloc[0]
    st.info(
        f"👶👵 **Faixa etária com melhor conversão:** {faixa} — "
        f"taxa de conversão média de **{tx:.1f}%**."
    )

# Uso de canal por faixa etária – canal predominante em cada faixa
uso_canal_faixa = (
    df_filt
    .groupby(["faixa_idade", col_canal])[col_id]
    .count()
    .reset_index(name="atendimentos")
)

if not uso_canal_faixa.empty:
    st.markdown("#### Canais mais usados por faixa etária (resumo)")

    # Para cada faixa, pega o canal com mais atendimentos
    resumo = []
    for faixa, grupo in uso_canal_faixa.groupby("faixa_idade"):
        canal_top = grupo.sort_values("atendimentos", ascending=False).iloc[0]
        resumo.append(
            f"- Faixa **{faixa}**: canal mais utilizado é **{canal_top[col_canal]}** "
            f"com **{canal_top['atendimentos']}** atendimentos."
        )

    st.markdown("\n".join(resumo))

st.markdown(
    """
---  
**Próximos passos (visão futura do CanalCerto):**  
- Incorporar modelos preditivos para recomendar o **melhor canal** para cada perfil de paciente, considerando canal, sexo, idade, histórico de conversão e cancelamento.  
- Adicionar alertas para canais com queda brusca de conversão ou aumento de cancelamentos.
"""
)
