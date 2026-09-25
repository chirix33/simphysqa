"""Actual-user reply intake and journal inspection. This CLI cannot call an API.

Initial answering and reviewed refinement use ClarificationService with an
explicitly authorized provider in the host application. This tool only receives
one reply into an already-created attempt, preserving the provider boundary.
"""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.inference.clarification import AttemptStore,ClarificationService,Reply,now


class NoProvider:
    identity={'kind':'reply_intake_only'}
    def complete(self,*args):
        raise RuntimeError('reply_intake_cannot_dispatch_provider')


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('show','reply','unavailable'))
    p.add_argument('--root',type=Path,required=True); p.add_argument('--attempt',required=True)
    p.add_argument('--actor'); p.add_argument('--message-id'); p.add_argument('--reply-file',type=Path)
    a=p.parse_args(argv); store=AttemptStore(a.root)
    if a.command=='show': result=store.snapshot(a.attempt)
    else:
        if not a.actor or not a.message_id: p.error('--actor and --message-id identify the actual reply source')
        if a.command=='unavailable' and a.reply_file: p.error('unavailable does not accept a reply file')
        text=None if a.command=='unavailable' else a.reply_file.read_text(encoding='utf-8') if a.reply_file else input('Actual user reply: ')
        received=Reply(text,'actual_user',a.actor,a.message_id,now(),'local_cli')
        result=ClarificationService(store,NoProvider()).submit_reply(a.attempt,received)
    print(json.dumps(result,indent=2))
    return 0


if __name__=='__main__': raise SystemExit(main())
