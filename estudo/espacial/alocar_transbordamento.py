#!/usr/bin/env python3
"""Regionalização contábil do transbordamento da operação de nicotina sem fumaça.

Reparte, entre os municípios do Rio Grande do Sul, o valor adicionado indireto
e o valor adicionado induzido já calculados na MIP Ipea (tipo I no RS e a
camada induzida separada). Não reestima a matriz e não estima um ρ de
econometria espacial.

O direto da planta fica 100% em Santa Cruz do Sul e fora da escala do mapa.

Fontes espaciais (baixadas para /tmp/espacial_rs, não versionadas):
  malha municipal IBGE 2022 (geobr / IBGE), SIRGAS 2000;
  PAM, SIDRA tabela 1612, fumo em folha, 2025;
  CEMPRE, SIDRA tabela 6450, pessoal ocupado, 2021;
  Censo Demográfico 2022, SIDRA tabela 10329, local de trabalho.

Uso:
  python3 estudo/espacial/alocar_transbordamento.py
"""

from __future__ import annotations

import json
import math
import unicodedata
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from matplotlib import font_manager
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib.patheffects as pe

ROOT = Path("/workspace")
ESP = ROOT / "estudo" / "espacial"
IPEA_JSON = ROOT / "estudo" / "resultados" / "ipea_totais.json"
IPEA_ATV = ROOT / "estudo" / "resultados" / "ipea_va_rs_atividade.csv"
TMP = Path("/tmp/espacial_rs")

# Albers equivalente sobre o elipsoide GRS80 (SIRGAS 2000).
# Uma UTM só não cobre o RS (fusos 21S e 22S). Paralelos padrão no intervalo do estado.
ALBERS = (
    "+proj=aea +lat_0=-30.5 +lat_1=-33 +lat_2=-28 +lon_0=-53 "
    "+x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs"
)

# Parâmetros de referência. A sensibilidade de λ está no relatório.
ALPHA = 0.5
LAMBDA_KM = 100.0       # presença setorial × distância até a sede
LAMBDA_C_KM = 28.0      # pendularidade residencial (deslocamento diário)
LAMBDA_G_KM = 75.0      # consumo induzido a partir da massa salarial da cadeia
DMAX_FORN_KM = 260.0    # fornecedor além disso sai do núcleo e o peso se renormaliza
DMAX_COMUTE_KM = 110.0  # não há deslocamento diário atribuído à sede além disso
DMAX_GRAV_KM = 180.0
SHARE_SERVICO_PEND = 0.50  # metade do serviço da cadeia segue o salário direto

FRACAO_FOLHA_2037 = 0.0086  # premissa: PAM × 0,86% em 2037
TONELADAS_RS_ESTUDO = 3007.0
FOLHA_RS_MI = 52.8

# Estatuto do COREDE Vale do Rio Pardo, art. 3º (coredevrp.org.br). 23 municípios.
COREDE_NOMES = [
    "Arroio do Tigre",
    "Boqueirão do Leão",
    "Candelária",
    "Encruzilhada do Sul",
    "Estrela Velha",
    "General Câmara",
    "Herveiras",
    "Ibarama",
    "Lagoa Bonita do Sul",
    "Mato Leitão",
    "Pantano Grande",
    "Passa Sete",
    "Passo do Sobrado",
    "Rio Pardo",
    "Santa Cruz do Sul",
    "Segredo",
    "Sinimbu",
    "Sobradinho",
    "Tunas",
    "Vale do Sol",
    "Vale Verde",
    "Venâncio Aires",
    "Vera Cruz",
]

CEMPRE_CATS = {
    "div02": "116866",
    "div12": "116960",
    "div16": "117007",
    "div17": "117015",
    "div19": "117039",
    "div20": "117048",
    "div22": "117089",
    "div26": "117159",
    "div27": "117179",
    "secB": "116880",
    "secC": "116910",
    "secD": "117296",
    "secF": "117329",
    "secG": "117363",
    "secH": "117484",
    "secI": "117543",
    "secJ": "117555",
    "secK": "117608",
    "secM": "117673",
    "secN": "117714",
    "total": "117897",
}

GRAY = "#d0d0d0"
BLUES = ["#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#2171b5", "#08306b"]
PISO_MANCHA_MI = 0.05  # abaixo disso o mapa fica cinza; o CSV guarda o valor
# Rótulos com deslocamento em km (leste, norte) para não cair em cima do município.
OFFSETS_KM = {
    "Santa Cruz do Sul": (6, 12),
    "Vera Cruz": (-9, -4),
    "Venâncio Aires": (16, 8),
    "Rio Pardo": (-14, 10),
    "Candelária": (-18, -8),
    "Vale do Sol": (12, 11),
    "Sinimbu": (8, 14),
    "Porto Alegre": (14, -14),
    "Caxias do Sul": (8, 12),
    "Eldorado do Sul": (-22, -8),
    "Guaíba": (10, -16),
    "Canoas": (20, 6),
    "São Leopoldo": (24, 2),
    "Lajeado": (-16, 10),
    "Gravataí": (22, -2),
    "Canguçu": (12, -8),
    "Estrela": (12, 6),
}
OCRE = "#8a5a12"
NAVY = "#0b2545"
INK = "#1a1a1a"

FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def _font_setup() -> None:
    font_manager.fontManager.addfont(FONT_REG)
    font_manager.fontManager.addfont(FONT_BOLD)
    plt.rcParams["font.family"] = "Liberation Sans"
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42


def _norm_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().replace("- rs", "").split())


def _num(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _sidra_series(path: Path) -> dict[int, float]:
    data = json.loads(path.read_text())
    out: dict[int, float] = {}
    for row in data[1:]:
        out[int(row["D1C"])] = _num(row["V"])
    return out


def _download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 500:
        return
    response = requests.get(url, timeout=180)
    response.raise_for_status()
    path.write_bytes(response.content)


def ensure_inputs() -> None:
    """Garante malha, PAM, CEMPRE, população e local de trabalho em /tmp."""
    TMP.mkdir(parents=True, exist_ok=True)
    mesh = TMP / "rs_mun_2022.gpkg"
    if not mesh.exists():
        import geobr

        gdf = geobr.read_municipality(code_muni=43, year=2022)
        gdf.to_file(mesh, driver="GPKG")
    _download(
        "https://apisidra.ibge.gov.br/values/t/1612/n6/in%20n3%2043/v/214/p/2025/c81/2703",
        TMP / "pam_fumo_2025.json",
    )
    _download(
        "https://apisidra.ibge.gov.br/values/t/4709/n6/in%20n3%2043/v/93/p/2022",
        TMP / "pop2022.json",
    )
    _download(
        "https://apisidra.ibge.gov.br/values/t/10329/n6/in%20n3%2043/v/13373/p/2022"
        "/c469/12167,12188,79176/c2/6794/c386/9680/c2087/79177",
        TMP / "censo2022_local_trabalho.json",
    )
    base = (
        "https://apisidra.ibge.gov.br/values/t/6450/n6/in%20n3%2043/v/707/p/2021/c12762/{}"
    )
    for name, cid in CEMPRE_CATS.items():
        _download(base.format(cid), TMP / "cempre" / f"{name}.json")


def load_frame() -> tuple[gpd.GeoDataFrame, np.ndarray, int]:
    gdf = gpd.read_file(TMP / "rs_mun_2022.gpkg")
    gdf["codigo_ibge"] = gdf["code_muni"].astype(int)
    gdf["nome"] = gdf["name_muni"].astype(str)
    gdf = gdf.to_crs(ALBERS).reset_index(drop=True)
    gdf["corede"] = gdf["nome"].map(_norm_name).isin({_norm_name(n) for n in COREDE_NOMES})
    missing = sorted(set(_norm_name(n) for n in COREDE_NOMES) - set(gdf.loc[gdf.corede, "nome"].map(_norm_name)))
    if missing or int(gdf.corede.sum()) != 23:
        raise RuntimeError(f"COREDE incompleto: {missing} n={int(gdf.corede.sum())}")

    pam = _sidra_series(TMP / "pam_fumo_2025.json")
    pop = _sidra_series(TMP / "pop2022.json")
    gdf["pam_t"] = gdf["codigo_ibge"].map(lambda c: pam.get(c, 0.0)).astype(float)
    gdf["pop"] = gdf["codigo_ibge"].map(lambda c: pop.get(c, 0.0)).astype(float)
    if gdf["pop"].sum() <= 0:
        raise RuntimeError("População 2022 não carregou.")

    cempre = {}
    for name in CEMPRE_CATS:
        cempre[name] = _sidra_series(TMP / "cempre" / f"{name}.json")
    for name, series in cempre.items():
        gdf[name] = gdf["codigo_ibge"].map(lambda c, s=series: s.get(c, 0.0)).astype(float)

    # Censo 2022: quem mora no município e trabalha nele, e quem trabalha em outro.
    local: dict[int, float] = {}
    fora: dict[int, float] = {}
    for row in json.loads((TMP / "censo2022_local_trabalho.json").read_text())[1:]:
        code = int(row["D1C"])
        kind = row["D4C"]
        if kind == "12167":
            local[code] = _num(row["V"])
        elif kind == "12188":
            fora[code] = _num(row["V"])
    gdf["trab_local"] = gdf["codigo_ibge"].map(lambda c: local.get(c, 0.0)).astype(float)
    gdf["trab_fora"] = gdf["codigo_ibge"].map(lambda c: fora.get(c, 0.0)).astype(float)

    cent = gdf.geometry.centroid
    xy = np.column_stack([cent.x.to_numpy(), cent.y.to_numpy()])
    diff = xy[:, None, :] - xy[None, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2)) / 1000.0
    idx = int(np.flatnonzero(gdf["nome"].map(_norm_name) == _norm_name("Santa Cruz do Sul"))[0])
    gdf["dist_sede_km"] = dist[idx]
    return gdf, dist, idx


def _kernel(employment: np.ndarray, dist_sede: np.ndarray, lam: float, alpha: float, dmax: float) -> np.ndarray:
    emp = np.maximum(employment.astype(float), 0.0)
    w = np.where((emp > 0) & (dist_sede <= dmax), np.power(emp, alpha) * np.exp(-dist_sede / lam), 0.0)
    total = w.sum()
    if total <= 0:
        raise RuntimeError("Núcleo setorial ficou sem massa. Revise emprego ou λ.")
    return w / total


def _pop_kernel(pop: np.ndarray, dist_sede: np.ndarray, lam: float, alpha: float, dmax: float) -> np.ndarray:
    return _kernel(np.maximum(pop, 0.0), dist_sede, lam, alpha, dmax)


def commuting_shares(
    trab_local: np.ndarray,
    trab_fora: np.ndarray,
    atracao: np.ndarray,
    dist: np.ndarray,
    idx_sede: int,
    lam_c: float,
    dmax_c: float,
) -> tuple[np.ndarray, dict]:
    """Residência de quem trabalha na sede.

    O microdado público do Censo 2022 não traz o município de destino. A parcela
    que mora na sede é a que o próprio Censo conta como ocupada no município de
    residência. A parcela que mora fora é a fração dos que trabalham em outro
    município, repartida por um núcleo gravitacional com destinos concorrentes
    (emprego formal do CEMPRE como atração). Não é um ρ estimado.
    """
    n = len(trab_local)
    atr = np.maximum(atracao.astype(float), 0.0)
    score = atr[None, :] * np.exp(-dist / lam_c)
    np.fill_diagonal(score, 0.0)
    denom = score.sum(axis=1)
    prob = np.zeros(n)
    ok = denom > 0
    prob[ok] = score[ok, idx_sede] / denom[ok]
    inflow = trab_fora * prob
    inflow[idx_sede] = 0.0
    d_sede = dist[idx_sede]
    inflow[d_sede > dmax_c] = 0.0
    workplace = np.zeros(n)
    workplace[idx_sede] = trab_local[idx_sede]
    workplace += inflow
    total = workplace.sum()
    if total <= 0:
        raise RuntimeError("Pendularidade sem massa.")
    shares = workplace / total
    detail = {
        "ocupados_modelo": float(total),
        "moram_na_sede": float(workplace[idx_sede]),
        "share_sede": float(shares[idx_sede]),
        "entrantes": float(inflow.sum()),
    }
    return shares, detail


def gravity_from_mass(
    mass: np.ndarray,
    pop: np.ndarray,
    dist: np.ndarray,
    alpha: float,
    lam_g: float,
    dmax_g: float,
) -> np.ndarray:
    """Consumo em j a partir da massa salarial já alocada em i.

    Peso de j = população^α × exp(−d_ij / λ_g), zerado além do raio, e a soma
    dos destinos fecha em 1. O próprio município de origem entra com d = 0.
    """
    pop_a = np.power(np.maximum(pop.astype(float), 0.0), alpha)
    kernel = np.exp(-dist / lam_g)
    kernel[dist > dmax_g] = 0.0
    pull = kernel.T @ np.maximum(mass.astype(float), 0.0)
    dest = pull * pop_a
    total = dest.sum()
    if total <= 0:
        raise RuntimeError("Núcleo gravitacional do consumo ficou vazio.")
    return dest / total


GRUPOS_ESPACIAIS = [
    "folha", "pecuaria", "madeira", "papel", "refino", "quim", "plast",
    "eletro", "eletrico", "extrativa", "energia", "construcao", "demais_ind",
    "comercio", "transporte", "aloj_alim", "informacao", "financeira",
    "imobiliario", "profissionais", "administrativo", "publico", "sociais",
]


def activity_values(cadeia_reais: float) -> dict[str, float]:
    """VA indireto no RS, por grupo espacial, na escala do total Ipea."""
    frame = pd.read_csv(IPEA_ATV)
    por_grupo = frame.groupby("grupo_espacial")["va_2025"].sum().to_dict()
    total = float(sum(por_grupo.values()))
    if total <= 0:
        raise RuntimeError("VA indireto por atividade da MIP Ipea veio vazio.")
    scale = cadeia_reais / total
    out = {nome: float(por_grupo.get(nome, 0.0)) * scale for nome in GRUPOS_ESPACIAIS}
    if abs(sum(out.values()) - cadeia_reais) > 1.0:
        raise RuntimeError("VA indireto por grupo não fecha com o total Ipea.")
    return out


def allocate(
    gdf: gpd.GeoDataFrame,
    dist: np.ndarray,
    idx: int,
    lam: float,
    alpha: float = ALPHA,
    share_servico_pend: float = SHARE_SERVICO_PEND,
    lam_c: float = LAMBDA_C_KM,
    lam_g: float = LAMBDA_G_KM,
) -> dict:
    ipea = json.loads(IPEA_JSON.read_text())
    va_direto = float(ipea["direto"]["va"])
    va_cadeia = float(ipea["indireto_rs"]["va_2025"])
    va_induzido = float(ipea["induzido_rs"]["va_2025"])
    rem_direto = float(ipea["direto"]["remuneracoes"])
    rem_cadeia = float(ipea["indireto_rs"]["rem_2025"])
    s_dir = rem_direto / (rem_direto + rem_cadeia)
    pot = activity_values(va_cadeia)
    n = len(gdf)
    d_sede = dist[idx]
    pop = gdf["pop"].to_numpy()

    demais_emp = np.maximum(
        gdf["secC"].to_numpy()
        - gdf["div12"].to_numpy()
        - gdf["div16"].to_numpy()
        - gdf["div17"].to_numpy()
        - gdf["div19"].to_numpy()
        - gdf["div20"].to_numpy()
        - gdf["div22"].to_numpy()
        - gdf["div26"].to_numpy()
        - gdf["div27"].to_numpy(),
        0.0,
    )
    madeira_emp = gdf["div16"].to_numpy() + gdf["div02"].to_numpy()

    pi, pend_detail = commuting_shares(
        gdf["trab_local"].to_numpy(),
        gdf["trab_fora"].to_numpy(),
        gdf["total"].to_numpy(),
        dist,
        idx,
        lam_c,
        DMAX_COMUTE_KM,
    )
    k_papel = _kernel(gdf["div17"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_quim = _kernel(gdf["div20"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_eletro = _kernel(gdf["div26"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_madeira = _kernel(madeira_emp, d_sede, lam, alpha, DMAX_FORN_KM)
    k_refino = _kernel(gdf["div19"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_plast = _kernel(gdf["div22"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_eletrico = _kernel(gdf["div27"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_extr = _kernel(gdf["secB"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_energia = _kernel(gdf["secD"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_constr = _kernel(gdf["secF"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_demais = _kernel(demais_emp, d_sede, lam, alpha, DMAX_FORN_KM)
    k_pec = _pop_kernel(pop, d_sede, lam, alpha, DMAX_FORN_KM)
    k_com = _kernel(gdf["secG"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_trans = _kernel(gdf["secH"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_aloj = _kernel(gdf["secI"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_info = _kernel(gdf["secJ"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_fin = _kernel(gdf["secK"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_pro = _kernel(gdf["secM"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_adm = _kernel(gdf["secN"].to_numpy(), d_sede, lam, alpha, DMAX_FORN_KM)
    k_pop = k_pec

    def mix(pend_share: float, kernel: np.ndarray) -> np.ndarray:
        return pend_share * pi + (1.0 - pend_share) * kernel

    folha = pot["folha"] * (gdf["pam_t"].to_numpy() / gdf["pam_t"].sum())
    industria = (
        pot["pecuaria"] * k_pec
        + pot["madeira"] * k_madeira
        + pot["papel"] * k_papel
        + pot["refino"] * k_refino
        + pot["quim"] * k_quim
        + pot["plast"] * k_plast
        + pot["eletro"] * k_eletro
        + pot["eletrico"] * k_eletrico
        + pot["extrativa"] * k_extr
        + pot["energia"] * k_energia
        + pot["construcao"] * k_constr
        + pot["demais_ind"] * k_demais
    )
    servicos = (
        pot["comercio"] * mix(share_servico_pend, k_com)
        + pot["transporte"] * mix(share_servico_pend, k_trans)
        + pot["aloj_alim"] * mix(0.70, k_aloj)
        + pot["informacao"] * mix(share_servico_pend, k_info)
        + pot["financeira"] * mix(0.25, k_fin)
        + pot["imobiliario"] * mix(0.60, k_pop)
        + pot["profissionais"] * mix(0.25, k_pro)
        + pot["administrativo"] * mix(0.25, k_adm)
        + pot["publico"] * pi
        + pot["sociais"] * mix(0.70, k_pop)
    )
    cadeia_esp = folha + industria + servicos
    grav = gravity_from_mass(cadeia_esp, pop, dist, alpha, lam_g, DMAX_GRAV_KM)
    induzido = va_induzido * (s_dir * pi + (1.0 - s_dir) * grav)
    trans = folha + industria + servicos + induzido

    # Pó abaixo de R$ 1 não pinta município. A soma volta para o maior, e os
    # componentes acompanham, para a linha municipal continuar fechando.
    folha = folha.copy()
    industria = industria.copy()
    servicos = servicos.copy()
    induzido = induzido.copy()
    trans = trans.copy()
    imax = int(np.argmax(trans))
    dust = trans < 1.0
    for arr in (folha, industria, servicos, induzido, trans):
        moved = float(arr[dust].sum())
        arr[dust] = 0.0
        arr[imax] += moved

    direto = np.zeros(n)
    direto[idx] = va_direto

    gap = (va_cadeia + va_induzido) - float(trans.sum())
    trans[imax] += gap
    induzido[imax] += gap

    return {
        "trans": trans,
        "folha": folha,
        "industria": industria,
        "servicos": servicos,
        "induzido": induzido,
        "direto": direto,
        "pi": pi,
        "pend_detail": pend_detail,
        "s_dir": s_dir,
        "va_direto": va_direto,
        "va_cadeia": va_cadeia,
        "va_induzido": va_induzido,
        "rem_direto": rem_direto,
        "rem_cadeia": rem_cadeia,
        "pot": pot,
        "alpha_local": float(ipea["choque"]["conteudo_local_nao_folha"]),
        "com_exportacao": True,
        "lam": lam,
        "alpha": alpha,
        "share_servico_pend": share_servico_pend,
    }


def _fmt_mi(value_mi: float, decimals: int = 1) -> str:
    sign = "-" if value_mi < 0 else ""
    value = abs(value_mi)
    text = f"{value:,.{decimals}f}"
    text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    return sign + text


def _fmt_rs_mi(value_mi: float) -> str:
    if abs(value_mi) >= 1000:
        return "R$ " + _fmt_mi(value_mi / 1000.0, 2) + " bi"
    return "R$ " + _fmt_mi(value_mi, 0) + " mi"


def readable_breaks(values_mi: np.ndarray) -> list[float]:
    """Quebras fixas, em R$ milhões, para a sede não cair na mesma classe que o fornecedor."""
    top = float(np.max(values_mi))
    schedule = [0.5, 2.0, 6.0, 15.0, 30.0]
    breaks = [b for b in schedule if b < top * 0.5]
    breaks.append(float(math.ceil(top)))
    return breaks


def _colormap(breaks: list[float]) -> tuple[ListedColormap, BoundaryNorm, list[float]]:
    bounds = [0.0, PISO_MANCHA_MI] + list(breaks)
    bounds[-1] = float(bounds[-1]) + 1e-6
    n_colors = len(bounds) - 1
    n_blue = n_colors - 1
    if n_blue == len(BLUES):
        blues = BLUES
    elif n_blue <= 1:
        blues = [BLUES[-1]]
    else:
        pick = [int(round(i * (len(BLUES) - 1) / (n_blue - 1))) for i in range(n_blue)]
        blues = [BLUES[i] for i in pick]
    colors = [GRAY] + blues
    if len(colors) != n_colors:
        raise RuntimeError(f"Escala com {n_colors} classes e {len(colors)} cores.")
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bounds, ncolors=cmap.N, clip=True)
    return cmap, norm, bounds


def _fmt_break(value: float) -> str:
    if value < 1:
        return _fmt_mi(value, 2)
    if value < 10:
        return _fmt_mi(value, 0 if float(value).is_integer() else 1)
    return _fmt_mi(value, 0)


def _class_labels(bounds: list[float]) -> list[str]:
    labels = [f"menos de {_fmt_break(bounds[1])} — sem mancha"]
    uppers = bounds[2:]
    for i, upper in enumerate(uppers):
        lower = bounds[i + 1]
        if i == len(uppers) - 1:
            labels.append(f"mais de {_fmt_break(lower)}")
        else:
            labels.append(f"{_fmt_break(lower)} a {_fmt_break(upper)}")
    return labels


def _add_north_scale(ax, scale_km: int) -> None:
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    dx, dy = x1 - x0, y1 - y0
    px = x0 + 0.045 * dx
    py = y0 + 0.055 * dy
    length = scale_km * 1000.0
    ax.plot([px, px + length], [py, py], color=INK, lw=1.35, solid_capstyle="butt", zorder=7)
    tick = 0.008 * dy
    ax.plot([px, px], [py - tick, py + tick], color=INK, lw=0.9, zorder=7)
    ax.plot([px + length, px + length], [py - tick, py + tick], color=INK, lw=0.9, zorder=7)
    ax.text(
        px + length / 2.0,
        py + 0.012 * dy,
        f"{scale_km} km",
        ha="center",
        va="bottom",
        fontsize=8,
        color=INK,
        zorder=7,
    )
    nx = x0 + 0.055 * dx
    ny = py + 0.055 * dy
    ah = 0.055 * dy
    ax.annotate(
        "",
        xy=(nx, ny + ah),
        xytext=(nx, ny),
        arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.05),
        zorder=7,
    )
    ax.text(nx, ny + ah + 0.008 * dy, "N", ha="center", va="bottom", fontsize=9, fontweight="bold", color=INK, zorder=7)


def _draw_legend(ax, bounds: list[float], colors: list[str], max_mi: float, max_nome: str, auxiliar: bool = False) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.0, 0.985, "R$ milhões de 2025", fontsize=11, fontweight="bold", color=NAVY, va="top", transform=ax.transAxes)
    labels = _class_labels(bounds)
    y = 0.93
    for color, label in zip(colors, labels):
        ax.add_patch(Rectangle((0.0, y - 0.022), 0.12, 0.032, facecolor=color, edgecolor="#4a4a4a", linewidth=0.4, transform=ax.transAxes))
        ax.text(0.17, y - 0.006, label, fontsize=9, color=INK, va="center", transform=ax.transAxes)
        y -= 0.048
    y -= 0.012
    ax.text(0.0, y, f"Máximo: R$ {_fmt_mi(max_mi, 1)} mi", fontsize=9, fontweight="bold", color=INK, va="top", transform=ax.transAxes)
    ax.text(0.0, y - 0.035, max_nome, fontsize=9, color=INK, va="top", transform=ax.transAxes)
    y -= 0.09
    ax.plot([0.0, 0.18], [y, y], color=OCRE, lw=2.2, transform=ax.transAxes, solid_capstyle="butt")
    ax.text(0.22, y, "COREDE Vale do Rio Pardo", fontsize=8.2, color=INK, va="center", transform=ax.transAxes)
    ax.text(0.22, y - 0.032, "23 municípios", fontsize=8, color="#444444", va="center", transform=ax.transAxes)
    y -= 0.08
    if auxiliar:
        titulo = "O que esta peça faz"
        nota = "O direto de R$ 7,83 bi\nentrou na escala, só para\nmostrar o estouro.\nNão use esta figura."
    else:
        titulo = "Fora desta escala"
        nota = "Direto da planta\nR$ 7,83 bilhões\nem Santa Cruz do Sul.\n\nNão entra na cor. Se\nentrasse, o estado\nficaria cinza e só a\nsede ficaria azul."
    ax.text(0.0, y, titulo, fontsize=9, fontweight="bold", color=NAVY, va="top", transform=ax.transAxes)
    ax.text(0.0, y - 0.04, nota, fontsize=8.6, color=INK, va="top", transform=ax.transAxes, linespacing=1.25)


def _style_map(ax) -> None:
    ax.set_axis_off()
    ax.set_aspect("equal")
    ax.set_facecolor("white")


def _paint(ax, gdf: gpd.GeoDataFrame, column: str, cmap, norm, edge_lw: float = 0.28, corede_lw: float = 1.7, sede_lw: float = 1.05) -> None:
    gdf.plot(
        column=column,
        cmap=cmap,
        norm=norm,
        linewidth=edge_lw,
        edgecolor="#5a5a5a",
        ax=ax,
        zorder=1,
    )
    gdf.dissolve().boundary.plot(ax=ax, color="#1c1c1c", linewidth=0.7, zorder=3)
    gdf.loc[gdf.corede].dissolve().boundary.plot(ax=ax, color=OCRE, linewidth=corede_lw, zorder=4)
    sede = gdf.loc[gdf["nome"].map(_norm_name) == _norm_name("Santa Cruz do Sul")]
    sede.boundary.plot(ax=ax, color=NAVY, linewidth=sede_lw, zorder=5)


def _label(ax, gdf: gpd.GeoDataFrame, nomes: list[str], fontsize: float = 7.4) -> None:
    wanted = {_norm_name(n): n for n in nomes}
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    for _, row in gdf.iterrows():
        key = _norm_name(row.nome)
        if key not in wanted:
            continue
        point = row.geometry.representative_point()
        if not (x0 <= point.x <= x1 and y0 <= point.y <= y1):
            continue
        dx, dy = OFFSETS_KM.get(row.nome, (0, 8))
        weight = "bold" if key == _norm_name("Santa Cruz do Sul") else "regular"
        ax.annotate(
            row.nome,
            xy=(point.x, point.y),
            xytext=(point.x + dx * 1000.0, point.y + dy * 1000.0),
            fontsize=fontsize,
            fontweight=weight,
            color=INK,
            ha="center",
            va="center",
            zorder=6,
            arrowprops=dict(arrowstyle="-", color="#555555", lw=0.35, shrinkA=0, shrinkB=2),
            path_effects=[pe.withStroke(linewidth=2.6, foreground="white")],
        )


def render_state(path_png: Path, path_pdf: Path, gdf, column, cmap, norm, bounds, colors, labels) -> None:
    fig = plt.figure(figsize=(16.4, 12.6), dpi=200, facecolor="white")
    grid = fig.add_gridspec(1, 2, width_ratios=[5.6, 1.55], wspace=0.03)
    ax = fig.add_subplot(grid[0, 0])
    ax_leg = fig.add_subplot(grid[0, 1])
    fig.subplots_adjust(left=0.012, right=0.985, top=0.86, bottom=0.045)
    _paint(ax, gdf, column, cmap, norm)
    _style_map(ax)
    _label(ax, gdf, labels, fontsize=7.5)
    _add_north_scale(ax, 100)
    max_idx = int(gdf[column].idxmax())
    _draw_legend(ax_leg, bounds, colors, float(gdf.loc[max_idx, column]), str(gdf.loc[max_idx, "nome"]))
    fig.text(
        0.015, 0.955,
        "Valor adicionado por transbordamento nos municípios do Rio Grande do Sul, 2037",
        fontsize=16, fontweight="bold", color=NAVY, ha="left", va="top",
    )
    fig.text(
        0.015, 0.915,
        "Operação de nicotina sem fumaça em Santa Cruz do Sul. R$ de 2025. O direto da planta não entra nesta escala.",
        fontsize=10.5, color="#333333", ha="left", va="top",
    )
    fig.text(
        0.015, 0.016,
        "Malha IBGE 2022, SIRGAS 2000, Albers equivalente (GRS80).  "
        "MIP Ipea 2018, origem do insumo pela NF-e, abertura estimada do BOM.  "
        f"λ = {int(LAMBDA_KM)} km.  Cinza = menos de R$ 50 mil.  Azul = valor positivo, classes do estado.",
        fontsize=7.3, color="#444444", ha="left", va="bottom",
    )
    fig.savefig(path_png, dpi=200, facecolor="white")
    fig.savefig(path_pdf, facecolor="white")
    plt.close(fig)


def render_zoom(path_png: Path, gdf, column, cmap, norm, bounds, colors) -> None:
    fig = plt.figure(figsize=(12.8, 12.4), dpi=200, facecolor="white")
    grid = fig.add_gridspec(1, 2, width_ratios=[4.4, 1.45], wspace=0.04)
    ax = fig.add_subplot(grid[0, 0])
    ax_leg = fig.add_subplot(grid[0, 1])
    fig.subplots_adjust(left=0.015, right=0.985, top=0.86, bottom=0.05)
    core = gdf.loc[gdf.corede]
    minx, miny, maxx, maxy = core.total_bounds
    pad = 28_000
    _paint(ax, gdf, column, cmap, norm, edge_lw=0.45, corede_lw=2.0, sede_lw=1.45)
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad * 0.55)
    _style_map(ax)
    vale = [
        "Santa Cruz do Sul", "Vera Cruz", "Venâncio Aires", "Rio Pardo",
        "Candelária", "Vale do Sol", "Lajeado", "Sinimbu",
    ]
    _label(ax, gdf, vale, fontsize=8.0)
    _add_north_scale(ax, 30)
    max_idx = int(gdf[column].idxmax())
    _draw_legend(ax_leg, bounds, colors, float(gdf.loc[max_idx, column]), str(gdf.loc[max_idx, "nome"]))
    fig.text(
        0.018, 0.955,
        "Vale do Rio Pardo e entorno — a mesma escala do mapa do estado",
        fontsize=15, fontweight="bold", color=NAVY, ha="left", va="top",
    )
    fig.text(
        0.018, 0.915,
        "As classes não foram reescaladas neste recorte. Santa Cruz do Sul é a sede. O direto da planta continua fora da cor.",
        fontsize=10, color="#333333", ha="left", va="top",
    )
    fig.text(
        0.018, 0.02,
        "Contorno ocre: COREDE Vale do Rio Pardo. Contorno azul-marinho: Santa Cruz do Sul. R$ milhões de 2025.",
        fontsize=8, color="#444444", ha="left",
    )
    fig.savefig(path_png, dpi=200, facecolor="white")
    plt.close(fig)


def render_com_direto(path_png: Path, gdf) -> None:
    """Peça auxiliar: a mesma conta com o direto dentro da escala, para mostrar o estouro."""
    work = gdf.copy()
    work["com_direto"] = work["va_transbordo_mi"] + work["va_direto_mi"]
    # Quebras largas de propósito: tudo que não é a sede cai na classe clara.
    top = float(work["com_direto"].max())
    cmap, norm, bounds = _colormap([500.0, float(math.ceil(top))])
    fig = plt.figure(figsize=(12.2, 10.6), dpi=160, facecolor="white")
    ax = fig.add_axes([0.02, 0.07, 0.72, 0.78])
    ax_leg = fig.add_axes([0.76, 0.18, 0.22, 0.62])
    _paint(ax, work, "com_direto", cmap, norm)
    _style_map(ax)
    _label(ax, work, ["Santa Cruz do Sul"], fontsize=8)
    _add_north_scale(ax, 100)
    colors = [cmap(i) for i in range(cmap.N)]
    max_idx = int(work["com_direto"].idxmax())
    _draw_legend(
        ax_leg, bounds, colors, float(work.loc[max_idx, "com_direto"]),
        str(work.loc[max_idx, "nome"]), auxiliar=True,
    )
    fig.text(
        0.02, 0.955,
        "Peça auxiliar — não é o mapa de transbordamento",
        fontsize=14, fontweight="bold", color=NAVY, ha="left", va="top",
    )
    fig.text(
        0.02, 0.915,
        "O direto de R$ 7,83 bi entrou na escala. O estado fica na classe clara e só Santa Cruz do Sul permanece azul.",
        fontsize=10, color="#333333", ha="left", va="top",
    )
    fig.text(
        0.02, 0.025,
        "Use o mapa de transbordamento. Esta figura só existe para mostrar por que o direto fica de fora.",
        fontsize=8, color="#444444",
    )
    fig.savefig(path_png, dpi=160, facecolor="white")
    plt.close(fig)


def render_prancha(path_pdf: Path, gdf, column, cmap, norm, bounds, colors, total_mi, corede_mi, resto_mi) -> None:
    fig = plt.figure(figsize=(16.54, 11.69), dpi=150, facecolor="white")
    fig.text(
        0.035, 0.955,
        "Valor adicionado por transbordamento no Rio Grande do Sul, 2037",
        fontsize=18, fontweight="bold", color=NAVY, ha="left", va="top",
    )
    fig.text(
        0.035, 0.918,
        "Operação de nicotina sem fumaça em Santa Cruz do Sul   ·   R$ de 2025   ·   o direto da planta não entra na cor",
        fontsize=11, color="#333333", ha="left", va="top",
    )
    ax = fig.add_axes([0.025, 0.07, 0.58, 0.82])
    axz = fig.add_axes([0.615, 0.455, 0.355, 0.445])
    _paint(ax, gdf, column, cmap, norm)
    _style_map(ax)
    estado_labels = [
        "Santa Cruz do Sul", "Vera Cruz", "Venâncio Aires", "Porto Alegre",
        "Caxias do Sul", "Guaíba", "Eldorado do Sul", "Lajeado", "Canguçu", "Canoas",
    ]
    _label(ax, gdf, estado_labels, fontsize=7.0)
    _add_north_scale(ax, 100)

    core = gdf.loc[gdf.corede]
    minx, miny, maxx, maxy = core.total_bounds
    pad = 28_000
    _paint(axz, gdf, column, cmap, norm, edge_lw=0.35, corede_lw=1.6, sede_lw=1.2)
    axz.set_xlim(minx - pad, maxx + pad)
    axz.set_ylim(miny - pad, maxy + pad * 0.45)
    _style_map(axz)
    _label(axz, gdf, ["Santa Cruz do Sul", "Vera Cruz", "Venâncio Aires", "Rio Pardo", "Candelária", "Lajeado"], fontsize=7.2)
    axz.set_title("Vale do Rio Pardo e entorno  ·  mesma escala", fontsize=10, color=NAVY, loc="left", pad=6)

    # Faixa de leitura
    axn = fig.add_axes([0.615, 0.045, 0.355, 0.395])
    axn.set_xlim(0, 1)
    axn.set_ylim(0, 1)
    axn.axis("off")
    axn.text(0.0, 0.98, _fmt_rs_mi(total_mi), fontsize=18, fontweight="bold", color=NAVY, va="top")
    axn.text(0.0, 0.86, "transbordamento no RS   ·   indireto Ipea + induzido", fontsize=8.2, color="#333333", va="top")
    axn.text(0.0, 0.74, _fmt_rs_mi(corede_mi), fontsize=15, fontweight="bold", color=OCRE, va="top")
    pct_c = 100.0 * corede_mi / total_mi
    axn.text(0.0, 0.62, f"no COREDE   ·   {_fmt_mi(pct_c, 1)}%".replace(".", ","), fontsize=8.2, color="#333", va="top")
    axn.text(0.48, 0.74, _fmt_rs_mi(resto_mi), fontsize=15, fontweight="bold", color=NAVY, va="top")
    pct_r = 100.0 * resto_mi / total_mi
    axn.text(0.48, 0.62, f"no resto do RS   ·   {_fmt_mi(pct_r, 1)}%".replace(".", ","), fontsize=8.2, color="#333", va="top")
    axn.text(
        0.0, 0.50,
        "À parte, fora da cor: direto da planta, R$ 7,83 bi, todo em Santa Cruz do Sul.",
        fontsize=8.2, color=INK, va="top",
    )
    axn.text(
        0.0, 0.38,
        "Como ler: cinza é menos de R$ 50 mil. O azul escuro isolado é Santa Cruz\n"
        "do Sul — salário de quem mora na sede e serviço local, não os R$ 7,83 bi.\n"
        "O anel do Vale é mais claro. A mancha metropolitana e da Serra é fornecedor.\n"
        "As classes do zoom são as do mapa do estado.",
        fontsize=8.0, color="#333333", va="top", linespacing=1.28,
    )
    # legenda compacta horizontal sob o título, à direita não cabe; fica uma linha no rodapé do mapa
    fig.text(
        0.035, 0.028,
        "Contorno ocre: COREDE Vale do Rio Pardo (23 municípios).  "
        "Escala: cinza = menos de R$ 50 mil; azul claro a azul escuro = valor positivo, classes do mapa do estado.  "
        f"λ = {int(LAMBDA_KM)} km.  Malha IBGE 2022.",
        fontsize=7.5, color="#444444", ha="left",
    )
    fig.savefig(path_pdf, facecolor="white")
    fig.savefig(TMP / "prancha_preview.png", dpi=120, facecolor="white")
    plt.close(fig)


def build_tables(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    cols = [
        "codigo_ibge", "nome", "va_transbordo_mi", "va_folha_mi", "va_industria_mi",
        "va_servicos_mi", "va_induzido_mi", "va_direto_mi", "folha_pam_t_2025",
        "folha_nova_t_2037", "distancia_km_sede", "corede_vale_do_rio_pardo",
    ]
    out = gdf[cols].copy()
    for col in ["va_transbordo_mi", "va_folha_mi", "va_industria_mi", "va_servicos_mi", "va_induzido_mi", "va_direto_mi"]:
        out[col] = out[col].round(6)
    out["folha_pam_t_2025"] = out["folha_pam_t_2025"].round(1)
    out["folha_nova_t_2037"] = out["folha_nova_t_2037"].round(3)
    out["distancia_km_sede"] = out["distancia_km_sede"].round(1)
    out["corede_vale_do_rio_pardo"] = out["corede_vale_do_rio_pardo"].astype(int)
    return out.sort_values("codigo_ibge")


def regional_summary(gdf: gpd.GeoDataFrame, total: float) -> dict:
    core = gdf.loc[gdf.corede]
    sede = gdf.loc[gdf["nome"].map(_norm_name) == _norm_name("Santa Cruz do Sul")].iloc[0]
    resto = gdf.loc[~gdf.corede]
    def pack(frame):
        return {
            "va_transbordo_mi": float(frame["va_transbordo_mi"].sum()),
            "va_folha_mi": float(frame["va_folha_mi"].sum()),
            "va_industria_mi": float(frame["va_industria_mi"].sum()),
            "va_servicos_mi": float(frame["va_servicos_mi"].sum()),
            "va_induzido_mi": float(frame["va_induzido_mi"].sum()),
            "pct": float(100.0 * frame["va_transbordo_mi"].sum() / total),
        }
    return {
        "corede": pack(core),
        "corede_sem_sede": pack(core.loc[core["nome"] != sede["nome"]]),
        "sede_transbordo": pack(gdf.loc[gdf["nome"] == sede["nome"]]),
        "resto": pack(resto),
        "direto_sede_mi": float(sede["va_direto_mi"]),
    }


def main() -> None:
    _font_setup()
    ensure_inputs()
    gdf, dist, idx = load_frame()
    result = allocate(gdf, dist, idx, LAMBDA_KM)
    n = len(gdf)
    mi = 1_000_000.0
    gdf["va_transbordo_mi"] = result["trans"] / mi
    gdf["va_folha_mi"] = result["folha"] / mi
    gdf["va_industria_mi"] = result["industria"] / mi
    gdf["va_servicos_mi"] = result["servicos"] / mi
    gdf["va_induzido_mi"] = result["induzido"] / mi
    gdf["va_direto_mi"] = result["direto"] / mi
    gdf["folha_pam_t_2025"] = gdf["pam_t"]
    gdf["folha_nova_t_2037"] = gdf["pam_t"] * FRACAO_FOLHA_2037
    gdf["distancia_km_sede"] = gdf["dist_sede_km"]
    gdf["corede_vale_do_rio_pardo"] = gdf["corede"]

    total_mi = float(gdf["va_transbordo_mi"].sum())
    esperado_mi = (result["va_cadeia"] + result["va_induzido"]) / mi
    if abs(total_mi - esperado_mi) > 0.001:
        raise RuntimeError(f"Soma municipal {total_mi} != estadual {esperado_mi}")
    if abs(float(gdf["va_direto_mi"].sum()) - result["va_direto"] / mi) > 0.001:
        raise RuntimeError("Direto não fecha.")
    if int((gdf["va_direto_mi"] > 0).sum()) != 1:
        raise RuntimeError("Direto vazou da sede.")

    table = build_tables(gdf)
    table.to_csv(ESP / "va_por_municipio.csv", index=False, encoding="utf-8-sig")
    corede = table.loc[table.corede_vale_do_rio_pardo == 1].sort_values("va_transbordo_mi", ascending=False)
    corede.to_csv(ESP / "corede_vale.csv", index=False, encoding="utf-8-sig")

    zeros = int((gdf["va_transbordo_mi"] <= 0).sum())
    top = gdf.nlargest(15, "va_transbordo_mi")
    summary = regional_summary(gdf, total_mi)

    # Sensibilidade de λ. α, pendularidade e gravidade ficam nos valores de referência.
    sens = []
    for lam in (80.0, 100.0, 150.0):
        alt = allocate(gdf, dist, idx, lam)
        va = alt["trans"] / mi
        core_share = float(va[gdf.corede.to_numpy()].sum() / va.sum() * 100.0)
        names = gdf["nome"].to_numpy()
        order = np.argsort(-va)[:5]
        sens.append({
            "lambda_km": lam,
            "corede_pct": round(core_share, 2),
            "sede_mi": round(float(va[idx]), 2),
            "top5": [{"nome": str(names[i]), "mi": round(float(va[i]), 2)} for i in order],
        })
    sens_alpha = []
    for alpha in (0.5, 1.0):
        alt = allocate(gdf, dist, idx, LAMBDA_KM, alpha=alpha)
        va = alt["trans"] / mi
        sens_alpha.append({
            "alpha": alpha,
            "corede_pct": round(float(va[gdf.corede.to_numpy()].sum() / va.sum() * 100.0), 2),
            "sede_mi": round(float(va[idx]), 2),
        })

    # Entorno da capital: municípios cujo centróide está a até 40 km de Porto Alegre.
    i_poa = int(np.flatnonzero(gdf["nome"].map(_norm_name) == _norm_name("Porto Alegre"))[0])
    perto_poa = dist[i_poa] <= 40.0
    poa_share = float(gdf.loc[perto_poa, "va_transbordo_mi"].sum() / total_mi * 100.0)

    pend_order = np.argsort(-result["pi"])[:12]
    pendularidade = []
    for i in pend_order:
        pendularidade.append({
            "nome": str(gdf.loc[i, "nome"]),
            "pct": round(float(result["pi"][i] * 100.0), 2),
            "dist_km": round(float(gdf.loc[i, "dist_sede_km"]), 1),
        })

    folha_top = gdf.nlargest(8, "va_folha_mi")[
        ["nome", "va_folha_mi", "folha_pam_t_2025", "folha_nova_t_2037"]
    ]
    tons_regra = float(gdf["folha_nova_t_2037"].sum())
    pop_rs = float(gdf["pop"].sum())
    pop_corede = float(gdf.loc[gdf.corede, "pop"].sum())
    tributo_mi = 480.0
    leitura_populacao = {
        "chave": "população residente do Censo 2022",
        "corede_mi": round(tributo_mi * pop_corede / pop_rs, 2),
        "corede_pct_pop": round(100.0 * pop_corede / pop_rs, 2),
        "resto_mi": round(tributo_mi * (1 - pop_corede / pop_rs), 2),
        "nota": "Leitura do tributo estadual e municipal de R$ 480 mi sobre o consumo do produto no RS. Não é VAF nem cota-parte.",
    }

    breaks = readable_breaks(gdf["va_transbordo_mi"].to_numpy())
    cmap, norm, bounds = _colormap(breaks)
    colors = [cmap(i) for i in range(cmap.N)]
    labels = [
        "Santa Cruz do Sul", "Vera Cruz", "Venâncio Aires", "Porto Alegre",
        "Caxias do Sul", "Guaíba", "Eldorado do Sul", "Lajeado", "Canguçu", "Canoas",
    ]

    render_state(
        ESP / "mapa_transbordamento_rs.png",
        ESP / "mapa_transbordamento_rs.pdf",
        gdf, "va_transbordo_mi", cmap, norm, bounds, colors, labels,
    )
    render_zoom(ESP / "mapa_vale_zoom.png", gdf, "va_transbordo_mi", cmap, norm, bounds, colors)
    render_com_direto(ESP / "mapa_com_direto.png", gdf)
    render_prancha(
        ESP / "prancha_governador.pdf",
        gdf, "va_transbordo_mi", cmap, norm, bounds, colors,
        total_mi, summary["corede"]["va_transbordo_mi"], summary["resto"]["va_transbordo_mi"],
    )

    # Classe do zero tem de ser cinza e não pode conter valor positivo.
    class_id = np.digitize(gdf["va_transbordo_mi"].to_numpy(), bounds[1:-1], right=False)
    n_gray = int((gdf["va_transbordo_mi"] <= 0).sum())
    n_gray_class = int((class_id == 0).sum())

    resumo = {
        "cenario": {
            "fonte": "estudo/resultados/ipea_totais.json — indireto no RS mais induzido no RS",
            "alpha_conteudo_local": result["alpha_local"],
            "com_exportacao": result["com_exportacao"],
            "va_direto": result["va_direto"],
            "va_cadeia": result["va_cadeia"],
            "va_induzido": result["va_induzido"],
            "va_transbordo": result["va_cadeia"] + result["va_induzido"],
            "rem_direto": result["rem_direto"],
            "rem_cadeia": result["rem_cadeia"],
            "s_dir": result["s_dir"],
        },
        "parametros": {
            "alpha": ALPHA,
            "lambda_km": LAMBDA_KM,
            "lambda_c_km": LAMBDA_C_KM,
            "lambda_g_km": LAMBDA_G_KM,
            "dmax_fornecedor_km": DMAX_FORN_KM,
            "dmax_comute_km": DMAX_COMUTE_KM,
            "dmax_gravidade_km": DMAX_GRAV_KM,
            "share_servico_pendular": SHARE_SERVICO_PEND,
            "fracao_folha": FRACAO_FOLHA_2037,
        },
        "fechamento": {
            "soma_municipal_mi": total_mi,
            "esperado_mi": esperado_mi,
            "zeros": zeros,
            "classe_cinza": n_gray_class,
            "pam_t_2025": float(gdf["pam_t"].sum()),
            "folha_nova_t_regra": tons_regra,
            "folha_nova_t_estudo": TONELADAS_RS_ESTUDO,
            "residual_toneladas": tons_regra - TONELADAS_RS_ESTUDO,
            "quebras_mi": breaks,
            "n_municipios": n,
        },
        "blocos_mi": {k: v / mi for k, v in result["pot"].items()},
        "recortes": summary,
        "poa_40km_pct": poa_share,
        "poa_mi": float(gdf.loc[gdf["nome"].map(_norm_name) == _norm_name("Porto Alegre"), "va_transbordo_mi"].sum()),
        "top15": [
            {
                "nome": str(r.nome),
                "mi": float(r.va_transbordo_mi),
                "pct": float(100.0 * r.va_transbordo_mi / total_mi),
                "folha": float(r.va_folha_mi),
                "industria": float(r.va_industria_mi),
                "servicos": float(r.va_servicos_mi),
                "induzido": float(r.va_induzido_mi),
                "corede": bool(r.corede),
                "dist_km": float(r.dist_sede_km),
            }
            for r in top.itertuples()
        ],
        "top_folha": folha_top.to_dict(orient="records"),
        "pendularidade": pendularidade,
        "pend_detail": result["pend_detail"],
        "sensibilidade_lambda": sens,
        "sensibilidade_alpha": sens_alpha,
        "leitura_tributo_480": leitura_populacao,
        "corede_municipios": [
            {
                "nome": str(r.nome),
                "mi": float(r.va_transbordo_mi),
                "folha": float(r.va_folha_mi),
                "industria": float(r.va_industria_mi),
                "servicos": float(r.va_servicos_mi),
                "induzido": float(r.va_induzido_mi),
                "pam_t": float(r.folha_pam_t_2025),
                "folha_t": float(r.folha_nova_t_2037),
            }
            for r in corede.itertuples()
        ],
    }
    texto = json.dumps(resumo, ensure_ascii=False, indent=2)
    (TMP / "resumo.json").write_text(texto, encoding="utf-8")
    (ESP / "resumo_alocacao.json").write_text(texto, encoding="utf-8")
    print(json.dumps({
        "transbordo_mi": round(total_mi, 3),
        "corede_mi": round(summary["corede"]["va_transbordo_mi"], 3),
        "corede_pct": round(summary["corede"]["pct"], 2),
        "corede_sem_sede_mi": round(summary["corede_sem_sede"]["va_transbordo_mi"], 3),
        "sede_transbordo_mi": round(summary["sede_transbordo"]["va_transbordo_mi"], 3),
        "resto_mi": round(summary["resto"]["va_transbordo_mi"], 3),
        "zeros": zeros,
        "classe_cinza": n_gray_class,
        "quebras": breaks,
        "pend_sede_pct": result["pend_detail"]["share_sede"],
        "top5": resumo["top15"][:5],
        "sens": sens,
        "folha_t": round(tons_regra, 2),
        "poa_40_pct": round(poa_share, 2),
    }, ensure_ascii=False, indent=2))
    print("PNG", (ESP / "mapa_transbordamento_rs.png").stat().st_size)
    print("zeros ok", n_gray, "classe cinza", n_gray_class)


if __name__ == "__main__":
    main()
