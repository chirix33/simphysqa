"""Reconstruct pinned local CPU dependencies in a fresh venv; no downloads."""
import argparse
from hashlib import sha256
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args(); output=args.output.resolve()
repo=Path(__file__).resolve().parents[1]
if output==repo or repo in output.parents:raise ValueError('use an external environment')
if output.exists():raise FileExistsError(output)
lock=repo/'configs/simphysqa/requirements-cpu.lock'
pins=dict(line.split('==') for line in lock.read_text().splitlines() if line and not line.startswith('#'))
for name,version in pins.items():
    if metadata.version(name)!=version:raise ValueError('local prerequisite mismatch: '+name)
subprocess.run([sys.executable,'-m','venv',str(output)],check=True)
site=output/('Lib/site-packages' if sys.platform=='win32' else f'lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages')
packages={}
for name,version in pins.items():
    dist=metadata.distribution(name); source_site=Path(dist.locate_file('')).resolve(); files={}
    for entry in dist.files or []:
        relative=Path(str(entry))
        if '..' in relative.parts or '__pycache__' in relative.parts:continue
        source=Path(dist.locate_file(entry)).resolve(); destination=(site/relative).resolve()
        if source_site not in source.parents or site.resolve() not in destination.parents:raise ValueError('unsafe distribution path')
        if not source.is_file():continue
        destination.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,destination)
        files[relative.as_posix()]=sha256(source.read_bytes()).hexdigest()
    packages[name]={'version':version,'files':files}
receipt={'version':'simphysqa-offline-cpu-setup/1.0.0','method':'fresh isolated venv with exact local distribution copy; editable pip installation is a separate command',
         'python':sys.version,'source_python':sys.executable,'venv':str(output),'lock_sha256':sha256(lock.read_bytes()).hexdigest(),'packages':packages,'network_calls':0}
(output/'offline-setup-manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'venv':str(output),'packages':len(packages),'network_calls':0}))
