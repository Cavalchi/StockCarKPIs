-- Criação das tabelas principais para o projeto Stock Car KPIs

CREATE TABLE IF NOT EXISTS corridas (
    id SERIAL PRIMARY KEY,
    data DATE,
    circuito VARCHAR(100),
    condicoes_pista VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS resultados (
    id SERIAL PRIMARY KEY,
    corrida_id INTEGER REFERENCES corridas(id),
    piloto VARCHAR(100),
    equipe VARCHAR(100),
    posicao INTEGER,
    tempo_total VARCHAR(50),
    voltas INTEGER
);

CREATE TABLE IF NOT EXISTS pit_stops (
    id SERIAL PRIMARY KEY,
    corrida_id INTEGER REFERENCES corridas(id),
    piloto VARCHAR(100),
    equipe VARCHAR(100),
    volta INTEGER,
    duracao_s NUMERIC(5, 2)
);
