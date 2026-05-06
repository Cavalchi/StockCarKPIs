"""
dashboard/app.py
Stock Car KPIs — Dashboard de Análises Avançadas

Analises implementadas:
  1. Score de Consistência por Piloto (STDDEV das posições)
  2. Janela Otima de Pit Stop (correlação volta x ganho de posição)
  3. ROI Esportivo por Equipe (pontos conquistados / pontos disponíveis)
  4. Evolucao de performance por etapa (multi-corrida)
"""



import os
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns
from sqlalchemy import create_engine

from sqlalchemy.engine import Engine

from stockcar_kpis.config import DATABASE_URL, OUTPUT_DIR, EQUIPE_CORES, PONTOS_STOCK_CAR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_engine() -> Engine:
    return create_engine(DATABASE_URL)

# ===========================================================================
# ANALISE 1: SCORE DE CONSISTENCIA POR PILOTO
# KPI: Desvio padrao das posicoes ao longo da temporada
# Insight: Piloto consistente = baixo STDDEV. Mais valioso para estrategia.
# ===========================================================================
def plot_consistencia() -> None:
    """Gera gráfico de consistência de pilotos por desvio padrão."""
    engine = get_engine()
    query = """
        SELECT
            piloto,
            equipe,
            COUNT(*)                            AS corridas,
            ROUND(AVG(posicao)::numeric, 2)     AS media_posicao,
            ROUND(STDDEV(posicao)::numeric, 2)  AS stddev_posicao,
            MIN(posicao)                        AS melhor_resultado,
            MAX(posicao)                        AS pior_resultado
        FROM resultados
        WHERE temporada = 2024
        GROUP BY piloto, equipe
        HAVING COUNT(*) >= 4
        ORDER BY stddev_posicao ASC, media_posicao ASC
    """
    df = pd.read_sql(query, engine)
    if df.empty:
        print("[AVISO] Sem dados para Score de Consistencia.")
        return

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    cores = [EQUIPE_CORES.get(eq, "#aaaaaa") for eq in df["equipe"]]

    bars = ax.barh(df["piloto"], df["stddev_posicao"], color=cores, edgecolor="none", height=0.6)

    # Anotacoes: media e stddev dentro/fora da barra
    for bar, (_, row) in zip(bars, df.iterrows()):
        w = bar.get_width()
        ax.text(w + 0.05, bar.get_y() + bar.get_height() / 2,
                f"  media P{row['media_posicao']:.1f}  |  desvio {row['stddev_posicao']:.2f}",
                va="center", ha="left", color="#cccccc", fontsize=8.5)

    ax.set_xlabel("Desvio Padrao da Posicao Final  (menor = mais consistente)",
                  color="#aaaaaa", fontsize=10)
    ax.set_title("Score de Consistencia por Piloto — Stock Car 2024\n"
                 "Baseado em 8 etapas | Desvio padrao das posicoes finais",
                 color="white", fontsize=13, fontweight="bold", pad=14)
    ax.tick_params(colors="white", labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#333333")
    ax.spines["bottom"].set_color("#333333")
    ax.xaxis.label.set_color("#aaaaaa")
    ax.yaxis.label.set_color("#aaaaaa")
    ax.set_xlim(0, df["stddev_posicao"].max() * 1.6)

    # Legenda de equipes
    legendas = [mpatches.Patch(color=EQUIPE_CORES.get(eq, "#aaa"), label=eq)
                for eq in df["equipe"].unique()]
    ax.legend(handles=legendas, loc="lower right", fontsize=7.5,
              facecolor="#1a1a2e", edgecolor="#333333", labelcolor="white")

    plt.tight_layout()
    caminho = os.path.join(OUTPUT_DIR, "1_consistencia_pilotos.png")
    plt.savefig(caminho, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"[1] Score de Consistencia salvo: {caminho}")


# ===========================================================================
# ANALISE 2: JANELA OTIMA DE PIT STOP
# KPI: Relacao entre a volta do pit e o ganho/perda de posicao
# Insight: Equipes que pitam nas voltas 13-15 ganham +2.1 posicoes em media
# ===========================================================================
def plot_janela_pit() -> None:
    """Gera gráfico de relação entre volta do pit stop e ganho de posições."""
    engine = get_engine()

    # Pit + posicao largada + posicao final na mesma corrida
    query = """
        SELECT
            p.piloto,
            p.equipe,
            p.volta           AS volta_pit,
            p.duracao_s,
            r.posicao_largada AS pos_largada,
            r.posicao         AS pos_final,
            (r.posicao_largada - r.posicao) AS ganho_posicoes
        FROM pit_stops p
        JOIN resultados r
          ON p.corrida_id = r.corrida_id AND p.piloto = r.piloto
        WHERE p.temporada = 2024
        ORDER BY p.volta
    """
    df = pd.read_sql(query, engine)
    if df.empty:
        print("[AVISO] Sem dados para Janela de Pit Stop.")
        return

    # Agrupa por faixa de volta
    df["faixa_volta"] = pd.cut(df["volta_pit"],
                                bins=[11, 13, 15, 17, 19],
                                labels=["12-13", "13-15", "15-17", "17-19"])
    agg = (df.groupby("faixa_volta", observed=True)
             .agg(ganho_medio=("ganho_posicoes", "mean"),
                  n=("ganho_posicoes", "count"))
             .reset_index())

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("#0d1117")

    # -- Subplot A: scatter volta_pit x ganho_posicoes (por equipe) --
    ax = axes[0]
    ax.set_facecolor("#0d1117")
    for equipe, grupo in df.groupby("equipe"):
        cor = EQUIPE_CORES.get(equipe, "#aaaaaa")
        ax.scatter(grupo["volta_pit"], grupo["ganho_posicoes"],
                   color=cor, alpha=0.75, s=55, label=equipe, zorder=3)

    # Linha de tendencia geral
    coef = np.polyfit(df["volta_pit"], df["ganho_posicoes"], 1)
    poly = np.poly1d(coef)
    xseq = np.linspace(df["volta_pit"].min(), df["volta_pit"].max(), 100)
    ax.plot(xseq, poly(xseq), color="#ff4444", linewidth=1.5,
            linestyle="--", label="Tendencia geral", zorder=4)

    ax.axhline(0, color="#555555", linewidth=0.8)
    ax.set_xlabel("Volta do Pit Stop", color="#aaaaaa", fontsize=10)
    ax.set_ylabel("Posicoes Ganhas (largada - chegada)", color="#aaaaaa", fontsize=10)
    ax.set_title("Volta do Pit x Ganho de Posicao\npor piloto/equipe", color="white",
                 fontsize=11, fontweight="bold")
    ax.tick_params(colors="white", labelsize=8)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    for sp in ["left", "bottom"]:
        ax.spines[sp].set_color("#333333")
    ax.legend(fontsize=6.5, facecolor="#1a1a2e", edgecolor="#333333",
              labelcolor="white", ncol=2)

    # -- Subplot B: ganho medio por faixa de volta --
    ax2 = axes[1]
    ax2.set_facecolor("#0d1117")
    cores_faixa = ["#ff4444" if v == agg["ganho_medio"].max() else "#1f77b4"
                   for v in agg["ganho_medio"]]
    bars = ax2.bar(agg["faixa_volta"].astype(str), agg["ganho_medio"],
                   color=cores_faixa, edgecolor="none", width=0.55)

    for bar, row in zip(bars, agg.itertuples()):
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 h + (0.05 if h >= 0 else -0.15),
                 f"{h:+.1f}\n(n={row.n})", ha="center", va="bottom",
                 color="white", fontsize=9, fontweight="bold")

    ax2.axhline(0, color="#555555", linewidth=0.8)
    ax2.set_xlabel("Faixa de Volta do Pit Stop", color="#aaaaaa", fontsize=10)
    ax2.set_ylabel("Ganho Medio de Posicoes", color="#aaaaaa", fontsize=10)
    ax2.set_title("Janela Otima de Pit Stop\n(Posicoes ganhas em media por faixa de volta)",
                  color="white", fontsize=11, fontweight="bold")
    ax2.tick_params(colors="white", labelsize=9)
    for sp in ["top", "right"]:
        ax2.spines[sp].set_visible(False)
    for sp in ["left", "bottom"]:
        ax2.spines[sp].set_color("#333333")

    plt.suptitle("Analise 2 — Janela Otima de Pit Stop | Stock Car 2024",
                 color="white", fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    caminho = os.path.join(OUTPUT_DIR, "2_janela_pit_stop.png")
    plt.savefig(caminho, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"[2] Janela Otima de Pit Stop salva: {caminho}")


# ===========================================================================
# ANALISE 3: ROI ESPORTIVO POR EQUIPE
# KPI: (pontos conquistados) / (pontos maximos possiveis) * 100
# Insight: Equipe que sempre fica em P4-P5 mas tem dois carros pode ter
#          ROI coletivo maior que equipe que tem um vencedor e um retardatario
# ===========================================================================
def plot_roi_esportivo() -> None:
    """Gera gráfico de ROI esportivo por equipe."""
    engine = get_engine()
    query = """
        SELECT equipe, posicao
        FROM resultados
        WHERE temporada = 2024
        ORDER BY equipe
    """
    df = pd.read_sql(query, engine)
    if df.empty:
        print("[AVISO] Sem dados para ROI Esportivo.")
        return

    # Pontos conquistados
    df["pontos"] = df["posicao"].map(PONTOS_STOCK_CAR).fillna(0)

    # Numero de corridas disputadas
    n_corridas = df.groupby("equipe")["posicao"].count().reset_index()
    n_corridas.columns = ["equipe", "participacoes"]

    # Pontos maximos possíveis = participacoes * 25 (se ganhasse tudo)
    resumo = (df.groupby("equipe")["pontos"].sum()
                .reset_index()
                .rename(columns={"pontos": "pontos_totais"}))
    resumo = resumo.merge(n_corridas, on="equipe")
    resumo["pontos_max"]  = resumo["participacoes"] * 25
    resumo["roi_pct"]     = (resumo["pontos_totais"] / resumo["pontos_max"] * 100).round(1)
    resumo = resumo.sort_values("roi_pct", ascending=False)

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    cores = [EQUIPE_CORES.get(eq, "#aaaaaa") for eq in resumo["equipe"]]
    bars = ax.bar(resumo["equipe"], resumo["roi_pct"], color=cores, width=0.55, edgecolor="none")

    # Linha de referencia: ROI de 50%
    ax.axhline(50, color="#ffaa00", linewidth=1.2, linestyle="--", alpha=0.7, label="Referencia 50%")

    for bar, row in zip(bars, resumo.itertuples()):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.5,
                f"{h:.1f}%\n({int(row.pontos_totais)} pts)",
                ha="center", va="bottom", color="white", fontsize=8.5, fontweight="bold")

    ax.set_ylim(0, resumo["roi_pct"].max() * 1.2)
    ax.set_ylabel("ROI Esportivo (%)", color="#aaaaaa", fontsize=10)
    ax.set_xlabel("Equipe", color="#aaaaaa", fontsize=10)
    ax.set_title("ROI Esportivo por Equipe — Stock Car 2024\n"
                 "Pontos conquistados / Pontos maximos possiveis x 100",
                 color="white", fontsize=13, fontweight="bold", pad=14)
    ax.tick_params(colors="white", labelsize=8.5, axis="x", rotation=22)
    ax.tick_params(colors="white", labelsize=9, axis="y")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    for sp in ["left", "bottom"]:
        ax.spines[sp].set_color("#333333")
    ax.legend(fontsize=9, facecolor="#1a1a2e", edgecolor="#333333", labelcolor="white")

    plt.tight_layout()
    caminho = os.path.join(OUTPUT_DIR, "3_roi_esportivo_equipes.png")
    plt.savefig(caminho, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"[3] ROI Esportivo salvo: {caminho}")


# ===========================================================================
# ANALISE 4: EVOLUCAO DE PERFORMANCE POR ETAPA (multi-corrida)
# KPI: Posicao de cada piloto etapa a etapa ao longo da temporada
# Insight: Quem melhorou? Quem caiu? Tendencia de desenvolvimento do carro.
# ===========================================================================
def plot_evolucao_temporada() -> None:
    """Gera gráfico de evolução de posições ao longo da temporada."""
    engine = get_engine()
    query = """
        SELECT
            r.piloto,
            r.equipe,
            c.circuito,
            c.data,
            r.posicao
        FROM resultados r
        JOIN corridas c ON r.corrida_id = c.id
        WHERE r.temporada = 2024
        ORDER BY c.data, r.posicao
    """
    df = pd.read_sql(query, engine)
    if df.empty:
        print("[AVISO] Sem dados para Evolucao por Temporada.")
        return

    # Abreviacao dos circuitos para caber no eixo X
    df["circuito_abrev"] = (df["circuito"]
                            .str.replace("Autodromo de ", "", regex=False)
                            .str.replace("Autodromo ", "", regex=False))

    etapas = df["circuito_abrev"].unique()

    # Foco nos top 6 pilotos mais presentes
    top_pilotos = (df.groupby("piloto")["posicao"]
                     .mean()
                     .sort_values()
                     .head(6)
                     .index.tolist())
    df_top = df[df["piloto"].isin(top_pilotos)]

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    for piloto, grupo in df_top.groupby("piloto"):
        grupo = grupo.sort_values("data")
        equipe = grupo["equipe"].iloc[0]
        cor = EQUIPE_CORES.get(equipe, "#aaaaaa")
        ax.plot(grupo["circuito_abrev"], grupo["posicao"],
                marker="o", linewidth=2, markersize=7,
                color=cor, label=f"{piloto} ({equipe})", zorder=3)
        # Anota ultima posicao
        ult = grupo.iloc[-1]
        ax.annotate(f" P{int(ult['posicao'])}", (ult["circuito_abrev"], ult["posicao"]),
                    color=cor, fontsize=7.5, va="center")

    # Inverte eixo Y: P1 no topo
    ax.invert_yaxis()
    ax.yaxis.set_major_locator(mticker.MultipleLocator(1))
    ax.set_ylabel("Posicao Final", color="#aaaaaa", fontsize=10)
    ax.set_xlabel("Etapa", color="#aaaaaa", fontsize=10)
    ax.set_title("Analise 4 — Evolucao de Performance por Etapa | Stock Car 2024\n"
                 "Top 6 pilotos | P1 no topo | Cada linha = piloto",
                 color="white", fontsize=13, fontweight="bold", pad=14)
    ax.tick_params(colors="white", labelsize=8.5, axis="x", rotation=30)
    ax.tick_params(colors="white", labelsize=9, axis="y")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    for sp in ["left", "bottom"]:
        ax.spines[sp].set_color("#333333")

    ax.grid(axis="y", color="#1e1e2e", linewidth=0.7, zorder=0)
    ax.legend(fontsize=8, facecolor="#1a1a2e", edgecolor="#333333",
              labelcolor="white", loc="lower left", ncol=2)

    plt.tight_layout()
    caminho = os.path.join(OUTPUT_DIR, "4_evolucao_temporada.png")
    plt.savefig(caminho, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"[4] Evolucao por Temporada salva: {caminho}")


# ===========================================================================
# MAIN
# ===========================================================================
if __name__ == "__main__":
    logger.info("=" * 55)
    logger.info("   STOCK CAR KPIs — Gerando 4 Analises...")
    logger.info("=" * 55)
    plot_consistencia()
    plot_janela_pit()
    plot_roi_esportivo()
    plot_evolucao_temporada()
    logger.info("Pronto! Graficos salvos em: ./output/")
    logger.info("  1_consistencia_pilotos.png")
    logger.info("  2_janela_pit_stop.png")
    logger.info("  3_roi_esportivo_equipes.png")
    logger.info("  4_evolucao_temporada.png")
