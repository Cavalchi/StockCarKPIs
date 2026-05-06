"""
dashboard/streamlit_app.py
Stock Car KPIs — Dashboard Interativo (Plotly)
Rode com: streamlit run dashboard/streamlit_app.py
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

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Car KPIs Analytics",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

PONTOS = PONTOS_STOCK_CAR

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#0d1117",
    plot_bgcolor="#0d1117",
    font=dict(color="#cccccc", size=12),
    margin=dict(l=30, r=30, t=50, b=30),
    hoverlabel=dict(bgcolor="#1a1a2e", font_size=12, font_color="white"),
)

# ── Helpers ───────────────────────────────────────────────────────────────────
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

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏎️ Filtros")

    df_all = load_resultados()
    temporadas = sorted(df_all["temporada"].dropna().unique().tolist(), reverse=True)
    equipes    = sorted(df_all["equipe"].unique().tolist())
    pilotos    = sorted(df_all["piloto"].unique().tolist())

    sel_temp   = st.multiselect("Temporada",  temporadas, default=temporadas)
    sel_equipe = st.multiselect("Equipe",     equipes,    default=equipes)
    sel_piloto = st.multiselect("Piloto",     pilotos,    default=pilotos)
    st.markdown("---")
    st.caption("Dados: stockcar.com.br / Wikipedia")

# ── Filtra ────────────────────────────────────────────────────────────────────
df = load_resultados()
df = df[df["temporada"].isin(sel_temp) &
        df["equipe"].isin(sel_equipe) &
        df["piloto"].isin(sel_piloto)].copy()

df_p = load_pit_stops()
df_p = df_p[df_p["temporada"].isin(sel_temp) &
            df_p["equipe"].isin(sel_equipe) &
            df_p["piloto"].isin(sel_piloto)].copy()

if df.empty:
    st.warning("Nenhum dado com os filtros selecionados.")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🏎️ Stock Car KPIs Analytics")
st.markdown("Pipeline de Engenharia de Dados aplicada ao motorsport brasileiro.")
st.markdown("---")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Corridas", df["corrida_id"].nunique())
c2.metric("Pilotos",  df["piloto"].nunique())
c3.metric("Equipes",  df["equipe"].nunique())
c4.metric("Pontos distribuidos", int(df["posicao"].map(PONTOS).fillna(0).sum()))
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISE 1 — Consistência
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("📊 Análise 1 — Score de Consistência por Piloto")
st.caption("Desvio padrão das posições finais. Passe o mouse para ver detalhes.")

cons = (df.groupby(["piloto","equipe"])
          .agg(corridas=("posicao","count"),
               media=("posicao","mean"),
               stddev=("posicao","std"),
               melhor=("posicao","min"),
               pior=("posicao","max"))
          .reset_index()
          .query("corridas >= 3")
          .sort_values("stddev", ascending=True))

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    y=cons["piloto"],
    x=cons["stddev"],
    orientation="h",
    marker_color=[EQUIPE_CORES.get(e, "#aaa") for e in cons["equipe"]],
    customdata=np.stack([cons["equipe"], cons["media"].round(2),
                         cons["corridas"], cons["melhor"], cons["pior"]], axis=-1),
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Equipe: %{customdata[0]}<br>"
        "Desvio Padrão: %{x:.2f}<br>"
        "Média: P%{customdata[1]}<br>"
        "Corridas: %{customdata[2]}<br>"
        "Melhor: P%{customdata[3]} | Pior: P%{customdata[4]}"
        "<extra></extra>"
    ),
))
fig1.update_layout(**PLOTLY_LAYOUT,
    title="Score de Consistência — Menor desvio = mais consistente",
    xaxis_title="Desvio Padrão (σ)",
    height=420)
st.plotly_chart(fig1, use_container_width=True)

with st.expander("📋 Ver tabela"):
    st.dataframe(cons.rename(columns={
        "piloto":"Piloto","equipe":"Equipe","corridas":"Corridas",
        "media":"Média Pos","stddev":"Desvio (σ)","melhor":"Melhor","pior":"Pior"
    }), use_container_width=True, hide_index=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISE 2 — Janela Ótima de Pit Stop
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("⏱️ Análise 2 — Janela Ótima de Pit Stop")
st.caption("Volta do pit × ganho de posições. Interaja para explorar os dados.")

if not df_p.empty:
    merged = df_p.merge(
        df[["corrida_id","piloto","posicao","posicao_largada"]],
        on=["corrida_id","piloto"], how="inner")
    merged["ganho"] = merged["posicao_largada"] - merged["posicao"]

    col_a, col_b = st.columns(2)

    with col_a:
        fig2a = px.scatter(
            merged, x="volta", y="ganho", color="equipe",
            color_discrete_map=EQUIPE_CORES,
            hover_data={"piloto":True, "equipe":True, "duracao_s":":.2f",
                        "volta":True, "ganho":True, "circuito":True},
            trendline="ols", trendline_scope="overall",
            labels={"volta":"Volta do Pit","ganho":"Posições Ganhas",
                    "equipe":"Equipe","piloto":"Piloto",
                    "duracao_s":"Duração (s)","circuito":"Circuito"},
        )
        fig2a.update_layout(**PLOTLY_LAYOUT,
            title="Scatter: Volta × Ganho de Posição", height=420,
            legend=dict(font_size=9, bgcolor="rgba(0,0,0,0)"))
        fig2a.add_hline(y=0, line_dash="dash", line_color="#555")
        st.plotly_chart(fig2a, use_container_width=True)

    with col_b:
        merged["faixa"] = pd.cut(merged["volta"], bins=[11,13,15,17,19],
                                 labels=["12-13","13-15","15-17","17-19"])
        agg = (merged.groupby("faixa", observed=True)["ganho"]
                     .agg(["mean","count"]).reset_index())
        agg.columns = ["faixa","ganho_medio","n"]

        fig2b = go.Figure()
        fig2b.add_trace(go.Bar(
            x=agg["faixa"].astype(str),
            y=agg["ganho_medio"],
            marker_color=["#ff4444" if v == agg["ganho_medio"].max() else "#1f77b4"
                          for v in agg["ganho_medio"]],
            text=[f"{v:+.1f} (n={int(n)})" for v, n in zip(agg["ganho_medio"], agg["n"])],
            textposition="outside", textfont=dict(color="white"),
            hovertemplate="Faixa: %{x}<br>Ganho médio: %{y:+.2f}<extra></extra>",
        ))
        fig2b.update_layout(**PLOTLY_LAYOUT,
            title="Ganho Médio por Faixa de Volta",
            xaxis_title="Faixa de Volta", yaxis_title="Ganho Médio",
            height=420)
        fig2b.add_hline(y=0, line_dash="dash", line_color="#555")
        st.plotly_chart(fig2b, use_container_width=True)
else:
    st.info("Sem dados de pit stop para os filtros selecionados.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISE 3 — ROI Esportivo
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("📈 Análise 3 — ROI Esportivo por Equipe")
st.caption("Pontos conquistados / pontos máximos possíveis × 100.")

df["pts"] = df["posicao"].map(PONTOS).fillna(0)
roi = (df.groupby("equipe")
         .agg(conquistados=("pts","sum"), participacoes=("posicao","count"))
         .reset_index())
roi["max_pos"] = roi["participacoes"] * 25
roi["roi"]     = (roi["conquistados"] / roi["max_pos"] * 100).round(1)
roi = roi.sort_values("roi", ascending=False)

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=roi["equipe"], y=roi["roi"],
    marker_color=[EQUIPE_CORES.get(e, "#aaa") for e in roi["equipe"]],
    text=[f"{v:.1f}%" for v in roi["roi"]],
    textposition="outside", textfont=dict(color="white"),
    customdata=np.stack([roi["conquistados"], roi["max_pos"], roi["participacoes"]], axis=-1),
    hovertemplate=(
        "<b>%{x}</b><br>"
        "ROI: %{y:.1f}%<br>"
        "Pontos: %{customdata[0]} / %{customdata[1]}<br>"
        "Participações: %{customdata[2]}"
        "<extra></extra>"
    ),
))
fig3.add_hline(y=50, line_dash="dash", line_color="#ffaa00",
               annotation_text="Referência 50%", annotation_font_color="#ffaa00")
fig3.update_layout(**PLOTLY_LAYOUT,
    title="ROI Esportivo por Equipe",
    yaxis_title="ROI (%)", height=420,
    yaxis=dict(range=[0, roi["roi"].max() * 1.2]))
st.plotly_chart(fig3, use_container_width=True)

with st.expander("📋 Ver tabela de ROI"):
    st.dataframe(roi[["equipe","participacoes","conquistados","max_pos","roi"]]
                   .rename(columns={"equipe":"Equipe","participacoes":"Participações",
                                    "conquistados":"Pts","max_pos":"Máximo","roi":"ROI (%)"}),
                 use_container_width=True, hide_index=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISE 4 — Evolução por Etapa
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("📉 Análise 4 — Evolução de Performance por Etapa")
st.caption("P1 no topo. Passe o mouse para ver detalhes de cada etapa.")

top_n = st.slider("Mostrar top N pilotos", 3, 10, 6)
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
        line=dict(color=EQUIPE_CORES.get(eq, "#aaa"), width=2.5),
        marker=dict(size=9),
        customdata=np.stack([grp["equipe"],
                             grp["posicao_largada"].astype(int),
                             grp["condicoes_pista"]], axis=-1),
        hovertemplate=(
            "<b>%{x}</b><br>"
            f"<b>{piloto}</b><br>"
            "Posição Final: P%{y}<br>"
            "Largada: P%{customdata[1]}<br>"
            "Equipe: %{customdata[0]}<br>"
            "Pista: %{customdata[2]}"
            "<extra></extra>"
        ),
    ))

fig4.update_layout(**PLOTLY_LAYOUT,
    title="Evolução de Performance por Etapa",
    yaxis=dict(title="Posição Final", autorange="reversed",
               dtick=1, gridcolor="#1e1e2e"),
    xaxis=dict(title="Etapa"),
    height=500,
    legend=dict(font_size=10, bgcolor="rgba(0,0,0,0)"))
st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISE 5 — Previsão de Posição (Machine Learning)
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("🤖 Análise 5 — Modelo Preditivo (Random Forest)")
st.caption("Previsão de posição de chegada com base no Grid de Largada e Equipe.")

if len(df) > 20: # Precisa de alguns dados para treinar
    # Preparar dados
    ml_df = df[["posicao_largada", "equipe", "posicao"]].dropna().copy()
    
    # Feature Engineering (One-Hot Encoding para equipe)
    X = pd.get_dummies(ml_df[["posicao_largada", "equipe"]], columns=["equipe"], drop_first=True)
    y = ml_df["posicao"]
    
    # Treinar modelo simples
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X, y)
    
    # Prever no mesmo dataset para demonstrar (idealmente train_test_split, mas aqui é demo)
    ml_df["previsao"] = rf.predict(X).round(1)
    ml_df["erro_absoluto"] = abs(ml_df["posicao"] - ml_df["previsao"])
    
    mae = mean_absolute_error(y, ml_df["previsao"])
    
    col_ml1, col_ml2 = st.columns([1, 2])
    with col_ml1:
        st.metric("Erro Médio Absoluto (MAE)", f"{mae:.2f} posições")
        st.write("Isso significa que o modelo erra a posição final em média por este número de posições.")
        
        # Simular uma nova corrida
        st.markdown("#### Simular Nova Corrida")
        sim_largada = st.number_input("Posição de Largada", min_value=1, max_value=30, value=5)
        sim_equipe = st.selectbox("Equipe", sorted(ml_df["equipe"].unique()))
        
        if st.button("Prever Posição Final"):
            # Criar input simulado
            sim_data = pd.DataFrame({"posicao_largada": [sim_largada], "equipe": [sim_equipe]})
            sim_X = pd.get_dummies(sim_data, columns=["equipe"])
            
            # Garantir as mesmas colunas do treino
            sim_X = sim_X.reindex(columns=X.columns, fill_value=0)
            
            pred = rf.predict(sim_X)[0]
            st.success(f"**Posição Final Prevista:** P{max(1, int(round(pred)))}")
            
    with col_ml2:
        # Importância das features
        feat_imp = pd.DataFrame({
            "Feature": X.columns.str.replace("equipe_", "Eq: "),
            "Importância": rf.feature_importances_
        }).sort_values("Importância", ascending=False).head(10)
        
        fig5 = px.bar(feat_imp, x="Importância", y="Feature", orientation="h",
                      title="Quais fatores o modelo considera mais importantes?")
        fig5.update_layout(**PLOTLY_LAYOUT, yaxis={'categoryorder':'total ascending'}, height=350)
        st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("Dados insuficientes para treinar o modelo de ML. Ajuste os filtros.")

st.markdown("---")
st.caption("Stock Car KPIs Analytics | Dados públicos — stockcar.com.br / Wikipedia")
