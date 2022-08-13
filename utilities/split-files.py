from pathlib import Path
import json5
import argparse
import pandas as pd
import numpy as np
import warnings


parser = argparse.ArgumentParser()
parser.add_argument('target', type=Path)
parser.add_argument('outdir', type=Path)
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
    with args.target.open('r', encoding='utf-8') as f:
        texts = json5.load(f)
    print(args.overwrite)
    for x in texts:
        with args.outdir.joinpath(f'{x["id"]}-{params["general"]["lang"]}.json') as fp:
            if args.overwrite:
                if fp.exists():
                    print(f"""{fp} already exists but overwrite now""")
                else:
                    print(f"""write to {fp}""")
                with fp.open('w', encoding='utf-8') as f:
                    json5.dump(x, f, ensure_ascii=False, indent=2, quote_keys=True, skipkeys=True, trailing_commas=False)
            else:
                if fp.exists():
                    print(f"""{fp} already exists. skip to write""")
                else:
                    with fp.open('w', encoding='utf-8') as f:
                        json5.dump(x, f, ensure_ascii=False, indent=2, quote_keys=True, skipkeys=True, trailing_commas=False)
                    print(f"""write to {fp}""")
