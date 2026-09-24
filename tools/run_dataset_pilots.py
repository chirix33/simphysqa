"""Reproducible bounded smoke + calibration orchestration, no final generation."""
import argparse
from phi_jepa.simulation.common import ROOT,read
from phi_jepa.simulation.pipeline import run

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--domains",nargs="+",required=True)
    parser.add_argument("--resume",action="store_true")
    args=parser.parse_args()
    for domain in args.domains:
        path="configs/dataset_refined_pilot.json" if domain in ("robotic_arm","driving") else "pilot_config.json"
        config=read(ROOT/path); config["limits"]["max_run_wall_seconds"]=1800
        for mode,count in (("smoke",20),("calibrate",100)):
            output=ROOT/"dataset-runs/final"/domain/mode
            result=run(config,domain,count,output,mode,args.resume)
            print(domain,mode,result["counts"],flush=True)

if __name__=="__main__": main()
