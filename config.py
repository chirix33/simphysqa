from pathlib import Path

MODE = "fixture"        # "openai", "manual", or "fixture"
MODEL = "gpt-4.1-mini-2025-04-14"
SEED = 7
EPOCHS = 400

# A cap, not a target. Normally: 3 roles x 2 phases x 5 examples = 30 requests.
# Repair rounds can increase the count. SDK HTTP retries are bounded separately.
MAX_API_CALLS = 90
MAX_OUTPUT_TOKENS = 4096

# Only run outputs are saved here; no source files or packages are created.
RESULTS_ROOT = Path("metacognition_results")

# The key is read from the environment, never hardcoded. Set OPENAI_API_KEY
# before running in "openai" mode, e.g. via a .env file or your shell profile.
