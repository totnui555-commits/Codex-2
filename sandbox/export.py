"""Immutable snapshot exporter. All output is independently validated by the host."""
import base64,hashlib,json
from pathlib import Path
root=Path('/workspace/repo').resolve();files=[]
for path in sorted(root.rglob('*')):
    if path.is_symlink():continue
    if not path.is_file():continue
    relative=path.relative_to(root)
    if any(p in {'.git','node_modules','__pycache__','.venv'} or p.startswith('.env') for p in relative.parts):continue
    if path.suffix not in {'.py','.ts','.tsx','.js','.jsx','.css','.html','.md','.json','.txt'}:continue
    data=path.read_bytes()
    if len(data)>200000:raise ValueError('Export limit exceeded')
    files.append({'path':str(relative),'content':base64.b64encode(data).decode(),'sha256':hashlib.sha256(data).hexdigest()})
    if len(files)>50:raise ValueError('Export count limit exceeded')
Path('/workspace/export.json').write_text(json.dumps({'files':files}))
