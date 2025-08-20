-- Carregamento da tabela de dimensão de zonas
-- Baseado no arquivo taxi_zone_lookup.csv

INSERT INTO silver.dim_zone (zone_id, borough, zone_name, service_zone) 
VALUES 
    (1, 'EWR', 'Newark Airport', 'EWR'),
    (2, 'Queens', 'Jamaica Bay', 'Boro Zone'),
    (3, 'Bronx', 'Allerton/Pelham Gardens', 'Boro Zone'),
    (4, 'Manhattan', 'Alphabet City', 'Yellow Zone'),
    (5, 'Staten Island', 'Arden Heights', 'Boro Zone')
-- Adicione mais zonas conforme necessário ou use COPY FROM para carregar do CSV

ON CONFLICT (zone_id) DO UPDATE SET
    borough = EXCLUDED.borough,
    zone_name = EXCLUDED.zone_name,
    service_zone = EXCLUDED.service_zone;

