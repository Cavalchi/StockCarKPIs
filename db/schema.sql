-- ============================================================
-- Stock Car KPIs — Schema do Banco de Dados
-- ============================================================
-- Fonte única de verdade.  Usado por:
--   • docker-compose (init script)
--   • scraper/load_db.py  (lê este arquivo via config.SCHEMA_PATH)
-- ============================================================

CREATE TABLE IF NOT EXISTS corridas (
    id              SERIAL PRIMARY KEY,
    data            DATE,
    circuito        VARCHAR(100),
    condicoes_pista VARCHAR(50),
    temporada       INTEGER
);

CREATE TABLE IF NOT EXISTS resultados (
    id              SERIAL PRIMARY KEY,
    corrida_id      INTEGER REFERENCES corridas(id),
    piloto          VARCHAR(100),
    equipe          VARCHAR(100),
    posicao         INTEGER,
    posicao_largada INTEGER,
    tempo_total     VARCHAR(50),
    voltas          INTEGER,
    temporada       INTEGER
);

CREATE TABLE IF NOT EXISTS pit_stops (
    id              SERIAL PRIMARY KEY,
    corrida_id      INTEGER REFERENCES corridas(id),
    piloto          VARCHAR(100),
    equipe          VARCHAR(100),
    volta           INTEGER,
    duracao_s       NUMERIC(5, 2),
    temporada       INTEGER
);
