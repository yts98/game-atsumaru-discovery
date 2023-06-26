import itertools
import os
import re
import time
import json

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

if not os.path.isfile('data/public.txt') or not os.path.isfile('data/key_valid.txt'):
    exit('Please check public and unlisted game_ids at first.')

games = []

with open('data/public.txt', 'r') as r, open('data/key_valid.txt', 'r') as rk:
    for line in itertools.chain(r.readlines(), rk.readlines()):
        match = re.search(r'^https://game\.nicovideo\.jp/atsumaru/games/gm([1-9][0-9]*)(?:\?key=([0-9a-f]{12}))?$', line.strip())
        assert isinstance(match, re.Match), line.strip()
        games.append((int(match[1]), match[2]))

games.sort()

for game_id, key in games:
    if key is None:
        ticket_url = f'https://api.game.nicovideo.jp/v1/rpgtkool/games/gm{game_id}/play-tickets.json?sandbox=0&wipAccessKey'
    else:
        ticket_url = f'https://api.game.nicovideo.jp/v1/rpgtkool/games/gm{game_id}/play-tickets.json?sandbox=0&wipAccessKey={key}'

    # Why did wget give me a empty cookie.txt?
    # boundary = f'---------------------------{random.randint(0, 2**32-1)}{random.randint(0, 2**32-1)}{random.randint(0, 2**32-1)}'
    # os.system(f'wget --verbose --output-document=ticket/gm{game_id}_ticket.json \
    #           --header="Host: api.game.nicovideo.jp" --header="User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0" \
    #           --header="X-Frontend-Id: 39" --header="X-Frontend-Version: 3.464.0" --header="X-Request-With: https://game.nicovideo.jp" \
    #           --header="Content-Type: multipart/form-data; boundary={boundary}" --header="Origin: https://game.nicovideo.jp" --header="Referer: https://game.nicovideo.jp/" \
    #           --save-cookies=ticket/gm{game_id}_cookie.txt --keep-session-cookies --method=POST --body-data="--{boundary}--\r\n" \
    #           --secure-protocol=TLSv1_2 --warc-file=warc/gm{game_id}_ticket --no-warc-compression --no-warc-keep-log "{ticket_url}"')
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
        game_url = json.load(r)['data']['gameUrl']

    os.system(f'wget --execute="robots=off" --no-verbose --force-directories --no-host-directories \
              --header="Host: resource.game.nicovideo.jp" --header="User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0" \
              {cookie_argument} \
              --load-cookies=ticket/gm{game_id}_cookie.txt --keep-session-cookies \
              --warc-file=warc/gm{game_id} --no-warc-compression --no-warc-keep-log \
              --recursive --level=inf --no-parent {game_url}')

    time.sleep(2)