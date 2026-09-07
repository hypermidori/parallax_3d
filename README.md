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
| 照準・移動 | マウス移動 / タッチ位置を基点にパッド操作 | WASD / 矢印 | 左スティック |
| ロック | 押したまま照準を敵へ動かす | Space / Zを長押し | A / RTを長押し |
| レーザー | 離す | 離す | 離す |
| ポーズ | 右上のⅡ | Escape / P | Start |

主人公は照準を追従し、通常弾は自動で撃ちます。ロックは最大8個。タッチ位置をバーチャルパッドの中心にし、指を倒した方向へ照準が移動します。指を離すと照準はその場に止まり、再タップしても位置は飛びません。上下は画面の高さ40〜70%、左右は幅35〜65%に制限しています。両軸の移動速度は共通です。
道中は約2分、続いて3段階の攻撃を持つボス戦。ボス戦も前進しながら戦い、ボスとの距離を保ちます。HPが尽きるとリトライできます。

スマホは縦・横どちらの向きでも遊べます。横向き固定や自動全画面化は行いません。回転時はタッチ入力を解除し、表示を新しい画面サイズに合わせてゲームを続けます。

## 今回の実装

- Blender CLI製の実際の3D市街地。曲線道路、段状のビル、窓枠、歩道、照明、ガラス連絡橋、高架下。
- 建物・路面を含む全98環境メッシュにUVと画像テクスチャ。発光と距離の霞をゲーム側で調整。
- 生成コンセプトを基準に造形し、Blenderレンダーとブラウザの描画を比較して修正。
- 2D主人公はニュートラル・左右旋回の各4コマ。髪と噴射のフレームアニメーション。
- 敵編隊、地上砲台、収納脚を持つホバー戦車ボス、追尾レーザー、被弾、チェインスコア、BGM、ポーズ、リザルト。

背景アセットの総三角形数は184,584。道中10区画とボス用4区画をBlenderで生成し、GLBにテクスチャを埋め込んでいます。ボス用は180m×4区画を8個の固定スロットで再利用し、カメラを通過した区画を前方へ移します。ボス戦中も街が流れ続け、戦闘時間に合わせて背景が増えることはありません。
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


## 迎撃機のモデル制作

原作の青白の航空機を参考に、２Dデザイン画を作ってからBlenderで制作した「AZURE KESTREL」を迎撃機へ組み込んでいます。約16秒から登場します。5,616三角形、専用画像テクスチャ付き。

[２D案と３Dモデルの比較画面](http://127.0.0.1:5180/enemy-lab.html)では拡大・回転と四方向の確認、夜間照明への切り替えができます。製品ビルドにも enemy-lab.html を含めています。

制作資料と再生成手順：[references/enemies/kestrel/README.md](references/enemies/kestrel/README.md)


偵察機「AMBER FIREFLY」と地上砲台「IRON WARDEN」も、２D案からBlenderで制作したテクスチャ付きモデルへ差し替えました。砲台は砲身を持たず、中央のコアから弾を出します。比較画面のMODEL選択で４種類を切り替えられます。

[全４体の制作資料](references/enemies/README.md)


## ボスのモデル制作

「GRENDEL HOVER」は原作の多脚戦車をホバー式に再設計。２D案からBlenderで制作し、専用画像テクスチャを貼った14,500三角形のモデルです。脚は収納したまま、機体がゆっくり上下・傾斜し、４つの推進器が脈動します。弾と照準は正面の赤いコアに一致します。

[ボスの２D・３D比較](http://127.0.0.1:5180/enemy-lab.html?model=boss) ／ [制作資料と再生成手順](references/enemies/grendel/README.md)
