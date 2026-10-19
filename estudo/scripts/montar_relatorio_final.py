#!/usr/bin/env python3
"""Gera estudo/relatorio_final.html e estudo/relatorio_final.pdf a partir do markdown."""

from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "relatorio_final.md"
HTML_OUT = ROOT / "relatorio_final.html"
PDF_OUT = ROOT / "relatorio_final.pdf"

CSS = r"""
@page {
  size: A4;
  margin: 15mm 13mm 16mm 13mm;
  @top-right {
    content: "Opção 2  ·  MIP Ipea + MIP-RS";
    font-family: "Liberation Sans", sans-serif;
    font-size: 8pt;
    color: #5c6b73;
  }
  @bottom-left {
    content: "Santa Cruz do Sul  ·  ano cheio 2037  ·  R$ de 2025";
    font-family: "Liberation Sans", sans-serif;
    font-size: 8pt;
    color: #5c6b73;
  }
  @bottom-right {
    content: counter(page);
    font-family: "Liberation Sans", sans-serif;
    font-size: 9pt;
    color: #1B3A4B;
  }
}
@page:first {
  margin: 16mm 16mm 16mm 16mm;
  @top-right { content: none; }
  @bottom-left { content: none; }
  @bottom-right { content: none; }
}
html { hyphens: auto; hyphenate-limit-chars: 6 3 3; }
* { box-sizing: border-box; }
body {
  font-family: "Liberation Serif", "DejaVu Serif", serif;
  font-size: 10.6pt;
  line-height: 1.42;
  color: #1B3A4B;
  margin: 0;
}
.capa {
  break-after: page;
  min-height: 250mm;
  padding-top: 28mm;
}
.capa .kicker {
  font-family: "Liberation Sans", sans-serif;
  font-size: 11pt;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #1F7A6B;
  margin: 0 0 10mm;
}
.capa h1 {
  font-family: "Liberation Sans", sans-serif;
  font-size: 22pt;
  line-height: 1.2;
  margin: 0 0 8mm;
  border: none;
  padding: 0;
}
.capa .opcao {
  font-family: "Liberation Sans", sans-serif;
  font-size: 13pt;
  line-height: 1.35;
  margin: 0 0 12mm;
}
.capa ul {
  list-style: none;
  padding: 0;
  margin: 0 0 14mm;
  font-family: "Liberation Sans", sans-serif;
  font-size: 12pt;
}
.capa li {
  border-top: 0.4pt solid #E0DCD3;
  padding: 2.2mm 0;
}
.capa .para {
  font-size: 11pt;
  margin-top: 8mm;
}
#sumario {
  break-after: page;
}
#sumario h2 {
  border: none;
  margin-top: 0;
}
#sumario ul { list-style: none; padding: 0; margin: 4mm 0 0; }
#sumario li { margin: 0; padding: 1.6mm 0; border-bottom: 0.3pt solid #E0DCD3; }
#sumario a {
  color: #1B3A4B;
  text-decoration: none;
  font-family: "Liberation Sans", sans-serif;
  font-size: 11pt;
}
#sumario a::after {
  content: leader(".") target-counter(attr(href), page);
  font-variant-numeric: tabular-nums;
}
h1, h2, h3 { font-family: "Liberation Sans", sans-serif; }
h2 {
  font-size: 13.2pt;
  line-height: 1.25;
  margin: 1.15em 0 0.4em;
  padding-bottom: 0.12em;
  border-bottom: 0.7pt solid #1F7A6B;
  break-after: avoid;
  bookmark-level: 1;
}
h3 {
  font-size: 11.4pt;
  margin: 0.95em 0 0.28em;
  break-after: avoid;
  bookmark-level: 2;
}
p { margin: 0.35em 0 0.55em; }
strong { font-weight: 700; }
a { color: #1B3A4B; overflow-wrap: anywhere; }
ol, ul { margin: 0.3em 0 0.7em; padding-left: 1.15em; }
li { margin: 0.18em 0; }
table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.45em 0 0.8em;
  font-family: "Liberation Sans", sans-serif;
  font-size: 8pt;
  line-height: 1.28;
}
th, td {
  border-bottom: 0.4pt solid #E0DCD3;
  padding: 2.5px 4px;
  vertical-align: top;
  text-align: left;
  overflow-wrap: break-word;
  hyphens: manual;
}
th { background: #F4F7F5; font-weight: 700; }
tr { break-inside: avoid; }
thead { display: table-header-group; }
code {
  font-family: "Liberation Mono", "DejaVu Sans Mono", monospace;
  font-size: 8.4pt;
}
figure {
  margin: 0.5em 0 0.9em;
  break-inside: avoid;
}
figure img {
  display: block;
  width: 100%;
  height: auto;
  margin: 0 auto;
}
figcaption {
  font-family: "Liberation Sans", sans-serif;
  font-size: 8.2pt;
  line-height: 1.3;
  color: #3d4f5a;
  margin-top: 1.5mm;
}
figure.grafico img { width: 96%; }
figure.mapa {
  break-before: page;
  break-inside: avoid;
  margin-top: 0;
}
figure.mapa img { width: 100%; max-height: 232mm; object-fit: contain; }
"""


def build() -> None:
    text = MD.read_text(encoding="utf-8")
    converter = markdown.Markdown(
        extensions=["tables", "toc", "sane_lists"],
        extension_configs={"toc": {"toc_depth": "2-3"}},
    )
    body = converter.convert(text)
    # A capa impressa já carrega o título. O h1 do markdown fica no fonte, fora do miolo.
    if body.startswith("<h1>"):
        body = body.split("</h1>", 1)[1].lstrip()
    toc = converter.toc
    doc = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório final — Opção 2. MIP Ipea + MIP-RS</title>
<style>{CSS}</style>
</head>
<body>
<section class="capa">
  <p class="kicker">Relatório final</p>
  <h1>Impacto econômico da operação de nicotina sem fumaça em Santa Cruz do Sul</h1>
  <p class="opcao">Opção 2. MIP Ipea + MIP-RS</p>
  <ul>
    <li>Santa Cruz do Sul</li>
    <li>Ano cheio 2037</li>
    <li>R$ de 2025</li>
    <li>MIP Ipea 2018, 27 UFs × 68 atividades, com a MIP-RS 2019 na coluna de checagem</li>
    <li>Outubro de 2026</li>
  </ul>
  <p class="para">Para o Governo do Rio Grande do Sul e a equipe econômica. A manchete é o tipo I da MIP Ipea. A obra de 2026–2027 fica em bloco separado. A cor do mapa é o transbordamento no RS.</p>
</section>
<nav id="sumario">
  <h2>Sumário</h2>
  {toc}
</nav>
{body}
</body>
</html>
"""
    HTML_OUT.write_text(doc, encoding="utf-8")
    HTML(filename=str(HTML_OUT), base_url=str(ROOT)).write_pdf(str(PDF_OUT))
    print(f"html {HTML_OUT}")
    print(f"pdf {PDF_OUT} bytes {PDF_OUT.stat().st_size}")


if __name__ == "__main__":
    build()
