
# Check if the length of each descriptions exceeds the threshold.
# Currently, when displaying in CJK characters, the text is cut off if it has more than about 60 letters. 
# 文字数チェック
# 現在のデフォルトCJKフォント設定ではアイテムの説明文が60字越えると見切れる

from pathlib import Path
import json5
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('target', type=Path)
parser.add_argument('--max-nchar', type=int, default=60)
args = parser.parse_args()


if __name__ == '__main__':
    with Path(args.target).open("r", encoding='utf-8') as f:
        text = json5.load(f, encoding='utf-8')
    i = 0
    for x in text['items']:
        if len(x['description']) > args.max_nchar:
            print(x['id'], x['name'], len(x['description']))
            i += 1
    print(f"{i} entries found.")
print('----- FINISHED -----')
