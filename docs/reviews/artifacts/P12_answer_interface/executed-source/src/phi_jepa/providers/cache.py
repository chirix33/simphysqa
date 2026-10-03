"""Content-addressed frozen outputs; projected tensors never enter this cache."""
import os
from pathlib import Path
import tempfile

from phi_jepa.artifacts import canonical, digest
from phi_jepa.integration.readers import strict_json
from .contracts import FailureCode, ProviderFailure


class FrozenOutputCache:
    def __init__(self, root: Path):
        self.root = Path(root)

    def read(self, request):
        path = self.root / (digest(request) + '.json')
        if not path.exists():
            return None
        try:
            if path.is_symlink():
                raise ValueError('symlink')
            record = strict_json(path.read_text(encoding='utf-8'))
            if set(record) != {'request_sha256', 'output', 'output_sha256'}:
                raise ValueError('record fields')
            if record['request_sha256'] != digest(request) or digest(record['output']) != record['output_sha256']:
                raise ValueError('identity')
            return record['output']
        except (ValueError, TypeError, KeyError):
            raise ProviderFailure(FailureCode.CACHE_INTEGRITY) from None

    def write(self, request, output):
        self.root.mkdir(parents=True, exist_ok=True)
        record = dict(request_sha256=digest(request), output=output, output_sha256=digest(output))
        # Publish complete bytes atomically; interruption leaves no partial hit.
        descriptor, temporary = tempfile.mkstemp(dir=self.root, prefix='.pending-')
        try:
            with os.fdopen(descriptor, 'wb') as handle:
                handle.write(canonical(record))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.root / (digest(request) + '.json'))
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
