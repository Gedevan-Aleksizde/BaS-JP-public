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
from typing import Callable, Dict, TypedDict, List, Hashable
import re

RENAME_MAP = {
    'name': 'name_transl',
    'description': 'description_transl'
}
RENAME_MAP_INV = {
    'name_transl': 'name',
    'description_transl': 'description'
}

DF_TRANSLATION_BLANK = pd.DataFrame(
    [('', '', '', '', '', '')],
    columns=['CATEGORY', 'CATEGORYSUB', 'loc_id', 'name_transl', 'descritpion_transl', 'language']
)

WAVETEXT = TypedDict(
    'WAVETEXT',
    {
        '$type': str,
        'id': str,
        'title': str,
        'descroption':str
    }
)

WAVEENTRY = TypedDict(
    'WAVEENTRY',
    {
        '$type': str,
        'localizationId': str,
        'displayName': str,
        'descroption':str
    }
)


ITEMTEXT = TypedDict(
    'ITEMTEXT',
    {
        '$type': str,
        'id': str,
        'name': str,
        'descroption':str
    }
)


ITEMENTRY = TypedDict(
    'ITEMENTRY',
    {
        '$type': str,
        'localizationId': str,
        'displayName': str,
        'descroption':str
    }
)

TGTEXT = TypedDict(
    'TGTEXT',
    {
        "$type": str,
        "id": str,
        "name": str,
        "description": str,
        "spriteAddress": str,
        "videoAddress": str
    }
)

TEXTGROUP = TypedDict(
    'TEXTGROUP',
    {
        '$type': str,
        'id': str,
        'texts': List[TGTEXT]
    }
)

TEXTJSON = TypedDict(
    'TEXTJSON',
    {
        '$type': str,
        'id': str,
        'textGroups': List[TEXTGROUP],
        'items': List[ITEMTEXT],
        'waves': List[WAVETEXT]
    }

)


def main(params: argparse.Namespace) -> None:
    assert params.target is not None, "???"
    df = search_all_files(params.target, params.language)
    df_transl = parse_translation(params.previous_translation)
    df = merge_user_translation(df, df_transl, params.output_full)
    to_text_json(df, params.language, params.output_path, params.output_full)


def read_translation(json: TEXTJSON) -> pd.DataFrame:
    """
    既に作っておいた言語ファイルのDictを読み込む
    """
    d = read_any_from_text_file(json).rename(columns=RENAME_MAP)
    if 'CATEGORYSUB' not in d.columns:
        d['CATEGORYSUB'] = None
    d = d.drop_duplicates()
    d = d.reset_index(drop=True)
    return d


def parse_translation(fpath: Path) -> pd.DataFrame:
    """
    既に作っておいた言語ファイルのJSONを読み込む
    """
    json = json5.load(fpath.open('r', encoding='utf-8'))
    if 'ThunderRoad.TextData' in json.get('$type'):
        return read_translation(json)
    return DF_TRANSLATION_BLANK


def search_all_files(fpath: Path, language:str, verbose: bool=False) -> pd.DataFrame:
    """
    全JSONを検索してDFにする
    """
    _dats = []
    _dats_text = []
    for jsonfp in fpath.rglob('*.json'):
        j = json5.load(jsonfp.open('r', encoding='utf-8'), encoding='utf-8')
        if verbose:
            print(f'reading {jsonfp}')
        if 'ThunderRoad.WaveData' in j.get('$type'):
            _dats += [read_wave_entry(j)]
        elif 'ThunderRoad.ItemData' in j.get('$type'):
            _dats += [read_item_entry(j)]
        elif 'ThunderRoad.TextData' in j.get('$type'):
            if j.get('id') in (language, 'English'):
                _dats_text += [
                    read_any_from_text_file(j).assign(language=j.get('id'))
                ]
    df_entry = pd.concat(_dats) if len(_dats) > 0 else pd.DataFrame({}, columns=['CATEGORY', 'CATEGORYSUB', 'loc_id', 'name', 'description'])
    if 'CATEGORYSUB' not in df_entry.columns:
        df_entry['CATEGORYSUB'] = None
    df_text = pd.concat(_dats_text) if len(_dats_text) > 0 else DF_TRANSLATION_BLANK
    if 'CATEGORYSUB' not in df_text.columns:
        df_text['CATEGORYSUB'] = None
    df_entry = merge_data(df_entry, df_text, language)
    return df_entry.reset_index(drop=True)


def merge_user_translation(df_entry: pd.DataFrame, df_translation: pd.DataFrame, output_full: bool) -> pd.DataFrame:
    key_columns = ['CATEGORY', 'CATEGORYSUB', 'loc_id']
    if check_duplication(df_entry, key_columns):
        pass
        # df_entry = df_entry.set_index(key_columns).drop_duplicates(subset=key_columns, ignore_index=True)
    if check_duplication(df_translation, key_columns):
        pass
        # df_translation = df_translation.drop_duplicates(subset=key_columns, ignore_index=True)
        # なぜか何もしてくれない...
    df_entry = (
        df_entry
        .set_index(key_columns)
        .loc[lambda d: ~d.index.duplicated()]
    )
    df_translation = (
        df_translation
        .set_index(key_columns)
        .loc[lambda d: ~d.index.duplicated()]
    )
    if output_full:
        df_entry = df_entry.join(df_translation, how='left')
    else:
        df_entry.update(df_translation)
    return df_entry.reset_index()



def merge_data(df_entry: pd.DataFrame, df_text: pd.DataFrame, language: str) -> pd.DataFrame:
    """
    TextDataとそれ以外の*Dataをマージする
    """
    df_text_en = df_text.loc[lambda d: d['language'] == 'English'].drop(columns='language')
    df_text_transl = df_text.loc[lambda d: d['language'] == language].drop(columns='language')
    df_entry = df_entry.set_index(['CATEGORY', 'CATEGORYSUB', 'loc_id'])
    df_entry.update(df_text_en.set_index(['CATEGORY', 'CATEGORYSUB', 'loc_id']))   # なんで構文統一できないの?
    df_entry = df_entry.reset_index()
    df_entry.merge(df_text_transl.rename(columns=RENAME_MAP), on=['CATEGORY', 'CATEGORYSUB', 'loc_id'])
    return df_entry


def read_jsons_folder(fpath: Path, func: Callable, verbose=False) -> pd.DataFrame:
    dat_ = []
    for jsonpath in fpath.glob('*.json'):
        if verbose:
            print(f""""reading {jsonpath}""")
        dat = func(jsonpath)
        dat_ += [dat]
    if len(dat_) > 0:
        return pd.concat(dat_)
    if verbose:
        print('no item json found...')
    return pd.DataFrame(columns=['loc_id', 'name', 'description', 'CATEGORY'])


def parse_item_entry(fpath: Path) -> pd.DataFrame:
    j = json5.load(fpath.open('r', encoding='utf-8'), encoding='utf-8')
    return read_item_entry(j)


def read_item_entry(json: ITEMENTRY):
    return pd.DataFrame(
        [(json.get('localizationId'), json.get('displayName'), json.get('description'))],
        columns=['loc_id', 'name', 'description']
    ).assign(
        CATEGORY='items'
    )


def read_wave_entry(json: WAVEENTRY) -> pd.DataFrame:
    return pd.DataFrame(
        [(json.get('localizationId'), json.get('title'), json.get('description'))],
        columns=['loc_id', 'name', 'description']
    ).assign(
        CATEGORY='waves'
    )


def parse_wave_entry(fpath: Path) -> pd.DataFrame:
    j = json5.load(fpath.open('r', encoding='utf-8'), encoding='utf-8')
    return read_wave_entry(j)


def parse_items_from_text_json(fpath: Path) -> pd.DataFrame:
    """
    itemsテキストだけDFにする
    """
    j = json5.load(fpath.open('r', encoding='utf-8'), encoding='utf-8')
    if 'items' in j.keys():
        return read_items_from_text_json(j['items'])
    return pd.DataFrame({}, columns=['type', 'loc_id', 'name', 'description', 'CATEGORY'])


def parse_waves_from_text_json(fpath: Path) -> pd.DataFrame:
    """
    waveテキストだけDFにする
    """
    j = json5.load(fpath.open('r', encoding='utf-8'), encoding='utf-8')
    if 'waves' in j.keys():
        return read_waves_from_text_json(j['waves'])
    return pd.DataFrame({}, columns=['type', 'loc_id', 'name', 'description', 'CATEGORY'])


def parse_tgs_from_text_json(fpath: Path) -> pd.DataFrame:
    """
    textGroupsだけDFにする
    """
    j = json5.load(fpath.open('r', encoding='utf-8'), encoding='utf-8')
    if 'textGroups' in j.keys():
        return read_tgs_from_text_json(j['textGroups'])
    return pd.DataFrame({}, columns=['type', 'loc_id', 'name', 'description', 'CATEGORY', 'CATEGORYSUB'])


def read_any_from_text_file(json: TEXTJSON) -> pd.DataFrame:
    """
    text_*.jsonから全て取得する
    """
    _dats = []
    if 'textGroups' in json.keys():
        _dats += [read_tgs_from_text_json(json['textGroups'])]
    if 'waves' in json.keys():
         _dats += [read_waves_from_text_json(json['waves'])]
    if 'items' in json.keys():
        _dats += [read_items_from_text_json(json['items'])]
    return pd.concat(_dats)



def read_items_from_text_json(json: List[ITEMTEXT]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            (v['$type'], v.get('id'), v.get('name'), v.get('description')) for v in json],
            columns=['type', 'loc_id', 'name', 'description'
        ]
    ).assign(CATEGORY = 'items')


def read_waves_from_text_json(json: List[WAVETEXT]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            (v['$type'], v.get('id'), v.get('title'), v.get('description')) for v in json
        ],
        columns=['type', 'loc_id', 'name', 'description']
    ).assign(
        CATEGORY = 'waves'
    )


def read_tgs_from_text_json(jsons: List[TEXTGROUP]) -> pd.DataFrame:
    d_ = []
    for tg in jsons:
        d_ += [
            pd.DataFrame(
                [
                    (
                        entry.get('$type'),
                        entry.get('id'),
                        entry.get('title'),
                        entry.get('description'),
                        entry.get('spriteAddress'),
                        entry.get('videoAddress')
                    ) for entry in tg['texts']], columns=['type', 'loc_id', 'name', 'description', 'spriteAddress', 'videoAddress']
            ).assign(
                CATEGORY='textGroups',
                CATEGORYSUB=tg.get('id')
            )
        ]
    return pd.concat(d_)


def to_text_json(data: pd.DataFrame, language: str, output_path: Path, output_full: bool) -> bool:
    output_json = {
          '$type': "ThunderRoad.TextData, ThunderRoad",
          'id': language,
          'sensitiveContent': 'None',
          'sensitiveFilterBehaviour': 'Discard',
          'version': 1,
    }
    d_tgs = data.loc[lambda d: d['CATEGORY'] == 'textGroups']
    if d_tgs.shape[0] > 0:
        output_json['textGroups'] = to_textgroups_text_json(d_tgs, output_full)
    d_items = data.loc[lambda d: d['CATEGORY'] == 'items']
    if d_items.shape[0] > 0:
        output_json['items'] = to_item_text_json(d_items, output_full)
    d_waves = data.loc[lambda d: d['CATEGORY'] == 'waves']
    if d_waves.shape[0] > 0:
        output_json['waves'] =  to_wave_text_json(d_waves, output_full)
    output_json['groupPath'] = 'null'
    json5.dump(output_json, output_path.open('w', encoding='utf-8'), indent=2, quote_keys=True, trailing_commas=False, ensure_ascii=False)
    return True


def to_wave_text_json(dat: pd.DataFrame, output_full: bool) -> List[WAVETEXT]:
    json = []
    if output_full:
        for _, r in dat.iterrows():
            json += [
                {
                    "$type": "ThunderRoad.TextData+Wave, ThunderRoad",
                    "id": r['loc_id'],
                    "title": r['name_transl'],
                    "title_ORIGINAL": r['name'],
                    "description": r['description_transl'],
                    "description_ORIGINAL": r['description']
                }
            ]
    else:
        for _, r in dat.iterrows():
            json += [
                {
                    "$type": "ThunderRoad.TextData+Wave, ThunderRoad",
                    "id": r['loc_id'],
                    "title": r['name'],
                    "description": r['description']
                }
            ]
    return json


def to_item_text_json(dat: pd.DataFrame, output_full: bool) -> List[ITEMTEXT]:
    json = []
    if output_full:
        for _, r in dat.iterrows():
            json += [
                {
                    "$type": "ThunderRoad.TextData+Item, ThunderRoad",
                    "id": r['loc_id'],
                    "name": r['name_transl'],
                    "name_ORIGINAL": r['name'],
                    "description": r['description_transl'],
                    "description_ORIGINAL": r['description']
                }
            ]
    else:
        for _, r in dat.iterrows():
            json += [
                {
                    "$type": "ThunderRoad.TextData+Item, ThunderRoad",
                    "id": r['loc_id'],
                    "name": r['name'],
                    "description": r['description']
                }
            ]
    return json


def to_textgroups_text_json(dat: pd.DataFrame, output_full: bool) -> List[TEXTGROUP]:
    json = []
    cats = dat['CATEGORYSUB'].unique()
    for cat in cats:
        json_tg = {
            "$type": "ThunderRoad.TextData+TextGroup, ThunderRoad",
            "id": cat,
            'texts': []
        }
        if output_full:
            for _, r in dat.loc[lambda d: d['CATEGORYSUB'] == cat].iterrows():
                json_tg['texts'] += [
                    {
                        "$type": "ThunderRoad.TextData+TextID, ThunderRoad",
                        "id": r['loc_id'],
                        "name": r['text_transl'],
                        "name_ORIGINAL": r['text'],
                        "description": r['description_transl'],
                        "description_ORIGINAL": r['description'],
                        "spriteAddress": r['spriteAddress'],
                        "videoAddress": r['videoAddress']
                    }
                ]
        else:
            for _, r in dat.loc[lambda d: d['CATEGORYSUB'] == cat].iterrows():
                json_tg['texts'] += [
                    {
                        "$type": "ThunderRoad.TextData+TextID, ThunderRoad",
                        "id": r['loc_id'],
                        "name": r['text'],
                        "description": r['description'],
                        "spriteAddress": r['spriteAddress'],
                        "videoAddress": r['videoAddress']
                    }
                ]
        json += [json_tg]
    return json


def check_duplication(data: pd.DataFrame, on: List[str]) -> bool:
    """
    重複があったら内容を標準出力してTrueを返す
    """
    duplications = data.set_index(on)
    duplications = duplications[duplications.index.duplicated()]
    if duplications.shape[0] > 0:
        print(f'--- {duplications.shape[0]} duplicated entries found! ---')
        print(duplications.reset_index())
    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=Path)
    parser.add_argument('--language', type=str)
    parser.add_argument('--out-dir', type=Path, default=Path().cwd())
    parser.add_argument('--previous-translation', type=Path)
    parser.add_argument('--previous-origin', type=Path)
    parser.add_argument('--output-full', action='store_true')
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    # parser.add_argument('--original', action='store_true', default=False)

    fp_params = Path().cwd().joinpath('utilities/params.json')
    if fp_params.exists():
        params = json5.load(fp_params.open('r', encoding='utf-8'), encoding='utf-8')

    args = parser.parse_args()
    if not args.output_full:
        args.output_full = None
    fp_params2 = (Path(__file__).parent if '__file__' in locals() else Path('utilities')).joinpath('params.json')
    if fp_params2.exists():
        params = json5.load(fp_params2.open('r', encoding='utf-8'), encoding='utf-8')
        params['target'] = Path(params.get('target'))
        params['output_full'] = params['output_full'] == 'True'
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

    params.previous_translation = Path(params.previous_translation)
    params.output_path = Path(params.output_path)

    print(params)

    main(params)