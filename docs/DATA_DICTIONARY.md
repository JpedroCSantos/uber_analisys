# Dicionário de Dados - Registros de Corridas de Táxi Amarelo

**Data do Documento:** 18 de Março de 2025

Este dicionário de dados descreve os dados de corridas de táxi amarelo. Para dicionários de dados envolvendo outros tipos de corrida e metadados como as Zonas de Táxi da TLC, por favor visite: http://www.nyc.gov/html/tlc/html/about/trip_record_data.shtml.

| Nome do Campo | Descrição |
| --- | --- |
| **VendorID** | Um código que indica o provedor TPEP que forneceu o registro. <br> `1` = Creative Mobile Technologies, LLC <br> `2` = Curb Mobility, LLC <br> `6` = Myle Technologies Inc <br> `7` = Helix |
| **tpep_pickup_datetime** | A data e a hora em que o taxímetro foi acionado (início da corrida). |
| **tpep_dropoff_datetime** | A data e a hora em que o taxímetro foi desativado (fim da corrida). |
| **passenger_count** | O número de passageiros no veículo. |
| **trip_distance** | A distância da corrida percorrida em milhas, reportada pelo taxímetro. |
| **RatecodeID** | O código da tarifa final em vigor no final da corrida. <br> `1` = Tarifa padrão <br> `2` = JFK <br> `3` = Newark <br> `4` = Nassau ou Westchester <br> `5` = Tarifa negociada <br> `6` = Corrida em grupo <br> `99` = Nulo/desconhecido |
| **store_and_fwd_flag** | Esta flag indica se o registro da corrida foi mantido na memória do veículo antes de ser enviado para o fornecedor (conhecido como "armazenar e encaminhar"), porque o veículo não tinha conexão com o servidor. <br> `Y` = corrida do tipo "armazenar e encaminhar" <br> `N` = não é uma corrida "armazenar e encaminhar" |
| **PULocationID** | Zona de Táxi da TLC na qual o taxímetro foi acionado (local de embarque). |
| **DOLocationID** | Zona de Táxi da TLC na qual o taxímetro foi desativado (local de desembarque). |
| **payment_type** | Um código numérico que significa como o passageiro pagou pela corrida. <br> `0` = Tarifa Flex (Flex Fare) <br> `1` = Cartão de crédito <br> `2` = Dinheiro <br> `3` = Sem cobrança <br> `4` = Disputa <br> `5` = Desconhecido <br> `6` = Corrida anulada |
| **fare_amount** | A tarifa de tempo e distância calculada pelo taxímetro. |
| **extra** | Extras e sobretaxas diversas. |
| **mta_tax** | Imposto que é acionado automaticamente com base na tarifa medida em uso. |
| **tip_amount** | Valor da gorjeta. Este campo é preenchido automaticamente para gorjetas no cartão de crédito. Gorjetas em dinheiro não são incluídas. |
| **tolls_amount** | Valor total de todos os pedágios pagos na corrida. |
| **improvement_surcharge** | Sobretaxa de melhoria aplicada às corridas no início da marcação ("bandeirada"). A sobretaxa de melhoria começou a ser cobrada em 2015. |
| **total_amount** | O valor total cobrado dos passageiros. Não inclui gorjetas em dinheiro. |
| **congestion_surcharge** | Valor total coletado na corrida para a sobretaxa de congestionamento do estado de Nova York (NYS). |
| **airport_fee** | Apenas para embarques nos aeroportos LaGuardia e John F. Kennedy. |
| **cbd_congestion_fee** | Cobrança por corrida para a Zona de Alívio de Congestionamento da MTA, a partir de 5 de janeiro de 2025. |