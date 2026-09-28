"""Inspect only approved model definitions; never execute or dump notebook globals."""
import ast,json
from pathlib import Path
from hashlib import sha256
root=Path(__file__).resolve().parents[1]
path=root/'Phi_JEPA_Final_+_Baselines.ipynb'
c=json.loads((root/'configs/custom_p06.json').read_text())
if sha256(path.read_bytes()).hexdigest()!=c['notebook_sha256']: raise ValueError('notebook_identity')
print('NOTEBOOK_SHA256',sha256(path.read_bytes()).hexdigest())
for i,cell in enumerate(json.loads(path.read_text(encoding='utf-8'))['cells']):
    if cell['cell_type']!='code': continue
    source=''.join(cell['source'])
    source='\n'.join('' if line.lstrip().startswith(('!','%')) else line for line in source.splitlines())
    try: tree=ast.parse(source)
    except SyntaxError: continue
    for node in tree.body:
        if isinstance(node,ast.ClassDef) and any(x in node.name.lower() for x in ('coconut','codi','latent')):
            print(f'CELL {i} CLASS {node.name}')
            print(ast.unparse(node))
