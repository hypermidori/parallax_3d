# Assets / NIGHT VECTOR

## 今回の新規制作

- `references/city/night-boulevard-concept-v01.png`：画像生成した夜間市街地のコンセプト。
- `public/assets/city-atlas.png`：画像生成した4分割の建築テクスチャ。窓、コンクリート外壁、金属、舗装。生成プロンプトは `references/city/atlas-prompt.txt`。
- `public/assets/player-flight-keyed.png`：元の主人公を参照して画像生成した4列×3行の飛行スプライト。ニュートラル・右旋回・左旋回の各4コマ。緑背景をゲームのシェーダーで透過する。元生成画像は `player-flight-sheet.png`。
- `public/assets/night-city.glb`：Blender CLIで生成した12区画・2,160mの都市。84メッシュ、159,564三角形。全てUVと画像テクスチャ付き。
- `public/assets/enemy-kit.glb`：Blenderで生成した偵察機、迎撃機、地上砲台、緑色の四脚戦車。
- `public/assets/surface-palette.png`：Blenderで生成した機械装甲・道路標示・発光部用の小さな色テクスチャ。

制作スクリプトは `blender_scripts/build_night_city.py`。実行すると編集用の `output/night-city/night-city.blend` とGLB、確認レンダー、統計を生成する。GLBには画像を埋め込んでいる。

主人公シートの配置は等間隔ではない。`src/hero-frames.js` に各コマの切り出し矩形と腰の基準点を保存している。表示はピクセル当たりの倍率を固定し、Sprite.centerを腰に合わせる。髪・脚・噴射を含む外接矩形の中心で位置合わせしない。`/scripts/hero-animation-preview.html` で修正前後を確認できる。4コマの胴体画像の位置比較では、修正前に最大31pxあった横ずれが、修正後は全3姿勢で0pxになった。

ニュートラルの元画像4コマ目と右旋回の2コマ目は、伸ばした脚と足の噴射が左右入れ替わっているため再生から除外。`HERO_FRAME_ORDER` で、ニュートラルは1→2→3→2、右旋回は1→3→4→3の往復再生とする。元画像の4コマ目と再生の4拍目は区別する。

さらに、残ったコマにも膝の角度の不整合があるため、下半身は各姿勢の先頭コマに固定した。`installHeroAnimation` のシェーダーで、腰より上だけ位置合わせ済みのコマを再生し、胴体の装甲部分で固定画像につなぐ。足・ノズル・噴射の形状はコマ切り替えで変化させず、噴射は明るさだけを変える。静止・左右旋回の姿勢切り替えは維持する。

## 元プロジェクトからの利用

元プロジェクト：`C:/workspace/codex_sample`。ユーザー指定のリメイク用素材。

- `player-hover.png`：主人公のデザイン参照。
- `road-original.png`：元の `road-texture.png`。ゲームの金属的な路面を継承。
- `sidewalk-original.png`：参照用に保管した `side-deck-readable-v1.png`。
- `city-approach-bgm.mp3`、`city-approach-boss-bgm.mp3`：ステージ・ボスBGM。
- ロック・爆発の既存効果音も保管しているが、今回のプレイ中の効果音はWeb Audio合成。

元素材の権利を変更するものではない。過去のキャラクター3D試作や `references/base-mesh` の素材は今回のゲームでは読み込まない。

## コンセプトとの比較

維持した要素：濃紺の夜景、点灯した高密度の窓、段状の建物、ガラス連絡橋とトラス、曲がる道路、青い道路脇の灯り、少量のマゼンタ。

初回レンダーを見て、建物下の地面の欠落を修正し、ゲーム側で窓の発光を抑え、夜空と距離の霞を調整した。カメラが進むと近景・中景・遠景で別々に流れる実形状になっている。

コンセプトの個別建築や細かな汚れまで一致するものではない。試作では同じ建築キットの繰り返しが目立つ区間がある。主人公は新規ドット絵で、元の4コマをそのまま使ったものではない。
