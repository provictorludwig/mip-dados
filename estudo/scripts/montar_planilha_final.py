#!/usr/bin/env python3
"""Monta estudo/planilha_final_opcao2.xlsx a partir dos resultados já fechados.

As células amarelas são entrada (premissa ou saída publicada do modelo).
Totais, o vetor de 2019, o Tipo II, o transbordamento municipal, o COREDE
e os quinze municípios mais azuis são fórmulas.
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
JSON_PATH = ROOT / "resultados" / "resultados.json"
MUN_PATH = ROOT / "espacial" / "va_por_municipio.csv"
ATV_PATH = ROOT / "resultados" / "cadeia_por_atividade.csv"

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
WRAP = Alignment(wrap_text=True, vertical="center")
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


def ref(sheet: str, row: int, c: int) -> str:
    return f"'{sheet}'!${col(c)}${row}"


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
        ws.oddHeader.right.text = "Opção 2 · MIP-RS + Análise espacial"
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


def main() -> None:
    dados = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    base = dados["base"]
    wb = Workbook()

    # ------------------------------------------------------------------ 00
    ws = wb.active
    ws.title = "00_leia"
    s = Sheet(
        ws,
        "Planilha final auditável — Opção 2",
        "Unidade de trabalho: R$ milhões de 2025, salvo linha que diga o contrário. Ano cheio: 2037.",
        "Cenário base: abertura estimada da lista de materiais, conteúdo local não agrícola implícito de 9,9%, com exportação. MIP-RS 2019, 117 × 52.",
    )
    s.widths({"A": 38, "B": 28, "C": 78, "D": 22, "E": 36})
    blocos = [
        ("O que é este arquivo", "A conta da operação de nicotina sem fumaça em Santa Cruz do Sul, com a regionalização do transbordamento. Cada número de manchete sai de uma célula de entrada ou de uma fórmula. A matriz L = (I−A)⁻¹ foi conferida com a tabela 14 no script estudo/scripts/calcular_impacto.py (desvio da ordem de 1e-15). A planilha oficial da MIP não está embutida."),
        ("Cenário base", "Abertura estimada. Conteúdo local dos insumos que não são folha: 9,9%. Exportação incluída. Uma rodada de consumo, propensão 60%. Adicionalidade 100%, premissa de capa da revisão 4."),
        ("O que é dado da revisão 4", "Receita, insumos totais (âncora R$ 8.000 milhões), valor adicionado direto, ocupações diretas, remuneração de R$ 150 mil por ocupação, folha (R$ 114,2 milhões no Sul, R$ 52,8 milhões e 3.007 t no RS), rampa 2028/2032/2037, tributos de memória e o bloco II. Células amarelas."),
        ("O que é estimativa", "A abertura linha a linha dos insumos que não são folha, o conteúdo local de 9,9%, o CAPEX de conversão, a hipótese FUNDOPEM de 30% por 96 meses, a cadeia, o induzido e a regionalização municipal. A regra de cada linha está na aba 02."),
        ("Fator de preço", "φ = IPCA dez/2019 ÷ IPCA dez/2025, SIDRA 1737. A célula nomeada phi fica nesta aba. O vetor de 2019 na aba 03 é a compra de 2025 vezes phi. Ocupação não se deflaciona."),
        ("Obra e mapa", "A obra de 2026–2027 fica na aba 06 e não se soma a 2037. O direto de R$ 7.830 milhões fica inteiro em Santa Cruz do Sul e fora da cor do mapa. A cor é o transbordamento: cadeia mais induzido."),
        ("Convenção numérica", "Uma casa decimal nas abas de premissa, resultado, obra, fiscal, COREDE e top 15. Três casas na abertura, no vetor e na cadeia, para o fechamento aparecer. Seis casas nos municípios, que é a precisão do CSV. O separador de milhar segue o idioma do Excel."),
        ("Conferência municipal", "O CSV guarda seis casas em R$ milhões. A soma dessas casas difere da cadeia em cerca de R$ 15 e do induzido em cerca de R$ 2, com sinal oposto. Esse resíduo volta a Santa Cruz do Sul, o maior município, a mesma regra de fechamento da nota de método. A célula de conferência da aba 08, em reais, é zero quando a soma municipal iguala a cadeia mais o induzido da aba 04."),
    ]
    s.r = 5
    s.headers(["Bloco", "Leitura", "Texto"])
    for nome, texto in blocos:
        s.write(1, nome, font=FONT_TOTAL)
        s.write(2, "", font=FONT)
        s.write(3, texto)
        ws.row_dimensions[s.r].height = 48
        s.r += 1
    s.r += 1
    s.write(1, "Parâmetros de preço", font=FONT_TOTAL)
    s.r += 1
    head = s.r
    s.headers(["Parâmetro", "Valor", "Unidade", "Fonte", "Natureza"])
    # headers() already advanced r
    s.write(1, "IPCA dezembro de 2019")
    ipca19 = s.input(2, dados["matriz"]["ipca_dez_2019"], FMT3)
    s.write(3, "índice, SIDRA 1737")
    s.write(4, "IBGE, SIDRA 1737, dez/2019")
    s.write(5, "dado")
    row_ipca19 = s.r
    s.r += 1
    s.write(1, "IPCA dezembro de 2025")
    s.input(2, dados["matriz"]["ipca_dez_2025"], FMT3)
    s.write(3, "índice, SIDRA 1737")
    s.write(4, "IBGE, SIDRA 1737, dez/2025")
    s.write(5, "dado")
    row_ipca25 = s.r
    s.r += 1
    s.write(1, "phi, 2019 sobre 2025", font=FONT_TOTAL)
    s.formula(2, f"=B{row_ipca19}/B{row_ipca25}", FMTPHI, total=True)
    s.write(3, "adimensional")
    s.write(4, "φ = IPCA 2019 / IPCA 2025")
    s.write(5, "fórmula")
    row_phi = s.r
    ws.row_dimensions[row_ipca19].height = 20
    ws.row_dimensions[row_ipca25].height = 20
    # named range
    wb.defined_names.add(DefinedName(name="phi", attr_text=f"'{ws.title}'!$B${row_phi}"))

    # ------------------------------------------------------------------ 01
    ws = wb.create_sheet("01_premissas_planta")
    s = Sheet(
        ws,
        "Premissas da planta",
        "R$ milhões de 2025, ocupações em pessoas, folha em toneladas quando a unidade disser. Células amarelas são entrada da revisão 4.",
        "Fonte: premissas do estudo, revisão 4, 18/10/2026, e ficha herdada do v6. A matriz multiplica o ano cheio de 2037.",
    )
    s.widths({"A": 46, "B": 22, "C": 16, "D": 16, "E": 16, "F": 62, "G": 22})
    s.headers(["Indicador", "Unidade", "2028", "2032", "2037", "Fonte", "Natureza"])
    linhas_prem = [
        ("Receita ex-fábrica", "R$ mi", 4700, 10680, 15830, "Premissas, revisão 4. 2037 = R$ 12,56 bi internos + R$ 3,27 bi FOB.", "dado"),
        ("Receita mercado interno", "R$ mi", None, None, 12560, "Premissas, revisão 4.", "dado"),
        ("Receita exportação FOB", "R$ mi", None, None, None, "Fórmula: receita total − receita interna, em 2037.", "fórmula"),
        ("Insumos", "R$ mi", None, None, 8000, "Âncora da revisão 4. R$ 8,00 bilhões.", "dado"),
        ("Insumos do mercado interno", "R$ mi", None, None, 5810, "Premissas, revisão 4.", "dado"),
        ("Insumos da exportação", "R$ mi", None, None, None, "Fórmula: insumos − insumos internos.", "fórmula"),
        ("Valor adicionado direto", "R$ mi", 2390, 5070, 7830, "Premissas, revisão 4. Em 2037, 15,83 − 8,00.", "dado"),
        ("Ocupações diretas", "pessoas", 1190, 2810, 4060, "Premissas, revisão 4. Estoque, não soma de anos.", "dado"),
        ("Ocupações da exportação", "pessoas", None, None, 1000, "Premissas, revisão 4. As 1,00 mil da variante sem exportação.", "dado"),
        ("Remuneração por ocupação", "R$", None, None, 150000, "Premissa v6, com encargos. Mantida.", "dado"),
        ("Remunerações", "R$ mi", 178, 421, None, "2028 e 2032 são a trajetória publicada. 2037 é ocupações × R$ 150 mil.", "dado / fórmula"),
        ("Folha comprada no RS", "R$ mi", 16, 35, 52.8, "Premissas. 2037 é R$ 52,8 milhões; o texto arredonda para R$ 53 milhões.", "dado"),
        ("Folha comprada no RS", "t", None, None, 3007, "Premissas, revisão 4. 46% do Sul.", "dado"),
        ("Folha comprada no Sul", "t", None, None, 6510, "Premissas, revisão 4.", "dado"),
        ("Folha comprada no Sul", "R$ mi", None, None, 114.2, "Premissas, revisão 4.", "dado"),
        ("Toneladas por família", "t / família", None, None, 5.5, "Regra das premissas. Família-equivalente fica fora da soma de empregos.", "dado"),
    ]
    addr = {}
    first_prem = s.r
    for nome, unidade, a, b, c, fonte, natureza in linhas_prem:
        s.write(1, nome)
        s.write(2, unidade)
        if a is None:
            s.write(3, None)
        else:
            s.input(3, a, FMT1 if unidade != "pessoas" else FMTI)
        if b is None:
            s.write(4, None)
        else:
            s.input(4, b, FMT1 if unidade != "pessoas" else FMTI)
        if c is None:
            s.write(5, None)
        else:
            fmt = FMTI if unidade == "pessoas" else (FMT2 if unidade == "R$" else FMT1)
            s.input(5, c, fmt)
        s.write(6, fonte)
        s.write(7, natureza)
        addr[nome + "|" + unidade] = s.r
        ws.row_dimensions[s.r].height = 30
        s.r += 1
    # fórmulas 2037
    r_rec = addr["Receita ex-fábrica|R$ mi"]
    r_int = addr["Receita mercado interno|R$ mi"]
    r_fob = addr["Receita exportação FOB|R$ mi"]
    r_ins = addr["Insumos|R$ mi"]
    r_ins_i = addr["Insumos do mercado interno|R$ mi"]
    r_ins_e = addr["Insumos da exportação|R$ mi"]
    r_va = addr["Valor adicionado direto|R$ mi"]
    r_occ = addr["Ocupações diretas|pessoas"]
    r_occ_e = addr["Ocupações da exportação|pessoas"]
    r_rem_u = addr["Remuneração por ocupação|R$"]
    r_rem = addr["Remunerações|R$ mi"]
    r_folha = addr["Folha comprada no RS|R$ mi"]
    r_ton = addr["Folha comprada no RS|t"]
    r_fam = addr["Toneladas por família|t / família"]
    s.ws.cell(r_fob, 5, f"=E{r_rec}-E{r_int}").number_format = FMT1
    s.ws.cell(r_fob, 5).font = FONT
    s.ws.cell(r_ins_e, 5, f"=E{r_ins}-E{r_ins_i}").number_format = FMT1
    s.ws.cell(r_ins_e, 5).font = FONT
    s.ws.cell(r_rem, 5, f"=E{r_occ}*E{r_rem_u}/1000000").number_format = FMT1
    s.ws.cell(r_rem, 5).font = FONT
    s.r += 1
    s.write(1, "Conferências da premissa, 2037", font=FONT_TOTAL)
    s.r += 1
    s.write(1, "Receita − insumos − VA direto")
    s.formula(5, f"=E{r_rec}-E{r_ins}-E{r_va}", FMT1, total=True)
    s.write(6, "Zero se a âncora contábil fecha.")
    r_conf_va = s.r
    s.r += 1
    s.write(1, "Ocupações × R$ 150 mil − remunerações, R$ mi")
    s.formula(5, f"=E{r_occ}*E{r_rem_u}/1000000-E{r_rem}", FMT1, total=True)
    s.write(6, "Zero por construção da remuneração de 2037.")
    s.r += 1
    s.write(1, "Famílias-equivalentes da folha no RS")
    s.formula(5, f"=E{r_ton}/E{r_fam}", FMT1, total=True)
    s.write(6, "3.007 t / 5,5 t. Fora da soma de ocupações. O texto lê 547.")
    s.r += 1
    s.write(1, "Ocupações só do mercado interno")
    s.formula(5, f"=E{r_occ}-E{r_occ_e}", FMTI)
    s.write(6, "4.060 − 1.000.")
    r_occ_int = s.r
    s.r += 1
    s.write(1, "VA só do mercado interno, R$ mi")
    s.formula(5, f"=E{r_int}-E{r_ins_i}", FMT1)
    s.write(6, "12.560 − 5.810 = 6.750.")
    r_va_int = s.r
    s.r += 1
    s.write(1, "Remuneração só do mercado interno, R$ mi")
    s.formula(5, f"=E{r_occ_int}*E{r_rem_u}/1000000", FMT1)
    r_rem_int = s.r

    # ------------------------------------------------------------------ 02
    ws = wb.create_sheet("02_bom")
    s = Sheet(
        ws,
        "Abertura estimada dos insumos",
        "R$ milhões de 2025, três casas. Compra no RS = valor × percentual. Compra fora = valor − compra no RS.",
        "Linhas que não são folha: estimativa desta rodada, estudo/resultados/resultados.json. Folha: dado da revisão 4. A âncora de R$ 8.000 milhões é a do arquivo.",
    )
    s.widths({
        "A": 42, "B": 12, "C": 12, "D": 16, "E": 12, "F": 16, "G": 16,
        "H": 18, "I": 16, "J": 16, "K": 78,
    })
    s.r = 5
    s.write(1, "Âncora de insumos da revisão 4")
    s.input(2, 8000, FMT3)
    s.write(3, "R$ mi")
    s.write(4, "Dado. O total da abertura fecha nesta âncora por fórmula.")
    r_ancora = s.r
    s.headers([
        "Linha", "Família", "Produto MIP", "Valor (R$ mi)", "% RS",
        "Compra RS (R$ mi)", "Compra fora (R$ mi)", "Outros estados (R$ mi)",
        "Importado (R$ mi)", "Natureza", "Regra",
    ])
    first_bom = s.r
    for linha in base["compras"]["linhas"]:
        s.write(1, linha["linha"])
        s.write(2, linha["familia"])
        s.write(3, linha["produto"])
        s.input(4, linha["valor"] / 1e6, FMT3)
        s.input(5, linha["rs"], "0%")
        s.formula(6, f"=D{s.r}*E{s.r}", FMT3)
        s.formula(7, f"=D{s.r}-F{s.r}", FMT3)
        s.input(8, linha["valor_uf"] / 1e6, FMT3)
        s.input(9, linha["valor_imp"] / 1e6, FMT3)
        s.write(10, "estimativa")
        s.write(11, linha["regra"])
        ws.row_dimensions[s.r].height = 32
        s.r += 1
    # folha
    s.write(1, "Folha no RS")
    s.write(2, "folha")
    s.write(3, "PR004")
    s.input(4, base["compras"]["folha_rs"] / 1e6, FMT3)
    s.input(5, 1, "0%")
    s.formula(6, f"=D{s.r}*E{s.r}", FMT3)
    s.formula(7, f"=D{s.r}-F{s.r}", FMT3)
    s.input(8, 0, FMT3)
    s.input(9, 0, FMT3)
    s.write(10, "dado")
    s.write(11, "Premissa da revisão 4. 3.007 t a preço de porteira. Entra na matriz em PR004.")
    r_folha_rs = s.r
    ws.row_dimensions[s.r].height = 30
    s.r += 1
    s.write(1, "Folha em SC e no PR")
    s.write(2, "folha")
    s.write(3, "fora")
    s.input(4, base["compras"]["folha_outras_uf"] / 1e6, FMT3)
    s.input(5, 0, "0%")
    s.formula(6, f"=D{s.r}*E{s.r}", FMT3)
    s.formula(7, f"=D{s.r}-F{s.r}", FMT3)
    s.input(8, base["compras"]["folha_outras_uf"] / 1e6, FMT3)
    s.input(9, 0, FMT3)
    s.write(10, "dado")
    s.write(11, "Premissa da revisão 4. Compra fora do RS. Não entra no vetor gaúcho.")
    ws.row_dimensions[s.r].height = 30
    last_antes_residuo = s.r
    s.r += 1
    s.write(1, "Resíduo até a âncora de R$ 8.000 mi")
    s.write(2, "encaixe")
    s.write(3, "—")
    s.formula(4, f"=$B${r_ancora}-SUM(D{first_bom}:D{last_antes_residuo})", FMT3)
    s.input(5, 0, "0%")
    s.formula(6, f"=D{s.r}*E{s.r}", FMT3)
    s.formula(7, f"=D{s.r}-F{s.r}", FMT3)
    s.formula(8, f"=D{s.r}", FMT3)
    s.formula(9, 0, FMT3)
    s.write(10, "encaixe")
    s.write(11, "Diferença entre a soma das linhas e a âncora da revisão 4. Não é compra e não entra no vetor. Na casa do milhão, o texto lê R$ 8.000 mi.")
    r_residuo = s.r
    ws.row_dimensions[s.r].height = 32
    s.r += 1
    r_tot_bom = s.r
    s.write(1, "Total", font=FONT_TOTAL)
    for c, letter in [(4, "D"), (6, "F"), (7, "G"), (8, "H"), (9, "I")]:
        s.formula(c, f"=SUM({letter}{first_bom}:{letter}{r_residuo})", FMT3, total=True)
    s.write(10, "fórmula", font=FONT_TOTAL)
    s.write(11, "O total de insumos fecha em 8.000. A compra no RS fecha em 830,039, lida no texto como R$ 830 milhões.", font=FONT_TOTAL)
    s.r += 1
    s.write(1, "Conferência: total − âncora")
    s.formula(4, f"=D{r_tot_bom}-$B${r_ancora}", FMT3, total=True)
    s.write(11, "Zero.")

    # ------------------------------------------------------------------ 03
    ws = wb.create_sheet("03_choque_mip")
    s = Sheet(
        ws,
        "Vetor de choque que entra na matriz",
        "R$ milhões. A coluna de 2025 é SOMASE da compra gaúcha na aba 02. A coluna de 2019 é o valor de 2025 vezes a célula nomeada phi.",
        "Preço básico. Só a compra no Rio Grande do Sul. O choque direto sobre a fabricação de produtos do fumo é zero.",
    )
    s.widths({"A": 14, "B": 62, "C": 28, "D": 28, "E": 55})
    s.r = 5
    s.write(1, "phi")
    s.formula(2, "=phi", FMTPHI)
    s.write(3, "Célula nomeada na aba 00. IPCA dez/2019 ÷ IPCA dez/2025.")
    s.headers(["Código", "Produto", "Compra RS, R$ mi de 2025", "Compra RS, R$ mi de 2019", "Fonte"])
    produtos = [
        ("PR066", "Material eletrônico e equipamentos de comunicações"),
        ("PR036", "Papel, papelão, embalagens e artefatos"),
        ("PR004", "Outros produtos da lavoura temporária (folha)"),
        ("PR086", "Transporte de carga"),
        ("PR080", "Eletricidade, gás e outras utilidades"),
        ("PR051", "Produtos químicos diversos"),
        ("PR079", "Manutenção e instalação de máquinas"),
        ("PR047", "Produtos químicos orgânicos"),
        ("PR081", "Água, esgoto e resíduos"),
    ]
    first_g = s.r
    for cod, nome in produtos:
        s.write(1, cod)
        s.write(2, nome)
        s.formula(3, f"=SUMIF('02_bom'!$C${first_bom}:$C${r_residuo},A{s.r},'02_bom'!$F${first_bom}:$F${r_residuo})", FMT3)
        s.formula(4, f"=C{s.r}*phi", FMT3)
        s.write(5, "Compra RS da aba 02, produto deste código. 2019 = 2025 × phi.")
        s.r += 1
    last_g = s.r - 1
    s.write(1, "Total", font=FONT_TOTAL)
    s.formula(3, f"=SUM(C{first_g}:C{last_g})", FMT3, total=True)
    s.formula(4, f"=SUM(D{first_g}:D{last_g})", FMT3, total=True)
    r_tot_g = s.r
    s.r += 1
    s.write(1, "Conferência com a compra RS da aba 02")
    s.formula(3, f"=C{r_tot_g}-'02_bom'!F{r_tot_bom}", FMT6, total=True)
    s.write(5, "Zero. O resíduo de encaixe da âncora tem produto “—” e fica de fora do vetor.")
    r_conf_g = s.r

    # ------------------------------------------------------------------ 04
    ws = wb.create_sheet("04_resultados_estaduais")
    s = Sheet(
        ws,
        "Resultados estaduais, 2037",
        "R$ milhões de 2025, uma casa. O Tipo II é direto + cadeia + induzido. O mesmo para ocupações.",
        "Direto: aba 01. Cadeia e induzido: saída de estudo/scripts/calcular_impacto.py, cenário base e sensibilidades, estudo/resultados/resultados.json.",
    )
    s.widths({"A": 42, "B": 18, "C": 18, "D": 18, "E": 18, "F": 18, "G": 55})
    s.r = 5
    s.write(1, "Manchete", font=FONT_TOTAL)
    s.r += 1
    s.headers(["Manchete", "Valor", "Unidade", "Origem"])
    # placeholders, formulas filled after the gaveta block addresses exist
    manchete_rows = {}
    for nome, unidade in [
        ("Valor adicionado direto", "R$ mi"),
        ("Ocupações diretas", "pessoas"),
        ("Valor adicionado da cadeia", "R$ mi"),
        ("Valor adicionado induzido", "R$ mi"),
        ("Transbordamento (cadeia + induzido)", "R$ mi"),
        ("Valor adicionado total, Tipo II", "R$ mi"),
        ("Ocupações totais, Tipo II", "pessoas"),
        ("Compra no RS", "R$ mi"),
        ("Vazamento", "R$ mi"),
    ]:
        s.write(1, nome, font=FONT_TOTAL)
        manchete_rows[nome] = s.r
        s.write(3, unidade)
        s.r += 1

    s.r += 1
    s.write(1, "Gavetas do cenário base", font=FONT_TOTAL)
    s.r += 1
    s.headers(["Gaveta", "VA (R$ mi)", "Remunerações (R$ mi)", "Ocupações", "Produção (R$ mi)", "Fonte", "Natureza"])
    # direto
    s.write(1, "Direto, planta")
    s.formula(2, f"='01_premissas_planta'!E{r_va}", FMT1)
    s.formula(3, f"='01_premissas_planta'!E{r_rem}", FMT1)
    s.formula(4, f"='01_premissas_planta'!E{r_occ}", FMTI)
    s.formula(5, f"='01_premissas_planta'!E{r_rec}", FMT1)
    s.write(6, "Aba 01, ano 2037.")
    s.write(7, "dado")
    r_dir = s.r
    s.r += 1
    s.write(1, "Cadeia, compras no RS")
    s.input(2, base["cadeia"]["va_2025"] / 1e6, FMT1)
    s.input(3, base["cadeia"]["rem_2025"] / 1e6, FMT1)
    s.input(4, base["cadeia"]["ocupacoes"], FMT1)
    s.input(5, base["cadeia"]["producao_2025"] / 1e6, FMT1)
    s.write(6, "calcular_impacto.py, chave base.cadeia. Inversa de Leontief da MIP-RS 2019.")
    s.write(7, "estimativa")
    r_cad = s.r
    s.r += 1
    s.write(1, "Induzido, uma rodada")
    s.input(2, base["induzido"]["va_2025"] / 1e6, FMT1)
    s.input(3, base["induzido"]["rem_2025"] / 1e6, FMT1)
    s.input(4, base["induzido"]["ocupacoes"], FMT1)
    s.input(5, base["induzido"]["producao_2025"] / 1e6, FMT1)
    s.write(6, "calcular_impacto.py, chave base.induzido. 60% da massa salarial, uma rodada.")
    s.write(7, "estimativa")
    r_ind = s.r
    s.r += 1
    s.write(1, "Total Tipo I (direto + cadeia)", font=FONT_TOTAL)
    s.formula(2, f"=B{r_dir}+B{r_cad}", FMT1, total=True)
    s.formula(3, f"=C{r_dir}+C{r_cad}", FMT1, total=True)
    s.formula(4, f"=D{r_dir}+D{r_cad}", FMT1, total=True)
    s.formula(5, f"=E{r_dir}+E{r_cad}", FMT1, total=True)
    s.write(7, "fórmula")
    r_ti = s.r
    s.r += 1
    s.write(1, "Total Tipo II (direto + cadeia + induzido)", font=FONT_TOTAL)
    s.formula(2, f"=B{r_dir}+B{r_cad}+B{r_ind}", FMT1, total=True)
    s.formula(3, f"=C{r_dir}+C{r_cad}+C{r_ind}", FMT1, total=True)
    s.formula(4, f"=D{r_dir}+D{r_cad}+D{r_ind}", FMT1, total=True)
    s.formula(5, f"=E{r_dir}+E{r_cad}+E{r_ind}", FMT1, total=True)
    s.write(7, "fórmula")
    r_tii = s.r
    s.r += 1
    s.write(1, "Transbordamento (cadeia + induzido)", font=FONT_TOTAL)
    s.formula(2, f"=B{r_cad}+B{r_ind}", FMT1, total=True)
    s.write(6, "É o total que a aba 08 reparte. O direto fica de fora.")
    s.write(7, "fórmula")
    r_trans = s.r
    s.r += 1
    s.write(1, "Compra no RS")
    s.formula(2, "='03_choque_mip'!C" + str(r_tot_g), FMT1)
    s.write(6, "Soma do vetor da aba 03.")
    r_compra = s.r
    s.r += 1
    s.write(1, "Vazamento")
    s.formula(2, f"='01_premissas_planta'!E{r_ins}-B{r_compra}", FMT1)
    s.write(6, "Insumos da aba 01 menos a compra no RS. Registrado, fora da inversa.")
    r_vaz = s.r
    s.r += 1
    s.write(1, "Produção da cadeia por real comprado no RS")
    s.formula(2, f"=E{r_cad}/B{r_compra}", FMT2)
    s.write(6, "O texto lê R$ 1,56.")
    s.r += 1
    s.write(1, "VA da cadeia por real comprado no RS")
    s.formula(2, f"=B{r_cad}/B{r_compra}", FMT2)
    s.write(6, "O texto lê R$ 0,60.")

    # preenche manchete agora que os endereços existem
    ligacoes = {
        "Valor adicionado direto": (f"=B{r_dir}", FMT1, "Aba 01, via gaveta direta."),
        "Ocupações diretas": (f"=D{r_dir}", FMTI, "Aba 01, via gaveta direta."),
        "Valor adicionado da cadeia": (f"=B{r_cad}", FMT1, "Saída do modelo, célula de entrada da gaveta cadeia."),
        "Valor adicionado induzido": (f"=B{r_ind}", FMT1, "Saída do modelo, célula de entrada da gaveta induzido."),
        "Transbordamento (cadeia + induzido)": (f"=B{r_trans}", FMT1, "Fórmula: cadeia + induzido."),
        "Valor adicionado total, Tipo II": (f"=B{r_tii}", FMT1, "Fórmula: direto + cadeia + induzido."),
        "Ocupações totais, Tipo II": (f"=D{r_tii}", FMTI, "Fórmula: direto + cadeia + induzido."),
        "Compra no RS": (f"=B{r_compra}", FMT1, "Aba 03, soma do vetor."),
        "Vazamento": (f"=B{r_vaz}", FMT1, "Insumos − compra no RS."),
    }
    for nome, (formula, fmt, origem) in ligacoes.items():
        rr = manchete_rows[nome]
        cell = ws.cell(rr, 2, formula)
        cell.font = FONT_TOTAL
        cell.number_format = fmt
        cell.fill = FILL_TOTAL
        ws.cell(rr, 4, origem).font = FONT

    # faixa
    s.r += 2
    s.write(1, "Faixa 10/20/35 e variante sem exportação", font=FONT_TOTAL)
    s.write(2, "O Tipo II e o Tipo I são fórmulas. Cadeia e induzido são a saída do modelo em cada cenário.")
    s.r += 1
    s.headers([
        "Cenário", "VA direto", "VA cadeia", "VA induzido", "VA Tipo I", "VA Tipo II",
        "Ocup. direto", "Ocup. cadeia", "Ocup. induzido", "Ocup. Tipo I", "Ocup. Tipo II",
        "Compra RS", "Vazamento",
    ])
    for letter, width in {
        "A": 32, "B": 14, "C": 14, "D": 14, "E": 14, "F": 14,
        "G": 14, "H": 14, "I": 14, "J": 14, "K": 14, "L": 14, "M": 14,
    }.items():
        ws.column_dimensions[letter].width = max(ws.column_dimensions[letter].width or 0, width)

    def cenario_row(nome, bloco, direto_formula=False, base_ligado=False):
        s.write(1, nome)
        if direto_formula:
            s.formula(2, f"=B{r_dir}", FMT1)
            s.formula(7, f"=D{r_dir}", FMT1)
        else:
            s.input(2, bloco["direto"]["va"] / 1e6, FMT1)
            s.input(7, bloco["direto"]["ocupacoes"], FMT1)
        if base_ligado:
            s.formula(3, f"=B{r_cad}", FMT1)
            s.formula(4, f"=B{r_ind}", FMT1)
            s.formula(8, f"=D{r_cad}", FMT1)
            s.formula(9, f"=D{r_ind}", FMT1)
            s.formula(12, f"=B{r_compra}", FMT1)
            s.formula(13, f"=B{r_vaz}", FMT1)
        else:
            s.input(3, bloco["cadeia"]["va_2025"] / 1e6, FMT1)
            s.input(4, bloco["induzido"]["va_2025"] / 1e6, FMT1)
            s.input(8, bloco["cadeia"]["ocupacoes"], FMT1)
            s.input(9, bloco["induzido"]["ocupacoes"], FMT1)
            s.input(12, bloco["compras"]["compras_rs"] / 1e6, FMT1)
            s.input(13, bloco["compras"]["vazamento"] / 1e6, FMT1)
        s.formula(5, f"=B{s.r}+C{s.r}", FMT1)
        s.formula(6, f"=B{s.r}+C{s.r}+D{s.r}", FMT1)
        s.formula(10, f"=G{s.r}+H{s.r}", FMT1)
        s.formula(11, f"=G{s.r}+H{s.r}+I{s.r}", FMT1)
        s.r += 1

    cenario_row("Abertura estimada (base, 9,9%)", base, direto_formula=True, base_ligado=True)
    for alpha, bloco in dados["faixa"].items():
        pct = int(round(float(alpha) * 100))
        cenario_row(f"Conteúdo local uniforme de {pct}%", bloco, direto_formula=True)
    sem = dados["sem_exportacao"]
    s.write(1, "Abertura, sem exportação")
    s.formula(2, f"='01_premissas_planta'!E{r_va_int}", FMT1)
    s.input(3, sem["cadeia"]["va_2025"] / 1e6, FMT1)
    s.input(4, sem["induzido"]["va_2025"] / 1e6, FMT1)
    s.formula(5, f"=B{s.r}+C{s.r}", FMT1)
    s.formula(6, f"=B{s.r}+C{s.r}+D{s.r}", FMT1)
    s.formula(7, f"='01_premissas_planta'!E{r_occ_int}", FMT1)
    s.input(8, sem["cadeia"]["ocupacoes"], FMT1)
    s.input(9, sem["induzido"]["ocupacoes"], FMT1)
    s.formula(10, f"=G{s.r}+H{s.r}", FMT1)
    s.formula(11, f"=G{s.r}+H{s.r}+I{s.r}", FMT1)
    s.input(12, sem["compras"]["compras_rs"] / 1e6, FMT1)
    s.input(13, sem["compras"]["vazamento"] / 1e6, FMT1)
    s.r += 2
    s.write(1, "Bloco II do contratante, para comparação, fora da soma", font=FONT_TOTAL)
    s.r += 1
    s.write(1, "VA do bloco II no RS, R$ mi")
    s.input(2, dados["bloco_II_contratante"]["vab_rs_bi"] * 1000, FMT1)
    s.write(6, "Premissas, revisão 4. R$ 8,85 bilhões. Não é choque.")
    s.r += 1
    s.write(1, "Ocupações do bloco II no RS")
    s.input(2, dados["bloco_II_contratante"]["ocupacoes_rs"], FMTI)
    s.write(6, "Premissas, revisão 4. 12,76 mil.")
    s.r += 1
    s.write(1, "Tributos sobre o consumo no RS, bloco II, R$ mi")
    s.input(2, dados["bloco_II_contratante"]["tributos_consumo_rs_bi"] * 1000, FMT1)
    s.write(6, "Premissas, revisão 4. R$ 0,928 bilhão.")

    wb.defined_names.add(DefinedName(name="va_cadeia", attr_text=f"'04_resultados_estaduais'!$B${r_cad}"))
    wb.defined_names.add(DefinedName(name="va_induzido", attr_text=f"'04_resultados_estaduais'!$B${r_ind}"))
    wb.defined_names.add(DefinedName(name="va_direto", attr_text=f"'04_resultados_estaduais'!$B${r_dir}"))
    wb.defined_names.add(DefinedName(name="transbordo", attr_text=f"'04_resultados_estaduais'!$B${r_trans}"))
    wb.defined_names.add(DefinedName(name="producao_cadeia", attr_text=f"'04_resultados_estaduais'!$E${r_cad}"))

    # ------------------------------------------------------------------ 05
    ws = wb.create_sheet("05_cadeia_atividade")
    s = Sheet(
        ws,
        "Cadeia por atividade",
        "R$ milhões de 2025, três casas. As 52 atividades são a saída publicada. O resíduo de arredondamento do CSV volta ao total da cadeia por fórmula.",
        "Fonte: estudo/resultados/cadeia_por_atividade.csv, reescalado no script para o valor adicionado da cadeia. Total de referência: célula nomeada va_cadeia.",
    )
    s.widths({"A": 12, "B": 78, "C": 28, "D": 28, "E": 16})
    atividades = list(csv.DictReader(ATV_PATH.open(encoding="utf-8")))
    s.headers(["Código", "Atividade", "Produção da cadeia (R$ mi)", "VA da cadeia (R$ mi)", "Coef. VA"])
    first_at = s.r
    for linha in atividades:
        s.write(1, linha["codigo"])
        s.write(2, linha["atividade"])
        s.input(3, float(linha["producao_cadeia_mi_2025"]), FMT3)
        s.input(4, float(linha["va_cadeia_mi_2025"]), FMT3)
        s.input(5, float(linha["coef_va"]), "0.0000")
        s.r += 1
    last_at = s.r - 1
    s.write(1, "", font=FONT_TOTAL)
    s.write(2, "Soma das 52 atividades", font=FONT_TOTAL)
    s.formula(3, f"=SUM(C{first_at}:C{last_at})", FMT3, total=True)
    s.formula(4, f"=SUM(D{first_at}:D{last_at})", FMT3, total=True)
    r_soma_at = s.r
    s.r += 1
    s.write(2, "Resíduo de arredondamento até o total da cadeia")
    s.formula(3, f"=producao_cadeia-C{r_soma_at}", FMT6)
    s.formula(4, f"=va_cadeia-D{r_soma_at}", FMT6)
    s.write(5, "CSV em três casas")
    r_resid_at = s.r
    s.r += 1
    s.write(2, "Total conferido", font=FONT_TOTAL)
    s.formula(3, f"=C{r_soma_at}+C{r_resid_at}", FMT3, total=True)
    s.formula(4, f"=D{r_soma_at}+D{r_resid_at}", FMT3, total=True)
    r_conf_at_tot = s.r
    s.r += 1
    s.write(2, "Conferência com a cadeia da aba 04 (R$ mi)")
    s.formula(3, f"=C{r_conf_at_tot}-producao_cadeia", FMT6, total=True)
    s.formula(4, f"=D{r_conf_at_tot}-va_cadeia", FMT6, total=True)
    s.write(5, "Zero.")

    # ------------------------------------------------------------------ 06
    ws = wb.create_sheet("06_obra")
    s = Sheet(
        ws,
        "Obra de conversão, 2026–2027",
        "R$ milhões de 2025. Este bloco não se soma ao ano cheio de 2037. Capital de giro fica fora do choque.",
        "Calibração: Papastratos (€300 mi, 20 bi sticks, desconto de 15% de galpão), ponto médio de US$ 50–150 mi no e-líquido e US$ 8–25 mi no sachê. Câmbio: PTAX venda média de 2025.",
    )
    s.widths({"A": 52, "B": 18, "C": 18, "D": 62, "E": 18})
    s.headers(["Parâmetro", "Valor", "Unidade", "Fonte", "Natureza"])
    params = {}

    def prow(nome, valor, unidade, fonte, natureza, fmt=FMT3):
        s.write(1, nome)
        if isinstance(valor, str) and valor.startswith("="):
            s.formula(2, valor, fmt)
        else:
            s.input(2, valor, fmt)
        s.write(3, unidade)
        s.write(4, fonte)
        s.write(5, natureza)
        params[nome] = s.r
        ws.row_dimensions[s.r].height = 28
        s.r += 1

    prow("PTAX dólar, média 2025", 5.585524, "R$ / US$", "BCB, PTAX venda, média de 2025. O texto lê R$ 5,59.", "dado", "0.0000")
    prow("PTAX euro, média 2025", 6.308451, "R$ / €", "BCB, PTAX venda, média de 2025. O texto lê R$ 6,31.", "dado", "0.0000")
    prow("Régua Papastratos", 300, "€ mi", "PMI, Grécia, 2017. €300 mi para cerca de 20 bi sticks.", "dado", FMT1)
    prow("Capacidade de referência", 20, "bi sticks", "Comunicado Papastratos.", "dado", FMT1)
    prow("Sticks em 2037", 12.338, "bi sticks", "Premissas, revisão 4. 11,420 internos + 0,918 de exportação.", "dado", FMT3)
    prow("Desconto de galpão existente", 0.85, "fração", "15% porque o galpão e o terreno já existem.", "estimativa", "0%")
    prow("Linha de e-líquido, ponto médio", 100, "US$ mi", "Ponto médio de US$ 50–150 mi. 271 milhões de pods.", "estimativa", FMT1)
    prow("Linha de sachê, ponto médio", 15, "US$ mi", "Ponto médio de US$ 8–25 mi.", "estimativa", FMT1)
    usd = f"B{params['PTAX dólar, média 2025']}"
    eur = f"B{params['PTAX euro, média 2025']}"
    prow(
        "Linha de sticks",
        f"=B{params['Régua Papastratos']}*(B{params['Sticks em 2037']}/B{params['Capacidade de referência']})*B{params['Desconto de galpão existente']}*{eur}",
        "R$ mi",
        "€300 mi × (12,338/20) × 0,85 × PTAX do euro. O texto lê R$ 992 mi.",
        "fórmula",
    )
    prow("Linha de e-líquido", f"=B{params['Linha de e-líquido, ponto médio']}*{usd}", "R$ mi", "US$ 100 mi × PTAX do dólar. O texto lê R$ 559 mi.", "fórmula")
    prow("Linha de sachê", f"=B{params['Linha de sachê, ponto médio']}*{usd}", "R$ mi", "US$ 15 mi × PTAX do dólar. O texto lê R$ 84 mi.", "fórmula")
    r_stick = params["Linha de sticks"]
    r_eliq = params["Linha de e-líquido"]
    r_sach = params["Linha de sachê"]
    prow("CAPEX da conversão", f"=B{r_stick}+B{r_eliq}+B{r_sach}", "R$ mi", "Soma dos três pedaços. O texto lê R$ 1,63 bi.", "fórmula")
    r_capex = params["CAPEX da conversão"]
    for nome, share, fonte in [
        ("Máquinas importadas", 0.62, "62%. Hipótese: máquina proprietária da PMI."),
        ("Obras civis e utilidades no RS", 0.18, "18%. Edificações, PR082."),
        ("Montagem no RS", 0.084, "8,4%. Manutenção e instalação, PR079."),
        ("Montagem importada", 0.036, "3,6%."),
        ("Engenharia no RS", 0.032, "3,2%. PR102."),
        ("Engenharia importada", 0.048, "4,8%."),
    ]:
        prow(nome, share, "fração do CAPEX", fonte, "estimativa", "0.0%")
        # valor ao lado será fórmula numa coluna extra? Keep share as input and value as next rows.
    s.r += 0
    s.write(1, "Valor dos pedaços", font=FONT_TOTAL)
    s.r += 1
    s.headers(["Pedaço", "Valor (R$ mi)", "Entra na matriz?", "Produto MIP", "Fórmula"])
    pedacos = [
        ("Máquinas importadas", "Máquinas importadas", "não", "—"),
        ("Obras civis e utilidades no RS", "Obras civis e utilidades no RS", "sim", "PR082"),
        ("Montagem no RS", "Montagem no RS", "sim", "PR079"),
        ("Montagem importada", "Montagem importada", "não", "—"),
        ("Engenharia no RS", "Engenharia no RS", "sim", "PR102"),
        ("Engenharia importada", "Engenharia importada", "não", "—"),
    ]
    first_ped = s.r
    for nome, chave, entra, produto in pedacos:
        s.write(1, nome)
        s.formula(2, f"=$B${r_capex}*B{params[chave]}", FMT3)
        s.write(3, entra)
        s.write(4, produto)
        s.write(5, "CAPEX × fração")
        params["valor:" + nome] = s.r
        s.r += 1
    last_ped = s.r - 1
    s.write(1, "Soma dos pedaços", font=FONT_TOTAL)
    s.formula(2, f"=SUM(B{first_ped}:B{last_ped})", FMT3, total=True)
    r_soma_ped = s.r
    s.r += 1
    s.write(1, "Conferência: soma dos pedaços − CAPEX")
    s.formula(2, f"=B{r_soma_ped}-B{r_capex}", FMT6, total=True)
    s.write(5, "Zero. As frações somam 1.")
    s.r += 1
    s.write(1, "Parcela gaúcha, que entra na matriz", font=FONT_TOTAL)
    s.formula(
        2,
        f"=B{params['valor:Obras civis e utilidades no RS']}+B{params['valor:Montagem no RS']}+B{params['valor:Engenharia no RS']}",
        FMT3,
        total=True,
    )
    s.write(5, "O texto lê R$ 484 mi.")
    r_rs = s.r
    s.r += 1
    s.write(1, "Parcela importada")
    s.formula(2, f"=B{r_capex}-B{r_rs}", FMT3)
    s.r += 1
    s.write(1, "Terreno")
    s.input(2, 0, FMT1)
    s.write(5, "Planta existente. Dado.")
    s.r += 1
    s.write(1, "Capital de giro, 45 dias, fora do choque")
    s.formula(2, f"='01_premissas_planta'!E{r_ins}*45/365", FMT3)
    s.write(5, "45/365 dos insumos de 2037. Fora da matriz.")
    s.r += 1
    s.write(1, "Piso observado na fábrica, fora do CAPEX")
    s.input(2, 100, FMT1)
    s.write(5, "Deck citado nas premissas. Não substitui o CAPEX.")
    s.r += 1
    s.write(1, "ISS, alíquota")
    s.input(2, 0.02, "0%")
    s.write(5, "Santa Cruz do Sul, lista de serviços, item 7.02.")
    r_aliq = s.r
    s.r += 1
    s.write(1, "ISS, fração da parcela local tomada como serviço")
    s.input(2, 0.5, "0%")
    s.write(5, "Ponto médio: materiais no ICMS, serviços no ISS.")
    r_frac = s.r
    s.r += 1
    s.write(1, "ISS da obra em Santa Cruz do Sul", font=FONT_TOTAL)
    s.formula(2, f"=B{r_aliq}*B{r_frac}*B{r_rs}", FMT3, total=True)
    s.write(5, "Uma vez, no biênio. O texto lê R$ 4,8 mi. Fora de 2037.")
    r_iss = s.r
    s.r += 2
    s.write(1, "Efeito da obra no RS, Tipo I, separado de 2037", font=FONT_TOTAL)
    s.r += 1
    s.headers(["Efeito", "Valor", "Unidade", "Fonte", "Natureza"])
    obra = dados["obra_2026_2027"]
    for nome, valor, unidade, fmt in [
        ("Produção gerada", obra["producao_2025"] / 1e6, "R$ mi", FMT1),
        ("Valor adicionado", obra["va_2025"] / 1e6, "R$ mi", FMT1),
        ("Remunerações", obra["rem_2025"] / 1e6, "R$ mi", FMT1),
        ("Ocupações do Leontief da obra", obra["ocupacoes_leontief"], "pessoas", FMT1),
        ("Postos temporários na construção", obra["postos_temporarios_construcao"], "pessoas", FMT1),
    ]:
        s.write(1, nome)
        s.input(2, valor, fmt)
        s.write(3, unidade)
        s.write(4, "calcular_impacto.py, bloco obra_2026_2027. Choque só da parcela gaúcha. O texto arredonda ao milhão e ao milhar.")
        s.write(5, "estimativa")
        s.r += 1

    # ------------------------------------------------------------------ 07
    ws = wb.create_sheet("07_fiscal")
    s = Sheet(
        ws,
        "Retorno fiscal e hipótese FUNDOPEM",
        "R$ milhões de 2037, reais de 2025, uma casa. O líquido é o bruto estadual e municipal menos o diferimento. O IRPJ fica à parte. O ISS é o da obra.",
        "Bruto: premissas, revisão 4. Hipótese: 30% por 96 meses, Lei 15.642/2021 e FUNDOPEM Recupera Avança. Sem INTEGRAR, a renúncia permanente é zero.",
    )
    s.widths({"A": 62, "B": 16, "C": 16, "D": 78, "E": 16})
    s.headers(["Canal", "Valor (R$ mi)", "Esfera", "Fonte", "Natureza"])
    s.write(1, "Tributos sobre o consumo no Brasil")
    s.input(2, 13700, FMT1)
    s.write(3, "Brasil")
    s.write(4, "Premissas, revisão 4. R$ 13,7 bi.")
    s.write(5, "dado")
    s.r += 1
    s.write(1, "Dos quais federais")
    s.input(2, 6580, FMT1)
    s.write(3, "Federal")
    s.write(4, "Premissas, revisão 4.")
    s.write(5, "dado")
    s.r += 1
    s.write(1, "Dos quais estaduais e municipais no Brasil")
    s.input(2, 7120, FMT1)
    s.write(3, "Estados e municípios")
    s.write(4, "Premissas, revisão 4.")
    s.write(5, "dado")
    s.r += 1
    s.write(1, "Tributos sobre o consumo no RS")
    s.input(2, 928, FMT1)
    s.write(3, "RS")
    s.write(4, "Premissas, revisão 4. Cerca de 6,8% do total nacional. R$ 0,93 bi.")
    s.write(5, "dado")
    s.r += 1
    s.write(1, "Dos quais federais no RS")
    s.input(2, 448, FMT1)
    s.write(3, "Federal")
    s.write(4, "Premissas, revisão 4.")
    s.write(5, "dado")
    s.r += 1
    s.write(1, "Bruto estadual e municipal no RS (ICMS)")
    s.input(2, 480, FMT1)
    s.write(3, "Estado e municípios")
    s.write(4, "Premissas, revisão 4. R$ 0,48 bi. Base da hipótese.")
    s.write(5, "dado")
    r_bruto = s.r
    s.r += 1
    s.write(1, "Cota-parte municipal, 25%")
    s.formula(2, f"=B{r_bruto}*0.25", FMT1)
    s.write(3, "Municípios gaúchos")
    s.write(4, "Cota constitucional sobre o ICMS do consumo no RS. Conjunto dos municípios, não a sede.")
    s.write(5, "fórmula")
    r_cota = s.r
    s.r += 1
    s.write(1, "ICMS estadual, líquido da cota")
    s.formula(2, f"=B{r_bruto}-B{r_cota}", FMT1)
    s.write(3, "Estado")
    s.write(4, "Bruto − cota-parte.")
    s.write(5, "fórmula")
    s.r += 1
    s.write(1, "IRPJ/CSLL da planta")
    s.input(2, dados["base"]["fiscal"]["irpj_csll"] / 1e6, FMT1)
    s.write(3, "Federal")
    s.write(4, "Regra do arquivo: 34% sobre 50% do excedente. Fora do retorno do RS. O texto lê R$ 1,23 bi.")
    s.write(5, "dado")
    s.r += 1
    s.write(1, "Hipótese FUNDOPEM, percentual")
    s.input(2, 0.30, "0%")
    s.write(4, "FUNDOPEM Recupera Avança, Plano Rio Grande. Financiamento, não o teto de 75%.")
    s.write(5, "hipótese")
    r_pct = s.r
    s.r += 1
    s.write(1, "Hipótese FUNDOPEM, prazo")
    s.input(2, 96, FMTI)
    s.write(3, "meses")
    s.write(4, "Lei 15.642/2021. Fruição máxima de referência.")
    s.write(5, "hipótese")
    s.r += 1
    s.write(1, "Diferimento no ano cheio")
    s.formula(2, f"=B{r_pct}*B{r_bruto}", FMT1)
    s.write(3, "Caixa adiado")
    s.write(4, "Percentual × bruto. Com início em 2028, a fruição acaba em 2035.")
    s.write(5, "fórmula")
    r_dif = s.r
    s.r += 1
    s.write(1, "Líquido enquanto a hipótese vigora", font=FONT_TOTAL)
    s.formula(2, f"=B{r_bruto}-B{r_dif}", FMT1, total=True)
    s.write(3, "Estado e municípios")
    s.write(4, "Bruto − diferimento. O texto lê R$ 336 mi.")
    s.write(5, "fórmula")
    s.r += 1
    s.write(1, "Abatimento INTEGRAR")
    s.input(2, 0, FMT1)
    s.write(4, "Hipótese sem abatimento.")
    s.write(5, "hipótese")
    r_intg = s.r
    s.r += 1
    s.write(1, "Renúncia permanente", font=FONT_TOTAL)
    s.formula(2, f"=B{r_intg}", FMT1, total=True)
    s.write(4, "Sem INTEGRAR, o financiado é pago depois. Zero.")
    s.write(5, "fórmula")
    s.r += 1
    s.write(1, "ISS da obra em Santa Cruz do Sul")
    s.formula(2, "='06_obra'!B" + str(r_iss), FMT1)
    s.write(3, "Município-sede")
    s.write(4, "Aba 06. Uma vez, em 2026–2027. Fora do ano de 2037.")
    s.write(5, "fórmula")
    s.r += 1
    s.write(1, "População do COREDE no Estado")
    s.input(2, 0.039, "0.0%")
    s.write(4, "Censo 2022, leitura da nota espacial. 3,9%.")
    s.write(5, "dado")
    r_pop = s.r
    s.r += 1
    s.write(1, "Leitura do bruto pela população do COREDE")
    s.formula(2, f"=B{r_bruto}*B{r_pop}", FMT1)
    s.write(4, "Destino do consumo. O texto lê R$ 18,7 mi. Não é cota-parte, VAF nem ISS.")
    s.write(5, "fórmula")

    # ------------------------------------------------------------------ 08
    ws = wb.create_sheet("08_municipios")
    s = Sheet(
        ws,
        "Transbordamento por município",
        "R$ milhões de 2025, seis casas, a precisão do CSV. Transbordamento = folha + indústria + serviços + induzido. O direto fica em coluna própria.",
        "Fonte: estudo/espacial/va_por_municipio.csv. Ajuste de centavos em Santa Cruz do Sul para a soma igualar va_cadeia + va_induzido. Flag COREDE: estatuto, 23 municípios.",
    )
    s.widths({
        "A": 14, "B": 28, "C": 16, "D": 16, "E": 16, "F": 16, "G": 18,
        "H": 16, "I": 12, "J": 16, "K": 16, "L": 14,
        "N": 16, "O": 16, "P": 16, "Q": 16,
    })
    municipios = list(csv.DictReader(MUN_PATH.open(encoding="utf-8-sig")))
    assert len(municipios) == 497, len(municipios)
    s.r = 5
    s.write(1, "Ajuste da cadeia, R$ mi", font=FONT_TOTAL)
    # fórmulas preenchidas depois que as linhas base existirem
    r_aj_cad = s.r
    s.write(3, "Volta para serviços de Santa Cruz do Sul. Resíduo do CSV de seis casas.")
    s.r += 1
    s.write(1, "Ajuste do induzido, R$ mi", font=FONT_TOTAL)
    r_aj_ind = s.r
    s.write(3, "Volta para o induzido de Santa Cruz do Sul.")
    s.r += 1
    s.write(1, "Conferência municipal, R$", font=FONT_TOTAL)
    r_conf_mun = s.r
    s.write(3, "Zero se a soma dos 497 municípios iguala a cadeia mais o induzido da aba 04.")
    s.r += 1
    s.write(1, "Conferência da cadeia, R$")
    r_conf_cad_m = s.r
    s.write(3, "Zero se folha + indústria + serviços fecham a cadeia.")
    s.r += 1
    s.write(1, "Conferência do induzido, R$")
    r_conf_ind_m = s.r
    s.write(3, "Zero se a coluna de induzido fecha o induzido estadual.")
    s.r += 1
    s.headers([
        "Código IBGE", "Município", "Folha (R$ mi)", "Indústria (R$ mi)", "Serviços (R$ mi)",
        "Induzido (R$ mi)", "Transbordamento (R$ mi)", "VA direto (R$ mi)", "COREDE",
        "PAM 2025 (t)", "Compra nova 2037 (t)", "Distância à sede (km)",
    ])
    # base à direita, a partir da coluna 14
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
        folha = float(linha["va_folha_mi"])
        industria = float(linha["va_industria_mi"])
        serv = float(linha["va_servicos_mi"])
        indu = float(linha["va_induzido_mi"])
        # base
        s.input(14, folha, FMT6)
        s.input(15, industria, FMT6)
        s.input(16, serv, FMT6)
        s.input(17, indu, FMT6)
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
    assert sede_row is not None
    s.write(1, "", font=FONT_TOTAL)
    s.write(2, "TOTAL", font=FONT_TOTAL)
    for c, letter in [(3, "C"), (4, "D"), (5, "E"), (6, "F"), (7, "G"), (8, "H"), (9, "I")]:
        s.formula(c, f"=SUM({letter}{first_m}:{letter}{last_m})", FMT6 if c < 8 else (FMT1 if c == 8 else FMTI), total=True)
    r_tot_m = s.r
    # ajustes e conferências
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
    ws.cell(r_conf_cad_m, 2, f"=ROUND((C{r_tot_m}+D{r_tot_m}+E{r_tot_m}-va_cadeia)*1000000,2)")
    ws.cell(r_conf_cad_m, 2).number_format = FMT2
    ws.cell(r_conf_cad_m, 2).font = FONT
    ws.cell(r_conf_ind_m, 2, f"=ROUND((F{r_tot_m}-va_induzido)*1000000,2)")
    ws.cell(r_conf_ind_m, 2).number_format = FMT2
    ws.cell(r_conf_ind_m, 2).font = FONT
    s.finish_filter(1, 12, last_m)
    # freeze already set by headers(); keep it
    wb.defined_names.add(DefinedName(name="conf_municipal_reais", attr_text=f"'08_municipios'!$B${r_conf_mun}"))

    # ------------------------------------------------------------------ 09
    ws = wb.create_sheet("09_corede")
    s = Sheet(
        ws,
        "COREDE Vale do Rio Pardo",
        "R$ milhões de 2025. Cada valor é SOMASE do código IBGE na aba 08. A lista dos 23 é a do estatuto.",
        "Artigo 3º do estatuto do COREDE Vale do Rio Pardo e Plano Estratégico de Desenvolvimento 2022–2030. Gramado Xavier fica de fora.",
    )
    s.widths({"A": 16, "B": 28, "C": 22, "D": 16, "E": 16, "F": 16, "G": 16, "H": 16, "I": 16})
    s.r = 5
    s.write(1, "Transbordamento do COREDE", font=FONT_TOTAL)
    r_corede_total_cell = s.r
    s.write(3, "Soma dos 23, fórmula no fim da lista.")
    s.r += 1
    s.write(1, "Parcela do transbordamento estadual")
    r_corede_pct = s.r
    s.r += 1
    s.write(1, "Conferência: SOMASE da flag − soma dos 23, R$ mi")
    r_corede_conf = s.r
    s.write(3, "Zero se a lista oficial é exatamente a flag da aba 08.")
    s.r += 1
    s.headers([
        "Código IBGE", "Município", "Transbordamento (R$ mi)", "Folha", "Indústria",
        "Serviços", "Induzido", "VA direto", "PAM 2025 (t)",
    ])
    corede = [m for m in municipios if int(m["corede_vale_do_rio_pardo"]) == 1]
    corede.sort(key=lambda m: -float(m["va_transbordo_mi"]))
    assert len(corede) == 23
    first_c = s.r
    rng_cod = f"'08_municipios'!$A${first_m}:$A${last_m}"
    for m in corede:
        codigo = int(m["codigo_ibge"])
        s.input(1, codigo, "0")
        s.formula(2, f"=INDEX('08_municipios'!$B${first_m}:$B${last_m},MATCH(A{s.r},{rng_cod},0))")
        for col_i, src in [(3, "G"), (4, "C"), (5, "D"), (6, "E"), (7, "F"), (8, "H"), (9, "J")]:
            fmt = FMT1 if col_i in (8, 9) else FMT3
            s.formula(
                col_i,
                f"=SUMIF({rng_cod},A{s.r},'08_municipios'!${src}${first_m}:${src}${last_m})",
                fmt,
            )
        s.r += 1
    last_c = s.r - 1
    s.write(2, "SOMA dos 23", font=FONT_TOTAL)
    for col_i, letter in [(3, "C"), (4, "D"), (5, "E"), (6, "F"), (7, "G"), (8, "H"), (9, "I")]:
        s.formula(col_i, f"=SUM({letter}{first_c}:{letter}{last_c})", FMT3 if col_i < 8 else FMT1, total=True)
    r_soma_corede = s.r
    ws.cell(r_corede_total_cell, 2, f"=C{r_soma_corede}")
    ws.cell(r_corede_total_cell, 2).number_format = FMT1
    ws.cell(r_corede_total_cell, 2).font = FONT_TOTAL
    ws.cell(r_corede_total_cell, 2).fill = FILL_TOTAL
    ws.cell(r_corede_pct, 2, f"=B{r_corede_total_cell}/transbordo")
    ws.cell(r_corede_pct, 2).number_format = FMTP
    ws.cell(r_corede_pct, 2).font = FONT_TOTAL
    ws.cell(
        r_corede_conf,
        2,
        f"=SUMIF('08_municipios'!$I${first_m}:$I${last_m},1,'08_municipios'!$G${first_m}:$G${last_m})-C{r_soma_corede}",
    )
    ws.cell(r_corede_conf, 2).number_format = FMT6
    ws.cell(r_corede_conf, 2).font = FONT_TOTAL
    s.r += 2
    s.write(1, "Santa Cruz do Sul, só transbordamento")
    s.formula(2, f"=SUMIF({rng_cod},{SEDE},'08_municipios'!$G${first_m}:$G${last_m})", FMT1)
    s.r += 1
    s.write(1, "COREDE sem a sede")
    s.formula(2, f"=B{r_corede_total_cell}-B{s.r - 1}", FMT1)
    s.r += 1
    s.write(1, "Resto do Estado")
    s.formula(2, f"=transbordo-B{r_corede_total_cell}", FMT1)

    # ------------------------------------------------------------------ 10
    ws = wb.create_sheet("10_top15")
    s = Sheet(
        ws,
        "Quinze municípios mais azuis",
        "R$ milhões de 2025. O valor é MAIOR da coluna de transbordamento da aba 08. Nome e componentes vêm de ÍNDICE/CORRESP.",
        "Nada nesta aba foi redigitado a partir do relatório. Se a aba 08 mudar, esta lista muda.",
    )
    s.widths({
        "A": 8, "B": 28, "C": 24, "D": 12, "E": 14, "F": 14, "G": 14, "H": 14, "I": 12,
    })
    s.headers([
        "Ordem", "Município", "Transbordamento (R$ mi)", "% do Estado",
        "Folha", "Indústria", "Serviços", "Induzido", "COREDE",
    ])
    g_rng = f"'08_municipios'!$G${first_m}:$G${last_m}"
    b_rng = f"'08_municipios'!$B${first_m}:$B${last_m}"
    first_top = s.r
    for k in range(1, 16):
        s.formula(1, f"=ROW()-{s.r - k}", FMTI) if False else s.write(1, k, fmt="0")
        s.formula(3, f"=LARGE({g_rng},{k})", FMT3)
        s.formula(2, f"=INDEX({b_rng},MATCH(C{s.r},{g_rng},0))")
        s.formula(4, f"=C{s.r}/transbordo", FMTP)
        for col_i, src in [(5, "C"), (6, "D"), (7, "E"), (8, "F"), (9, "I")]:
            fmt = "0" if col_i == 9 else FMT3
            s.formula(
                col_i,
                f"=INDEX('08_municipios'!${src}${first_m}:${src}${last_m},MATCH(C{s.r},{g_rng},0))",
                fmt,
            )
        s.r += 1
    last_top = s.r - 1
    s.write(2, "Soma dos 15", font=FONT_TOTAL)
    s.formula(3, f"=SUM(C{first_top}:C{last_top})", FMT3, total=True)
    s.formula(4, f"=C{s.r}/transbordo", FMTP, total=True)

    # ------------------------------------------------------------------ 11
    ws = wb.create_sheet("11_fontes")
    s = Sheet(
        ws,
        "Fontes",
        "Cada linha é uma fonte usada na conta. A planilha da MIP não está neste arquivo.",
        "A trilha de reprodução são os dois scripts citados na última linha e os CSV em estudo/resultados e estudo/espacial.",
    )
    s.widths({"A": 8, "B": 42, "C": 88, "D": 36})
    s.headers(["#", "Fonte", "O que sustenta", "Onde na planilha"])
    fontes = [
        ("1", "DEE/SPGG e UFRJ, MIP-RS 2019, 117 × 52", "Inversa de Leontief, coeficientes, TRU-16. L conferida com a tabela 14, desvio da ordem de 1e-15, em estudo/scripts/calcular_impacto.py. https://dee.rs.gov.br/matriz-insumo-produto", "Abas 03, 04 e 05"),
        ("2", "IBGE, SIDRA 1737, IPCA", "Dezembro de 2019: 5.320,25. Dezembro de 2025: 7.403,29. φ = 0,7186.", "Aba 00, célula nomeada phi"),
        ("3", "IBGE, SIDRA 1612, PAM 2025, fumo em folha", "Produção municipal, produto 2703, variável 214. Regra de 0,86% das premissas.", "Aba 08, toneladas"),
        ("4", "IBGE, SIDRA 6450, CEMPRE 2021", "Emprego setorial municipal, peso do fornecedor. Série encerrada em 2021. Célula suprimida entra como zero.", "Nota de método; peso já aplicado no CSV"),
        ("5", "IBGE, SIDRA 1849, PIA-Empresa 2023", "Folha da divisão 12 no RS, leitura salarial. A premissa de R$ 150 mil permanece.", "Aba 01"),
        ("6", "IBGE, SIDRA 10329, Censo 2022", "Ocupados que trabalham no próprio município e os que trabalham em outro. Base da residência π.", "Nota de método; π já aplicado no CSV"),
        ("7", "IBGE, SIDRA 4709, Censo 2022", "População residente. Leitura territorial do tributo de R$ 480 mi: 3,9% no COREDE.", "Aba 07"),
        ("8", "Banco Central, PTAX venda, média de 2025", "Dólar R$ 5,5855. Euro R$ 6,3085.", "Aba 06"),
        ("9", "Premissas, revisão 4, 18/10/2026", "Receita, insumos, VA direto, ocupações, folha, tributos de memória, bloco II e rampa 2028/2032/2037.", "Aba 01 e aba 07"),
        ("10", "PMI, indicadores de manufatura 2022 e comunicados de fábrica", "Energia e água de referência. Papastratos, Crespellano e Dresden como régua de CAPEX.", "Abas 02 e 06"),
        ("11", "Lei 15.642/2021 e FUNDOPEM/INTEGRAR, RN até 11/2025", "Hipótese de 30% por 96 meses, sem INTEGRAR. Plano Rio Grande, FUNDOPEM Recupera Avança.", "Aba 07"),
        ("12", "Prefeitura de Santa Cruz do Sul, item 7.02", "ISS de 2% sobre metade da parcela local da obra.", "Abas 06 e 07"),
        ("13", "COREDE Vale do Rio Pardo, estatuto art. 3º e Plano 2022–2030", "Lista fechada dos 23 municípios.", "Aba 09"),
        ("14", "Censo 2010, Revista Jovens Pesquisadores, UNISC, 2015", "Conferência da residência: 91,8% na sede. Fora do insumo do mapa.", "Nota de método"),
        ("15", "estudo/scripts/calcular_impacto.py", "Cadeia, induzido, obra e fiscal do cenário base.", "Abas 04, 05, 06 e 07"),
        ("16", "estudo/espacial/alocar_transbordamento.py", "Regionalização dos 497 municípios. λ = 100 km, α = 0,5.", "Aba 08"),
    ]
    for n, fonte, sustenta, onde in fontes:
        s.write(1, n)
        s.write(2, fonte, font=FONT_TOTAL)
        s.write(3, sustenta)
        s.write(4, onde)
        ws.row_dimensions[s.r].height = 36
        s.r += 1

    # freeze header consistency: 00 sheet text rows
    wb.calculation.calcMode = "auto"
    wb.calculation.fullCalcOnLoad = True
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"xlsx {OUT}")
    print(f"conf_municipal em 08!B{r_conf_mun}")
    print(f"municipios {first_m}-{last_m} sede {sede_row} total {r_tot_m}")
    print(f"phi 00!B{row_phi} ancora 02!B{r_ancora} tot bom F{r_tot_bom}")


if __name__ == "__main__":
    main()
