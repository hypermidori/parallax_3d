# 敵モデルの制作資料

| 種類 | 名前 | 三角形数 | 制作資料 |
|---|---|---:|---|
| 偵察機 | AMBER FIREFLY | 3,940 | [資料](firefly/README.md) |
| 迎撃機 | AZURE KESTREL | 5,616 | [資料](kestrel/README.md) |
| 地上砲台 | IRON WARDEN | 2,288 | [資料](warden/README.md) |

それぞれ２D案を決めてからBlenderで造形し、画像テクスチャを貼ったモデル。
比較画面 enemy-lab.html のMODEL選択で切り替えできる。地上砲台は砲身を持たず、中央の発光コアから弾を出す。

検証：node scripts/verify-support-enemies.mjs
