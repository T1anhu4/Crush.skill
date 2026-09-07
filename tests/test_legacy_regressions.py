import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def runtime(tmp_path,monkeypatch):
    monkeypatch.setenv('CRUSH_DATA_DIR',str(tmp_path))
    monkeypatch.setenv('CRUSH_MEMORY_BACKEND','sqlite')
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    sys.path.insert(0,str(ROOT/'Crush.skill'))
    sys.path.insert(0,str(ROOT/'scripts'))
    import execute
    monkeypatch.setattr(execute,'DATA_DIR',tmp_path)
    instance=execute.CrushSkillRuntime()
    yield instance
    instance.memory.sqlite.close()


def test_plain_import(runtime):
    result=runtime.run('chat_import','plain',{'source_text':'她: 周末见\n我: 好的'})
    assert result['success']


def test_import_state_mode_delete(runtime,tmp_path):
    from smoke_weflow_import import sample
    source=json.dumps(sample(),ensure_ascii=False)
    imported=runtime.run('weflow_import','one',{'source_text':source})
    turn=runtime.run('chat_turn','one',{'message':'你喜欢我吗'})
    assert turn['memory_context']['mode']=='companion'
    assert '关系复盘助手' not in turn['runtime_prompt']
    state=runtime.memory.sqlite.load_session('one')['state']
    runtime.run('weflow_import','one',{'source_text':source})
    assert runtime.memory.sqlite.load_session('one')['state']==state
    runtime.run('chat_turn','one',{'message':'分析一下','mode':'review'})
    assert runtime.memory.sqlite.load_session('one')['state']==state
    runtime.run('delete_import','one',{'import_id':imported['import_id']})
    assert not list((tmp_path/'weflow').rglob('persona_profile.json'))


def test_historical_chinese_retrieval(runtime):
    db=runtime.memory.sqlite
    db.append_episode('recall','user','周六一起看电影')
    for i in range(125):db.append_episode('recall','user',f'其他信息{i}')
    rows=db.retrieve_relevant('recall','周六电影')
    assert rows[0]['content']=='周六一起看电影'


def test_cli_quote_sleep_key_and_probability(runtime,tmp_path,monkeypatch):
    from crush_cli import app
    args=app.build_parser().parse_args(['--plain','--home',str(tmp_path),'--data-dir',str(tmp_path),'--session','a'])
    cli=app.CrushCLI(args)
    cli.ensure_session()
    assert cli.command('/use "') is True
    assert cli.assess_reply_to_pending('刚刚睡着了',{})['quality']=='valid_busy'
    before=cli.proactive_probability()
    cli.timeline_state().update(initiative=.08,warmth=.12,ignored_streak=5)
    assert cli.proactive_probability()<before
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-openai')
    assert app.ChatClient({'provider':'claude','api_key':'synthetic-claude'}).api_key=='synthetic-claude'
    with patch.object(app,'urlopen',side_effect=TimeoutError('test')):
        with pytest.raises(app.ModelError):app.ChatClient({'api_key':'fake'}).reply('system','hello')


def test_legacy_async_session_identity(runtime,tmp_path):
    from crush_cli import app
    cli=app.CrushCLI(app.build_parser().parse_args(['--plain','--home',str(tmp_path),'--data-dir',str(tmp_path),'--session','a']))
    cli.ensure_session()
    cli.runtime.run('quick_start','b',{'config':{'archetype':'security'}})
    def switch(*args):
        cli.session_id='b'
        return '只属于会话 A 的合成回复'
    with patch.object(app.random,'random',return_value=0),patch.object(cli.client,'reply',side_effect=switch):
        cli.maybe_proactive_message()
    assert any('会话 A' in e['content'] for e in cli.runtime.memory.sqlite.get_recent_episodes('a'))
    assert not any('会话 A' in e['content'] for e in cli.runtime.memory.sqlite.get_recent_episodes('b'))
