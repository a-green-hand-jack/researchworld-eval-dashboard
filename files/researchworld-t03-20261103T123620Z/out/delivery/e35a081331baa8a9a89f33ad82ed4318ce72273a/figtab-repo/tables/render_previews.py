"""Compile the four delivered main tables in a 5.5-inch text block for inspection."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import pymupdf
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'figures'))
from rendering import file_record
NAMES=['study_coverage','primary_rates','reference_assessability','main_compute']
if (ROOT/'tables/background_compute.tex').exists(): NAMES.append('background_compute')

def main():
    outputs=[]
    with tempfile.TemporaryDirectory(prefix='figtab-preview-') as folder:
        for stem in NAMES:
            source=(ROOT/f'tables/{stem}.tex').resolve()
            tex=(r'\documentclass{article}\usepackage[letterpaper,textwidth=5.5in,textheight=9in]{geometry}'
                 r'\usepackage{times,booktabs}\begin{document}'
                 r'\input{'+str(source)+r'}\end{document}')
            task_path=Path(folder)/'table.tex';task_path.write_text(tex)
            result=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error',
                '-output-directory='+folder,str(task_path)],capture_output=True,text=True,check=True)
            if 'Overfull' in result.stdout:
                raise ValueError(f'Overflow in {stem}: inspect LaTeX log')
            pdf=ROOT/f'tables/{stem}.preview.pdf';pdf.write_bytes((Path(folder)/'table.pdf').read_bytes())
            doc=pymupdf.open(pdf)
            if len(doc)!=1:raise ValueError('Table preview did not fit one page')
            png=pdf.with_suffix('.png');doc[0].get_pixmap(matrix=pymupdf.Matrix(1.7,1.7)).save(png)
            outputs.extend([file_record(pdf,ROOT),file_record(png,ROOT)])
    provenance={'command':'python3 tables/render_previews.py',
        'generator':file_record(Path(__file__),ROOT),
        'inputs':[file_record(ROOT/f'tables/{n}.tex',ROOT) for n in NAMES],
        'outputs':outputs,'scope':'Article preview with official-width text block; integrated root PDF needs separate inspection'}
    (ROOT/'tables/main_previews.manifest.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print('Compiled all one-page previews; no overfull boxes. Open each before acceptance.')

if __name__=='__main__':main()
