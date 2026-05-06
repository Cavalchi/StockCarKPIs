"""
load_db.py — ETL Pipeline: Stock Car KPIs
============================================
Pipeline real que lê dados de CSVs em data/raw/, valida,
e carrega no PostgreSQL.

Fluxo:
  1. Descobre CSVs por temporada em data/raw/
  2. Valida integridade dos dados (posições, nulos, ranges)
  3. Cria schema a partir de db/schema.sql (fonte única de verdade)
  4. Insere dados no banco por temporada

Uso:
  python scraper/load_db.py               # carrega todas as temporadas
  python scraper/load_db.py --season 2024  # carrega só uma temporada
"""

import argparse
import logging
from typing import Dict, Tuple
import pandas as pd
from sqlalchemy import create_engine, text

from stockcar_kpis.config import DATABASE_URL, SCHEMA_PATH, PROJECT_ROOT, DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

TEMPORADAS_DISPONIVEIS = sorted(
    {int(f.stem.split("_")[-1]) for f in DATA_DIR.glob("corridas_*.csv")}
)


# ===========================================================================
# VALIDAÇÃO DE DADOS
# ===========================================================================
class ValidationError(Exception):
    """Erro de validação nos dados de entrada."""


def validar_corridas(df: pd.DataFrame, temporada: int) -> None:
    """Valida o DataFrame de corridas."""
    erros = []

    if df.empty:
        erros.append(f"[{temporada}] corridas: arquivo vazio")

    # Colunas obrigatórias
    cols_esperadas = {"data", "circuito", "condicoes_pista"}
    faltando = cols_esperadas - set(df.columns)
    if faltando:
        erros.append(f"[{temporada}] corridas: colunas faltando: {faltando}")

    # Sem nulos em campos críticos
    for col in ["data", "circuito"]:
        if col in df.columns and df[col].isna().any():
            erros.append(f"[{temporada}] corridas: valores nulos em '{col}'")

    # Condições de pista válidas
    if "condicoes_pista" in df.columns:
        validas = {"Seco", "Molhado", "Misto"}
        invalidas = set(df["condicoes_pista"].dropna().unique()) - validas
        if invalidas:
            erros.append(
                f"[{temporada}] corridas: condicoes_pista inválidas: {invalidas}"
            )

    if erros:
        raise ValidationError("\n".join(erros))


def validar_resultados(df: pd.DataFrame, temporada: int, n_etapas: int) -> None:
    """Valida o DataFrame de resultados."""
    erros = []

    if df.empty:
        erros.append(f"[{temporada}] resultados: arquivo vazio")

    # Colunas obrigatórias
    cols_esperadas = {"etapa", "piloto", "equipe", "posicao", "posicao_largada", "voltas"}
    faltando = cols_esperadas - set(df.columns)
    if faltando:
        erros.append(f"[{temporada}] resultados: colunas faltando: {faltando}")

    # Sem nulos em campos críticos
    for col in ["piloto", "equipe", "posicao"]:
        if col in df.columns and df[col].isna().any():
            erros.append(f"[{temporada}] resultados: valores nulos em '{col}'")

    # Posições devem ser >= 1
    if "posicao" in df.columns:
        if (df["posicao"] < 1).any():
            erros.append(f"[{temporada}] resultados: posição < 1 encontrada")

    # Posições únicas por etapa (sem empates)
    if "etapa" in df.columns and "posicao" in df.columns:
        for etapa, grupo in df.groupby("etapa"):
            dups = grupo[grupo["posicao"].duplicated()]
            if not dups.empty:
                erros.append(
                    f"[{temporada}] resultados: posições duplicadas na etapa {etapa}: "
                    f"{dups['posicao'].tolist()}"
                )

    # Número de etapas deve bater
    if "etapa" in df.columns:
        etapas_csv = df["etapa"].nunique()
        if etapas_csv != n_etapas:
            erros.append(
                f"[{temporada}] resultados: {etapas_csv} etapas no CSV vs "
                f"{n_etapas} corridas"
            )

    if erros:
        raise ValidationError("\n".join(erros))


def validar_pit_stops(df: pd.DataFrame, temporada: int, n_etapas: int) -> None:
    """Valida o DataFrame de pit stops."""
    erros = []

    if df.empty:
        erros.append(f"[{temporada}] pit_stops: arquivo vazio")

    # Colunas obrigatórias
    cols_esperadas = {"etapa", "piloto", "equipe", "volta", "duracao_s"}
    faltando = cols_esperadas - set(df.columns)
    if faltando:
        erros.append(f"[{temporada}] pit_stops: colunas faltando: {faltando}")

    # Duração deve ser positiva e razoável (1s a 30s)
    if "duracao_s" in df.columns:
        if (df["duracao_s"] <= 0).any():
            erros.append(f"[{temporada}] pit_stops: duração <= 0 encontrada")
        if (df["duracao_s"] > 30).any():
            erros.append(f"[{temporada}] pit_stops: duração > 30s (suspeita)")

    # Volta deve ser positiva
    if "volta" in df.columns:
        if (df["volta"] < 1).any():
            erros.append(f"[{temporada}] pit_stops: volta < 1 encontrada")

    if erros:
        raise ValidationError("\n".join(erros))


# ===========================================================================
# ETL
# ===========================================================================
def carregar_csvs(temporada: int) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carrega e retorna os 3 DataFrames de uma temporada."""
    corridas_path = DATA_DIR / f"corridas_{temporada}.csv"
    resultados_path = DATA_DIR / f"resultados_{temporada}.csv"
    pit_stops_path = DATA_DIR / f"pit_stops_{temporada}.csv"

    for p in [corridas_path, resultados_path, pit_stops_path]:
        if not p.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {p}")

    df_corridas = pd.read_csv(corridas_path)
    df_resultados = pd.read_csv(resultados_path)
    df_pit_stops = pd.read_csv(pit_stops_path)

    return df_corridas, df_resultados, df_pit_stops


def reset_db(engine) -> None:
    """Limpa todas as tabelas para rodar o ETL do zero sem duplicatas."""
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS pit_stops"))
        conn.execute(text("DROP TABLE IF EXISTS resultados"))
        conn.execute(text("DROP TABLE IF EXISTS corridas"))
    logger.info("Banco limpo.")


def inserir_temporada(engine, temporada: int,
                      df_corridas: pd.DataFrame,
                      df_resultados: pd.DataFrame,
                      df_pit_stops: pd.DataFrame) -> Dict[str, int]:
    """Insere os dados de uma temporada no banco. Retorna contadores."""
    contadores = {"corridas": 0, "resultados": 0, "pit_stops": 0}

    with engine.begin() as conn:
        # Mapeia etapa -> corrida_id
        etapa_para_id = {}

        for idx, row in df_corridas.iterrows():
            res = conn.execute(text("""
                INSERT INTO corridas (data, circuito, condicoes_pista, temporada)
                VALUES (:data, :circuito, :condicoes, :temporada)
                RETURNING id
            """), {
                "data": row["data"],
                "circuito": row["circuito"],
                "condicoes": row["condicoes_pista"],
                "temporada": temporada,
            })
            corrida_id = res.fetchone()[0]
            etapa_para_id[idx + 1] = corrida_id  # etapas são 1-indexed
            contadores["corridas"] += 1

        # Insere resultados
        for _, row in df_resultados.iterrows():
            corrida_id = etapa_para_id[int(row["etapa"])]
            conn.execute(text("""
                INSERT INTO resultados
                    (corrida_id, piloto, equipe, posicao, posicao_largada,
                     tempo_total, voltas, temporada)
                VALUES
                    (:cid, :piloto, :equipe, :pos, :pos_l, '-', :voltas, :temp)
            """), {
                "cid": corrida_id,
                "piloto": row["piloto"],
                "equipe": row["equipe"],
                "pos": int(row["posicao"]),
                "pos_l": int(row["posicao_largada"]),
                "voltas": int(row["voltas"]),
                "temp": temporada,
            })
            contadores["resultados"] += 1

        # Insere pit stops
        for _, row in df_pit_stops.iterrows():
            corrida_id = etapa_para_id[int(row["etapa"])]
            conn.execute(text("""
                INSERT INTO pit_stops
                    (corrida_id, piloto, equipe, volta, duracao_s, temporada)
                VALUES
                    (:cid, :piloto, :equipe, :volta, :dur, :temp)
            """), {
                "cid": corrida_id,
                "piloto": row["piloto"],
                "equipe": row["equipe"],
                "volta": int(row["volta"]),
                "dur": float(row["duracao_s"]),
                "temp": temporada,
            })
            contadores["pit_stops"] += 1

    return contadores


# ===========================================================================
# MAIN
# ===========================================================================
def main() -> None:
    parser = argparse.ArgumentParser(description="Stock Car KPIs — ETL Pipeline")
    parser.add_argument(
        "--season", type=int, default=None,
        help="Temporada específica para carregar (ex: 2024). "
             "Omita para carregar todas."
    )
    args = parser.parse_args()

    temporadas = [args.season] if args.season else TEMPORADAS_DISPONIVEIS

    logger.info("=" * 60)
    logger.info("   STOCK CAR KPIs — ETL Pipeline")
    logger.info("=" * 60)
    logger.info(f"Temporadas: {temporadas}")
    logger.info(f"Fonte:      {DATA_DIR}")
    logger.info(f"Banco:      {DATABASE_URL}")

    # 1. Conecta ao banco
    engine = create_engine(DATABASE_URL)

    # 2. Limpa e recria schema
    reset_db(engine)
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.execute(text(schema_sql))
    logger.info(f"Schema criado ({SCHEMA_PATH.name}).")

    # 3. Processa cada temporada
    totais = {"corridas": 0, "resultados": 0, "pit_stops": 0}

    for temporada in temporadas:
        logger.info(f"── Temporada {temporada} ──")

        # 3a. Carregar CSVs
        df_corridas, df_resultados, df_pit_stops = carregar_csvs(temporada)
        n_etapas = len(df_corridas)

        # 3b. Validar
        logger.info("Validando dados...")
        validar_corridas(df_corridas, temporada)
        validar_resultados(df_resultados, temporada, n_etapas)
        validar_pit_stops(df_pit_stops, temporada, n_etapas)
        logger.info("Validação OK ✓")

        # 3c. Inserir
        contadores = inserir_temporada(
            engine, temporada, df_corridas, df_resultados, df_pit_stops
        )
        for k, v in contadores.items():
            totais[k] += v

        logger.info(
            f"{contadores['corridas']} corridas | "
            f"{contadores['resultados']} resultados | "
            f"{contadores['pit_stops']} pit stops"
        )

    # 4. Resumo
    logger.info("=" * 60)
    logger.info("ETL concluído!")
    logger.info(
        f"TOTAL: {totais['corridas']} corridas | "
        f"{totais['resultados']} resultados | "
        f"{totais['pit_stops']} pit stops"
    )
    logger.info("-> Rode: python -m stockcar_kpis.dashboard.app")
    logger.info("-> Ou:   streamlit run stockcar_kpis/dashboard/streamlit_app.py")


if __name__ == "__main__":
    main()
