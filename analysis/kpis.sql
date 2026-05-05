-- ===========================================================================
-- PROJETO STOCK CAR KPIs - ANÁLISE AVANÇADA DE PERFORMANCE
-- Temporada 2024 | 8 etapas | 10 pilotos
-- ===========================================================================

-- ===========================================================================
-- ANÁLISE 1: SCORE DE CONSISTÊNCIA POR PILOTO
-- Desvio padrão das posições finais ao longo da temporada.
-- Piloto consistente = desvio baixo = mais previsível e valioso para estratégia.
-- ===========================================================================
SELECT
    piloto,
    equipe,
    COUNT(*)                            AS corridas_disputadas,
    ROUND(AVG(posicao)::numeric, 2)     AS media_posicao,
    ROUND(STDDEV(posicao)::numeric, 2)  AS desvio_padrao_posicao,
    MIN(posicao)                        AS melhor_resultado,
    MAX(posicao)                        AS pior_resultado,
    -- Score normalizado 0-100 (100 = consistência máxima)
    ROUND(
        100 - (STDDEV(posicao) / NULLIF(AVG(posicao), 0) * 100)::numeric,
        1
    ) AS score_consistencia
FROM resultados
WHERE temporada = 2024
GROUP BY piloto, equipe
HAVING COUNT(*) >= 4
ORDER BY desvio_padrao_posicao ASC, media_posicao ASC;


-- ===========================================================================
-- ANÁLISE 2: JANELA ÓTIMA DE PIT STOP
-- Relação entre a volta do pit e o ganho/perda de posição na corrida.
-- Identifica em quais voltas as equipes que avançaram mais posições pitaram.
-- ===========================================================================
SELECT
    p.equipe,
    p.volta                              AS volta_pit,
    ROUND(AVG(p.duracao_s)::numeric, 2)  AS duracao_media_s,
    ROUND(AVG((r.posicao_largada - r.posicao))::numeric, 1) AS ganho_medio_posicoes,
    COUNT(*)                             AS total_paradas
FROM pit_stops p
JOIN resultados r ON p.corrida_id = r.corrida_id AND p.piloto = r.piloto
WHERE p.temporada = 2024
GROUP BY p.equipe, p.volta
ORDER BY ganho_medio_posicoes DESC, duracao_media_s ASC;

-- Versão agregada: ganho médio por faixa de volta (estratégia geral)
SELECT
    CASE
        WHEN p.volta BETWEEN 12 AND 13 THEN 'Volta 12-13 (Undercut)'
        WHEN p.volta BETWEEN 14 AND 15 THEN 'Volta 14-15 (Janela Ótima)'
        WHEN p.volta BETWEEN 16 AND 17 THEN 'Volta 16-17 (Overcut)'
        ELSE 'Volta 18+'
    END AS faixa_estrategica,
    ROUND(AVG((r.posicao_largada - r.posicao))::numeric, 2) AS ganho_medio_posicoes,
    COUNT(*) AS n
FROM pit_stops p
JOIN resultados r ON p.corrida_id = r.corrida_id AND p.piloto = r.piloto
WHERE p.temporada = 2024
GROUP BY faixa_estrategica
ORDER BY ganho_medio_posicoes DESC;


-- ===========================================================================
-- ANÁLISE 3: ROI ESPORTIVO POR EQUIPE
-- (Pontos conquistados / Pontos máximos possíveis) x 100
-- Equipes com dois carros competitivos têm vantagem no ROI coletivo.
-- ===========================================================================
WITH pontos_sistema AS (
    SELECT
        equipe,
        SUM(
            CASE posicao
                WHEN 1  THEN 25 WHEN 2  THEN 20 WHEN 3  THEN 16
                WHEN 4  THEN 13 WHEN 5  THEN 11 WHEN 6  THEN 9
                WHEN 7  THEN 7  WHEN 8  THEN 5  WHEN 9  THEN 3
                WHEN 10 THEN 1  ELSE 0
            END
        )                AS pontos_conquistados,
        COUNT(*) * 25    AS pontos_maximos_possiveis,
        COUNT(*)         AS participacoes
    FROM resultados
    WHERE temporada = 2024
    GROUP BY equipe
)
SELECT
    equipe,
    pontos_conquistados,
    pontos_maximos_possiveis,
    participacoes,
    ROUND(
        (pontos_conquistados::numeric / pontos_maximos_possiveis) * 100,
        1
    ) AS roi_esportivo_pct
FROM pontos_sistema
ORDER BY roi_esportivo_pct DESC;


-- ===========================================================================
-- ANÁLISE 4: EVOLUÇÃO DE PERFORMANCE POR ETAPA (Série temporal)
-- Posição de cada piloto etapa a etapa para identificar tendência de
-- desenvolvimento do carro e recuperações/quedas de performance.
-- ===========================================================================
SELECT
    c.data,
    c.circuito,
    r.piloto,
    r.equipe,
    r.posicao_largada,
    r.posicao                AS posicao_final,
    (r.posicao_largada - r.posicao) AS posicoes_ganhas,
    p.duracao_s              AS pit_duracao_s,
    p.volta                  AS pit_volta
FROM resultados r
JOIN corridas c ON r.corrida_id = c.id
LEFT JOIN pit_stops p ON p.corrida_id = r.corrida_id AND p.piloto = r.piloto
WHERE r.temporada = 2024
ORDER BY c.data, r.posicao;


-- ===========================================================================
-- BONUS: RANKING EUROFARMA RC - ANÁLISE INTERNA DA EQUIPE
-- Quão bem cada piloto aproveitou as oportunidades da equipe?
-- ===========================================================================
SELECT
    r.piloto,
    COUNT(*)                            AS corridas,
    ROUND(AVG(r.posicao)::numeric, 1)   AS media_posicao,
    ROUND(STDDEV(r.posicao)::numeric, 2) AS consistencia,
    ROUND(AVG(p.duracao_s)::numeric, 2)  AS media_pit_s,
    SUM(CASE WHEN r.posicao <= 3 THEN 1 ELSE 0 END) AS podios,
    SUM(CASE WHEN r.posicao = 1 THEN 1 ELSE 0 END)  AS vitorias
FROM resultados r
LEFT JOIN pit_stops p ON p.corrida_id = r.corrida_id AND p.piloto = r.piloto
WHERE r.equipe = 'Eurofarma RC'
  AND r.temporada = 2024
GROUP BY r.piloto
ORDER BY media_posicao ASC;
