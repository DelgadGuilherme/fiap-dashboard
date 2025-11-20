import os
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

# ============================
# CanalCerto Color Palette (from logo)
# ============================

LOGO_PINK = "#FF66C4"
LOGO_PURPLE = "#C266FF"
LOGO_BLUE = "#66C4FF"

PINK_LIGHT = "#FF99D9"
PINK_MEDIUM = "#FF66C4"
PINK_DARK = "#CC529D"

PURPLE_LIGHT = "#D699FF"
PURPLE_MEDIUM = "#C266FF"
PURPLE_DARK = "#9B52CC"

BLUE_LIGHT = "#99D9FF"
BLUE_MEDIUM = "#66C4FF"
BLUE_DARK = "#529FCC"

# Sexo
GENDER_COLOR_SCALE = alt.Scale(
    domain=["Feminino", "Masculino"],
    range=[PINK_MEDIUM, BLUE_MEDIUM],
)

# Canais (até 5 canais distintos)
CHANNEL_COLOR_BASE = [PINK_MEDIUM, PURPLE_MEDIUM, BLUE_MEDIUM, PINK_DARK, BLUE_DARK]

# Faixas etárias (a partir de 18)
AGE_COLOR_SCALE = alt.Scale(
    domain=["18-25", "26-35", "36-45", "46-60", "60+"],
    range=[BLUE_LIGHT, BLUE_MEDIUM, BLUE_DARK, PURPLE_LIGHT, PURPLE_MEDIUM],
)

DIGITAL_CHANNELS = ["App", "WhatsApp", "SMS"] 

# ============================
# Page config
# ============================
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

# ============================
# Helper – styled insight boxes
# ============================

def insight_box(text: str, tone: str = "info", icon: str = "ℹ️"):
    tones = {
        "info": {
            "bg": "linear-gradient(90deg,#020617,#0f172a)",
            "border": LOGO_BLUE,
        },
        "success": {
            "bg": "linear-gradient(90deg,#022c22,#0f172a)",
            "border": "#22c55e",
        },
        "warning": {
            "bg": "linear-gradient(90deg,#422006,#0f172a)",
            "border": "#eab308",
        },
        "danger": {
            "bg": "linear-gradient(90deg,#450a0a,#0f172a)",
            "border": "#ef4444",
        },
    }

    style = tones.get(tone, tones["info"])

    html = f"""
    <div style="
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 8px;
        border: 1px solid {style['border']};
        background: {style['bg']};
        color: #e5e7eb;
        font-size: 0.95rem;
    ">
        <span style="margin-right:8px;">{icon}</span>{text}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ============================
# 1. Load data
# ============================

DATA_PATH = os.path.join("data", "dataset_canalcerto.csv")

st.sidebar.header("1. Carregar base de dados")
st.sidebar.success(f"Usando arquivo local:\n`{DATA_PATH}`")


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df_local = pd.read_csv(path)
    df_local["data_atendimento"] = pd.to_datetime(df_local["data_atendimento"])
    return df_local


try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(f"Arquivo não encontrado em `{DATA_PATH}`. Verifique o caminho e o nome do arquivo.")
    st.stop()

st.info(f"Base carregada com **{len(df):,}** atendimentos.".replace(",", "."))

# Column mapping
id_col = "id_atendimento"
date_col = "data_atendimento"
month_col = "mes_referencia"
patient_col = "paciente_id"
gender_col = "sexo_paciente"
age_col = "idade_paciente"
channel_col = "canal_atendimento"
type_col = "tipo_atendimento"
specialty_col = "especialidade"
status_col = "status_atendimento"
gross_value_col = "valor_bruto"
cost_col = "custo_operacional"
profit_col = "lucro_liquido"
positive_return_col = "retorno_positivo"

# ============================
# 2. Filters
# ============================

st.sidebar.header("2. Filtros")

min_date = df[date_col].min()
max_date = df[date_col].max()

period = st.sidebar.date_input(
    "Período de agendamento",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(period, tuple):
    start_date, end_date = period
else:
    start_date, end_date = min_date, max_date

channels = sorted(df[channel_col].dropna().unique().tolist())
selected_channels = st.sidebar.multiselect(
    "Canais de agendamento",
    options=channels,
    default=channels,
)

status_options = sorted(df[status_col].dropna().unique().tolist())
selected_status = st.sidebar.multiselect(
    "Status do atendimento",
    options=status_options,
    default=status_options,
)

genders = sorted(df[gender_col].dropna().unique().tolist())
selected_genders = st.sidebar.multiselect(
    "Sexo do paciente",
    options=genders,
    default=genders,
)

age_min = int(df[age_col].min())
age_max = int(df[age_col].max())
selected_age_range = st.sidebar.slider(
    "Faixa de idade",
    min_value=age_min,
    max_value=age_max,
    value=(age_min, age_max),
)

filter_mask = (
    (df[date_col].dt.date >= start_date)
    & (df[date_col].dt.date <= end_date)
    & (df[channel_col].isin(selected_channels))
    & (df[status_col].isin(selected_status))
    & (df[gender_col].isin(selected_genders))
    & (df[age_col].between(selected_age_range[0], selected_age_range[1]))
)

filtered_df = df.loc[filter_mask].copy()

st.markdown("### Visão geral dos atendimentos filtrados")
st.write(f"Registros após filtros: **{len(filtered_df):,}**".replace(",", "."))

if filtered_df.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
    st.stop()

# ============================
# 3. KPIs
# ============================

total_appointments = len(filtered_df)
done_appointments = (filtered_df[status_col] == "Realizado").sum()
canceled_appointments = (filtered_df[status_col] == "Cancelado").sum()
no_show_appointments = (filtered_df[status_col] == "Não compareceu").sum()

total_revenue = filtered_df[gross_value_col].sum()
total_profit = filtered_df[profit_col].sum()

avg_ticket = filtered_df.loc[filtered_df[status_col] == "Realizado", gross_value_col].mean()

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.metric("Total de atendimentos", f"{total_appointments:,}".replace(",", "."))
with col_kpi2:
    done_rate = done_appointments / total_appointments * 100 if total_appointments > 0 else 0
    st.metric("Taxa de realização", f"{done_rate:.2f}%")
with col_kpi3:
    cancel_rate = canceled_appointments / total_appointments * 100 if total_appointments > 0 else 0
    st.metric("Taxa de cancelamento", f"{cancel_rate:.2f}%")
with col_kpi4:
    ticket_label = f"R$ {avg_ticket:,.2f}" if not np.isnan(avg_ticket) else "R$ 0,00"
    st.metric("Ticket médio (realizados)", ticket_label.replace(",", "."))

col_kpi5, col_kpi6 = st.columns(2)

with col_kpi5:
    st.metric("Faturamento total (bruto)", f"R$ {total_revenue:,.2f}".replace(",", "."))
with col_kpi6:
    st.metric("Lucro total (estimado)", f"R$ {total_profit:,.2f}".replace(",", "."))

st.markdown("---")

# ============================
# 4. Performance by channel
# ============================

st.markdown("## Desempenho por canal de agendamento")

channel_group = (
    filtered_df
    .groupby(channel_col)
    .agg(
        appointments=(id_col, "count"),
        done=(status_col, lambda x: (x == "Realizado").sum()),
        canceled=(status_col, lambda x: (x == "Cancelado").sum()),
        no_show=(status_col, lambda x: (x == "Não compareceu").sum()),
        revenue=(gross_value_col, "sum"),
        profit=(profit_col, "sum"),
    )
)

channel_group["conversion_rate"] = (
    channel_group["done"] / channel_group["appointments"] * 100
).round(2)

channel_group["cancel_rate"] = (
    channel_group["canceled"] / channel_group["appointments"] * 100
).round(2)

channel_group["avg_ticket"] = (
    channel_group["revenue"] / channel_group["done"]
).replace([np.inf, -np.inf], np.nan).round(2)

channel_group = channel_group.sort_values("revenue", ascending=False)
channel_group_df = channel_group.reset_index()

# escala global de cor para canais
channel_domain = channel_group_df[channel_col].tolist()
channel_color_scale = alt.Scale(
    domain=channel_domain,
    range=CHANNEL_COLOR_BASE[: len(channel_domain)],
)

# Tabela com nomes em português
channel_table = channel_group_df.rename(
    columns={
        channel_col: "canal_atendimento",
        "appointments": "atendimentos",
        "done": "realizados",
        "canceled": "cancelados",
        "no_show": "nao_compareceu",
        "revenue": "faturamento",
        "profit": "lucro",
        "conversion_rate": "taxa_conversao",
        "cancel_rate": "taxa_cancelamento",
        "avg_ticket": "ticket_medio",
    }
)

# Construir tabela com nomes em português e colunas formatadas
channel_table = (
    channel_group_df
    .assign(
        taxa_conversao=lambda d: d["conversion_rate"].map(lambda v: f"{v:.2f}%"),
        taxa_cancelamento=lambda d: d["cancel_rate"].map(lambda v: f"{v:.2f}%"),
        faturamento=lambda d: d["revenue"].map(lambda v: f"R$ {v:,.2f}".replace(",", ".")),
        lucro=lambda d: d["profit"].map(lambda v: f"R$ {v:,.2f}".replace(",", ".")),
        ticket_medio=lambda d: d["avg_ticket"].map(lambda v: f"R$ {v:,.2f}".replace(",", ".")),
    )
    .rename(
        columns={
            channel_col: "canal_atendimento",
            "appointments": "atendimentos",
            "done": "realizados",
            "canceled": "cancelados",
            "no_show": "nao_compareceu",
        }
    )[
        [
            "canal_atendimento",
            "atendimentos",
            "realizados",
            "cancelados",
            "nao_compareceu",
            "faturamento",
            "lucro",
            "taxa_conversao",
            "taxa_cancelamento",
            "ticket_medio",
        ]
    ]
)

st.dataframe(channel_table, use_container_width=True)

col_ch1, col_ch2 = st.columns(2)

with col_ch1:
    st.markdown("#### Atendimentos por canal")

    base_appointments = alt.Chart(channel_group_df).encode(
        x=alt.X(f"{channel_col}:N", title="Canal"),
    )

    bars_appointments = base_appointments.mark_bar().encode(
        y=alt.Y("appointments:Q", title="Nº de atendimentos"),
        color=alt.Color(f"{channel_col}:N", title="Canal", scale=channel_color_scale),
        tooltip=[channel_col, "appointments"],
    )

    line_appointments = base_appointments.mark_line(color="#FFFFFF", point=True).encode(
        y="appointments:Q"
    )

    chart_appointments = (bars_appointments + line_appointments).properties(
        background="transparent"
    )
    st.altair_chart(chart_appointments, use_container_width=True)

with col_ch2:
    st.markdown("#### Faturamento por canal")

    base_revenue = alt.Chart(channel_group_df).encode(
        x=alt.X(f"{channel_col}:N", title="Canal"),
    )

    bars_revenue = base_revenue.mark_bar().encode(
        y=alt.Y("revenue:Q", title="Faturamento (R$)"),
        color=alt.Color(f"{channel_col}:N", title="Canal", scale=channel_color_scale),
        tooltip=[channel_col, alt.Tooltip("revenue:Q", format=",.2f")],
    )

    line_revenue = base_revenue.mark_line(color="#FFFFFF", point=True).encode(
        y="revenue:Q"
    )

    chart_revenue = (bars_revenue + line_revenue).properties(background="transparent")
    st.altair_chart(chart_revenue, use_container_width=True)

col_ch3, col_ch4 = st.columns(2)

with col_ch3:
    st.markdown("#### Taxa de conversão (%) por canal")

    base_conv_channel = alt.Chart(channel_group_df).encode(
        x=alt.X(f"{channel_col}:N", title="Canal"),
    )

    bars_conv_channel = base_conv_channel.mark_bar().encode(
        y=alt.Y("conversion_rate:Q", title="Taxa de conversão (%)"),
        color=alt.Color(f"{channel_col}:N", title="Canal", scale=channel_color_scale),
        tooltip=[channel_col, "conversion_rate"],
    )

    line_conv_channel = base_conv_channel.mark_line(color="#FFFFFF", point=True).encode(
        y="conversion_rate:Q"
    )

    chart_conv_channel = (bars_conv_channel + line_conv_channel).properties(
        background="transparent"
    )
    st.altair_chart(chart_conv_channel, use_container_width=True)

with col_ch4:
    st.markdown("#### Taxa de cancelamento (%) por canal")

    base_cancel_channel = alt.Chart(channel_group_df).encode(
        x=alt.X(f"{channel_col}:N", title="Canal"),
    )

    bars_cancel_channel = base_cancel_channel.mark_bar().encode(
        y=alt.Y("cancel_rate:Q", title="Taxa de cancelamento (%)"),
        color=alt.Color(f"{channel_col}:N", title="Canal", scale=channel_color_scale),
        tooltip=[channel_col, "cancel_rate"],
    )

    line_cancel_channel = base_cancel_channel.mark_line(color="#FFFFFF", point=True).encode(
        y="cancel_rate:Q"
    )

    chart_cancel_channel = (bars_cancel_channel + line_cancel_channel).properties(
        background="transparent"
    )
    st.altair_chart(chart_cancel_channel, use_container_width=True)

st.markdown("---")

# ============================
# 5. Patient profile
# ============================

st.markdown("## Perfil dos pacientes")

filtered_df["age_group"] = pd.cut(
    filtered_df[age_col],
    bins=[0, 17, 25, 35, 45, 60, 200],
    labels=["0-17", "18-25", "26-35", "36-45", "46-60", "60+"],
    right=True,
)

valid_age_groups = (
    filtered_df["age_group"]
    .value_counts()
    .loc[lambda x: x > 0]
    .index
)

filtered_valid_age_df = filtered_df[filtered_df["age_group"].isin(valid_age_groups)]

age_dist_df = (
    filtered_valid_age_df["age_group"]
    .value_counts()
    .rename("appointments")
    .reset_index()
    .rename(columns={"index": "age_group"})
    .sort_values("age_group")
)

gender_dist_df = (
    filtered_valid_age_df
    .groupby(gender_col)[id_col]
    .count()
    .reset_index(name="appointments")
)

conversion_by_age = (
    filtered_valid_age_df
    .groupby("age_group")
    .agg(
        appointments=(id_col, "count"),
        done=(status_col, lambda x: (x == "Realizado").sum()),
        revenue=(gross_value_col, "sum"),
        profit=(profit_col, "sum"),
        canceled=(status_col, lambda x: (x == "Cancelado").sum()),
    )
)

conversion_by_age["conversion_rate"] = (
    conversion_by_age["done"] / conversion_by_age["appointments"] * 100
).round(2)

conversion_by_age["cancel_rate"] = (
    conversion_by_age["canceled"] / conversion_by_age["appointments"] * 100
).round(2)

conversion_by_age["avg_profit"] = (
    conversion_by_age["profit"] / conversion_by_age["appointments"]
).round(2)

conversion_by_age_df = conversion_by_age.reset_index()

usage_by_age_df = (
    filtered_valid_age_df
    .groupby(["age_group", channel_col])[id_col]
    .count()
    .reset_index(name="appointments")
)

col_pf1, col_pf2 = st.columns(2)

with col_pf1:
    st.markdown("#### Distribuição por faixa etária")

    age_chart = (
        alt.Chart(age_dist_df)
        .mark_bar()
        .encode(
            x=alt.X("age_group:N", title="Faixa etária"),
            y=alt.Y("appointments:Q", title="Nº de atendimentos"),
            color=alt.Color("age_group:N", scale=AGE_COLOR_SCALE, title="Faixa etária"),
            tooltip=["age_group", "appointments"],
        )
        .properties(background="transparent")
    )

    st.altair_chart(age_chart, use_container_width=True)

with col_pf2:
    st.markdown("#### Distribuição por sexo")

    gender_chart = (
        alt.Chart(gender_dist_df)
        .mark_bar()
        .encode(
            x=alt.X(f"{gender_col}:N", title="Sexo"),
            y=alt.Y("appointments:Q", title="Nº de atendimentos"),
            color=alt.Color(
                f"{gender_col}:N",
                title="Sexo",
                scale=GENDER_COLOR_SCALE,
            ),
            tooltip=[gender_col, "appointments"],
        )
        .properties(background="transparent")
    )

    st.altair_chart(gender_chart, use_container_width=True)

st.markdown("### Conversão e uso de canais por faixa etária")

col_pf3, col_pf4 = st.columns(2)

with col_pf3:
    base_conv_age = alt.Chart(conversion_by_age_df).encode(
        x=alt.X("age_group:N", title="Faixa etária"),
    )

    bars_conv_age = base_conv_age.mark_bar().encode(
        y=alt.Y("conversion_rate:Q", title="Taxa de conversão (%)"),
        color=alt.Color(
            "age_group:N",
            scale=AGE_COLOR_SCALE,
            title="Faixa etária",
        ),
        tooltip=["age_group", "conversion_rate"],
    )

    line_conv_age = base_conv_age.mark_line(color="#FFFFFF", point=True).encode(
        y="conversion_rate:Q"
    )

    conv_age_chart = (bars_conv_age + line_conv_age).properties(
        background="transparent"
    )

    st.markdown("#### Taxa de conversão (%) por faixa etária")
    st.altair_chart(conv_age_chart, use_container_width=True)

with col_pf4:
    st.markdown("#### Uso dos canais por faixa etária (empilhado)")

    usage_chart = (
        alt.Chart(usage_by_age_df)
        .mark_bar()
        .encode(
            x=alt.X("age_group:N", title="Faixa etária"),
            y=alt.Y("appointments:Q", title="Nº de atendimentos", stack="zero"),
            color=alt.Color(
                f"{channel_col}:N",
                title="Canal",
                scale=channel_color_scale,
            ),
            tooltip=["age_group", channel_col, "appointments"],
        )
        .properties(background="transparent")
    )

    st.altair_chart(usage_chart, use_container_width=True)

    # ============================
# 5.1. Análises avançadas
# ============================

st.markdown("## Análises avançadas")

col_adv1, col_adv2 = st.columns(2)

# ----------------------------------------
# A) Idade x probabilidade de agendamento digital
# ----------------------------------------
with col_adv1:
    st.markdown("### Idade x probabilidade de agendamento digital")

    if not filtered_valid_age_df.empty:
        age_digital_df = (
            filtered_valid_age_df
            .assign(
                is_digital=lambda d: d[channel_col].isin(DIGITAL_CHANNELS)
            )
            .groupby("age_group")
            .agg(
                total_appointments=(id_col, "count"),
                digital_appointments=("is_digital", "sum"),
            )
        )

        age_digital_df["digital_rate"] = (
            age_digital_df["digital_appointments"]
            / age_digital_df["total_appointments"]
            * 100
        ).round(2)

        age_digital_df = age_digital_df.reset_index()

        base_digital_age = alt.Chart(age_digital_df).encode(
            x=alt.X("age_group:N", title="Faixa etária"),
        )

        bars_digital_age = base_digital_age.mark_bar().encode(
            y=alt.Y("digital_rate:Q", title="Probabilidade de agendamento digital (%)"),
            color=alt.Color(
                "age_group:N",
                scale=AGE_COLOR_SCALE,
                title="Faixa etária",
            ),
            tooltip=[
                "age_group",
                alt.Tooltip("digital_rate:Q", title="Prob. digital (%)", format=".2f"),
                "total_appointments",
                "digital_appointments",
            ],
        )

        line_digital_age = base_digital_age.mark_line(color="#FFFFFF", point=True).encode(
            y="digital_rate:Q"
        )

        digital_age_chart = (bars_digital_age + line_digital_age).properties(
            background="transparent"
        )

        st.altair_chart(digital_age_chart, use_container_width=True)
    else:
        st.info("Não há dados suficientes para calcular a probabilidade de agendamento digital por faixa etária.")

# ----------------------------------------
# B) Tipo de especialidade x canal
# ----------------------------------------
with col_adv2:
    st.markdown("### Tipo de especialidade x canal")

    # usar o dataframe filtrado principal (todas idades)
    if not filtered_df.empty:
        # pegar as 5 especialidades com maior volume
        top_specialties = (
            filtered_df
            .groupby(specialty_col)[id_col]
            .count()
            .sort_values(ascending=False)
            .head(5)
            .index
            .tolist()
        )

        specialty_channel_df = (
            filtered_df[filtered_df[specialty_col].isin(top_specialties)]
            .groupby([specialty_col, channel_col])[id_col]
            .count()
            .reset_index(name="appointments")
        )

        # normalizar por especialidade para mostrar proporção (0–100%)
        specialty_totals = (
            specialty_channel_df
            .groupby(specialty_col)["appointments"]
            .transform("sum")
        )
        specialty_channel_df["percentage"] = (
            specialty_channel_df["appointments"] / specialty_totals * 100
        ).round(2)

        specialty_chart = (
            alt.Chart(specialty_channel_df)
            .mark_bar()
            .encode(
                x=alt.X(f"{specialty_col}:N", title="Especialidade"),
                y=alt.Y("percentage:Q", title="Participação do canal (%)", stack="normalize"),
                color=alt.Color(
                    f"{channel_col}:N",
                    title="Canal",
                    scale=channel_color_scale,
                ),
                tooltip=[
                    specialty_col,
                    channel_col,
                    "appointments",
                    alt.Tooltip("percentage:Q", title="Participação (%)", format=".2f"),
                ],
            )
            .properties(background="transparent")
        )

        st.altair_chart(specialty_chart, use_container_width=True)
    else:
        st.info("Não há dados suficientes para analisar especialidade x canal.")

# ============================
# 6. Automatic insights
# ============================

st.markdown("## Insights automáticos")

st.markdown("### 📌 Canais de agendamento")

top_conv_channel = channel_group.sort_values("conversion_rate", ascending=False).head(1)
if not top_conv_channel.empty:
    name = top_conv_channel.index[0]
    conv_value = top_conv_channel["conversion_rate"].iloc[0]
    insight_box(
        f"<b>Melhor canal em conversão:</b> {name} — taxa de conversão de "
        f"<b>{conv_value:.2f}%</b> sobre os atendimentos filtrados.",
        tone="info",
        icon="📌",
    )

top_revenue_channel = channel_group.sort_values("revenue", ascending=False).head(1)
if not top_revenue_channel.empty:
    name = top_revenue_channel.index[0]
    revenue_value = top_revenue_channel["revenue"].iloc[0]
    insight_box(
        f"<b>Canal com maior faturamento:</b> {name} — faturamento bruto de "
        f"<b>R$ {revenue_value:,.2f}</b> no período selecionado.".replace(",", "."),
        tone="info",
        icon="💰",
    )

top_profit_channel = channel_group.sort_values("profit", ascending=False).head(1)
if not top_profit_channel.empty:
    name = top_profit_channel.index[0]
    profit_value = top_profit_channel["profit"].iloc[0]
    insight_box(
        f"<b>Canal com maior lucro estimado:</b> {name} — lucro aproximado de "
        f"<b>R$ {profit_value:,.2f}</b> para os atendimentos filtrados.".replace(",", "."),
        tone="info",
        icon="📈",
    )

top_cancel_channel = channel_group.sort_values("cancel_rate", ascending=False).head(1)
if not top_cancel_channel.empty:
    name = top_cancel_channel.index[0]
    cancel_value = top_cancel_channel["cancel_rate"].iloc[0]
    insight_box(
        f"<b>Canal com maior taxa de cancelamento:</b> {name} — "
        f"<b>{cancel_value:.2f}%</b> dos atendimentos são cancelados.",
        tone="warning",
        icon="⚠️",
    )

large_sample_channels = channel_group[channel_group["appointments"] >= 50]
if not large_sample_channels.empty:
    worst_conv_channel = large_sample_channels.sort_values(
        "conversion_rate", ascending=True
    ).head(1)
    name = worst_conv_channel.index[0]
    conv_value = worst_conv_channel["conversion_rate"].iloc[0]
    insight_box(
        f"<b>Canal com pior conversão (amostra ≥ 50 atendimentos):</b> {name} — "
        f"taxa de conversão de apenas <b>{conv_value:.2f}%</b>.",
        tone="danger",
        icon="❗",
    )

st.markdown("---")

st.markdown("### 👥 Por idade")

if not conversion_by_age.empty:
    best_conv_age = conversion_by_age.sort_values("conversion_rate", ascending=False).head(1)
    age_group_best = best_conv_age.index[0]
    conv_value = best_conv_age["conversion_rate"].iloc[0]

    insight_box(
        f"<b>Faixa etária com maior conversão:</b> {age_group_best} — "
        f"taxa de conversão média de <b>{conv_value:.2f}%</b>.",
        tone="info",
        icon="📌",
    )

    best_profit_age = conversion_by_age.sort_values("profit", ascending=False).head(1)
    age_group_profit = best_profit_age.index[0]
    profit_value = best_profit_age["profit"].iloc[0]

    insight_box(
        f"<b>Faixa etária mais rentável (lucro total):</b> {age_group_profit} — "
        f"lucro estimado de <b>R$ {profit_value:,.2f}</b>.".replace(",", "."),
        tone="info",
        icon="💰",
    )

    worst_cancel_age = conversion_by_age.sort_values("cancel_rate", ascending=False).head(1)
    age_group_cancel = worst_cancel_age.index[0]
    cancel_value = worst_cancel_age["cancel_rate"].iloc[0]

    insight_box(
        f"<b>Faixa etária com maior taxa de cancelamento:</b> {age_group_cancel} — "
        f"<b>{cancel_value:.2f}%</b> dos atendimentos são cancelados.",
        tone="warning",
        icon="⚠️",
    )

st.markdown("---")

st.markdown("### 📱 Comportamento digital")

if not age_digital_df.empty:
    top_digital_age = age_digital_df.sort_values("digital_rate", ascending=False).head(1)
    age_top = top_digital_age["age_group"].iloc[0]
    rate_top = top_digital_age["digital_rate"].iloc[0]

    insight_box(
        f"<b>Faixa etária mais digital:</b> {age_top} — probabilidade de "
        f"<b>{rate_top:.2f}%</b> de agendamento via canais digitais.",
        tone="info",
        icon="📊",
    )

    bottom_digital_age = age_digital_df.sort_values("digital_rate", ascending=True).head(1)
    age_low = bottom_digital_age["age_group"].iloc[0]
    rate_low = bottom_digital_age["digital_rate"].iloc[0]

    insight_box(
        f"<b>Faixa menos digital:</b> {age_low} — apenas <b>{rate_low:.2f}%</b> utilizam App, WhatsApp ou SMS.",
        tone="warning",
        icon="⚠️",
    )

    gap = rate_top - rate_low
    insight_box(
        f"A diferença entre o público mais e o menos digital é de <b>{gap:.2f} pontos percentuais</b>, "
        f"indicando potencial para estratégias segmentadas por idade.",
        tone="info",
        icon="📈",
    )
else:
    insight_box("Não há dados suficientes para gerar insights digitais por idade.", tone="warning")

st.markdown("---")

st.markdown("### 🏥 Tipo de especialidade")

if not specialty_channel_df.empty:

    for canal in channel_domain:
        df_canal = specialty_channel_df[specialty_channel_df[channel_col] == canal]
        if not df_canal.empty:
            top_spec = df_canal.sort_values("percentage", ascending=False).head(1)
            spec_name = top_spec[specialty_col].iloc[0]
            pct = top_spec["percentage"].iloc[0]

            insight_box(
                f"O canal <b>{canal}</b> é mais utilizado na especialidade <b>{spec_name}</b> "
                f"({pct:.2f}% dos atendimentos desta especialidade).",
                tone="info",
                icon="📌",
            )

    dig_df = specialty_channel_df[specialty_channel_df[channel_col].isin(DIGITAL_CHANNELS)]
    dig_group = (
        dig_df.groupby(specialty_col)["percentage"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    top_digital_spec = dig_group.head(1)
    spec_dig = top_digital_spec[specialty_col].iloc[0]
    pct_dig = top_digital_spec["percentage"].iloc[0]

    insight_box(
        f"A especialidade mais digital é <b>{spec_dig}</b>, com <b>{pct_dig:.2f}%</b> dos seus "
        f"agendamentos realizados via App, WhatsApp ou SMS.",
        tone="success",
        icon="💡",
    )

    non_digital = specialty_channel_df[~specialty_channel_df[channel_col].isin(DIGITAL_CHANNELS)]
    non_group = (
        non_digital.groupby(specialty_col)["percentage"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    top_nondigital_spec = non_group.head(1)
    spec_nondig = top_nondigital_spec[specialty_col].iloc[0]
    pct_nondig = top_nondigital_spec["percentage"].iloc[0]

    insight_box(
        f"A especialidade com maior dependência de canais tradicionais é <b>{spec_nondig}</b>, "
        f"com <b>{pct_nondig:.2f}%</b> dos atendimentos ocorrendo via telefone ou presencial.",
        tone="warning",
        icon="☎️",
    )

else:
    insight_box("Não há dados suficientes para gerar insights por especialidade.", tone="warning")

st.markdown(
    """
    ---  
    ### 🔮 Próximos passos (visão futura do CanalCerto)

    O CanalCerto evoluirá para incorporar recursos avançados de inteligência analítica, incluindo:

    - **Módulo preditivo** para estimar o canal mais provável de agendamento para cada paciente, considerando idade, sexo, comportamento digital, especialidade e histórico de conversão.
    - **Detecção automática de anomalias**, identificando quedas repentinas de conversão ou aumentos incomuns de cancelamentos.
    - **Recomendações inteligentes**, sugerindo ajustes operacionais, priorização de canais e oportunidades de otimização baseadas em padrões dos dados.
    - **Aprimoramento do perfil digital do paciente**, permitindo segmentações mais precisas e ações personalizadas.
        
    Essas funcionalidades complementam o protótipo atual e representam a próxima fase de evolução da plataforma CanalCerto.
    """
)
