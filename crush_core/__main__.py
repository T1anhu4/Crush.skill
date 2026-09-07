"""JSON adapter for terminals and agent hosts; uses the same engine as the GUI."""
import argparse
import json
import os
import sqlite3
from pathlib import Path
from .engine import Engine


def main():
    parser=argparse.ArgumentParser(description='Crush v3 event runtime')
    parser.add_argument('action',choices=['start','list','status','send','tick','review','advance','withdraw','pause','resume','retry','branch','export','delete','migrate'])
    parser.add_argument('--home',default=os.environ.get('CRUSH_V3_HOME',str(Path(os.environ.get('CRUSH_HOME',str(Path.home()/'.crush')))/'v3')))
    parser.add_argument('--session')
    parser.add_argument('--character',default='lin')
    parser.add_argument('--mode',choices=['demo','live'],default='demo')
    parser.add_argument('--message',default='')
    parser.add_argument('--request-id')
    parser.add_argument('--message-id')
    parser.add_argument('--job-id')
    parser.add_argument('--source-db')
    parser.add_argument('--legacy-session')
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--confirm-private-data',action='store_true')
    parser.add_argument('--confirm-delete',action='store_true')
    parser.add_argument('--seconds',type=float,default=3600)
    args=parser.parse_args()
    if args.action=='migrate' and (not args.source_db or not args.legacy_session):
        parser.error('migrate requires --source-db and --legacy-session')
    if args.action=='migrate' and args.apply and not args.confirm_private_data:
        parser.error('--apply requires --confirm-private-data')
    if args.action not in ('start','list','migrate') and not args.session:
        parser.error('--session is required (tick processes only this session)')
    def settings():
        path=Path(args.home)/'provider.json'
        return json.loads(path.read_text()) if path.exists() else {}
    try:
        if args.action=='migrate' and not args.apply:
            from .migration import preview
            print(json.dumps(preview(args.source_db,args.legacy_session),ensure_ascii=False))
            return 0
        engine=Engine(Path(args.home)/'crush.sqlite3',settings=settings)
        if args.action=='migrate':
            from .migration import migrate
            result=migrate(engine,args.source_db,args.legacy_session,confirmed=args.confirm_private_data)
        elif args.action=='start':
            result=engine.create(args.character,args.mode)
        elif args.action=='list':
            result=engine.list()
        elif args.action=='tick':
            engine.snapshot(args.session)
            engine.tick(args.session);result=engine.snapshot(args.session)
        elif not args.session:
            parser.error('--session is required')
        elif args.action=='status':
            result=engine.snapshot(args.session)
        elif args.action=='review':
            result=engine.review(args.session)
        elif args.action=='export':
            result=engine.export(args.session)
        elif args.action in ('pause','resume'):
            result=engine.pause(args.session,args.action=='pause')
        elif args.action=='retry':
            if not args.job_id:
                parser.error('--job-id is required')
            result=engine.retry(args.session,args.job_id)
        elif args.action=='branch':
            if not args.message_id:
                parser.error('--message-id is required')
            result=engine.branch(args.session,args.message_id)
        elif args.action=='delete':
            if not args.confirm_delete:
                parser.error('--confirm-delete is required')
            engine.delete(args.session);result={'deleted':True}
        elif args.action=='send':
            if not args.request_id:
                parser.error('--request-id is required for idempotent sending')
            result=engine.send(args.session,args.message,args.request_id)
        elif args.action=='withdraw':
            result=engine.withdraw(args.session,args.message_id)
        else:
            result=engine.advance(args.session,args.seconds)
        print(json.dumps(result,ensure_ascii=False))
        return 0
    except (ValueError,OSError,sqlite3.Error) as exc:
        print(json.dumps({'error':str(exc)},ensure_ascii=False))
        return 1


if __name__=='__main__':
    raise SystemExit(main())
