from bs4 import BeautifulSoup
import datetime
import itertools
import json
import os
import pyjsparser
import re
import sys
import tempfile
import time
import urllib.parse

if not os.path.isdir('./ticket'):
    os.mkdir('./ticket')
if not os.path.isdir('./warc'):
    os.mkdir('./warc')

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

games = list(filter(lambda item: item[0] in framework_games['Unity'], games))
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
    timestamp_suffix = '' and f'_{int(time.time()*1E6)}'
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
                --warc-file=warc/gm{game_id}{timestamp_suffix} --no-warc-compression --no-warc-keep-log \
                --recursive --level=inf --no-parent')

        # Step 1: UNITY_WEBGL_BUILD_URL

        discovered_urls = []
        step_urls = []
        resource_urls = []
        UNITY_WEBGL_BUILD_URL = None

        assert os.path.isfile(os.path.join(game_path, 'index.html')), 'index.html'
        with open(os.path.join(game_path, 'index.html'), 'r') as r:
            content = r.read()
            soup = BeautifulSoup(content, features='lxml')
            for script in soup.find_all('script'):
                if script.string:
                    script_lines = list(map(lambda x: x.strip(), script.string.strip().split('\n')))
                    for script_line in script_lines:
                        instantiate_re = re.search(r'(?:var (?:game|unity)Instance *= *)?UnityLoader\.instantiate\("(?:game|unity)Container", "(Build\/[^\/"]+\.json)"(?:, {onProgress: UnityProgress})?\);?', script_line)
                        if instantiate_re:
                            UNITY_WEBGL_BUILD_URL = instantiate_re[1]
            if not UNITY_WEBGL_BUILD_URL:
                raise NotImplementedError('unknown HTML', game_url)
            else:
                resource_urls.append(UNITY_WEBGL_BUILD_URL)

        for resource_url in sorted(set(resource_urls)):
            step_urls.append(os.path.join(resource_root, game_path, urllib.parse.quote(resource_url, safe='/')))

        with open('data/tmp', 'w') as w:
            for url in step_urls: print(url, file=w)
        os.system(f'wget --execute="robots=off" --no-verbose --input-file=data/tmp --force-directories --no-host-directories \
                --header="Host: resource.game.nicovideo.jp" --header="User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0" \
                {cookie_argument} \
                --load-cookies=ticket/gm{game_id}_cookie.txt --keep-session-cookies \
                --warc-file=warc/gm{game_id}_1{timestamp_suffix} --no-warc-compression --no-warc-keep-log \
                --recursive --level=inf --no-parent --timeout=10')

        # Step 2: Package

        discovered_urls.extend(step_urls)
        step_urls = []
        build_path = os.path.dirname(UNITY_WEBGL_BUILD_URL)

        assert os.path.isfile(os.path.join(game_path, UNITY_WEBGL_BUILD_URL))
        with open(os.path.join(game_path, UNITY_WEBGL_BUILD_URL), 'r') as r:
            build_json = json.load(r)
            for key, value in build_json.items():
                if key not in ['companyName', 'productName', 'productVersion', 'TOTAL_MEMORY', 'splashScreenStyle', 'backgroundColor', 'unityVersion'] and isinstance(value, str):
                    resource_urls.append(os.path.join(build_path, value))
                    if key not in ['dataUrl', 'asmCodeUrl', 'asmMemoryUrl', 'asmFrameworkUrl', 'wasmCodeUrl', 'wasmMemoryUrl', 'wasmFrameworkUrl'] and isinstance(value, str):
                        print(key, value)

        for resource_url in sorted(set(resource_urls)):
            step_urls.append(os.path.join(resource_root, game_path, urllib.parse.quote(resource_url, safe='/')))

        with open('data/tmp', 'w') as w:
            for url in step_urls: print(url, file=w)
        os.system(f'wget --execute="robots=off" --no-verbose --input-file=data/tmp --force-directories --no-host-directories \
                --header="Host: resource.game.nicovideo.jp" --header="User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0" \
                {cookie_argument} \
                --load-cookies=ticket/gm{game_id}_cookie.txt --keep-session-cookies \
                --warc-file=warc/gm{game_id}_1{timestamp_suffix} --no-warc-compression --no-warc-keep-log \
                --recursive --level=inf --no-parent --timeout=10')

        discovered_urls.extend(step_urls)
        step_urls = []

        with open(f'data/iterate/urls_gm{game_id}.txt', 'w') as w:
            for url in discovered_urls:
                print(url, file=w)

        temp_dir.cleanup()

    except (AssertionError, NotImplementedError) as ex:
        if temp_dir: temp_dir.cleanup()
        now_string = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{now_string} gm{game_id} (UN) failed. {ex.args}')
        with open(f'data/iterate.txt', 'a') as a:
            print(f'{now_string} gm{game_id:05d} (UN) failed. {ex.args}', file=a)