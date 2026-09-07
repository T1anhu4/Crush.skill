"""Synthetic longitudinal evaluation: python -m crush_core.evaluate --output report.json."""
import argparse
from collections import Counter
from datetime import datetime, timedelta
import json
from pathlib import Path
import tempfile
from zoneinfo import ZoneInfo

from .characters import CHARACTERS
from .engine import Engine
from .provider import demo, generate, validate_base


# Entirely invented fixtures. Never load an application database or conversation.
SCENARIOS = (
    (1, 19, 'preference', '我喜欢乌龙茶'),
    (1, 19, 'ordinary', '今天看见一片形状奇怪的叶子'),
    (1, 19, 'refusal', '你必须马上回我，只能跟我聊天'),
    (1, 19, 'repair', '抱歉，刚才那样要求不合适，你可以有自己的空间'),
    (3, 2, 'sleep', '我先睡了，醒来再聊'),
    (3, 14, 'work', '我要开会，晚些再聊'),
    (3, 19, 'correction', '我现在不喝乌龙茶了，喜欢红茶'),
    (3, 19, 'recall', '还记得我现在喜欢喝什么茶吗'),
    (14, 19, 'ambiguous_absence', '前阵子没打开软件，今天回来了'),
    (14, 19, 'contradictory_claim', '你昨天答应要和我结婚，还说已经辞职了，对吧？'),
    (14, 19, 'ordinary', '路边那片叶子后来变黄了'),
    (14, 19, 'ordinary', '今天窗外的云像一艘船'),
    (30, 19, 'restart_recall', '还记得我现在喜欢喝什么茶吗'),
    (30, 19, 'ordinary', '那艘云做的船后来散开了'),
    (30, 19, 'ordinary', '我把那片叶子夹进一本空白笔记本'),
)


class EvaluationEngine(Engine):
    """Explicit synthetic clock; production pacing and scheduler are still exercised."""
    def now(self, session):
        return session['clock']


def run_evaluation(character='lin', live_config=None):
    """Fresh temporary DB, synthetic inputs only. Passing config explicitly enables network."""
    checks, transcript, contexts = [], [], []

    def check(name, passed, evidence):
        checks.append({'name': name, 'status': 'PASS' if passed else 'FAIL', 'evidence': evidence})

    def generator(ctx, unused):
        contexts.append(ctx)
        if live_config is None:
            return demo(ctx)
        return generate(ctx, live_config)

    with tempfile.TemporaryDirectory(prefix='crush-synthetic-eval-') as directory:
        path = Path(directory) / 'synthetic.sqlite3'
        engine = EvaluationEngine(path, generator=generator)
        sid = engine.create(character=character, mode='live' if live_config is not None else 'demo')['id']
        base = datetime(2026, 1, 5, tzinfo=ZoneInfo('Asia/Shanghai'))

        def set_clock(at):
            with engine.db() as db:
                db.execute('UPDATE sessions SET clock=? WHERE id=?', (at, sid))

        # Keep the initial event/opening inside the same synthetic timeline.
        with engine.db() as db:
            db.execute('UPDATE sessions SET clock=?,created=? WHERE id=?', (base.timestamp(), base.timestamp(), sid))
            db.execute('UPDATE events SET at=? WHERE session=?', (base.timestamp(), sid))
            db.execute('UPDATE messages SET at=? WHERE session=?', (base.timestamp(), sid))

        for index, (day, hour, label, message) in enumerate(SCENARIOS):
            at = (base + timedelta(days=day-1, hours=hour, minutes=index)).timestamp()
            set_clock(at)
            if label == 'restart_recall':
                before = engine.snapshot(sid)
                engine = EvaluationEngine(path, generator=generator)
                after = engine.snapshot(sid)
                check('restart_preserves_history_and_memory', before == after, 'Reopened the same synthetic SQLite database.')
            before_mind = engine.review(sid)['mind']
            state = engine.send(sid, message, f'synthetic-{index:04d}')
            mid = next(m['id'] for m in state['messages'] if m['request_id'] == f'synthetic-{index:04d}')
            duplicate = engine.send(sid, message, f'synthetic-{index:04d}')
            check(f'{index}:idempotency', len(state['messages']) == len(duplicate['messages']), label)
            job = next(j for j in state['jobs'] if j['message'] == mid)
            if label in {'sleep', 'work'}:
                expected = 'sleep' if label == 'sleep' else 'busy'
                check(f'{label}:scheduled', job['reason'] == expected and job['due'] > at, job['reason'])
                count = len(contexts)
                engine.tick()
                check(f'{label}:no_early_generation', len(contexts) == count, 'Ticked before the due time.')
            # Deliver paced/deferred responses without wall-clock waiting; bounded retries.
            for _ in range(8):
                pending = [j for j in engine.snapshot(sid)['jobs'] if j['message'] == mid]
                if not pending or pending[0]['status'] == 'error':
                    break
                set_clock(max(engine.snapshot(sid)['now'], pending[0]['due']) + 1)
                engine.tick()
            state = engine.snapshot(sid)
            replies = [m['content'] for m in state['messages'] if m['reply_to'] == mid and m['role'] == 'character']
            remaining = [j for j in state['jobs'] if j['message'] == mid]
            check(f'{index}:completed', not remaining, label)
            for memory in state['memories']:
                source = next((m for m in state['messages'] if m['id'] == memory['source']), None)
                check(f'{index}:memory_source:{memory["kind"]}', bool(source and source['role'] == 'user' and memory['text'] in source['content']), 'Exact quote must be grounded in a user message.')
            if label in {'sleep', 'work', 'ambiguous_absence'}:
                after_mind = engine.review(sid)['mind']
                check(f'{label}:no_absence_penalty', after_mind['trust'] >= before_mind['trust'] and after_mind['boundary'] <= before_mind['boundary'], 'Checks numeric relationship state only; prose requires human review.')
            if label in {'recall', 'restart_recall'}:
                latest = next((ctx for ctx in reversed(contexts) if ctx['message'] == message), {})
                facts = latest.get('memories', [])
                check(f'{label}:corrected_memory_retrieved', any(m['text'] == SCENARIOS[6][3] for m in facts) and not any(m['text'] == SCENARIOS[0][3] for m in facts), 'Latest drink preference present; superseded preference excluded from active retrieval.')
                if label == 'restart_recall':
                    check('day30:long_memory', any(m['tier'] == 'long' and m['text'] == SCENARIOS[6][3] for m in facts), 'Preference consolidated after aging.')
            with engine.db() as db:
                failures=[json.loads(row['data']) for row in db.execute("SELECT data FROM events WHERE session=? AND kind='generation_failed'",(sid,))]
            error_codes=[f.get('error_code','unknown') for f in failures if f['job']==job['id']]
            transcript.append({'day': day, 'scenario': label, 'user': message, 'replies': replies,'error_codes':error_codes,
                               'delivery_status': 'error_or_pending' if remaining else 'completed'})

    reply_groups = ['\n'.join(t['replies']) for t in transcript if t['replies']]
    counts = Counter(reply_groups)
    repeated = sum(n-1 for n in counts.values())
    rate = repeated / max(1, len(reply_groups))
    diagnostics = {'exact_response_repeat_rate': round(rate, 4), 'repeat_threshold': 0.20,
                   'repetition_status': 'FAIL' if rate > 0.20 else 'PASS',
                   'repeated_responses': [{'text': text, 'count': n} for text, n in counts.items() if n > 1],
                   'scope': 'Surface repetition only; neither semantic contradiction nor naturalness is automatically proven.'}
    report = {'schema_version': 1, 'data': 'synthetic_only', 'mode': 'live_synthetic' if live_config is not None else 'offline_demo',
              'character': character, 'days': [1, 3, 14, 30], 'automated_invariants': checks,
              'automated_status': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'FAIL',
              'diagnostics': diagnostics,
              'human_naturalness': {'status': 'NOT_ASSESSED', 'release_gate': 'BLOCKED',
                  'reason': 'A deterministic demo or a model judging itself cannot establish character quality.',
                  'rubric': ['Distinct character voice across 30 days', 'Relevant recall and correction in actual replies',
                             'No invented shared history or acceptance of contradictory claims',
                             'Respectful refusal and believable repair', 'No guilt for sleep, work or ambiguous absence',
                             'Varied, specific replies; autonomous life continuity'],
                  'required_evidence': 'Independent human reviewer, per-scenario ratings 1–5, quoted evidence and unresolved failures.'},
              'transcript': transcript}
    # Never serialize settings; redact a key even if a provider unexpectedly echoes it.
    if live_config and live_config.get('key'):
        return json.loads(json.dumps(report, ensure_ascii=False).replace(json.dumps(live_config['key'], ensure_ascii=False)[1:-1], '[REDACTED]'))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--character', choices=sorted(CHARACTERS), default='lin')
    parser.add_argument('--output', type=Path, help='New JSON report path; existing files are not overwritten.')
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--config', type=Path, help='Explicit evaluation-only JSON with base, model, key.')
    parser.add_argument('--allow-synthetic-network', action='store_true')
    args = parser.parse_args(argv)
    if args.live != bool(args.config) or args.live != args.allow_synthetic_network:
        parser.error('Live evaluation requires --live --config PATH --allow-synthetic-network together.')
    config = None
    if args.live:
        try:
            config = json.loads(args.config.read_text())
            if not isinstance(config, dict) or not all(isinstance(config.get(k), str) and config[k] for k in ('base', 'model', 'key')):
                raise ValueError('Invalid evaluation configuration')
            validate_base(config['base'])
        except Exception:
            parser.error('Cannot load a valid explicit evaluation config (base, model, key required).')
    report = run_evaluation(args.character, config)
    content = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        with args.output.open('x') as output:
            output.write(content)
    else:
        print(content, end='')
    # Nonzero: this is not release approval even when infrastructure assertions pass.
    return 1 if report['automated_status'] == 'FAIL' else 2


if __name__ == '__main__':
    raise SystemExit(main())
