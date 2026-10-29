#!/usr/bin/env python3
"""Build the manuscript while preserving the supplied references.bib verbatim."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent


def run(command, cwd, env=None):
    result = subprocess.run(command, cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(result.stdout[-12000:])
    return result.stdout


def prepare_bibliography(destination):
    # Remove redundant separators in a temporary build copy, never the source.
    removed = 0
    previous = ''
    with (ROOT / 'references.bib').open() as source, destination.open('w') as out:
        for line in source:
            if line.strip() == ',' and previous.rstrip().endswith(','):
                removed += 1
                continue
            out.write(line)
            if line.strip():
                previous = line
    return removed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--style-dir', type=Path,
                        help='Directory containing the official neurips_2025.sty')
    parser.add_argument('--bibliography-only', action='store_true',
                        help='Generate template.bbl without requiring the style')
    args = parser.parse_args()
    if not args.bibliography_only:
        local = ROOT / 'neurips_2025.sty'
        explicit = args.style_dir / 'neurips_2025.sty' if args.style_dir else None
        found = subprocess.run(['kpsewhich', 'neurips_2025.sty'],
                               stdout=subprocess.PIPE, text=True).stdout.strip()
        if not (local.exists() or (explicit and explicit.exists()) or found):
            parser.error('Official neurips_2025.sty is missing. Supply it in this '
                         'directory or use --style-dir. The conference style is '
                         'preserved; no replacement style is used.')
    with tempfile.TemporaryDirectory(prefix='vl_rethinker_') as temporary:
        build = Path(temporary)
        removed = prepare_bibliography(build / 'references.bib')
        source = (ROOT / 'template.tex').read_text()
        (build / 'template.tex').write_text(source)
        for directory in ('figures', 'figure', 'code'):
            if (ROOT / directory).exists():
                (build / directory).symlink_to(ROOT / directory,
                                               target_is_directory=True)
        style = (args.style_dir or ROOT) / 'neurips_2025.sty'
        if style.exists():
            shutil.copy2(style, build / style.name)
        if args.bibliography_only:
            keys = []
            for group in re.findall(r'\\cite\w*\*?(?:\[[^\]]*\]){0,2}\{([^}]+)\}', source):
                for key in group.split(','):
                    key = key.strip()
                    if key not in keys:
                        keys.append(key)
            (build / 'template.aux').write_text(
                '\\relax\n\\citation{' + ','.join(keys) + '}\n'
                '\\bibstyle{unsrtnat}\n\\bibdata{references}\n')
            run(['bibtex', 'template'], build)
        else:
            command = ['pdflatex', '-interaction=nonstopmode', '-halt-on-error',
                       'template.tex']
            run(command, build)
            run(['bibtex', 'template'], build)
            run(command, build)
            output = run(command, build)
            shutil.copy2(build / 'template.pdf', ROOT / 'template.pdf')
            shutil.copy2(build / 'template.log', ROOT / 'template.log')
            match = re.search(r'Output written on.*?\((\d+) pages?', output, re.S)
            print('Built template.pdf' + (f' ({match[1]} pages)' if match else ''))
        shutil.copy2(build / 'template.bbl', ROOT / 'template.bbl')
        print(f'Generated template.bbl; skipped {removed} duplicate separators '
              'in the temporary bibliography copy. Source references.bib unchanged.')


if __name__ == '__main__':
    main()
