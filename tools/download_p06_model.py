"""Explicit pinned download boundary; all model loads later are local-only."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from huggingface_hub import snapshot_download

parser=argparse.ArgumentParser(); parser.add_argument('--cache-dir',required=True); parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
root=Path(__file__).resolve().parents[1]; config=json.loads((root/'configs/custom_p06.json').read_text())
if not config['download']['authorized']: raise ValueError('download_not_authorized')
path=Path(snapshot_download(config['model'],revision=config['revision'],cache_dir=args.cache_dir,max_workers=config['download']['max_workers'],
    allow_patterns=['config.json','generation_config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json','spiece.model','model.safetensors']))
files={p.name:{'sha256':sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in path.iterdir() if p.is_file()}
if files['model.safetensors']['bytes']>config['download']['max_model_weight_bytes']: raise ValueError('weight_size_cap')
args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'model':config['model'],'revision':config['revision'],'files':files},indent=2))
print(json.dumps({'model':config['model'],'revision':config['revision'],'files':len(files),'bytes':sum(f['bytes'] for f in files.values())}))
