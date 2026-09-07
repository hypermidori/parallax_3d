# Blender CLI 制作環境

CodexからPythonスクリプトを使ってゲーム用アセットを生成する、Windows x64向けの環境です。
Blender 4.5.13 LTSをプロジェクト内に固定しています。追加のPythonやMCPは不要です。

## セットアップ

プロジェクトのフォルダーでPowerShellから実行します。

```powershell
.\tools\setup-blender.ps1
.\tools\blender.ps1 --version
```

公式のZIPとSHA256を取得し、照合後に `.tools/blender-4.5.13-windows-x64` に展開します。
ダウンロードは約380 MB、展開用にも空き容量が必要です。`.tools` はGit管理から除外しています。
Blenderの設定は同梱の `portable` フォルダーに保存します。
インストール後の生成・レンダリングにネット接続は不要です。

## テスト用マップ・キャラクターを生成

```powershell
.\tools\build-demo.ps1
```

`output/demo/` に以下が作成されます。

| ファイル | 内容 |
|---|---|
| `scene.blend` | マップ、ロボット、プレビュー用カメラ・照明を含む編集用シーン |
| `map.glb` | マップ単体。カメラ・照明は含めません |
| `character.glb` | 原点に配置したロボット単体 |
| `preview.png` | 960×720の完成イメージ |
| `manifest.json` | Blenderバージョン、単位、メッシュ数、三角形数 |
| `verification.json` | GLB再読み込み時のメッシュ数・三角形数・材質確認結果 |

既存の出力は上書きしません。再実行時は別名を指定してください。

```powershell
.\tools\build-demo.ps1 -Name demo02
.\tools\build-demo.ps1 -Name quick-check -SkipRender
```

レンダリングはGPU設定に依存しないCycles CPUを使用します。所要時間はPC性能によります。
出力フォルダーが残った状態で失敗した場合も、別の `-Name` で再実行できます。

## 今後Codexに頼むとき

「この環境でローポリの岩を5種類作って。高さは1～2m、GLB形式で」など、
形状・寸法・見た目・出力形式を伝えてください。

制作スクリプトは `blender_scripts/` に置きます。
`asset_utils.py` は材質、立方体、GLB書き出し、メッシュ統計の共通処理です。
`create_demo.py` を参考に新しいスクリプトを作成し、次の形式で実行できます。

```powershell
.\tools\blender.ps1 --background --factory-startup --python-exit-code 1 --python .\blender_scripts\create_demo.py '--' --output .\output\custom-demo
```

`--python-exit-code 1` によってPython例外をコマンドの失敗として検出します。
PowerShellのラッパーに渡す区切りの `--` は、上記のように引用符で囲んでください。
`--factory-startup` は新しいプロセスの初期状態を揃えるための指定です。
既存のシーンを編集する場合は、その `.blend` を明示して専用スクリプトで読み込み、別名保存します。

## Blenderの画面で開く

次のコマンドを通常のPowerShellで実行すると、生成したシーンを表示できます。

```powershell
.\tools\blender.ps1 .\output\demo\scene.blend
```

## アセットの規約と現在の範囲

- 1 Blender unit = 1メートル。Blender内はZ上向き、GLBはY上向きで出力します。
- ロボットは高さ約1.9m、足元が原点です。Blender内では正面が-Y方向です。
- デモキャラクターは静的な形状です。ボーン、スキニング、アニメーションは未作成です。
- 当たり判定用メッシュ、LOD、ゲーム内ナビゲーションは未作成です。
- GLBの構造・材質の再読み込みまで検証します。ゲームエンジン上の描画・物理設定は別途調整します。
- プレビューの光や影はGLBに焼き込まず、ゲーム側の照明で表示します。

公式配布元: https://download.blender.org/release/Blender4.5/
