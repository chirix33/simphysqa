"""Public portable entry point. No organizer data or installed simphysqa needed.

This adapter does not grant launch permission. A centrally issued assignment,
reservation and fresh qualification are required. No auto-all default or retry.
"""
import argparse
from execution_readiness import validate_package, launch_job, export_return, canonical


def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='command', required=True)
    v = sub.add_parser('validate'); v.add_argument('--package', required=True)
    l = sub.add_parser('launch'); l.add_argument('--package', required=True); l.add_argument('--job', required=True)
    l.add_argument('--authorize-main', action='store_true', required=True)
    r = sub.add_parser('return'); r.add_argument('--job', required=True); r.add_argument('--output', required=True)
    a = p.parse_args()
    if a.command == 'validate': result = {'verified_files': len(validate_package(a.package)['files'])}
    elif a.command == 'launch': launch_job(a.job, a.package); result = {'job': a.job}
    else: result = {'return_envelope_sha256': export_return(a.job, a.output)}
    print(canonical(result).decode())


if __name__ == '__main__': main()
