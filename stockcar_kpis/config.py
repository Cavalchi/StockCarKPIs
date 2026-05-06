"""
config.py — Configuração centralizada do projeto Stock Car KPIs

Carrega variáveis de ambiente do arquivo .env (se existir) e monta
a URI de conexão com o banco de dados.  Todos os módulos devem
importar daqui em vez de manter strings de conexão hardcoded.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega o .env que estiver na raiz do projeto
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Banco de Dados
# ---------------------------------------------------------------------------
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "stockcar_kpis")

USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() == "true"

if USE_SQLITE:
    # Para deploy gratuito no Streamlit Cloud
    _sqlite_path = _PROJECT_ROOT / "stockcar.db"
    DATABASE_URL = f"sqlite:///{_sqlite_path}"
else:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
    )

# ---------------------------------------------------------------------------
# Caminhos do projeto
# ---------------------------------------------------------------------------
PROJECT_ROOT = _PROJECT_ROOT
SCHEMA_PATH = _PROJECT_ROOT / "db" / "schema.sql"
OUTPUT_DIR = _PROJECT_ROOT / "output"
DATA_DIR = _PROJECT_ROOT / "data" / "raw"

# ---------------------------------------------------------------------------
# Paleta de cores por equipe (consistente em todos os gráficos)
# ---------------------------------------------------------------------------
EQUIPE_CORES: dict[str, str] = {
    "Eurofarma RC":        "#1976D2",  # Azul Eurofarma
    "Ipiranga Racing":     "#FFB300",  # Amarelo Ipiranga
    "A.Mattheis Vogel":    "#2E7D32",  # Verde Crown
    "RCM Motorsport":      "#D32F2F",  # Vermelho RCM
    "Full Time Sports":    "#7B1FA2",  # Roxo Mobil
    "Lubrax Podium Stock": "#00897B",  # Teal Lubrax/Petrobras
    "Red Bull Racing BR":  "#5C6BC0",  # Índigo Red Bull
    "Blau Motorsport":     "#00ACC1",  # Ciano Blau
    "Pole Motorsport":     "#EF6C00",  # Laranja Pole
    "TMG Racing":          "#E64A19",  # Terracota TMG
}

# ---------------------------------------------------------------------------
# Sistema de pontos Stock Car (top 10)
# ---------------------------------------------------------------------------
PONTOS_STOCK_CAR: dict[int, int] = {
    1: 25, 2: 20, 3: 16, 4: 13, 5: 11,
    6: 9,  7: 7,  8: 5,  9: 3,  10: 1,
}
