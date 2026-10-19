#!/usr/bin/env python3
"""Impacto 2037 com a MIP inter-regional Ipea–Receita Federal, ano-base 2018.

A matriz do multiplicador é a do release v1
(https://github.com/provictorludwig/mip-dados/releases/tag/v1):
27 UFs × 68 atividades, transações com base em NF-e. A planilha fica em
/tmp/mip-ipea e não entra no repositório.

O valor adicionado, o emprego e o salário da planta entram uma vez, em
Santa Cruz do Sul. A receita ex-fábrica não é choque. O BOM de R$ 8,00 bi,
aberto pelos produtos já estimados, entra como demanda intermediária a preço
básico, deflacionado a 2018 pelo IPCA (SIDRA 1737, dez/2018 e dez/2025).

A origem geográfica de cada insumo que não é folha é a oferta daquele produto
ao consumo intermediário do RS, lida na TRU (uso no RS por UF de origem).
A folha do RS, de SC e do PR vai para a agricultura desses estados.

x = (I − A)⁻¹ f. O modelo é tipo I: o consumo das famílias está fora de A.
A camada induzida é uma rodada à parte, 60% da massa salarial gerada no RS,
só sobre a oferta gaúcha, e não entra na manchete de tipo I.

A obra de 2026–2027 não é recalculada aqui. A MAI não casa com a parcela
local já estimada (máquinas importadas fora). O número permanece o da MIP-RS.
"""

from __future__ import annotations

import csv
import json
import subprocess
import urllib.request
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
RESULTADOS = ROOT / "resultados"
FIGURAS = ROOT / "figuras"
TMP = Path("/tmp/mip-ipea")
RELEASE_REPO = "provictorludwig/mip-dados"

# SIDRA 1737, variável 2266, número-índice (dez/1993 = 100).
# Lidos em 19/10/2026 e reconferidos na execução, se a rede responder.
IPCA_DEZ_2018 = 5100.61
IPCA_DEZ_2025 = 7403.29

N_UF = 27
N_AT = 68
N = N_UF * N_AT  # 1836
UFS = [
    "RO", "AC", "AM", "RR", "PA", "AP", "TO", "MA", "PI", "CE", "RN", "PB",
    "PE", "AL", "SE", "BA", "MG", "ES", "RJ", "SP", "PR", "SC", "RS", "MS",
    "MT", "GO", "DF",
]
I_PR, I_SC, I_RS = UFS.index("PR"), UFS.index("SC"), UFS.index("RS")

# Premissas da revisão 4, ano cheio 2037, R$ de 2025. Âncoras que não se movem.
VBP = 15.83e9
BOM = 8.00e9
VA_DIRETO = 7.83e9
LEAF_TOTAL = 114.2e6
LEAF_RS = 52.8e6
LEAF_TON_RS = 3007.0
OCC_DIRETO = 4060.0
REM_DIRETO = 609.0e6
PROPENSAO = 0.60

# MIP-RS 2019, coluna de checagem já publicada. Não é recalculada e não se soma.
MIP_RS = {
    "compra_rs": 830_039_006.82,
    "va_cadeia": 498_881_989.23,
    "va_induzido": 370_800_852.43,
    "va_tipo_I": 8_328_881_989.23,
    "va_tipo_II": 8_699_682_841.67,
    "rem_cadeia": 187_146_442.92,
    "rem_induzido": 144_396_191.18,
    "occ_cadeia": 4554.975001,
    "occ_induzido": 4202.135952,
    "occ_tipo_II": 12817.110953,
}

# Obra já calculada na MIP-RS. Bloco 2026–2027, fora de 2037.
OBRA_MIP_RS = {
    "capex_total": 1_634_714_532.58,
    "capex_rs": 483_875_501.65,
    "capex_importado": 1_150_839_030.94,
    "producao_2025": 740_356_286.67,
    "va_2025": 341_755_847.54,
    "rem_2025": 125_478_246.33,
    "ocupacoes_leontief": 4356.901637,
    "postos_temporarios_construcao": 2639.483276,
}

# Produto da TRU (índice 0–127 dentro da UF) e atividade Ipea (0–67).
# A atividade é o destino contábil; a TRU ainda reparte pela matriz de recursos
# quando o produto tem mais de um produtor na UF de origem.
PONTE = {
    "Dispositivo e eletrônico do pod": {
        "produto_tru": 73,
        "produto_nome": "Material eletrônico e equip. de comunicações",
        "atividade": 29,
        "grupo": "Dispositivo e eletrônico",
    },
    "Glicerina vegetal do e-líquido": {
        "produto_tru": 54,
        "produto_nome": "Produtos químicos orgânicos",
        "atividade": 20,
        "grupo": "Químicos",
    },
    "Propilenoglicol do e-líquido": {
        "produto_tru": 54,
        "produto_nome": "Produtos químicos orgânicos",
        "atividade": 20,
        "grupo": "Químicos",
    },
    "Aroma do e-líquido": {
        "produto_tru": 57,
        "produto_nome": "Produtos químicos diversos",
        "atividade": 21,
        "grupo": "Químicos",
    },
    "Extração de nicotina além da folha": {
        "produto_tru": 57,
        "produto_nome": "Produtos químicos diversos",
        "atividade": 21,
        "grupo": "Químicos",
    },
    "Embalagem do pod": {
        "produto_tru": 43,
        "produto_nome": "Papel, papelão, embalagens e artefatos de papel",
        "atividade": 16,
        "grupo": "Papel, filtro e embalagem",
    },
    "Químicos do stick": {
        "produto_tru": 57,
        "produto_nome": "Produtos químicos diversos",
        "atividade": 21,
        "grupo": "Químicos",
    },
    "Papel, filtro e embalagem do stick": {
        "produto_tru": 43,
        "produto_nome": "Papel, papelão, embalagens e artefatos de papel",
        "atividade": 16,
        "grupo": "Papel, filtro e embalagem",
    },
    "Químicos do sachê": {
        "produto_tru": 57,
        "produto_nome": "Produtos químicos diversos",
        "atividade": 21,
        "grupo": "Químicos",
    },
    "Papel e embalagem do sachê": {
        "produto_tru": 43,
        "produto_nome": "Papel, papelão, embalagens e artefatos de papel",
        "atividade": 16,
        "grupo": "Papel, filtro e embalagem",
    },
    "Energia elétrica e combustível": {
        "produto_tru": 87,
        "produto_nome": "Eletricidade, gás e outras utilidades",
        "atividade": 37,
        "grupo": "Energia",
    },
    "Água": {
        "produto_tru": 88,
        "produto_nome": "Água, esgoto, reciclagem e gestão de resíduos",
        "atividade": 38,
        "grupo": "Água",
    },
    "Frete interno": {
        "produto_tru": 94,
        "produto_nome": "Transporte terrestre de carga",
        "atividade": 42,
        "grupo": "Frete interno",
    },
    "Manutenção": {
        "produto_tru": 86,
        "produto_nome": "Manutenção, reparação e instalação de máquinas e equipamentos",
        "atividade": 36,
        "grupo": "Manutenção",
    },
}

# Grupo espacial: mesma regra de núcleo do mapa (PAM, CEMPRE, pendularidade).
GRUPO_ESPACIAL = {
    0: "folha",
    1: "pecuaria",
    2: "madeira",
    3: "extrativa",
    4: "extrativa",
    5: "extrativa",
    6: "extrativa",
    7: "demais_ind",
    8: "demais_ind",
    9: "demais_ind",
    10: "demais_ind",
    11: "demais_ind",
    12: "demais_ind",
    13: "demais_ind",
    14: "demais_ind",
    15: "madeira",
    16: "papel",
    17: "papel",
    18: "refino",
    19: "refino",
    20: "quim",
    21: "quim",
    22: "quim",
    23: "quim",
    24: "plast",
    25: "demais_ind",
    26: "demais_ind",
    27: "demais_ind",
    28: "demais_ind",
    29: "eletro",
    30: "eletrico",
    31: "demais_ind",
    32: "demais_ind",
    33: "demais_ind",
    34: "demais_ind",
    35: "demais_ind",
    36: "demais_ind",
    37: "energia",
    38: "energia",
    39: "construcao",
    40: "comercio",
    41: "comercio",
    42: "transporte",
    43: "transporte",
    44: "transporte",
    45: "transporte",
    46: "aloj_alim",
    47: "aloj_alim",
    48: "informacao",
    49: "informacao",
    50: "informacao",
    51: "informacao",
    52: "financeira",
    53: "imobiliario",
    54: "profissionais",
    55: "profissionais",
    56: "profissionais",
    57: "administrativo",
    58: "administrativo",
    59: "administrativo",
    60: "publico",
    61: "sociais",
    62: "sociais",
    63: "sociais",
    64: "sociais",
    65: "sociais",
    66: "sociais",
    67: "sociais",
}

NAVY = "#1B3A4B"
TEAL = "#1F7A6B"
SAND = "#C4A46B"
INK = "#243038"


def _font() -> None:
    regular = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    bold = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    font_manager.fontManager.addfont(regular)
    font_manager.fontManager.addfont(bold)
    plt.rcParams["font.family"] = "Liberation Sans"
    plt.rcParams["axes.unicode_minus"] = False


def garantir_release() -> dict[str, Path]:
    """Baixa o release v1 para /tmp e descompacta. Não versiona xlsx nem zip."""
    TMP.mkdir(parents=True, exist_ok=True)
    zips = {
        "mip": TMP / "MIP_Interregional_2018_68_27.xlsx.zip",
        "tru": TMP / "TRU_Interregional_2018_68_27.1.xlsx.zip",
        "mai": TMP / "MAI_InterReg_2018_27_68.xlsx.zip",
    }
    if not all(p.exists() and p.stat().st_size > 1_000_000 for p in zips.values()):
        subprocess.check_call(
            ["gh", "release", "download", "v1", "--repo", RELEASE_REPO, "-D", str(TMP)],
        )
    alvos = {
        "mip": TMP / "mip" / "MIP_Interregional_2018_68_27.xlsx",
        "tru": TMP / "tru" / "TRU_Interregional_2018_68_27 (1).xlsx",
        "mai": TMP / "mai" / "MAI_InterReg_2018_27_68.xlsx",
    }
    if not all(p.exists() and p.stat().st_size > 1_000_000 for p in alvos.values()):
        subprocess.check_call(["unzip", "-o", "-q", str(zips["mip"]), "-d", str(TMP / "mip")])
        subprocess.check_call(["unzip", "-o", "-q", str(zips["tru"]), "-d", str(TMP / "tru")])
        subprocess.check_call(["unzip", "-o", "-q", str(zips["mai"]), "-d", str(TMP / "mai")])
    return alvos


def ipca() -> dict:
    """Reconfere dez/2018 e dez/2025 na SIDRA. Usa o valor lido se a rede falhar."""
    url = (
        "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/201812,202512"
    )
    lido = {}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        for row in data[1:]:
            lido[row["D3C"]] = float(row["V"])
    except Exception as exc:  # noqa: BLE001 — a âncora já foi lida nesta data
        return {
            "dez_2018": IPCA_DEZ_2018,
            "dez_2025": IPCA_DEZ_2025,
            "phi": IPCA_DEZ_2018 / IPCA_DEZ_2025,
            "fonte": "SIDRA 1737, conferido em 19/10/2026; a rede não respondeu nesta execução",
            "erro_rede": str(exc),
        }
    d2018 = lido["201812"]
    d2025 = lido["202512"]
    if abs(d2018 - IPCA_DEZ_2018) > 0.001 or abs(d2025 - IPCA_DEZ_2025) > 0.001:
        raise SystemExit(f"IPCA divergiu do valor conferido: {lido}")
    return {
        "dez_2018": d2018,
        "dez_2025": d2025,
        "phi": d2018 / d2025,
        "fonte": "IBGE SIDRA tabela 1737, variável 2266, número-índice, dezembro",
    }


def _num_row(row, start: int, n: int) -> np.ndarray:
    out = np.zeros(n, dtype=float)
    for j in range(n):
        v = row[start + j]
        if isinstance(v, (int, float)):
            out[j] = float(v)
    return out


def carregar_mip(path: Path) -> dict:
    from python_calamine import CalamineWorkbook

    data = CalamineWorkbook.from_path(str(path)).get_sheet_by_name("MIP_Reg").to_python()
    atividades = [str(data[3 + k][1]) for k in range(N_AT)]
    if len(data) < 1864 or len(data[0]) < 2003:
        raise SystemExit(f"MIP com forma inesperada: {len(data)} x {len(data[0])}")

    Z = np.zeros((N, N), dtype=float)
    f_fd = np.zeros(N, dtype=float)
    for i in range(N):
        row = data[3 + i]
        Z[i, :] = _num_row(row, 2, N)
        f_fd[i] = float(np.sum(_num_row(row, 1839, N_UF * 6)))

    def linha_rodape(idx: int) -> np.ndarray:
        return _num_row(data[idx], 2, N)

    x = linha_rodape(1862)
    va = linha_rodape(1861)
    rem = linha_rodape(1849)
    occ = linha_rodape(1863)
    ci = linha_rodape(1848)
    if data[1862][1] != "VALOR DA PRODUCAO":
        raise SystemExit(f"Rodapé inesperado na produção: {data[1862][1]!r}")
    if "Valor adicionado bruto" not in str(data[1861][1]):
        raise SystemExit(f"Rodapé inesperado no VA: {data[1861][1]!r}")
    if data[1849][1] != "Remuneracoes":
        raise SystemExit(f"Rodapé inesperado na remuneração: {data[1849][1]!r}")
    if "Fator trabalho" not in str(data[1863][1]):
        raise SystemExit(f"Rodapé inesperado no trabalho: {data[1863][1]!r}")

    # Identidade de linha: produção = consumo intermediário doméstico + demanda final.
    row_sum = Z.sum(axis=1) + f_fd
    erro_linha = float(np.max(np.abs(row_sum - x)))

    positivo = x > 0
    A = np.zeros_like(Z)
    A[:, positivo] = Z[:, positivo] / x[positivo]
    coef_va = np.zeros(N)
    coef_rem = np.zeros(N)
    coef_occ = np.zeros(N)
    coef_va[positivo] = va[positivo] / x[positivo]
    coef_rem[positivo] = rem[positivo] / x[positivo]
    coef_occ[positivo] = occ[positivo] / x[positivo]

    # CI + VA = produção, nas colunas. Fecha a leitura do rodapé.
    erro_coluna = float(np.max(np.abs((ci + va) - x)))
    soma_A = A.sum(axis=0)
    # (I−A) x = f. Conferência antes de usar o choque da planta.
    x_hat = np.linalg.solve(np.eye(N) - A, f_fd)
    erro_abs = float(np.max(np.abs(x_hat - x)))
    base = np.maximum(np.abs(x), 1.0)
    erro_rel = float(np.max(np.abs(x_hat - x) / base))
    if erro_linha > 1e-4 or erro_coluna > 1e-4 or erro_rel > 1e-6:
        raise SystemExit(
            "A MIP não reproduziu a produção conhecida. "
            f"linha {erro_linha} coluna {erro_coluna} rel {erro_rel} abs {erro_abs}"
        )

    # Cesta de consumo das famílias no RS: coluna de demanda final, só a oferta gaúcha.
    # Ordem por UF: exportação, governo, ISFLSF, famílias, FBCF, estoque.
    col_fam_rs = 1839 + I_RS * 6 + 3
    cesta = np.zeros(N)
    neg = 0.0
    for k in range(N_AT):
        v = data[3 + I_RS * N_AT + k][col_fam_rs]
        if isinstance(v, (int, float)):
            if v < 0:
                neg += float(v)
            else:
                cesta[I_RS * N_AT + k] = float(v)
    if cesta.sum() <= 0:
        raise SystemExit("Cesta de consumo das famílias no RS ficou vazia.")
    share = cesta / cesta.sum()

    return {
        "atividades": atividades,
        "Z": Z,
        "A": A,
        "x": x,
        "va": va,
        "f_fd": f_fd,
        "coef_va": coef_va,
        "coef_rem": coef_rem,
        "coef_occ": coef_occ,
        "share_consumo_rs": share,
        "consumo_rs_mi": float(cesta.sum()),
        "consumo_rs_negativo_cortado_mi": neg,
        "erro_linha_mi": erro_linha,
        "erro_coluna_mi": erro_coluna,
        "erro_leontief_abs_mi": erro_abs,
        "erro_leontief_rel": erro_rel,
        "max_soma_coluna_A": float(soma_A.max()),
        "n_colunas_x_zero": int((~positivo).sum()),
        "producao_total_mi": float(x.sum()),
    }


def _uso_rs_por_origem(usos, pidx: int) -> np.ndarray:
    cols = range(2 + I_RS * N_AT, 2 + (I_RS + 1) * N_AT)
    out = np.zeros(N_UF, dtype=float)
    for u in range(N_UF):
        row = usos[3 + u * 128 + pidx]
        s = 0.0
        for c in cols:
            v = row[c]
            if isinstance(v, (int, float)):
                s += float(v)
        out[u] = s
    return out


def _make_uf(recursos, u: int, pidx: int) -> np.ndarray:
    row = recursos[3 + u * 128 + pidx]
    return np.maximum(_num_row(row, 2 + u * N_AT, N_AT), 0.0)


def montar_choque(usos, recursos, phi: float, linhas_bom: list[dict]) -> dict:
    """f em R$ milhões de 2018. Origem = oferta do produto ao consumo intermediário do RS."""
    f = np.zeros(N, dtype=float)
    por_linha = []
    origem_rows = []
    grupos: dict[str, dict] = {}

    somados: dict[str, float] = {}
    for linha in linhas_bom:
        somados[linha["linha"]] = somados.get(linha["linha"], 0.0) + float(linha["valor"])

    for nome, valor in somados.items():
        if nome not in PONTE:
            raise SystemExit(f"Linha do BOM sem ponte: {nome}")
        meta = PONTE[nome]
        bruto = _uso_rs_por_origem(usos, meta["produto_tru"])
        cortado = float(bruto[bruto < 0].sum())
        positivo = np.maximum(bruto, 0.0)
        total = float(positivo.sum())
        if total <= 0:
            raise SystemExit(f"Oferta ao RS zerada para {nome}")
        shares = positivo / total
        valor_2018_mi = valor * phi / 1e6
        principal = 0.0
        for u in range(N_UF):
            if shares[u] <= 0:
                continue
            pedaco = valor_2018_mi * float(shares[u])
            make = _make_uf(recursos, u, meta["produto_tru"])
            if make.sum() <= 0:
                f[u * N_AT + meta["atividade"]] += pedaco
                principal += pedaco
                peso = np.zeros(N_AT)
                peso[meta["atividade"]] = 1.0
            else:
                peso = make / make.sum()
                f[u * N_AT:(u + 1) * N_AT] += pedaco * peso
                principal += pedaco * float(peso[meta["atividade"]])
            origem_rows.append({
                "linha": nome,
                "grupo": meta["grupo"],
                "uf": UFS[u],
                "participacao": float(shares[u]),
                "valor_2025": valor * float(shares[u]),
                "valor_2018_mi": pedaco,
            })
        por_linha.append({
            "linha": nome,
            "grupo": meta["grupo"],
            "valor_2025": valor,
            "produto_tru": meta["produto_nome"],
            "produto_tru_indice": meta["produto_tru"],
            "atividade_indice": meta["atividade"],
            "atividade": None,  # preenchido depois
            "participacao_rs": float(shares[I_RS]),
            "valor_rs_2025": valor * float(shares[I_RS]),
            "valor_outros_ufs_2025": valor * (1.0 - float(shares[I_RS])),
            "negativo_cortado_mi_2018": cortado,
            "parcela_na_atividade_ponte": principal / valor_2018_mi,
            "chave": (
                "TRU Usos: participação de cada UF na oferta do produto ao "
                "consumo intermediário das 68 atividades do RS. A matriz de "
                "recursos reparte o valor, dentro da UF de origem, entre as "
                "atividades que produzem esse produto."
            ),
        })
        g = grupos.setdefault(meta["grupo"], {"valor": 0.0, "rs": 0.0})
        g["valor"] += valor
        g["rs"] += valor * float(shares[I_RS])

    # Folha: âncora publicada. RS 52,8 mi. O restante do Sul, 61,4 mi, em SC e PR
    # na proporção 29:25 (os 54% já definidos). Não usa a chave de oferta.
    resto = LEAF_TOTAL - LEAF_RS
    leaf_sc = resto * 29.0 / 54.0
    leaf_pr = resto * 25.0 / 54.0
    if abs((LEAF_RS + leaf_sc + leaf_pr) - LEAF_TOTAL) > 1.0:
        raise SystemExit("Folha do Sul não fecha.")
    for uf_i, valor, rotulo in (
        (I_RS, LEAF_RS, "Folha no RS"),
        (I_SC, leaf_sc, "Folha em Santa Catarina"),
        (I_PR, leaf_pr, "Folha no Paraná"),
    ):
        f[uf_i * N_AT + 0] += valor * phi / 1e6
        origem_rows.append({
            "linha": rotulo,
            "grupo": "Folha",
            "uf": UFS[uf_i],
            "participacao": valor / LEAF_TOTAL,
            "valor_2025": valor,
            "valor_2018_mi": valor * phi / 1e6,
        })
    grupos["Folha"] = {"valor": LEAF_TOTAL, "rs": LEAF_RS}

    return {
        "f": f,
        "por_linha": por_linha,
        "origem_rows": origem_rows,
        "grupos": grupos,
        "folha_sc": leaf_sc,
        "folha_pr": leaf_pr,
        "bom_linhas": float(sum(somados.values())),
    }


def propagar(mip: dict, f: np.ndarray) -> dict:
    x = np.linalg.solve(np.eye(N) - mip["A"], f)
    va = mip["coef_va"] * x
    rem = mip["coef_rem"] * x
    occ = mip["coef_occ"] * x
    return {"x": x, "va": va, "rem": rem, "occ": occ}


def fatia(vetor: np.ndarray, uf: int | None) -> float:
    if uf is None:
        return float(vetor.sum())
    return float(vetor[uf * N_AT:(uf + 1) * N_AT].sum())


def para_2025(valor_mi_2018: float, phi: float) -> float:
    return valor_mi_2018 * 1e6 / phi


def diagnostico_mai(path: Path) -> dict:
    """A MAI reparte investimento. A coluna do fumo no RS não é a parcela local."""
    from python_calamine import CalamineWorkbook

    data = CalamineWorkbook.from_path(str(path)).get_sheet_by_name("Sheet1").to_python()
    hdr = data[0]
    col = hdr.index("RS_1200")
    total = 0.0
    por_setor: dict[str, float] = {}
    por_uf: dict[str, float] = {}
    nomes = {}
    for row in data[1:]:
        v = row[col]
        if not isinstance(v, (int, float)) or v == 0:
            continue
        total += float(v)
        sec = str(row[1])
        por_setor[sec] = por_setor.get(sec, 0.0) + float(v)
        uf = str(row[0])
        por_uf[uf] = por_uf.get(uf, 0.0) + float(v)
        nomes[sec] = str(row[2])
    ordem = sorted(por_setor, key=lambda s: -abs(por_setor[s]))
    return {
        "coluna": "RS_1200",
        "descricao": "Fabricação de produtos do fumo, absorção de investimento, RS",
        "total_mi_2018": total,
        "participacao_construcao_4180": por_setor.get("4180", 0.0) / total,
        "participacao_maquinas_2800": por_setor.get("2800", 0.0) / total,
        "participacao_veiculos_2991": por_setor.get("2991", 0.0) / total,
        "participacao_manutencao_3300": por_setor.get("3300", 0.0) / total,
        "participacao_engenharia_7180": por_setor.get("7180", 0.0) / total,
        "participacao_resto_do_mundo": por_uf.get("RM", 0.0) / total,
        "top_setores": [
            {"codigo": s, "nome": nomes.get(s, ""), "participacao": por_setor[s] / total}
            for s in ordem[:8]
        ],
        "decisao": (
            "A coluna de investimento do fumo no RS é uma receita geral de FBCF: "
            "máquinas mecânicas e veículos somam mais da metade, construção fica "
            "em cerca de 10%, e há origem 'resto do mundo'. A parcela local já "
            "estimada (R$ 484 mi) é obra civil, montagem e engenharia, com a "
            "máquina importada fora. A MAI não reparte esse pedaço. A obra "
            "permanece o número já calculado na MIP-RS 2019, bloco 2026–2027, "
            "sem somar a 2037."
        ),
    }


def bloco(va, rem, occ, phi: float, uf: int | None) -> dict:
    return {
        "va_2025": para_2025(fatia(va, uf), phi),
        "rem_2025": para_2025(fatia(rem, uf), phi),
        "ocupacoes": fatia(occ, uf),
        "producao_2025": None,
    }


def figuras(saida: dict, phi: float) -> None:
    _font()
    FIGURAS.mkdir(parents=True, exist_ok=True)
    ind = saida["indireto_rs"]
    resto = saida["indireto_resto"]
    indu = saida["induzido_rs"]
    # Figura 1 — gavetas do tipo I e a camada induzida à parte.
    fig, ax = plt.subplots(figsize=(9.2, 5.2), dpi=160)
    labels = [
        "Direto\nda planta",
        "Indireto\nno RS",
        "Indireto\nno resto\ndo Brasil",
        "Tipo I\nno RS",
        "Induzido\nno RS\n(à parte)",
    ]
    vals = [
        VA_DIRETO / 1e9,
        ind["va_2025"] / 1e9,
        resto["va_2025"] / 1e9,
        saida["tipo_I_rs"]["va_2025"] / 1e9,
        indu["va_2025"] / 1e9,
    ]
    cores = [NAVY, TEAL, SAND, NAVY, "#8AA0A8"]
    bars = ax.bar(labels, vals, color=cores, width=0.72)
    ax.set_ylabel("R$ bilhões de 2025")
    ax.set_title("MIP Ipea, 2037 — tipo I e a camada induzida, que não entra na soma")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.08, f"{v:.2f}".replace(".", ","), ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_ylim(0, max(vals) * 1.18)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig1_valor_adicionado.png", facecolor="white")
    plt.close(fig)

    # Figura 2 — atividades do indireto no RS.
    top = saida["top_atividades_rs"][:8]
    fig, ax = plt.subplots(figsize=(9.2, 5.4), dpi=160)
    nomes = [t["nome"].split(",")[0][:42] for t in top][::-1]
    valores = [t["va_2025"] / 1e6 for t in top][::-1]
    ax.barh(nomes, valores, color=TEAL)
    ax.set_xlabel("R$ milhões de 2025")
    ax.set_title("Indireto no RS por atividade — MIP Ipea, tipo I")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig2_cadeia_por_atividade.png", facecolor="white")
    plt.close(fig)

    # Figura 3 — conteúdo local que a NF-e implicou, por grande linha.
    grupos = saida["conteudo_local_grupos"]
    fig, ax = plt.subplots(figsize=(9.2, 5.4), dpi=160)
    nomes = [g["grupo"] for g in grupos]
    rs = [100 * g["participacao_rs"] for g in grupos]
    cores = [TEAL if g["grupo"] != "Folha" else NAVY for g in grupos]
    ax.barh(nomes[::-1], rs[::-1], color=cores[::-1])
    ax.axvline(10, color=SAND, lw=1, ls="--")
    ax.axvline(20, color=SAND, lw=1, ls="--")
    ax.set_xlabel("Parcela produzida no RS, %")
    ax.set_title("Origem no RS pela oferta da NF-e ao consumo intermediário gaúcho")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig3_faixa_e_exportacao.png", facecolor="white")
    plt.close(fig)

    # Figura 4 — Ipea tipo I no RS ao lado do bloco II e da coluna MIP-RS.
    fig, ax = plt.subplots(figsize=(9.2, 5.2), dpi=160)
    labels = [
        "Direto\nIpea",
        "Tipo I RS\nIpea",
        "Tipo I RS\n+ induzido\nIpea",
        "Tipo II\nMIP-RS\n(checagem)",
        "Bloco II\ndo contratante",
    ]
    vals = [
        VA_DIRETO / 1e9,
        saida["tipo_I_rs"]["va_2025"] / 1e9,
        (saida["tipo_I_rs"]["va_2025"] + indu["va_2025"]) / 1e9,
        MIP_RS["va_tipo_II"] / 1e9,
        8.85,
    ]
    cores = [NAVY, TEAL, "#8AA0A8", SAND, "#7A4E2D"]
    bars = ax.bar(labels, vals, color=cores, width=0.72)
    ax.set_ylabel("R$ bilhões de 2025")
    ax.set_title("Mesma planta, leituras que não se somam")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.08, f"{v:.2f}".replace(".", ","), ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, max(vals) * 1.18)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig4_comparacao_bloco_ii.png", facecolor="white")
    plt.close(fig)

    # Figura 5 — ocupações.
    fig, ax = plt.subplots(figsize=(9.2, 5.2), dpi=160)
    labels = ["Direto\nna planta", "Indireto\nno RS", "Indireto\nno resto\ndo Brasil", "Induzido\nno RS\n(à parte)"]
    vals = [
        OCC_DIRETO / 1000,
        ind["ocupacoes"] / 1000,
        resto["ocupacoes"] / 1000,
        indu["ocupacoes"] / 1000,
    ]
    cores = [NAVY, TEAL, SAND, "#8AA0A8"]
    bars = ax.bar(labels, vals, color=cores, width=0.72)
    ax.set_ylabel("Mil ocupações")
    ax.set_title("Ocupações, 2037 — direto da planta uma vez; indireto pelo fator trabalho da MIP")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.15, f"{v:.1f}".replace(".", ","), ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, max(vals) * 1.2)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig5_ocupacoes.png", facecolor="white")
    plt.close(fig)


def escrever_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    try:
        import python_calamine  # noqa: F401
    except ImportError:
        subprocess.check_call(["pip", "install", "python-calamine", "-q"])

    precos = ipca()
    phi = precos["phi"]
    caminhos = garantir_release()
    mip = carregar_mip(caminhos["mip"])
    from python_calamine import CalamineWorkbook

    tru = CalamineWorkbook.from_path(str(caminhos["tru"]))
    usos = tru.get_sheet_by_name("Usos").to_python()
    recursos = tru.get_sheet_by_name("Recursos").to_python()

    antigo = json.loads((RESULTADOS / "resultados.json").read_text(encoding="utf-8"))
    linhas = antigo["base"]["compras"]["linhas"]
    choque = montar_choque(usos, recursos, phi, linhas)
    for linha in choque["por_linha"]:
        linha["atividade"] = mip["atividades"][linha["atividade_indice"]]

    f = choque["f"]
    # A receita não entra. A atividade do fumo não recebe o VBP.
    fumo = float(f[I_RS * N_AT + 11] + f[I_PR * N_AT + 11] + f[I_SC * N_AT + 11])
    prop = propagar(mip, f)
    x, va, rem, occ = prop["x"], prop["va"], prop["rem"], prop["occ"]

    indireto_rs = {
        "va_2025": para_2025(fatia(va, I_RS), phi),
        "rem_2025": para_2025(fatia(rem, I_RS), phi),
        "ocupacoes": fatia(occ, I_RS),
        "producao_2025": para_2025(fatia(x, I_RS), phi),
    }
    indireto_resto = {
        "va_2025": para_2025(fatia(va, None) - fatia(va, I_RS), phi),
        "rem_2025": para_2025(fatia(rem, None) - fatia(rem, I_RS), phi),
        "ocupacoes": fatia(occ, None) - fatia(occ, I_RS),
        "producao_2025": para_2025(fatia(x, None) - fatia(x, I_RS), phi),
    }
    tipo_I = {
        "va_2025": VA_DIRETO + indireto_rs["va_2025"],
        "rem_2025": REM_DIRETO + indireto_rs["rem_2025"],
        "ocupacoes": OCC_DIRETO + indireto_rs["ocupacoes"],
    }

    # Induzido: uma rodada, 60% da massa salarial gerada no RS, só a oferta gaúcha.
    massa = REM_DIRETO + indireto_rs["rem_2025"]
    consumo = PROPENSAO * massa
    f_ind = mip["share_consumo_rs"] * (consumo * phi / 1e6)
    pind = propagar(mip, f_ind)
    induzido_rs = {
        "consumo_2025": consumo,
        "massa_salarial_rs_2025": massa,
        "va_2025": para_2025(fatia(pind["va"], I_RS), phi),
        "rem_2025": para_2025(fatia(pind["rem"], I_RS), phi),
        "ocupacoes": fatia(pind["occ"], I_RS),
        "producao_2025": para_2025(fatia(pind["x"], I_RS), phi),
        "va_fora_do_rs_2025": para_2025(fatia(pind["va"], None) - fatia(pind["va"], I_RS), phi),
        "nota": (
            "Uma rodada. 60% da massa salarial gerada no RS (direto da planta "
            "mais remuneração indireta que cai no RS) vira consumo no perfil "
            "da oferta gaúcha às famílias do RS. O valor adicionado induzido "
            "da manchete é o que cai no RS. O pedaço que a rodada gera fora "
            "do RS fica registrado e fora da manchete."
        ),
    }

    # Atividades no RS.
    at_rows = []
    for k, nome in enumerate(mip["atividades"]):
        i0 = I_RS * N_AT + k
        at_rows.append({
            "indice": k,
            "codigo": f"A{k:02d}",
            "nome": nome,
            "grupo_espacial": GRUPO_ESPACIAL[k],
            "va_2025": para_2025(float(va[i0]), phi),
            "rem_2025": para_2025(float(rem[i0]), phi),
            "ocupacoes": float(occ[i0]),
            "producao_2025": para_2025(float(x[i0]), phi),
            "choque_2025": para_2025(float(f[i0]), phi),
        })
    top = sorted(at_rows, key=lambda r: -r["va_2025"])

    uf_rows = []
    for u, sigla in enumerate(UFS):
        sl = slice(u * N_AT, (u + 1) * N_AT)
        uf_rows.append({
            "uf": sigla,
            "choque_2025": para_2025(float(f[sl].sum()), phi),
            "producao_2025": para_2025(float(x[sl].sum()), phi),
            "va_2025": para_2025(float(va[sl].sum()), phi),
            "rem_2025": para_2025(float(rem[sl].sum()), phi),
            "ocupacoes": float(occ[sl].sum()),
        })

    nao_folha = choque["bom_linhas"]
    rs_nao_folha = sum(L["valor_rs_2025"] for L in choque["por_linha"])
    grupos = []
    for nome, g in choque["grupos"].items():
        grupos.append({
            "grupo": nome,
            "valor_2025": g["valor"],
            "valor_rs_2025": g["rs"],
            "participacao_rs": g["rs"] / g["valor"] if g["valor"] else 0.0,
        })

    diff_ind = indireto_rs["va_2025"] - MIP_RS["va_cadeia"]
    diff_pct = diff_ind / MIP_RS["va_cadeia"]
    dentro_banda = 0.10 <= abs(diff_pct) <= 0.20

    conteudo_nao_folha = rs_nao_folha / nao_folha
    mai = diagnostico_mai(caminhos["mai"])

    saida = {
        "matriz": {
            "nome": "MIP inter-regional Ipea–Receita Federal",
            "ano_base": 2018,
            "dimensao": "27 UFs × 68 atividades",
            "release": "https://github.com/provictorludwig/mip-dados/releases/tag/v1",
            "unidade_matriz": "R$ milhões de 2018",
            "tipo": "I — consumo das famílias fora de A",
            "chave_origem": (
                "TRU Usos, oferta de cada produto ao consumo intermediário do RS, "
                "por UF de origem. Não é a produção nacional sem destino e não é "
                "a coluna de uma atividade compradora. A matriz de recursos reparte "
                "o produto entre as atividades produtoras da UF de origem."
            ),
            "erro_linha_mi": mip["erro_linha_mi"],
            "erro_coluna_mi": mip["erro_coluna_mi"],
            "erro_leontief_abs_mi": mip["erro_leontief_abs_mi"],
            "erro_leontief_rel": mip["erro_leontief_rel"],
            "max_soma_coluna_A": mip["max_soma_coluna_A"],
            "n_colunas_x_zero": mip["n_colunas_x_zero"],
            "producao_total_mi_2018": mip["producao_total_mi"],
            "conferencia": (
                "Antes do choque, (I−A)⁻¹ vezes a demanda final doméstica reproduz "
                "o valor da produção de cada coluna. O erro relativo máximo está "
                "no json."
            ),
        },
        "precos": precos,
        "direto": {
            "vbp": VBP,
            "va": VA_DIRETO,
            "ocupacoes": OCC_DIRETO,
            "remuneracoes": REM_DIRETO,
            "bom": BOM,
            "onde": "Santa Cruz do Sul, uma vez. Fora do vetor f.",
        },
        "folha": {
            "total": LEAF_TOTAL,
            "rs": LEAF_RS,
            "sc": choque["folha_sc"],
            "pr": choque["folha_pr"],
            "toneladas_rs": LEAF_TON_RS,
            "regra": "RS na âncora de R$ 52,8 mi. SC e PR repartem os R$ 61,4 mi restantes em 29:25.",
        },
        "choque": {
            "bom_linhas_nao_folha": nao_folha,
            "rs_nao_folha": rs_nao_folha,
            "conteudo_local_nao_folha": conteudo_nao_folha,
            "rs_total_com_folha": rs_nao_folha + LEAF_RS,
            "soma_f_2025": para_2025(float(f.sum()), phi),
            "fumo_rs_sc_pr_2018_mi": fumo,
            "nota_fumo": "A atividade fabricação de produtos do fumo não recebe a receita. O valor aqui é só o que a matriz de recursos atribui, se atribuir, a algum produto do BOM.",
        },
        "conteudo_local_grupos": grupos,
        "indireto_rs": indireto_rs,
        "indireto_resto": indireto_resto,
        "tipo_I_rs": tipo_I,
        "induzido_rs": induzido_rs,
        "tipo_I_rs_mais_induzido_nao_e_manchete": {
            "va_2025": tipo_I["va_2025"] + induzido_rs["va_2025"],
            "nota": "Soma só para leitura. A manchete principal é o tipo I.",
        },
        "mip_rs_checagem": MIP_RS,
        "comparacao": {
            "indireto_ipea_rs": indireto_rs["va_2025"],
            "cadeia_mip_rs": MIP_RS["va_cadeia"],
            "diferenca": diff_ind,
            "diferenca_pct": diff_pct,
            "banda_10_20": "As premissas tratavam 10% a 20% de conteúdo local como a faixa típica de sensibilidade.",
            "diferenca_dentro_da_banda_10_20": dentro_banda,
            "conteudo_local_nao_folha_nfe": conteudo_nao_folha,
            "conteudo_local_antigo": 0.0985622170007082,
            "conteudo_dentro_da_banda_10_20": 0.10 <= conteudo_nao_folha <= 0.20,
            "frase": (
                "A origem do insumo agora é a NF-e; a abertura do que a planta compra continua estimada."
            ),
        },
        "obra_2026_2027": {
            **OBRA_MIP_RS,
            "origem_do_numero": "MIP-RS 2019 (DEE/SPGG e UFRJ), já calculado. Não foi reestimado na MAI.",
            "mai": mai,
            "nao_soma_com_2037": True,
        },
        "top_atividades_rs": [
            {"nome": r["nome"], "codigo": r["codigo"], "va_2025": r["va_2025"], "ocupacoes": r["ocupacoes"]}
            for r in top[:12]
        ],
    }

    RESULTADOS.mkdir(parents=True, exist_ok=True)
    (RESULTADOS / "ipea_totais.json").write_text(
        json.dumps(saida, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    escrever_csv(RESULTADOS / "ipea_ponte_bom.csv", choque["por_linha"])
    escrever_csv(RESULTADOS / "ipea_origem_uf.csv", choque["origem_rows"])
    escrever_csv(RESULTADOS / "ipea_va_por_uf.csv", uf_rows)
    escrever_csv(RESULTADOS / "ipea_va_rs_atividade.csv", at_rows)
    escrever_csv(
        RESULTADOS / "ipea_grupos_conteudo_local.csv",
        grupos,
    )

    figuras(saida, phi)

    print("phi", round(phi, 6))
    print("erro rel", mip["erro_leontief_rel"], "abs mi", mip["erro_leontief_abs_mi"])
    print("conteudo local nao folha", round(conteudo_nao_folha, 4))
    print("RS nao folha mi", round(rs_nao_folha / 1e6, 3), "com folha", round((rs_nao_folha + LEAF_RS) / 1e6, 3))
    print("soma f bi", round(para_2025(float(f.sum()), phi) / 1e9, 4))
    print("VA direto bi", round(VA_DIRETO / 1e9, 2))
    print("VA indireto RS bi", round(indireto_rs["va_2025"] / 1e9, 4))
    print("VA indireto resto bi", round(indireto_resto["va_2025"] / 1e9, 4))
    print("tipo I RS bi", round(tipo_I["va_2025"] / 1e9, 4))
    print("induzido RS bi", round(induzido_rs["va_2025"] / 1e9, 4))
    print("occ indireto RS", round(indireto_rs["ocupacoes"], 1), "resto", round(indireto_resto["ocupacoes"], 1))
    print("occ induzido", round(induzido_rs["ocupacoes"], 1))
    print("diff pct cadeia", round(100 * diff_pct, 2), "dentro banda", dentro_banda)
    print("fumo f mi 2018", fumo)
    for g in grupos:
        print(f"  {g['grupo']}: RS {100*g['participacao_rs']:.1f}% de {g['valor_2025']/1e6:.1f} mi")


if __name__ == "__main__":
    main()
