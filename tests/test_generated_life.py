from datetime import datetime
from zoneinfo import ZoneInfo
from crush_core.engine import Engine


def test_live_life_can_extend_after_authored_arc_once_daily(tmp_path):
    contexts=[]
    def generate(ctx,settings):
        contexts.append(ctx)
        return {'action':'reply','messages':['今天把阳台的小花盆换了个位置。'],
                'life_update':{'text':'今天把阳台的小花盆换了个位置。','thread':'阳台植物'}}
    e=Engine(tmp_path/'test.db',generator=generate)
    sid=e.create(mode='live')['id']
    now=datetime(2026,9,20,20,tzinfo=ZoneInfo('Asia/Shanghai')).timestamp()
    def prepare_day(at):
        with e.db() as db:
            db.execute('UPDATE sessions SET clock=?,anchor=? WHERE id=?',(at,__import__('time').time(),sid))
            db.execute("UPDATE events SET at=? WHERE session=? AND kind='started'",(now-30*86400,sid))
    def send(key):
        e.send(sid,'今天怎么样？',key)
        with e.db() as db:
            db.execute('UPDATE jobs SET due=0 WHERE session=?',(sid,))
        e.tick(sid)
    prepare_day(now);send('new-life-day-001')
    assert contexts[-1]['allow_life_update'] is True
    with e.db() as db:
        facts=db.execute("SELECT * FROM life_events WHERE session=? AND story_key LIKE 'generated:%'",(sid,)).fetchall()
        assert len(facts)==1 and facts[0]['shared_at']
    send('new-life-day-002')
    assert contexts[-1]['allow_life_update'] is False
    prepare_day(now+86400);send('new-life-day-003')
    assert contexts[-1]['allow_life_update'] is True
    # Repeated generated text is not treated as a new event on another day.
    with e.db() as db:
        assert db.execute("SELECT COUNT(*) FROM life_events WHERE session=? AND story_key LIKE 'generated:%'",(sid,)).fetchone()[0]==1


def test_demo_cannot_inject_generated_life(tmp_path):
    e=Engine(tmp_path/'test.db',generator=lambda c,s:{'action':'reply','messages':['收到'],
             'life_update':{'text':'不应该存在','thread':'test'}})
    sid=e.create()['id'];e.send(sid,'嗨','demo-life-001');e.advance(sid,60)
    with e.db() as db:
        assert not db.execute("SELECT 1 FROM life_events WHERE text='不应该存在'").fetchone()
