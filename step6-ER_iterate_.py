import itertools
import json
import os
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

if not os.path.isfile('data/catagory.json'):
    exit('Please categorize games at first.')

games = []

with open('data/public.txt', 'r') as r, open('data/key_valid.txt', 'r') as rk:
    for line in itertools.chain(r.readlines(), rk.readlines()):
        match = re.search(r'^https://game\.nicovideo\.jp/atsumaru/games/gm([1-9][0-9]*)(?:\?key=([0-9a-f]{12}))?$', line.strip())
        assert isinstance(match, re.Match), line.strip()
        games.append((int(match[1]), match[2]))

with open('data/catagory.json', 'r') as r:
    framework_games = json.load(r)

games = list(filter(lambda item: item[0] in framework_games['EasyRPG'], games))
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

        with open(temp_urllist, 'w') as w:
            print(game_url, file=w)
        os.system(f'wget --execute="robots=off" --no-verbose --input-file={temp_urllist} --force-directories --no-host-directories \
                --header="Host: resource.game.nicovideo.jp" --header="User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0" \
                {cookie_argument} \
                --load-cookies=ticket/gm{game_id}_cookie.txt --keep-session-cookies \
                --warc-file=warc/gm{game_id} --no-warc-compression --no-warc-keep-log \
                --recursive --level=inf --no-parent')

        # Step 1: index.json

        discovered_urls = []
        step_urls = []
        resource_urls = [
            'index.json',
            'ExFont',
            'Font/ExFont',
            'Font/Font',
            'Font/Font2',
        ]
        resource_path = 'games/default/'

        for resource_url in sorted(set(resource_urls)):
            step_urls.append(os.path.join(resource_root, game_path, resource_path, urllib.parse.quote(resource_url, safe='/')))

        with open(temp_urllist, 'w') as w:
            for url in step_urls: print(url, file=w)
        os.system(f'wget --execute="robots=off" --no-verbose --input-file={temp_urllist} --force-directories --no-host-directories \
                --header="Host: resource.game.nicovideo.jp" --header="User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0" \
                {cookie_argument} \
                --load-cookies=ticket/gm{game_id}_cookie.txt --keep-session-cookies \
                --warc-file=warc/gm{game_id}_1 --no-warc-compression --no-warc-keep-log \
                --recursive --level=inf --no-parent --timeout=10')

        # Step 2: Resources

        discovered_urls.extend(step_urls)
        step_urls = []
        resource_urls = [
            'RPG_RT.ldb',
            'RPG_RT.lmt',
            'RPG_RT.ini',
            'easyrpg.soundfont',
        ]

        assert os.path.isfile(os.path.join(game_path, resource_path, 'index.json')), 'index.json'
        with open(os.path.join(game_path, resource_path, 'index.json'), 'r') as r:
            data_index = json.load(r)
            assert set(data_index.keys()) == set(['cache', 'metadata'])
            for key, property in data_index['cache'].items():
                if key in ['easyrpg.soundfont', 'rpg_rt.ldb', 'rpg_rt.lmt', 'rpg_rt.ini'] \
                    or re.search(r'^map[0-9]+\.lmu$', key):
                    assert isinstance(property, str), 'index.json'
                    resource_urls.append(property)
                else:
                    assert isinstance(property, dict), 'index.json'
                    assert '_dirname' in property.keys(), 'index.json'
                    for resource_key, resource_name in property.items():
                        if resource_key != '_dirname':
                            resource_urls.append(os.path.join(property['_dirname'], resource_name))

        for resource_url in sorted(set(resource_urls)):
            step_urls.append(os.path.join(resource_root, game_path, resource_path, resource_url))

        with open(temp_urllist, 'w') as w:
            for url in step_urls: print(url, file=w)
        os.system(f'wget --execute="robots=off" --no-verbose --input-file={temp_urllist} --force-directories --no-host-directories \
                --header="Host: resource.game.nicovideo.jp" --header="User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0" \
                {cookie_argument} \
                --load-cookies=ticket/gm{game_id}_cookie.txt --keep-session-cookies \
                --warc-file=warc/gm{game_id}_2 --no-warc-compression --no-warc-keep-log \
                --recursive --level=inf --no-parent --timeout=10')

        discovered_urls.extend(step_urls)
        step_urls = []

        with open(f'data/iterate/urls_gm{game_id}.txt', 'w') as w:
            for url in discovered_urls:
                print(url, file=w)

        temp_dir.cleanup()

    except AssertionError as ex:
        if temp_dir: temp_dir.cleanup()
        print(f'gm{game_id} (ER) failed. {ex.args}')
        with open(f'data/iterate.txt', 'a') as a:
            print(f'gm{game_id:05d} (ER) failed. {ex.args}', file=a)