# 主人公3D試作

承認された三面図 `turnaround-v01.png` を元に、Blenderで制作したローポリ初稿です。
採用版は `C:\workspace\parallax_3d\output\player-v03`。ゲーム側には `raw-assets/player-3d-v01` にコピーします。

## 確認方法

`viewer.html` をブラウザーで開くと、モデルを回転・拡大して確認できます。
Three.jsとGLBをHTMLに埋め込んでいるため、閲覧時の外部CDNや開発サーバーは不要です。
正面／側面／背面、ワイヤー表示、簡易ホバー再生に対応しています。

`player.blend` は編集用、`player.glb` はモデル・テクスチャ・ボーン・アニメーションを含む交換用です。
`front.png`、`back.png`、`side.png`、`three-quarter.png`、`hover-back.png` は確認用レンダリングです。

## 仕様

- 約5,600三角形。正確な値は `manifest.json` と `verification.json` に記録。
- 1メッシュ、1マテリアル、17ボーン。
- ペイント済みカラーアトラス 2048×2048、発光アトラス 512×512。GLBとblendへ埋め込み済み。
- 当初の1024px目安より顔の読みやすさを優先し、試作では2048pxにしています。製品用の縮小・描き直しは別工程です。
- 直立時の身長は頭の通信フィン込み約1.825m。1 unit = 1m。
- BlenderはZ-up／正面-Y。GLBはY-up／正面+Z。
- `HoverIdle` は2秒・24fpsの短い動作。再生停止時の基準は低いAポーズです。

## テクスチャと形状

三面図と顔のペイントは内蔵image_genで作成しました。実際のプロンプトは `turnaround-v01-prompt.txt` と `face-texture-prompt.txt` に保存しています。
顔のペイントを頭部のUVに合わせ、髪のストライプ、装甲の色分け・陰影と一緒にBlenderでカラーアトラスへ焼き込みました。
テクスチャを個別に描き直せるよう、元の顔画像と生成スクリプトも保存しています。

## 検証

出力GLBを別のBlenderプロセスで再読み込みし、三角形数、1マテリアル、2枚の埋め込みテクスチャ、UV、ボーン、全頂点のウェイト、アニメーションによる実メッシュの変位を検証します。
確認結果は `verification.json` に保存します。

採用版のGLB再読み込み検証は成功しました（5,616三角形、1メッシュ・1マテリアル、17ボーン、2枚の埋め込みテクスチャ、全頂点のウェイト、実メッシュのアニメーション変位を確認）。
ビューアーのバンドル生成は成功しましたが、CodexブラウザーのローカルファイルURL制限により、HTMLの実表示とボタン操作の確認はできていません。Blenderの各方向のレンダリングは確認済みです。

## 初稿の範囲

シルエットと制作パイプラインを確かめるための試作です。三面図の細かな装甲形状をすべて再現した完成モデルではありません。
特に顔・前髪・足首・腰装甲は追加調整の余地があります。

ウェイトは装甲パーツ単位の簡易割り当てです。表情リグ、指の個別操作、髪の物理、布の変形、当たり判定、LODはありません。
ホバー姿勢での関節・髪の干渉には追加調整が必要です。ブースター炎は未作成です。
ゲームの描画や操作コードは変更していません。採用する見た目が決まった段階で読み込み・アニメーション・エフェクトを接続できます。

## 再生成

`C:\workspace\parallax_3d` のPowerShellで、新しい出力名を指定します。

```powershell
.\tools\build-player.ps1 -Name player-next
node .\tools\build-player-viewer.cjs .\output\player-next
```

ビューアーの再ビルドだけ、ゲーム側にインストール済みのThree.js／esbuildを参照します。
完成したHTMLは単独で開けます。Three.jsのライセンスは同梱の `THREE-LICENSE.txt` を参照してください。

制作スクリプト: `blender_scripts/create_player.py`
検証スクリプト: `blender_scripts/verify_player.py`

元のゲーム画像 `assets/player-hover.png` は変更していません。
