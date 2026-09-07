from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from crush_core.engine import Engine
from crush_core.provider import demo


def at_day(engine, sid, day):
    with engine.db() as db:
        start = db.execute("SELECT at FROM events WHERE session=? AND kind='started' ORDER BY at LIMIT 1", (sid,)).fetchone()[0]
        target = (datetime.fromtimestamp(start, ZoneInfo('Asia/Shanghai')) + timedelta(days=day)).replace(hour=20, minute=0)
        s = engine.session(db, sid)
        delta = target.timestamp() - engine.now(s)
    while delta > 0:
        step = min(delta, 604800)
        engine.advance(sid, step)
        delta -= step


def facts(engine, sid):
    with engine.db() as db:
        return [dict(r) for r in db.execute('SELECT * FROM life_events WHERE session=? ORDER BY at', (sid,))]


def test_daily_life_continues_without_user_or_model(tmp_path):
    calls = []
    def generate(ctx, settings):
        calls.append(ctx)
        return demo(ctx)
    e = Engine(tmp_path/'test.db', generator=generate)
    sid = e.create()['id']
    at_day(e, sid, 1)
    assert facts(e, sid)
    at_day(e, sid, 3)
    assert len(facts(e, sid)) == 3
    assert len(calls) == 1  # life continues privately, no unanswered message flood
    assert facts(e, sid)[0]['thread'] == facts(e, sid)[2]['thread']
    assert facts(e, sid)[0]['step'] + 1 == facts(e, sid)[2]['step']


def test_world_is_idempotent_across_restart(tmp_path):
    e = Engine(tmp_path/'test.db')
    sid = e.create()['id']
    at_day(e, sid, 2)
    before = facts(e, sid)
    restored = Engine(e.path)
    for _ in range(5):
        restored.tick()
    assert facts(restored, sid) == before


def test_old_life_is_not_recycled_forever(tmp_path):
    e = Engine(tmp_path/'test.db')
    sid = e.create()['id']
    at_day(e, sid, 40)
    before = len(e.snapshot(sid)['messages'])
    e.send(sid, '嗨，我回来了', 'back-from-trip')
    e.advance(sid, 60)
    after_reply = len(e.snapshot(sid)['messages'])
    assert after_reply > before
    e.advance(sid, 86400)
    assert len(e.snapshot(sid)['messages']) == after_reply
    assert len(facts(e, sid)) <= 8


def test_world_context_keeps_previous_life_and_time(tmp_path):
    contexts = []
    def generate(ctx, settings):
        contexts.append(ctx)
        return demo(ctx)
    e = Engine(tmp_path/'test.db', generator=generate)
    sid = e.create()['id']
    at_day(e, sid, 3)
    e.send(sid, '书店的事后来怎么样了？', 'ask-about-life')
    e.advance(sid, 60)
    world = contexts[-1]['world']
    assert len(world) == 3
    assert all(x['at'] and x['text'] for x in world)
    assert 'at' in contexts[-1]['recent'][-1]
    assert all(x['at'] <= e.snapshot(sid)['now'] for x in world)


def test_only_sent_life_is_public(tmp_path):
    def quiet(ctx, settings):
        return {'action':'wait','messages':[], 'memories':[]}
    e = Engine(tmp_path/'test.db', generator=quiet)
    sid = e.create()['id']
    at_day(e, sid, 1)
    assert facts(e, sid)
    assert e.snapshot(sid)['life'] == []
    assert not any(x['kind']=='life_shared' for x in e.review(sid)['events'])


def test_branch_and_delete_do_not_leak_world(tmp_path):
    e = Engine(tmp_path/'test.db')
    sid = e.create()['id']
    at_day(e, sid, 1)
    sent = e.send(sid, '今天过得怎么样', 'branch-life-point')
    mid = sent['messages'][-1]['id']
    e.advance(sid, 60)
    at_day(e, sid, 3)
    child = e.branch(sid, mid)['id']
    assert len(facts(e, child)) == 1
    assert len(facts(e, sid)) == 3
    e.delete(child)
    assert facts(e, child) == []
    assert len(facts(e, sid)) == 3


def test_memory_consolidation_notifies_ui(tmp_path):
    e = Engine(tmp_path/'test.db')
    sid = e.create()['id']
    e.send(sid, '我喜欢乌龙茶', 'memory-long-term')
    e.advance(sid, 60)
    with e.db() as db:
        db.execute('UPDATE memories SET at=at-90000 WHERE session=?', (sid,))
    before = e.snapshot(sid)['revision']
    e.tick()
    assert e.snapshot(sid)['memories'][0]['tier'] == 'long'
    assert e.snapshot(sid)['revision'] > before
    revision = e.snapshot(sid)['revision']
    e.tick()
    assert e.snapshot(sid)['revision'] == revision


def test_preference_update_preserves_original_evidence(tmp_path):
    e = Engine(tmp_path/'test.db')
    sid = e.create()['id']
    e.send(sid, '我喜欢乌龙茶', 'preference-first')
    e.advance(sid, 60)
    e.send(sid, '现在喜欢红茶，不喝乌龙茶了', 'preference-update')
    e.advance(sid, 60)
    memories = e.snapshot(sid)['memories']
    assert len(memories) == 1
    assert memories[0]['text'] == '现在喜欢红茶，不喝乌龙茶了'
    assert memories[0]['previous'] == '我喜欢乌龙茶'


def test_additional_preference_is_not_a_contradiction(tmp_path):
    e = Engine(tmp_path/'test.db')
    sid = e.create()['id']
    e.send(sid, '我喜欢乌龙茶', 'first-drink-preference')
    e.advance(sid, 60)
    e.send(sid, '我也喜欢咖啡', 'another-drink-preference')
    e.advance(sid, 60)
    assert len(e.snapshot(sid)['memories']) == 2
