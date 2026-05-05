"""
dashboard/streamlit_app.py
Stock Car KPIs — Dashboard Interativo
Rode com: streamlit run dashboard/streamlit_app.py
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
from sqlalchemy import create_engine

# ── Config da página ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Car KPIs Analytics",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_URI = "postgresql://admin:password@localhost:5432/stockcar_kpis"

EQUIPE_CORES = {
    "Eurofarma RC":          "#1f77b4",
    "Ipiranga Racing":       "#ff7f0e",
    "A.Mattheis Vogel":      "#2ca02c",
    "RCM Motorsport":        "#d62728",
    "Full Time Sports":      "#9467bd",
    "Lubrax Podium Stock":   "#8c564b",
    "Red Bull Racing BR":    "#e377c2",
    "Blau Motorsport":       "#7f7f7f",
    "Pole Motorsport":       "#bcbd22",
    "TMG Racing":            "#17becf",
}

PONTOS = {1:25, 2:20, 3:16, 4:13, 5:11, 6:9, 7:7, 8:5, 9:3, 10:1}

# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    return create_engine(DB_URI)

@st.cache_data(ttl=60)
def load_resultados():
    return pd.read_sql("SELECT r.*, c.circuito, c.data, c.condicoes_pista FROM resultados r JOIN corridas c ON r.corrida_id = c.id ORDER BY c.data", get_engine())

@st.cache_data(ttl=60)
def load_pitstops():
    return pd.read_sql("SELECT p.*, c.circuito, c.data FROM pit_stops p JOIN corridas c ON p.corrida_id = c.id ORDER BY c.data", get_engine())

# ── Sidebar / Filtros ─────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Stock_Car_Brasil_logo.png/320px-Stock_Car_Brasil_logo.png", width=200)
    st.title("Filtros")

    df_all = load_resultados()
    temporadas = sorted(df_all["temporada"].dropna().unique().tolist(), reverse=True)
    equipes    = sorted(df_all["equipe"].unique().tolist())
    pilotos    = sorted(df_all["piloto"].unique().tolist())

    sel_temp   = st.multiselect("Temporada", temporadas, default=temporadas)
    sel_equipe = st.multiselect("Equipe", equipes, default=equipes)
    sel_piloto = st.multiselect("Piloto", pilotos, default=pilotos)

    st.markdown("---")
    st.caption("Dados: stockcar.com.br / Wikipedia")

# ── Filtra dados ──────────────────────────────────────────────────────────────
df_res = load_resultados()
df_pit = load_pitstops()

mask = (
    df_res["temporada"].isin(sel_temp) &
    df_res["equipe"].isin(sel_equipe) &
    df_res["piloto"].isin(sel_piloto)
)
df = df_res[mask].copy()
df_p = df_pit[
    df_pit["temporada"].isin(sel_temp) &
    df_pit["equipe"].isin(sel_equipe) &
    df_pit["piloto"].isin(sel_piloto)
].copy()

if df.empty:
    st.warning("Nenhum dado com os filtros selecionados.")
    st.stop()

# ── Cabeçalho ────────────────────────────────────────────────────────────────
st.markdown("# 🏎️ Stock Car KPIs Analytics")
st.markdown("Pipeline de Engenharia de Dados aplicada ao motorsport brasileiro.")
st.markdown("---")

# ── Métricas rápidas ──────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Corridas analisadas", df["corrida_id"].nunique())
c2.metric("Pilotos", df["piloto"].nunique())
c3.metric("Equipes", df["equipe"].nunique())
total_pts = df["posicao"].map(PONTOS).fillna(0).sum()
c4.metric("Total de pontos distribuídos", int(total_pts))

st.markdown("---")

# ── ANÁLISE 1: Consistência ───────────────────────────────────────────────────
st.subheader("📊 Análise 1 — Score de Consistência por Piloto")
st.caption("Desvio padrão das posições finais. Menor = mais consistente.")

cons = (df.groupby(["piloto","equipe"])
          .agg(corridas=("posicao","count"),
               media=("posicao","mean"),
               stddev=("posicao","std"))
          .reset_index()
          .query("corridas >= 3")
          .sort_values("stddev"))

fig1, ax1 = plt.subplots(figsize=(10, 5))
fig1.patch.set_facecolor("#0d1117"); ax1.set_facecolor("#0d1117")
cores = [EQUIPE_CORES.get(e, "#aaa") for e in cons["equipe"]]
ax1.barh(cons["piloto"], cons["stddev"], color=cores, height=0.6)
for _, row in cons.iterrows():
    ax1.text(row["stddev"]+0.04, cons.index.get_loc(_)+0,
             f"  média P{row['media']:.1f}  σ={row['stddev']:.2f}",
             va="center", color="#ccc", fontsize=8)
ax1.set_xlabel("Desvio Padrão (σ)", color="#aaa"); ax1.tick_params(colors="white", labelsize=8)
for sp in ["top","right"]: ax1.spines[sp].set_visible(False)
for sp in ["left","bottom"]: ax1.spines[sp].set_color("#333")
ax1.set_xlim(0, cons["stddev"].max()*1.55)
st.pyplot(fig1, use_container_width=True)
plt.close()

with st.expander("Ver tabela completa"):
    st.dataframe(cons.rename(columns={"piloto":"Piloto","equipe":"Equipe",
                                       "corridas":"Corridas","media":"Média Pos",
                                       "stddev":"Desvio Padrão (σ)"}),
                 use_container_width=True)

st.markdown("---")

# ── ANÁLISE 2: Janela de Pit ──────────────────────────────────────────────────
st.subheader("⏱️ Análise 2 — Janela Ótima de Pit Stop")
st.caption("Volta do pit x ganho de posições. Identifica undercut e overcut.")

if not df_p.empty:
    merged = df_p.merge(df[["corrida_id","piloto","posicao","posicao_largada"]],
                        on=["corrida_id","piloto"], how="inner")
    merged["ganho"] = merged["posicao_largada"] - merged["posicao"]
    merged["faixa"] = pd.cut(merged["volta"], bins=[11,13,15,17,19],
                             labels=["12-13","13-15","15-17","17-19"])
    agg = merged.groupby("faixa", observed=True)["ganho"].agg(["mean","count"]).reset_index()

    fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(13,5))
    fig2.patch.set_facecolor("#0d1117")
    for ax in [ax2a, ax2b]:
        ax.set_facecolor("#0d1117")
        for sp in ["top","right"]: ax.spines[sp].set_visible(False)
        for sp in ["left","bottom"]: ax.spines[sp].set_color("#333")
        ax.tick_params(colors="white", labelsize=8)

    # scatter
    for eq, grp in merged.groupby("equipe"):
        ax2a.scatter(grp["volta"], grp["ganho"], color=EQUIPE_CORES.get(eq,"#aaa"),
                     alpha=0.7, s=50, label=eq)
    coef = np.polyfit(merged["volta"], merged["ganho"], 1)
    xs = np.linspace(merged["volta"].min(), merged["volta"].max(), 80)
    ax2a.plot(xs, np.poly1d(coef)(xs), "--", color="#ff4444", lw=1.5, label="Tendência")
    ax2a.axhline(0, color="#555", lw=0.8)
    ax2a.set_xlabel("Volta do Pit", color="#aaa"); ax2a.set_ylabel("Posições Ganhas", color="#aaa")
    ax2a.set_title("Scatter: Volta x Ganho", color="white", fontsize=10)
    ax2a.legend(fontsize=6, facecolor="#1a1a2e", edgecolor="#333", labelcolor="white", ncol=2)

    # barras faixa
    cores_f = ["#ff4444" if v==agg["mean"].max() else "#1f77b4" for v in agg["mean"]]
    ax2b.bar(agg["faixa"].astype(str), agg["mean"], color=cores_f, width=0.5)
    for _, row in agg.iterrows():
        ax2b.text(list(agg["faixa"].astype(str)).index(str(row["faixa"])),
                  row["mean"]+0.05, f"{row['mean']:+.1f}\n(n={int(row['count'])})",
                  ha="center", color="white", fontsize=9, fontweight="bold")
    ax2b.axhline(0, color="#555", lw=0.8)
    ax2b.set_xlabel("Faixa de Volta", color="#aaa"); ax2b.set_ylabel("Ganho Médio", color="#aaa")
    ax2b.set_title("Ganho Médio por Faixa", color="white", fontsize=10)

    st.pyplot(fig2, use_container_width=True)
    plt.close()
else:
    st.info("Sem dados de pit stop para os filtros selecionados.")

st.markdown("---")

# ── ANÁLISE 3: ROI Esportivo ──────────────────────────────────────────────────
st.subheader("📈 Análise 3 — ROI Esportivo por Equipe")
st.caption("Pontos conquistados / pontos máximos possíveis × 100.")

df["pts"] = df["posicao"].map(PONTOS).fillna(0)
roi = (df.groupby("equipe")
         .agg(conquistados=("pts","sum"), participacoes=("posicao","count"))
         .reset_index())
roi["max_pos"] = roi["participacoes"] * 25
roi["roi"]     = (roi["conquistados"] / roi["max_pos"] * 100).round(1)
roi = roi.sort_values("roi", ascending=False)

fig3, ax3 = plt.subplots(figsize=(10,5))
fig3.patch.set_facecolor("#0d1117"); ax3.set_facecolor("#0d1117")
cores3 = [EQUIPE_CORES.get(e,"#aaa") for e in roi["equipe"]]
ax3.bar(roi["equipe"], roi["roi"], color=cores3, width=0.55)
ax3.axhline(50, color="#ffaa00", lw=1.2, ls="--", alpha=0.7, label="Ref. 50%")
for _, row in roi.iterrows():
    ax3.text(list(roi["equipe"]).index(row["equipe"]), row["roi"]+0.4,
             f"{row['roi']:.1f}%", ha="center", color="white", fontsize=8.5, fontweight="bold")
ax3.set_ylabel("ROI (%)", color="#aaa"); ax3.tick_params(colors="white", labelsize=8, axis="x", rotation=25)
ax3.tick_params(colors="white", labelsize=9, axis="y")
for sp in ["top","right"]: ax3.spines[sp].set_visible(False)
for sp in ["left","bottom"]: ax3.spines[sp].set_color("#333")
ax3.legend(fontsize=9, facecolor="#1a1a2e", edgecolor="#333", labelcolor="white")
st.pyplot(fig3, use_container_width=True)
plt.close()

with st.expander("Ver tabela de ROI"):
    st.dataframe(roi[["equipe","participacoes","conquistados","max_pos","roi"]]
                   .rename(columns={"equipe":"Equipe","participacoes":"Participações",
                                    "conquistados":"Pts Conquistados",
                                    "max_pos":"Pts Máximos","roi":"ROI (%)"}),
                 use_container_width=True)

st.markdown("---")

# ── ANÁLISE 4: Evolução ───────────────────────────────────────────────────────
st.subheader("📉 Análise 4 — Evolução de Performance por Etapa")
st.caption("Posição final por etapa. P1 no topo.")

top_p = (df.groupby("piloto")["posicao"].mean().sort_values().head(8).index.tolist())
df_evo = df[df["piloto"].isin(top_p)].copy()
df_evo["circ"] = df_evo["circuito"].str.replace("Autodromo de ","",regex=False).str.replace("Autodromo ","",regex=False)

fig4, ax4 = plt.subplots(figsize=(13,6))
fig4.patch.set_facecolor("#0d1117"); ax4.set_facecolor("#0d1117")
for piloto, grp in df_evo.groupby("piloto"):
    grp = grp.sort_values("data")
    eq  = grp["equipe"].iloc[0]
    cor = EQUIPE_CORES.get(eq,"#aaa")
    ax4.plot(grp["circ"], grp["posicao"], marker="o", lw=2, ms=7, color=cor, label=f"{piloto}")
    ult = grp.iloc[-1]
    ax4.annotate(f" P{int(ult['posicao'])}", (ult["circ"], ult["posicao"]), color=cor, fontsize=7.5)
ax4.invert_yaxis()
ax4.yaxis.set_major_locator(mticker.MultipleLocator(1))
ax4.set_ylabel("Posição Final", color="#aaa"); ax4.set_xlabel("Etapa", color="#aaa")
ax4.tick_params(colors="white", labelsize=8, axis="x", rotation=30)
ax4.tick_params(colors="white", labelsize=9, axis="y")
for sp in ["top","right"]: ax4.spines[sp].set_visible(False)
for sp in ["left","bottom"]: ax4.spines[sp].set_color("#333")
ax4.grid(axis="y", color="#1e1e2e", lw=0.7)
ax4.legend(fontsize=8, facecolor="#1a1a2e", edgecolor="#333", labelcolor="white", ncol=2)
st.pyplot(fig4, use_container_width=True)
plt.close()

st.markdown("---")
st.caption("Stock Car KPIs Analytics | Dados públicos — stockcar.com.br / Wikipedia")
