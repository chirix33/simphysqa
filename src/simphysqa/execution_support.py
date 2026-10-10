"""SPQ06 portable worker instrumentation 1.0.0; stdlib, public-only.

This module never imports the dataset, parsers, scorers or coordinator resources.
The adapter must reserve centrally before launching a worker. Sampling is device
wide and may miss peaks; it is not torch's process allocator measurement.
"""
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import threading
import time

VERSION = 'SPQ06-execution/1.0.0'


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


class MemoryMonitor:
    def __init__(self, command, device, interval=.5, reader=None):
        self.command, self.device, self.interval = command, device, interval
        self.reader = reader or self._read
        self.samples, self.errors = [], []
        self.lock, self.stop = threading.Lock(), threading.Event()
        self.thread = None

    def _read(self):
        result = subprocess.run([self.command, '-i', self.device, '--query-gpu=uuid,name,memory.used',
                                 '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=3)
        if result.returncode:
            raise RuntimeError(result.stderr.strip())
        uuid, name, used = result.stdout.strip().split(',')
        return {'device_uuid': uuid.strip(), 'device_name': name.strip(), 'used_mib': int(used)}

    def sample(self):
        try:
            value = {**self.reader(), 'monotonic_seconds': time.monotonic()}
            with self.lock:
                self.samples.append(value)
        except Exception as exc:
            with self.lock:
                self.errors.append({'monotonic_seconds': time.monotonic(), 'error': str(exc)[:500]})

    def start(self):
        def run():
            while not self.stop.is_set():
                self.sample()
                self.stop.wait(self.interval)
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def report(self, since=0):
        with self.lock:
            samples = [s for s in self.samples if s['monotonic_seconds'] >= since]
            errors = [e for e in self.errors if e['monotonic_seconds'] >= since]
        return {'source': 'nvidia-smi device-wide memory.used', 'device_selector': self.device,
                'sampling_interval_seconds': self.interval, 'successful_sample_count': len(samples),
                'sampled_peak_mib': max((s['used_mib'] for s in samples), default=None),
                'status': 'available' if samples else 'unavailable',
                'unavailable_reason': None if samples else 'no successful samples in this interval',
                'samples': samples, 'errors': errors, 'may_miss_peaks': True}

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=4)


def termination(status, backend_reason=None, evidence=None):
    category = {'completed': 'complete', 'length_limited': 'length_limited', 'timeout': 'timed_out',
                'failed': 'failed', 'interrupted': 'interrupted', 'unknown': 'unknown',
                'unexecuted_conditional': 'unexecuted_conditional'}.get(status, 'unknown')
    return {'category': category, 'raw_backend_reason': backend_reason,
            'reason_source': 'backend' if backend_reason is not None else 'derived' if evidence else 'unavailable',
            'derivation': evidence, 'semantic_refusal': None, 'semantic_refusal_status': 'not_measured'}


class Instrumentation:
    def __init__(self, context_path, worker_path, condition_path):
        self.context = json.loads(Path(context_path).read_bytes())
        c = self.context
        if c['version'] != VERSION or sha(worker_path) != c['worker_sha256'] or sha(condition_path) != c['resolved_condition_sha256']:
            raise ValueError('instrumented worker/config identity mismatch')
        scope = c.get('execution_scope', 'main')
        qualified = c['qualification_status'] == 'task_qualified'
        if scope == 'development_rehearsal':
            # Bootstrap requires fresh hardware/runtime qualification, but cannot
            # require task results from the rehearsal that it is about to measure.
            qualified = c['qualification_status'] in ('runtime_qualified', 'task_qualified')
            if not c.get('development_manifest_sha256') or not c.get('development_sample_ids') or len(c['stage_reservations']) > 6:
                raise ValueError('bounded prespecified development rehearsal context required')
            if any(key.split('|')[0] not in c['development_sample_ids'] for key in c['stage_reservations']):
                raise ValueError('rehearsal reservation outside development manifest')
        elif scope != 'main':
            qualified = False
        if not qualified or not c['process_reservation'] or not c['stage_reservations']:
            raise ValueError('qualified runtime and central reservations required')
        self.process_start = time.monotonic()
        self.monitor = MemoryMonitor(c['nvidia_smi'], c['device_uuid'], c['memory_interval_seconds'])
        device = self.monitor.reader()
        if device['device_uuid'] != c['device_uuid'] or device['device_name'] != c['gpu_name']:
            raise RuntimeError('qualified device UUID/name changed')
        query = subprocess.run([c['nvidia_smi'], '-i', c['device_uuid'], '--query-gpu=driver_version,memory.total',
            '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=3)
        if query.returncode: raise RuntimeError('hardware runtime preflight unavailable: ' + query.stderr)
        driver, memory = [v.strip() for v in query.stdout.strip().split(',')]
        hw = c['hardware_runtime']
        if driver != hw['driver'] or int(memory) != hw['vram_mib'] or platform.platform() != hw['os']:
            raise RuntimeError('qualified driver/VRAM/OS changed')
        self.observed_hardware = {'driver': driver, 'os': platform.platform(), 'vram_mib': int(memory)}
        self.monitor.start()
        self.stage_start = None

    def begin_stage(self):
        self.stage_start = time.monotonic()

    def enrich(self, path, value):
        value = dict(value)
        c = self.context
        if path.parent.name == 'results':
            key = '|'.join((value['sample_id'], value['condition_id'], c['representation'], str(value['stage'])))
            if key not in c['stage_reservations']:
                raise ValueError('unreserved stage')
            value.update({'execution_version': VERSION, 'representation': c['representation'], 'stage_key': key,
                          'execution_scope': c.get('execution_scope', 'main'), 'qualification_status': c['qualification_status'],
                          'qualification_sha256': c['qualification_sha256'], 'assignment_sha256': c['assignment_sha256'],
                          'hardware_runtime_sha256': c['hardware_runtime_sha256'], 'worker_sha256': c['worker_sha256'],
                          'scientific_condition_sha256': c['scientific_condition_sha256'],
                          'process_reservation': c['process_reservation'], 'stage_reservation': c['stage_reservations'][key],
                          'total_stage_seconds': time.monotonic() - self.stage_start if self.stage_start is not None else None,
                          'total_stage_boundaries': 'before seed/render/tokenization through result construction; excludes result file write',
                          'device_memory': self.monitor.report(self.stage_start or time.monotonic()),
                          'cpu_fallback': False})
            if 'termination' not in value:
                events = value.get('raw_stream_events', [])
                reason = events[-1].get('stop_type') if events and events[-1].get('stop') else None
                value['termination'] = termination(value['completion_status'], reason,
                    {'status': value['completion_status'], 'failure_reason': value.get('failure_reason')} if reason is None else None)
            # Legacy Gemma zero was not an unavailable measurement. New values are nullable.
            if 'peak_device_memory_mib' in value:
                value['peak_device_memory_mib'] = value['device_memory']['sampled_peak_mib']
        elif path.name in ('runtime.json', 'completed.json'):
            value.update({'execution_version': VERSION, 'qualification_sha256': c['qualification_sha256'],
                          'hardware_runtime_sha256': c['hardware_runtime_sha256'], 'process_reservation': c['process_reservation'],
                          'process_elapsed_seconds_at_receipt': time.monotonic() - self.process_start,
                          'device_memory': self.monitor.report(self.process_start)})
            value['gpu_name'] = c['gpu_name']
            value['device_uuid'] = c['device_uuid']
            value['hardware_runtime_observed'] = self.observed_hardware
        return value

    def require_gpu(self, actual_name, cuda_runtime=None):
        if actual_name != self.context['gpu_name']:
            raise RuntimeError('qualified GPU identity changed; CPU fallback forbidden')
        if cuda_runtime != self.context['hardware_runtime']['cuda_runtime']:
            raise RuntimeError('qualified CUDA runtime changed')

    def close(self):
        self.monitor.close()
