"""Re-import each GLB in a fresh scene and compare actual mesh/triangle counts."""
import argparse
import json
from pathlib import Path
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from asset_utils import mesh_stats

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
out = Path(args.output).resolve()
manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
results = {}
for name in ('map', 'character'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    path = out / f'{name}.glb'
    assert path.stat().st_size > 100, f'Missing or empty GLB: {path}'
    bpy.ops.import_scene.gltf(filepath=str(path))
    actual = mesh_stats(bpy.context.scene.objects)
    expected = manifest['stats'][name]
    assert actual == expected, f'{name}: expected {expected}, got {actual}'
    assert actual['mesh_objects'] > 0 and actual['triangles'] > 0
    assert all(obj.data.materials for obj in bpy.context.scene.objects if obj.type == 'MESH')
    results[name] = {'status': 'passed', **actual}
assert (out / 'scene.blend').stat().st_size > 100
if manifest['rendered']:
    assert (out / 'preview.png').read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'
(out / 'verification.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print('VERIFICATION PASSED:', results)
