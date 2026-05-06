<div align="center">

# 🏎️ Stock Car KPIs Analytics

**Pipeline de Engenharia de Dados aplicada ao motorsport brasileiro**

[![CI Pipeline](https://github.com/Cavalchi/StockCarKPIs/actions/workflows/ci.yml/badge.svg)](https://github.com/Cavalchi/StockCarKPIs/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat-square&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

*Transformando dados brutos da Stock Car Brasil em inteligência competitiva real*

[🇺🇸 Read this in English](README_EN.md)

</div>

---

## O Problema

O site oficial da Stock Car publica tabelas de resultados corrida a corrida — posições finais, pit stops, grid de largada. Dados brutos.

**O que nenhum analista da equipe consegue ver facilmente nesses dados:**
- Qual piloto é *estatisticamente* mais consistente ao longo da temporada?
- Em quais voltas as equipes que **subiram de posição** fizeram o pit — e qual a janela ideal?
- Qual equipe está aproveitando *melhor* o seu equipamento, independente de vitórias?
- Quem está evoluindo no campeonato e quem está estagnado?

Este projeto automatiza a coleta, estrutura em banco relacional e responde essas perguntas com SQL e visualizações.

---

## Arquitetura

```
┌───────────────────┐      ┌──────────────────────┐      ┌─────────────────────┐
│   data/raw/*.csv  │─────▶│  scraper/load_db.py  │─────│  PostgreSQL (Docker)│
│  (3 temporadas)   │      │  Validação + ETL     │      │  3 tabelas relacionadas│
└───────────────────┘      └──────────────────────┘      └──────────┬──────────┘
                                                                    │
                                                        ┌───────────▼──────────┐
                                                        │  dashboard/app.py    │
                                                        │  streamlit_app.py    │
                                                        │  4 análises + charts │
                                                        └──────────────────────┘
```

**Schema do banco:**
```
corridas  (id, data, circuito, condicoes_pista, temporada)
    │
    ├──▶  resultados  (corrida_id, piloto, equipe, posicao, posicao_largada, voltas)
    │
    └──▶  pit_stops   (corrida_id, piloto, equipe, volta, duracao_s)
```

---

## Stack

| Ferramenta | Papel no projeto |
|---|---|
| **Python 3.10** | Orquestração do pipeline ETL e visualizações |
| **Selenium** | Web scraping do site oficial (com fallback automático) |
| **PostgreSQL 15** | Armazenamento relacional com constraints e chaves estrangeiras |
| **Docker Compose** | Banco isolado e reproduzível — roda igual em qualquer máquina |
| **SQLAlchemy** | Conexão Python → PostgreSQL, inserção via DataFrame |
| **Pandas** | Transformação dos dados e preparação para análise |
| **Matplotlib + Seaborn** | Visualizações com tema escuro e paleta por equipe |
| **Git** | Controle de versão |

---

## As 4 Análises

### 1 — Score de Consistência por Piloto

> *"Quem entrega resultado toda etapa, independente do circuito?"*

Mede o **desvio padrão das posições finais** ao longo da temporada.
Um piloto consistente tem STDDEV baixo — termina sempre na mesma região, independente do circuito ou condição de pista. Isso é crucial para estratégia de campeonato: equipes que precisam acumular pontos preferem consistência a picos isolados.

```sql
SELECT piloto, equipe,
       ROUND(AVG(posicao)::numeric, 2)     AS media_posicao,
       ROUND(STDDEV(posicao)::numeric, 2)  AS desvio_padrao
FROM resultados
WHERE temporada = 2024
GROUP BY piloto, equipe
ORDER BY desvio_padrao ASC;
```

![Consistência](assets/1_consistencia_pilotos.png)

---

### 2 — Janela Ótima de Pit Stop

> *"Em quais voltas os pilotos que subiram de posição fizeram a parada?"*

Cruza a **volta do pit stop** com o **ganho de posições** resultante (posição de largada − posição final).
Identifica estatisticamente a janela de undercut e overcut mais eficaz para cada circuito.

```sql
SELECT faixa_volta,
       ROUND(AVG(posicao_largada - posicao)::numeric, 2) AS ganho_medio_posicoes
FROM pit_stops p
JOIN resultados r ON p.corrida_id = r.corrida_id AND p.piloto = r.piloto
GROUP BY faixa_volta
ORDER BY ganho_medio_posicoes DESC;
```

![Janela Pit](assets/2_janela_pit_stop.png)

---

### 3 — ROI Esportivo por Equipe

> *"Qual equipe está aproveitando melhor o seu equipamento?"*

**ROI Esportivo = (Pontos conquistados / Pontos máximos possíveis) × 100**

Uma equipe que sempre termina em P4–P5 pode ter ROI coletivo maior do que uma equipe com um vencedor e um piloto na parte de trás do grid. Essa métrica mede eficiência real — não apenas brilho isolado.

```sql
WITH pontos AS (
  SELECT equipe,
         SUM(CASE posicao WHEN 1 THEN 25 WHEN 2 THEN 20 ... END) AS conquistados,
         COUNT(*) * 25 AS maximo_possivel
  FROM resultados WHERE temporada = 2024
  GROUP BY equipe
)
SELECT equipe,
       ROUND(conquistados::numeric / maximo_possivel * 100, 1) AS roi_pct
FROM pontos ORDER BY roi_pct DESC;
```

![ROI Esportivo](assets/3_roi_esportivo_equipes.png)

---

### 4 — Evolução de Performance por Etapa

> *"Quem melhorou no segundo semestre? Quem sofreu com mudanças de regulamento?"*

Série temporal da posição final de cada piloto etapa a etapa.
Revela tendências de desenvolvimento de carro, recuperações após problemas mecânicos e impacto de condições adversas (ex: etapa de pista molhada em Londrina).

![Evolução](assets/4_evolucao_temporada.png)

---

### 5 — Previsão de Posição Final (Machine Learning)

> *"Dado que eu larguei em P5 pela Ipiranga Racing, onde eu devo terminar?"*

O dashboard conta com um modelo **Random Forest Regressor** treinado com o histórico da Stock Car. Ele faz o *feature engineering* da equipe (One-Hot Encoding) e da posição de largada para prever matematicamente a posição final, informando também o erro médio absoluto (MAE) do modelo.

![Machine Learning](assets/5_machine_learning.png)

---

## Como rodar

### Pré-requisitos
- Python 3.10+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e aberto

```bash
# 1. Clonar
git clone https://github.com/Cavalchi/StockCarKPIs.git
cd StockCarKPIs

# 2. Configurar variáveis de ambiente
cp .env.example .env          # edite se necessário (credenciais, porta, etc.)

# 3. Rodar tudo com o Makefile (Instala dependências, sobe DB, roda ETL e abre Dashboard)
make all

# --- Ou rodar os comandos individualmente ---
# make setup       (instala requirements e sobe o docker)
# make etl         (roda o pipeline de dados)
# make dashboard   (abre o streamlit)
# make test        (roda os testes automatizados)
```

---

## Estrutura

```
StockCarKPIs/
├── data/
│   └── raw/                 # CSVs por temporada (fonte dos dados 2022-2024)
├── stockcar_kpis/           # Pacote principal
│   ├── __init__.py
│   ├── config.py            # Configuração centralizada (DB, cores, constantes)
│   ├── etl/
│   │   ├── scraper.py       # Selenium: coleta do site oficial
│   │   └── load_db.py       # ETL: CSV → Validação → PostgreSQL
│   ├── analysis/
│   │   └── kpis.sql         # SQL das 4 análises + bônus
│   └── dashboard/
│       ├── app.py           # Gráficos estáticos (Matplotlib + Seaborn)
│       └── streamlit_app.py # Dashboard interativo (Streamlit + Plotly)
├── tests/
│   └── test_etl.py          # Testes unitários de validação (pytest)
├── db/
│   └── schema.sql           # Schema do banco (fonte única de verdade)
├── .env.example             # Template de variáveis de ambiente
├── Makefile                 # Automação de comandos (setup, etl, test, etc.)
├── docker-compose.yml       # PostgreSQL 15 em container
└── requirements.txt         # Dependências do projeto
```

---

<div align="center">

*Engenharia de Dados aplicada ao motorsport brasileiro*
*Dados coletados de fontes públicas — stockcar.com.br / Wikipedia*

</div>
