import json
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from crush_core.engine import Engine
from crush_core.provider import ProviderError, demo
from crush_core.server import create_app


@pytest.fixture
def engine(tmp_path):
    return Engine(tmp_path/'test.sqlite3')


def deliver(engine,sid,text,rid='request-0001'):
    engine.send(sid,text,rid)
    engine.advance(sid,300)
    return engine.snapshot(sid)


def test_message_idempotency_and_memory(engine):
    sid=engine.create()['id']
    first=engine.send(sid,'我喜欢乌龙茶','same-request')
    second=engine.send(sid,'我喜欢乌龙茶','same-request')
    assert len(first['messages'])==len(second['messages'])
    engine.advance(sid,300)
    state=engine.snapshot(sid)
    assert len(state['memories'])==1
    assert state['memories'][0]['text']=='我喜欢乌龙茶'
    with pytest.raises(ValueError):
        engine.send(sid,'另一条','same-request')


def test_recovery_and_long_memory(engine):
    sid=engine.create()['id']
    deliver(engine,sid,'我喜欢乌龙茶')
    restored=Engine(engine.path)
    with restored.db() as db:
        for i in range(140):
            restored.message(db,sid,'user',f'不相关片段{i}',restored.now(restored.session(db,sid)))
        assert restored.recall(db,sid,'乌龙茶')[0]['text']=='我喜欢乌龙茶'
    restored.advance(sid,2*86400)
    assert restored.snapshot(sid)['memories'][0]['tier']=='long'


def test_review_is_read_only(engine):
    sid=engine.create()['id']
    deliver(engine,sid,'你喜欢我吗')
    before=engine.snapshot(sid)
    review=engine.review(sid)
    after=engine.snapshot(sid)
    assert before['revision']==after['revision']
    assert before['messages']==after['messages']
    assert any(e['quote']=='你喜欢我吗' for e in review['events'])
    assert not any('复盘助手' in m['content'] for m in after['messages'])


def test_withdraw_cancels_pending(engine):
    sid=engine.create()['id']
    state=engine.send(sid,'我喜欢绿茶','withdraw-request')
    mid=state['messages'][-1]['id']
    engine.withdraw(sid,mid)
    engine.advance(sid,300)
    state=engine.snapshot(sid)
    assert state['messages'][-1]['status']=='withdrawn'
    assert len(state['messages'])==3
    assert not state['memories']


def test_withdraw_inflight_cannot_resurrect_or_write_memory(engine):
    sid=engine.create()['id']
    state=engine.send(sid,'我喜欢绿茶','withdraw-inflight')
    mid=state['messages'][-1]['id']
    def generator(ctx,config):
        engine.withdraw(sid,mid)
        return demo(ctx)
    engine.generator=generator
    engine.advance(sid,30)
    assert len(engine.snapshot(sid)['messages'])==3
    assert not engine.snapshot(sid)['memories']


def test_sleep_and_wake(engine):
    sid=engine.create()['id']
    with engine.db() as db:
        s=engine.session(db,sid)
        midnight=datetime.fromtimestamp(engine.now(s),ZoneInfo(s['timezone'])).replace(hour=2).timestamp()
        db.execute('UPDATE sessions SET clock=? WHERE id=?',(midnight,sid))
    engine.send(sid,'睡着了，刚看到','sleep-request')
    engine.advance(sid,3600)
    assert len(engine.snapshot(sid)['messages'])==3
    engine.advance(sid,6*3600)
    state=engine.snapshot(sid)
    assert len(state['messages'])>3
    assert engine.review(sid)['mind']['boundary']==0


def test_no_unanswered_proactive_flood(engine):
    sid=engine.create()['id']
    engine.advance(sid,86400)
    first=engine.snapshot(sid)
    engine.advance(sid,3*86400)
    second=engine.snapshot(sid)
    assert len(first['messages'])==len(second['messages'])


def test_pause_and_live_clock_constraints(engine):
    sid=engine.create()['id']
    engine.pause(sid,True)
    engine.send(sid,'你好','pause-request')
    engine.advance(sid,600)
    assert len(engine.snapshot(sid)['messages'])==3
    engine.pause(sid,False)
    engine.tick()
    assert len(engine.snapshot(sid)['messages'])>3
    live=engine.create(mode='live')['id']
    with pytest.raises(ValueError):
        engine.advance(live,100)


def test_pause_during_generation_caches_result(engine):
    sid=engine.create()['id']
    calls=[]
    def generator(ctx,config):
        calls.append(1)
        engine.pause(sid,True)
        return demo(ctx)
    engine.generator=generator
    engine.send(sid,'你好','pause-flight')
    engine.advance(sid,30)
    assert len(engine.snapshot(sid)['messages'])==3
    engine.pause(sid,False)
    engine.tick()
    assert len(calls)==1
    assert len(engine.snapshot(sid)['messages'])>3


def test_failure_retry_does_not_duplicate_or_score(engine):
    sid=engine.create()['id']
    def fail(*args):
        raise ProviderError('模拟断网')
    engine.generator=fail
    before=engine.review(sid)['mind']
    deliver(engine,sid,'我喜欢花')
    state=engine.snapshot(sid)
    assert state['jobs'][0]['status']=='error'
    assert before==engine.review(sid)['mind']
    engine.generator=lambda ctx,config:demo(ctx)
    engine.retry(sid,state['jobs'][0]['id'])
    engine.tick()
    after=engine.snapshot(sid)
    assert sum(m['role']=='user' for m in after['messages'])==1
    assert len(after['memories'])==1


def test_concurrent_session_isolation(engine):
    a=engine.create()['id'];b=engine.create('zhou')['id']
    deliver(engine,a,'我喜欢红茶','a-request')
    deliver(engine,b,'我喜欢蓝色','b-request')
    assert engine.snapshot(a)['memories'][0]['text']=='我喜欢红茶'
    assert engine.snapshot(b)['memories'][0]['text']=='我喜欢蓝色'


def test_duplicate_concurrent_send(engine):
    sid=engine.create()['id']
    threads=[threading.Thread(target=engine.send,args=(sid,'你好','concurrent-id')) for _ in range(5)]
    for t in threads:t.start()
    for t in threads:t.join()
    assert sum(m['role']=='user' for m in engine.snapshot(sid)['messages'])==1


def test_delete_erases_derived_records(engine):
    sid=engine.create()['id']
    deliver(engine,sid,'我喜欢小猫')
    engine.delete(sid)
    assert not engine.list()
    with engine.db() as db:
        for table in ['messages','memories','jobs','events']:
            assert db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]==0


def test_closed_relationship_no_automatic_revival(engine):
    sid=engine.create()['id']
    deliver(engine,sid,'不要再联系了')
    assert engine.snapshot(sid)['closed']
    before=len(engine.snapshot(sid)['messages'])
    engine.advance(sid,86400)
    assert len(engine.snapshot(sid)['messages'])==before
    with pytest.raises(ValueError):engine.send(sid,'你好','return-again')


def test_model_cannot_invent_memory(engine):
    sid=engine.create()['id']
    engine.generator=lambda ctx,config:{'action':'reply','messages':['你好'],'memories':[{'kind':'preference','key':'birthday','text':'生日','quote':'用户从未说过的话'}]}
    deliver(engine,sid,'你好')
    assert not engine.snapshot(sid)['memories']


def test_local_api_guards_and_key_redaction(tmp_path):
    app=create_app(tmp_path,run_worker=False)
    with TestClient(app) as client:
        boot=client.get('/api/bootstrap').json()
        assert client.post('/api/sessions',json={}).status_code==403
        headers={'x-crush-token':boot['token']}
        assert client.post('/api/sessions',json={},headers={**headers,'origin':'https://evil.example'}).status_code==403
        assert client.get('/api/bootstrap',headers={'host':'evil.example'}).status_code==403
        response=client.post('/api/sessions',json={'character':'lin'},headers=headers)
        assert response.status_code==200
        settings=client.post('/api/settings',json={'base':'https://api.example.com/v1','model':'example','key':'synthetic-secret'},headers=headers)
        assert settings.status_code==200
        assert 'synthetic-secret' not in client.get('/api/bootstrap').text
        assert (tmp_path/'provider.json').stat().st_mode & 0o777==0o600
        assert client.post('/api/settings',json={'base':'https://other.example/v1','model':'example','key':''},headers=headers).status_code==400


def test_new_reader_does_not_reset_active_generation(engine):
    sid=engine.create()['id']
    def during(ctx,config):
        reader=Engine(engine.path)
        assert reader.snapshot(sid)['jobs'][0]['status']=='generating'
        return demo(ctx)
    engine.generator=during
    deliver(engine,sid,'你好')
    assert not engine.snapshot(sid)['jobs']


def test_branch_preserves_parent_and_excludes_future(engine):
    sid=engine.create()['id']
    deliver(engine,sid,'我喜欢绿茶','memory-before')
    sent=engine.send(sid,'你必须马上回我','branch-target')
    target=sent['messages'][-1]['id']
    engine.advance(sid,300)
    deliver(engine,sid,'我喜欢大海','memory-after')
    original=engine.snapshot(sid)
    child=engine.branch(sid,target)
    assert child['id']!=sid
    assert len(child['messages'])<len(original['messages'])
    assert {m['text'] for m in child['memories']}=={'我喜欢绿茶'}
    assert engine.snapshot(sid)['messages']==original['messages']
    assert not any(m['content']=='你必须马上回我' for m in child['messages'])
    assert engine.review(child['id'])['mind']['boundary']==0


def test_character_delayed_reply_is_durable(engine):
    sid=engine.create()['id'];calls=[]
    def delayed(ctx,config):
        calls.append(1)
        return {'action':'reply','messages':['忙完了，刚才说到哪儿了？'],'delay_minutes':30}
    engine.generator=delayed
    engine.send(sid,'你好','delay-test')
    engine.advance(sid,300)
    assert len(engine.snapshot(sid)['messages'])==3
    restored=Engine(engine.path,generator=lambda *args:pytest.fail('Cached decision should not regenerate'))
    restored.advance(sid,1801)
    assert len(restored.snapshot(sid)['messages'])==4
    assert len(calls)==1


def test_structured_live_transport(monkeypatch):
    from crush_core import provider
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,*args):return json.dumps({'choices':[{'message':{'content':json.dumps({'action':'reply','messages':['今天那本书读完了。'],'feeling':'轻松'})}}]}).encode()
    requests=[]
    def fake(request,timeout):
        requests.append(json.loads(request.data))
        return Response()
    monkeypatch.setattr(provider,'urlopen',fake)
    result=provider.generate({'session':{'mode':'live'}},{'base':'https://example.com/v1','model':'synthetic','key':'dummy'})
    Engine.validate(result)
    assert requests[0]['model']=='synthetic'
    assert requests[0]['max_tokens']==2048
    assert result['messages']==['今天那本书读完了。']
