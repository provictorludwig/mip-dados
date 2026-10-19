# Valor adicionado por transbordamento nos municípios do Rio Grande do Sul, 2037

Operação de nicotina sem fumaça em Santa Cruz do Sul. Valores em reais de 2025. Peça para leitura com o mapa estadual (`mapa_transbordamento_rs.png`), o recorte do Vale (`mapa_vale_zoom.png`) e a prancha (`prancha_governador.pdf`).

O cenário que esta conta reparte é o **cenário base vigente no arquivo de resultados**: abertura estimada da lista de materiais (BOM), conteúdo local não agrícola implícito de **9,9%**, com exportação. Nesse cenário o valor adicionado direto da planta é **R$ 7,83 bilhões**, o valor adicionado da cadeia é **R$ 498,9 milhões** e o valor adicionado induzido, em uma rodada, é **R$ 370,8 milhões**. A faixa uniforme de conteúdo local (10%, 20% e 35%) continua no estudo como sensibilidade. No ponto de 20% a cadeia fica perto de R$ 938 milhões e o induzido perto de R$ 455 milhões. O mapa usa o base vigente, o de 9,9%, e declara isso para a soma municipal fechar com o total que o modelo de insumo-produto já calculou para o Estado.

O transbordamento alocado é a soma da cadeia com o induzido: **R$ 869,7 milhões**. A soma dos 497 municípios é esse mesmo valor. O direto de R$ 7,83 bilhões fica registrado à parte, inteiro em Santa Cruz do Sul, e não entra na cor do mapa.

## O que é transbordamento nesta conta

Transbordamento, aqui, é o valor adicionado que a operação gera **fora da planta**, ainda que parte dele volte a cair no município da sede. São três peças, todas já fechadas na matriz de insumo-produto do Rio Grande do Sul antes de qualquer mapa:

1. **A cadeia produtiva.** Compras de fumo em folha, papel, eletrônicos, químicos, energia, transporte, comércio e os demais serviços que a lista de materiais puxa dentro do Estado. Valor adicionado dessa cadeia: R$ 498,9 milhões.
2. **O salário de quem trabalha na planta e mora em outro município.** A remuneração direta é R$ 609 milhões. A maior parte dos ocupados da sede mora em Santa Cruz do Sul. Uma parcela mora em Vera Cruz, Venâncio Aires, Rio Pardo, Vale do Sol e nos demais municípios de deslocamento diário. Essa parcela leva consumo para a casa, não para o portão da fábrica.
3. **O consumo induzido de uma rodada.** O salário direto e o salário da cadeia viram gasto das famílias dentro do Estado e esse gasto vira valor adicionado em comércio e serviços. São R$ 370,8 milhões.

A conta municipal **reparte** esses dois totais (cadeia e induzido). Ela não recalcula a matriz, não estima um coeficiente de defasagem espacial e não cria valor adicionado novo. O que o mapa mostra é onde esse valor adicionado já calculado se apoia: na folha, no fornecedor e na casa de quem recebe o salário.

Dentro dos R$ 869,7 milhões, os quatro componentes fecham assim:

| Componente | R$ milhões | O que o mapa lê |
|---|---:|---|
| Folha e valor adicionado agrícola da cadeia | 30,7 | Mancha leve no sul e no Vale, no peso da PAM |
| Indústria da cadeia | 321,3 | Papel, eletrônicos e o restante da indústria, com distância até a sede |
| Comércio, transporte e serviços da cadeia | 146,8 | Metade segue a casa do salário direto; metade segue o emprego do setor |
| Induzido, uma rodada | 370,8 | 76,5% segue a casa do salário direto; o resto, um núcleo gravitacional |
| **Transbordamento** | **869,7** | Soma dos municípios |

A indústria da cadeia, neste cenário, é sobretudo **papel (R$ 146,8 milhões)** e **eletrônicos (R$ 92,1 milhões)**. Químicos ficam em R$ 11,8 milhões. Energia e água, R$ 27,8 milhões. O restante da indústria de transformação, R$ 23,7 milhões. A frase do mapa acompanha essa composição: a mancha forte fora do Vale é fornecedor de papel e de eletrônicos, com desconto de distância, e a mancha forte dentro do Vale é salário e serviço local.

## Por que os R$ 7,83 bilhões ficam fora da escala

O valor adicionado direto é a produção no estabelecimento, em Santa Cruz do Sul. São R$ 7,83 bilhões, 4.060 ocupações diretas e R$ 609 milhões de salário direto. Cem por cento desse valor adicionado permanecem no município-sede. Colocá-lo na mesma escala do transbordamento apaga o Estado: o maior transbordamento municipal fora da sede é R$ 23 milhões em Porto Alegre, e o direto é cerca de 340 vezes isso.

A peça auxiliar `mapa_com_direto.png` faz exatamente esse exercício, de propósito. As classes vão de R$ 500 milhões até o máximo (Santa Cruz do Sul, direto mais transbordamento, cerca de R$ 8,17 bilhões). O Estado inteiro cai na classe clara e a sede fica isolada no azul escuro. Essa figura explica a escala. **A peça de decisão é o mapa de transbordamento**, em que Santa Cruz do Sul recebe só os R$ 340,0 milhões de cadeia e induzido que a regra atribui ao município, e o direto aparece como número próprio ao lado.

No mapa principal, zero e quase zero são cinza neutro (`#d0d0d0`). Valor positivo segue uma rampa de azul claro (`#deebf7`) a azul escuro (`#08306b`). A classe cinza junta o que fica abaixo de R$ 50 mil: 116 municípios, R$ 1,8 milhão no total, 0,21% do transbordamento. Esse dinheiro permanece no CSV, para a soma municipal continuar igual ao total estadual. Dois municípios fecham em zero estrutural, Barra do Quaraí e Chuí: sem folha na PAM, sem emprego setorial publicado dentro do raio e sem deslocamento diário até a sede.

## Como o total estadual vira município

A regionalização é contábil e espacial. Cada real de valor adicionado da cadeia e do induzido recebe um município por uma chave explícita. As chaves somam 1. A fórmula está no anexo. Os parâmetros de referência são **α = 0,5** e **λ = 100 km** para fornecedor e para a presença de serviços. A pendularidade usa outro alcance, **λ_c = 28 km**, porque deslocamento casa-trabalho é deslocamento diário. O consumo induzido que não segue a casa do salário direto usa **λ_g = 75 km**.

### Direto

Cem por cento em Santa Cruz do Sul. Fora da mancha. Registrado na coluna `va_direto_mi` de `va_por_municipio.csv`, positiva em um único município.

### Folha

A premissa do estudo é que, em 2037, a operação compra no Rio Grande do Sul **0,86%** da produção municipal de fumo em folha. A produção é a PAM do IBGE, SIDRA tabela 1612, produto fumo em folha, variável quantidade produzida, ano **2025**, o mais recente disponível na data desta conta. O Estado soma **349.928 toneladas**. Aplicada a fração, são **3.009,4 toneladas**. A âncora do estudo para a compra no Rio Grande do Sul é **3.007 toneladas** e **R$ 52,8 milhões** na porteira. A diferença é **+2,4 toneladas (0,08%)**. Ela fica explícita. O valor adicionado agrícola da cadeia não é o valor bruto da compra: depois do coeficiente da matriz, a agricultura (atividade 01) vale **R$ 30,7 milhões**. Esse valor adicionado reparte-se pelos mesmos pesos da PAM, e a soma municipal fecha nos R$ 30,7 milhões.

Os maiores pesos de folha em 2025, e a compra nova correspondente (PAM × 0,86%):

| Município | PAM 2025 (t) | Compra nova 2037 (t) | VA agrícola (R$ mi) |
|---|---:|---:|---:|
| Canguçu | 26.156 | 224,9 | 2,3 |
| São Lourenço do Sul | 21.600 | 185,8 | 1,9 |
| Venâncio Aires | 21.242 | 182,7 | 1,9 |
| Candelária | 13.500 | 116,1 | 1,2 |
| Arroio do Tigre | 13.464 | 115,8 | 1,2 |
| Dom Feliciano | 13.275 | 114,2 | 1,2 |
| Camaquã | 13.020 | 112,0 | 1,1 |
| Vale do Sol | 12.974 | 111,6 | 1,1 |
| Santa Cruz do Sul | 12.610 | 108,4 | 1,1 |

Santa Cruz do Sul, na PAM 2025, confirma as 12.610 toneladas citadas nas premissas. Canguçu, Venâncio Aires, São Lourenço do Sul e Candelária estão acima dos exemplos de imprensa que as premissas guardavam (21.064, 17.779, 16.374 e 11.462 toneladas). O mapa usa a SIDRA, não o recorte de imprensa. A folha é visível e é pequena: R$ 30,7 milhões em R$ 869,7 milhões, isto é, **3,5%** do transbordamento. Ela pinta uma mancha leve no sul e no Vale. Ela não pinta o azul escuro.

### Indústria da cadeia

Papel, químicos, eletrônicos e o restante da indústria **não** são jogados em Porto Alegre. O peso do município é o emprego formal do setor, comprimido por α, vezes um decaimento exponencial da distância até Santa Cruz do Sul, e zero além de 260 km. O peso é normalizado para somar 1 dentro do Estado. Emprego vem do CEMPRE, SIDRA tabela 6450, pessoal ocupado total, ano **2021** (último ano da tabela; a série municipal por divisão foi encerrada). Célula suprimida pelo sigilo (“-”) entra como zero e o peso se renormaliza sobre o emprego publicado. Isso puxa a indústria para as plantas grandes o suficiente para aparecer na tabela. É um viés conhecido e está declarado na nota de método.

Cada bloco industrial usa o emprego da sua divisão (papel na 17, eletrônicos na 26, químicos na 20, e assim por diante; a lista fechada está na nota de método). A fabricação de produtos do fumo, divisão 12, fica de fora desse peso: o emprego publicado está em Santa Cruz do Sul (3.155 pessoas), Venâncio Aires (1.710) e Vera Cruz (253), e usá-lo como ímã colocaria papel e eletrônicos em cima da própria indústria do fumo. A cadeia de papel vai para onde há fábrica de papel dentro do raio: Guaíba, Campo Bom, Caxias do Sul, Farroupilha, Canoas. A de eletrônicos vai para Eldorado do Sul, Gravataí, Porto Alegre e Caxias do Sul. Rio Grande tem emprego químico publicado alto e fica de fora do núcleo porque a distância até a sede passa do corte.

Com λ de 100 km, **89,5%** do valor adicionado industrial da cadeia cai **fora** do COREDE Vale do Rio Pardo (R$ 287,6 milhões de R$ 321,3 milhões). Dentro do COREDE ficam R$ 33,7 milhões. Porto Alegre, sozinha, fica com R$ 23,1 milhões de transbordamento, dos quais R$ 15,2 milhões são indústria. O conjunto de municípios a até 40 km do centroide de Porto Alegre reúne **16,2%** do transbordamento. A capital aparece, e aparece junto com Eldorado do Sul, Guaíba, Canoas, Campo Bom e a Serra. Ela não absorve a cadeia.

### Serviços da cadeia e consumo induzido

Comércio, transporte e serviços não têm um único endereço. A regra de referência reparte cada bloco em duas chaves:

- uma parte segue a **residência** de quem trabalha em Santa Cruz do Sul (a pendularidade π);
- a outra segue o emprego do próprio setor, com o mesmo núcleo de distância usado na indústria.

Comércio, transporte e informação usam metade e metade. Alojamento, alimentação e serviços sociais usam 70% na residência, porque acompanham a casa e a rua de quem mora. Finanças, serviços profissionais e administrativos usam 25% na residência e 75% na praça em que o setor já está. Atividades imobiliárias usam 60% na residência. Administração pública da cadeia, pequena nesta conta, segue inteira a residência. São escolhas declaradas, não elasticidades estimadas.

A residência π vem do Censo Demográfico 2022, SIDRA tabela 10329: para cada município, quantas pessoas ocupadas trabalham no próprio município de residência e quantas trabalham em outro. O microdado público do Censo 2022 não traz o município de destino do trabalho. A parcela que mora na sede é a que o Censo conta como ocupada no próprio município: **64.071** pessoas em Santa Cruz do Sul. A parcela que mora fora é o contingente que trabalha em outro município, repartido por destinos concorrentes: a atração é o emprego formal total do CEMPRE, o decaimento é λ_c de 28 km, e o deslocamento atribuído à sede zera além de 110 km. O modelo coloca **6.068** pessoas entrando em Santa Cruz do Sul para trabalhar. A fatia da sede fica em **91,3%**.

Uma chave independente, já registrada no arquivo de resultados e **não usada como insumo desta conta**, reproduz o deslocamento casa-trabalho do Censo 2010 (Revista Jovens Pesquisadores, UNISC, 2015) e chega a **91,8%** de residência em Santa Cruz do Sul. As duas leituras, uma de 2022 modelada e uma de 2010 contada no destino, ficam a menos de um ponto percentual. O anel existe e é fino em dinheiro.

O induzido parte da mesma lógica. A remuneração direta é R$ 609 milhões e a remuneração da cadeia é R$ 187,1 milhões, de modo que **76,5%** do valor adicionado induzido segue a casa do salário direto (π). Os outros **23,5%** seguem um núcleo gravitacional: a massa de valor adicionado da cadeia já alocada em cada município puxa consumo para os municípios vizinhos, com população^0,5 e decaimento de 75 km, até 180 km. O interior não zera por falta de capital, e a capital não recebe o salário de quem mora no Vale.

Por isso Santa Cruz do Sul é o município mais azul **do mapa de transbordamento**, com R$ 340,0 milhões, e esse azul é salário e serviço, não a planta:

| Peça, só em Santa Cruz do Sul | R$ milhões |
|---|---:|
| Folha | 1,1 |
| Indústria da cadeia | 18,4 |
| Serviços da cadeia | 60,0 |
| Induzido | 260,5 |
| **Transbordamento na sede** | **340,0** |
| Direto da planta, fora da cor | 7.830,0 |

## O alcance de 100 km, e o que muda se ele mudar

λ é a distância em que o peso de um fornecedor cai a cerca de 37% do peso que teria junto à sede, para o mesmo emprego. A banda pedida para essa escolha é 80 a 150 km. O valor de referência é **100 km**, o meio da banda: curto o bastante para o Vale e o entorno pesarem na indústria que de fato existe ali (Vera Cruz, Venâncio Aires, Lajeado, Estrela), longo o bastante para Guaíba, Eldorado do Sul, Canoas e Caxias do Sul permanecerem na mancha de papel e de eletrônicos. Abaixo disso a Serra some cedo demais. Acima disso a capital e Caxias passam a dividir fornecedor que, na operação, concorre com plantas mais próximas.

A pendularidade **não** usa esse λ. O salário mora onde o Censo e o deslocamento diário mandam. Por isso a sensibilidade mexe na mancha do fornecedor e quase não mexe no azul da sede.

| λ (km) | COREDE | Sede (R$ mi) | O que a ordem mostra |
|---:|---:|---:|---|
| 80 | 47,2% | 346,7 | Vera Cruz passa à frente de Porto Alegre |
| **100** | **45,9%** | **340,0** | Referência desta prancha |
| 150 | 44,4% | 333,1 | Caxias do Sul entra entre os cinco primeiros |

Com α = 1, no mesmo λ de 100 km, o emprego grande pesa por inteiro, o COREDE cai a 43,5% e a sede fica em R$ 332,9 milhões. α = 0,5 comprime a diferença entre uma planta de milhares de postos e uma planta média, para o sigilo do CEMPRE não entregar a cadeia inteira ao primeiro município que publicou a célula. Também é escolha, e está na sensibilidade.

## Os quinze municípios mais azuis

Percentuais sobre os R$ 869,7 milhões. Componentes em R$ milhões.

| | Município | Transbordamento | % | Folha | Indústria | Serviços | Induzido | COREDE |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Santa Cruz do Sul | 340,0 | 39,1 | 1,1 | 18,4 | 60,0 | 260,5 | sim |
| 2 | Porto Alegre | 23,1 | 2,7 | 0 | 15,2 | 4,0 | 3,9 | |
| 3 | Eldorado do Sul | 20,1 | 2,3 | 0 | 18,6 | 0,7 | 0,8 | |
| 4 | Vera Cruz | 19,8 | 2,3 | 0,7 | 9,6 | 2,3 | 7,2 | sim |
| 5 | Guaíba | 17,9 | 2,1 | 0 | 16,2 | 0,8 | 1,0 | |
| 6 | Canoas | 17,2 | 2,0 | 0 | 13,4 | 1,6 | 2,2 | |
| 7 | Caxias do Sul | 16,8 | 1,9 | 0 | 13,4 | 1,5 | 1,8 | |
| 8 | São Leopoldo | 14,8 | 1,7 | 0 | 11,9 | 1,1 | 1,8 | |
| 9 | Lajeado | 14,1 | 1,6 | 0 | 8,9 | 2,5 | 2,7 | |
| 10 | Gravataí | 13,8 | 1,6 | 0 | 11,3 | 0,8 | 1,7 | |
| 11 | Estrela | 13,1 | 1,5 | 0 | 10,6 | 1,2 | 1,3 | |
| 12 | Campo Bom | 12,7 | 1,5 | 0 | 11,1 | 0,7 | 0,9 | |
| 13 | Cachoeirinha | 11,9 | 1,4 | 0 | 9,7 | 0,9 | 1,3 | |
| 14 | Bento Gonçalves | 11,9 | 1,4 | 0 | 9,4 | 1,3 | 1,3 | |
| 15 | Farroupilha | 10,6 | 1,2 | 0 | 8,9 | 0,8 | 0,9 | |

Os quinze somam cerca de **64%** do transbordamento. A sede, sozinha, é 39%. Do segundo ao décimo quinto, nenhum passa de 3%. Eldorado do Sul e Guaíba ficam à frente de vários municípios maiores porque o emprego publicado de eletrônicos e de papel, descontado a distância, pesa mais do que a população.

## COREDE Vale do Rio Pardo, sede e resto do Estado

A lista oficial tem **23 municípios**, a do artigo 3º do estatuto do COREDE Vale do Rio Pardo e a do Plano Estratégico de Desenvolvimento 2022–2030 do Conselho: Arroio do Tigre, Boqueirão do Leão, Candelária, Encruzilhada do Sul, Estrela Velha, General Câmara, Herveiras, Ibarama, Lagoa Bonita do Sul, Mato Leitão, Pantano Grande, Passa Sete, Passo do Sobrado, Rio Pardo, Santa Cruz do Sul, Segredo, Sinimbu, Sobradinho, Tunas, Vale do Sol, Vale Verde, Venâncio Aires e Vera Cruz. O contorno ocre dos mapas segue essa lista. Gramado Xavier fica de fora, como na relação do Estado.

| Recorte | R$ milhões | % do transbordamento | Folha | Indústria | Serviços | Induzido |
|---|---:|---:|---:|---:|---:|---:|
| Santa Cruz do Sul, só transbordamento | 340,0 | 39,1 | 1,1 | 18,4 | 60,0 | 260,5 |
| COREDE sem a sede | 58,9 | 6,8 | 11,6 | 15,3 | 10,9 | 21,1 |
| **COREDE, 23 municípios** | **398,9** | **45,9** | **12,7** | **33,7** | **70,9** | **281,6** |
| Resto do Rio Grande do Sul | 470,8 | 54,1 | 18,0 | 287,6 | 75,9 | 89,2 |
| Estado | 869,7 | 100 | 30,7 | 321,3 | 146,8 | 370,8 |
| Direto da planta, só na sede, fora da cor | 7.830,0 | — | — | — | — | — |

O COREDE fica com **45,9%** do transbordamento. Tira-se a sede e o restante do Conselho fica com **6,8%**. O resto do Estado fica com **54,1%**, e esse resto é sobretudo indústria (R$ 287,6 milhões). A folha do COREDE é R$ 12,7 milhões; a folha de fora, R$ 18,0 milhões, com Canguçu e São Lourenço do Sul na frente.

Os 23, em R$ milhões de transbordamento. Toneladas de PAM 2025 e toneladas da compra nova (PAM × 0,86%). A soma arredondada da tabela reconcilia com os R$ 398,9 milhões do arquivo `corede_vale.csv`.

| Município | Transbordamento | PAM 2025 (t) | Compra nova (t) |
|---|---:|---:|---:|
| Santa Cruz do Sul | 340,0 | 12.610 | 108 |
| Vera Cruz | 19,8 | 8.126 | 70 |
| Venâncio Aires | 9,3 | 21.242 | 183 |
| Rio Pardo | 4,5 | 5.474 | 47 |
| Candelária | 3,7 | 13.500 | 116 |
| Vale do Sol | 2,9 | 12.974 | 112 |
| Sinimbu | 2,7 | 7.560 | 65 |
| Arroio do Tigre | 1,9 | 13.464 | 116 |
| Passo do Sobrado | 1,6 | 4.098 | 35 |
| Sobradinho | 1,6 | 3.420 | 29 |
| Boqueirão do Leão | 1,4 | 7.906 | 68 |
| Mato Leitão | 1,3 | 175 | 2 |
| Segredo | 1,1 | 7.115 | 61 |
| Encruzilhada do Sul | 1,0 | 521 | 4 |
| Passa Sete | 0,9 | 5.500 | 47 |
| Pantano Grande | 0,8 | 7 | 0 |
| General Câmara | 0,8 | 1.144 | 10 |
| Ibarama | 0,7 | 5.063 | 44 |
| Herveiras | 0,7 | 3.830 | 33 |
| Vale Verde | 0,6 | 1.920 | 17 |
| Estrela Velha | 0,5 | 3.360 | 29 |
| Lagoa Bonita do Sul | 0,5 | 2.788 | 24 |
| Tunas | 0,4 | 2.800 | 24 |

Onde a residência do trabalho na sede se apoia, no modelo: Santa Cruz do Sul 91,3%; Vera Cruz 2,3% (15 km); Rio Pardo 0,8% (42 km); Venâncio Aires 0,7% (22 km); Lajeado 0,5% (45 km); Vale do Sol e Candelária 0,3% cada. Lajeado e Estrela aparecem alto na tabela dos quinze pela indústria e pelo serviço do Vale do Taquari, a uma hora da sede, e não porque o COREDE os inclua. Os dois ficam de fora do contorno ocre, e o mapa deixa isso visível.

## Como ler a prancha

Há duas manchas, e elas contam coisas diferentes.

A mancha do **Vale do Rio Pardo** é a casa do salário e o serviço que acompanha essa casa. Santa Cruz do Sul, no azul mais escuro, são R$ 340 milhões de transbordamento: cerca de R$ 260 milhões de consumo induzido de quem mora na sede e R$ 60 milhões de serviço da cadeia. O anel imediato é mais claro e é real: Vera Cruz (R$ 19,8 milhões), Venâncio Aires (R$ 9,3 milhões), depois Rio Pardo, Candelária e Vale do Sol. O contorno ocre fecha os 23 municípios. O COREDE inteiro soma R$ 399 milhões, **45,9%** do transbordamento. Sem a sede, o Conselho soma R$ 59 milhões.

A mancha da **folha** é outra, e é leve. Canguçu, São Lourenço do Sul e Venâncio Aires lideram as toneladas. O valor adicionado agrícola da cadeia inteira é R$ 31 milhões. Não é essa a origem do azul escuro.

A mancha da **região metropolitana e da Serra** é fornecedor. Porto Alegre (R$ 23 milhões), Eldorado do Sul (R$ 20 milhões, eletrônicos), Guaíba (R$ 18 milhões, papel), Canoas, Caxias do Sul, São Leopoldo, Gravataí, Campo Bom, Farroupilha e Bento Gonçalves formam um arquipélago azul médio, separado do Vale por municípios mais claros. Neste cenário de abertura da lista de materiais, papel e eletrônicos dominam essa mancha. Químicos são uma fatia pequena. A Campanha e o extremo oeste ficam cinza: sem folha relevante na conta, sem emprego setorial publicado dentro do raio e sem deslocamento diário até Santa Cruz do Sul.

O zoom do Vale usa **as mesmas classes do mapa estadual**. Um azul no recorte é o mesmo azul no Estado. A barra de 30 km e a seta de norte estão no recorte; a barra de 100 km, no mapa cheio. O direto de R$ 7,83 bilhões permanece escrito ao lado, inteiro em Santa Cruz do Sul, fora da cor.

Três números, os da prancha: transbordamento **R$ 870 milhões**; COREDE **R$ 399 milhões (45,9%)**; resto do Estado **R$ 471 milhões (54,1%)**. O direto, ao lado: **R$ 7,83 bilhões** na sede.

## O que esta conta não faz

Ela reparte um total estadual já calculado. Não é um modelo de equilíbrio espacial, não estima ρ e não substitui a matriz. Distância é a reta entre centroides municipais na projeção equivalente do Estado, não a distância de rodovia e não a coordenada do portão da fábrica. As premissas mandam usar a sede municipal.

O CEMPRE municipal por divisão para em 2021, e o sigilo esconde a planta pequena. Onde a célula não foi publicada, o peso é zero e a soma se refaz sobre o que foi publicado. O resultado favorece município com planta grande o bastante para aparecer na tabela.

A pendularidade de 2022 é um modelo de destinos concorrentes sobre a taxa de quem trabalha fora do município de residência. Não é a matriz origem-destino contada pessoa a pessoa, e não é o arquivo de recursos humanos da planta. A conferência com a chave do Censo 2010 (91,8% na sede, contra 91,3% neste modelo) reduz o risco de a residência estar no lugar errado. Ela não transforma o modelo em contagem.

α, as frações de serviço que seguem a casa e os três raios de corte (260 km para fornecedor, 110 km para o deslocamento diário, 180 km para o consumo gravitacional) são parâmetros declarados. A sensibilidade de λ e de α está acima. O piso de R$ 50 mil é cartográfico: abaixo dele o polígono fica cinza e o real continua no CSV.

A obra de 2026–2027 é outro bloco do estudo. Este mapa é o ano de operação, 2037. O investimento da construção não está na cor.

O tributo estadual e municipal de **R$ 480 milhões** sobre o consumo do produto no Rio Grande do Sul, no bloco fiscal do cenário base, admite uma leitura territorial e só uma leitura honesta com a natureza do tributo. É tributo no destino do consumo do produto. A chave usada aqui é a **população residente do Censo 2022**. O COREDE tem **3,9%** da população do Estado, o que lê **R$ 18,7 milhões** no Conselho e **R$ 461,3 milhões** no resto. Aplicar a esses R$ 480 milhões a chave do valor adicionado de transbordamento colocaria cerca de R$ 220 milhões no COREDE e misturaria o lugar do salário com o lugar da compra do produto. Essa segunda conta não é a leitura recomendada, e nenhuma das duas é cota-parte, VAF ou ISS do estabelecimento. ISS municipal por cidade não foi calculado.

## Anexo. Fórmulas da regionalização

Sede s = Santa Cruz do Sul. d é a distância em quilômetros entre centroides na projeção de Albers equivalente sobre o elipsoide GRS80 (SIRGAS 2000), meridiano central 53°W, paralelos padrão 33°S e 28°S. Uma zona UTM não cobre o Estado. A distância da conta é a euclidiana nessa projeção.

**Folha.** T_i é a quantidade produzida de fumo em folha na PAM 2025. A compra nova é 0,0086 × T_i. O valor adicionado agrícola da cadeia reparte-se por T_i / Σ T.

**Fornecedor.** Emprego publicado E_i (célula suprimida = 0), α = 0,5, λ = 100 km, raio D = 260 km:

```
w_i = E_i^α × exp(−d_is / λ)    se E_i > 0 e d_is ≤ D;   senão w_i = 0
k_i = w_i / Σ w
```

Cada bloco industrial multiplica o seu valor adicionado por k do seu setor. A divisão 12 não entra no emprego do restante da indústria.

**Residência de quem trabalha na sede.** L_s é o contingente que o Censo 2022 conta como ocupado no próprio município, em Santa Cruz do Sul. F_j é quem, morando em j, trabalha em outro município. A_m é o emprego formal total de m. Com λ_c = 28 km e d_js ≤ 110 km:

```
p_{j→s} = [A_s × exp(−d_js / λ_c)] / Σ_{m ≠ j} [A_m × exp(−d_jm / λ_c)]
```

Além de 110 km, p = 0. O posto atribuído é L_s na sede mais Σ_j F_j p_{j→s} nos demais. π é esse vetor sobre a sua soma. Na referência, π_s = 0,913.

**Serviços.** Com fração φ na residência e núcleo setorial k, σ = φ π + (1 − φ) k. Os φ estão na nota de método (0,50 no comércio e no transporte; 0,70 no alojamento e nos serviços sociais; 0,25 em finanças e serviços profissionais; 0,60 nas atividades imobiliárias; 1 na administração pública da cadeia).

**Induzido.** s_dir = 0,765 é a remuneração direta sobre a soma das remunerações direta e da cadeia. M_i é o valor adicionado da cadeia já alocado em i, P_j a população, λ_g = 75 km, raio 180 km. O núcleo g_j é proporcional a P_j^α × Σ_i M_i exp(−d_ij / λ_g), com a exponencial zerada além do raio, e g soma 1. Então induzido_j = V_induzido × (s_dir π_j + (1 − s_dir) g_j).

**Fechamento.** Valor abaixo de R$ 1 em um município volta ao município de maior transbordamento, componente a componente. A soma de folha, indústria, serviços e induzido nos 497 municípios é R$ 869.682.841,66. O CSV guarda seis casas decimais em R$ milhões.

Reprodução: `python3 estudo/espacial/alocar_transbordamento.py`. As bases grandes ficam em `/tmp/espacial_rs`.
