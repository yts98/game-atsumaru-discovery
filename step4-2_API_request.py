from bs4 import BeautifulSoup
import itertools
import json
import os
import re
import requests

if not os.path.isfile('data/public.txt') or not os.path.isfile('data/key_valid.txt'):
    exit('Please check public and unlisted game_ids at first.')

if not os.path.isdir('./data/state'):
    os.mkdir('./data/state')

games = []

with open('data/public.txt', 'r') as r, open('data/key_valid.txt', 'r') as rk:
    for line in itertools.chain(r.readlines(), rk.readlines()):
        match = re.search(r'^https://game\.nicovideo\.jp/atsumaru/games/gm([1-9][0-9]*)(?:\?key=([0-9a-f]{12}))?$', line.strip())
        assert isinstance(match, re.Match), line.strip()
        games.append((int(match[1]), match[2]))

games.sort()

# TODO: analyze games to discover more scenes (leafCodes)!

default_leaf_codes = ['__title', '__gameover']
if os.path.isfile('data/leaf_codes.json'):
    with open('data/leaf_codes.json', 'r') as r:
        discovered_leaf_codes = json.load(r)
else:
    discovered_leaf_codes = {
        "25791": ['Title', 'BadEnd'],
    }

headers = {
    'Cache-Control': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}

get_headers = {
    'Cache-Control': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
    'X-Frontend-Id': '39',
    'X-Frontend-Version': '3.464.0',
    'Origin': 'https://game.nicovideo.jp',
    'Referer': 'https://game.nicovideo.jp/',
}

for game_id, key in games:
    game_id = str(game_id)
    if os.path.isfile(f'data/state/state_gm{game_id}.json'):
        continue
    print(f'gm{game_id}')

    response = requests.get(f'https://game.nicovideo.jp/atsumaru/games/gm{game_id}', headers=headers)

    soup = BeautifulSoup(response.text, features='lxml')
    glob_state = json.loads(soup.find(id='stateSerialized')['data-state'])
    if game_id not in discovered_leaf_codes.keys():
        discovered_leaf_codes[game_id] = []
    for effect in glob_state['initialState']['initialState']['effects']['value']['effects']:
        if effect['leafCode'] not in discovered_leaf_codes[game_id]:
            discovered_leaf_codes[game_id].append(effect['leafCode'])
    discovered_leaf_codes[game_id] = list(sorted(set(discovered_leaf_codes[game_id])))

    # getEffects
    # getLeafComments
    leaf_codes = default_leaf_codes
    if game_id in discovered_leaf_codes.keys():
        print(' '.join(discovered_leaf_codes[game_id]))
        leaf_codes.extend(discovered_leaf_codes[game_id])
    for leaf_code in sorted(set(leaf_codes)):
        if key is None:
            with open('data/api_requests.txt', 'a') as a:
                print(f'https://api.game.nicovideo.jp/v1/rpgtkool/games/gm{game_id}/effects/{leaf_code}.json', file=a)
                print(f'https://api.game.nicovideo.jp/v1/rpgtkool/games/gm{game_id}/leafs/{leaf_code}/comments', file=a)
        else:
            with open('data/api_requests.txt', 'a') as a:
                print(f'https://api.game.nicovideo.jp/v1/rpgtkool/games/gm{game_id}/effects/{leaf_code}.json', file=a)
                print(f'https://api.game.nicovideo.jp/v1/rpgtkool/games/gm{game_id}/leafs/{leaf_code}/comments', file=a)
    # getScoreboardRanking
    for board_id in range(1, 30+1):
        if key is None:
            board_url = f'https://api.game.nicovideo.jp/v1/rpgtkool/games/gm{game_id}/scoreboards/{board_id}.json'
        else:
            board_url = f'https://api.game.nicovideo.jp/v1/rpgtkool/games/gm{game_id}/scoreboards/{board_id}.json?wipAccessKey={key}'
        if board_id == 11:
            response = requests.get(board_url, headers=get_headers)
            if response.status_code == 200:
                with open('data/api_requests.txt', 'a') as a:
                    print(board_url, file=a)
            else:
                assert response.status_code == 400
                assert response.json()['meta']['errorMessage'] == 'boardIdが範囲外です'
                break
        else:
            with open('data/api_requests.txt', 'a') as a:
                print(board_url, file=a)

    with open('data/leaf_codes.json', 'w') as w:
        json.dump(discovered_leaf_codes, w, separators=(',', ':'))

    with open(f'data/state/state_gm{game_id}.json', 'w') as w:
        json.dump(glob_state, w, separators=(',', ':'))

discovered_leaf_codes = dict(sorted(discovered_leaf_codes.items(), key=(lambda item: int(item[0]))))

with open('data/leaf_codes.json', 'w') as w:
    json.dump(discovered_leaf_codes, w, separators=(',', ':'))