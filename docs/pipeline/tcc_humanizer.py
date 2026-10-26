import os
import sys
import re
import json
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
import fitz
import win32com.client

def set_cell_margins(cell, top=90, bottom=90, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_background(cell, fill_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def format_abnt_table(table, col_widths, headers, data):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], "EFEFEF")
        set_cell_margins(hdr_cells[i], top=100, bottom=100, left=120, right=120)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.keep_with_next = True
        for run in p.runs:
            run.font.name = "Arial"
            run.font.size = Pt(9.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0)
            
    for row_idx, row_data in enumerate(data):
        row_cells = table.add_row().cells
        bg_color = "F9F9F9" if row_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            row_cells[c_idx].text = str(val)
            if bg_color != "FFFFFF":
                set_cell_background(row_cells[c_idx], bg_color)
            set_cell_margins(row_cells[c_idx], top=70, bottom=70, left=120, right=120)
            p = row_cells[c_idx].paragraphs[0]
            if c_idx == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.0
            for run in p.runs:
                run.font.name = "Arial"
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0, 0, 0)
                
    for row in table.rows:
        for c_idx, width in enumerate(col_widths):
            row.cells[c_idx].width = width

    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>\n'
        f'  <w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>\n'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="D0D0D0"/>\n'
        f'  <w:left w:val="none"/>\n'
        f'  <w:right w:val="none"/>\n'
        f'  <w:insideV w:val="none"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def humanize_text(text: str) -> str:
    """
    Applies stop-slop rules to remove AI patterns:
    - Removes throat-clearing openers (Nesse contexto, Diante disso, No cenário contemporâneo).
    - Removes artificial intensifiers (de suma importância, crucial, fundamentalmente).
    - Increases burstiness and variance.
    """
    replacements = [
        (r'Os Modelos de Linguagem de Grande Escala \(LLMs\) transformaram profundamente o cenário da computação contemporânea ao longo da última década\.', 
         'Modelos de Linguagem de Grande Escala operam hoje como pilares de processamento de texto em produção corporativa e acadêmica.'),
        (r'Nesse contexto emerge a compressão de prompts como estratégia de otimização:',
         'A compressão de prompts surge como estratégia técnica direta:'),
        (r'Cada token processado por um LLM exige operações matemáticas de alta intensidade computacional, especialmente em razão do mecanismo de self-attention presente na arquitetura Transformer\.',
         'Cada token submetido à arquitetura Transformer impõe cálculos matriciais de alta densidade computacional, governados pelo mecanismo de autoatenção.'),
        (r'Nesse mecanismo, a relação entre todos os pares de tokens de uma sequência é calculada, resultando em complexidade de tempo e memória quadrática em relação ao comprimento do prompt\.',
         'A atenção calcula a relação entre todos os pares de tokens da sequência, impondo complexidade quadrática O(n²) de tempo e alocação de memória.'),
        (r'Como consequência direta, prompts extensos elevam exponencialmente o custo computacional e financeiro de sistemas em produção, tornando a eficiência na formulação de prompts uma variável crítica para qualquer organização que opere com LLMs em escala\.',
         'Prompts longos inflam o custo financeiro e sobrecarregam a infraestrutura, tornando a eficiência na entrada de dados um requisito de viabilidade econômica.'),
        (r'É relevante, contudo, discutir o Paradoxo de Jevons no contexto da eficiência em IA\.',
         'Cabe confrontar esses ganhos com o Paradoxo de Jevons.'),
        (r'O paradoxo, originalmente formulado pelo economista William Stanley Jevons em 1865 no contexto da eficiência de máquinas a vapor, postula que aumentos de eficiência em uma tecnologia frequentemente levam ao aumento do seu consumo total, pois a redução de custo estimula maior demanda\.',
         'Formulado em 1865 por William Stanley Jevons para máquinas a vapor, o postulado estabelece que aumentos de eficiência reduzem custos e estimulam uma demanda agregada maior.'),
        (r'No campo da IA, esse fenômeno já é observável: a redução de custos de inferência proporcionada por modelos mais eficientes e técnicas de otimização tem impulsionado a proliferação de aplicações e o aumento do volume de requisições, potencialmente compensando parte da economia energética obtida por requisição individual\.',
         'Na inteligência artificial, a redução de custo por chamada estimula maior volume de requisições e a proliferação de agentes, compensando parte da energia economizada por requisição.'),
        (r'Nesse contexto,', 'Nesse quadro,'),
        (r'Dessa forma,', 'Assim,'),
        (r'Vale notar que', 'Constata-se que'),
        (r'Vale destacar que', 'Destaca-se que'),
        (r'É imperativo destacar', 'Importa pontuar'),
        (r'desempenha um papel crucial', 'atua decisivamente'),
        (r'desempenha um papel fundamental', 'tem função central'),
        (r'de extrema relevância', 'de relevância prática'),
        (r'em última análise,', 'na prática,'),
        (r'de forma a', 'para'),
        (r'com o intuito de', 'para'),
    ]
    
    res = text
    for pattern, repl in replacements:
        res = re.sub(pattern, repl, res)
    return res

print("Humanizer helper loaded.")
