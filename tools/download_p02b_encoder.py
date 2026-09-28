"""Explicit authorized download boundary. Never called by model inference."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from phi_jepa.providers.qwen import MODEL, REVISION

parser = argparse.ArgumentParser()
parser.add_argument('--cache-dir', required=True)
args = parser.parse_args()
from huggingface_hub import snapshot_download
path = snapshot_download(MODEL, revision=REVISION, cache_dir=args.cache_dir,
    allow_patterns=['config.json', 'model.safetensors', 'tokenizer.json',
                    'tokenizer_config.json', 'vocab.json', 'merges.txt',
                    'modules.json', '1_Pooling/config.json', 'config_sentence_transformers.json'],
    max_workers=2)
print(json.dumps({'model': MODEL, 'revision': REVISION, 'snapshot_path': path}))
