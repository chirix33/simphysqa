#!/usr/bin/env bash
# Isolated core runtime. Never reuse or modify either latent-baseline environment.
set -euo pipefail
task_core="$HOME/phi-jepa/.venvs/phi-core"
python3 -m venv "$task_core"
"$task_core/bin/python" -m pip install 'pip==25.1.1'
"$task_core/bin/python" -m pip install 'torch==2.7.1' --index-url https://download.pytorch.org/whl/cu128
"$task_core/bin/python" -m pip install 'transformers==4.51.3' 'tokenizers==0.21.1' 'huggingface-hub==0.30.2' 'safetensors==0.5.3' 'python-dotenv==1.1.0' 'numpy==2.2.4'
"$task_core/bin/python" -m pip check
