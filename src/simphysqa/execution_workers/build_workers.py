"""Offline, asserted source transformation; generation calls/settings unchanged.

Writes separate snapshots. Never edits frozen sources. Every replacement must
match exactly once; transformations and hashes form the reviewable provenance.
"""
from pathlib import Path
import argparse
import hashlib
import json


def build(preparation, output):
    preparation, output = Path(preparation), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    receipts = []
    for path in sorted((preparation / 'workers').glob('*.py')):
        original = path.read_text(encoding='utf-8'); text = original; changes = []
        gemma = 'GGUF' in original
        def replace(old, new, count=1):
            nonlocal text
            if text.count(old) != count: raise ValueError(path.name + ': transformation mismatch: ' + old[:90])
            text = text.replace(old, new); changes.append({'before': old, 'after': new, 'count': count})
        replace('def put(p,x):\n', 'instrument = None\n\ndef put(p,x):\n    if instrument is not None:x=instrument.enrich(p,x)\n')
        replace('def main():\n', 'def main():\n    global instrument\n')
        replace("a=p.parse_args();", "p.add_argument('--execution-context',type=Path,required=True)\n    a=p.parse_args();")
        variable = 'c' if gemma else 'condition'
        anchor = "    if any(q['tools']"  # inject before tools check, after args parsed
        pos = text.index(anchor)
        text = text[:pos] + "    from execution_support import Instrumentation,termination\n    instrument=Instrumentation(a.execution_context,__file__,a.condition)\n" + text[pos:]
        changes.append({'injection': 'required standalone Instrumentation before backend imports'})
        if gemma:
            replace("sha(__file__)!=c['worker_sha256'] or ", '')
            replace("'CUDA0' not in devices.stdout or 'NVIDIA GeForce RTX 5090' not in devices.stdout",
                    "instrument.context['llama_device'] not in devices.stdout or instrument.context['gpu_name'] not in devices.stdout")
            replace("'--device','CUDA0'", "'--device',instrument.context['llama_device']")
            replace("            prompt=call('/apply-template'", "            instrument.begin_stage()\n            prompt=call('/apply-template'")
            replace("            except (TimeoutError,socket.timeout):", "            except KeyboardInterrupt:status='interrupted';reason='KeyboardInterrupt; partial stream retained'\n            except (TimeoutError,socket.timeout):")
            replace("'peak_loading_device_memory_mib':peak[0]", "'peak_loading_device_memory_mib':instrument.monitor.report(instrument.process_start)['sampled_peak_mib']")
            # Remove deficient old extra monitor. Common monitor is authoritative.
            start = text.index('    peak=[0];stop=threading.Event()')
            end = text.index('    args=[str(server)', start)
            changes.append({'before': text[start:end], 'after': '    peak=[None]\n'})
            text = text[:start] + '    peak=[None]\n' + text[end:]
            replace('        stop.set();proc.terminate()', '        instrument.close();proc.terminate()')
        else:
            replace("if torch.cuda.get_device_name(0)!='NVIDIA GeForce RTX 5090':raise RuntimeError('GPU identity changed')",
                    "instrument.require_gpu(torch.cuda.get_device_name(0),torch.version.cuda)")
            replace("versions={k:importlib.metadata.version(k) for k in ('torch','transformers','tokenizers','safetensors')}",
                    "versions={k:importlib.metadata.version(k) for k in condition['runtime_versions']}")
            replace("        torch.manual_seed(s['seed']);", "        instrument.begin_stage()\n        torch.manual_seed(s['seed']);")
            replace("started=time.monotonic();status='completed';reason=None;output=[];raw=''", "started=time.monotonic();status='completed';reason=None;output=[];raw='';last=None;backend_reason=None;stop_evidence=None")
            replace("                if not output or output[-1] not in eos:",
                    "                stop_evidence={'method':'terminal generated token versus model.generation_config EOS IDs and elapsed deadline', 'last_token':output[-1] if output else None, 'eos_token_ids':eos}\n                if not output or output[-1] not in eos:")
            replace("                    output=list(last.outputs[0].token_ids)",
                    "                    output=list(last.outputs[0].token_ids)\n                    backend_reason={'finish_reason':last.outputs[0].finish_reason,'stop_reason':last.outputs[0].stop_reason}")
            replace("        except Exception as e:status='failed';reason=type(e).__name__+': '+str(e)[:220]",
                    "        except KeyboardInterrupt:\n            status='interrupted';reason='KeyboardInterrupt; available output retained'\n            if last and last.outputs:output=list(last.outputs[0].token_ids)\n            raw=tokenizer.decode(output,skip_special_tokens=True)\n        except Exception as e:\n            status='failed';reason=type(e).__name__+': '+str(e)[:220]\n            if last and last.outputs:output=list(last.outputs[0].token_ids)\n            raw=tokenizer.decode(output,skip_special_tokens=True)")
            replace("'raw_output':raw,'output_token_ids':output", "'termination':termination(status,backend_reason,stop_evidence or {'failure_reason':reason}),\n            'raw_output':raw,'output_token_ids':output")
            replace("    put(a.output/'completed.json'", "    instrument.close()\n    put(a.output/'completed.json'")
        # Persist interrupted partial output, then stop; later reserved keys remain unknown.
        lines = text.splitlines()
        index = next(i for i, line in enumerate(lines) if 'put(result,value);print' in line or "put(a.output/'results'/(stem+'.json'),value);print" in line)
        indent = ' ' * (12 if gemma else 8)
        lines.insert(index + 1, indent + "if status=='interrupted':break")
        text = '\n'.join(lines) + '\n'
        changes.append({'injection': 'break after immutable interrupted partial result'})
        compile(text, path.name, 'exec')
        dest = output / path.name
        dest.write_text(text, encoding='utf-8', newline='\n')
        receipts.append({'condition_id': path.stem, 'original_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                         'instrumented_sha256': hashlib.sha256(dest.read_bytes()).hexdigest(), 'changes': changes})
    (output / 'transformations.json').write_text(json.dumps({'version': 'SPQ06-workers/1.0.0', 'workers': receipts}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--preparation', required=True); p.add_argument('--output', required=True)
    a = p.parse_args(); build(a.preparation, a.output)
