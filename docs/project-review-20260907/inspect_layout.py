"""Rasterize Word-exported PDFs and report page content for document QA."""
from pathlib import Path
import json
import sys
import subprocess
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding='utf-8')
report=[]
for path in sorted((ROOT/'qa').glob('*/*.pdf')):
    pdf=PdfReader(path)
    subprocess.run([
        'C:/Users/CapooSenor/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe',
        '-r', '108', '-png', str(path), str(path.parent/'page')
    ],check=True)
    pages=[]
    for i,p in enumerate(pdf.pages):
        text=p.extract_text()
        pages.append({'page':i+1,'chars':len(text),'start':text[:150],'end':text[-180:]})
    report.append({'file':path.stem,'page_count':len(pdf.pages),'pages':pages})
(ROOT/'qa'/'layout.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
