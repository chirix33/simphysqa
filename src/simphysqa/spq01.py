"""SPQ01 command-line entry points."""
import argparse
from pathlib import Path
from .audit_method import check
from .dataset import load
from .job import comparison, dry_run, export_development, run
from .release import inventory, select
from .io import canonical, read

def main(argv=None):
    parser=argparse.ArgumentParser(prog="python -m simphysqa.spq01")
    sub=parser.add_subparsers(dest="command",required=True)
    inv=sub.add_parser("inventory")
    inv.add_argument("--data-root",type=Path,required=True)
    inv.add_argument("--output",type=Path,required=True)
    sel=sub.add_parser("select")
    sel.add_argument("--inventory",type=Path,required=True)
    sel.add_argument("--output",type=Path,required=True)
    sel.add_argument("--exclusions",type=Path,required=True)
    sel.add_argument("--seed",type=int,default=20261004)
    stat=sub.add_parser("audit-check")
    stat.add_argument("--script",type=Path,default=Path("docs/references/spq01_audit/audit_power_analysis.py"))
    stat.add_argument("--output",type=Path,required=True)
    stat.add_argument("--seed",type=int,default=20261004)
    stat.add_argument("--replicates",type=int,default=200000)
    for name in ("dry-run","annotate","export-development","compare-prepare"):
        p=sub.add_parser(name)
        p.add_argument("--records",type=Path,required=True)
        p.add_argument("--output",type=Path,required=True)
        if name in ("dry-run","annotate","compare-prepare"):
            p.add_argument("--config",type=Path,default=Path("configs/simphysqa/annotation_spq01.json"))
        if name=="export-development":
            p.add_argument("--job",type=Path,required=True)
        if name=="compare-prepare":
            p.add_argument("--alternative",type=Path,default=Path("configs/simphysqa/annotation_alternative.proposed.json"))
    verify=sub.add_parser("verify-development")
    verify.add_argument("--selection",type=Path,required=True)
    verify.add_argument("--job",type=Path,required=True)
    verify.add_argument("--development",type=Path,required=True)
    verify.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    if args.command=="inventory":
        result=inventory(args.data_root,args.output)
    elif args.command=="select":
        config=read(args.exclusions)
        result=select(args.inventory,args.output,config["excluded_groups"],args.seed)
        result={k:v for k,v in result.items() if k not in ("selected","variation")}
    elif args.command=="audit-check":
        result=check(args.script,args.output,args.seed,args.replicates)
    elif args.command=="verify-development":
        from .verification import verify
        result=verify(args.selection,args.job,args.development,args.output)
    else:
        records=list(load(args.records))
        if args.command=="dry-run":
            result=dry_run(records,read(args.config),args.output)
        elif args.command=="annotate":
            result=run(records,read(args.config),args.output)
        elif args.command=="export-development":
            result=export_development(records,args.job,args.output)
        elif args.command=="compare-prepare":
            result=comparison(records,read(args.config),read(args.alternative),args.output)
    print(canonical(result).decode(),end="")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
