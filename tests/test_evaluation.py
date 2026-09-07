import json
from unittest.mock import patch

import pytest

from crush_core.evaluate import main, run_evaluation


@pytest.mark.parametrize('character', ['lin', 'zhou', 'qiao'])
def test_offline_longitudinal_report(character):
    with patch('urllib.request.urlopen', side_effect=AssertionError('No network')), patch('crush_core.provider.urlopen', side_effect=AssertionError('No network')):
        report = run_evaluation(character)
    assert report['days'] == [1, 3, 14, 30]
    assert report['automated_status'] == 'PASS', [c for c in report['automated_invariants'] if c['status'] == 'FAIL']
    assert report['human_naturalness']['status'] == 'NOT_ASSESSED'
    assert report['human_naturalness']['release_gate'] == 'BLOCKED'
    assert report['diagnostics']['repetition_status'] == 'FAIL'
    assert len(report['transcript']) == 15


def test_cli_writes_report_and_does_not_claim_release(tmp_path):
    output = tmp_path / 'report.json'
    assert main(['--output', str(output)]) == 2
    assert json.loads(output.read_text())['mode'] == 'offline_demo'
    with pytest.raises(FileExistsError):
        main(['--output', str(output)])


@pytest.mark.parametrize('args', [['--live'], ['--config', '/no/private/config'], ['--allow-synthetic-network'], ['--live', '--config', '/no/private/config']])
def test_network_requires_all_explicit_flags(args):
    with patch('pathlib.Path.read_text', side_effect=AssertionError('Must not read config')):
        with pytest.raises(SystemExit) as exc:
            main(args)
    assert exc.value.code == 2


def test_provider_failure_is_an_invariant_failure():
    with patch('crush_core.evaluate.demo', side_effect=RuntimeError('synthetic failure')):
        report = run_evaluation()
    assert report['automated_status'] == 'FAIL'
    assert report['human_naturalness']['status'] == 'NOT_ASSESSED'


def test_explicit_live_adapter_redacts_key_without_real_network():
    from crush_core.provider import demo
    key = 'synthetic-secret-for-test'
    def fake_live(ctx, config):
        assert ctx['session']['mode'] == 'live'
        result = demo(ctx)
        result['messages'].append(key)
        return result
    with patch('crush_core.evaluate.generate', side_effect=fake_live):
        report = run_evaluation(live_config={'base': 'https://example.invalid/v1', 'model': 'fake', 'key': key})
    assert key not in json.dumps(report)
    assert '[REDACTED]' in json.dumps(report)


def test_live_session_exercises_long_term_life_updates_without_network():
    from crush_core.provider import demo
    contexts = []

    def fake_live(ctx, config):
        contexts.append(ctx)
        assert ctx['session']['mode'] == 'live'
        result = demo(ctx)
        if ctx['allow_life_update']:
            fact = '合成生活进展：' + ctx['session']['time'][:10]
            result['life_update'] = {'thread': 'synthetic-progress', 'text': fact}
            result['messages'] = [fact]
        return result

    with patch('crush_core.evaluate.generate', side_effect=fake_live), patch('crush_core.provider.urlopen', side_effect=AssertionError('No network')):
        report = run_evaluation(live_config={'base': 'https://example.invalid/v1', 'model': 'fake', 'key': 'fake-key'})
    assert report['automated_status'] == 'PASS'
    for date in ('2026-01-05', '2026-01-07'):
        assert all(not ctx['allow_life_update'] for ctx in contexts if ctx['session']['time'].startswith(date))
    for date in ('2026-01-18', '2026-02-03'):
        daily = [ctx for ctx in contexts if ctx['session']['time'].startswith(date)]
        assert daily and daily[0]['allow_life_update'] is True
        assert all(ctx['allow_life_update'] is False for ctx in daily[1:])
        assert any(fact['text'] == '合成生活进展：' + date for fact in daily[1]['world'])
