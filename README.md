<div align="center">

# 🏎️ Stock Car KPIs Analytics

**Pipeline de Engenharia de Dados aplicada ao motorsport brasileiro**

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat-square&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.2-150458?style=flat-square&logo=pandas&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.8-white?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

*Transformando dados brutos da Stock Car Brasil em inteligência competitiva real*

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
┌─────────────────────┐      ┌──────────────────────┐      ┌─────────────────────┐
│   stockcar.com.br   │─────▶│  scraper/scraper.py  │─────▶│  PostgreSQL (Docker)│
│   (Selenium)        │      │  ETL / load_db.py    │      │  3 tabelas relacionadas│
└─────────────────────┘      └──────────────────────┘      └──────────┬──────────┘
                                                                        │
                                                            ┌───────────▼──────────┐
                                                            │  dashboard/app.py    │
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

## Como rodar

### Pré-requisitos
- Python 3.10+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e aberto

```bash
# 1. Clonar
git clone https://github.com/Cavalchi/StockCarKPIs.git
cd StockCarKPIs

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Subir o banco (PostgreSQL no Docker)
docker-compose up -d

# 4. Executar o pipeline ETL
python scraper/load_db.py

# 5. Gerar os 4 gráficos
python dashboard/app.py
# → Salvo em ./output/
```

---

## Estrutura

```
StockCarKPIs/
├── scraper/
│   ├── scraper.py       # Selenium: coleta real do site oficial
│   └── load_db.py       # ETL: schema + 8 etapas 2024 (80 resultados, 80 pit stops)
├── analysis/
│   └── kpis.sql         # SQL das 4 análises + bônus Eurofarma RC
├── dashboard/
│   └── app.py           # Geração dos 4 gráficos (matplotlib, seaborn)
├── assets/              # Charts para o README
├── db/
│   └── schema.sql       # Schema de referência
├── docker-compose.yml   # PostgreSQL 15 em container
└── requirements.txt
```

---

<div align="center">

*Engenharia de Dados aplicada ao motorsport brasileiro*
*Dados coletados de fontes públicas — stockcar.com.br / Wikipedia*

</div>
