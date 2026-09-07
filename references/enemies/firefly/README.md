# AMBER FIREFLY

原作の雲海ステージの橙色の小型機。短い中央胴体、左右の丸い推進器、橙と白の塗装を採用。

## 制作

内蔵 image_gen で２Dデザイン（design-v01.png）を制作し、その輪郭・大きな部品構成・配色を基準にBlender CLIで立体化した。
次にブラウザで正面・上面・側面・斜めの表示を確認した。レンズ／コアは複数の同心パーツで構成し、細部と発射位置を調整した。
生成プロンプトは design-prompt.txt、共通塗装アトラスのプロンプトは ../support-atlas-prompt.txt。

3,940 三角形、6 材質。全パーツにUVと画像テクスチャがある。
橙色・オリーブ・象牙色の塗装、金属、黒い内部、発光ガラス、警告帯を描いた専用アトラスを２体で使用する。

## ファイル

- ゲーム用モデル：../../../public/assets/amber-firefly.glb
- 専用アトラス：../../../public/assets/support-enemies-atlas.png
- パーツ別の編集用Blender：../../../output/amber-firefly/amber-firefly.blend
- 生成スクリプト：../../../blender_scripts/build_support_enemies.py
- UV・材質・書き出しの共通処理：../../../blender_scripts/painted_enemy_mesh.py
- 比較画面：../../../enemy-lab.html

GLBとBlenderにはテクスチャを埋め込み済み。GLBには ShotOrigin という発射位置も含む。
ゲームはこのノードのワールド座標に弾を生成するため、モデルの向きと大きさを反映して発射部に一致する。
Blender座標での発射位置は [0.0, 2.1589999198913574, 0.11999999731779099]。+Yが前方、Zが上。

再生成：

    .\tools\blender.ps1 --background --factory-startup --python-exit-code 1 --python blender_scripts/build_support_enemies.py
