#!/usr/bin/env python3
"""Monta estudo/planilha_final_opcao2.xlsx.

Motor: MIP Ipea 2018. A MIP-RS 2019 entra como coluna de checagem.
Células amarelas são entrada. Totais, o tipo I, a origem e o
transbordamento municipal são fórmulas. A conferência municipal, em reais, é zero.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "planilha_final_opcao2.xlsx"
IPEA = ROOT / "resultados" / "ipea_totais.json"
ANTIGO = ROOT / "resultados" / "resultados.json"
MUN = ROOT / "espacial" / "va_por_municipio.csv"
ATV = ROOT / "resultados" / "ipea_va_rs_atividade.csv"
UF = ROOT / "resultados" / "ipea_va_por_uf.csv"
PONTE = ROOT / "resultados" / "ipea_ponte_bom.csv"
ORIGEM = ROOT / "resultados" / "ipea_origem_uf.csv"

NAVY = "1B3A4B"
FILL_INPUT = PatternFill("solid", fgColor="FFF8E7")
FILL_HEADER = PatternFill("solid", fgColor="E7EEF0")
FILL_TOTAL = PatternFill("solid", fgColor="F3F6F4")
FONT_TITLE = Font(name="Calibri", size=16, bold=True, color=NAVY)
FONT_H = Font(name="Calibri", size=10, bold=True, color=NAVY)
FONT = Font(name="Calibri", size=10, color="243038")
FONT_NOTE = Font(name="Calibri", size=9, italic=True, color="5C6B73")
FONT_TOTAL = Font(name="Calibri", size=10, bold=True, color=NAVY)
THIN = Border(bottom=Side(style="thin", color="E0DCD3"))
TOP = Border(top=Side(style="thin", color=NAVY))
LEFT = Alignment(vertical="center", wrap_text=True)

FMT1 = "#,##0.0"
FMT3 = "#,##0.000"
FMT6 = "#,##0.000000"
FMTI = "#,##0"
FMT2 = "#,##0.00"
FMTP = "0.0%"
FMTPHI = "0.000000"

SEDE = 4316808


def col(n: int) -> str:
    return get_column_letter(n)


class Sheet:
    def __init__(self, ws, title: str, unit: str, source: str):
        self.ws = ws
        self.title = ws.title
        ws.sheet_view.showGridLines = False
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.oddHeader.right.text = "Opção 2 · MIP Ipea + MIP-RS"
        ws.oddFooter.left.text = "Santa Cruz do Sul · 2037 · R$ de 2025"
        ws.oddFooter.right.text = "Página &P"
        self.r = 1
        self.write(1, title, font=FONT_TITLE)
        ws.row_dimensions[1].height = 24
        self.r = 2
        self.write(1, unit, font=FONT_NOTE)
        self.r = 3
        self.write(1, source, font=FONT_NOTE)
        ws.row_dimensions[2].height = 18
        ws.row_dimensions[3].height = 32
        self.r = 4

    def write(self, c, value, font=FONT, fmt=None, fill=None, align=None, border=None):
        cell = self.ws.cell(self.r, c, value)
        cell.font = font
        cell.alignment = align or LEFT
        if fmt:
            cell.number_format = fmt
        if fill:
            cell.fill = fill
        if border:
            cell.border = border
        return cell

    def input(self, c, value, fmt=None):
        return self.write(c, value, fmt=fmt, fill=FILL_INPUT, border=THIN)

    def formula(self, c, value, fmt=None, total=False):
        font = FONT_TOTAL if total else FONT
        border = TOP if total else None
        fill = FILL_TOTAL if total else None
        return self.write(c, value, font=font, fmt=fmt, fill=fill, border=border)

    def headers(self, labels, freeze=True):
        self.r += 1
        for i, lab in enumerate(labels, 1):
            self.write(i, lab, font=FONT_H, fill=FILL_HEADER, border=THIN)
        self.header_row = self.r
        if freeze and self.ws.freeze_panes is None:
            self.ws.freeze_panes = f"A{self.r + 1}"
            self.ws.print_title_rows = f"{self.r}:{self.r}"
        self.r += 1
        return self.header_row

    def widths(self, pairs):
        for letter, width in pairs.items():
            self.ws.column_dimensions[letter].width = width

    def finish_filter(self, first_col, last_col, last_row):
        self.ws.auto_filter.ref = f"{col(first_col)}{self.header_row}:{col(last_col)}{last_row}"


def mi(valor: float) -> float:
    return valor / 1_000_000.0


def main() -> None:
    ipea = json.loads(IPEA.read_text(encoding="utf-8"))
    antigo = json.loads(ANTIGO.read_text(encoding="utf-8"))
    base = antigo["base"]
    miprs = ipea["mip_rs_checagem"]
    obra = ipea["obra_2026_2027"]
    wb = Workbook()

    # ------------------------------------------------------------------ 00
    ws = wb.active
    ws.title = "00_leia"
    s = Sheet(
        ws,
        "Planilha final auditável — Opção 2, MIP Ipea + MIP-RS",
        "Unidade de trabalho: R$ milhões de 2025, salvo linha que diga o contrário. Ano cheio: 2037.",
        "Motor: MIP inter-regional Ipea–Receita Federal, 2018, 27 UFs × 68 atividades, release v1 (NF-e). A MIP-RS 2019 é coluna de checagem. As duas contas não se somam.",
    )
    s.widths({"A": 36, "B": 88})
    blocos = [
        ("O que é este arquivo", "A conta da operação de nicotina sem fumaça em Santa Cruz do Sul. A matriz que propaga o choque é a MIP Ipea. A MIP-RS 2019 (DEE/SPGG e UFRJ) permanece como ordem de grandeza, com os números já publicados."),
        ("Manchete", "Tipo I da MIP Ipea no RS: direto da planta mais indireto inter-regional que cai no RS. O induzido é uma rodada à parte e não entra nessa soma. O indireto nos outros estados é o vazamento medido."),
        ("O que é dado da revisão 4", "Receita, insumos de R$ 8.000 milhões, valor adicionado direto, 4.060 ocupações, remuneração de R$ 150 mil por ocupação, folha de R$ 114,2 milhões no Sul e R$ 52,8 milhões no RS. Células amarelas."),
        ("O que continua estimativa", "A abertura de produtos do BOM. A origem geográfica deixou de ser o percentual manual e passou a ser a oferta da TRU ao consumo intermediário do RS."),
        ("Fator de preço", "φ = IPCA dez/2018 ÷ IPCA dez/2025, SIDRA 1737. A célula nomeada phi está na aba 01. O coeficiente 0,7186 era 2019 e não entra."),
        ("Obra", "A MAI não casa com a parcela local (máquina importada fora). O número da obra é o da MIP-RS, bloco 2026–2027, e não se soma a 2037."),
        ("Conferência municipal", "A soma dos 497 municípios, com o ajuste de fechamento em Santa Cruz do Sul, iguala o indireto Ipea no RS mais o induzido no RS. A célula de conferência, em reais, é zero."),
        ("O que não somar", "Não some Ipea com MIP-RS. Não some o induzido ao tipo I na manchete. Não some a obra a 2037. Não aplique a coluna do fumo sobre a receita."),
    ]
    s.r = 5
    s.headers(["Bloco", "Texto"])
    for titulo, texto in blocos:
        s.write(1, titulo, font=FONT_H)
        s.write(2, texto)
        s.ws.row_dimensions[s.r].height = 36
        s.r += 1

    # ------------------------------------------------------------------ 01
    ws = wb.create_sheet("01_premissas")
    s = Sheet(
        ws,
        "Premissas da planta — revisão 4, intactas",
        "R$ milhões de 2025, ano cheio 2037, com exportação. A receita não é o choque.",
        "Âncoras da revisão 4 de 18/10/2026. O IPCA é SIDRA 1737, número-índice, dezembro.",
    )
    s.widths({"A": 52, "B": 22, "C": 62})
    s.r = 5
    s.headers(["Item", "Valor", "Papel"])
    linhas_p = [
        ("Receita ex-fábrica", 15830.0, FMT1, "Teto contábil. Fora do vetor."),
        ("Insumos, âncora", 8000.0, FMT1, "Base das compras. O vetor publicado fecha em R$ 7.999,97 milhões."),
        ("Valor adicionado direto", 7830.0, FMT1, "Uma vez, em Santa Cruz do Sul."),
        ("Ocupações diretas", 4060, FMTI, "Estoque de 2037."),
        ("Remuneração por ocupação, R$ ", 150000, FMTI, "Com encargos. Premissa v6."),
        ("Remuneração direta", None, FMT1, "Ocupações × remuneração, em R$ milhões."),
        ("Folha no Sul", 114.2, FMT1, "RS + SC + PR."),
        ("Folha no RS", 52.8, FMT1, "3.007 t. Agricultura do RS."),
        ("Folha em Santa Catarina", None, FMT1, "29/54 do que não é RS."),
        ("Folha no Paraná", None, FMT1, "25/54 do que não é RS."),
        ("Toneladas de folha no RS", 3007, FMT1, "Âncora."),
        ("IPCA dezembro de 2018", 5100.61, FMT2, "SIDRA 1737."),
        ("IPCA dezembro de 2025", 7403.29, FMT2, "SIDRA 1737."),
        ("phi, 2018 sobre 2025", None, FMTPHI, "IPCA 2018 ÷ IPCA 2025."),
        ("Propensão a consumir no RS", 0.60, FMTP, "Uma rodada, só para o induzido."),
    ]
    refs = {}
    for nome, valor, fmt, nota in linhas_p:
        s.write(1, nome)
        if nome == "Remuneração direta":
            s.formula(2, f"=B{refs['Ocupações diretas']}*B{refs['Remuneração por ocupação, R$ ']}/1000000", fmt)
        elif nome == "Folha em Santa Catarina":
            s.formula(2, f"=(B{refs['Folha no Sul']}-B{refs['Folha no RS']})*29/54", fmt)
        elif nome == "Folha no Paraná":
            s.formula(2, f"=(B{refs['Folha no Sul']}-B{refs['Folha no RS']})*25/54", fmt)
        elif nome.startswith("phi"):
            s.formula(2, f"=B{refs['IPCA dezembro de 2018']}/B{refs['IPCA dezembro de 2025']}", fmt)
        else:
            s.input(2, valor, fmt)
        s.write(3, nota)
        refs[nome] = s.r
        s.r += 1
    r_phi = refs["phi, 2018 sobre 2025"]
    r_va = refs["Valor adicionado direto"]
    r_rem = refs["Remuneração direta"]
    r_occ = refs["Ocupações diretas"]
    r_folha_rs = refs["Folha no RS"]
    r_folha_sc = refs["Folha em Santa Catarina"]
    r_folha_pr = refs["Folha no Paraná"]
    wb.defined_names.add(DefinedName(name="phi", attr_text=f"'01_premissas'!$B${r_phi}"))
    wb.defined_names.add(DefinedName(name="va_direto", attr_text=f"'01_premissas'!$B${r_va}"))

    # ------------------------------------------------------------------ 02
    ws = wb.create_sheet("02_bom")
    s = Sheet(
        ws,
        "Abertura estimada dos produtos — reusada",
        "R$ milhões de 2025. O valor da linha entra no vetor. O percentual manual da rodada anterior fica na coluna ao lado e não define a origem.",
        "Fonte: resultados.json, compras do cenário base, linhas já ancoradas. A origem geográfica está na aba 04.",
    )
    s.widths({"A": 46, "B": 14, "C": 18, "D": 16, "E": 18, "F": 55})
    s.r = 5
    s.headers(["Linha", "Família", "Valor (R$ mi)", "Percentual manual RS", "Produto antigo", "Regra antiga, fora do vetor Ipea"])
    first_bom = s.r
    for linha in base["compras"]["linhas"]:
        s.write(1, linha["linha"])
        s.write(2, linha["familia"])
        s.input(3, mi(linha["valor"]), FMT3)
        s.input(4, linha["rs"], FMTP)
        s.write(5, linha["produto"])
        s.write(6, linha["regra"])
        s.r += 1
    last_bom = s.r - 1
    s.write(1, "Insumos que não são folha", font=FONT_TOTAL)
    s.formula(3, f"=SUM(C{first_bom}:C{last_bom})", FMT3, total=True)
    r_nao_folha = s.r
    s.r += 1
    s.write(1, "Folha no Sul", font=FONT_TOTAL)
    s.formula(3, "='01_premissas'!B" + str(refs["Folha no Sul"]), FMT3, total=True)
    s.r += 1
    s.write(1, "Vetor, insumos", font=FONT_TOTAL)
    s.formula(3, f"=C{r_nao_folha}+C{s.r - 1}", FMT3, total=True)
    s.write(6, "Fecha na âncora de 8.000 a menos do resíduo já publicado, cerca de R$ 0,03 milhão.")
    s.finish_filter(1, 6, last_bom)

    # ------------------------------------------------------------------ 03
    ws = wb.create_sheet("03_ponte")
    s = Sheet(
        ws,
        "Ponte do BOM para a atividade Ipea de 68",
        "R$ milhões de 2025. A parcela RS é a oferta gaúcha do produto ao consumo intermediário do RS.",
        "Fonte: ipea_ponte_bom.csv. A folha não usa a TRU: vai para a agricultura do RS, de SC e do PR.",
    )
    s.widths({"A": 46, "B": 18, "C": 55, "D": 55, "E": 16, "F": 18, "G": 16})
    s.r = 5
    s.headers(["Linha", "Valor (R$ mi)", "Produto na TRU", "Atividade Ipea", "Parcela RS", "Valor no RS", "Parcela na atividade ponte"])
    first_p = s.r
    for linha in csv.DictReader(PONTE.open(encoding="utf-8")):
        s.write(1, linha["linha"])
        s.input(2, mi(float(linha["valor_2025"])), FMT3)
        s.write(3, linha["produto_tru"])
        s.write(4, linha["atividade"])
        s.input(5, float(linha["participacao_rs"]), FMTP)
        s.formula(6, f"=B{s.r}*E{s.r}", FMT3)
        s.input(7, float(linha["parcela_na_atividade_ponte"]), FMTP)
        s.r += 1
    # Folha
    for nome, ref, pct_formula in (
        ("Folha no RS", r_folha_rs, None),
        ("Folha em Santa Catarina", r_folha_sc, None),
        ("Folha no Paraná", r_folha_pr, None),
    ):
        s.write(1, nome)
        s.formula(2, f"='01_premissas'!B{ref}", FMT3)
        s.write(3, "Âncora do estudo, não a TRU")
        s.write(4, "Agricultura, inclusive o apoio à agricultura e a pós-colheita")
        if nome == "Folha no RS":
            s.formula(5, f"=B{s.r}/('01_premissas'!B{refs['Folha no Sul']})", FMTP)
        elif nome.startswith("Folha em"):
            s.formula(5, f"=B{s.r}/('01_premissas'!B{refs['Folha no Sul']})", FMTP)
        s.formula(6, f"=B{s.r}*E{s.r}", FMT3)
        s.input(7, 1, FMTP)
        s.r += 1
    last_p = s.r - 1
    s.write(1, "Soma", font=FONT_TOTAL)
    s.formula(2, f"=SUM(B{first_p}:B{last_p})", FMT3, total=True)
    s.formula(6, f"=SUM(F{first_p}:F{last_p})", FMT3, total=True)
    s.finish_filter(1, 7, last_p)

    # ------------------------------------------------------------------ 04
    ws = wb.create_sheet("04_origem_uf")
    s = Sheet(
        ws,
        "Origem por UF — oferta ao consumo intermediário do RS",
        "R$ milhões de 2025. Cada linha de produto soma 100% das UFs. A conferência, em R$ milhões, é zero quando a soma iguala o valor da ponte.",
        "Chave: TRU Usos, participação de cada UF na oferta do produto às 68 atividades do RS. Folha: âncora, agricultura do RS, de SC e do PR.",
    )
    s.widths({"A": 46, "B": 22, "C": 8, "D": 16, "E": 18, "F": 18})
    s.r = 5
    s.write(1, "Conferência da origem, R$ mi", font=FONT_TOTAL)
    r_conf_origem = s.r
    s.write(3, "Zero se a soma por linha iguala o valor da aba 03.")
    s.r += 1
    s.headers(["Linha", "Grupo", "UF", "Participação", "Valor (R$ mi)", "Valor 2018 (R$ mi)"])
    first_o = s.r
    for linha in csv.DictReader(ORIGEM.open(encoding="utf-8")):
        s.write(1, linha["linha"])
        s.write(2, linha["grupo"])
        s.write(3, linha["uf"])
        s.input(4, float(linha["participacao"]), "0.00%")
        s.input(5, mi(float(linha["valor_2025"])), FMT6)
        s.formula(6, f"=E{s.r}*phi", FMT6)
        s.r += 1
    last_o = s.r - 1
    s.write(1, "Soma do vetor", font=FONT_TOTAL)
    s.formula(5, f"=SUM(E{first_o}:E{last_o})", FMT3, total=True)
    r_soma_o = s.r
    # Conferência contra a soma da ponte (mesmos valores, linha a linha via SOMASE).
    # A ponte tem uma linha por produto; a origem pode repetir o nome.
    s.ws.cell(
        r_conf_origem,
        2,
        f"=ROUND((E{r_soma_o}-'03_ponte'!B{last_p + 1})*1000000,2)",
    )
    s.ws.cell(r_conf_origem, 2).number_format = FMT2
    s.ws.cell(r_conf_origem, 2).font = FONT_TOTAL
    s.ws.cell(r_conf_origem, 2).fill = FILL_TOTAL
    s.finish_filter(1, 6, last_o)

    # ------------------------------------------------------------------ 05 atividades (precisa existir antes do resultado que soma)
    ws = wb.create_sheet("05_indireto_rs_atividade")
    s = Sheet(
        ws,
        "Indireto no RS por atividade — MIP Ipea",
        "R$ milhões de 2025. O total é a soma. Esse total é o indireto que cai no RS.",
        "Coeficiente de valor adicionado, remuneração e fator trabalho da própria MIP, sobre x = (I−A)⁻¹ f.",
    )
    s.widths({"A": 10, "B": 62, "C": 16, "D": 18, "E": 18, "F": 14, "G": 18})
    s.r = 5
    s.headers(["Código", "Atividade", "Grupo espacial", "VA indireto", "Remuneração", "Ocupações", "Produção"])
    first_a = s.r
    for linha in csv.DictReader(ATV.open(encoding="utf-8")):
        s.write(1, linha["codigo"])
        s.write(2, linha["nome"])
        s.write(3, linha["grupo_espacial"])
        s.input(4, mi(float(linha["va_2025"])), FMT6)
        s.input(5, mi(float(linha["rem_2025"])), FMT6)
        s.input(6, float(linha["ocupacoes"]), FMT3)
        s.input(7, mi(float(linha["producao_2025"])), FMT6)
        s.r += 1
    last_a = s.r - 1
    s.write(1, "", font=FONT_TOTAL)
    s.write(2, "Soma, indireto no RS", font=FONT_TOTAL)
    for c, letter, fmt in ((4, "D", FMT6), (5, "E", FMT6), (6, "F", FMT3), (7, "G", FMT6)):
        s.formula(c, f"=SUM({letter}{first_a}:{letter}{last_a})", fmt, total=True)
    r_soma_at = s.r
    s.finish_filter(1, 7, last_a)

    # ------------------------------------------------------------------ 06 UFs
    ws = wb.create_sheet("06_indireto_por_uf")
    s = Sheet(
        ws,
        "Indireto por UF — vazamento medido",
        "R$ milhões de 2025. O resto do Brasil é a soma menos o RS.",
        "Mesma solução x = (I−A)⁻¹ f. O choque é a origem do BOM. O valor adicionado é o coeficiente da MIP.",
    )
    s.widths({"A": 8, "B": 18, "C": 18, "D": 18, "E": 14, "F": 18})
    s.r = 5
    s.headers(["UF", "Choque", "Produção", "VA indireto", "Ocupações", "Remuneração"])
    first_u = s.r
    row_rs = None
    for linha in csv.DictReader(UF.open(encoding="utf-8")):
        s.write(1, linha["uf"])
        s.input(2, mi(float(linha["choque_2025"])), FMT6)
        s.input(3, mi(float(linha["producao_2025"])), FMT6)
        s.input(4, mi(float(linha["va_2025"])), FMT6)
        s.input(5, float(linha["ocupacoes"]), FMT3)
        s.input(6, mi(float(linha["rem_2025"])), FMT6)
        if linha["uf"] == "RS":
            row_rs = s.r
        s.r += 1
    last_u = s.r - 1
    s.write(1, "Brasil", font=FONT_TOTAL)
    for c, letter, fmt in ((2, "B", FMT6), (3, "C", FMT6), (4, "D", FMT6), (5, "E", FMT3), (6, "F", FMT6)):
        s.formula(c, f"=SUM({letter}{first_u}:{letter}{last_u})", fmt, total=True)
    r_br = s.r
    s.r += 1
    s.write(1, "Resto", font=FONT_TOTAL)
    for c, letter, fmt in ((2, "B", FMT6), (3, "C", FMT6), (4, "D", FMT6), (5, "E", FMT3), (6, "F", FMT6)):
        s.formula(c, f"={letter}{r_br}-{letter}{row_rs}", fmt, total=True)
    r_resto = s.r
    s.finish_filter(1, 6, last_u)

    # ------------------------------------------------------------------ 07 resultados
    ws = wb.create_sheet("07_resultados")
    s = Sheet(
        ws,
        "Resultados — MIP Ipea ao lado da MIP-RS",
        "R$ milhões de 2025 e ocupações. O tipo I da coluna Ipea é fórmula. A coluna MIP-RS é a conta já publicada, para checagem. Não some as colunas.",
        "Indireto Ipea: soma das abas 05 e 06. Induzido: uma rodada, 60% da massa salarial gerada no RS, só a oferta gaúcha. MIP-RS: resultados.json, sem recálculo.",
    )
    s.widths({"A": 46, "B": 22, "C": 22, "D": 18, "E": 55})
    s.r = 5
    s.headers(["Leitura", "MIP Ipea", "MIP-RS 2019", "Diferença", "Nota"])

    def linha_res(nome, formula_b, valor_c, fmt, nota, entrada_c=True):
        s.write(1, nome)
        s.formula(2, formula_b, fmt)
        if valor_c is None:
            s.write(3, "—")
        elif entrada_c:
            s.input(3, valor_c, fmt)
        else:
            s.formula(3, valor_c, fmt)
        if valor_c is None:
            s.write(4, "—")
        else:
            s.formula(4, f"=B{s.r}-C{s.r}", fmt)
        s.write(5, nota)
        atual = s.r
        s.r += 1
        return atual

    r_dir = linha_res(
        "Valor adicionado direto",
        f"=va_direto",
        mi(miprs["va_tipo_I"] - miprs["va_cadeia"]),
        FMT3,
        "A mesma planta. Na MIP-RS o direto também é R$ 7.830 milhões.",
    )
    # O direto MIP-RS publicado é 7830. Usar a âncora, não a subtração, para não arrastar arredondamento.
    s.ws.cell(r_dir, 3, "=va_direto")
    s.ws.cell(r_dir, 3).number_format = FMT3
    s.ws.cell(r_dir, 3).font = FONT
    s.ws.cell(r_dir, 3).fill = FILL_TOTAL

    r_ind = linha_res(
        "Indireto no RS / cadeia MIP-RS",
        f"='05_indireto_rs_atividade'!D{r_soma_at}",
        mi(miprs["va_cadeia"]),
        FMT3,
        "Ipea: soma das 68 atividades. MIP-RS: cadeia já publicada, R$ 498,9 milhões.",
    )
    r_resto = linha_res(
        "Indireto no resto do Brasil",
        f"='06_indireto_por_uf'!D{r_resto}",
        None,
        FMT3,
        "Vazamento medido. A MIP-RS registrava a compra fora do RS e não a multiplicava.",
    )
    r_tipo = linha_res(
        "Tipo I no RS",
        f"=B{r_dir}+B{r_ind}",
        f"=C{r_dir}+C{r_ind}",
        FMT3,
        "Manchete Ipea: direto + indireto no RS. A coluna MIP-RS é direto + cadeia.",
        entrada_c=False,
    )
    r_indu = linha_res(
        "Induzido no RS, uma rodada, à parte",
        None,
        mi(miprs["va_induzido"]),
        FMT3,
        "Fora da manchete de tipo I. 60% da massa salarial gerada no RS.",
    )
    # induzido Ipea é saída do modelo: entrada amarela, não fórmula de soma.
    s.ws.cell(r_indu, 2, mi(ipea["induzido_rs"]["va_2025"]))
    s.ws.cell(r_indu, 2).number_format = FMT3
    s.ws.cell(r_indu, 2).font = FONT
    s.ws.cell(r_indu, 2).fill = FILL_INPUT
    s.ws.cell(r_indu, 2).border = THIN

    r_trans = linha_res(
        "Transbordamento no RS (mapa)",
        f"=B{r_ind}+B{r_indu}",
        f"=C{r_ind}+C{r_indu}",
        FMT3,
        "O que o mapa reparte. Não é a manchete de tipo I.",
        entrada_c=False,
    )
    r_tipo2 = linha_res(
        "Direto + indireto no RS + induzido",
        f"=B{r_tipo}+B{r_indu}",
        f"=C{r_tipo}+C{r_indu}",
        FMT3,
        "Leitura auxiliar. A manchete Ipea permanece o tipo I. O tipo II da MIP-RS é esta coluna.",
        entrada_c=False,
    )
    r_occ_i = linha_res(
        "Ocupações do indireto no RS",
        f"='05_indireto_rs_atividade'!F{r_soma_at}",
        miprs["occ_cadeia"],
        FMT1,
        "Fator trabalho da MIP Ipea. MIP-RS: coeficiente da TRU-16.",
    )
    r_occ_d = linha_res(
        "Ocupações diretas",
        f"='01_premissas'!B{r_occ}",
        4060,
        FMTI,
        "Premissa. Uma vez.",
    )
    linha_res(
        "Ocupações do tipo I no RS",
        f"=B{r_occ_d}+B{r_occ_i}",
        f"=C{r_occ_d}+C{r_occ_i}",
        FMT1,
        "Direto + indireto no RS.",
        entrada_c=False,
    )
    s.write(1, "Diferença do indireto no RS")
    s.formula(2, f"=D{r_ind}/C{r_ind}", FMTP)
    s.write(5, "Fora da banda de 10% a 20%. A origem agora é a NF-e.")
    s.r += 1
    s.write(1, "Diferença do tipo I no RS")
    s.formula(2, f"=D{r_tipo}/C{r_tipo}", FMTP)
    s.write(5, "Dentro da banda de 10% a 20%, porque o direto de R$ 7.830 milhões é comum.")
    s.r += 1
    s.write(1, "Conteúdo local dos insumos que não são folha, NF-e")
    s.input(2, ipea["choque"]["conteudo_local_nao_folha"], FMTP)
    s.input(3, ipea["comparacao"]["conteudo_local_antigo"], FMTP)
    s.formula(4, f"=B{s.r}-C{s.r}", FMTP)
    s.write(5, "Coluna Ipea: oferta ao RS. Coluna MIP-RS: percentual manual, 9,9%. 44,7% fica fora da banda de 10% a 20%.")

    wb.defined_names.add(DefinedName(name="va_cadeia", attr_text=f"'07_resultados'!$B${r_ind}"))
    wb.defined_names.add(DefinedName(name="va_induzido", attr_text=f"'07_resultados'!$B${r_indu}"))
    wb.defined_names.add(DefinedName(name="transbordo", attr_text=f"'07_resultados'!$B${r_trans}"))

    # ------------------------------------------------------------------ 08 obra
    ws = wb.create_sheet("08_obra")
    s = Sheet(
        ws,
        "Obra 2026–2027 — número da MIP-RS, fora de 2037",
        "R$ milhões de 2025. Este bloco não entra no ano cheio.",
        "A MAI da fabricação de fumo no RS é receita geral de investimento (máquina 40,4%, veículo 16,0%, construção 10,5%, resto do mundo 38,5%). Não reparte a parcela local já estimada. O efeito permanece o da MIP-RS 2019.",
    )
    s.widths({"A": 52, "B": 18, "C": 62})
    s.r = 5
    s.headers(["Item", "Valor", "Origem"])
    obra_linhas = [
        ("CAPEX total", mi(obra["capex_total"]), "Estimativa calibrada, já publicada."),
        ("Parcela gaúcha", mi(obra["capex_rs"]), "Obra civil, montagem e engenharia."),
        ("Máquinas e serviços importados", mi(obra["capex_importado"]), "Fora do choque."),
        ("Produção gerada no RS", mi(obra["producao_2025"]), "MIP-RS 2019."),
        ("Valor adicionado no RS", mi(obra["va_2025"]), "MIP-RS 2019."),
        ("Remunerações", mi(obra["rem_2025"]), "MIP-RS 2019."),
        ("Ocupações do Leontief", obra["ocupacoes_leontief"], "MIP-RS 2019."),
        ("Postos temporários na construção", obra["postos_temporarios_construcao"], "MIP-RS 2019. Fora das 4.060."),
    ]
    r_iss = None
    for nome, valor, nota in obra_linhas:
        s.write(1, nome)
        fmt = FMT1 if isinstance(valor, float) and valor > 100 else FMT1
        s.input(2, valor, FMT1 if "Ocup" not in nome and "Postos" not in nome else FMT1)
        if "Ocup" in nome or "Postos" in nome:
            s.ws.cell(s.r, 2).number_format = FMT1
        s.write(3, nota)
        s.r += 1
    s.write(1, "ISS em Santa Cruz do Sul")
    s.formula(2, f"=0.02*0.5*B{s.r - 6}", FMT3)
    # B da parcela gaúcha é a segunda linha de dados. Recalcular de forma estável.
    # As linhas começam em header+1. Parcela gaúcha é a segunda.
    # Vou apontar para a célula já escrita: header está em 6, dados a partir de 7.
    s.ws.cell(s.r, 2, "=0.02*0.5*B8")
    s.ws.cell(s.r, 2).number_format = FMT3
    s.ws.cell(s.r, 2).font = FONT_TOTAL
    s.ws.cell(s.r, 2).fill = FILL_TOTAL
    s.write(3, "2% sobre metade da parcela local. Uma vez, no biênio. Fora de 2037.")
    r_iss = s.r

    # ------------------------------------------------------------------ 09 fiscal
    ws = wb.create_sheet("09_fiscal")
    s = Sheet(
        ws,
        "Fiscal de referência — premissas, hipótese FUNDOPEM",
        "R$ milhões de 2025. Hipótese de cálculo, não incentivo concedido.",
        "Revisão 4 e Lei 15.642/2021. O desenho de 30% por 96 meses, sem INTEGRAR, permanece.",
    )
    s.widths({"A": 52, "B": 18, "C": 55})
    s.r = 5
    s.headers(["Canal", "Valor", "Nota"])
    fiscais = [
        ("Tributos sobre o consumo no Brasil", 13700, "Memória da revisão 4."),
        ("Dos quais federais", 6580, ""),
        ("Tributos sobre o consumo no RS", 928, "Cerca de 6,8% do nacional."),
        ("ICMS estadual e municipal no RS", 480, "Base da hipótese."),
        ("Cota-parte municipal, 25%", None, "Fórmula."),
        ("ICMS estadual líquido da cota", None, "Fórmula."),
        ("IRPJ/CSLL da planta", 1227.57, "34% sobre 50% do excedente, com exportação."),
        ("Diferimento, 30% de 96 meses", None, "Hipótese. Não é renúncia permanente."),
        ("Líquido no ano de fruição", None, "Bruto municipal e estadual menos o diferimento."),
        ("ISS da obra", None, "Aba 08. Fora de 2037."),
    ]
    primeiro = s.r
    for nome, valor, nota in fiscais:
        s.write(1, nome)
        s.write(3, nota)
        s.r += 1
    # rows: primeiro is ICMS? let's assign by order
    # 0 consumo brasil, 1 federal, 2 consumo rs, 3 icms 480, 4 cota, 5 liquido, 6 irpj, 7 dif, 8 liq, 9 iss
    base_row = primeiro
    for i, (nome, valor, nota) in enumerate(fiscais):
        rr = base_row + i
        if valor is not None:
            cell = ws.cell(rr, 2, valor)
            cell.number_format = FMT1
            cell.fill = FILL_INPUT
            cell.font = FONT
            cell.border = THIN
    # formulas
    ws.cell(base_row + 4, 2, f"=B{base_row + 3}*0.25")
    ws.cell(base_row + 5, 2, f"=B{base_row + 3}-B{base_row + 4}")
    ws.cell(base_row + 7, 2, f"=B{base_row + 3}*0.30")
    ws.cell(base_row + 8, 2, f"=B{base_row + 3}-B{base_row + 7}")
    ws.cell(base_row + 9, 2, f"='08_obra'!B{r_iss}")
    for rr in range(base_row + 4, base_row + 10):
        ws.cell(rr, 2).number_format = FMT1
        ws.cell(rr, 2).font = FONT_TOTAL if rr in (base_row + 5, base_row + 8) else FONT
        ws.cell(rr, 2).fill = FILL_TOTAL

    # ------------------------------------------------------------------ 10 municípios
    ws = wb.create_sheet("10_municipios")
    s = Sheet(
        ws,
        "Transbordamento por município",
        "R$ milhões de 2025. Transbordamento = folha + indústria + serviços + induzido. O direto fica em coluna própria e fora da cor.",
        "Fonte: va_por_municipio.csv, indireto Ipea no RS mais induzido. O ajuste de fechamento volta a Santa Cruz do Sul. A conferência, em reais, é zero.",
    )
    s.widths({
        "A": 14, "B": 28, "C": 16, "D": 16, "E": 16, "F": 16, "G": 18,
        "H": 16, "I": 12, "J": 16, "K": 16, "L": 14,
        "N": 16, "O": 16, "P": 16, "Q": 16,
    })
    municipios = list(csv.DictReader(MUN.open(encoding="utf-8-sig")))
    if len(municipios) != 497:
        raise SystemExit(f"Municípios: {len(municipios)}")
    s.r = 5
    s.write(1, "Ajuste da cadeia, R$ mi", font=FONT_TOTAL)
    r_aj_cad = s.r
    s.write(3, "Volta para serviços de Santa Cruz do Sul.")
    s.r += 1
    s.write(1, "Ajuste do induzido, R$ mi", font=FONT_TOTAL)
    r_aj_ind = s.r
    s.write(3, "Volta para o induzido de Santa Cruz do Sul.")
    s.r += 1
    s.write(1, "Conferência municipal, R$", font=FONT_TOTAL)
    r_conf_mun = s.r
    s.write(3, "Zero se a soma dos 497 municípios iguala o indireto Ipea no RS mais o induzido.")
    s.r += 1
    s.headers([
        "Código IBGE", "Município", "Folha (R$ mi)", "Indústria (R$ mi)", "Serviços (R$ mi)",
        "Induzido (R$ mi)", "Transbordamento (R$ mi)", "VA direto (R$ mi)", "COREDE",
        "PAM 2025 (t)", "Compra nova 2037 (t)", "Distância à sede (km)",
    ])
    for i, lab in enumerate(["Folha CSV", "Indústria CSV", "Serviços CSV", "Induzido CSV"], 14):
        cell = ws.cell(s.header_row, i, lab)
        cell.font = FONT_H
        cell.fill = FILL_HEADER
    first_m = s.r
    sede_row = None
    for linha in municipios:
        codigo = int(linha["codigo_ibge"])
        s.write(1, codigo, fmt="0")
        s.write(2, linha["nome"])
        s.input(14, float(linha["va_folha_mi"]), FMT6)
        s.input(15, float(linha["va_industria_mi"]), FMT6)
        s.input(16, float(linha["va_servicos_mi"]), FMT6)
        s.input(17, float(linha["va_induzido_mi"]), FMT6)
        s.formula(3, f"=N{s.r}", FMT6)
        s.formula(4, f"=O{s.r}", FMT6)
        if codigo == SEDE:
            s.formula(5, f"=P{s.r}+$B${r_aj_cad}", FMT6)
            s.formula(6, f"=Q{s.r}+$B${r_aj_ind}", FMT6)
            sede_row = s.r
        else:
            s.formula(5, f"=P{s.r}", FMT6)
            s.formula(6, f"=Q{s.r}", FMT6)
        s.formula(7, f"=C{s.r}+D{s.r}+E{s.r}+F{s.r}", FMT6)
        s.input(8, float(linha["va_direto_mi"]), FMT1)
        s.input(9, int(linha["corede_vale_do_rio_pardo"]), "0")
        s.input(10, float(linha["folha_pam_t_2025"]), FMT1)
        s.input(11, float(linha["folha_nova_t_2037"]), FMT3)
        s.input(12, float(linha["distancia_km_sede"]), FMT1)
        s.r += 1
    last_m = s.r - 1
    if sede_row is None:
        raise SystemExit("Santa Cruz do Sul não está na malha.")
    s.write(2, "TOTAL", font=FONT_TOTAL)
    for c, letter in ((3, "C"), (4, "D"), (5, "E"), (6, "F"), (7, "G"), (8, "H")):
        s.formula(c, f"=SUM({letter}{first_m}:{letter}{last_m})", FMT6 if c < 8 else FMT1, total=True)
    r_tot_m = s.r
    ws.cell(r_aj_cad, 2, f"=va_cadeia-SUM(N{first_m}:P{last_m})")
    ws.cell(r_aj_cad, 2).number_format = FMT6
    ws.cell(r_aj_cad, 2).font = FONT_TOTAL
    ws.cell(r_aj_ind, 2, f"=va_induzido-SUM(Q{first_m}:Q{last_m})")
    ws.cell(r_aj_ind, 2).number_format = FMT6
    ws.cell(r_aj_ind, 2).font = FONT_TOTAL
    ws.cell(r_conf_mun, 2, f"=ROUND((G{r_tot_m}-va_cadeia-va_induzido)*1000000,2)")
    ws.cell(r_conf_mun, 2).number_format = FMT2
    ws.cell(r_conf_mun, 2).font = FONT_TOTAL
    ws.cell(r_conf_mun, 2).fill = FILL_TOTAL
    s.finish_filter(1, 12, last_m)
    wb.defined_names.add(DefinedName(name="conf_municipal_reais", attr_text=f"'10_municipios'!$B${r_conf_mun}"))

    # ------------------------------------------------------------------ 11 corede
    ws = wb.create_sheet("11_corede")
    s = Sheet(
        ws,
        "COREDE Vale do Rio Pardo",
        "R$ milhões de 2025. Cada valor é SOMASE do código IBGE na aba 10.",
        "Artigo 3º do estatuto. 23 municípios. Gramado Xavier fica de fora.",
    )
    s.widths({"A": 16, "B": 28, "C": 22, "D": 16, "E": 16, "F": 16, "G": 16})
    s.r = 5
    s.headers(["Código IBGE", "Município", "Transbordamento", "Folha", "Indústria", "Serviços", "Induzido"])
    corede = [m for m in municipios if int(m["corede_vale_do_rio_pardo"]) == 1]
    corede.sort(key=lambda m: -float(m["va_transbordo_mi"]))
    if len(corede) != 23:
        raise SystemExit(f"COREDE: {len(corede)}")
    first_c = s.r
    rng_cod = f"'10_municipios'!$A${first_m}:$A${last_m}"
    for m in corede:
        codigo = int(m["codigo_ibge"])
        s.input(1, codigo, "0")
        s.formula(2, f"=INDEX('10_municipios'!$B${first_m}:$B${last_m},MATCH(A{s.r},{rng_cod},0))")
        for dest, src in ((3, "G"), (4, "C"), (5, "D"), (6, "E"), (7, "F")):
            s.formula(
                dest,
                f"=INDEX('10_municipios'!${src}${first_m}:${src}${last_m},MATCH(A{s.r},{rng_cod},0))",
                FMT3,
            )
        s.r += 1
    last_c = s.r - 1
    s.write(2, "COREDE", font=FONT_TOTAL)
    for c, letter in ((3, "C"), (4, "D"), (5, "E"), (6, "F"), (7, "G")):
        s.formula(c, f"=SUM({letter}{first_c}:{letter}{last_c})", FMT3, total=True)
    r_core = s.r
    s.r += 1
    s.write(1, "Parcela do transbordamento estadual")
    s.formula(3, f"=C{r_core}/transbordo", FMTP)
    s.r += 1
    s.write(1, "Conferência da flag, R$ mi")
    s.formula(
        3,
        f"=SUMIF('10_municipios'!$I${first_m}:$I${last_m},1,'10_municipios'!$G${first_m}:$G${last_m})-C{r_core}",
        FMT6,
    )

    wb.save(OUT)
    print(f"planilha {OUT} bytes {OUT.stat().st_size}")
    print(f"conferência aponta para 10_municipios!B{r_conf_mun}")
    print(f"indireto linha {r_ind} induzido linha {r_indu} transbordo linha {r_trans}")


if __name__ == "__main__":
    main()
