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

# ── Design Tokens ─────────────────────────────────────────────────────────────
BG_PAGE   = "#080810"
BG_CARD   = "#0F0F1A"
BG_PANEL  = "#14141F"
RED       = "#E63946"
GOLD      = "#F4A261"
TEAL      = "#2EC4B6"
WHITE     = "#F0F0F0"
GRAY      = "#8B8B9E"
GRAYL     = "#C8C8D8"

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor=BG_CARD,
    plot_bgcolor=BG_CARD,
    font=dict(family="'DM Mono', monospace", color=GRAYL, size=11),
    margin=dict(l=40, r=40, t=52, b=40),
    hoverlabel=dict(bgcolor="#1A1A2E", font_size=12, font_color=WHITE,
                    bordercolor=RED),
    xaxis=dict(gridcolor="#1E1E30", zerolinecolor="#1E1E30"),
    yaxis=dict(gridcolor="#1E1E30", zerolinecolor="#1E1E30"),
)

# ── CSS Global ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Barlow+Condensed:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');

/* Reset e base */
html, body, [class*="css"] {
    background-color: #080810 !important;
    color: #C8C8D8;
    font-family: 'Inter', sans-serif;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #080810; }
::-webkit-scrollbar-thumb { background: #E63946; border-radius: 3px; }

/* Header Hero */
.hero-wrapper {
    background: linear-gradient(135deg, #080810 0%, #0F0F1A 50%, #080810 100%);
    border: 1px solid #1E1E30;
    border-top: 3px solid #E63946;
    border-radius: 0 0 4px 4px;
    padding: 32px 40px 28px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.hero-wrapper::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 300px; height: 100%;
    background: repeating-linear-gradient(
        -45deg,
        transparent,
        transparent 8px,
        rgba(230, 57, 70, 0.04) 8px,
        rgba(230, 57, 70, 0.04) 16px
    );
}
.hero-tag {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: #E63946;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.hero-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 52px;
    font-weight: 800;
    color: #F0F0F0;
    line-height: 1;
    letter-spacing: -1px;
    margin-bottom: 8px;
}
.hero-title span { color: #E63946; }
.hero-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: #8B8B9E;
    letter-spacing: 0.5px;
}

/* KPI Cards */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 32px;
}
.kpi-card {
    background: #0F0F1A;
    border: 1px solid #1E1E30;
    border-left: 3px solid #E63946;
    border-radius: 4px;
    padding: 18px 20px;
    position: relative;
}
.kpi-card.gold { border-left-color: #F4A261; }
.kpi-card.teal { border-left-color: #2EC4B6; }
.kpi-card.white { border-left-color: #8B8B9E; }
.kpi-label {
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    color: #8B8B9E;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.kpi-value {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 38px;
    font-weight: 700;
    color: #F0F0F0;
    line-height: 1;
}
.kpi-card.gold .kpi-value { color: #F4A261; }
.kpi-card.teal .kpi-value { color: #2EC4B6; }

/* Section headers */
.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 32px 0 4px;
    padding-bottom: 12px;
    border-bottom: 1px solid #1E1E30;
}
.section-num {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: #E63946;
    background: rgba(230, 57, 70, 0.1);
    border: 1px solid rgba(230, 57, 70, 0.3);
    padding: 2px 8px;
    border-radius: 2px;
    letter-spacing: 2px;
}
.section-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: #F0F0F0;
    letter-spacing: 0.5px;
}
.section-caption {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: #8B8B9E;
    margin-bottom: 20px;
    letter-spacing: 0.5px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0A0A14 !important;
    border-right: 1px solid #1E1E30;
}
section[data-testid="stSidebar"] .stMultiSelect > div > div {
    background: #0F0F1A !important;
    border-color: #2A2A40 !important;
}

/* Chart containers */
.chart-container {
    background: #0F0F1A;
    border: 1px solid #1E1E30;
    border-radius: 4px;
    padding: 4px;
    margin-bottom: 16px;
}

/* ML Section */
.ml-card {
    background: #0F0F1A;
    border: 1px solid #1E1E30;
    border-top: 2px solid #2EC4B6;
    border-radius: 4px;
    padding: 20px;
}
.ml-metric {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 42px;
    font-weight: 700;
    color: #2EC4B6;
}
.ml-metric-label {
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    color: #8B8B9E;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 4px;
}

/* Divider */
.race-divider {
    height: 1px;
    background: linear-gradient(90deg, #E63946, transparent);
    margin: 24px 0;
    opacity: 0.4;
}

/* Flag pattern footer */
.flag-footer {
    margin-top: 40px;
    padding: 16px 0;
    border-top: 1px solid #1E1E30;
    display: flex;
    align-items: center;
    gap: 12px;
}
.flag-pattern {
    display: grid;
    grid-template-columns: repeat(4, 10px);
    grid-template-rows: repeat(2, 10px);
    gap: 1px;
}
.flag-sq { width: 10px; height: 10px; }
.flag-sq.b { background: #1A1A2A; }
.flag-sq.w { background: #8B8B9E; }

/* Expander */
.streamlit-expanderHeader {
    background: #0F0F1A !important;
    border: 1px solid #1E1E30 !important;
    border-radius: 4px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
    color: #8B8B9E !important;
}

/* Buttons */
.stButton button {
    background: #E63946 !important;
    color: white !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    padding: 8px 20px !important;
}
.stButton button:hover {
    background: #C62D3A !important;
    transform: translateY(-1px);
}

/* Metrics override */
[data-testid="metric-container"] {
    background: #0F0F1A;
    border: 1px solid #1E1E30;
    border-radius: 4px;
    padding: 12px 16px;
}

/* Success box */
.stSuccess {
    background: rgba(46, 196, 182, 0.1) !important;
    border: 1px solid rgba(46, 196, 182, 0.3) !important;
    border-radius: 4px !important;
    color: #2EC4B6 !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 18px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

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
    st.markdown("""
    <div style='padding: 8px 0 16px;'>
        <div style='font-family: Barlow Condensed, sans-serif; font-size: 20px;
                    font-weight: 700; color: #E63946; letter-spacing: 1px;'>
            FILTROS
        </div>
        <div style='font-family: DM Mono, monospace; font-size: 9px;
                    color: #8B8B9E; letter-spacing: 2px;'>
            REFINE OS DADOS
        </div>
    </div>
    """, unsafe_allow_html=True)

    df_all = load_resultados()
    temporadas = sorted(df_all["temporada"].dropna().unique().tolist(), reverse=True)
    equipes    = sorted(df_all["equipe"].unique().tolist())
    pilotos    = sorted(df_all["piloto"].unique().tolist())

    sel_temp   = st.multiselect("Temporada",  temporadas, default=temporadas)
    sel_equipe = st.multiselect("Equipe",     equipes,    default=equipes)
    sel_piloto = st.multiselect("Piloto",     pilotos,    default=pilotos)

    st.markdown("<div class='race-divider'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-family: DM Mono, monospace; font-size: 9px;
                color: #8B8B9E; letter-spacing: 1px; line-height: 1.8;'>
        FONTE<br>
        <span style='color: #E63946;'>stockcar.com.br</span><br>
        <span style='color: #E63946;'>wikipedia.org</span>
    </div>
    """, unsafe_allow_html=True)

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

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrapper">
    <div class="hero-tag">▶ ENGENHARIA DE DADOS APLICADA AO MOTORSPORT</div>
    <div class="hero-title">STOCK CAR <span>KPIs</span></div>
    <div class="hero-subtitle">
        PIPELINE DE DADOS · ANÁLISE COMPETITIVA · INTELIGÊNCIA ESTRATÉGICA · BRASIL
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
n_corridas  = df["corrida_id"].nunique()
n_pilotos   = df["piloto"].nunique()
n_equipes   = df["equipe"].nunique()
n_pontos    = int(df["posicao"].map(PONTOS).fillna(0).sum())

st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card">
        <div class="kpi-label">CORRIDAS</div>
        <div class="kpi-value">{n_corridas}</div>
    </div>
    <div class="kpi-card gold">
        <div class="kpi-label">PILOTOS</div>
        <div class="kpi-value">{n_pilotos}</div>
    </div>
    <div class="kpi-card teal">
        <div class="kpi-label">EQUIPES</div>
        <div class="kpi-value">{n_equipes}</div>
    </div>
    <div class="kpi-card white">
        <div class="kpi-label">PONTOS DISTRIBUÍDOS</div>
        <div class="kpi-value">{n_pontos:,}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISE 1 — Consistência
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-header">
    <span class="section-num">01</span>
    <span class="section-title">SCORE DE CONSISTÊNCIA</span>
</div>
<div class="section-caption">
    DESVIO PADRÃO DAS POSIÇÕES FINAIS · MENOR = MAIS CONSISTENTE · MÍNIMO 3 CORRIDAS
</div>
""", unsafe_allow_html=True)

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
    marker=dict(
        color=[EQUIPE_CORES.get(e, GRAY) for e in cons["equipe"]],
        line=dict(color="rgba(0,0,0,0)", width=0),
    ),
    customdata=np.stack([cons["equipe"], cons["media"].round(2),
                         cons["corridas"], cons["melhor"], cons["pior"]], axis=-1),
    hovertemplate=(
        "<b style='font-size:14px'>%{y}</b><br>"
        "<span style='color:#8B8B9E'>Equipe:</span> %{customdata[0]}<br>"
        "<span style='color:#8B8B9E'>Desvio Padrão:</span> <b>%{x:.2f}σ</b><br>"
        "<span style='color:#8B8B9E'>Média:</span> P%{customdata[1]}<br>"
        "<span style='color:#8B8B9E'>Corridas:</span> %{customdata[2]}<br>"
        "<span style='color:#8B8B9E'>Melhor / Pior:</span> P%{customdata[3]} / P%{customdata[4]}"
        "<extra></extra>"
    ),
))
fig1.update_layout(
    **PLOTLY_LAYOUT,
    title=dict(text="Consistência por Piloto — Temporada Selecionada",
               font=dict(family="Barlow Condensed, sans-serif", size=16, color=WHITE)),
    xaxis_title="Desvio Padrão (σ)",
    height=max(380, len(cons) * 22),
    showlegend=False,
)
fig1.update_layout(
    xaxis=dict(gridcolor="#1A1A28", zerolinecolor="#E63946", zerolinewidth=1),
    yaxis=dict(gridcolor="#1A1A28"),
)
st.plotly_chart(fig1, use_container_width=True)

with st.expander("↓  Ver tabela completa"):
    st.dataframe(
        cons.rename(columns={
            "piloto":"Piloto","equipe":"Equipe","corridas":"Corridas",
            "media":"Média","stddev":"Desvio σ","melhor":"Melhor","pior":"Pior"
        }).style.format({"Média": "{:.1f}", "Desvio σ": "{:.2f}"}),
        use_container_width=True, hide_index=True
    )

st.markdown("<div class='race-divider'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISE 2 — Janela Ótima de Pit Stop
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-header">
    <span class="section-num">02</span>
    <span class="section-title">JANELA ÓTIMA DE PIT STOP</span>
</div>
<div class="section-caption">
    VOLTA DO PIT × GANHO DE POSIÇÕES · IDENTIFICA UNDERCUT E OVERCUT MAIS EFICAZES
</div>
""", unsafe_allow_html=True)

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
            hover_data={"piloto":True,"equipe":True,"duracao_s":":.2f",
                        "volta":True,"ganho":True,"circuito":True},
            trendline="ols", trendline_scope="overall",
            labels={"volta":"Volta","ganho":"Posições Ganhas","equipe":"Equipe"},
        )
        fig2a.update_traces(marker=dict(size=8, opacity=0.85,
                            line=dict(color="#080810", width=0.5)))
        fig2a.update_layout(
            **PLOTLY_LAYOUT,
            title=dict(text="Scatter: Volta × Ganho de Posição",
                       font=dict(family="Barlow Condensed, sans-serif", size=15, color=WHITE)),
            height=400,
            legend=dict(font_size=9, bgcolor="rgba(0,0,0,0)",
                        bordercolor="#1E1E30", borderwidth=1),
        )
        fig2a.add_hline(y=0, line_dash="dot", line_color=GRAY, line_width=1)
        fig2a.add_vline(x=merged["volta"].median(), line_dash="dot",
                        line_color=RED, line_width=1,
                        annotation_text="Mediana", annotation_font_color=RED,
                        annotation_font_size=9)
        st.plotly_chart(fig2a, use_container_width=True)

    with col_b:
        merged["faixa"] = pd.cut(merged["volta"], bins=[11,13,15,17,19],
                                 labels=["12–13","13–15","15–17","17–19"])
        agg = (merged.groupby("faixa", observed=True)["ganho"]
                     .agg(["mean","count"]).reset_index())
        agg.columns = ["faixa","ganho_medio","n"]

        cores_bar = [RED if v == agg["ganho_medio"].max() else "#2A2A40"
                     for v in agg["ganho_medio"]]

        fig2b = go.Figure()
        fig2b.add_trace(go.Bar(
            x=agg["faixa"].astype(str),
            y=agg["ganho_medio"],
            marker=dict(color=cores_bar, line=dict(color="rgba(0,0,0,0)", width=0)),
            text=[f"{v:+.1f}  (n={int(n)})" for v,n in zip(agg["ganho_medio"], agg["n"])],
            textposition="outside",
            textfont=dict(color=WHITE, family="DM Mono, monospace", size=11),
            hovertemplate="Faixa: %{x}<br>Ganho médio: %{y:+.2f}<extra></extra>",
        ))
        fig2b.update_layout(
            **PLOTLY_LAYOUT,
            title=dict(text="Ganho Médio por Janela de Pit",
                       font=dict(family="Barlow Condensed, sans-serif", size=15, color=WHITE)),
            xaxis_title="Janela (voltas)", yaxis_title="Ganho Médio (posições)",
            height=400,
        )
        fig2b.add_hline(y=0, line_dash="dot", line_color=GRAY, line_width=1)
        st.plotly_chart(fig2b, use_container_width=True)
else:
    st.info("Sem dados de pit stop para os filtros selecionados.")

st.markdown("<div class='race-divider'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISE 3 — ROI Esportivo
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-header">
    <span class="section-num">03</span>
    <span class="section-title">ROI ESPORTIVO POR EQUIPE</span>
</div>
<div class="section-caption">
    (PONTOS CONQUISTADOS / PONTOS MÁXIMOS POSSÍVEIS) × 100 · EFICIÊNCIA REAL, NÃO APENAS VITÓRIAS
</div>
""", unsafe_allow_html=True)

df["pts"] = df["posicao"].map(PONTOS).fillna(0)
roi = (df.groupby("equipe")
         .agg(conquistados=("pts","sum"), participacoes=("posicao","count"))
         .reset_index())
roi["max_pos"] = roi["participacoes"] * 25
roi["roi"]     = (roi["conquistados"] / roi["max_pos"] * 100).round(1)
roi = roi.sort_values("roi", ascending=False)

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=roi["equipe"],
    y=roi["roi"],
    marker=dict(
        color=[EQUIPE_CORES.get(e, GRAY) for e in roi["equipe"]],
        line=dict(color="rgba(0,0,0,0)", width=0),
    ),
    text=[f"{v:.1f}%" for v in roi["roi"]],
    textposition="outside",
    textfont=dict(color=WHITE, family="DM Mono, monospace", size=11),
    customdata=np.stack([roi["conquistados"], roi["max_pos"], roi["participacoes"]], axis=-1),
    hovertemplate=(
        "<b>%{x}</b><br>"
        "ROI: <b>%{y:.1f}%</b><br>"
        "Pontos: %{customdata[0]} / %{customdata[1]}<br>"
        "Participações: %{customdata[2]}"
        "<extra></extra>"
    ),
))
fig3.add_hline(y=50, line_dash="dot", line_color=GOLD, line_width=1.5,
               annotation_text="Referência 50%",
               annotation_font=dict(color=GOLD, size=10, family="DM Mono, monospace"))
fig3.update_layout(
    **PLOTLY_LAYOUT,
    title=dict(text="ROI Esportivo — Eficiência por Equipe",
               font=dict(family="Barlow Condensed, sans-serif", size=16, color=WHITE)),
    height=420,
)
fig3.update_layout(
    yaxis=dict(title="ROI (%)", range=[0, roi["roi"].max() * 1.18],
               gridcolor="#1A1A28"),
    xaxis=dict(gridcolor="#1A1A28"),
)
st.plotly_chart(fig3, use_container_width=True)

with st.expander("↓  Ver tabela de ROI"):
    st.dataframe(
        roi[["equipe","participacoes","conquistados","max_pos","roi"]]
          .rename(columns={"equipe":"Equipe","participacoes":"Participações",
                           "conquistados":"Pts","max_pos":"Máximo","roi":"ROI %"})
          .style.format({"ROI %": "{:.1f}"}),
        use_container_width=True, hide_index=True
    )

st.markdown("<div class='race-divider'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISE 4 — Evolução por Etapa
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-header">
    <span class="section-num">04</span>
    <span class="section-title">EVOLUÇÃO DE PERFORMANCE</span>
</div>
<div class="section-caption">
    POSIÇÃO FINAL POR ETAPA · P1 NO TOPO · TENDÊNCIAS DE DESENVOLVIMENTO E QUEDA
</div>
""", unsafe_allow_html=True)

top_n = st.slider("Pilotos exibidos", 3, 12, 6,
                  help="Selecione quantos pilotos mostrar no gráfico")
top_p = df.groupby("piloto")["posicao"].mean().sort_values().head(top_n).index.tolist()
df_evo = df[df["piloto"].isin(top_p)].copy()
df_evo["circ"] = (df_evo["circuito"]
                  .str.replace("Autodromo de ","",regex=False)
                  .str.replace("Autodromo ","",regex=False))
df_evo = df_evo.sort_values("data")

fig4 = go.Figure()
for piloto in top_p:
    grp = df_evo[df_evo["piloto"]==piloto].sort_values("data")
    eq  = grp["equipe"].iloc[0]
    cor = EQUIPE_CORES.get(eq, GRAY)
    fig4.add_trace(go.Scatter(
        x=grp["circ"], y=grp["posicao"],
        mode="lines+markers",
        name=piloto,
        line=dict(color=cor, width=2.5, shape="spline"),
        marker=dict(size=9, color=cor,
                    line=dict(color=BG_PAGE, width=2)),
        customdata=np.stack([grp["equipe"],
                             grp["posicao_largada"].astype(int),
                             grp["condicoes_pista"]], axis=-1),
        hovertemplate=(
            f"<b>{piloto}</b><br>"
            "<span style='color:#8B8B9E'>Etapa:</span> %{x}<br>"
            "<span style='color:#8B8B9E'>Chegada:</span> <b>P%{y}</b><br>"
            "<span style='color:#8B8B9E'>Largada:</span> P%{customdata[1]}<br>"
            "<span style='color:#8B8B9E'>Equipe:</span> %{customdata[0]}<br>"
            "<span style='color:#8B8B9E'>Pista:</span> %{customdata[2]}"
            "<extra></extra>"
        ),
    ))

fig4.update_layout(
    **PLOTLY_LAYOUT,
    title=dict(text="Evolução de Performance — Etapa a Etapa",
               font=dict(family="Barlow Condensed, sans-serif", size=16, color=WHITE)),
    height=500,
    legend=dict(font=dict(size=11, family="Inter, sans-serif"),
                bgcolor="rgba(0,0,0,0)", bordercolor="#1E1E30", borderwidth=1),
)
fig4.update_layout(
    yaxis=dict(title="Posição Final", autorange="reversed", dtick=1,
               gridcolor="#1A1A28"),
    xaxis=dict(title="Etapa", gridcolor="#1A1A28"),
)
st.plotly_chart(fig4, use_container_width=True)

st.markdown("<div class='race-divider'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISE 5 — Machine Learning
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-header">
    <span class="section-num">05</span>
    <span class="section-title">MODELO PREDITIVO — RANDOM FOREST</span>
</div>
<div class="section-caption">
    PREVISÃO DE POSIÇÃO FINAL · GRID DE LARGADA + EQUIPE · RANDOM FOREST REGRESSOR
</div>
""", unsafe_allow_html=True)

if len(df) > 20:
    ml_df = df[["posicao_largada","equipe","posicao"]].dropna().copy()
    X = pd.get_dummies(ml_df[["posicao_largada","equipe"]], columns=["equipe"], drop_first=True)
    y = ml_df["posicao"]

    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X, y)
    ml_df["previsao"] = rf.predict(X).round(1)
    mae = mean_absolute_error(y, ml_df["previsao"])

    col_ml1, col_ml2 = st.columns([1, 2])

    with col_ml1:
        st.markdown(f"""
        <div class="ml-card">
            <div class="ml-metric">±{mae:.2f}</div>
            <div class="ml-metric-label">ERRO MÉDIO ABSOLUTO (MAE)</div>
            <p style='font-size:12px; color:#8B8B9E; margin-top:12px; line-height:1.6;'>
                O modelo erra a posição final em média <b style='color:#2EC4B6'>{mae:.2f} posições</b>.
                Treinado com histórico real da Stock Car Brasil.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='font-family: Barlow Condensed, sans-serif; font-size: 16px;
                    font-weight: 700; color: #F0F0F0; letter-spacing: 0.5px;
                    margin-bottom: 12px;'>
            SIMULAR CORRIDA
        </div>
        """, unsafe_allow_html=True)

        sim_largada = st.number_input("Grid de largada", min_value=1, max_value=30, value=5)
        sim_equipe  = st.selectbox("Equipe", sorted(ml_df["equipe"].unique()))

        if st.button("▶  PREVER POSIÇÃO FINAL"):
            sim_data = pd.DataFrame({"posicao_largada":[sim_largada],"equipe":[sim_equipe]})
            sim_X    = pd.get_dummies(sim_data, columns=["equipe"])
            sim_X    = sim_X.reindex(columns=X.columns, fill_value=0)
            pred     = rf.predict(sim_X)[0]
            pos      = max(1, int(round(pred)))
            st.success(f"🏁  Posição prevista: P{pos}")

    with col_ml2:
        feat_imp = pd.DataFrame({
            "Feature":    X.columns.str.replace("equipe_","Equipe: "),
            "Importância": rf.feature_importances_
        }).sort_values("Importância", ascending=False).head(10)

        fig5 = go.Figure()
        fig5.add_trace(go.Bar(
            x=feat_imp["Importância"],
            y=feat_imp["Feature"],
            orientation="h",
            marker=dict(
                color=[RED if i == 0 else "#2A2A40"
                       for i in range(len(feat_imp))],
                line=dict(color="rgba(0,0,0,0)", width=0),
            ),
            hovertemplate="%{y}: <b>%{x:.3f}</b><extra></extra>",
        ))
        fig5.update_layout(
            **PLOTLY_LAYOUT,
            title=dict(text="Importância das Features — O que o modelo prioriza",
                       font=dict(family="Barlow Condensed, sans-serif", size=15, color=WHITE)),
            height=380,
        )
        fig5.update_layout(
            yaxis=dict(categoryorder="total ascending"),
        )
        st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("Dados insuficientes para treinar o modelo. Ajuste os filtros.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='margin-top: 48px; padding: 20px 0 8px;
            border-top: 1px solid #1E1E30;
            display: flex; align-items: center; gap: 16px;'>
    <div style='font-family: Barlow Condensed, sans-serif; font-size: 18px;
                font-weight: 700; color: #E63946;'>
        STOCK CAR KPIs
    </div>
    <div style='font-family: DM Mono, monospace; font-size: 9px;
                color: #8B8B9E; letter-spacing: 2px;'>
        DADOS PÚBLICOS · STOCKCAR.COM.BR · WIKIPEDIA
    </div>
    <div style='margin-left: auto; font-family: DM Mono, monospace;
                font-size: 9px; color: #8B8B9E; letter-spacing: 1px;'>
        github.com/Cavalchi
    </div>
</div>
""", unsafe_allow_html=True)