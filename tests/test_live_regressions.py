from datetime import datetime
from zoneinfo import ZoneInfo
import pytest
from crush_core.engine import Engine
from crush_core.provider import ProviderError


def runtime(tmp_path,monkeypatch,generator):
    now=datetime(2026,1,18,20,tzinfo=ZoneInfo('Asia/Shanghai')).timestamp()
    monkeypatch.setattr('crush_core.engine.time.time',lambda:now)
    e=Engine(tmp_path/'test.db',generator=generator)
    sid=e.create(mode='live')['id']
    return e,sid,now


def deliver(e,sid,text,key):
    e.send(sid,text,key)
    with e.db() as db:
        db.execute('UPDATE jobs SET due=0 WHERE session=?',(sid,))
    e.tick(sid)


def test_correction_survives_generation_failure(tmp_path,monkeypatch):
    def unavailable(c,s):
        raise ProviderError('unavailable')
    e,sid,_=runtime(tmp_path,monkeypatch,unavailable)
    deliver(e,sid,'我喜欢乌龙茶','preference-first')
    deliver(e,sid,'我现在不喝乌龙茶了，喜欢红茶','preference-correction')
    memories=e.snapshot(sid)['memories']
    assert [m['text'] for m in memories]==['我现在不喝乌龙茶了，喜欢红茶']
    restored=Engine(e.path,generator=unavailable)
    with restored.db() as db:
        assert [m['text'] for m in restored.recall(db,sid,'喜欢什么茶')]==['我现在不喝乌龙茶了，喜欢红茶']
    mid=e.snapshot(sid)['messages'][-1]['id']
    e.withdraw(sid,mid)
    assert [m['text'] for m in e.snapshot(sid)['memories']]==['我喜欢乌龙茶']


def test_temporal_context_has_explicit_elapsed_days(tmp_path,monkeypatch):
    contexts=[]
    def generate(c,s):
        contexts.append(c);return {'action':'reply','messages':['嗯']}
    e,sid,now=runtime(tmp_path,monkeypatch,generate)
    with e.db() as db:
        db.execute("UPDATE events SET at=? WHERE session=? AND kind='started'",(now-13*86400,sid))
    deliver(e,sid,'你好','temporal-request')
    assert contexts[-1]['session']['relationship_day']==14
    assert contexts[-1]['session']['month']==1


@pytest.mark.parametrize('content',['我下午在书店门口捡到一片，边缘卷得像被猫踩过。','我以前也在一本旧书里夹过一片银杏叶。'])
def test_unsupported_past_experience_is_not_delivered(tmp_path,monkeypatch,content):
    e,sid,_=runtime(tmp_path,monkeypatch,lambda c,s:{'action':'reply','messages':[content]})
    deliver(e,sid,'今天看见一片叶子','unsupported-fact')
    snap=e.snapshot(sid)
    assert content not in [m['content'] for m in snap['messages'] if m['role']=='character']
    assert snap['jobs'][0]['status']=='error'


def test_clear_preference_does_not_extract_questions_or_other_people(tmp_path,monkeypatch):
    e,sid,_=runtime(tmp_path,monkeypatch,lambda c,s:{'action':'reply','messages':['嗯']})
    for index,text in enumerate(['你喜欢红茶吗？','她说我喜欢红茶','我喜欢红茶吗？','我对红茶过敏']):
        deliver(e,sid,text,f'no-preference-{index}')
    assert not e.snapshot(sid)['memories']


def test_old_model_quote_cannot_reactivate_superseded_preference(tmp_path,monkeypatch):
    e,sid,_=runtime(tmp_path,monkeypatch,lambda c,s:{'action':'reply','messages':['嗯'],
        'memories':[{'kind':'preference','key':'随意生成的另一个主题','quote':'我喜欢乌龙茶'}]})
    deliver(e,sid,'我喜欢乌龙茶','old-quote-first')
    deliver(e,sid,'我现在不喝乌龙茶了，喜欢红茶','old-quote-second')
    assert [m['text'] for m in e.snapshot(sid)['memories']]==['我现在不喝乌龙茶了，喜欢红茶']


def test_grounding_accepts_registered_fact_and_rejects_disabled_update(tmp_path,monkeypatch):
    from crush_core.grounding import validate_grounding
    content='我下午在书店门口捡到一片叶子'
    context={'session':{'mode':'live'},'character':{'opening':[]},'world':[{'text':content}], 'allow_life_update':False}
    validate_grounding({'action':'reply','messages':[content]},context)
    with pytest.raises(ProviderError):
        validate_grounding({'action':'reply','messages':[content],'life_update':{'text':content,'thread':'叶子'}},context)


def test_provider_timeout_is_classified_without_private_error(monkeypatch):
    from crush_core.provider import generate
    def fail(*args,**kwargs):
        raise TimeoutError('secret-provider-response')
    monkeypatch.setattr('crush_core.provider.urlopen',fail)
    with pytest.raises(ProviderError) as error:
        generate({'session':{'mode':'live'}},{'base':'https://example.invalid/v1','key':'secret-key','model':'test'})
    assert getattr(error.value,'code',None)=='timeout'
    assert 'secret' not in str(error.value)
