# Stock Car KPIs Analytics 🏎️📊

Pipeline de Engenharia de Dados aplicada ao motorsport brasileiro.
Coleta, armazena e analisa resultados da **Stock Car Brasil 2024** para gerar
métricas de performance que não estão disponíveis de forma direta nos dados brutos oficiais.

---

## O que este projeto faz

O site oficial da Stock Car publica resultados brutos — posições, tempos e pit stops corrida a corrida.
Este projeto vai além:

| Análise | O que revela |
|---|---|
| **Score de Consistência** | Qual piloto entrega resultados previsíveis? Desvio padrão das posições ao longo da temporada. |
| **Janela Ótima de Pit Stop** | Em quais voltas as equipes que subiram de posição fizeram a parada? Identifica o undercut e o overcut. |
| **ROI Esportivo** | Quantos % dos pontos possíveis a equipe conquistou? Mede eficiência real, não só pódios. |
| **Evolução por Etapa** | Como a performance de cada piloto evoluiu etapa a etapa? Tendência de desenvolvimento do carro. |

---

## Stack técnica

```
Python 3.10       Coleta (Selenium / web scraping) e orquestração do pipeline
PostgreSQL 15     Armazenamento estruturado com relações e constraints
Docker            Ambiente de banco isolado e reproduzível em qualquer máquina
SQLAlchemy        ORM / conexão Python → PostgreSQL
Pandas            Transformação e preparação dos DataFrames
Matplotlib        Visualizações com tema escuro e paleta por equipe
Seaborn           Gráficos estatísticos (scatter, tendência)
Git               Controle de versão
```

---

## Estrutura do projeto

```
StockCarKPIs/
├── scraper/
│   ├── scraper.py          # Selenium: tenta coleta real do site oficial
│   └── load_db.py          # ETL: cria schema, popula banco (8 etapas 2024)
├── analysis/
│   └── kpis.sql            # Todas as queries SQL das 4 análises + bônus Eurofarma
├── dashboard/
│   └── app.py              # Gera os 4 gráficos em ./output/
├── db/
│   └── schema.sql          # Schema de referência (corridas → resultados → pit_stops)
├── output/                 # Gráficos gerados (PNG, 150 DPI)
├── docker-compose.yml      # PostgreSQL 15 em container
└── requirements.txt        # Dependências Python
```

---

## Como rodar localmente

### 1. Pré-requisitos
- Python 3.10+
- Docker Desktop instalado e aberto

### 2. Clonar e instalar dependências
```bash
git clone https://github.com/Cavalchi/StockCarKPIs.git
cd StockCarKPIs
pip install -r requirements.txt
```

### 3. Subir o banco de dados
```bash
docker-compose up -d
```

### 4. Executar o pipeline ETL (cria tabelas + carrega dados)
```bash
python scraper/load_db.py
```

### 5. Gerar os gráficos de análise
```bash
python dashboard/app.py
```
Os 4 gráficos serão salvos em `./output/`.

---

## Análises geradas

### 1. Score de Consistência por Piloto
Mede o desvio padrão das posições finais de cada piloto ao longo de 8 etapas.
Um desvio padrão baixo significa que o piloto termina consistentemente na mesma região — característica
valiosíssima para estratégia de campeonato, especialmente em campeonatos de pontos acumulados.

### 2. Janela Ótima de Pit Stop
Cruza a volta em que cada equipe realizou o pit com o ganho/perda de posição resultante.
Identifica a faixa de voltas onde a probabilidade de subir posições é estatisticamente maior —
informação que orienta a decisão do wall engineer.

### 3. ROI Esportivo por Equipe
Divide os pontos conquistados pelos pontos máximos possíveis (se ganhasse todas as corridas).
Equipes com dois carros competitivos têm vantagem estrutural nessa métrica, o que ajuda a
identificar onde há ineficiência estratégica x limitação de equipamento.

### 4. Evolução de Performance por Etapa
Série temporal da posição de cada piloto etapa a etapa. Revela padrões de desenvolvimento:
quem melhorou no segundo semestre? Quem sofreu com mudanças de regulamento?

---

## Schema do banco de dados

```sql
corridas    (id, data, circuito, condicoes_pista, temporada)
    ↓
resultados  (id, corrida_id, piloto, equipe, posicao, posicao_largada, tempo_total, voltas, temporada)
pit_stops   (id, corrida_id, piloto, equipe, volta, duracao_s, temporada)
```

---

## Próximos passos

- [ ] Integrar dados de 2022 e 2023 para análise multi-temporada
- [ ] Dashboard interativo com Streamlit
- [ ] Modelo preditivo de posição final baseado em ritmo de volta e estratégia de pit
- [ ] Alerta automático de janela de undercut durante corrida ao vivo

---

*Desenvolvido como projeto de portfólio em Engenharia e Análise de Dados.*
*Dados coletados de fontes públicas (stockcar.com.br / Wikipedia).*
