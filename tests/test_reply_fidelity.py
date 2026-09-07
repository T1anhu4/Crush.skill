import pytest
from crush_core.grounding import validate_grounding
from crush_core.provider import ProviderError
from test_live_regressions import runtime, deliver


def context():
    return {'session':{'mode':'live','month':1,'relationship_day':14},'character':{'opening':[]},
            'world':[],'memories':[{'text':'我喜欢红茶'}], 'message':'还记得我喜欢喝什么茶吗',
            'recent':[{'role':'user','content':'我喜欢红茶'},{'role':'character','content':'我私藏了一罐正山小种'}]}


def test_character_suggestion_is_not_user_preference():
    with pytest.raises(ProviderError):
        validate_grounding({'messages':['记得，正山小种那一挂的红茶，你自己改的口味。']},context())


def test_historical_season_is_allowed_but_current_season_not_inferred():
    validate_grounding({'messages':['去年秋天拍的照片，还留着吗？']},context())
    with pytest.raises(ProviderError):
        validate_grounding({'messages':['秋天快收尾的时候，什么都不做，叶子自己也会变。']},context())


def test_repair_is_bounded_and_only_final_reply_is_saved(tmp_path,monkeypatch):
    calls=[]
    def generator(c,s):
        calls.append(c)
        if len(calls)==1:
            return {'action':'reply','messages':['我下午捡到一片叶子。']}
        return {'action':'reply','messages':['长什么样？']}
    e,sid,_=runtime(tmp_path,monkeypatch,generator)
    deliver(e,sid,'看到一片叶子','repair-once-01')
    assert len(calls)==2 and calls[1]['repair']['reason']
    assert e.snapshot(sid)['messages'][-1]['content']=='长什么样？'
    assert not e.snapshot(sid)['jobs']


def test_repair_does_not_retry_transport_failure(tmp_path,monkeypatch):
    calls=[]
    def generator(c,s):
        calls.append(c);raise ProviderError('超时','timeout')
    e,sid,_=runtime(tmp_path,monkeypatch,generator)
    deliver(e,sid,'你好','no-transport-retry')
    assert len(calls)==1


def test_failed_rewrite_stops_after_two_calls(tmp_path,monkeypatch):
    calls=[]
    def generator(c,s):
        calls.append(c);return {'action':'reply','messages':['我下午捡到一片叶子。']}
    e,sid,_=runtime(tmp_path,monkeypatch,generator)
    deliver(e,sid,'看到一片叶子','repair-limit-01')
    assert len(calls)==2
    assert e.snapshot(sid)['jobs'][0]['status']=='error'


def test_pause_during_invalid_draft_does_not_leave_lease_running(tmp_path,monkeypatch):
    calls=[]
    def generator(c,s):
        calls.append(c);e.pause(sid,True)
        return {'action':'reply','messages':['我下午捡到一片叶子。']}
    e,sid,_=runtime(tmp_path,monkeypatch,generator)
    deliver(e,sid,'看到一片叶子','repair-pause-01')
    assert len(calls)==1
    assert e.snapshot(sid)['jobs'][0]['status']=='queued'


def test_model_context_excludes_unscheduled_life_examples(tmp_path,monkeypatch):
    contexts=[]
    def generator(c,s):
        contexts.append(c);return {'action':'reply','messages':['嗯']}
    e,sid,_=runtime(tmp_path,monkeypatch,generator)
    deliver(e,sid,'你好','context-facts-01')
    assert 'life' not in contexts[-1]['character']
    assert 'scene' not in contexts[-1]['character']
    assert contexts[-1]['character']['initial_scene']


def test_provider_reviews_draft_against_sources_before_delivery(monkeypatch):
    import json
    from crush_core import provider
    requests=[]
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,*args):
            text='你喜欢正山小种。' if len(requests)==1 else '红茶，记得。'
            return json.dumps({'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'action':'reply','messages':[text]})}}]}).encode()
    def transport(request,timeout):
        requests.append(json.loads(request.data));return Response()
    monkeypatch.setattr(provider,'urlopen',transport)
    result=provider.generate(context(),{'base':'https://example.invalid/v1','model':'test','key':'test'})
    assert result['messages']==['红茶，记得。']
    assert len(requests)==2
    review=json.loads(requests[1]['messages'][1]['content'])
    assert review['draft']['messages']==['你喜欢正山小种。']
    assert review['context']['memories']==context()['memories']


def test_fact_editor_cannot_change_relationship_action(monkeypatch):
    from crush_core import provider
    results=iter([{'action':'reply','messages':['你好']},{'action':'end','messages':['再见']}])
    monkeypatch.setattr(provider,'completion',lambda *args:next(results))
    with pytest.raises(ProviderError):
        provider.generate(context(),{'base':'https://example.invalid/v1','model':'test','key':'test'})


def test_last_rewrite_does_not_start_another_editor_loop(monkeypatch):
    from crush_core import provider
    calls=[]
    def complete(*args):
        calls.append(args);return {'action':'reply','messages':['红茶，记得。']}
    monkeypatch.setattr(provider,'completion',complete)
    provider.generate({**context(),'repair':{'reason':'仅依据用户原话'}},{'base':'https://example.invalid/v1','model':'test','key':'test'})
    assert len(calls)==1
