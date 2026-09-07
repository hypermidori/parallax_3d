# OUTER PARALLAX FIELD — NIGHT VECTOR

夜の市街地を画面奥へ飛ぶ、ブラウザ向けレールシューティングの1ステージ試作です。
元ゲームは `C:/workspace/codex_sample`。このフォルダーに独立したリメイクを実装しています。

## 遊ぶ

```powershell
.\tools\start-game.ps1
```

**http://127.0.0.1:5180/** を開き、「出撃する」を押します。現在のマシンでは既存のNode.jsも自動検出します。
通常のNode.js環境では以下でも起動できます。

```powershell
npm ci
npm run dev
```

| 操作 | マウス / タッチ | キーボード | ゲームパッド |
|---|---|---|---|
| 照準・移動 | マウス移動 / 指でドラッグ | WASD / 矢印 | 左スティック |
| ロック | 押したまま敵をなぞる | Space / Zを長押し | A / RTを長押し |
| レーザー | 離す | 離す | 離す |
| ポーズ | 右上のⅡ | Escape / P | Start |

主人公は照準を追従し、通常弾は自動で撃ちます。ロックは最大8個。タッチでは指より少し上に照準を表示します。
道中は約2分、続いて3段階の攻撃を持つボス戦。HPが尽きるとリトライできます。

スマホは横画面専用です。縦画面では回転アイコンを表示します。全画面ボタンまたは出撃時に、対応ブラウザへ全画面化と横向き固定を要求します。非対応・拒否された場合は端末を手動で横にしてください。プレイ中に縦へ戻るとポーズし、横に戻して再開できます。向き固定そのものの対応はブラウザ・OSに依存します。

## 今回の実装

- Blender CLI製の実際の3D市街地。曲線道路、段状のビル、窓枠、歩道、照明、ガラス連絡橋、高架下。
- 建物・路面を含む全84環境メッシュにUVと画像テクスチャ。発光と距離の霞をゲーム側で調整。
- 生成コンセプトを基準に造形し、Blenderレンダーとブラウザの描画を比較して修正。
- 2D主人公はニュートラル・左右旋回の各4コマ。髪と噴射のフレームアニメーション。
- 敵編隊、地上砲台、四脚戦車ボス、追尾レーザー、被弾、チェインスコア、BGM、ポーズ、リザルト。

背景の総三角形数は159,564。12区画を距離で表示切り替えします。GLBにはテクスチャを埋め込んでいます。
試作段階のため建築キットの繰り返しがあり、コンセプトの全ての細部を一致させたものではありません。

## Blenderから再生成

```powershell
.\tools\blender.ps1 --background --factory-startup --python-exit-code 1 --python .\blender_scripts\build_night_city.py
```

このコマンドは今回の市街地・敵の生成物を再生成します。

- 編集用シーン：`output/night-city/night-city.blend`
- ゲーム用背景：`public/assets/night-city.glb`
- ゲーム用の敵：`public/assets/enemy-kit.glb`
- 確認レンダー：`output/night-city/concept-match.png`
- 生成統計：`output/night-city/manifest.json`

Blenderをまだ配置していない環境では `.\tools\setup-blender.ps1` を先に実行します。
Blender CLI環境の詳細と過去のデモは [docs/BLENDER_CLI.md](docs/BLENDER_CLI.md) を参照してください。

## ビルド・検証

```powershell
npm test
npm run build
npm run preview
```

ビルド結果は `dist/`。外部CDNは使いません。WebGLが有効なブラウザが必要です。

- [仕様](docs/REMAKE_SPEC.md)
- [素材とコンセプト比較](docs/ASSETS.md)
- [操作確認・自動検証](docs/PLAYTEST.md)

スマホの縦画面とタッチ入力はブラウザでエミュレーション確認しています。スマホ実機の速度、物理コントローラーは未検証です。
