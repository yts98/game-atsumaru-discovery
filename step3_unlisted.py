import os
import re
import time
import json
import requests

get_headers = {
    'Cache-Control': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
    'X-Frontend-Id': '39',
    'X-Frontend-Version': '3.464.0',
    'Origin': 'https://game.nicovideo.jp',
    'Referer': 'https://game.nicovideo.jp/',
}

post_headers = {
    'Cache-Control': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
    'X-Frontend-Id': '39',
    'X-Frontend-Version': '3.464.0',
    'X-Request-With': 'https://game.nicovideo.jp',
    'Origin': 'https://game.nicovideo.jp',
    'Referer': 'https://game.nicovideo.jp/',
}

if not os.path.isfile('data/findings_2.json'):
    exit('Please fetch public game_ids at first.')

if os.path.isfile('data/urls_3.txt'):
    exit('Not overwriting data/urls_3.txt .')

if os.path.isfile('data/public.txt'):
    exit('Not overwriting data/public.txt .')

if os.path.isfile('data/public_payment.txt'):
    exit('Not overwriting data/public_payment.txt .')

if os.path.isfile('data/key_valid.txt'):
    exit('Not overwriting data/key_valid.txt .')

if os.path.isfile('data/key_invalid.txt'):
    exit('Not overwriting data/key_invalid.txt .')

findings = {}

with open('data/findings_2.json', 'r') as r:
    findings = json.load(r)
    print(f'total {len(findings["200"]) + len(findings["404"])} found {len(findings["200"]) - len(findings["losts"])} lost {len(findings["losts"])}')

for lost_id in findings['losts']:
    url = f'https://api.game.nicovideo.jp/v1/rpgtkool/games/gm{lost_id}/permission-info.json?sandbox=0'
    response = requests.get(url, headers=get_headers)

    api_response = json.loads(response.text)
    assert api_response['meta']['status'] == 200
    assert api_response['data']['isPaymentRequired'] == True, api_response['data']

unlisted_games = []

with open('data/key_CDX.txt', 'r') as r:
    for line in r.readlines():
        match = re.search(r'^https://game\.nicovideo\.jp/atsumaru/games/gm([1-9][0-9]*)\?key=([0-9a-f]{12})$', line.strip())
        assert isinstance(match, re.Match), line.strip()
        if int(match[1]) in findings['200']:
            print(f'{match[1]} is public now.')
        else:
            assert int(match[1]) in findings['404']
            unlisted_games.append((int(match[1]), match[2]))

with open('data/key_Google.txt', 'r') as r:
    for line in r.readlines():
        match = re.search(r'^https://game\.nicovideo\.jp/atsumaru/games/gm([1-9][0-9]*)\?key=([0-9a-f]{12})$', line.strip())
        assert isinstance(match, re.Match), line.strip()
        if int(match[1]) in findings['200']:
            print(f'{match[1]} is public now.')
        else:
            assert int(match[1]) in findings['404']
            unlisted_games.append((int(match[1]), match[2]))

unlisted_games = sorted(list(dict.fromkeys(unlisted_games)))

game_urls = findings['urls']
unlisted_ids = []
correct_pairs = []
wrong_pairs = []

for game_id, key in unlisted_games:
    url = f'https://api.game.nicovideo.jp/v1/rpgtkool/games/gm{game_id}/play-tickets.json?sandbox=0&wipAccessKey={key}'
    response = requests.post(url, data={}, headers=post_headers)

    api_response = json.loads(response.text)
    if api_response['meta']['status'] == 200:
        version = api_response['data'].get('version')
        assert isinstance(version, int), version
        assert api_response['data'].get('path') == f'/games/gm{game_id}/{version}'
        assert api_response['data'].get('gameUrl') == f'https://resource.game.nicovideo.jp/games/gm{game_id}/{version}/index.html'
        assert api_response['data'].get('gamePath') == f'/games/gm{game_id}/{version}/index.html'
        game_urls.append(api_response['data']['gameUrl'])
        unlisted_ids.append(game_id)
        correct_pairs.append((game_id, key))
        print(api_response['data']['path'])
    else:
        assert api_response['meta']['status'] == 404
        assert api_response['meta']['errorCode'] == 'NOT_FOUND'
        wrong_pairs.append((game_id, key))
        print(f'{game_id} key {key} is wrong')

    time.sleep(0.1)

findings.update({ "urls": game_urls, 'payment': findings['losts'], 'unlisted': unlisted_ids })
findings.pop('losts', None)

with open('data/findings_3.json', 'w') as w:
    json.dump(findings, w)

with open('data/urls_3.txt', 'w') as w:
    for url in game_urls:
        print(url, file=w)

with open('data/public.txt', 'w') as w, open('data/public_payment.txt', 'w') as wp:
    for game_id in findings['200']:
        if game_id in findings['payment']:
            print(f'https://game.nicovideo.jp/atsumaru/games/gm{game_id}', file=wp)
        else:
            print(f'https://game.nicovideo.jp/atsumaru/games/gm{game_id}', file=w)

with open('data/key_valid.txt', 'w') as w:
    for game_id, key in correct_pairs:
        print(f'https://game.nicovideo.jp/atsumaru/games/gm{game_id}?key={key}', file=w)

with open('data/key_invalid.txt', 'w') as w:
    for game_id, key in wrong_pairs:
        print(f'https://game.nicovideo.jp/atsumaru/games/gm{game_id}?key={key}', file=w)