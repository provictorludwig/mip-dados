#!/usr/bin/env python3
"""Impacto da operação de nicotina sem fumaça em Santa Cruz do Sul (2037).

Calcula a cadeia com a inversa de Leontief da MIP-RS 2019 (DEE/SPGG e UFRJ),
nível 117 produtos × 52 atividades. A planilha oficial fica em /tmp e não entra
no repositório. Os resultados em R$ de 2025 saem em estudo/resultados/.

Três gavetas, nesta ordem:
  1. Efeito direto da planta (VAB, ocupações e remunerações do arquivo de premissas).
  2. Cadeia: só a compra feita no RS, a preço básico, choque nos produtos fornecedores.
  3. Vazamento para fora do RS, registrado e não multiplicado.

A receita ex-fábrica não é o choque. A atividade "fabricação de produtos do fumo"
não recebe a receita. O cenário base usa a abertura estimada do BOM. A obra
entra em bloco separado (2026–2027) e não se soma ao fluxo de 2037.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import openpyxl
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
RESULTADOS = ROOT / "resultados"
FIGURAS = ROOT / "figuras"
TMP = Path("/tmp/mip_rs")
MIP_PATH = TMP / "mip_117_52.xlsx"
TRU_PATH = TMP / "tru_rs_2019.xlsx"
MIP_URL = (
    "https://dee.rs.gov.br/upload/arquivos/202409/"
    "11100149-20240906162755mip-rs-2019-117-52-v2-1.xlsx"
)
TRU_URL = (
    "https://dee.rs.gov.br/upload/arquivos/202409/"
    "11095935-20240906160547tru-rs-2019-v3-1.xlsx"
)

# IBGE SIDRA tabela 1737, variável 2266 (número-índice, dez/1993 = 100).
# Conferido em 19/10/2026: dezembro de 2019 e dezembro de 2025.
IPCA_DEZ_2019 = 5320.25
IPCA_DEZ_2025 = 7403.29
PHI = IPCA_DEZ_2019 / IPCA_DEZ_2025  # multiplica fluxo de 2025 para entrar na matriz

# Premissas da revisão 4 (18/10/2026), ano cheio 2037, R$ de 2025.
VBP_INT = 12.56e9
VBP_EXP = 3.27e9
VBP = VBP_INT + VBP_EXP  # 15,83 bi
BOM_INT = 5.81e9
BOM_EXP = 2.19e9
BOM = BOM_INT + BOM_EXP  # 8,00 bi
VA_DIRETO = 7.83e9  # 15,83 − 8,00
LEAF_TOTAL = 114.2e6
LEAF_RS = 52.8e6
LEAF_TON_TOTAL = 6510.0
LEAF_TON_RS = 3007.0
OCC_DIRETO = 4060.0
OCC_EXP = 1000.0
OCC_INT = OCC_DIRETO - OCC_EXP  # 3.060
REM_POR_OCUP = 150_000.0
REM_DIRETO = OCC_DIRETO * REM_POR_OCUP  # R$ 609 milhões
TAXA_CONTEUDO_LOCAL = (0.10, 0.20, 0.35)
TAXA_BASE = 0.20
PROPENSAO_CONSUMO_RS = 0.60

# Reconstrução das fichas v6 para separar interno e exportação.
# Volumes em unidades físicas; BOM em R$ por unidade; folha em t e R$/t.
ELIQ_INT_ML = 2.118e9
ELIQ_EXP_ML = 0.956e9
STICK_INT = 11.42e9
STICK_EXP = 0.918e9
SACH_EXP = 0.138e9
BOM_ELIQ = 2.14375
BOM_STICK = 0.110925
BOM_SACH = 0.268225
LEAF_G_ELIQ = 0.90
LEAF_G_STICK = 0.30
LEAF_G_SACH = 0.27
PRECO_LEAF_NIC = 15_000.0
PRECO_LEAF_REC = 19_500.0

# Bloco II do contratante (Tipo I deles, 2037, RS). Comparação, não insumo.
BLOCO_II = {
    "vab_rs_bi": 8.85,
    "ocupacoes_rs": 12760.0,
    "tributos_consumo_rs_bi": 0.928,
    "vab_brasil_bi": 15.55,
    "ocupacoes_brasil": 67350.0,
}

# Exemplos já escritos nas premissas (ranking de imprensa, a conferir no SIDRA).
# Não são estimativa de área de influência.
EXEMPLOS_FOLHA = [
    {"municipio": "Canguçu", "uf": "RS", "pam_t": 21064, "folha_nova_t": 181, "lat": -31.395, "lon": -52.676},
    {"municipio": "Venâncio Aires", "uf": "RS", "pam_t": 17779, "folha_nova_t": 153, "lat": -29.606, "lon": -52.192},
    {"municipio": "São Lourenço do Sul", "uf": "RS", "pam_t": 16374, "folha_nova_t": 141, "lat": -31.365, "lon": -51.978},
    {"municipio": "Santa Cruz do Sul", "uf": "RS", "pam_t": 12610, "folha_nova_t": 108, "lat": -29.718, "lon": -52.426, "sede": True},
    {"municipio": "Candelária", "uf": "RS", "pam_t": 11462, "folha_nova_t": 98, "lat": -29.669, "lon": -52.789},
]

# 52 atividades da MIP → 16 grupos da TRU (mesma família DEE/UFRJ 2019).
# A conferência com o valor da produção da TRU valida o mapa.
GRUPOS_16 = [
    ("Agropecuária", ["AT01", "AT02", "AT03"]),
    ("Indústria extrativa", ["AT04", "AT05"]),
    ("Indústrias de transformação", [f"AT{i:02d}" for i in range(6, 33)]),
    ("Eletricidade, gás, água e resíduos", ["AT33", "AT34"]),
    ("Construção", ["AT35"]),
    ("Comércio", ["AT36"]),
    ("Transporte, armazenagem e correio", ["AT37", "AT38", "AT39", "AT40"]),
    ("Alojamento e alimentação", ["AT41", "AT42"]),
    ("Informação e comunicação", ["AT43", "AT44"]),
    ("Atividades financeiras e de seguros", ["AT45"]),
    ("Atividades imobiliárias", ["AT46"]),
    ("Atividades profissionais e administrativas", ["AT47", "AT48"]),
    ("Administração pública", ["AT49"]),
    ("Educação e saúde mercantis", ["AT50"]),
    ("Artes, cultura e outros serviços", ["AT51"]),
    ("Serviços domésticos", ["AT52"]),
]


def baixar(url: str, destino: Path) -> None:
    if destino.exists() and destino.stat().st_size > 10_000:
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        destino.write_bytes(resp.read())


def norm(valor) -> str:
    if valor is None:
        return ""
    texto = str(valor).replace("-\n", "").replace("-\r", "")
    return " ".join(texto.replace("\n", " ").replace("\r", " ").split())


def ler_bloco(ws, n_linhas: int, n_cols: int, linha0: int = 5, col0: int = 2):
    """Lê rótulos da coluna A/B e um bloco numérico."""
    codigos = []
    nomes = []
    dados = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i < linha0:
            continue
        if len(codigos) >= n_linhas:
            break
        codigo = norm(row[0]) if row else ""
        if not codigo:
            continue
        codigos.append(codigo)
        nomes.append(norm(row[1]) if len(row) > 1 else "")
        linha = []
        for j in range(n_cols):
            v = row[col0 + j] if len(row) > col0 + j else 0
            linha.append(0.0 if v is None else float(v))
        dados.append(linha)
    return codigos, nomes, np.array(dados, dtype=float)


def cabecalhos_colunas(ws, n_cols: int, linha_cod: int = 3, linha_nome: int = 4, col0: int = 2):
    linhas = list(ws.iter_rows(max_row=linha_nome + 1, values_only=True))
    cod = linhas[linha_cod]
    nome = linhas[linha_nome]
    codigos, nomes = [], []
    for j in range(n_cols):
        codigos.append(norm(cod[col0 + j]) if len(cod) > col0 + j else "")
        nomes.append(norm(nome[col0 + j]) if len(nome) > col0 + j else "")
    return codigos, nomes


def carregar_mip():
    baixar(MIP_URL, MIP_PATH)
    baixar(TRU_URL, TRU_PATH)
    wb = openpyxl.load_workbook(MIP_PATH, read_only=True, data_only=True)

    prod_cod, prod_nom, B = ler_bloco(wb["9"], 117, 52)
    # Tabela 12 é atividades × produtos.
    ati_cod, ati_nom, D = ler_bloco(wb["12"], 52, 117)
    ati_a, _, A = ler_bloco(wb["13"], 52, 52)
    ati_l, _, L_pub = ler_bloco(wb["14"], 52, 52)
    if ati_cod != ati_a or ati_a != ati_l:
        raise SystemExit("Ordem das atividades diverge entre as tabelas 12, 13 e 14.")

    # Demanda da produção gaúcha a preço básico (tabela 3) e usos a preço de consumidor (tabela 2).
    dem_cod, dem_nom, dem = ler_bloco(wb["3"], 117, 62)
    uso_cod, _, uso = ler_bloco(wb["2"], 117, 52)
    col_dem, nome_dem = cabecalhos_colunas(wb["3"], 62)
    wb.close()

    if dem_cod != prod_cod or uso_cod != prod_cod:
        raise SystemExit("Ordem dos produtos diverge entre as tabelas 2, 3 e 9.")

    I = np.eye(52)
    L = np.linalg.inv(I - A)
    erro_L = np.max(np.abs(L - L_pub))
    erro_ident = np.max(np.abs((I - A) @ L - I))
    A_db = D @ B
    erro_A = np.max(np.abs(A_db - A))
    soma_D = D.sum(axis=0)

    # Colunas da tabela 3, depois das 52 atividades: totais e demanda final.
    idx = {norm(c).lower(): i for i, c in enumerate(col_dem)}
    # Os cabeçalhos de exportação e de consumo vêm na linha de nomes quando o código está vazio.
    # Mapeia pelo nome normalizado da linha 4 quando o código não identifica.
    nomes_l = [norm(n).lower() for n in nome_dem]

    def achar(*chaves):
        for i, (c, n) in enumerate(zip(col_dem, nomes_l)):
            texto = f"{c} {n}".lower()
            if all(k in texto for k in chaves):
                return i
        raise SystemExit(f"Coluna não encontrada: {chaves}")

    c_ci = achar("total")  # primeiro "Total" é o total do consumo intermediário
    # O segundo total é o das exportações. Procura de forma explícita.
    totais = [i for i, c in enumerate(col_dem) if norm(c).lower() == "total"]
    if len(totais) < 1:
        raise SystemExit(f"Totais não identificados: {col_dem}")
    c_ci = totais[0]
    c_fam = achar("fam")
    c_gov = achar("admin")
    c_isfl = achar("isfl")
    c_fbcf = achar("capital")
    c_est = achar("estoque")
    c_df = None
    for i, c in enumerate(col_dem):
        if "demanda" in norm(c).lower() and "final" in norm(c).lower():
            c_df = i
    if c_df is None:
        # linha de código pode estar quebrada: "Demanda final"
        for i, n in enumerate(nomes_l):
            if "demanda" in n and "final" in n:
                c_df = i
                break
    c_xw = achar("resto do mundo")
    c_xuf = achar("demais unidades")

    ci_prod = dem[:, c_ci]
    if c_df is not None:
        q = ci_prod + dem[:, c_df]
    else:
        q = (
            dem[:, :52].sum(axis=1)
            + dem[:, c_xw]
            + dem[:, c_xuf]
            + dem[:, c_gov]
            + dem[:, c_isfl]
            + dem[:, c_fam]
            + dem[:, c_fbcf]
            + dem[:, c_est]
        )
    q_alt = (
        dem[:, :52].sum(axis=1)
        + dem[:, c_xw]
        + dem[:, c_xuf]
        + dem[:, c_gov]
        + dem[:, c_isfl]
        + dem[:, c_fam]
        + dem[:, c_fbcf]
        + dem[:, c_est]
    )

    x_ativ = D @ q
    ci_ativ = uso.sum(axis=0)  # preço de consumidor, R$ milhões de 2019
    va_ativ = x_ativ - ci_ativ
    with np.errstate(divide="ignore", invalid="ignore"):
        coef_va = np.where(x_ativ > 1.0, va_ativ / x_ativ, 0.0)

    consumo = dem[:, c_fam].astype(float)
    consumo_pos = np.clip(consumo, 0.0, None)
    massa_neg = float((-np.clip(consumo, None, 0)).sum())
    if consumo_pos.sum() <= 0:
        raise SystemExit("Vetor de consumo das famílias está vazio.")
    share_consumo = consumo_pos / consumo_pos.sum()

    tru = carregar_tru()
    mapa_grupo = {}
    for nome_g, membros in GRUPOS_16:
        for m in membros:
            mapa_grupo[m] = nome_g
    if set(mapa_grupo) != set(ati_cod):
        raise SystemExit("Mapa de 16 grupos não cobre as 52 atividades.")

    prod_grupo = {g[0]: 0.0 for g in GRUPOS_16}
    for codigo, x in zip(ati_cod, x_ativ):
        prod_grupo[mapa_grupo[codigo]] += float(x)

    coef_rem = {}
    coef_occ = {}  # ocupações por R$ milhão de produção de 2019
    coef_va_tru = {}
    # A ordem de GRUPOS_16 segue a ordem das 16 colunas da TRU.
    for i, (nome_g, _) in enumerate(GRUPOS_16):
        prod = float(tru["producao"][i])
        coef_rem[nome_g] = float(tru["remuneracoes"][i] / prod)
        coef_occ[nome_g] = float(tru["ocupacoes"][i] / prod)
        coef_va_tru[nome_g] = float(tru["va"][i] / prod)

    w_ativ = np.array([coef_rem[mapa_grupo[c]] for c in ati_cod])
    e_ativ = np.array([coef_occ[mapa_grupo[c]] for c in ati_cod])

    return {
        "prod_cod": prod_cod,
        "prod_nom": prod_nom,
        "ati_cod": ati_cod,
        "ati_nom": ati_nom,
        "A": A,
        "B": B,
        "D": D,
        "L": L,
        "q": q,
        "q_alt": q_alt,
        "x_ativ": x_ativ,
        "va_ativ": va_ativ,
        "coef_va": coef_va,
        "ci_ativ": ci_ativ,
        "share_consumo": share_consumo,
        "consumo_pos_mi": float(consumo_pos.sum()),
        "consumo_neg_mi": massa_neg,
        "w_ativ": w_ativ,
        "e_ativ": e_ativ,
        "mapa_grupo": mapa_grupo,
        "prod_grupo": prod_grupo,
        "tru": tru,
        "coef_rem": coef_rem,
        "coef_occ": coef_occ,
        "coef_va_tru": coef_va_tru,
        "soma_D_min": float(soma_D.min()),
        "soma_D_max": float(soma_D.max()),
        "erro_L": float(erro_L),
        "erro_ident": float(erro_ident),
        "erro_A": float(erro_A),
        "col_dem": col_dem,
        "nome_dem": nome_dem,
        "idx_consumo": {
            "ci": int(c_ci),
            "familia": int(c_fam),
            "demanda_final": None if c_df is None else int(c_df),
        },
    }


def carregar_tru():
    wb = openpyxl.load_workbook(TRU_PATH, read_only=True, data_only=True)
    ws = wb["VA_16"]
    linhas = list(ws.iter_rows(values_only=True))
    wb.close()
    cab = [norm(c) for c in linhas[3][1:17]]
    def linha(rotulo_ini):
        for row in linhas:
            if norm(row[0]).lower().startswith(rotulo_ini):
                return [float(row[j]) for j in range(1, 17)]
        raise SystemExit(f"Linha TRU não encontrada: {rotulo_ini}")

    return {
        "grupos": cab,
        "va": linha("valor adicionado"),
        "remuneracoes": linha("remunera"),
        "producao": linha("valor da produ"),
        "ocupacoes": linha("fator trabalho"),
    }


def toneladas_folha(ml_eliq, n_stick, n_sach) -> float:
    return (
        ml_eliq * LEAF_G_ELIQ / 1e6
        + n_stick * LEAF_G_STICK / 1e6
        + n_sach * LEAF_G_SACH / 1e6
    )


def valor_folha(ml_eliq, n_stick, n_sach) -> float:
    t_eliq = ml_eliq * LEAF_G_ELIQ / 1e6
    t_stick = n_stick * LEAF_G_STICK / 1e6
    t_sach = n_sach * LEAF_G_SACH / 1e6
    return t_eliq * PRECO_LEAF_NIC + t_stick * PRECO_LEAF_REC + t_sach * PRECO_LEAF_NIC


def _folha_partes():
    folha_int = valor_folha(ELIQ_INT_ML, STICK_INT, 0.0)
    folha_exp = valor_folha(ELIQ_EXP_ML, STICK_EXP, SACH_EXP)
    share_int = folha_int / (folha_int + folha_exp)
    ton_int = toneladas_folha(ELIQ_INT_ML, STICK_INT, 0.0)
    ton_exp = toneladas_folha(ELIQ_EXP_ML, STICK_EXP, SACH_EXP)
    share_ton_int = ton_int / (ton_int + ton_exp)
    return share_int, share_ton_int


def abertura_bom(com_exportacao: bool) -> dict:
    """Abertura estimada do BOM de 2037, em R$ de 2025.

    A âncora é a do arquivo: insumos R$ 8,00 bi, dos quais folha R$ 114,2 mi.
    As linhas físicas (gramas, kWh, preços) são estimativa com fonte na ficha
    de cada linha. Um fator único, da ordem de 1,0006, ajusta a soma das linhas
    de insumo que não são folha à âncora. Não é uma casa decimal inventada:
    é a diferença entre volume × custo unitário e o agregado arredondado.
    """
    share_int, share_ton_int = _folha_partes()
    familias = {
        "eliq": {
            "vol": (ELIQ_INT_ML + ELIQ_EXP_ML) if com_exportacao else ELIQ_INT_ML,
            "vol_cheio": ELIQ_INT_ML + ELIQ_EXP_ML,
            "bom_u": BOM_ELIQ,
            "folha_g": LEAF_G_ELIQ,
            "preco_folha": PRECO_LEAF_NIC,
        },
        "stick": {
            "vol": (STICK_INT + STICK_EXP) if com_exportacao else STICK_INT,
            "vol_cheio": STICK_INT + STICK_EXP,
            "bom_u": BOM_STICK,
            "folha_g": LEAF_G_STICK,
            "preco_folha": PRECO_LEAF_REC,
        },
        "sach": {
            "vol": SACH_EXP if com_exportacao else 0.0,
            "vol_cheio": SACH_EXP,
            "bom_u": BOM_SACH,
            "folha_g": LEAF_G_SACH,
            "preco_folha": PRECO_LEAF_NIC,
        },
    }
    # Não folha de ano cheio, antes do corte de exportação, para o fator de âncora.
    nf_cheio = 0.0
    for f in familias.values():
        bom = f["vol_cheio"] * f["bom_u"]
        folha = f["vol_cheio"] * f["folha_g"] / 1e6 * f["preco_folha"]
        nf_cheio += bom - folha
    nf_ancora = BOM - LEAF_TOTAL
    fator = nf_ancora / nf_cheio

    ml = familias["eliq"]["vol"]
    st = familias["stick"]["vol"]
    sa = familias["sach"]["vol"]
    # Participação do ano cheio que permanece neste cenário (1 no ano cheio).
    w = {k: (familias[k]["vol"] / familias[k]["vol_cheio"] if familias[k]["vol_cheio"] else 0.0) for k in familias}

    def linha(nome, valor_cheio, rs, uf, imp, produto, familia, regra):
        valor = valor_cheio * w[familia] * fator
        return {
            "linha": nome,
            "familia": familia,
            "produto": produto,
            "valor": valor,
            "rs": rs,
            "outros_estados": uf,
            "importado": imp,
            "valor_rs": valor * rs,
            "valor_uf": valor * uf,
            "valor_imp": valor * imp,
            "regra": regra,
        }

    # Preços e intensidades: ver ficha no relatório. Valores de ano cheio, em R$.
    vg = (ELIQ_INT_ML + ELIQ_EXP_ML) * 0.5075 / 1000 * 12.0
    pg = (ELIQ_INT_ML + ELIQ_EXP_ML) * 0.5075 / 1000 * 14.0
    aroma_e = (ELIQ_INT_ML + ELIQ_EXP_ML) * 0.115 / 1000 * 170.0
    nic = (ELIQ_INT_ML + ELIQ_EXP_ML) * 0.020 / 1000 * 440.0
    pods = (ELIQ_INT_ML + ELIQ_EXP_ML) / 11.36
    emb_e = pods * 0.20
    gli = (STICK_INT + STICK_EXP) * 5e-5 * 12.0
    lig = (STICK_INT + STICK_EXP) * 1e-5 * 20.0
    aroma_s = (STICK_INT + STICK_EXP) * 0.003
    # Energia: 7,56 GJ por milhão de cigarros-equivalentes (PMI, 2022),
    # ponto médio do intervalo 1–3× nos sticks e sachês e 1–5× no e-líquido.
    # Tarifa industrial: ponto médio R$ 550/MWh de um intervalo R$ 400–700.
    def energia(unidades, mult):
        mwh = unidades / 1e6 * 7.56 * mult / 3.6
        return mwh * 550.0, mwh

    en_e, mwh_e = energia(ELIQ_INT_ML + ELIQ_EXP_ML, 3.0)
    en_s, mwh_s = energia(STICK_INT + STICK_EXP, 2.0)
    en_a, mwh_a = energia(SACH_EXP, 2.0)

    def agua(unidades, mult):
        m3 = unidades / 1e6 * 3.79 * mult
        return m3 * 15.0, m3

    ag_e, m3_e = agua(ELIQ_INT_ML + ELIQ_EXP_ML, 3.0)
    ag_s, m3_s = agua(STICK_INT + STICK_EXP, 2.0)
    ag_a, m3_a = agua(SACH_EXP, 2.0)

    # Não folha de ano cheio por família, já na âncora, para a manutenção em %.
    def nf_familia(cod_vol, bom_u, folha_g, preco):
        return (cod_vol * bom_u - cod_vol * folha_g / 1e6 * preco) * fator

    nf_e = nf_familia(ELIQ_INT_ML + ELIQ_EXP_ML, BOM_ELIQ, LEAF_G_ELIQ, PRECO_LEAF_NIC)
    nf_s = nf_familia(STICK_INT + STICK_EXP, BOM_STICK, LEAF_G_STICK, PRECO_LEAF_REC)
    nf_a = nf_familia(SACH_EXP, BOM_SACH, LEAF_G_SACH, PRECO_LEAF_NIC)
    mt_e, mt_s, mt_a = 0.006 * nf_e, 0.06 * nf_s, 0.06 * nf_a
    fr_e, fr_s, fr_a = 25e6, 25e6, 1.5e6

    fixos_e = (vg + pg + aroma_e + nic + emb_e + en_e + ag_e + mt_e + fr_e) * fator
    # O fator já está nas linhas via `linha`. Os fixos acima estão em ano cheio
    # SEM o fator; `linha` aplica fator e peso. O dispositivo é o residual da
    # âncora de não folha do e-líquido.
    dev = nf_e / fator - (vg + pg + aroma_e + nic + emb_e + en_e + ag_e + mt_e / fator + fr_e)
    # Manutenção foi definida já com o fator (0,6% do não folha ancorado).
    # Energia, água, químicos e frete são físicos, sem o fator. Para o residual
    # fechar a âncora, a manutenção entra sem duplo fator.
    dev = nf_e - (vg + pg + aroma_e + nic + emb_e + en_e + ag_e + fr_e) * fator - mt_e
    paper = nf_s - (gli + lig + aroma_s + en_s + ag_s + fr_s) * fator - mt_s
    resto_a = nf_a - (en_a + ag_a + fr_a) * fator - mt_a
    chem_a = 0.55 * resto_a
    emb_a = 0.45 * resto_a

    # `linha` multiplica de novo por fator e pelo peso. As grandezas `dev` e
    # `paper` já estão ancoradas. Por isso entram com familia e com um caminho
    # que não reaplicaria o fator. Abaixo as linhas são gravadas já no cenário.
    def L(nome, valor_ancorado_cheio, rs, uf, imp, produto, familia, regra):
        valor = valor_ancorado_cheio * w[familia]
        return {
            "linha": nome,
            "familia": familia,
            "produto": produto,
            "valor": valor,
            "rs": rs,
            "outros_estados": uf,
            "importado": imp,
            "valor_rs": valor * rs,
            "valor_uf": valor * uf,
            "valor_imp": valor * imp,
            "regra": regra,
        }

    # Recalcula device/paper/chem no espaço ancorado de ano cheio (fator uma vez).
    dev = nf_e - fator * (vg + pg + aroma_e + nic + emb_e + en_e + ag_e + fr_e) - mt_e
    paper = nf_s - fator * (gli + lig + aroma_s + en_s + ag_s + fr_s) - mt_s
    resto_a = nf_a - fator * (en_a + ag_a + fr_a) - mt_a
    chem_a = 0.55 * resto_a
    emb_a = resto_a - chem_a

    r_disp = "5% RS. Teto MIP PR066 no consumo intermediário: 8,2% local. Pod específico, desconto de especificidade; 85% importado."
    r_vg = "35% RS. Piso abaixo da média MIP de químicos orgânicos (PR047, 65% local): glicerina de biodiesel tem oferta gaúcha, sem ser a média do produto."
    r_pg = "10% RS. Químico orgânico mais específico que a média do PR047; oferta petroquímica concentrada em outros estados."
    r_ar = "15% RS. Abaixo do PR051 (químicos diversos, 40,3% local): aroma composto é especialidade, com peso de importação."
    r_nic = "30% RS. Insumo de extração (solvente e processo), entre o PR047 e o PR051. A folha em si não está nesta linha."
    r_emb_e = "40% RS. Perto da média MIP do papel e da embalagem (PR036, 39,7% local): caixa e rótulo podem ser impressos no estado."
    r_quim_s = "25% RS. Entre a média do PR051 (40%) e um desconto de especialidade do stick (aroma e ligante)."
    r_pap = "25% RS. Abaixo do PR036 (39,7%): papel de cigarro e filtro de acetato são mais específicos que a média de papel e embalagem; parte do acetato é importada."
    r_quim_a = "15% RS. Sachê de exportação, insumo mais específico e mais importado que a média do PR051."
    r_emb_a = "30% RS. Entre o PR036 (39,7%) e um desconto de especificidade da lata e do papel do sachê."
    r_en = "100% RS. Energia faturada no estado entra local; o vazamento da geração já está na matriz. MIP PR080: 66% da oferta média é gaúcha — não se usa esse percentual para descontar a fatura."
    r_ag = "100% RS. Água, esgoto e resíduo (PR081) são locais na MIP (99,9%)."
    r_fr = "100% RS. Frete interno até a planta. MIP do transporte de carga (PR086): 99,2% local."
    r_mt = "20% RS. MIP da manutenção (PR079): 30,2% local e 5% importado. Peça de máquina da PMI é mais importada que a média; desconto para 20% RS e 50% importado."

    linhas = [
        L("Dispositivo e eletrônico do pod", dev, 0.05, 0.10, 0.85, "PR066", "eliq", r_disp),
        L("Glicerina vegetal do e-líquido", fator * vg, 0.35, 0.50, 0.15, "PR047", "eliq", r_vg),
        L("Propilenoglicol do e-líquido", fator * pg, 0.10, 0.70, 0.20, "PR047", "eliq", r_pg),
        L("Aroma do e-líquido", fator * aroma_e, 0.15, 0.45, 0.40, "PR051", "eliq", r_ar),
        L("Extração de nicotina além da folha", fator * nic, 0.30, 0.50, 0.20, "PR051", "eliq", r_nic),
        L("Embalagem do pod", fator * emb_e, 0.40, 0.45, 0.15, "PR036", "eliq", r_emb_e),
        L("Químicos do stick", fator * (gli + lig + aroma_s), 0.25, 0.45, 0.30, "PR051", "stick", r_quim_s),
        L("Papel, filtro e embalagem do stick", paper, 0.25, 0.45, 0.30, "PR036", "stick", r_pap),
        L("Químicos do sachê", chem_a, 0.15, 0.40, 0.45, "PR051", "sach", r_quim_a),
        L("Papel e embalagem do sachê", emb_a, 0.30, 0.40, 0.30, "PR036", "sach", r_emb_a),
        L("Energia elétrica e combustível", fator * en_e, 1.0, 0.0, 0.0, "PR080", "eliq", r_en),
        L("Energia elétrica e combustível", fator * en_s, 1.0, 0.0, 0.0, "PR080", "stick", r_en),
        L("Energia elétrica e combustível", fator * en_a, 1.0, 0.0, 0.0, "PR080", "sach", r_en),
        L("Água", fator * ag_e, 1.0, 0.0, 0.0, "PR081", "eliq", r_ag),
        L("Água", fator * ag_s, 1.0, 0.0, 0.0, "PR081", "stick", r_ag),
        L("Água", fator * ag_a, 1.0, 0.0, 0.0, "PR081", "sach", r_ag),
        L("Frete interno", fr_e, 1.0, 0.0, 0.0, "PR086", "eliq", r_fr),
        L("Frete interno", fr_s, 1.0, 0.0, 0.0, "PR086", "stick", r_fr),
        L("Frete interno", fr_a, 1.0, 0.0, 0.0, "PR086", "sach", r_fr),
        L("Manutenção", mt_e, 0.20, 0.30, 0.50, "PR079", "eliq", r_mt),
        L("Manutenção", mt_s, 0.20, 0.30, 0.50, "PR079", "stick", r_mt),
        L("Manutenção", mt_a, 0.20, 0.30, 0.50, "PR079", "sach", r_mt),
    ]
    # Frete e manutenção de ano cheio não levam o fator de âncora no valor físico;
    # o residual do dispositivo e do papel absorve o fator. Conferência abaixo.
    if com_exportacao:
        folha_total = LEAF_TOTAL
        folha_rs = LEAF_RS
        toneladas_rs = LEAF_TON_RS
        bom = BOM
    else:
        folha_total = LEAF_TOTAL * share_int
        folha_rs = LEAF_RS * share_int
        toneladas_rs = LEAF_TON_RS * share_ton_int
        bom = BOM_INT
        alvo_nf = bom - folha_total
        soma_nf = sum(x["valor"] for x in linhas)
        if soma_nf > 0:
            aj = alvo_nf / soma_nf
            for x in linhas:
                x["valor"] *= aj
                x["valor_rs"] *= aj
                x["valor_uf"] *= aj
                x["valor_imp"] *= aj

    por_produto = {}
    for x in linhas:
        por_produto[x["produto"]] = por_produto.get(x["produto"], 0.0) + x["valor_rs"]
    por_produto["PR004"] = por_produto.get("PR004", 0.0) + folha_rs
    nao_folha = sum(x["valor"] for x in linhas)
    rs_nao = sum(x["valor_rs"] for x in linhas)
    return {
        "com_exportacao": com_exportacao,
        "fator_ancora_nao_folha": fator,
        "bom": bom,
        "folha_total": folha_total,
        "folha_rs": folha_rs,
        "folha_outras_uf": folha_total - folha_rs,
        "toneladas_rs": toneladas_rs,
        "nao_folha": nao_folha,
        "alpha": (rs_nao / nao_folha) if nao_folha else 0.0,
        "rs_nao_folha": rs_nao,
        "rs_total": rs_nao + folha_rs,
        "compras_rs": rs_nao + folha_rs,
        "vazamento": bom - (rs_nao + folha_rs),
        "importado_nao_folha": sum(x["valor_imp"] for x in linhas),
        "outros_estados_nao_folha": sum(x["valor_uf"] for x in linhas),
        "linhas": linhas,
        "por_produto": por_produto,
        "mwh": {"eliq": mwh_e * w["eliq"], "stick": mwh_s * w["stick"], "sach": mwh_a * w["sach"]},
        "m3": {"eliq": m3_e * w["eliq"], "stick": m3_s * w["stick"], "sach": m3_a * w["sach"]},
        "pods": pods * w["eliq"],
        "share_folha_interna": share_int,
        "ajuste": "abertura estimada; conteúdo local implícito, não percentual único",
    }


def capex_conversao() -> dict:
    """CAPEX de conversão calibrado por anúncio, não o número de uma planta alheia.

    Sticks: Papastratos (Grécia, 2017), €300 mi para converter fábrica existente
    e chegar a cerca de 20 bi de sticks. Escala pelo volume de 2037 e desconto
    de 15% porque o galpão e o terreno em Santa Cruz já existem.
    E-líquido: ponto médio de US$ 50–150 mi para linhas de envase e montagem
    de 271 mi de pods. Sachê: ponto médio de US$ 8–25 mi.
    Câmbio: média da PTAX venda de 2025 (BCB), USD 5,5855 e EUR 6,3085.
    """
    usd, eur = 5.585524, 6.308451
    stick = 300e6 * ((STICK_INT + STICK_EXP) / 20e9) * 0.85 * eur
    eliq = 100e6 * usd
    sach = 15e6 * usd
    total = stick + eliq + sach
    # Composição da conversão com terreno e galpão já existentes.
    partes = {
        "maquinas_importadas": 0.62,
        "obras_civis_utilidades_rs": 0.18,
        "montagem_rs": 0.084,
        "montagem_importada": 0.036,
        "engenharia_rs": 0.032,
        "engenharia_importada": 0.048,
    }
    valores = {k: total * p for k, p in partes.items()}
    rs = valores["obras_civis_utilidades_rs"] + valores["montagem_rs"] + valores["engenharia_rs"]
    imp = total - rs
    por_produto = {
        "PR082": valores["obras_civis_utilidades_rs"],
        "PR079": valores["montagem_rs"],
        "PR102": valores["engenharia_rs"],
    }
    giro = BOM * 45.0 / 365.0
    return {
        "total": total,
        "sticks": stick,
        "eliq": eliq,
        "sach": sach,
        "usd": usd,
        "eur": eur,
        "partes": valores,
        "rs": rs,
        "importado": imp,
        "por_produto_rs": por_produto,
        "capital_giro": giro,
        "piso_observado": 100e6,
        "iss_base_servicos": 0.50 * rs,
        "iss_aliquota": 0.02,
        "iss": 0.02 * 0.50 * rs,
        "terreno": 0.0,
    }


def montar_compras(alpha: float, com_exportacao: bool) -> dict:
    """Faixa uniforme 10/20/35. A folha é dada. O resto segue a hipótese alpha."""
    folha_int = valor_folha(ELIQ_INT_ML, STICK_INT, 0.0)
    folha_exp = valor_folha(ELIQ_EXP_ML, STICK_EXP, SACH_EXP)
    share_int = folha_int / (folha_int + folha_exp)
    ton_int = toneladas_folha(ELIQ_INT_ML, STICK_INT, 0.0)
    ton_exp = toneladas_folha(ELIQ_EXP_ML, STICK_EXP, SACH_EXP)
    share_ton_int = ton_int / (ton_int + ton_exp)

    if com_exportacao:
        bom = BOM
        folha_total = LEAF_TOTAL
        folha_rs = LEAF_RS
        eliq_bom = (ELIQ_INT_ML + ELIQ_EXP_ML) * BOM_ELIQ
        toneladas_rs = LEAF_TON_RS
    else:
        bom = BOM_INT
        folha_total = LEAF_TOTAL * share_int
        folha_rs = LEAF_RS * share_int
        eliq_bom = ELIQ_INT_ML * BOM_ELIQ
        toneladas_rs = LEAF_TON_RS * share_ton_int

    nao_folha = bom - folha_total
    dispositivo_nacional = 0.50 * eliq_bom
    rs_dispositivo = 0.10 * dispositivo_nacional
    alvo = alpha * nao_folha
    if rs_dispositivo > alvo:
        rs_dispositivo = alvo
        rs_quim = 0.0
        rs_papel = 0.0
        ajuste = "dispositivo limitado pelo teto de conteúdo local"
    else:
        resto = alvo - rs_dispositivo
        # 30 e 40 são pesos relativos da hipótese de composição, não alíquotas de nota.
        rs_quim = resto * 30.0 / 70.0
        rs_papel = resto * 40.0 / 70.0
        ajuste = "residual do bolo repartido 30/70 químicos e 40/70 papel"

    compras = {
        "PR004": folha_rs,
        "PR066": rs_dispositivo,
        "PR051": rs_quim,
        "PR036": rs_papel,
    }
    return {
        "com_exportacao": com_exportacao,
        "alpha": alpha,
        "bom": bom,
        "folha_total": folha_total,
        "folha_rs": folha_rs,
        "toneladas_rs": toneladas_rs,
        "nao_folha": nao_folha,
        "alvo_rs_nao_folha": alvo,
        "dispositivo_nacional": dispositivo_nacional,
        "rs_dispositivo": rs_dispositivo,
        "rs_quimicos": rs_quim,
        "rs_papel": rs_papel,
        "compras_rs": sum(compras.values()),
        "vazamento": bom - sum(compras.values()),
        "ajuste": ajuste,
        "share_folha_interna": share_int,
        "por_produto": compras,
    }


def direto(com_exportacao: bool) -> dict:
    if com_exportacao:
        return {
            "vbp": VBP,
            "va": VA_DIRETO,
            "ocupacoes": OCC_DIRETO,
            "remuneracoes": REM_DIRETO,
            "bom": BOM,
        }
    va = VBP_INT - BOM_INT
    occ = OCC_INT
    return {
        "vbp": VBP_INT,
        "va": va,
        "ocupacoes": occ,
        "remuneracoes": occ * REM_POR_OCUP,
        "bom": BOM_INT,
    }


def propagar(mip, compras_rs: dict) -> dict:
    """Choque de produto em R$ de 2025 → produção, VAB, salários e ocupações da cadeia."""
    idx = {c: i for i, c in enumerate(mip["prod_cod"])}
    g_2025 = np.zeros(117)
    for cod, valor in compras_rs.items():
        g_2025[idx[cod]] += valor
    g_2019_mi = g_2025 * PHI / 1e6  # R$ milhões de 2019
    f = mip["D"] @ g_2019_mi
    x = mip["L"] @ f
    va = mip["coef_va"] * x
    rem = mip["w_ativ"] * x
    occ = mip["e_ativ"] * x
    return {
        "g_2025": g_2025,
        "f_2019_mi": f,
        "x_2019_mi": x,
        "va_2019_mi": va,
        "rem_2019_mi": rem,
        "occ": occ,
        "producao_2025": float(x.sum() * 1e6 / PHI),
        "va_2025": float(va.sum() * 1e6 / PHI),
        "rem_2025": float(rem.sum() * 1e6 / PHI),
        "ocupacoes": float(occ.sum()),
        "choque_atividade_2025": f * 1e6 / PHI,
        "occ_por_atividade": occ,
    }


def induzido(mip, remuneracao_rs: float) -> dict:
    """Uma rodada. 60% da massa salarial do RS vira consumo no perfil da MIP."""
    consumo = PROPENSAO_CONSUMO_RS * remuneracao_rs
    g_2025 = mip["share_consumo"] * consumo
    g_2019_mi = g_2025 * PHI / 1e6
    f = mip["D"] @ g_2019_mi
    x = mip["L"] @ f
    va = mip["coef_va"] * x
    rem = mip["w_ativ"] * x
    occ = mip["e_ativ"] * x
    va_2025 = float(va.sum() * 1e6 / PHI)
    rem_2025 = float(rem.sum() * 1e6 / PHI)
    # Série fechada, só para nota: realimenta o salário desta rodada.
    k = (PROPENSAO_CONSUMO_RS * rem_2025 / consumo) if consumo else 0.0
    fator = (1.0 / (1.0 - k)) if 0 <= k < 1 else None
    return {
        "consumo_2025": consumo,
        "x_2019_mi": x,
        "va_2019_mi": va,
        "producao_2025": float(x.sum() * 1e6 / PHI),
        "va_2025": va_2025,
        "rem_2025": rem_2025,
        "ocupacoes": float(occ.sum()),
        "k_realimentacao": k,
        "fator_serie_fechada": fator,
        "va_serie_fechada_2025": None if fator is None else va_2025 * fator,
    }


def fiscal(com_exportacao: bool, va: float, rem: float) -> dict:
    """Fiscal bruto da revisão 4. Exportação é imune: o tributo sobre consumo não muda."""
    eob = va - rem
    irpj = 0.34 * 0.50 * eob
    return {
        "tributos_consumo_brasil": 13.70e9,
        "tributos_consumo_federal": 6.58e9,
        "tributos_consumo_subnacional_brasil": 7.12e9,
        "tributos_consumo_rs": 0.928e9,
        "tributos_consumo_rs_estadual_municipal": 0.48e9,
        "irpj_csll": irpj,
        "incentivo": 0.0,
        "retorno_liquido": None,
        "icms_rs_incentivavel": 0.48e9,
        "icms_rs_municipal": 0.12e9,
        "icms_rs_estadual": 0.36e9,
        "consumo_federal_no_rs": 0.928e9 - 0.48e9,
        "fundopem_percentual": 0.30,
        "fundopem_prazo_meses": 96,
        "fundopem_diferido_ano_cheio": 0.30 * 0.48e9,
        "integrar_abatimento": 0.0,
        "renuncia_permanente": 0.0,
        "nota_irpj": (
            "mesma regra da revisão 4: 34% sobre lucro fiscal = 50% do excedente "
            "(VAB − remunerações). No cenário sem exportação, a regra é reaplicada "
            "ao VAB e à remuneração internos."
            if not com_exportacao
            else "hipótese da revisão 4, R$ 1,23 bi no ano cheio com exportação."
        ),
    }


def cenario(mip, alpha: float, com_exportacao: bool, modo: str = "estimado") -> dict:
    d = direto(com_exportacao)
    if modo == "uniforme":
        compras = montar_compras(alpha, com_exportacao)
        compras["linhas"] = []
        compras["alpha"] = alpha
    else:
        compras = abertura_bom(com_exportacao)
        alpha = compras["alpha"]
    cadeia = propagar(mip, compras["por_produto"])
    ind = induzido(mip, d["remuneracoes"] + cadeia["rem_2025"])
    fisc = fiscal(com_exportacao, d["va"], d["remuneracoes"])
    return {
        "alpha": alpha,
        "com_exportacao": com_exportacao,
        "direto": d,
        "compras": {k: v for k, v in compras.items() if k != "por_produto"},
        "por_produto_2025": compras["por_produto"],
        "cadeia": {
            "producao_2025": cadeia["producao_2025"],
            "va_2025": cadeia["va_2025"],
            "rem_2025": cadeia["rem_2025"],
            "ocupacoes": cadeia["ocupacoes"],
        },
        "induzido": {
            "consumo_2025": ind["consumo_2025"],
            "producao_2025": ind["producao_2025"],
            "va_2025": ind["va_2025"],
            "rem_2025": ind["rem_2025"],
            "ocupacoes": ind["ocupacoes"],
            "k_realimentacao": ind["k_realimentacao"],
            "fator_serie_fechada": ind["fator_serie_fechada"],
            "va_serie_fechada_2025": ind["va_serie_fechada_2025"],
        },
        "total_tipo_I": {
            "va_2025": d["va"] + cadeia["va_2025"],
            "rem_2025": d["remuneracoes"] + cadeia["rem_2025"],
            "ocupacoes": d["ocupacoes"] + cadeia["ocupacoes"],
            "producao_2025": d["vbp"] + cadeia["producao_2025"],
        },
        "total_tipo_II": {
            "va_2025": d["va"] + cadeia["va_2025"] + ind["va_2025"],
            "rem_2025": d["remuneracoes"] + cadeia["rem_2025"] + ind["rem_2025"],
            "ocupacoes": d["ocupacoes"] + cadeia["ocupacoes"] + ind["ocupacoes"],
            "producao_2025": d["vbp"] + cadeia["producao_2025"] + ind["producao_2025"],
        },
        "fiscal": fisc,
        "_x_cadeia": cadeia["x_2019_mi"],
        "_va_cadeia": cadeia["va_2019_mi"],
        "_x_ind": ind["x_2019_mi"],
        "_va_ind": ind["va_2019_mi"],
        "_f_cadeia": cadeia["choque_atividade_2025"],
    }


def mi(valor: float) -> int:
    return int(round(valor / 1e6))


def bi1(valor: float) -> float:
    return round(valor / 1e9, 1)


def bi2(valor: float) -> float:
    return round(valor / 1e9, 2)


def salvar_tabelas(mip, base, faixa, sem_exp):
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    # Vetor de choque por produto e por atividade (R$ milhões de 2025).
    linhas = ["codigo,nome,compra_rs_mi_2025,hipotese"]
    rotulo = {
        "PR004": "dado das premissas (folha, porteira, margem zero)",
        "PR066": "hipótese de composição: dispositivo",
        "PR051": "hipótese de composição: químicos",
        "PR036": "hipótese de composição: embalagem e papel",
    }
    for cod, nome in zip(mip["prod_cod"], mip["prod_nom"]):
        valor = base["por_produto_2025"].get(cod, 0.0)
        if valor == 0:
            continue
        linhas.append(
            f"{cod},\"{nome}\",{valor/1e6:.3f},{rotulo.get(cod, '')}"
        )
    (RESULTADOS / "choque_produtos.csv").write_text("\n".join(linhas) + "\n", encoding="utf-8")

    linhas = ["codigo,atividade,choque_mi_2025,producao_cadeia_mi_2025,va_cadeia_mi_2025,coef_va"]
    for i, (cod, nome) in enumerate(zip(mip["ati_cod"], mip["ati_nom"])):
        linhas.append(
            f"{cod},\"{nome}\","
            f"{base['_f_cadeia'][i]/1e6:.3f},"
            f"{base['_x_cadeia'][i] * 1e6 / PHI / 1e6:.3f},"
            f"{base['_va_cadeia'][i] * 1e6 / PHI / 1e6:.3f},"
            f"{mip['coef_va'][i]:.4f}"
        )
    (RESULTADOS / "cadeia_por_atividade.csv").write_text("\n".join(linhas) + "\n", encoding="utf-8")

    def linha_cen(nome, c):
        return (
            f"{nome},{c['alpha']:.2f},{int(c['com_exportacao'])},"
            f"{mi(c['direto']['va'])},{mi(c['cadeia']['va_2025'])},{mi(c['induzido']['va_2025'])},"
            f"{mi(c['total_tipo_I']['va_2025'])},{mi(c['total_tipo_II']['va_2025'])},"
            f"{c['direto']['ocupacoes']:.0f},{c['cadeia']['ocupacoes']:.0f},{c['induzido']['ocupacoes']:.0f},"
            f"{c['total_tipo_I']['ocupacoes']:.0f},{c['total_tipo_II']['ocupacoes']:.0f},"
            f"{mi(c['direto']['remuneracoes'])},{mi(c['cadeia']['rem_2025'])},{mi(c['induzido']['rem_2025'])},"
            f"{mi(c['compras']['compras_rs'])},{mi(c['compras']['vazamento'])},"
            f"{mi(c['cadeia']['producao_2025'])},{mi(c['induzido']['producao_2025'])}"
        )

    cab = (
        "cenario,alpha,com_exportacao,"
        "va_direto_mi,va_cadeia_mi,va_induzido_mi,va_tipo_I_mi,va_tipo_II_mi,"
        "occ_direto,occ_cadeia,occ_induzido,occ_tipo_I,occ_tipo_II,"
        "rem_direto_mi,rem_cadeia_mi,rem_induzido_mi,"
        "compras_rs_mi,vazamento_mi,producao_cadeia_mi,producao_induzido_mi"
    )
    linhas = [cab, linha_cen("base_abertura_estimada", base)]
    for a, c in faixa.items():
        linhas.append(linha_cen(f"sensibilidade_local_{int(a*100)}", c))
    linhas.append(linha_cen("abertura_sem_exportacao", sem_exp))
    (RESULTADOS / "resultados_cenarios.csv").write_text("\n".join(linhas) + "\n", encoding="utf-8")

    linhas = ["grupo_tru16,producao_mip_mi_2019,producao_tru_mi_2019,coef_remuneracao,coef_ocupacoes_por_mi"]
    tru_prod = dict(zip(mip["tru"]["grupos"], mip["tru"]["producao"]))
    # A ordem dos nomes pode diferir; casa pelo índice da lista GRUPOS_16, que segue a TRU.
    for i, (nome, _) in enumerate(GRUPOS_16):
        tru_nome = mip["tru"]["grupos"][i]
        linhas.append(
            f"\"{nome}\",{mip['prod_grupo'][nome]:.3f},{mip['tru']['producao'][i]:.3f},"
            f"{mip['coef_rem'][nome]:.6f},{mip['coef_occ'][nome]:.6f}"
        )
    (RESULTADOS / "coeficientes_tru16.csv").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def estilo():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#D5D1C8",
            "axes.labelcolor": "#1B3A4B",
            "xtick.color": "#1B3A4B",
            "ytick.color": "#1B3A4B",
            "text.color": "#1B3A4B",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.titleweight": "medium",
            "axes.titlesize": 12,
            "axes.labelsize": 10,
        }
    )


NAVY = "#1B3A4B"
TEAL = "#1F7A6B"
GOLD = "#B0893E"
CLAY = "#A24B32"
SLATE = "#5C6B73"


def figura_gavetas(base):
    estilo()
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    nomes = ["Direto\n(planta)", "Cadeia\n(compras no RS)", "Induzido\n(uma rodada)", "Total\nno RS"]
    vals = [
        base["direto"]["va"] / 1e9,
        base["cadeia"]["va_2025"] / 1e9,
        base["induzido"]["va_2025"] / 1e9,
        base["total_tipo_II"]["va_2025"] / 1e9,
    ]
    cores = [NAVY, TEAL, GOLD, "#0E2A36"]
    barras = ax.bar(nomes, vals, color=cores, width=0.72)
    for b, v in zip(barras, vals):
        ax.text(
            b.get_x() + b.get_width() / 2,
            v + 0.15,
            f"{v:.2f}".replace(".", ","),
            ha="center",
            va="bottom",
            fontsize=11,
            color=NAVY,
        )
    ax.set_ylabel("R$ bilhões de 2025")
    ax.set_title("Valor adicionado no Rio Grande do Sul em 2037\nCenário base: abertura estimada do custo dos insumos")
    ax.set_ylim(0, max(vals) * 1.18)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig1_valor_adicionado.png", dpi=160)
    plt.close()


def figura_setores(mip, base):
    estilo()
    va = base["_va_cadeia"] * 1e6 / PHI / 1e9
    ordem = np.argsort(va)[::-1][:8]
    nomes = []
    for i in ordem:
        nome = mip["ati_nom"][i]
        if len(nome) > 42:
            nome = nome[:40] + "…"
        nomes.append(nome)
    valores = va[ordem]
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    y = np.arange(len(nomes))[::-1]
    ax.barh(y, valores, color=TEAL, height=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels(nomes, fontsize=9)
    ax.set_xlabel("Valor adicionado da cadeia, R$ bilhões de 2025")
    ax.set_title("Onde a cadeia gaúcha acrescenta valor em 2037\nOito atividades com maior valor adicionado indireto")
    for yi, v in zip(y, valores):
        ax.text(v + 0.005, yi, f"{v:.2f}".replace(".", ","), va="center", fontsize=8, color=NAVY)
    ax.set_xlim(0, max(valores) * 1.22)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig2_cadeia_por_atividade.png", dpi=160)
    plt.close()


def figura_faixa(faixa, sem_exp, base):
    estilo()
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.4))
    alphas = [10, 20, 35]
    va_c = [faixa[a / 100]["cadeia"]["va_2025"] / 1e9 for a in alphas]
    va_t = [faixa[a / 100]["total_tipo_II"]["va_2025"] / 1e9 for a in alphas]
    ax = axes[0]
    x = np.arange(len(alphas))
    ax.bar(x - 0.18, va_c, width=0.36, color=TEAL, label="Cadeia")
    ax.bar(x + 0.18, va_t, width=0.36, color=NAVY, label="Total com induzido")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{a}%" for a in alphas])
    ax.set_xlabel("Conteúdo local dos insumos não agrícolas")
    ax.set_ylabel("R$ bilhões de 2025")
    ax.axhline(base["cadeia"]["va_2025"] / 1e9, color=CLAY, lw=1.2, label="Abertura estimada")
    ax.set_title("Sensibilidade 10 / 20 / 35")
    ax.legend(frameon=False, fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax = axes[1]
    rotulos = ["Com exportação", "Sem exportação"]
    va_dir = [base["direto"]["va"] / 1e9, sem_exp["direto"]["va"] / 1e9]
    va_cad = [base["cadeia"]["va_2025"] / 1e9, sem_exp["cadeia"]["va_2025"] / 1e9]
    va_ind = [base["induzido"]["va_2025"] / 1e9, sem_exp["induzido"]["va_2025"] / 1e9]
    ax.bar(rotulos, va_dir, color=NAVY, label="Direto")
    ax.bar(rotulos, va_cad, bottom=va_dir, color=TEAL, label="Cadeia")
    baixo = [a + b for a, b in zip(va_dir, va_cad)]
    ax.bar(rotulos, va_ind, bottom=baixo, color=GOLD, label="Induzido")
    ax.set_ylabel("R$ bilhões de 2025")
    ax.set_title("Variante sem exportação")
    ax.legend(frameon=False, fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.suptitle("Valor adicionado no RS em 2037", fontsize=12, color=NAVY)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig3_faixa_e_exportacao.png", dpi=160)
    plt.close()


def figura_comparacao(base):
    estilo()
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    nomes = [
        "Este estudo\nTipo I\n(direto + cadeia)",
        "Bloco II\ndo contratante\nTipo I, RS",
        "Este estudo\nTipo II\n(+ induzido)",
    ]
    vals = [
        base["total_tipo_I"]["va_2025"] / 1e9,
        BLOCO_II["vab_rs_bi"],
        base["total_tipo_II"]["va_2025"] / 1e9,
    ]
    cores = [TEAL, SLATE, NAVY]
    barras = ax.bar(nomes, vals, color=cores, width=0.62)
    for b, v in zip(barras, vals):
        ax.text(
            b.get_x() + b.get_width() / 2,
            v + 0.12,
            f"{v:.2f}".replace(".", ","),
            ha="center",
            fontsize=11,
        )
    ax.set_ylabel("Valor adicionado no RS, R$ bilhões de 2025")
    ax.set_title("Ordem de grandeza em 2037\nO bloco II não entra na conta e não se soma a este estudo")
    ax.set_ylim(0, max(vals) * 1.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig4_comparacao_bloco_ii.png", dpi=160)
    plt.close()


def figura_ocupacoes(base):
    estilo()
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    nomes = ["Direto\n(planta, premissa v6)", "Cadeia\n(coeficiente TRU-16)", "Induzido\n(coeficiente TRU-16)"]
    vals = [
        base["direto"]["ocupacoes"] / 1000,
        base["cadeia"]["ocupacoes"] / 1000,
        base["induzido"]["ocupacoes"] / 1000,
    ]
    cores = [NAVY, TEAL, GOLD]
    barras = ax.bar(nomes, vals, color=cores, width=0.68)
    for b, v in zip(barras, vals):
        ax.text(
            b.get_x() + b.get_width() / 2,
            v + 0.08,
            f"{v:.1f}".replace(".", ","),
            ha="center",
            fontsize=11,
        )
    ax.set_ylabel("Mil ocupações em 2037")
    ax.set_title("Ocupações no Rio Grande do Sul em 2037\nCadeia e induzido usam o coeficiente agregado da TRU, não um levantamento da planta")
    ax.set_ylim(0, max(vals) * 1.22)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig5_ocupacoes.png", dpi=160)
    plt.close()


def figura_mapa(pontos=None):
    estilo()
    fig, ax = plt.subplots(figsize=(8.2, 6.2))
    geo_ok = False
    geo_path = Path("/tmp/brazil-states.geojson")
    if not geo_path.exists():
        try:
            import urllib.request

            url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                geo_path.write_bytes(resp.read())
        except Exception:
            geo_ok = False
    if geo_path.exists():
        try:
            geo = json.loads(geo_path.read_text(encoding="utf-8"))
            for feat in geo["features"]:
                nome = (
                    feat.get("properties", {}).get("name")
                    or feat.get("properties", {}).get("sigla")
                    or ""
                )
                if nome not in {"Rio Grande do Sul", "RS"}:
                    continue
                geom = feat["geometry"]
                polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
                if geom["type"] == "Polygon":
                    polys = [geom["coordinates"]]
                for poly in polys:
                    anel = poly[0]
                    xs = [p[0] for p in anel]
                    ys = [p[1] for p in anel]
                    ax.fill(xs, ys, color="#E7F0EA", zorder=0)
                    ax.plot(xs, ys, color="#7FA392", lw=0.8, zorder=1)
                geo_ok = True
        except Exception:
            geo_ok = False
    if not geo_ok:
        ax.set_xlim(-58, -49)
        ax.set_ylim(-34, -27)
        ax.add_patch(
            FancyBboxPatch(
                (-57.2, -33.4),
                7.4,
                6.2,
                boxstyle="round,pad=0.02,rounding_size=0.4",
                facecolor="#E7F0EA",
                edgecolor="#7FA392",
            )
        )
    pontos = pontos or []
    desloc = {
        "Santa Cruz do Sul": (8, -12),
        "Venâncio Aires": (8, 6),
        "Candelária": (-70, 4),
        "Canguçu": (-58, -10),
        "São Lourenço do Sul": (8, -8),
        "Vale do Sol": (-72, 8),
        "Rio Pardo": (8, -8),
        "Vera Cruz": (-64, -8),
    }
    for p in pontos:
        if p.get("lon") is None:
            continue
        sede = p["municipio"] == "Santa Cruz do Sul"
        tamanho = 18 + p["folha_t"] * 1.1
        ax.scatter(
            [p["lon"]],
            [p["lat"]],
            s=tamanho,
            color=CLAY if sede else (TEAL if p.get("corede") else NAVY),
            alpha=0.85,
            zorder=3,
        )
        if p["folha_t"] >= 100 or sede:
            texto = "Santa Cruz do Sul (sede)" if sede else p["municipio"]
            ax.annotate(
                texto,
                (p["lon"], p["lat"]),
                textcoords="offset points",
                xytext=desloc.get(p["municipio"], (5, 5)),
                fontsize=7.5,
                color=NAVY,
            )
    ax.set_title(
        "Área de apresentação: sede, COREDE e folha estimada em 2037\n"
        "Bolha proporcional à tonelada. Regionalização contábil, não spillover econométrico."
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="datalim")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig6_mapa_exemplos.png", dpi=160)
    plt.close()


COREDE_VRP = [
    "Arroio do Tigre", "Boqueirão do Leão", "Candelária", "Encruzilhada do Sul",
    "Estrela Velha", "General Câmara", "Herveiras", "Ibarama", "Lagoa Bonita do Sul",
    "Mato Leitão", "Pantano Grande", "Passa Sete", "Passo do Sobrado", "Rio Pardo",
    "Santa Cruz do Sul", "Segredo", "Sinimbu", "Sobradinho", "Tunas", "Vale do Sol",
    "Vale Verde", "Venâncio Aires", "Vera Cruz",
]

# Sedes municipais, para o mapa de apresentação. Não é o portão da planta.
COORDS = {
    "Santa Cruz do Sul": (-29.718, -52.426),
    "Vera Cruz": (-29.718, -52.507),
    "Venâncio Aires": (-29.606, -52.192),
    "Rio Pardo": (-29.988, -52.378),
    "Candelária": (-29.669, -52.789),
    "Vale do Sol": (-29.596, -52.683),
    "Sinimbu": (-29.528, -52.524),
    "Mato Leitão": (-29.524, -52.128),
    "Passo do Sobrado": (-29.748, -52.275),
    "Herveiras": (-29.455, -52.655),
    "Boqueirão do Leão": (-29.305, -52.430),
    "Arroio do Tigre": (-29.333, -53.093),
    "Sobradinho": (-29.414, -53.029),
    "Ibarama": (-29.420, -53.136),
    "Estrela Velha": (-29.177, -53.158),
    "Segredo": (-29.337, -52.978),
    "Tunas": (-29.104, -52.953),
    "Passa Sete": (-29.453, -52.960),
    "Lagoa Bonita do Sul": (-29.489, -53.014),
    "Encruzilhada do Sul": (-30.544, -52.522),
    "Pantano Grande": (-30.192, -52.373),
    "Vale Verde": (-29.787, -52.185),
    "General Câmara": (-29.905, -51.760),
    "Canguçu": (-31.395, -52.676),
    "São Lourenço do Sul": (-31.365, -51.978),
    "Dom Feliciano": (-30.704, -52.108),
    "Camaquã": (-30.851, -51.812),
    "Pelotas": (-31.765, -52.337),
    "Barros Cassal": (-29.095, -52.583),
}

# Censo 2010, trabalho principal em outro município. Revista Jovens Pesquisadores
# (UNISC), v. 5, n. 1, 2015, tabela 4, a partir do IBGE.
OUTFLOW_2010 = {
    "Vera Cruz": 2992, "Venâncio Aires": 2179, "Rio Pardo": 2856, "Candelária": 1171,
    "Mato Leitão": 401, "Sinimbu": 456, "Vale do Sol": 336, "Passo do Sobrado": 239,
    "Herveiras": 17, "Boqueirão do Leão": 22, "General Câmara": 435,
}
OCUPADOS_NO_PROPRIO_MUNICIPIO_SCS_2010 = 62396


def folha_municipal():
    """PAM 2025, SIDRA 1612, fumo em folha (produto 2703), quantidade produzida."""
    import urllib.request

    def baixar_uf(n3, nome):
        destino = TMP / f"pam_{nome}.json"
        url = (
            "https://servicodados.ibge.gov.br/api/v3/agregados/1612/periodos/2025/"
            f"variaveis/214?localidades=N6[N3[{n3}]]&classificacao=81[2703]"
        )
        if not (destino.exists() and destino.stat().st_size > 1000):
            TMP.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                destino.write_bytes(resp.read())
        data = json.loads(destino.read_text(encoding="utf-8"))
        saida = []
        for s in data[0]["resultados"][0]["series"]:
            nome_m = s["localidade"]["nome"].split(" - ")[0]
            uf = s["localidade"]["nome"].split(" - ")[-1]
            v = s["serie"].get("2025")
            if v in (None, "-", "...", "X", ""):
                continue
            saida.append((uf, nome_m, float(v)))
        return saida

    registros = baixar_uf(43, "rs") + baixar_uf(42, "sc") + baixar_uf(41, "pr")
    total_rs = sum(t for uf, _, t in registros if uf == "RS")
    bruto = [(uf, m, t, t * 0.0086) for uf, m, t in registros]
    soma_bruta_rs = sum(f for uf, _, _, f in bruto if uf == "RS")
    fator = (LEAF_TON_RS / soma_bruta_rs) if soma_bruta_rs else 1.0
    linhas = []
    for uf, m, t, f in bruto:
        folha = f * fator if uf == "RS" else f
        linhas.append({
            "uf": uf,
            "municipio": m,
            "pam_t": t,
            "folha_regra_t": f,
            "folha_t": folha,
            "valor_rs": folha * 17561.0 if uf == "RS" else None,
            "familias": folha / 5.5 if uf == "RS" else None,
            "corede": m in COREDE_VRP and uf == "RS",
            "lat": COORDS.get(m, (None, None))[0],
            "lon": COORDS.get(m, (None, None))[1],
        })
    return {
        "ano": 2025,
        "total_pam_rs_t": total_rs,
        "folha_bruta_rs_t": soma_bruta_rs,
        "fator_fecha_3007": fator,
        "residuo_t": soma_bruta_rs - LEAF_TON_RS,
        "linhas": linhas,
    }


def residencia():
    """Ponto médio do fator de destino 0–1 sobre a pendularidade publicada de 2010."""
    fator = 0.5
    peso_in = fator * sum(OUTFLOW_2010.values())
    base = OCUPADOS_NO_PROPRIO_MUNICIPIO_SCS_2010 + peso_in
    linhas = [{
        "municipio": "Santa Cruz do Sul",
        "peso": OCUPADOS_NO_PROPRIO_MUNICIPIO_SCS_2010 / base,
        "ocupacoes": OCC_DIRETO * OCUPADOS_NO_PROPRIO_MUNICIPIO_SCS_2010 / base,
        "remuneracoes": REM_DIRETO * OCUPADOS_NO_PROPRIO_MUNICIPIO_SCS_2010 / base,
    }]
    for m, n in OUTFLOW_2010.items():
        p = fator * n / base
        linhas.append({
            "municipio": m,
            "peso": p,
            "ocupacoes": OCC_DIRETO * p,
            "remuneracoes": REM_DIRETO * p,
            "outflow_2010": n,
        })
    return {
        "fator_destino": fator,
        "fonte": "Censo 2010, tabela de deslocamento para o trabalho reproduzida em Revista Jovens Pesquisadores, UNISC, 2015; fator de destino 0,5 é o ponto médio",
        "linhas": linhas,
    }


def leitura_salarial():
    """Comparação. Não substitui as 4,06 mil ocupações nem os R$ 609 mi."""
    ipca_21, ipca_23 = 6120.04, 6773.27
    cempre_anual_2021 = 338_100_000 / 3136
    pia_anual_2023 = 732_683_000 / 6165
    cempre_2025 = cempre_anual_2021 * IPCA_DEZ_2025 / ipca_21
    pia_2025 = pia_anual_2023 * IPCA_DEZ_2025 / ipca_23
    encargos = 0.368
    quadro = [
        ("Produção e operação", 0.55, 8000),
        ("Manutenção", 0.15, 11500),
        ("Administração e suporte", 0.15, 13000),
        ("Técnicos de processo e qualidade", 0.08, 15000),
        ("Técnico de campo", 0.07, 9500),
    ]
    media_mensal = sum(p * s for _, p, s in quadro)
    return {
        "premissa_com_encargos": REM_POR_OCUP,
        "cempre_2021_scs_divisao_12_anual": cempre_anual_2021,
        "cempre_2021_pessoas": 3136,
        "cempre_2025": cempre_2025,
        "pia_2023_rs_anual": pia_anual_2023,
        "pia_2023_pessoas": 6165,
        "pia_2025": pia_2025,
        "encargos_patronais": encargos,
        "cempre_2025_com_encargos": cempre_2025 * (1 + encargos),
        "pia_2025_com_encargos": pia_2025 * (1 + encargos),
        "quadro": [
            {"funcao": n, "parcela": p, "salario_mensal": s, "ocupacoes": OCC_DIRETO * p}
            for n, p, s in quadro
        ],
        "media_mensal_quadro": media_mensal,
        "anual_13_quadro": media_mensal * 13,
    }


def limpar(obj):
    if isinstance(obj, dict):
        return {k: limpar(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [limpar(v) for v in obj]
    if isinstance(obj, float):
        return round(obj, 6) if abs(obj) < 1e6 else round(obj, 2)
    return obj


def main():
    FIGURAS.mkdir(parents=True, exist_ok=True)
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    print("Carregando MIP-RS 2019...")
    mip = carregar_mip()
    print(f"PHI IPCA = {PHI:.6f}")
    print(f"erro L vs tabela 14 = {mip['erro_L']:.3e}")
    print(f"erro (I-A)L - I = {mip['erro_ident']:.3e}")
    print(f"erro D@B - A = {mip['erro_A']:.3e}")
    print(f"soma colunas D: {mip['soma_D_min']:.4f} a {mip['soma_D_max']:.4f}")
    print(f"produção total atividades R$ mi 2019 = {mip['x_ativ'].sum():.1f}")
    print(f"TRU produção total = {sum(mip['tru']['producao']):.1f}")
    print("Produção por grupo (MIP agregado vs TRU):")
    for i, (nome, _) in enumerate(GRUPOS_16):
        tru_n = mip["tru"]["grupos"][i]
        a = mip["prod_grupo"][nome]
        b = mip["tru"]["producao"][i]
        print(f"  {a:12.1f} {b:12.1f} dif {a-b:10.1f}  mip={nome[:28]:28s} tru={tru_n[:36]}")

    base = cenario(mip, TAXA_BASE, True, "estimado")
    faixa = {a: cenario(mip, a, True, "uniforme") for a in TAXA_CONTEUDO_LOCAL}
    sem_exp = cenario(mip, TAXA_BASE, False, "estimado")
    investimento = capex_conversao()
    obra = propagar(mip, investimento["por_produto_rs"])
    i_constr = [i for i, c in enumerate(mip["ati_cod"]) if mip["mapa_grupo"][c] == "Construção"]
    postos_obra = float(obra["occ_por_atividade"][i_constr].sum()) if i_constr else 0.0

    print("\n=== BASE 2037 ===")
    for bloco in ("direto", "cadeia", "induzido"):
        b = base[bloco]
        if bloco == "direto":
            print(f"direto VA {b['va']/1e9:.3f} occ {b['ocupacoes']:.0f} rem {b['remuneracoes']/1e6:.1f}")
        else:
            print(
                f"{bloco} VA {b['va_2025']/1e9:.3f} prod {b['producao_2025']/1e9:.3f} "
                f"occ {b['ocupacoes']:.0f} rem {b['rem_2025']/1e6:.1f}"
            )
    print("tipo I", base["total_tipo_I"]["va_2025"] / 1e9, "tipo II", base["total_tipo_II"]["va_2025"] / 1e9)
    print("compras RS", base["compras"]["compras_rs"] / 1e6, "vazamento", base["compras"]["vazamento"] / 1e6)
    print("alpha implícito", base["alpha"])
    print(
        f"OBRA capex {investimento['total']/1e6:.1f} RS {investimento['rs']/1e6:.1f} "
        f"VA {obra['va_2025']/1e6:.1f} occ {obra['ocupacoes']:.0f} postos constr {postos_obra:.0f}"
    )
    print("k induzido", base["induzido"]["k_realimentacao"], "fator", base["induzido"]["fator_serie_fechada"])
    print("sem exp VA tipo II", sem_exp["total_tipo_II"]["va_2025"] / 1e9, "occ", sem_exp["total_tipo_II"]["ocupacoes"])
    for a, c in faixa.items():
        print(
            f"alpha {a:.0%} cadeia VA {c['cadeia']['va_2025']/1e9:.3f} "
            f"total II {c['total_tipo_II']['va_2025']/1e9:.3f} occ II {c['total_tipo_II']['ocupacoes']:.0f}"
        )

    # Coeficientes de VA dos setores que recebem o choque direto de atividade.
    print("\nChoque por atividade (R$ mi 2025) — maiores:")
    ordem = np.argsort(base["_f_cadeia"])[::-1][:8]
    for i in ordem:
        print(f"  {mip['ati_cod'][i]} {mip['ati_nom'][i][:50]:50s} {base['_f_cadeia'][i]/1e6:8.1f} va_coef {mip['coef_va'][i]:.3f}")

    salvar_tabelas(mip, base, faixa, sem_exp)
    geo = folha_municipal()
    casa = residencia()
    salario = leitura_salarial()
    pontos_mapa = [
        x for x in geo["linhas"]
        if x["uf"] == "RS" and x["folha_t"] >= 40 and x["lat"] is not None
    ]
    figura_gavetas(base)
    figura_setores(mip, base)
    figura_faixa(faixa, sem_exp, base)
    figura_comparacao(base)
    figura_ocupacoes(base)
    figura_mapa(pontos_mapa)

    linhas_bom = ["linha,familia,produto,valor_mi,pct_rs,valor_rs_mi,valor_outros_estados_mi,valor_importado_mi,regra"]
    for x in base["compras"]["linhas"]:
        linhas_bom.append(
            f"\"{x['linha']}\",{x['familia']},{x['produto']},{x['valor']/1e6:.3f},{x['rs']:.2f},"
            f"{x['valor_rs']/1e6:.3f},{x['valor_uf']/1e6:.3f},{x['valor_imp']/1e6:.3f},\"{x['regra']}\""
        )
    (RESULTADOS / "bom_abertura.csv").write_text("\n".join(linhas_bom) + "\n", encoding="utf-8")

    linhas_mun = ["uf,municipio,corede,pam_2025_t,folha_regra_t,folha_ajustada_t,valor_mi,familias"]
    for x in geo["linhas"]:
        if x["pam_t"] <= 0:
            continue
        valor = "" if x["valor_rs"] is None else f"{x['valor_rs']/1e6:.3f}"
        fam = "" if x["familias"] is None else f"{x['familias']:.1f}"
        linhas_mun.append(
            f"{x['uf']},\"{x['municipio']}\",{int(x['corede'])},{x['pam_t']:.0f},"
            f"{x['folha_regra_t']:.2f},{x['folha_t']:.2f},{valor},{fam}"
        )
    (RESULTADOS / "folha_municipios.csv").write_text("\n".join(linhas_mun) + "\n", encoding="utf-8")

    obra_out = {
        "capex_total": investimento["total"],
        "capex_rs": investimento["rs"],
        "capex_importado": investimento["importado"],
        "partes": investimento["partes"],
        "capital_giro_fora_do_choque": investimento["capital_giro"],
        "piso_observado_fabrica": investimento["piso_observado"],
        "iss_santa_cruz": investimento["iss"],
        "producao_2025": obra["producao_2025"],
        "va_2025": obra["va_2025"],
        "rem_2025": obra["rem_2025"],
        "ocupacoes_leontief": obra["ocupacoes"],
        "postos_temporarios_construcao": postos_obra,
        "usd_ptax_2025": investimento["usd"],
        "eur_ptax_2025": investimento["eur"],
    }

    saida = {
        "matriz": {
            "nome": "MIP-RS 2019",
            "fonte": "DEE/SPGG e UFRJ (MAEP)",
            "agregacao": "117 produtos x 52 atividades",
            "arquivo": MIP_URL,
            "unidade_matriz": "R$ milhões correntes de 2019",
            "leontief": "L = (I − A)^(−1) calculada da tabela 13 e conferida com a tabela 14",
            "erro_max_L_vs_tabela14": mip["erro_L"],
            "erro_max_identidade": mip["erro_ident"],
            "erro_max_DxB_vs_A": mip["erro_A"],
            "ipca_dez_2019": IPCA_DEZ_2019,
            "ipca_dez_2025": IPCA_DEZ_2025,
            "phi_2019_sobre_2025": PHI,
            "formula": "fluxo_2019 = fluxo_2025 × (IPCA_dez2019 / IPCA_dez2025); resultado_2025 = resultado_2019 / phi",
        },
        "hipoteses": {
            "cenario_base": "abertura estimada do BOM",
            "conteudo_local_nao_agricola_implicito": base["alpha"],
            "faixa_sensibilidade_uniforme": list(TAXA_CONTEUDO_LOCAL),
            "propensao_consumo_rs": PROPENSAO_CONSUMO_RS,
            "adicionalidade": 1.0,
            "capex": "conversão calibrada; choque só da parcela gaúcha, bloco separado",
            "emprego_indireto": "coeficiente de ocupações por R$ milhão de produção da TRU-RS 2019, 16 atividades, aplicado a cada atividade do grupo",
        },
        "base": limpar(base),
        "faixa": {str(a): limpar(c) for a, c in faixa.items()},
        "sem_exportacao": limpar(sem_exp),
        "obra_2026_2027": limpar(obra_out),
        "folha_municipal": limpar({k: v for k, v in geo.items() if k != "linhas"}),
        "residencia": limpar(casa),
        "leitura_salarial": limpar(salario),
        "bloco_II_contratante": BLOCO_II,
        "exemplos_folha_premissas": EXEMPLOS_FOLHA,
        "consumo_familias_rs_preco_basico_mi_2019": mip["consumo_pos_mi"],
        "consumo_familias_valores_negativos_cortados_mi_2019": mip["consumo_neg_mi"],
    }
    (RESULTADOS / "resultados.json").write_text(
        json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Arquivos em", RESULTADOS, "e", FIGURAS)


if __name__ == "__main__":
    main()
