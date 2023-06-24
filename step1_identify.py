from bs4 import BeautifulSoup
import os
import time
import json
import requests

headers = {
    'Cache-Control': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}

public_games = []
inaccessible_games = []

if os.path.isfile('data/findings_1.json'):
    exit('Not overwriting data/findings_1.json .')

for game_id in range(1, 29754+1):
    url = f'https://game.nicovideo.jp/atsumaru/games/gm{game_id}'
    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, features='lxml')
    glob_state = soup.find(id='stateSerialized')['data-state']
    glob_state = json.loads(glob_state)
    assert set(glob_state.keys()) == set(['initialState', 'baseInitialState', 'targetPathAndSearch', 'reduxState']), ' '.join(glob_state.keys())
    initialState, baseInitialState, targetPathAndSearch, reduxState = glob_state['initialState'], glob_state['baseInitialState'], glob_state['targetPathAndSearch'], glob_state['reduxState']

    def display_state(states):
        for key, state in states.items():
            if isinstance(state, dict):
                assert 'type' in state.keys()
                assert state['type'] in ['loading', 'resolved', 'rejected'], state['type']
                if state['type'] == 'loading': assert set(state.keys()) == set(['type'])
                if state['type'] == 'resolved': assert set(state.keys()) == set(['type', 'value'])
                if state['type'] == 'rejected': assert set(state.keys()) == set(['type', 'error'])
                print(key, f'({state["type"]})', state.get('error') or '')
            else:
                print(key, type(state).__name__, state)

    # print('\ninitialState')
    assert set(initialState.keys()) == set(['initialState', 'path']), ' '.join(initialState.keys())
    assert initialState['path'] == '/games/:gameId'
    assert isinstance(initialState['initialState'], dict), type(initialState['initialState'])
    # display_state(initialState['initialState'])

    # print('\nbaseInitialState')
    assert isinstance(baseInitialState, dict), type(baseInitialState)
    # display_state(baseInitialState)

    # print('\ntargetPathAndSearch')
    assert isinstance(targetPathAndSearch, str), type(targetPathAndSearch)
    assert targetPathAndSearch == f'/atsumaru/games/gm{game_id}'
    # print(targetPathAndSearch)

    # print('\nreduxState')
    assert isinstance(reduxState, dict), type(reduxState)
    # display_state(reduxState)

    if initialState['initialState']['articles']['type'] == initialState['initialState']['tags']['type'] == 'rejected':
        assert initialState['initialState']['articles']['error']['status'] == 404
        assert initialState['initialState']['tags']['error']['status'] == 404
        print(f'gm{game_id} inaccessible')
        inaccessible_games.append(game_id)
    else:
        assert initialState['initialState']['articles']['type'] == initialState['initialState']['tags']['type'] == 'resolved'
        for key, value in initialState['initialState']['game']['value'].items():
            if key == 'id': assert value == f'gm{game_id}'
            elif key == 'title': print(f'gm{game_id}', value)
            # print(key, type(value).__name__ if value is not None else '', value)
        public_games.append(game_id)

    time.sleep(0.1)

with open('data/findings_1.json', 'w') as w:
    json.dump({
        '200': public_games,
        '404': inaccessible_games,
    }, w)