-- Pergunta: Qual a média de corridas por hora e qual a diferença em relação à hora anterior?

-- CTE 1: Calcula o número de dias distintos no período
WITH total_days AS (
    SELECT
        COUNT(DISTINCT DATE_TRUNC('day', pickup_at)) AS distinct_day_count
    FROM
        silver.fact_trips_2025_01
),

-- CTE 2: Calcula a média de corridas por hora (a nossa query anterior)
hourly_averages AS (
    SELECT
        ft.hour_of_day,
        ROUND(
            CAST(COUNT(ft.trip_id) AS NUMERIC) / (SELECT distinct_day_count FROM total_days),
            2
        ) AS avg_trips_per_hour
    FROM
        silver.fact_trips_2025_01 AS ft
    CROSS JOIN
        total_days
    GROUP BY
        ft.hour_of_day,
        total_days.distinct_day_count
),

-- Query Final: Aplica a função de janela sobre os resultados já agregados
final_analysis AS (
    SELECT
        ha.hour_of_day,
        ha.avg_trips_per_hour,
        -- Aplica a função LAG() sobre a janela de todas as horas ordenadas
        LAG(ha.avg_trips_per_hour, 1, 0) OVER (ORDER BY ha.hour_of_day) AS previous_hour_avg
    FROM
        hourly_averages AS ha
)

-- Seleção final para calcular a diferença
SELECT
    fa.hour_of_day,
    fa.avg_trips_per_hour,
    fa.previous_hour_avg,
    -- Calcula a diferença entre a média da hora atual e a da hora anterior
    (fa.avg_trips_per_hour - fa.previous_hour_avg) AS hour_difference
FROM
    final_analysis AS fa
ORDER BY
    fa.hour_of_day;