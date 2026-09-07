# AZURE KESTREL — enemy model study

原作の雲海ステージに出る青白の cloudFighter（cloud-city-enemy-sprites-v4.png の右上）を参考にした迎撃機。
今回の差し替え対象はゲームの interceptor。出撃約16秒から最初の編隊が現れる。

## 制作の順序

1. 原作の複数の敵シートを比較し、広い翼・二つのエンジン・青白の装甲・中央のセンサーを持つ機体を選んだ。
2. 内蔵 image_gen で２D三面図と斜めのデザイン画を生成。design-v01.png に保存した。
3. 同じ配色で、専用の塗装・金属・発光トリムの画像アトラスを内蔵 image_gen で生成した。
4. Blender CLIで上面の輪郭を基準にロフトした胴体、厚みのある翼、傾けた尾翼、六角形センサー、奥行きのある吸気口、ノズル、砲身を作成。全パーツにUVと画像テクスチャを設定。
5. Blenderレンダーとブラウザの正面・上面・側面・斜め表示で比較した。センサーの装甲基部、機首の接続、正面からの尾翼の見え方、発光を修正した。
6. ゲームの迎撃機を差し替え、独立した比較画面も追加した。

三面図の上面シルエットを優先して立体化している。図に描かれていない下面と内部は補完した。センサー周辺や細かい装甲の分割は３D向けに整理しており、各画素をそのまま立体にしたものではない。

## ファイル

- 原作参考：original-cloud-enemies.png
- ２D案：design-v01.png
- 最終デザイン生成プロンプト：design-prompt.txt
- 最終テクスチャ生成プロンプト：texture-prompt.txt
- 専用テクスチャ：../../../public/assets/kestrel-atlas.png
- ゲーム用GLB：../../../public/assets/azure-kestrel.glb
- パーツ別の編集用Blender：../../../output/kestrel/azure-kestrel.blend
- 生成スクリプト：../../../blender_scripts/build_kestrel.py
- 比較画面：http://127.0.0.1:5180/enemy-lab.html

ゲーム用GLBはテクスチャを埋め込んでいる。編集用Blenderも画像をパック済み。
比較画面の回転、正面・上面・側面表示、夜の照明切り替えはテクスチャを表示したまま利用できる。

## 規模と検証

5,616 三角形、7材質、1254×1254 の専用画像アトラス。GLBでは7つの描画メッシュすべてにUVと画像テクスチャがある。ゲーム上はモデルを0.68倍で使用する。

node scripts/verify-kestrel.mjs で、モデルのテクスチャ、ポリゴン数、デザイン画像、回転表示、ゲーム内の差し替え、リトライ、読み込みエラーを確認する。
再生成は以下のコマンド：

    .\tools\blender.ps1 --background --factory-startup --python-exit-code 1 --python blender_scripts/build_kestrel.py

画像は保存済みなので、再生成に画像APIへの接続は不要。背景の再生成スクリプトとは独立している。
