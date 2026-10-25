import argparse
import json
from pathlib import Path
import sys
from .validation import validate

def main():
    p=argparse.ArgumentParser(description='AI CAD Bridge / Autodesk Inventor')
    p.add_argument('--workspace',default='.')
    p.add_argument('--start',action='store_true',help='Start Inventor if not running')
    sub=p.add_subparsers(dest='action',required=True)
    for action in ('prepare','validate','run'):
        s=sub.add_parser(action); s.add_argument('command')
    sub.add_parser('status')
    args=p.parse_args(); cx=None
    try:
        if args.action in ('prepare','validate','run'):
            command=json.loads(Path(args.command).read_text(encoding='utf-8-sig'))
            if args.action!='prepare': validate(command)
        if args.action=='prepare':
            from .intake import prepare
            result=prepare(command,args.workspace)
        elif args.action=='validate': result={'valid':True,'schema_version':'1.0'}
        else:
            from .connector import Connector
            cx=Connector(args.start)
            if args.action=='status': result=cx.status()
            else:
                from .runner import Runner
                result=Runner(cx,args.workspace).execute(command)
        print(json.dumps(result,indent=2,ensure_ascii=False))
        return 0 if result.get('success',True) else 1
    except Exception as exc:
        print(json.dumps({'success':False,'error':{'type':type(exc).__name__,'message':str(exc)}},ensure_ascii=False))
        return 1
    finally:
        if cx: cx.close()

if __name__=='__main__': sys.exit(main())
