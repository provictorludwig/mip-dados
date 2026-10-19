# Nota de método — regionalização do transbordamento

Conta reproduzida por `estudo/espacial/alocar_transbordamento.py`. Valores em reais de 2025, ano de operação 2037. A nota cobre as fontes, os parâmetros e o que permanece proxy. A leitura para decisão está em `analise_espacial.md`.

## Totais que a conta reparte

A fonte do total é `estudo/resultados/ipea_totais.json`, lida no momento da execução. O indireto é o da MIP Ipea 2018 (NF-e), não o da MIP-RS. A abertura de produtos continua estimada. O conteúdo local dos insumos que não são folha, pela oferta ao RS, é 44,7%.

| Grandeza | Valor |
|---|---:|
| Valor adicionado direto | R$ 7.830.000.000 |
| Remuneração direta | R$ 609.000.000 |
| Valor adicionado indireto no RS | R$ 1.772.908.816,04 |
| Remuneração indireta no RS | R$ 1.002.795.321,16 |
| Valor adicionado induzido, uma rodada, no RS | R$ 627.761.135,91 |
| Transbordamento (indireto no RS + induzido no RS) | R$ 2.400.669.951,95 |

A composição setorial do indireto no RS vem de `estudo/resultados/ipea_va_rs_atividade.csv`, agrupada nos mesmos núcleos (folha, papel, eletrônico, serviços). As fatias fecham no valor adicionado indireto do json. O direto entra na coluna `va_direto_mi` e fica de fora da escala do mapa.

## Fontes espaciais

Os arquivos grandes ficam em `/tmp/espacial_rs` e não entram no repositório.

**Malha.** Municípios do Rio Grande do Sul, IBGE 2022, 497 polígonos, obtidos pela biblioteca geobr (malha oficial IBGE). Sistema original SIRGAS 2000 (EPSG:4674). Para desenho e para distância, a malha vai a uma projeção equivalente de Albers no elipsoide GRS80, com paralelos padrão em 33°S e 28°S e meridiano central em 53°W:

```
+proj=aea +lat_0=-30.5 +lat_1=-33 +lat_2=-28 +lon_0=-53 +x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs
```

Uma zona UTM não cobre o Estado. A distância da fórmula é a euclidiana entre centroides nessa projeção, em quilômetros. É a sede municipal, não o portão da fábrica.

**Folha.** IBGE, Produção Agrícola Municipal, SIDRA tabela 1612, variável 214 (quantidade produzida, toneladas), produto fumo em folha (categoria c81, código 2703), ano 2025, nível municipal. Total do Estado: 349.928 t, em 207 municípios com produção. A fração das premissas, 0,86% em 2037, aplica-se às toneladas. O produto é 3.009,38 t, contra a âncora de 3.007 t do estudo: resíduo de +2,38 t (0,08%). O valor adicionado agrícola do indireto no RS (agricultura da MIP Ipea, R$ 58,6 milhões) usa os pesos da PAM normalizados, e por isso fecha no valor adicionado, não nas 3.007 t. O ano de 2025 é o mais recente disponível na SIDRA nesta execução; o último ano da PAM segue sujeito a revisão pelo IBGE. Os exemplos de imprensa citados nas premissas são outra safra: a conta usa a tabela.

**Emprego setorial.** IBGE, CEMPRE, SIDRA tabela 6450, variável 707 (pessoal ocupado total), classificação 12762, ano 2021. A série municipal dessa tabela encerra em 2021. Categorias usadas: divisão 02 (116866), 12 (116960), 16 (117007), 17 (117015), 19 (117039), 20 (117048), 22 (117089), 26 (117159), 27 (117179); seções B (116880), C (116910), D (117296), F (117329), G (117363), H (117484), I (117543), J (117555), K (117608), M (117673), N (117714); total (117897). Célula não numérica, o traço de sigilo, entra como zero. O núcleo se renormaliza sobre o emprego positivo dentro do raio. Papel tem célula publicada em 46 municípios; químicos, em 74; eletrônicos, em 27. O viés é para a planta grande o bastante para a tabela mostrar. A divisão 12 (produtos do fumo: Santa Cruz do Sul 3.155, Venâncio Aires 1.710, Vera Cruz 253) documenta a indústria local e **não** entra como peso da cadeia de papel, químicos ou eletrônicos.

**Pendularidade e população.** Censo Demográfico 2022, SIDRA tabela 10329: pessoas ocupadas que trabalham no município de residência (categoria 12167) e pessoas ocupadas que trabalham em outro município (categoria 12188), por município de residência. O microdado público do Censo 2022 (arquivo de pessoas) não contém município de residência nem município de trabalho; as variáveis de local de trabalho do questionário não estão no arquivo divulgado. Por isso não há matriz origem-destino contada. A população residente é a SIDRA tabela 4709, variável 93, Censo 2022, e serve ao núcleo de consumo e à leitura do tributo.

**COREDE.** Artigo 3º do estatuto do COREDE Vale do Rio Pardo e Plano Estratégico de Desenvolvimento 2022–2030 do Conselho. Vinte e três municípios, listados em `corede_vale.csv`. O contorno do mapa segue essa lista.

## Parâmetros de referência

| Parâmetro | Valor | Função |
|---|---:|---|
| α | 0,5 | Comprime o emprego (e a população) antes do decaimento |
| λ | 100 km | Fornecedor e presença de serviços até a sede |
| λ_c | 28 km | Destinos concorrentes do deslocamento casa-trabalho |
| λ_g | 75 km | Consumo induzido a partir da massa da cadeia já alocada |
| Raio do fornecedor | 260 km | Além disso o peso setorial é zero |
| Raio do deslocamento | 110 km | Além disso ninguém é atribuído à sede por pendularidade |
| Raio da gravidade | 180 km | Além disso o consumo gravitacional não alcança |
| Fração da folha | 0,86% | Só nas toneladas da PAM |
| Piso cartográfico | R$ 0,05 milhão | Abaixo disso o polígono fica cinza; o CSV guarda o valor |

Frações do serviço da cadeia que seguem a residência π, e não o emprego do setor: comércio, transporte e informação, 0,50; alojamento, alimentação e serviços sociais, 0,70; finanças, profissionais e administrativos, 0,25; atividades imobiliárias, 0,60; administração pública da cadeia, 1,00. Pecuária e a parte populacional dos serviços usam o núcleo de população, não uma divisão do CEMPRE.

O valor adicionado induzido reparte-se com s_dir = 609 / (609 + 1.002,8) = 0,378 na residência π, e o complemento no núcleo gravitacional. A remuneração indireta no RS supera a remuneração direta, e por isso a mancha induzida acompanha mais o fornecedor. Na referência, π da sede é 0,9135 (64.071 residentes ocupados no próprio município e 6.068 entrantes modelados).

## Sensibilidade curta

Mesmos α, λ_c e λ_g. Muda só o λ do fornecedor e da presença de serviços.

| λ (km) | Parcela do COREDE | Transbordamento na sede |
|---:|---:|---:|
| 80 | 29,0% | R$ 484 milhões |
| 100 | 26,8% | R$ 458 milhões |
| 150 | 24,5% | R$ 431 milhões |

Com λ = 80 km, Venâncio Aires entra entre os cinco primeiros, atrás de Porto Alegre e Eldorado do Sul. Com λ = 150 km, Gravataí sobe e Eldorado do Sul permanece entre os cinco. Com α = 1 e λ = 100 km, o COREDE cai a 23,8% e a sede fica em R$ 426 milhões. O λ de referência é 100 km. O indireto agora pesa em eletrônico, papel e máquina elétrica, e a mancha metropolitana e da Serra fica à frente do anel do Vale.

## Fechamento e cartografia

A soma de `va_transbordo_mi` nos 497 municípios é R$ 2.400,669954 milhões no CSV (seis casas). O total não arredondado é R$ 2.400.669.951,95. Dois municípios ficam em zero: Barra do Quaraí e Chuí. Sessenta e seis municípios ficam abaixo de R$ 50 mil e somam R$ 1,15 milhão; no mapa são cinza e no CSV entram na soma. A conferência da planilha, em reais, é zero.

Classes do mapa, em R$ milhões: cinza abaixo de 0,05; depois 0,5; 2; 6; 15; 30; e a classe aberta até o máximo (R$ 340 milhões na sede). As classes são do Estado. O zoom do Vale não as recalcula. Cores: `#d0d0d0` e, na rampa, `#deebf7`, `#c6dbef`, `#9ecae1`, `#6baed6`, `#2171b5`, `#08306b`. Contorno do COREDE em ocre `#8a5a12`. Sede com contorno em azul-marinho `#0b2545`. Fundo branco. Tipografia Liberation Sans. A peça `mapa_com_direto.png` usa outras quebras, de propósito, para isolar o direto; a legenda avisa que ela não é o mapa de transbordamento.

## O que continua proxy

- Emprego setorial de 2021, com sigilo nas células pequenas, no lugar de uma RAIS identificada que não está disponível nesta execução.
- Pendularidade modelada sobre a taxa de quem trabalha fora do município de residência, no lugar de uma matriz origem-destino do Censo 2022. A chave do Censo 2010 registrada no arquivo de resultados (91,8% de residência na sede) é conferência, não insumo.
- Distância entre centroides, no lugar da malha rodoviária e da coordenada da planta.
- α, as frações φ e os três raios, declarados e testados em λ e em α, não estimados.
- Leitura do tributo de R$ 480 milhões pela população do Censo 2022 (3,9% no COREDE, R$ 18,7 milhões). Não é VAF, não é cota-parte e não é ISS municipal.
