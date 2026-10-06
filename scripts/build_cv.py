"""Build cv.pdf from cv-source.md with ReportLab and embedded serif fonts.

Usage: python scripts/build_cv.py [--output output/pdf/Hoonki_Yeo_CV.pdf]
Requires reportlab. Set CV_FONT_DIR if Liberation Serif is not installed locally.
"""

from pathlib import Path
import argparse
import html
import os
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, KeepTogether, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, default=ROOT / 'cv.pdf')
args = parser.parse_args()
font_dirs = [
    Path(os.environ['CV_FONT_DIR']) if 'CV_FONT_DIR' in os.environ else Path('/nonexistent'),
    Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fonts/truetype',
    Path('/usr/share/fonts/truetype/liberation2'),
    Path('/usr/share/fonts/truetype/liberation'),
]
font_dir = next((p for p in font_dirs if (p / 'LiberationSerif-Regular.ttf').exists()), None)
if font_dir is None:
    raise SystemExit('Install Liberation Serif fonts or set CV_FONT_DIR to their directory.')
for name, filename in [
    ('CVSerif', 'LiberationSerif-Regular.ttf'),
    ('CVSerif-Bold', 'LiberationSerif-Bold.ttf'),
    ('CVSerif-Italic', 'LiberationSerif-Italic.ttf'),
    ('CVSerif-BoldItalic', 'LiberationSerif-BoldItalic.ttf'),
]:
    pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
pdfmetrics.registerFontFamily('CVSerif', normal='CVSerif', bold='CVSerif-Bold', italic='CVSerif-Italic', boldItalic='CVSerif-BoldItalic')

INK = colors.HexColor('#17212d')
MUTED = colors.HexColor('#485463')
LINK = '#193f65'
WIDTH, HEIGHT = letter
MARGIN = 49
CONTENT = WIDTH - 2 * MARGIN
styles = {
    'body': ParagraphStyle('body', fontName='CVSerif', fontSize=11, leading=14.2, textColor=INK, spaceAfter=4),
    'name': ParagraphStyle('name', fontName='CVSerif-Bold', fontSize=27, leading=31, textColor=INK, spaceAfter=8),
    'contact': ParagraphStyle('contact', fontName='CVSerif', fontSize=10.3, leading=13.5, textColor=MUTED, spaceAfter=2),
    'entry': ParagraphStyle('entry', fontName='CVSerif-Bold', fontSize=11.5, leading=14.5, textColor=INK),
    'date': ParagraphStyle('date', fontName='CVSerif', fontSize=10.2, leading=14.5, textColor=MUTED, alignment=TA_RIGHT),
    'meta': ParagraphStyle('meta', fontName='CVSerif', fontSize=10.6, leading=13.5, textColor=MUTED),
    'bullet': ParagraphStyle('bullet', fontName='CVSerif', fontSize=11, leading=14.2, textColor=INK, leftIndent=11, firstLineIndent=0, bulletIndent=0, spaceAfter=5),
}

def markup(text):
    text = html.escape(text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: f'<link href="{m[2]}" color="{LINK}">{m[1]}</link>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    return text

def para(text, kind='body'):
    return Paragraph(markup(text), styles[kind])

class Section(Flowable):
    def __init__(self, title):
        super().__init__()
        self.title = title.upper()
        self.height = 29
        self.keepWithNext = True

    def wrap(self, available_width, available_height):
        self.width = available_width
        return self.width, self.height

    def draw(self):
        self.canv.setFillColor(INK)
        self.canv.setFont('CVSerif-Bold', 11.8)
        self.canv.drawString(0, 10, self.title)
        self.canv.setStrokeColor(colors.HexColor('#738092'))
        self.canv.setLineWidth(.5)
        self.canv.line(0, 4, self.width, 4)

def split_row(text, main_style, right_width=164):
    left, sep, right = text.partition(' | ')
    if not sep:
        return para(left, main_style)
    t = Table([[para(left, main_style), para(right, 'date')]], colWidths=[CONTENT-right_width, right_width])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    return t

source = (ROOT / 'cv-source.md').read_text()
updated = re.search(r'<!-- updated: (.*?) -->', source)[1]

def decoration(canvas, doc):
    canvas.saveState()
    canvas.setTitle('Hoonki Yeo - Curriculum Vitae')
    canvas.setAuthor('Hoonki Yeo')
    canvas.setSubject('Academic CV: stochastic and derivative-free optimization')
    if doc.page > 1:
        canvas.setFont('CVSerif-Bold', 12)
        canvas.setFillColor(INK)
        canvas.drawString(MARGIN, HEIGHT - 38, 'Hoonki Yeo')
        canvas.setStrokeColor(colors.HexColor('#c7cdd4'))
        canvas.setLineWidth(.4)
        canvas.line(MARGIN, HEIGHT-46, WIDTH-MARGIN, HEIGHT-46)
    canvas.setFont('CVSerif', 9)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, 29, f'Updated {updated}')
    canvas.drawRightString(WIDTH-MARGIN, 29, f'Hoonki Yeo | {doc.page}')
    canvas.restoreState()

doc = BaseDocTemplate(str(args.output), pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=48, bottomMargin=48, allowSplitting=1)
frame = Frame(MARGIN, 48, CONTENT, HEIGHT-103, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates(PageTemplate(id='cv', frames=frame, onPage=decoration))
story = []
entry = []
in_header = False

def flush_entry():
    if entry:
        story.append(KeepTogether(entry[:]))
        entry.clear()

for raw in source.splitlines():
    line = raw.strip()
    if not line or line.startswith('<!-- updated:'):
        continue
    if line == '<!-- pagebreak -->':
        flush_entry(); story.append(PageBreak()); continue
    if line.startswith('# '):
        story.append(para(line[2:], 'name')); in_header = True; continue
    if line.startswith('## '):
        flush_entry(); in_header = False; story.append(Section(line[3:])); continue
    if line.startswith('### '):
        flush_entry(); entry.extend([Spacer(1, 7), split_row(line[4:], 'entry')]); continue
    if in_header:
        story.append(para(line, 'contact')); continue
    if entry:
        if line.startswith('- '):
            entry.append(Paragraph(markup(line[2:]), styles['bullet'], bulletText='•'))
        elif line.startswith('*') and not line.startswith('**'):
            entry.extend([split_row(line, 'meta', 116), Spacer(1, 4)])
        else:
            entry.append(para(line))
    else:
        story.append(para(line))
flush_entry()
args.output.parent.mkdir(parents=True, exist_ok=True)
doc.build(story)
print(args.output)
