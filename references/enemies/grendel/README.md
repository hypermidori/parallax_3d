# GRENDEL HOVER

原作の多脚戦車（original-enemies.png の右下）を、脚を収納して浮く重装甲ボスへ再設計。
内蔵画像生成で２D案と専用アトラスを作成し、その案を基準にBlender CLIで造形した。

- デザイン画：design-v01.png
- デザイン生成条件：design-prompt.txt
- テクスチャ生成条件：atlas-prompt.txt
- ゲーム用：public/assets/grendel-hover.glb
- 画像テクスチャ：public/assets/grendel-atlas.png（1536 × 1024、GLBにも埋め込み）
- 14,500三角形、９マテリアル。全39描画メッシュにUVと画像テクスチャ。
- 中央装甲、左右の大型ポッド、上部・下部の赤いセンサー、４本の収納脚と青い下向き推進器。
- 高密度なコンセプトの微細部品は簡略化し、輪郭と主要構造を優先したゲーム用モデル。

## 動きと戦闘

src/grendel-motion.js がゲームと比較画面の共通の浮遊処理。
脚は固定した収納姿勢のまま。機体の微小な上下動・傾斜と、４つの噴射の長さだけを動かす。
アニメーションはシミュレーション時間に従い、ポーズ中は止まる。

ゲーム内では1.25倍で表示し、原点高さ1.8mを基準に浮遊。夜間でも塗装が読めるよう弱い補助発光を設定。
ShotOrigin と AimTarget を赤い中央コアに配置。発射点と照準・レーザーの到達点が機体の姿勢に追従する。
HP2200、３段階の弾幕、前方68mを保つ移動と市街地のループは従来の仕様を使う。

## 再生成

```powershell
.\tools\blender.ps1 --background --factory-startup --python-exit-code 1 --python .\blender_scripts\build_grendel.py
```

編集用部品を残したシーン：output/grendel-hover/grendel-hover.blend
レンダーと統計：同じフォルダの beauty.png / top.png / front.png / manifest.json
出力時に装甲をまとめ、FoldedLeg0〜3、HoverJet0〜3 と各アンカーを保持する。

比較画面：enemy-lab.html?model=boss（浮遊、回転、正面・上・横、夜間照明）。
検証用の直接ボス戦：?debug=1&bossPreview=1。通常の開始は従来どおり道中から。

## 検証

```powershell
node scripts/verify-grendel.mjs
node scripts/verify-browser.mjs
node --test tests/*.test.mjs
npm run build
```

verify-grendel は全表面の画像テクスチャ、描画量、４推進器、実際の弾の発生点、浮遊の範囲、
脚の固定、ポーズ、描画資源の増加がないこと、縦画面の照準、３段階の戦闘と撃破・再試行を確認する。
通しプレイは通常の道中からの進行も確認。無敵・加速オートプレイは進行確認用で、難易度の評価ではない。
スマホ実機のフレームレートは未確認。
