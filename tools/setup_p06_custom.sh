#!/usr/bin/env bash
set -euo pipefail
# Separate environments; never modify the existing upstream or core environments.
for method in coconut codi; do
  env_path="$HOME/phi-jepa/.venvs/phi-${method}-custom"
  if [ ! -x "$env_path/bin/python" ]; then python3 -m venv "$env_path"; fi
  "$env_path/bin/python" -m pip install pip==25.1.1
  "$env_path/bin/python" -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128
  "$env_path/bin/python" -m pip install transformers==4.51.3 tokenizers==0.21.1 safetensors==0.5.3 huggingface-hub==0.30.2 numpy==2.2.4 sentencepiece==0.2.0 protobuf==5.29.4
  "$env_path/bin/python" -m pip check
  "$env_path/bin/python" -m pip freeze > "configs/${method}-custom-p06.lock.txt"
done
