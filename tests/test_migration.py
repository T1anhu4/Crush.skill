import hashlib
import json
import sqlite3

import pytest

from crush_core.engine import Engine


def legacy(path):
    with sqlite3.connect(path) as db:
        db.executescript('''CREATE TABLE sessions(session_id TEXT,profile_json TEXT,state_json TEXT,persona_json TEXT,canonical_archetype TEXT,created_at TEXT,updated_at TEXT);
        CREATE TABLE episodes(id INTEGER,session_id TEXT,role TEXT,content TEXT,created_at TEXT);
        CREATE TABLE summaries(session_id TEXT,summary TEXT,updated_at TEXT);''')
        db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?,?)',('old',json.dumps({'name':'示例角色','age':28}), '{}','{}','passive','2026-08-01T12:00:00+00:00','2026-08-01T12:00:00+00:00'))
        db.execute('INSERT INTO episodes VALUES(1,?,?,?,?)',('old','user','我喜欢雨天散步','2026-08-01T12:00:00+00:00'))
        db.execute('INSERT INTO episodes VALUES(2,?,?,?,?)',('old','npc','那就挑条安静的路','2026-08-01T12:01:00+00:00'))
        db.execute('INSERT INTO summaries VALUES(?,?,?)',('old','旧版摘要，不应被当成已核实事实','2026-08-01'))


def test_preview_is_read_only_and_does_not_expose_content(tmp_path):
    from crush_core.migration import preview
    source=tmp_path/'old.db';legacy(source)
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    report=preview(source,'old')
    assert report['counts']['episodes']==2
    assert '雨天' not in json.dumps(report,ensure_ascii=False)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest


def test_migration_paused_idempotent_and_preserves_archive(tmp_path):
    from crush_core.migration import migrate
    source=tmp_path/'old.db';legacy(source)
    e=Engine(tmp_path/'new.db')
    with pytest.raises(ValueError):
        migrate(e,source,'old')
    result=migrate(e,source,'old',confirmed=True)
    sid=result['session']['id'];snap=e.snapshot(sid)
    assert snap['paused'] and snap['mode']=='live'
    assert snap['character']['name']=='示例角色'
    assert [x['content'] for x in snap['messages']]==['我喜欢雨天散步','那就挑条安静的路']
    assert snap['memories'][0]['text']=='我喜欢雨天散步'
    assert not snap['jobs']
    assert migrate(e,source,'old',confirmed=True)['session']['id']==sid
    assert len(e.list())==1
    assert len(e.export(sid)['legacy_archive'])==4
    with e.db() as db:
        assert db.execute('SELECT COUNT(*) FROM legacy_records WHERE session=?',(sid,)).fetchone()[0]==4
    e.delete(sid)
    with e.db() as db:
        assert db.execute('SELECT COUNT(*) FROM legacy_records').fetchone()[0]==0
    assert sqlite3.connect(source).execute('SELECT COUNT(*) FROM episodes').fetchone()[0]==2


def test_invalid_source_cannot_create_half_session(tmp_path):
    from crush_core.migration import migrate
    source=tmp_path/'bad.db';legacy(source)
    with sqlite3.connect(source) as db:
        db.execute("UPDATE sessions SET profile_json='invalid'")
    e=Engine(tmp_path/'new.db')
    with pytest.raises(ValueError):
        migrate(e,source,'old',confirmed=True)
    assert e.list()==[]


def test_unknown_age_is_an_honest_readonly_archive(tmp_path):
    from crush_core.migration import migrate
    source=tmp_path/'old.db';legacy(source)
    with sqlite3.connect(source) as db:
        db.execute('UPDATE sessions SET profile_json=?',(json.dumps({'name':'未知年龄'}),))
    e=Engine(tmp_path/'new.db');result=migrate(e,source,'old',confirmed=True)
    sid=result['session']['id']
    assert result['session']['character']['age'] is None
    with pytest.raises(ValueError):
        e.pause(sid,False)
    with pytest.raises(ValueError):
        e.send(sid,'你好','archived-send-01')
