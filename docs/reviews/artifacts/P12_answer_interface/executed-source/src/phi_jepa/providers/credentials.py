"""Explicit dotenv/key-file boundary; never inspect notebook or legacy keys."""
from pathlib import Path

from .contracts import FailureCode, ProviderFailure


def load_openai_key(env_file):
    from dotenv import dotenv_values
    path = Path(env_file).resolve()
    try:
        # No environment mutation/interpolation, and no key value in diagnostics.
        values = dotenv_values(path, interpolate=False)
        reference = values.get('OPENAI_API_KEY_FILE')
        if not reference:
            raise ValueError('missing reference')
        key = (path.parent / reference).read_text(encoding='utf-8-sig').strip()
        if not key or any(c.isspace() for c in key):
            raise ValueError('malformed key file')
        return key
    except (OSError, ValueError):
        raise ProviderFailure(FailureCode.MISSING_CREDENTIALS) from None
