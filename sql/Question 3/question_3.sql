-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
-- SOLUÇÃO 1 UTILIZANDO RANK
-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
WITH zone_rank AS (
	SELECT 
		zone_name,
		borough,
		ROUND(avg_tip_amount, 2) AS avg_tip_amount,
		RANK() OVER(ORDER BY avg_tip_amount DESC) AS zone_rank
	FROM 
		gold.zone_payment_summary
	WHERE
		payment_name = 'Cartão de crédito'
)
SELECT * FROM zone_rank 
WHERE zone_rank <= 5

-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
-- SOLUÇÃO 2 UTILIZANDO LIMIT
-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
SELECT
    zone_name,
    borough,
    avg_tip_amount
FROM
    gold.zone_payment_summary
WHERE
    payment_name = 'Cartão de crédito'
ORDER BY
    avg_tip_amount DESC
LIMIT 5;
