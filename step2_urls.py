import os
import time
import json
import requests

post_headers = {
    'Cache-Control': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
    'X-Frontend-Id': '39',
    'X-Frontend-Version': '3.464.0',
    'X-Request-With': 'https://game.nicovideo.jp',
    'Origin': 'https://game.nicovideo.jp',
    'Referer': 'https://game.nicovideo.jp/',
}

if not os.path.isfile('data/findings_1.json'):
    exit('Please do game_id identification at first.')

if os.path.isfile('data/findings_2.json'):
    exit('Not overwriting data/findings_2.json .')

if os.path.isfile('data/urls_2.txt'):
    exit('Not overwriting data/urls_2.txt .')

findings = {}

with open('data/findings_1.json', 'r') as r:
    findings = json.load(r)
    print(f'total {len(findings["200"]) + len(findings["404"])} found {len(findings["200"])}')

game_urls = []
lost_ids = []

for game_id in findings['200']:
    url = f'https://api.game.nicovideo.jp/v1/rpgtkool/games/gm{game_id}/play-tickets.json?sandbox=0&wipAccessKey'
    response = requests.post(url, data={}, headers=post_headers)

    api_response = json.loads(response.text)
    if api_response['meta']['status'] == 200:
        version = api_response['data'].get('version')
        assert isinstance(version, int), version
        assert api_response['data'].get('path') == f'/games/gm{game_id}/{version}'
        assert api_response['data'].get('gameUrl') == f'https://resource.game.nicovideo.jp/games/gm{game_id}/{version}/index.html'
        assert api_response['data'].get('gamePath') == f'/games/gm{game_id}/{version}/index.html'
        game_urls.append(api_response['data']['gameUrl'])
        print(api_response['data']['path'])
    else:
        assert api_response['meta']['status'] == 404
        assert api_response['meta']['errorCode'] == 'NOT_FOUND'
        lost_ids.append(game_id)
        print(f'{game_id} was lost')

    time.sleep(0.5)

findings.update({ 'urls': game_urls, 'losts': lost_ids })

with open('data/findings_2.json', 'w') as w:
    json.dump(findings, w)

with open('data/urls_2.txt', 'w') as w:
    for url in game_urls:
        print(url, file=w)