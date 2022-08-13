from pathlib import Path
import json5
import argparse
import pandas as pd
import numpy as np
import warnings


parser = argparse.ArgumentParser()
parser.add_argument('target', type=Path)
parser.add_argument('outdir', type=Path)
parser.add_argument('--text-path', type=Path)
parser.add_argument('--category', type=str, default='items')
parser.add_argument('--overwrite', action='store_true', default=False)
parser.add_argument('-v', '--verbose', action='store_true', default=False)

with Path().cwd().joinpath('utilities/params.json') as fp:
    if fp.exists():
        with fp.open('r', encoding='utf-8') as f:
            params = json5.load(f, encoding='utf-8')

if __name__ == '__main__':
    args = parser.parse_args()
    if not args.outdir.exists():
        print(f'{args.outdir} not found. create now.')
        args.outdir.mkdir()

if args.text_path:
    with args.text_path.open('r', encoding='utf-8') as f:
        translation = json5.load(f, encoding='utf-8')[args.category.lower()]
for fp in args.target.rglob('*.json'):
    print(fp)
    with fp.open('r', encoding='utf-8') as f:
        j = json5.load(f, encoding='utf-8')
        j_ = j.copy()
        j = {k: v for k, v in j.items() if k in ['$type', 'id', 'version', 'localizationId']}
        if  j.get('localizationId') is None:
            j['localizationId'] = j['id']
        if args.text_path:
            texts = [x for x in translation if x['id'] == j['localizationId']]
            if len(texts) > 0:
                j['displayName'] = texts[0]['name']
                # j['description'] = texts[0]['description']
            else:
                print(f'!!! {j["id"]} NOT FOUND !!!')
        if j.get('localizationId') == j_.get('localizationId'):
            del j['localizationId']
        if j != j_:
            with args.outdir.joinpath(fp.relative_to(args.target)) as fp:
                if not fp.parent.exists():
                    fp.parent.mkdir(parents=True, exist_ok=True)
                with fp.open('w', encoding='utf-8') as f:
                    json5.dump(
                        j, f,
                        encoding='utf-8', ensure_ascii=False,
                        indent=2, quote_keys=True,
                        skipkeys=True, trailing_commas=False
                    )
