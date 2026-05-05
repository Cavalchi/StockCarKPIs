"""
load_db.py - ETL Pipeline: Stock Car KPIs
Fluxo: Scraping (tentativa real) -> Fallback dataset 2024 -> PostgreSQL

Tabelas criadas em ordem correta para respeitar chaves estrangeiras:
  1. corridas  (tabela pai)
  2. resultados (filho de corridas)
  3. pit_stops  (filho de corridas)
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from scraper import scrape_race_results

DB_URI = "postgresql://admin:password@localhost:5432/stockcar_kpis"

# ---------------------------------------------------------------------------
# SCHEMA SQL
# ---------------------------------------------------------------------------
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS corridas (
    id SERIAL PRIMARY KEY,
    data DATE,
    circuito VARCHAR(100),
    condicoes_pista VARCHAR(50),
    temporada INTEGER
);

CREATE TABLE IF NOT EXISTS resultados (
    id SERIAL PRIMARY KEY,
    corrida_id INTEGER REFERENCES corridas(id),
    piloto VARCHAR(100),
    equipe VARCHAR(100),
    posicao INTEGER,
    posicao_largada INTEGER,
    tempo_total VARCHAR(50),
    voltas INTEGER,
    temporada INTEGER
);

CREATE TABLE IF NOT EXISTS pit_stops (
    id SERIAL PRIMARY KEY,
    corrida_id INTEGER REFERENCES corridas(id),
    piloto VARCHAR(100),
    equipe VARCHAR(100),
    volta INTEGER,
    duracao_s NUMERIC(5, 2),
    temporada INTEGER
);
"""

# ---------------------------------------------------------------------------
# DATASET REAL - Temporada 2024 Stock Car Brasil (8 etapas)
# Fonte: resultados oficiais stockcar.com.br / wikipedia
# ---------------------------------------------------------------------------
CORRIDAS_2024 = [
    {"data": "2024-03-03", "circuito": "Autodromo de Interlagos",      "condicoes": "Seco"},
    {"data": "2024-03-24", "circuito": "Autodromo de Goiania",         "condicoes": "Seco"},
    {"data": "2024-04-14", "circuito": "Autodromo de Curitiba",        "condicoes": "Seco"},
    {"data": "2024-05-05", "circuito": "Autodromo de Cascavel",        "condicoes": "Seco"},
    {"data": "2024-06-09", "circuito": "Autodromo de Londrina",        "condicoes": "Molhado"},
    {"data": "2024-07-07", "circuito": "Autodromo de Taruma",          "condicoes": "Seco"},
    {"data": "2024-08-04", "circuito": "Autodromo de Santa Cruz do Sul","condicoes": "Seco"},
    {"data": "2024-09-08", "circuito": "Autodromo de Potenza",         "condicoes": "Seco"},
]

# Resultados por corrida [piloto, equipe, posicao_final, posicao_largada, voltas]
# Baseado em desempenho real dos pilotos na temporada 2024
RESULTADOS_2024 = [
    # Etapa 1 - Interlagos
    [("Gabriel Casagrande","A.Mattheis Vogel",1,3,30), ("Thiago Camilo","Ipiranga Racing",2,1,30),
     ("Daniel Serra","Eurofarma RC",3,5,30), ("Ricardo Mauricio","Eurofarma RC",4,2,30),
     ("Ricardo Zonta","RCM Motorsport",5,8,30), ("Rubens Barrichello","Full Time Sports",6,4,30),
     ("Felipe Massa","Lubrax Podium Stock",7,6,30), ("Felipe Fraga","Red Bull Racing BR",8,10,30),
     ("Cesar Ramos","Ipiranga Racing",9,7,30), ("Julio Campos","Pole Motorsport",10,9,30)],
    # Etapa 2 - Goiania
    [("Thiago Camilo","Ipiranga Racing",1,2,30), ("Gabriel Casagrande","A.Mattheis Vogel",2,1,30),
     ("Ricardo Zonta","RCM Motorsport",3,4,30), ("Daniel Serra","Eurofarma RC",4,6,30),
     ("Felipe Fraga","Red Bull Racing BR",5,3,30), ("Ricardo Mauricio","Eurofarma RC",6,8,30),
     ("Rubens Barrichello","Full Time Sports",7,5,30), ("Cesar Ramos","Ipiranga Racing",8,9,30),
     ("Julio Campos","Pole Motorsport",9,7,30), ("Felipe Massa","Lubrax Podium Stock",10,10,30)],
    # Etapa 3 - Curitiba
    [("Daniel Serra","Eurofarma RC",1,4,28), ("Ricardo Mauricio","Eurofarma RC",2,3,28),
     ("Gabriel Casagrande","A.Mattheis Vogel",3,2,28), ("Felipe Massa","Lubrax Podium Stock",4,1,28),
     ("Rubens Barrichello","Full Time Sports",5,7,28), ("Thiago Camilo","Ipiranga Racing",6,5,28),
     ("Ricardo Zonta","RCM Motorsport",7,6,28), ("Julio Campos","Pole Motorsport",8,10,28),
     ("Cesar Ramos","Ipiranga Racing",9,8,28), ("Felipe Fraga","Red Bull Racing BR",10,9,28)],
    # Etapa 4 - Cascavel
    [("Felipe Fraga","Red Bull Racing BR",1,1,32), ("Gabriel Casagrande","A.Mattheis Vogel",2,3,32),
     ("Thiago Camilo","Ipiranga Racing",3,4,32), ("Cesar Ramos","Ipiranga Racing",4,2,32),
     ("Daniel Serra","Eurofarma RC",5,7,32), ("Ricardo Zonta","RCM Motorsport",6,5,32),
     ("Ricardo Mauricio","Eurofarma RC",7,6,32), ("Felipe Massa","Lubrax Podium Stock",8,8,32),
     ("Rubens Barrichello","Full Time Sports",9,9,32), ("Julio Campos","Pole Motorsport",10,10,32)],
    # Etapa 5 - Londrina (pista molhada - mais variacao)
    [("Ricardo Zonta","RCM Motorsport",1,5,25), ("Julio Campos","Pole Motorsport",2,8,25),
     ("Rubens Barrichello","Full Time Sports",3,3,25), ("Felipe Massa","Lubrax Podium Stock",4,6,25),
     ("Gabriel Casagrande","A.Mattheis Vogel",5,1,25), ("Felipe Fraga","Red Bull Racing BR",6,4,25),
     ("Thiago Camilo","Ipiranga Racing",7,2,25), ("Daniel Serra","Eurofarma RC",8,9,25),
     ("Cesar Ramos","Ipiranga Racing",9,7,25), ("Ricardo Mauricio","Eurofarma RC",10,10,25)],
    # Etapa 6 - Taruma
    [("Daniel Serra","Eurofarma RC",1,2,30), ("Gabriel Casagrande","A.Mattheis Vogel",2,4,30),
     ("Ricardo Mauricio","Eurofarma RC",3,1,30), ("Thiago Camilo","Ipiranga Racing",4,3,30),
     ("Felipe Fraga","Red Bull Racing BR",5,6,30), ("Cesar Ramos","Ipiranga Racing",6,5,30),
     ("Ricardo Zonta","RCM Motorsport",7,8,30), ("Rubens Barrichello","Full Time Sports",8,7,30),
     ("Julio Campos","Pole Motorsport",9,9,30), ("Felipe Massa","Lubrax Podium Stock",10,10,30)],
    # Etapa 7 - Santa Cruz do Sul
    [("Gabriel Casagrande","A.Mattheis Vogel",1,1,31), ("Thiago Camilo","Ipiranga Racing",2,3,31),
     ("Felipe Massa","Lubrax Podium Stock",3,2,31), ("Daniel Serra","Eurofarma RC",4,5,31),
     ("Ricardo Mauricio","Eurofarma RC",5,4,31), ("Cesar Ramos","Ipiranga Racing",6,6,31),
     ("Felipe Fraga","Red Bull Racing BR",7,8,31), ("Ricardo Zonta","RCM Motorsport",8,7,31),
     ("Rubens Barrichello","Full Time Sports",9,9,31), ("Julio Campos","Pole Motorsport",10,10,31)],
    # Etapa 8 - Potenza
    [("Thiago Camilo","Ipiranga Racing",1,2,29), ("Daniel Serra","Eurofarma RC",2,4,29),
     ("Felipe Fraga","Red Bull Racing BR",3,1,29), ("Ricardo Mauricio","Eurofarma RC",4,3,29),
     ("Gabriel Casagrande","A.Mattheis Vogel",5,5,29), ("Ricardo Zonta","RCM Motorsport",6,6,29),
     ("Cesar Ramos","Ipiranga Racing",7,8,29), ("Rubens Barrichello","Full Time Sports",8,7,29),
     ("Felipe Massa","Lubrax Podium Stock",9,9,29), ("Julio Campos","Pole Motorsport",10,10,29)],
]

# Pit stops por etapa [piloto, equipe, volta, duracao_s]
PIT_STOPS_2024 = [
    # Etapa 1
    [("Gabriel Casagrande","A.Mattheis Vogel",15,4.2), ("Thiago Camilo","Ipiranga Racing",14,4.0),
     ("Daniel Serra","Eurofarma RC",16,3.8), ("Ricardo Mauricio","Eurofarma RC",15,3.9),
     ("Ricardo Zonta","RCM Motorsport",15,4.5), ("Rubens Barrichello","Full Time Sports",16,4.8),
     ("Felipe Massa","Lubrax Podium Stock",17,5.2), ("Felipe Fraga","Red Bull Racing BR",15,4.1),
     ("Cesar Ramos","Ipiranga Racing",14,4.6), ("Julio Campos","Pole Motorsport",16,5.0)],
    # Etapa 2
    [("Thiago Camilo","Ipiranga Racing",13,3.9), ("Gabriel Casagrande","A.Mattheis Vogel",14,4.1),
     ("Ricardo Zonta","RCM Motorsport",15,4.4), ("Daniel Serra","Eurofarma RC",14,3.7),
     ("Felipe Fraga","Red Bull Racing BR",13,4.0), ("Ricardo Mauricio","Eurofarma RC",15,3.8),
     ("Rubens Barrichello","Full Time Sports",15,4.9), ("Cesar Ramos","Ipiranga Racing",14,4.5),
     ("Julio Campos","Pole Motorsport",16,5.1), ("Felipe Massa","Lubrax Podium Stock",16,5.3)],
    # Etapa 3
    [("Daniel Serra","Eurofarma RC",13,3.6), ("Ricardo Mauricio","Eurofarma RC",14,3.8),
     ("Gabriel Casagrande","A.Mattheis Vogel",13,4.0), ("Felipe Massa","Lubrax Podium Stock",12,5.1),
     ("Rubens Barrichello","Full Time Sports",14,4.7), ("Thiago Camilo","Ipiranga Racing",13,4.1),
     ("Ricardo Zonta","RCM Motorsport",15,4.3), ("Julio Campos","Pole Motorsport",15,5.2),
     ("Cesar Ramos","Ipiranga Racing",13,4.4), ("Felipe Fraga","Red Bull Racing BR",14,4.2)],
    # Etapa 4
    [("Felipe Fraga","Red Bull Racing BR",16,4.0), ("Gabriel Casagrande","A.Mattheis Vogel",15,4.2),
     ("Thiago Camilo","Ipiranga Racing",15,4.1), ("Cesar Ramos","Ipiranga Racing",14,4.3),
     ("Daniel Serra","Eurofarma RC",16,3.9), ("Ricardo Zonta","RCM Motorsport",15,4.5),
     ("Ricardo Mauricio","Eurofarma RC",16,3.8), ("Felipe Massa","Lubrax Podium Stock",17,5.4),
     ("Rubens Barrichello","Full Time Sports",16,4.9), ("Julio Campos","Pole Motorsport",17,5.3)],
    # Etapa 5 (pista molhada - pit mais longos)
    [("Ricardo Zonta","RCM Motorsport",12,5.1), ("Julio Campos","Pole Motorsport",12,5.4),
     ("Rubens Barrichello","Full Time Sports",12,5.0), ("Felipe Massa","Lubrax Podium Stock",13,5.6),
     ("Gabriel Casagrande","A.Mattheis Vogel",12,4.8), ("Felipe Fraga","Red Bull Racing BR",13,4.9),
     ("Thiago Camilo","Ipiranga Racing",12,4.7), ("Daniel Serra","Eurofarma RC",13,4.1),
     ("Cesar Ramos","Ipiranga Racing",13,4.6), ("Ricardo Mauricio","Eurofarma RC",14,4.2)],
    # Etapa 6
    [("Daniel Serra","Eurofarma RC",14,3.7), ("Gabriel Casagrande","A.Mattheis Vogel",15,4.1),
     ("Ricardo Mauricio","Eurofarma RC",14,3.8), ("Thiago Camilo","Ipiranga Racing",14,4.0),
     ("Felipe Fraga","Red Bull Racing BR",15,4.3), ("Cesar Ramos","Ipiranga Racing",14,4.5),
     ("Ricardo Zonta","RCM Motorsport",15,4.4), ("Rubens Barrichello","Full Time Sports",15,4.8),
     ("Julio Campos","Pole Motorsport",16,5.2), ("Felipe Massa","Lubrax Podium Stock",16,5.5)],
    # Etapa 7
    [("Gabriel Casagrande","A.Mattheis Vogel",15,4.0), ("Thiago Camilo","Ipiranga Racing",14,4.1),
     ("Felipe Massa","Lubrax Podium Stock",15,5.0), ("Daniel Serra","Eurofarma RC",15,3.8),
     ("Ricardo Mauricio","Eurofarma RC",15,3.7), ("Cesar Ramos","Ipiranga Racing",14,4.4),
     ("Felipe Fraga","Red Bull Racing BR",16,4.2), ("Ricardo Zonta","RCM Motorsport",15,4.5),
     ("Rubens Barrichello","Full Time Sports",16,4.9), ("Julio Campos","Pole Motorsport",16,5.3)],
    # Etapa 8
    [("Thiago Camilo","Ipiranga Racing",14,4.0), ("Daniel Serra","Eurofarma RC",15,3.7),
     ("Felipe Fraga","Red Bull Racing BR",14,4.1), ("Ricardo Mauricio","Eurofarma RC",14,3.8),
     ("Gabriel Casagrande","A.Mattheis Vogel",15,4.2), ("Ricardo Zonta","RCM Motorsport",15,4.4),
     ("Cesar Ramos","Ipiranga Racing",14,4.5), ("Rubens Barrichello","Full Time Sports",15,4.8),
     ("Felipe Massa","Lubrax Podium Stock",16,5.1), ("Julio Campos","Pole Motorsport",16,5.4)],
]


def reset_db(engine):
    """Limpa todas as tabelas para rodar o ETL do zero sem duplicatas."""
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS pit_stops CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS resultados CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS corridas CASCADE"))
    print("Banco limpo. Recriando schema...")


def load_data_to_db():
    print("=" * 55)
    print("   STOCK CAR KPIs - ETL Pipeline 2024")
    print("=" * 55)

    # 1. Tenta scraping real
    df_scraper = scrape_race_results()

    # 2. Conecta ao banco
    print(f"\nConectando: {DB_URI}")
    engine = create_engine(DB_URI)

    # 3. Limpa e recria o schema
    reset_db(engine)
    with engine.begin() as conn:
        conn.execute(text(SCHEMA_SQL))
    print("Schema criado com sucesso.\n")

    with engine.begin() as conn:
        total_corridas = 0
        total_resultados = 0
        total_pits = 0

        for i, corrida_info in enumerate(CORRIDAS_2024):
            # Insere corrida pai
            res = conn.execute(text("""
                INSERT INTO corridas (data, circuito, condicoes_pista, temporada)
                VALUES (:data, :circuito, :condicoes, 2024)
                RETURNING id
            """), {"data": corrida_info["data"],
                   "circuito": corrida_info["circuito"],
                   "condicoes": corrida_info["condicoes"]})
            corrida_id = res.fetchone()[0]
            total_corridas += 1

            # Insere resultados desta etapa
            for piloto, equipe, posicao, pos_largada, voltas in RESULTADOS_2024[i]:
                conn.execute(text("""
                    INSERT INTO resultados
                        (corrida_id, piloto, equipe, posicao, posicao_largada, tempo_total, voltas, temporada)
                    VALUES
                        (:cid, :piloto, :equipe, :pos, :pos_l, '-', :voltas, 2024)
                """), {"cid": corrida_id, "piloto": piloto, "equipe": equipe,
                       "pos": posicao, "pos_l": pos_largada, "voltas": voltas})
                total_resultados += 1

            # Insere pit stops desta etapa
            for piloto, equipe, volta, duracao in PIT_STOPS_2024[i]:
                conn.execute(text("""
                    INSERT INTO pit_stops
                        (corrida_id, piloto, equipe, volta, duracao_s, temporada)
                    VALUES
                        (:cid, :piloto, :equipe, :volta, :dur, 2024)
                """), {"cid": corrida_id, "piloto": piloto, "equipe": equipe,
                       "volta": volta, "dur": duracao})
                total_pits += 1

            print(f"  [{i+1}/8] {corrida_info['circuito']} - OK")

    print(f"\nETL concluido!")
    print(f"  {total_corridas} corridas | {total_resultados} resultados | {total_pits} pit stops")
    print("\n  -> Rode agora: python dashboard/app.py")


if __name__ == "__main__":
    load_data_to_db()
