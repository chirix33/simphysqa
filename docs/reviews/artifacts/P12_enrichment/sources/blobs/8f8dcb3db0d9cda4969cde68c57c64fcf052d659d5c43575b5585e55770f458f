"""phi-dataset entry point. Simulator imports occur only inside engine calls."""
import argparse
import json
from pathlib import Path
from .common import ROOT,read,write

def main(argv=None):
    parser=argparse.ArgumentParser(prog="phi-dataset")
    sub=parser.add_subparsers(dest="command",required=True)
    env=sub.add_parser("inspect-environment"); env.add_argument("--device-step",action="store_true"); env.add_argument("--output",type=Path)
    schema=sub.add_parser("validate-schema"); schema.add_argument("--path",type=Path,default=ROOT/"example_record.json"); schema.add_argument("--kind",choices=["record","public_record","bundle"],default="record")
    for name in ("smoke","calibrate","compare-engines"):
        cmd=sub.add_parser(name); cmd.add_argument("--domain",required=True); cmd.add_argument("--config",type=Path,default=ROOT/"pilot_config.json")
        cmd.add_argument("--scenarios" if name!="compare-engines" else "--pairs",type=int,default=100 if name=="calibrate" else 20)
        cmd.add_argument("--output",type=Path); cmd.add_argument("--resume",action="store_true")
    for name in ("validate-dataset","export-public"):
        cmd=sub.add_parser(name); cmd.add_argument("--path",type=Path,required=True)
    gen=sub.add_parser("generate"); gen.add_argument("--config",type=Path,required=True); gen.add_argument("--resume",action="store_true")
    args=parser.parse_args(argv)
    try:
        if args.command=="inspect-environment":
            from .environment import inspect_environment
            result=inspect_environment(device_step=args.device_step)
            if args.output: write(args.output,result)
        elif args.command=="validate-schema":
            from .validation import validator
            validator(args.kind).validate(read(args.path)); result={"schema":"pass","physics":"not_checked"}
        elif args.command in ("smoke","calibrate"):
            from .pipeline import run
            output=args.output or ROOT/"dataset-runs"/(args.command+"-"+args.domain)
            result=run(read(args.config),args.domain,args.scenarios,output,args.command,args.resume)
            result={k:result[k] for k in ("status","counts","wall_seconds","peak_rss_bytes","disk_bytes")}
        elif args.command=="validate-dataset":
            from .pipeline import validate_dataset
            result=validate_dataset(args.path)
        elif args.command=="export-public":
            from .pipeline import export
            result={"exported":export(args.path)}
        elif args.command=="compare-engines":
            from .diagnostics import compare_engines
            result=compare_engines(read(args.config),args.domain,args.pairs,args.output or ROOT/"dataset-runs"/"arm-comparison")
        elif args.command=="generate":
            from .release import generate
            result=generate(args.config,args.resume)
        print(json.dumps(result,indent=2,allow_nan=False))
        return 0
    except Exception as exc:
        print(json.dumps({"status":"failed","error":type(exc).__name__+": "+str(exc)}))
        return 1

if __name__=="__main__":
    raise SystemExit(main())
