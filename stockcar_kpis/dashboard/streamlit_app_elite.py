"""
dashboard/streamlit_app_elite.py
Stock Car KPIs — Dashboard de Elite (Telemetria Profissional)

Visual inspirado em sistemas de telemetria da F1 (McLaren, Red Bull).
Foco: Impressionar. Demonstrar maestria. Parecer que você é o cara.

Rode com: streamlit run stockcar_kpis/dashboard/streamlit_app_elite.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sqlalchemy.engine import Engine

from stockcar_kpis.config import DATABASE_URL, EQUIPE_CORES, PONTOS_STOCK_CAR
from stockcar_kpis.dashboard.streamlit_config import apply_motorsport_theme, create_section_header
from stockcar_kpis.ml.explainability import ModelExplainer, create_prediction_explanation_chart

# ════════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO INICIAL
# ════════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Stock Car Performance Analytics",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_motorsport_theme()

PONTOS = PONTOS_STOCK_CAR

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#0A0E27",
    plot_bgcolor="#1A1F3A",
    font=dict(color="#E0E0E0", size=11, family="Monaco, monospace"),
    margin=dict(l=40, r=40, t=60, b=40),
    hoverlabel=dict(bgcolor="#1A1F3A", font_size=11, font_color="#E0E0E0", bordercolor="#00D9FF"),
    title_font_size=14,
    title_font_color="#00D9FF",
)

# ════════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_engine() -> Engine:
    return create_engine(DATABASE_URL)


@st.cache_data(ttl=60)
def load_resultados() -> pd.DataFrame:
    return pd.read_sql(
        "SELECT r.*, c.circuito, c.data, c.condicoes_pista "
        "FROM resultados r JOIN corridas c ON r.corrida_id = c.id "
        "ORDER BY c.data", get_engine())


@st.cache_data(ttl=60)
def load_pit_stops() -> pd.DataFrame:
    return pd.read_sql(
        "SELECT p.*, c.circuito, c.data "
        "FROM pit_stops p JOIN corridas c ON p.corrida_id = c.id "
        "ORDER BY c.data", get_engine())


# ════════════════════════════════════════════════════════════════════════════════
# SIDEBAR — CONTROLES
# ════════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### ⚙️ FILTROS")
    st.markdown("---")

    df_all = load_resultados()
    temporadas = sorted(df_all["temporada"].dropna().unique().tolist(), reverse=True)
    equipes    = sorted(df_all["equipe"].unique().tolist())
    pilotos    = sorted(df_all["piloto"].unique().tolist())

    sel_temp   = st.multiselect("📅 TEMPORADA", temporadas, default=temporadas)
    sel_equipe = st.multiselect("🏁 EQUIPE",    equipes,    default=equipes)
    sel_piloto = st.multiselect("👤 PILOTO",    pilotos,    default=pilotos)

    st.markdown("---")
    st.caption("📊 Dados: stockcar.com.br / Wikipedia")

# ════════════════════════════════════════════════════════════════════════════════
# FILTRAR DADOS
# ════════════════════════════════════════════════════════════════════════════════

df = load_resultados()
df = df[df["temporada"].isin(sel_temp) &
        df["equipe"].isin(sel_equipe) &
        df["piloto"].isin(sel_piloto)].copy()

df_p = load_pit_stops()
df_p = df_p[df_p["temporada"].isin(sel_temp) &
            df_p["equipe"].isin(sel_equipe) &
            df_p["piloto"].isin(sel_piloto)].copy()

if df.empty:
    st.error("❌ Nenhum dado com os filtros selecionados.")
    st.stop()

# ════════════════════════════════════════════════════════════════════════════════
# HEADER ELITE
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("# 🏎️ STOCK CAR PERFORMANCE ANALYTICS")
st.markdown("*Elite Telemetry Dashboard — Engineered for Victory*")
st.markdown("---")

c1, c2, c3, c4 = st.columns(4)
c1.metric("🏁 CORRIDAS",  df["corrida_id"].nunique())
c2.metric("👤 PILOTOS",   df["piloto"].nunique())
c3.metric("🏢 EQUIPES",   df["equipe"].nunique())
c4.metric("⭐ PONTOS",    int(df["posicao"].map(PONTOS).fillna(0).sum()))

st.markdown("---")

# ════════════════════════════════════════════════════════════════════════════════
# ANÁLISE 1 — CONSISTÊNCIA
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("## 📊 CONSISTÊNCIA — QUEM ENTREGA TODA ETAPA?")
st.caption("Desvio padrão baixo = piloto confiável. Esse é o cara que você coloca em campeonato.")

cons = (df.groupby(["piloto", "equipe"])
        .agg(corridas=("posicao", "count"),
             media=("posicao", "mean"),
             stddev=("posicao", "std"),
             melhor=("posicao", "min"),
             pior=("posicao", "max"))
        .reset_index()
        .query("corridas >= 3")
        .sort_values("stddev", ascending=True))

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    y=cons["piloto"],
    x=cons["stddev"],
    orientation="h",
    marker_color=[EQUIPE_CORES.get(e, "#888") for e in cons["equipe"]],
    marker_line_width=2,
    marker_line_color="rgba(0, 217, 255, 0.3)",
    customdata=np.stack([cons["equipe"], cons["media"].round(2),
                         cons["corridas"], cons["melhor"], cons["pior"]], axis=-1),
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Equipe: %{customdata[0]}<br>"
        "Desvio: %{x:.2f}σ<br>"
        "Média: P%{customdata[1]}<br>"
        "Corridas: %{customdata[2]}<br>"
        "Range: P%{customdata[3]} → P%{customdata[4]}"
        "<extra></extra>"
    ),
))
fig1.update_layout(**PLOTLY_LAYOUT, title="SCORE DE CONSISTÊNCIA", height=450, showlegend=False)
fig1.add_vline(x=cons["stddev"].median(), line_dash="dash", line_color="#FFB300",
               annotation_text="MEDIANA", annotation_position="top right")
st.plotly_chart(fig1, use_container_width=True)

with st.expander("📋 DADOS COMPLETOS — CONSISTÊNCIA"):
    st.dataframe(cons.rename(columns={
        "piloto": "PILOTO", "equipe": "EQUIPE", "corridas": "CORRIDAS",
        "media": "MÉDIA", "stddev": "DESVIO", "melhor": "MELHOR", "pior": "PIOR"
    }), use_container_width=True, hide_index=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════════════════════════
# ANÁLISE 2 — PIT STOP
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("## ⏱️ JANELA ÓTIMA DE PIT STOP — UNDERCUT vs OVERCUT")
st.caption("Quando você faz pit, você ganha ou perde posição? Os dados revelam o padrão.")

if not df_p.empty:
    merged = df_p.merge(
        df[["corrida_id", "piloto", "posicao", "posicao_largada"]],
        on=["corrida_id", "piloto"], how="inner")
    merged["ganho"] = merged["posicao_largada"] - merged["posicao"]

    col_a, col_b = st.columns(2)

    with col_a:
        fig2a = go.Figure()
        for eq in sorted(merged["equipe"].unique()):
            grp = merged[merged["equipe"] == eq].sort_values("volta")
            fig2a.add_trace(go.Scatter(
                x=grp["volta"], y=grp["ganho"],
                mode="lines+markers",
                name=eq,
                line=dict(color=EQUIPE_CORES.get(eq, "#888"), width=2),
                marker=dict(size=8, line=dict(width=1, color="rgba(255,255,255,0.3)")),
                customdata=np.stack([
                    grp["piloto"],
                    grp["duracao_s"].round(2),
                    grp["circuito"],
                ], axis=-1),
                hovertemplate=(
                    f"<b>{eq}</b><br>"
                    "Volta: %{x}<br>"
                    "Ganho: %{y:+.1f} pos<br>"
                    "Piloto: %{customdata[0]}<br>"
                    "Duração pit: %{customdata[1]}s<br>"
                    "Circuito: %{customdata[2]}"
                    "<extra></extra>"
                ),
            ))
        # Trendline geral (OLS manual via numpy)
        if len(merged) > 2:
            z = np.polyfit(merged["volta"], merged["ganho"], 1)
            x_line = np.linspace(merged["volta"].min(), merged["volta"].max(), 100)
            y_line = np.polyval(z, x_line)
            fig2a.add_trace(go.Scatter(
                x=x_line, y=y_line,
                mode="lines", name="Tendência Geral",
                line=dict(color="#00D9FF", width=2, dash="dot"),
                hoverinfo="skip",
            ))
        fig2a.update_layout(**PLOTLY_LAYOUT, title="SCATTER: VOLTA × GANHO", height=420,
                            xaxis_title="VOLTA DO PIT", yaxis_title="POSIÇÕES GANHAS")
        fig2a.add_hline(y=0, line_dash="dash", line_color="#888", line_width=1)
        st.plotly_chart(fig2a, use_container_width=True)

    with col_b:
        merged["faixa"] = pd.cut(merged["volta"], bins=[11, 13, 15, 17, 19],
                                 labels=["12-13", "13-15", "15-17", "17-19"])
        agg = (merged.groupby("faixa", observed=True)["ganho"]
               .agg(["mean", "count"]).reset_index())
        agg.columns = ["faixa", "ganho_medio", "n"]

        fig2b = go.Figure()
        fig2b.add_trace(go.Bar(
            x=agg["faixa"].astype(str),
            y=agg["ganho_medio"],
            marker_color=["#00FF41" if v == agg["ganho_medio"].max() else "#FF0080"
                          for v in agg["ganho_medio"]],
            text=[f"{v:+.1f}\n(n={int(n)})" for v, n in zip(agg["ganho_medio"], agg["n"])],
            textposition="outside", textfont=dict(color="white", size=10),
            hovertemplate="Faixa: %{x}<br>Ganho: %{y:+.2f}<extra></extra>",
        ))
        fig2b.update_layout(**PLOTLY_LAYOUT, title="GANHO MÉDIO POR FAIXA", height=420)
        fig2b.add_hline(y=0, line_dash="dash", line_color="#888", line_width=1)
        st.plotly_chart(fig2b, use_container_width=True)
else:
    st.info("⚠️ Sem dados de pit stop para os filtros selecionados.")

st.markdown("---")

# ════════════════════════════════════════════════════════════════════════════════
# ANÁLISE 3 — ROI ESPORTIVO
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("## 📈 ROI ESPORTIVO — EFICIÊNCIA DE PONTOS")
st.caption("Qual equipe aproveita melhor o equipamento? Pontos conquistados vs. máximo possível.")

df["pts"] = df["posicao"].map(PONTOS).fillna(0)
roi = (df.groupby("equipe")
       .agg(conquistados=("pts", "sum"), participacoes=("posicao", "count"))
       .reset_index())
roi["max_pos"] = roi["participacoes"] * 25
roi["roi"]     = (roi["conquistados"] / roi["max_pos"] * 100).round(1)
roi = roi.sort_values("roi", ascending=False)

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=roi["equipe"], y=roi["roi"],
    marker_color=[EQUIPE_CORES.get(e, "#888") for e in roi["equipe"]],
    marker_line_width=2,
    marker_line_color="rgba(0, 217, 255, 0.3)",
    text=[f"{v:.1f}%" for v in roi["roi"]],
    textposition="outside", textfont=dict(color="white", size=11),
    customdata=np.stack([roi["conquistados"], roi["max_pos"], roi["participacoes"]], axis=-1),
    hovertemplate=(
        "<b>%{x}</b><br>"
        "ROI: %{y:.1f}%<br>"
        "Pontos: %{customdata[0]} / %{customdata[1]}<br>"
        "Participações: %{customdata[2]}"
        "<extra></extra>"
    ),
))
fig3.add_hline(y=50, line_dash="dash", line_color="#FFB300", line_width=2,
               annotation_text="50% (Referência)", annotation_position="right")
fig3.update_layout(**PLOTLY_LAYOUT, title="ROI ESPORTIVO POR EQUIPE", height=420,
                   yaxis_title="ROI (%)",
                   yaxis=dict(range=[0, roi["roi"].max() * 1.2]))
st.plotly_chart(fig3, use_container_width=True)

with st.expander("📋 DADOS COMPLETOS — ROI"):
    st.dataframe(roi[["equipe", "participacoes", "conquistados", "max_pos", "roi"]]
                 .rename(columns={"equipe": "EQUIPE", "participacoes": "PARTICIPAÇÕES",
                                  "conquistados": "PTS", "max_pos": "MÁXIMO", "roi": "ROI (%)"}),
                 use_container_width=True, hide_index=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════════════════════════
# ANÁLISE 4 — EVOLUÇÃO
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("## 📉 EVOLUÇÃO DE PERFORMANCE — TENDÊNCIA POR ETAPA")
st.caption("Quem está melhorando? Quem sofreu com mudanças de regulamento?")

top_n = st.slider("TOP N PILOTOS", 3, 10, 6, step=1)
top_p = df.groupby("piloto")["posicao"].mean().sort_values().head(top_n).index.tolist()
df_evo = df[df["piloto"].isin(top_p)].copy()
df_evo["circ"] = (df_evo["circuito"]
                  .str.replace("Autodromo de ", "", regex=False)
                  .str.replace("Autodromo ", "", regex=False))
df_evo = df_evo.sort_values("data")

fig4 = go.Figure()
for piloto in top_p:
    grp = df_evo[df_evo["piloto"] == piloto].sort_values("data")
    eq  = grp["equipe"].iloc[0]
    fig4.add_trace(go.Scatter(
        x=grp["circ"], y=grp["posicao"],
        mode="lines+markers",
        name=f"{piloto}",
        line=dict(color=EQUIPE_CORES.get(eq, "#888"), width=3),
        marker=dict(size=10, symbol="circle"),
        customdata=np.stack([grp["equipe"],
                             grp["posicao_largada"].astype(int),
                             grp["condicoes_pista"]], axis=-1),
        hovertemplate=(
            "<b>%{x}</b><br>"
            f"<b>{piloto}</b><br>"
            "Final: P%{y}<br>"
            "Largada: P%{customdata[1]}<br>"
            "Equipe: %{customdata[0]}<br>"
            "Pista: %{customdata[2]}"
            "<extra></extra>"
        ),
    ))

fig4.update_layout(**PLOTLY_LAYOUT, title="EVOLUÇÃO POR ETAPA", height=450,
                   yaxis_title="POSIÇÃO FINAL",
                   yaxis=dict(autorange="reversed"),
                   hovermode="x unified")
st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════════════════════════
# ANÁLISE 5 — MODELO PREDITIVO + EXPLAINABILITY
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("## 🤖 MODELO PREDITIVO — RANDOM FOREST + EXPLAINABILITY")
st.caption("Previsão de posição final + explicação de cada fator. Ciência de dados aplicada ao grid.")

if len(df) > 20:
    ml_df = df[["posicao_largada", "equipe", "posicao"]].dropna().copy()
    X = pd.get_dummies(ml_df[["posicao_largada", "equipe"]], columns=["equipe"], drop_first=True)
    y = ml_df["posicao"]

    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X, y)

    mae = mean_absolute_error(y, rf.predict(X))

    # Instancia o explainer
    explainer = ModelExplainer(rf, X)

    col_ml1, col_ml2 = st.columns([1, 2])

    with col_ml1:
        st.metric("Erro Médio Absoluto (MAE)", f"{mae:.2f} posições")
        st.write("O modelo erra a posição final em média esse tanto de posições.")

        st.markdown("#### Simular Nova Corrida")
        sim_largada = st.number_input("Posição de Largada", min_value=1, max_value=30, value=5)
        sim_equipe  = st.selectbox("Equipe", sorted(ml_df["equipe"].unique()))

        if st.button("🔮 PREVER POSIÇÃO FINAL"):
            sim_data = pd.DataFrame({"posicao_largada": [sim_largada], "equipe": [sim_equipe]})
            sim_X    = pd.get_dummies(sim_data, columns=["equipe"])
            sim_X    = sim_X.reindex(columns=X.columns, fill_value=0)

            pred = rf.predict(sim_X)[0]
            pos_final = max(1, int(round(pred)))

            st.success(f"**Posição Final Prevista: P{pos_final}**")

            # Explainability — mostra quais fatores influenciaram
            explanation = explainer.explain_prediction(sim_X)
            chart_html  = create_prediction_explanation_chart(explanation)
            st.markdown(chart_html, unsafe_allow_html=True)

            narrative = explainer.get_prediction_narrative(sim_X)
            with st.expander("📖 Entenda a previsão"):
                st.markdown(narrative)

    with col_ml2:
        # Feature importance do modelo completo
        feat_imp = explainer.get_feature_importance(top_n=10)
        feat_imp["feature"] = feat_imp["feature"].str.replace("equipe_", "Eq: ")

        fig5 = go.Figure()
        fig5.add_trace(go.Bar(
            y=feat_imp["feature"],
            x=feat_imp["importance"],
            orientation="h",
            marker_color=["#00D9FF" if i == 0 else "#1A6B8A"
                          for i in range(len(feat_imp))],
            marker_line_width=1,
            marker_line_color="rgba(0,217,255,0.3)",
            text=[f"{v*100:.1f}%" for v in feat_imp["importance"]],
            textposition="outside",
            textfont=dict(color="white", size=10),
            hovertemplate="<b>%{y}</b><br>Importância: %{x:.4f}<extra></extra>",
        ))
        fig5.update_layout(
            **PLOTLY_LAYOUT,
            title="IMPORTÂNCIA DAS FEATURES",
            height=420,
            showlegend=False,
            yaxis=dict(categoryorder="total ascending"),
        )
        st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("⚠️ Dados insuficientes para treinar o modelo. Ajuste os filtros.")

st.markdown("---")

st.markdown("""
<div style="text-align: center; color: #555; margin-top: 40px; font-size: 0.85em;
            font-family: Monaco, monospace;">
    <p>🏎️ <b style="color:#00D9FF">STOCK CAR PERFORMANCE ANALYTICS</b> — Elite Dashboard</p>
    <p>Engineered by someone who understands racing data.</p>
    <p style="margin-top:5px;">Dados públicos — stockcar.com.br / Wikipedia</p>
</div>
""", unsafe_allow_html=True)
