import itertools
import json
import os
import pyjsparser
import re
import sys
import tempfile
import urllib.parse

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

resource_root = 'https://resource.game.nicovideo.jp/'

if not os.path.isfile('data/public.txt') or not os.path.isfile('data/key_valid.txt'):
    exit('Please check public and unlisted game_ids at first.')

games = []

with open('data/public.txt', 'r') as r, open('data/key_valid.txt', 'r') as rk:
    for line in itertools.chain(r.readlines(), rk.readlines()):
        match = re.search(r'^https://game\.nicovideo\.jp/atsumaru/games/gm([1-9][0-9]*)(?:\?key=([0-9a-f]{12}))?$', line.strip())
        assert isinstance(match, re.Match), line.strip()
        games.append((int(match[1]), match[2]))

games = list(filter(lambda item: item[0] in [15302], games))
games.sort()

if len(sys.argv) >= 3 and re.search('^[0-9]+$', sys.argv[1]) and re.search('^[0-9]+$', sys.argv[2]):
    games = list(filter(lambda item: int(sys.argv[1]) <= item[0] <= int(sys.argv[2]), games))
    if len(games):
        print(f'Fetching gm{games[0][0]} ~ gm{games[-1][0]}')
elif len(sys.argv) >= 2 and re.search('^[0-9]+$', sys.argv[1]):
    games = list(filter(lambda item: item[0] == int(sys.argv[1]), games))
    if len(games):
        print(f'Fetching gm{games[0][0]}')

for game_id, key in games:
    try:
        if key is None:
            ticket_url = f'https://api.game.nicovideo.jp/v1/rpgtkool/games/gm{game_id}/play-tickets.json?sandbox=0&wipAccessKey'
        else:
            ticket_url = f'https://api.game.nicovideo.jp/v1/rpgtkool/games/gm{game_id}/play-tickets.json?sandbox=0&wipAccessKey={key}'
        os.system(f'curl -X POST -A "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0" \
                -H "X-Frontend-Id: 39" -H "X-Frontend-Version: 3.464.0" -H "X-Request-With: https://game.nicovideo.jp" \
                -H "Origin: https://game.nicovideo.jp" -H "Referer: https://game.nicovideo.jp/" -F "=" \
                -c "ticket/gm{game_id}_cookie.txt" -o ticket/gm{game_id}_ticket.json "{ticket_url}"')

        assert os.path.isfile(f'ticket/gm{game_id}_cookie.txt')
        cookie_jar = []
        with open(f'ticket/gm{game_id}_cookie.txt', 'r') as r:
            for line in r.readlines():
                fields = line.strip().split('\t')
                if len(fields) == 7:
                    cookie_jar.append(f'{fields[5]}={fields[6]}')
            cookie_argument = f'--header="Cookie: {"; ".join(cookie_jar)}"'

        assert os.path.isfile(f'ticket/gm{game_id}_ticket.json')
        with open(f'ticket/gm{game_id}_ticket.json', 'r') as r:
            ticket = json.load(r)
            game_path = ticket['data']['path'].lstrip('/')
            game_url = ticket['data']['gameUrl']

        temp_dir = tempfile.TemporaryDirectory()
        temp_urllist = os.path.join(temp_dir.name, 'temp_urllist')

        os.system(f'wget --execute="robots=off" --no-verbose --force-directories --no-host-directories \
                --header="Host: resource.game.nicovideo.jp" --header="User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0" \
                {cookie_argument} \
                --load-cookies=ticket/gm{game_id}_cookie.txt --keep-session-cookies \
                --warc-file=warc/gm{game_id} --no-warc-compression --no-warc-keep-log \
                --recursive --level=inf --no-parent {game_url}')

        # Step 1: Resources

        discovered_urls = []
        step_urls = []
        resource_urls = []

        with open(os.path.join(game_path, 'data.js'), 'r') as r:
            content = r.read()
            json_like = re.search(r'^gdjs\.projectData = ({.+});$', content)
            json_data = json.loads(json_like[1])
            # body = pyjsparser.parse(content)['body']
            # for node in filter(lambda node: node['type'] == 'ExpressionStatement'
            #                 and node['expression']['type'] == 'AssignmentExpression'
            #                 and node['expression']['operator'] == '='
            #                 and node['expression']['left']['type'] == 'MemberExpression'
            #                 and node['expression']['left']['object']['type'] == 'Identifier'
            #                 and node['expression']['left']['object']['name'] == 'gdjs'
            #                 and node['expression']['left']['property']['type'] == 'Identifier'
            #                 and node['expression']['left']['property']['name'] == 'projectData', body):
            #     assert node['expression']['right']['type'] == 'ObjectExpression', 'data.js'
            #     for property in node['expression']['right']['properties']:
            #         if property['key']['value'] == 'properties':
            #             for property in property['value']['properties']:
            #                 if property['key']['value'] == 'platformSpecificAssets':
            #                     for property in property['value']['properties']:
            #                         resource_urls.append(property['value']['value'])
            assert set(json_data.keys()).issuperset(set(['properties', 'resources']))
            for key, value in json_data['properties']['platformSpecificAssets'].items():
                resource_urls.append(value)
            for resource in json_data['resources']['resources']:
                assert isinstance(resource['file'], str)
                resource_urls.append(resource['file'])

        for resource_url in sorted(set(resource_urls)):
            step_urls.append(os.path.join(resource_root, game_path, urllib.parse.quote(resource_url, safe='/')))

        with open('data/tmp', 'w') as w:
            for url in step_urls: print(url, file=w)
        os.system(f'wget --execute="robots=off" --no-verbose --input-file=data/tmp --force-directories --no-host-directories \
                --header="Host: resource.game.nicovideo.jp" --header="User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0" \
                {cookie_argument} \
                --load-cookies=ticket/gm{game_id}_cookie.txt --keep-session-cookies \
                --warc-file=warc/gm{game_id}_1 --no-warc-compression --no-warc-keep-log \
                --recursive --level=inf --no-parent --timeout=10')

        discovered_urls.extend(step_urls)
        step_urls = []

        with open(f'data/iterate/urls_gm{game_id}.txt', 'w') as w:
            for url in discovered_urls:
                print(url, file=w)

        temp_dir.cleanup()

    except AssertionError as ex:
        if temp_dir: temp_dir.cleanup()
        print(f'gm{game_id} (GDJS) failed. {ex.args}')
        with open(f'data/iterate.txt', 'a') as a:
            print(f'gm{game_id:05d} (GDJS) failed. {ex.args}', file=a)