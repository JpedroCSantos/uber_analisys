INSERT INTO silver.dim_payment_type (payment_type_id, description) VALUES
(0, 'Tarifa Flex (Flex Fare)'),
(1, 'Cartão de crédito'),
(2, 'Dinheiro'),
(3, 'Sem cobrança'),
(4, 'Disputa'),
(5, 'Desconhecido'),
(6, 'Corrida anulada');

INSERT INTO silver.dim_rate_code  (rate_code_id, description) VALUES
(1, 'Tarifa padrão'),
(2, 'JFK'),
(3, 'Newark'),
(4, 'Nassau ou Westchester'),
(5, 'Tarifa negociada'),
(6, 'Corrida em grupo'),
(99, 'Nulo/desconhecido');

INSERT INTO silver.dim_vendor (vendor_id, name) VALUES
(1, 'Creative Mobile Technologies, LLC'),
(2, 'Curb Mobility, LLC'),
(3, 'Myle Technologies Inc'),
(4, 'Helix')
