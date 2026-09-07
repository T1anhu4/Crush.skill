from datetime import datetime
from zoneinfo import ZoneInfo

from crush_core.engine import Engine
from crush_core.provider import demo


def runtime(tmp_path, monkeypatch, hour=11):
    stamp = datetime(2026,9,7,hour,0,tzinfo=ZoneInfo('Asia/Shanghai')).timestamp()
    monkeypatch.setattr('crush_core.engine.time.time',lambda:stamp)
    return Engine(tmp_path/'wait.db',generator=demo)


def test_first_live_message_skips_busy_delay_only_once(tmp_path,monkeypatch):
    e=runtime(tmp_path,monkeypatch)
    sid=e.create(mode='live')['id']
    first=e.send(sid,'你好','first-message')
    assert 0 < first['jobs'][0]['due']-first['now'] < 20
    assert first['jobs'][0]['reason']=='first_contact'
    e.withdraw(sid,first['messages'][-1]['id'])
    second=e.send(sid,'又来了','second-message')
    assert second['jobs'][0]['due']-second['now']==180
    assert second['jobs'][0]['reason']=='busy'


def test_first_message_does_not_wake_sleeping_character(tmp_path,monkeypatch):
    e=runtime(tmp_path,monkeypatch,2)
    sid=e.create(mode='live')['id']
    state=e.send(sid,'你好','night-message')
    assert state['jobs'][0]['due']-state['now'] > 6*3600
    assert state['jobs'][0]['reason']=='sleep'


def test_pause_reason_does_not_erase_queued_reason(tmp_path,monkeypatch):
    e=runtime(tmp_path,monkeypatch)
    sid=e.create(mode='live')['id']
    e.send(sid,'你好','pause-message')
    assert e.pause(sid,True)['jobs'][0]['reason']=='paused'
    assert e.pause(sid,False)['jobs'][0]['reason']=='first_contact'


def test_waiting_reason_survives_reopen_and_retry(tmp_path,monkeypatch):
    e=runtime(tmp_path,monkeypatch)
    sid=e.create(mode='live')['id']
    state=e.send(sid,'你好','durable-message')
    jid=state['jobs'][0]['id']
    restored=Engine(e.path,generator=demo)
    assert restored.snapshot(sid)['jobs'][0]['reason']=='first_contact'
    with restored.db() as db:
        db.execute("UPDATE jobs SET status='error' WHERE id=?",(jid,))
    assert restored.retry(sid,jid)['jobs'][0]['reason']=='retry'


def test_character_chosen_delay_remains(tmp_path,monkeypatch):
    e=runtime(tmp_path,monkeypatch,20)
    sid=e.create()['id']
    def delayed(ctx,settings):
        assert e.snapshot(sid)['jobs'][0]['status']=='generating'
        result=demo(ctx)
        result['delay_minutes']=10
        return result
    e.generator=delayed
    e.send(sid,'你好','delayed-message')
    e.advance(sid,30)
    state=e.snapshot(sid)
    assert state['jobs'][0]['reason']=='character_delay'
    assert state['jobs'][0]['due']-state['now']==600
    assert len(state['messages'])==3
