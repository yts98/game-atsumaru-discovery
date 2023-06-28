game-atsumaru-discovery
=============

## Privacy setting (公開設定)

| [公開](data/public.txt) | [公開、会員限定](data/public_payment.txt) | [限定公開](data/key_valid.txt) | 非公開 |
| ---: | -: | -----: | -------: |
| 9467 | 21 | >= 306 | <= 19960 |

## Framework (フレームワーク)

| Framework                    | Count | Reclassify |
| :--------------------------- | ----: | ---------: |
| [RPG Maker MV][MV]           |  5988 |         42 |
| [RPG Maker MZ][MZ]           |  1332 |          0 |
| [Akashic Engine][AK]         |  1019 |          3 |
| [EasyRPG Player][ER]         |   299 |          0 |
| [TyranoBuilder][TY]          |   250 |         10 |
| [Unity][UN]                  |   185 |        135 |
| [SUCCESS Corporation][SU]    |    85 |          0 |
| [GameMaker Studio][GM]       |    27 |          0 |
| [Tonyu System][TO]           |    15 |          0 |
| [Visual Novel Maker][VN]     |    11 |          0 |
| Others                       |   375 |            |

[MV]: https://rpgmakerofficial.com/product/mv/
[MZ]: https://rpgmakerofficial.com/product/mz/
[AK]: https://akashic-games.github.io/
[ER]: https://atsumaru.github.io/api-references/download/200x-player/
[TY]: https://tyranobuilder.com/
[UN]: https://unity.com/
[SU]: https://www.success-corp.co.jp/
[GM]: https://gamemaker.io/
[TO]: https://www.tonyu.jp/
[VN]: https://visualnovelmaker.com/

### RPG Maker MV with modifications
- 55, 529, 596, 1250, 3477, 7764, 9022, 13915
- 3621, 3736, 3765

### RPG Maker MZ with modifications
- 22144

### Unity with non-default WebGLTemplates
- 7735, 7956, 8518, 8569, 9540, 9799, 12097, 12356, 12988, 13987 (BetterMinimal 2.0)
- 8025 (modified BetterMinimal 2.0)
- 11353, 14360, 17211, 18014, 23340, 25791 (modified BetterMinimal)
- 11833, 12231 (Responsive)
- 17774 (modified BetterMinimal 2.2)

## Others

- Add URLs you found to `data/manual_URLs.txt` and execute `step7-manual.py`.

### Phaser
- 2742
- 14174

### enchant.js + Box2D
- 5404, 5461, 5530, 5608, 5614, 5749, 6016

### GDevelop JavaScript
- 15302 (DONE)

### GB Studio
- 17434, 17646, 18005, 18146 (DONE)

### binjgb
- 29320, 29532, 29752, 29754 (DONE)

### Vanilla JS
- 165 (DONE)
- 29249, 29267 (DONE)

## Usage

### Requirements

- `pip install pyjsparser`

### Fetch RPG Maker MV resources

```
python step6-MV_iterate_.py
python step6-MV_iterate_.py <gameId>
python step6-MV_iterate_.py <gameId_range_start> <gameId_range_end>
```

### Fetch RPG Maker MZ resources

```
python step6-MZ_iterate_.py
python step6-MZ_iterate_.py <gameId>
python step6-MZ_iterate_.py <gameId_range_start> <gameId_range_end>
```

### Fetch Akashic Engine resources

```
python step6-AK_iterate_.py
python step6-AK_iterate_.py <gameId>
python step6-AK_iterate_.py <gameId_range_start> <gameId_range_end>
```

### Fetch EasyRPG Player resources (for RPG Maker 2000, RPG Maker 2003)

```
python step6-ER_iterate_.py
python step6-ER_iterate_.py <gameId>
python step6-ER_iterate_.py <gameId_range_start> <gameId_range_end>
```

### Fetch Unity resources

```
python step6-UN_iterate_.py
python step6-UN_iterate_.py <gameId>
python step6-UN_iterate_.py <gameId_range_start> <gameId_range_end>
```

## Contribution

- Game Atsumaru went offline around 12pm on June 28, 2023 (JST, UTC+9).

- ~~You could claim an `gameId` range in https://pad.notkiska.pw/p/game-atsumaru . ~~

- ~~ Inform `yts98` on `#archiveteam-bs@irc.hackint.org` before the deadline if: ~~
    - ~~ You encountered an exception during script execution. ~~
    - ~~ You're willing to reverse engineer one or more game frameworks or games that do not use frameworks. ~~
        - ~~ You have ability to derive a list of resource URLs from games using frameworks. ~~
        - ~~ You have ability to identify interactive API calls including: ~~
            - ~~ `window.RPGAtsumaru.comment.changeScene(sceneName: string)` ~~
            - ~~ `window.RPGAtsumaru.comment.resetAndChangeScene(sceneName: string)` ~~
            - ~~ `window.RPGAtsumaru.scoreboards.setRecord(boardId: number, score: number)` ~~
            - ~~ `window.RPGAtsumaru.scoreboards.display(boardId: number)` ~~
        - ~~ You have ability to deobfuscate JavaScript or disassemble WASM for games that do not use frameworks. ~~
    - ~~ You found any uncategorized games that actually fall into the above frameworks. ~~
    - ~~ You have a list of resource URLs for a specific game. ~~
        - ~~ You can open the browser devtool and play the game throughly. ~~
    - ~~ You found a game available elsewhere, and you're sure they're identical. ~~
    - ~~ You found more unlisted games (removing the `key` parameter from the URL will make it inaccessible). ~~