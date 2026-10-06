"""Model-conditioned score test and finite-sample checks of the supplied PowerBinary approximation."""
from pathlib import Path
import contextlib
import importlib.util
import io
import json
import math
from hashlib import sha256
from .io import external, manifest, write

def reproduce(script: Path):
    spec=importlib.util.spec_from_file_location("supplied_audit_power_analysis",script)
    module=importlib.util.module_from_spec(spec)
    buffer=io.StringIO()
    with contextlib.redirect_stdout(buffer):
        spec.loader.exec_module(module)
    return json.loads(buffer.getvalue()),module

def check(script: Path, output: Path, seed=20261004, replicates=200000):
    import numpy as np
    import scipy
    from scipy.stats import chi2, norm, multinomial
    planning,module=reproduce(script)
    p,k0,k1,n=.90,.60,.80,140
    q0=np.array(module.count_probabilities(k0,p))
    q1=np.array(module.count_probabilities(k1,p))
    derivative=np.array([p*((1-p)**2+1-p),-3*p*(1-p)**2,-3*p*p*(1-p),p*(1-p*p)])
    weights=derivative/q0
    information=float(sum(derivative*weights))
    critical=float(chi2.ppf(.80,1))
    rng=np.random.Generator(np.random.PCG64(seed))
    results={}
    for label,probs in (("type_I_error",q0),("power",q1)):
        cells=rng.multinomial(n,probs,size=replicates)
        statistic=(cells@weights)**2/(n*information)
        rejects=int(sum(statistic>critical))
        rate=rejects/replicates
        z=float(norm.ppf(.975))
        center=(rate+z*z/(2*replicates))/(1+z*z/replicates)
        half=z*math.sqrt(rate*(1-rate)/replicates+z*z/(4*replicates**2))/(1+z*z/replicates)
        # Cells 1 and 2 have the same score weight; exact enumeration uses their aggregate.
        collapsed=[probs[0],probs[1]+probs[2],probs[3]]
        exact=0.
        for zero in range(n+1):
            for mixed in range(n-zero+1):
                three=n-zero-mixed
                stat=(zero*weights[0]+mixed*weights[1]+three*weights[3])**2/(n*information)
                if stat>critical:
                    exact+=float(multinomial.pmf([zero,mixed,three],n,collapsed))
        results[label]={"replicates":replicates,"rejections":rejects,"estimate":rate,
            "monte_carlo_se":math.sqrt(rate*(1-rate)/replicates),"mc_95pct_wilson_interval":[center-half,center+half],
            "exact_enumerated_probability":exact}
    result={"version":"simphysqa-audit-method/0.1.0","planning":planning,
        "source_script_sha256":sha256(script.read_bytes()).hexdigest(),"source_package":"kappaSize 1.2 (2018-11-25)",
        "execution":"supplied Python/SciPy reproduction; no executed R analysis",
        "runtime":{"numpy":np.__version__,"scipy":scipy.__version__},
        "seed":seed,"rng":"numpy.PCG64","test":{"name":"fixed-prevalence one-parameter score chi-square",
            "null":{"kappa":k0,"p":p},"alternative":{"kappa":k1,"p":p},"statistic":"[sum_i qprime[C_i]/q0[C_i]]^2 / (n * sum_j qprime[j]^2/q0[j])",
            "critical_value":critical,"degrees_of_freedom":1,"two_sided_alpha":.20,"information_per_record":information,
            "calibration_records_in_test":0,"formal_records":n},
        "model":"independent records; exchangeable binary raters; with probability kappa all three share Bernoulli(p), otherwise independent Bernoulli(p)",
        "simulation":results,"material_discrepancy_definition":"absolute power deviation above 0.02 (specified before saved simulation)",
        "power_difference_vs_approximation":results["power"]["estimate"]-planning["selected_modeled_power"],
        "material_power_discrepancy":abs(results["power"]["estimate"]-planning["selected_modeled_power"])>.02,
        "allocation_changed":False,
        "limitations":["p=.90 is fixed for this conditional planning-model check, not an observed prevalence",
            "PowerBinary supplies cell effect and df=1 approximation, not a finite-sample Fleiss test implementation",
            "full four-cell Pearson goodness-of-fit has df=3 and is not interchangeable with the df=1 score statistic",
            "noncentral chi-square power is a local approximation; score variance under finite alternative changes",
            "heterogeneous reviewer marginals, group dependence, prevalence estimation and missing judgments need an analysis-freeze decision",
            "Fleiss kappa may be descriptive but does not constitute this model-conditioned powered test"]}
    output=external(output)
    output.mkdir(parents=True,exist_ok=False)
    write(output/"audit-reconciliation.json",result)
    manifest(output,{"purpose":"audit_power_reproduction_and_finite_sample_simulation","seed":seed,"replicates_per_hypothesis":replicates})
    return result
