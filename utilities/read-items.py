# REQUIREMENTS: Python >= 3.8, pandas >= 1.0, numpy >= 1.0 json5 >= 0.9.6
#
# USAGE:
#  1. place previous json files in <PREVIOUS VERSION DIRECTORY> if possible
#  2. place previous translated json files in <PREVIOUS VERSION TRANSLATION DIRECTORY> if possible
#  3. exececute the following:
#   python read-items.py --target <MOD DIRECTORY> --out-dir <OUTPUT DIRECTORY>
#   [--previous-translation <PREVIOUS VERSION TRANSLATION DIRECTORY> --previous-origin <PREVIOUS VERSION DIRECTORY>| --overwrite | -v]
#     the script outputs json files which contain minimal fields required for the translation
# python3 .\utilities\read-items.py --target .\Origin\MMP\U10.2-8.3\ --out-dir .\work\MMP-JP\ --previous-origin .\Origin\MMP\U10.2-8.2\ --previous-translation .\MMP-JP\Texts\Text_Japanese.json
# You can also set the arguments to write them in `params.json` and place at the same directory.

from cgitb import text
from pathlib import Path
import json5
import argparse
import pandas as pd
import numpy as np
import warnings


parser = argparse.ArgumentParser()
parser.add_argument('--target', type=Path)
parser.add_argument('--out-dir', type=Path, default=Path().cwd())
parser.add_argument('--previous-translation', type=Path)
parser.add_argument('--previous-origin', type=Path)
parser.add_argument('--overwrite', action='store_true')
parser.add_argument('-v', '--verbose', action='store_true', default=False)

with Path().cwd().joinpath('utilities/params.json') as fp:
    if fp.exists():
        with fp.open('r', encoding='utf-8') as f:
            params = json5.load(f, encoding='utf-8')

if __name__ == '__main__':

    args = parser.parse_args()
    with (Path(__file__).parent if '__file__' in locals() else Path('utilities')).joinpath('params.json') as fp:
        if fp.exists():
            params = json5.load(fp.open('r', encoding='utf-8'), encoding='utf-8')
            params['target'] = Path(params.get('target'))
        
        else:
            params = {}
    
    params.update({k: v for k, v in vars(args).items() if v is not None})
    params = argparse.Namespace(**params)
    params.target = Path(params.target)
    rename_table = {'$type': '$type', 'localizationId': 'id', 'displayName': 'name', 'description': 'description'}
    rename_table = dict(rename_table, **{f'UPDATED_{k}': f'UPDATED_{v}' for k, v in rename_table.items()})
    
    print(f"B&S target dir: {params.target}")
    print(f"Output dir:     {params.out_dir}")
    
    previous_origin_exists =  'previous_origin' in vars(params).keys()
    previous_translation_exists = 'previous_translation' in vars(params).keys()
    entries = {
        'new': {
            'path': Path(params.target),
            'text': {}
        }
    }
    for f in params.attrs.keys():
        entries['new']['text'][f] = []
    if previous_origin_exists:
        entries['previous_origin'] = {
            'path': Path(params.previous_origin),
            'text': {}
        }
        for f in params.attrs.keys():
            entries['previous_origin']['text'][f] = []

    # read each json
    for version in entries.keys():
        for folder in entries[version]['text'].keys():
            for fp in entries[version]['path'].joinpath(f'{folder}').rglob('*.json'):
                if fp.exists():
                    print(fp)
                    with fp.open('r', encoding='utf-8') as f:
                        item = json5.load(f, encoding='utf-8')
                    if params.verbose:
                        print(f"{fp} loaded.")
                else:
                    warnings.warning(f'{fp} not exists!')
                item = {k:v for k, v in item.items() if k in params.attrs[folder]}
                entries[version]['text'][folder] += [item]
        if len(entries[version]['text']['Texts']) != 0:
            entries[version]['text']['Texts'] = [x['texts'] for x in entries[version]['text']['Texts'][0]['textGroups'] if x['id'] == 'Tips'][0]
    
    if previous_translation_exists:
        with Path(params.previous_translation) as fp:
            entries['previous_translation'] = {
                'path': fp
            }
            with fp.open('r', encoding='utf-8') as f:
                tmp =  json5.load(f, encoding='utf-8')
                entries['previous_translation']['text'] = {}
                if 'items' in tmp.keys():
                    entries['previous_translation']['text']['Items'] = tmp['items']
                if 'textGroups' in tmp.keys():
                    textGroupDefault = [x for x in tmp['textGroups'] if x.get('id') == 'Default']
                    if len(textGroupDefault) > 0:
                        entries['previous_translation']['text']['Texts'] = textGroupDefault
                if 'waves' in tmp.keys():
                    entries['previous_translation']['text']['Waves'] = tmp['waves']
    
    # merge and update
    print('--- merging with previous translation text ---')
    for folder in entries['new']['text'].keys():
        print(f'processing {folder}...')
        tmp_fields = vars(params)['attrs'][folder]
        d = pd.DataFrame(entries['new']['text'][folder])
        if folder == 'Texts':
            tmp_fields = ['$type','id', 'text']  # TODO: very UGLY implementation
        
        if previous_origin_exists and len(entries['previous_origin']['text'][folder]) != 0:
            print('reading previous original text')
            d = d.merge(
                pd.DataFrame(entries['previous_origin']['text'][folder]),
                on=[x for x in ['$type', 'id'] if x in d.columns],
                how='left'
            ).assign(
                **{f'UPDATED_{field}': (lambda x: lambda d: d[f'{x}_x'] != d[f'{x}_y'])(field) for field in tmp_fields if field not in ['$type', 'id'] and field in d.columns}
            ).rename(
                columns={f'{field}_x': field for field in tmp_fields if field not in ['$type', 'id']},
                errors='ignore'
            ).drop(
                columns=[elm for sub in [[f'{field}_x', f'{field}_y'] for field in d.columns] for elm in sub], errors='ignore')
        else:
            print('new text entries found')
            for field in [x for x in tmp_fields if x not in ['$type', 'id']]:
                d[f'UPDATED_{field}'] = True
        # grrrr....
        if folder in ["Items", "Waves"]:
            if d.shape[0] > 0:
                d['$type'] = f'ThunderRoad.TextData+{folder.title()[:-1]}, ThunderRoad'
                d = d.drop(columns=['id']).rename(columns=rename_table)
                tmp_fields = set([rename_table.get(x, x) for x in tmp_fields])
        if previous_translation_exists and folder in entries['previous_translation']['text'].keys() and folder != 'Texts': # TODO: なんか更新でjsonの構造がややこしくなったので一旦手動で
            tmp_prev_translation = pd.DataFrame(
                entries['previous_translation']['text'][folder]
            )
            tmp_prev_translation = tmp_prev_translation[[c for c in tmp_fields if c in tmp_prev_translation.columns]]
            if d.shape[0] > 0:
                d = d.merge(
                    tmp_prev_translation,
                    on=[x for x in ['$type', 'id'] if x in d.columns],
                    how='left'
                ).assign(
                    **{f'{field}': (lambda x: lambda d: np.where(
                        d[f'UPDATED_{x}'],
                        d[f'{x}_x'],
                        d[f'{x}_y'].combine_first(d[f'{x}_x'])))(field) for field in tmp_fields if field not in ['$type', 'id', 'version']
                    }
                ).drop(
                    columns=[elm for sub in [[f'{field}_x', f'{field}_y'] for field in tmp_fields] for elm in sub], errors='ignore'
                )
    
        with params.out_dir.joinpath(f'Text-{folder}.json') as fp_out:
            if fp_out.exists() and not params.overwrite:
                print(f'{fp_out} already exists! This file skipped.')
        
            with fp_out.open('w', encoding='utf-8') as f:
                items = [{k: v for k, v in x[1].items() if v != False} for x in d.iterrows()]
                json5.dump(items, f, indent=2, quote_keys=True, trailing_commas=False, ensure_ascii=False)
        
    print("FINISHED")
