const fs=require('node:fs');
const path=require('node:path');
const esbuild=require('C:/workspace/codex_sample/node_modules/esbuild/lib/main.js');
const dir=path.resolve(process.argv[2]);
const result=esbuild.buildSync({entryPoints:[path.join(__dirname,'player-viewer.js')],bundle:true,write:false,minify:true,format:'iife',legalComments:'eof'});
const script=result.outputFiles[0].text;
const info=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'),'utf8'));
const html=`<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PLAYER · 3D prototype</title>
<style>*{box-sizing:border-box}body{margin:0;background:#171c29;color:#eef0ff;font:14px/1.6 system-ui,sans-serif}main{display:grid;grid-template-columns:310px 1fr;height:100vh}aside{padding:34px 25px;background:#202534;border-right:1px solid #373b50;overflow:auto}.tag{font-size:11px;letter-spacing:.18em;color:#bcb1ee}h1{font-size:29px;line-height:1.3;margin:12px 0 7px}p{color:#abb3c9}h2{font-size:12px;letter-spacing:.1em;color:#a79dc8;margin:30px 0 10px}.buttons{display:flex;gap:7px;flex-wrap:wrap}button{border:1px solid #4b4c67;background:#282d40;color:#dfe1f7;border-radius:7px;padding:9px 14px;font:inherit;cursor:pointer}button:hover{background:#3c3b58}button.active{background:#6c5596;border-color:#bc95ec;color:white}dl{display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px}dt{color:#adb3c9}dd{margin:0;text-align:right}.note{font-size:12px;color:#8994af;border-top:1px solid #393e52;margin-top:25px;padding-top:15px}#viewport{position:relative;min-width:0;min-height:0}#viewport canvas{display:block}#status{position:absolute;bottom:22px;left:0;right:0;text-align:center;color:#a9b4cc;font-size:12px;pointer-events:none}a{color:#cbb5ff}@media(max-width:700px){main{grid-template-columns:1fr;grid-template-rows:auto 65vh;height:auto}aside{padding:20px}h2{margin-top:14px}dl,.note{display:none}}</style>
<main><aside><div class="tag">P.A.T.H.O.S / CHARACTER STUDY</div><h1>PLAYER<br>3D PROTOTYPE</h1><p>三面図から起こした、テクスチャ付きローポリの初稿。</p>
<h2>VIEW</h2><div class="buttons"><button data-view="front">正面</button><button data-view="side">側面</button><button data-view="back">背面</button><button class="active" data-view="perspective">斜め</button></div>
<h2>INSPECT</h2><div class="buttons"><button id="rotate">自動回転</button><button id="motion">ホバー再生</button><button id="wire">ワイヤー</button><button id="grid" class="active">グリッド</button></div>
<h2>MODEL</h2><dl><dt>三角形</dt><dd>${info.triangles.toLocaleString()}</dd><dt>ボーン</dt><dd>${info.bones}</dd><dt>マテリアル</dt><dd>1</dd><dt>カラー</dt><dd>2048 px</dd><dt>発光</dt><dd>512 px</dd></dl>
<p class="note">簡易ボーンによる試作です。表情・揺れ物の物理・噴射炎は未実装。ゲーム本体への組み込み前の確認用です。</p></aside><section id="viewport"><div id="status">モデルを読み込み中…</div></section></main>
<script>window.PLAYER_GLB=${JSON.stringify(fs.readFileSync(path.join(dir,'player.glb')).toString('base64'))};</script><script>${script.replace(/<\/script/gi,'<\\/script')}</script></html>`;
fs.writeFileSync(path.join(dir,'viewer.html'),html);
fs.copyFileSync('C:/workspace/codex_sample/node_modules/three/LICENSE',path.join(dir,'THREE-LICENSE.txt'));
console.log('Standalone viewer written:',path.join(dir,'viewer.html'));
