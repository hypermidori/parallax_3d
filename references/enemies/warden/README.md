# IRON WARDEN

原作の装甲車両を参考にした地上砲台。ユーザーの指定により砲身を取り除き、浅い中央の赤い発光コアを唯一の発射部とした。

## 制作

内蔵 image_gen で２Dデザイン（design-v02.png）を制作し、その輪郭・大きな部品構成・配色を基準にBlender CLIで立体化した。
次にブラウザで正面・上面・側面・斜めの表示を確認した。レンズ／コアは複数の同心パーツで構成し、細部と発射位置を調整した。
生成プロンプトは design-prompt.txt、共通塗装アトラスのプロンプトは ../support-atlas-prompt.txt。

2,288 三角形、8 材質。全パーツにUVと画像テクスチャがある。
橙色・オリーブ・象牙色の塗装、金属、黒い内部、発光ガラス、警告帯を描いた専用アトラスを２体で使用する。

## ファイル

- ゲーム用モデル：../../../public/assets/iron-warden.glb
- 専用アトラス：../../../public/assets/support-enemies-atlas.png
- パーツ別の編集用Blender：../../../output/iron-warden/iron-warden.blend
- 生成スクリプト：../../../blender_scripts/build_support_enemies.py
- UV・材質・書き出しの共通処理：../../../blender_scripts/painted_enemy_mesh.py
- 比較画面：../../../enemy-lab.html

GLBとBlenderにはテクスチャを埋め込み済み。GLBには ShotOrigin という発射位置も含む。
ゲームはこのノードのワールド座標に弾を生成するため、モデルの向きと大きさを反映して発射部に一致する。
Blender座標での発射位置は [0.0, 1.1449999809265137, 1.4800000190734863]。+Yが前方、Zが上。

再生成：

    .\tools\blender.ps1 --background --factory-startup --python-exit-code 1 --python blender_scripts/build_support_enemies.py
