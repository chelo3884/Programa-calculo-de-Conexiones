"""Escritor mínimo de .docx (WordprocessingML) sin dependencias: títulos, párrafos, listas, tablas con colores e imágenes PNG.

build(bloques, titulo_pie) → bytes del archivo .docx (A4, márgenes de 2 cm). Los bloques son diccionarios:
  {"t": "h", "n": 1..3, "text"}                       título
  {"t": "p", "text", "b", "i", "sz", "color", "al"}   párrafo (al: left | center | right)
  {"t": "ul", "items": [texto, ...]}                  viñetas
  {"t": "table", "rows": [[celda, ...], ...], "w": [pesos]}   celda: {"text", "b", "bg", "color", "al", "span", "sz"}
  {"t": "imgs", "items": [{"png": base64, "w": px, "h": px}], "cm": ancho_total_cm}   imágenes en una misma línea
  {"t": "pb"}                                          salto de página
"""
from __future__ import annotations

import base64
import struct
import zipfile
from io import BytesIO
from xml.sax.saxutils import escape

ANCHO = 9638          # twips útiles (A4 con márgenes de 2 cm)
EMU_CM = 360000
NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')


def _t(s):
    return escape(str(s)).replace("\u0000", "")


def _run(text, b=False, i=False, sz=None, color=None):
    pr = ""
    if b:
        pr += "<w:b/>"
    if i:
        pr += "<w:i/>"
    if color:
        pr += f'<w:color w:val="{color.lstrip("#")}"/>'
    if sz:
        pr += f'<w:sz w:val="{int(sz * 2)}"/><w:szCs w:val="{int(sz * 2)}"/>'
    return f'<w:r>{"<w:rPr>" + pr + "</w:rPr>" if pr else ""}<w:t xml:space="preserve">{_t(text)}</w:t></w:r>'


def _par(text, b=False, i=False, sz=None, color=None, al="left", style=None, ind=None, space_after=80, keep=False):
    ppr = (f'<w:pStyle w:val="{style}"/>' if style else "") + ("<w:keepNext/>" if keep else "")
    ppr += f'<w:spacing w:after="{space_after}"/>'
    if ind:
        ppr += f'<w:ind w:left="{ind}" w:hanging="220"/>'
    if al != "left":
        ppr += f'<w:jc w:val="{ {"right": "right", "center": "center"}.get(al, "left") }"/>'
    return f"<w:p><w:pPr>{ppr}</w:pPr>{_run(text, b, i, sz, color) if text != '' else ''}</w:p>"


def _png_dims(raw):
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("la imagen no es PNG")
    return struct.unpack(">II", raw[16:24])


def _cell(c, ancho, borde=True):
    if isinstance(c, str):
        c = {"text": c}
    span = int(c.get("span", 1))
    tcpr = f'<w:tcW w:w="{ancho}" w:type="dxa"/>'
    if span > 1:
        tcpr += f'<w:gridSpan w:val="{span}"/>'
    if c.get("bg"):
        tcpr += f'<w:shd w:val="clear" w:color="auto" w:fill="{c["bg"].lstrip("#")}"/>'
    tcpr += '<w:tcMar><w:top w:w="30" w:type="dxa"/><w:bottom w:w="30" w:type="dxa"/></w:tcMar><w:vAlign w:val="center"/>'
    p = _par(c.get("text", ""), c.get("b", False), False, c.get("sz", 8.5), c.get("color"), c.get("al", "left"), space_after=0)
    return f"<w:tc><w:tcPr>{tcpr}</w:tcPr>{p}</w:tc>"


def _tabla(b):
    rows = b["rows"]
    ncol = max(sum(int((c if isinstance(c, dict) else {}).get("span", 1)) for c in r) for r in rows)
    w = list(b.get("w") or [1] * ncol)
    w = (w + [1] * ncol)[:ncol]
    tot = sum(w)
    tw = [max(300, int(ANCHO * x / tot)) for x in w]
    grid = "".join(f'<w:gridCol w:w="{x}"/>' for x in tw)
    out = ['<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>'
           + "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="D5DBE3"/>' for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
           + '</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="70" w:type="dxa"/><w:right w:w="70" w:type="dxa"/></w:tblCellMar></w:tblPr>'
           + f"<w:tblGrid>{grid}</w:tblGrid>"]
    for ri, r in enumerate(rows):
        trpr = "<w:trPr><w:cantSplit/>" + ("<w:tblHeader/>" if ri == 0 and b.get("header", True) else "") + "</w:trPr>"
        cells, k = [], 0
        for c in r:
            span = int((c if isinstance(c, dict) else {}).get("span", 1))
            cells.append(_cell(c, sum(tw[k:k + span])))
            k += span
        while k < ncol:
            cells.append(_cell("", tw[k]))
            k += 1
        out.append(f"<w:tr>{trpr}{''.join(cells)}</w:tr>")
    out.append("</w:tbl>")
    return "".join(out) + _par("", space_after=60)


def build(bloques, titulo_pie="Memoria de cálculo de conexiones metálicas"):
    cuerpo, medios, rels = [], [], []

    def imagen(png_b64, w_px, h_px, ancho_cm):
        raw = base64.b64decode(png_b64.split(",")[-1])
        pw, ph = _png_dims(raw)
        idx = len(medios) + 1
        medios.append(raw)
        rid = f"rIdImg{idx}"
        rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image{idx}.png"/>')
        cx = int(ancho_cm * EMU_CM)
        cy = int(cx * ph / pw)
        return (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
                f'<wp:docPr id="{idx}" name="Imagen {idx}"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{idx}" name="image{idx}.png"/><pic:cNvPicPr/></pic:nvPicPr>'
                f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
                f"</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>")

    for b in bloques:
        t = b.get("t")
        if t == "h":
            cuerpo.append(_par(b["text"], style=f"Heading{min(3, max(1, int(b.get('n', 1))))}", keep=True))
        elif t == "p":
            cuerpo.append(_par(b.get("text", ""), b.get("b"), b.get("i"), b.get("sz"), b.get("color"), b.get("al", "left")))
        elif t == "ul":
            for it in b["items"]:
                cuerpo.append(_par("•  " + it, sz=9.5, ind=360, space_after=40))
        elif t == "table":
            cuerpo.append(_tabla(b))
        elif t == "imgs":
            its = b["items"]
            if its:
                total = float(b.get("cm", 17))
                cm = (total - 0.2 * (len(its) - 1)) / len(its)
                cuerpo.append('<w:p><w:pPr><w:spacing w:after="80"/></w:pPr>'
                              + '<w:r><w:t xml:space="preserve"> </w:t></w:r>'.join(imagen(i["png"], i.get("w"), i.get("h"), cm) for i in its) + "</w:p>")
        elif t == "pb":
            cuerpo.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
    sect = ('<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter"/><w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="567" w:footer="567" w:gutter="0"/></w:sectPr>')
    documento = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>{"".join(cuerpo)}{sect}</w:body></w:document>'
    estilos = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
               '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/><w:sz w:val="20"/><w:szCs w:val="20"/>'
               '<w:lang w:val="es-EC"/></w:rPr></w:rPrDefault></w:docDefaults>'
               '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
               + "".join(f'<w:style w:type="paragraph" w:styleId="Heading{n}"><w:name w:val="heading {n}"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/>'
                         f'<w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="{300 - 60 * n}" w:after="100"/><w:outlineLvl w:val="{n - 1}"/>'
                         f'{"<w:pBdr><w:bottom w:val=" + chr(34) + "single" + chr(34) + " w:sz=" + chr(34) + "8" + chr(34) + " w:space=" + chr(34) + "1" + chr(34) + " w:color=" + chr(34) + "1F4E8C" + chr(34) + "/></w:pBdr>" if n == 2 else ""}'
                         f'</w:pPr><w:rPr><w:b/><w:color w:val="1F4E8C"/><w:sz w:val="{[40, 28, 23][n - 1]}"/><w:szCs w:val="{[40, 28, 23][n - 1]}"/></w:rPr></w:style>'
                         for n in (1, 2, 3))
               + "</w:styles>")
    pie = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {NS}><w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
           f'{_run(titulo_pie + "  ·  página ", sz=8, color="667085")}'
           '<w:r><w:rPr><w:sz w:val="16"/><w:color w:val="667085"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
           '<w:r><w:rPr><w:sz w:val="16"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
           '<w:r><w:rPr><w:sz w:val="16"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')
    doc_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                '<Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
                + "".join(rels) + "</Relationships>")
    tipos = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
             '<Default Extension="png" ContentType="image/png"/>'
             '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
             '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
             '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
             '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>')
    raiz = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>')
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>' + _t(titulo_pie) + "</dc:title><dc:creator>Conexiones metálicas</dc:creator></cp:coreProperties>")
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", tipos)
        z.writestr("_rels/.rels", raiz)
        z.writestr("docProps/core.xml", core)
        z.writestr("word/document.xml", documento)
        z.writestr("word/styles.xml", estilos)
        z.writestr("word/footer1.xml", pie)
        z.writestr("word/_rels/document.xml.rels", doc_rels)
        for i, raw in enumerate(medios, 1):
            z.writestr(f"word/media/image{i}.png", raw)
    return buf.getvalue()
