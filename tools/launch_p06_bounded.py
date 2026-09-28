"""Hard wall-clock enforcement for one explicit custom GPU subprocess."""
import argparse,json,subprocess,sys,time
from pathlib import Path
parser=argparse.ArgumentParser(); parser.add_argument('--mode',choices=('qualify','fit','infer'),required=True); parser.add_argument('--method',required=True); parser.add_argument('--profile',type=Path,required=True); parser.add_argument('--output',type=Path,required=True); parser.add_argument('--cache-dir',required=True); args=parser.parse_args()
root=Path(__file__).resolve().parents[1]; config=json.loads((root/'configs/custom_p06.json').read_text()); cap=config['correctness']['max_seconds_per_method']
args.output.mkdir(parents=True,exist_ok=True)
report=args.output/f'{args.mode}-report.json'
if report.exists(): raise ValueError('existing_attempt_do_not_overwrite')
command=[sys.executable,str(root/'tools/run_p06_custom.py'),'--mode',args.mode,'--method',args.method,'--profile',str(args.profile),'--output',str(args.output),'--cache-dir',args.cache_dir]
start=time.perf_counter()
with (args.output/f'{args.mode}.log').open('w') as log:
    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
    try: code=process.wait(timeout=cap)
    except subprocess.TimeoutExpired:
        process.terminate()
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired: process.kill(); process.wait()
        value=json.loads(report.read_text()) if report.exists() else {}
        value.update(status='failed',failure_type='WallClockBudgetExceeded',reason='hard_subprocess_time_cap',seconds=time.perf_counter()-start,peak_allocated_bytes=None,peak_reserved_bytes=None)
        report.write_text(json.dumps(value,sort_keys=True)); code=124
if report.exists():
    value=json.loads(report.read_text()); print(json.dumps({k:v for k,v in value.items() if k!='source'}),flush=True)
else: print(json.dumps({'status':'failed','exit_code':code,'reason':'no_report'}),flush=True)
raise SystemExit(code)
