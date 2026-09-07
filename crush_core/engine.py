"""Transactional event engine. No model call runs inside a database transaction."""
from contextlib import contextmanager
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import threading
import time
import uuid
from zoneinfo import ZoneInfo

from .characters import CHARACTERS, initial_mind
from .provider import generate, ProviderError
from .life import due_facts


def uid():
    return uuid.uuid4().hex


def encode(value):
    return json.dumps(value, ensure_ascii=False)


def tokens(text):
    result = set(re.findall(r"[a-z0-9]+", text.lower()))
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        result.update(run[i:i+2] for i in range(max(1, len(run)-1)))
    return result


class Engine:
    def __init__(self, path, settings=lambda: {}, generator=generate):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.settings = settings
        self.generator = generator
        self.lock = threading.RLock()
        self.local = threading.local()
        with self.db() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, character TEXT, mode TEXT, clock REAL,
                anchor REAL, timezone TEXT, paused INTEGER, mind TEXT, created REAL, revision INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY, session TEXT, role TEXT, content TEXT,
                at REAL, status TEXT, reply_to TEXT, read_at REAL, request_id TEXT, UNIQUE(session,request_id));
            CREATE INDEX IF NOT EXISTS message_session ON messages(session,at);
            CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, session TEXT, message TEXT, due REAL,
                status TEXT, life TEXT, error TEXT DEFAULT '', result TEXT, lease REAL DEFAULT 0);
            CREATE INDEX IF NOT EXISTS job_status ON jobs(status,due);
            CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, session TEXT, kind TEXT, at REAL, data TEXT);
            CREATE INDEX IF NOT EXISTS event_session ON events(session,at);
            CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY, session TEXT, kind TEXT, topic TEXT,
                text TEXT, quote TEXT, source TEXT, at REAL, tier TEXT, active INTEGER DEFAULT 1);
            CREATE INDEX IF NOT EXISTS memory_session ON memories(session,active);
            CREATE TABLE IF NOT EXISTS life_events(id TEXT PRIMARY KEY, session TEXT, story_key TEXT,
                thread TEXT, step INTEGER, at REAL, text TEXT, offered_at REAL, shared_at REAL,
                UNIQUE(session,story_key));
            CREATE INDEX IF NOT EXISTS life_session ON life_events(session,at);
            CREATE TABLE IF NOT EXISTS character_profiles(session TEXT PRIMARY KEY,data TEXT);
            CREATE TABLE IF NOT EXISTS legacy_records(id TEXT PRIMARY KEY,session TEXT,source_table TEXT,data TEXT);
            CREATE TABLE IF NOT EXISTS legacy_migrations(fingerprint TEXT PRIMARY KEY,session TEXT);
            """)
            columns = {row['name'] for row in db.execute('PRAGMA table_info(jobs)')}
            if 'lease' not in columns:
                db.execute('ALTER TABLE jobs ADD COLUMN lease REAL DEFAULT 0')
            if 'life_id' not in columns:
                db.execute('ALTER TABLE jobs ADD COLUMN life_id TEXT')
            if 'reason' not in columns:
                db.execute("ALTER TABLE jobs ADD COLUMN reason TEXT DEFAULT 'scheduled'")

    @contextmanager
    def db(self):
        with self.lock:
            if getattr(self.local, 'connection', None) is not None:
                yield self.local.connection
                return
            connection = sqlite3.connect(self.path, timeout=15)
            self.local.connection = connection
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                self.local.connection = None
                connection.close()

    def session(self, db, sid):
        row = db.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
        if not row:
            raise ValueError("这段会话不存在。")
        return dict(row)

    def now(self, session):
        return session['clock'] + max(0, time.time() - session['anchor'])

    def character(self, session):
        with self.db() as db:
            row=db.execute('SELECT data FROM character_profiles WHERE session=?',(session['id'],)).fetchone()
            return json.loads(row['data']) if row else CHARACTERS[session['character']]

    def event(self, db, sid, kind, at, data):
        db.execute("INSERT INTO events VALUES(?,?,?,?,?)", (uid(), sid, kind, at, encode(data)))
        db.execute("UPDATE sessions SET revision=revision+1 WHERE id=?", (sid,))

    def message(self, db, sid, role, content, at, status='sent', request_id=None, reply_to=None):
        mid = uid()
        db.execute("INSERT INTO messages VALUES(?,?,?,?,?,?,?,?,?)", (mid, sid, role, content, at, status, reply_to, None, request_id))
        return mid

    def create(self, character='lin', mode='demo', timezone='Asia/Shanghai'):
        if character not in CHARACTERS or mode not in {'demo', 'live'}:
            raise ValueError("场景或模式无效。")
        try:
            tz = ZoneInfo(timezone)
        except Exception:
            raise ValueError("时区无效。")
        now = time.time()
        clock = now if mode == 'live' else datetime.now(tz).replace(hour=18, minute=35, second=0, microsecond=0).timestamp()
        sid = uid()
        with self.db() as db:
            db.execute("INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?,?,0)", (sid, character, mode, clock, now, timezone, 0, encode(initial_mind()), now))
            for i, text in enumerate(CHARACTERS[character]['opening']):
                self.message(db, sid, 'character', text, clock-30+i*5)
            self.event(db, sid, 'started', clock, {'text': CHARACTERS[character]['scene']})
        return self.snapshot(sid)

    def list(self):
        with self.db() as db:
            sessions = [dict(row) for row in db.execute('SELECT * FROM sessions ORDER BY created DESC')]
            result = []
            for s in sessions:
                last = db.execute("SELECT content FROM messages WHERE session=? AND status!='withdrawn' ORDER BY at DESC,rowid DESC LIMIT 1", (s['id'],)).fetchone()
                result.append({'id': s['id'], 'character': self.character(s), 'mode': s['mode'], 'preview': last['content'] if last else '', 'revision': s['revision']})
            return result

    def availability(self, s):
        now = self.now(s)
        local = datetime.fromtimestamp(now, ZoneInfo(s['timezone']))
        routine = self.character(s)['routine']
        if local.hour < routine['wake']:
            wake = local.replace(hour=routine['wake'], minute=10, second=0, microsecond=0).timestamp()
            return 'sleep', wake
        if local.weekday() < 5 and routine['busy_start'] <= local.hour < routine['busy_end']:
            return 'busy', now + 180
        return 'free', now

    def snapshot(self, sid):
        with self.db() as db:
            s = self.session(db, sid)
            messages = [dict(row) for row in db.execute("SELECT * FROM messages WHERE session=? ORDER BY at,rowid", (sid,))]
            jobs = [dict(row) for row in db.execute("SELECT id,message,status,due,error,reason FROM jobs WHERE session=? AND status IN ('queued','generating','error') ORDER BY due,rowid", (sid,))]
            for job in jobs:
                if s['paused'] and job['status']=='queued':
                    job['reason']='paused'
            memories = [dict(row) for row in db.execute("""SELECT m.id,m.kind,m.text,m.tier,m.source,m.at,
                (SELECT old.text FROM memories old WHERE old.session=m.session AND old.topic=m.topic
                 AND old.active=0 AND old.at<=m.at ORDER BY old.at DESC,old.rowid DESC LIMIT 1) AS previous
                FROM memories m WHERE m.session=? AND m.active=1 ORDER BY m.at DESC""", (sid,))]
            life = [dict(row) for row in db.execute('SELECT id,thread,at,text,shared_at FROM life_events WHERE session=? AND shared_at IS NOT NULL ORDER BY shared_at DESC LIMIT 12',(sid,))]
            return {'id': sid, 'character': self.character(s), 'mode': s['mode'], 'paused': bool(s['paused']),
                    'now': self.now(s), 'timezone': s['timezone'], 'messages': messages, 'jobs': jobs,
                    'memories': memories, 'life':life, 'revision': s['revision'], 'closed': json.loads(s['mind'])['closed']}

    def send(self, sid, content, request_id, reply_to=None):
        content = content.strip()
        if not content or len(content) > 4000 or not re.fullmatch(r'[A-Za-z0-9_-]{8,100}', request_id):
            raise ValueError("消息需要 1–4000 字，并提供有效请求标识。")
        with self.db() as db:
            s = self.session(db, sid)
            previous = db.execute('SELECT id,content FROM messages WHERE session=? AND request_id=?', (sid, request_id)).fetchone()
            if previous:
                if previous['content'] != content:
                    raise ValueError("请求标识已用于另一条消息。")
                return self.snapshot(sid)
            if json.loads(s['mind'])['closed']:
                raise ValueError("这段关系已经结束，可以在复盘后开始新的相遇。")
            if self.character(s).get('archive_only'):
                raise ValueError('迁移资料未确认成年，只能查看和导出归档，不能继续恋爱模拟。')
            if reply_to and not db.execute('SELECT id FROM messages WHERE id=? AND session=?', (reply_to, sid)).fetchone():
                raise ValueError("引用消息不属于当前会话。")
            now = self.now(s)
            first = not db.execute("SELECT 1 FROM messages WHERE session=? AND role='user' LIMIT 1",(sid,)).fetchone()
            mid = self.message(db, sid, 'user', content, now, 'queued', request_id, reply_to)
            state, due = self.availability(s)
            delay = 2.2 if s['mode'] == 'demo' else 4 + int(hashlib.sha256(content.encode()).hexdigest()[:2], 16) % 12
            reason = state if state in {'sleep','busy'} else 'pacing'
            if first and s['mode']=='live' and state!='sleep':
                due=now
                reason='first_contact'
            db.execute("INSERT INTO jobs(id,session,message,due,status,life,reason) VALUES(?,?,?,?,?,?,?)", (uid(), sid, mid, max(now+delay, due), 'queued', '',reason))
            self.event(db, sid, 'message_sent', now, {'message_id': mid})
        return self.snapshot(sid)

    def withdraw(self, sid, mid):
        with self.db() as db:
            s = self.session(db, sid)
            row = db.execute('SELECT * FROM messages WHERE session=? AND id=? AND role=\'user\'', (sid, mid)).fetchone()
            if not row:
                raise ValueError("只能撤回自己的消息。")
            if row['status'] == 'withdrawn':
                return self.snapshot(sid)
            if self.now(s) - row['at'] > 120:
                raise ValueError("只能撤回两分钟内的消息。")
            db.execute("UPDATE messages SET status='withdrawn',content='' WHERE id=?", (mid,))
            topics=[r['topic'] for r in db.execute('SELECT DISTINCT topic FROM memories WHERE session=? AND source=?',(sid,mid))]
            db.execute('DELETE FROM memories WHERE session=? AND source=?',(sid,mid))
            for topic in topics:
                db.execute('UPDATE memories SET active=0 WHERE session=? AND topic=?',(sid,topic))
                db.execute("UPDATE memories SET active=1 WHERE id=(SELECT m.id FROM memories m JOIN messages s ON s.id=m.source WHERE m.session=? AND m.topic=? AND s.status!='withdrawn' ORDER BY s.at DESC,s.rowid DESC,m.rowid DESC LIMIT 1)",(sid,topic))
            db.execute("UPDATE jobs SET status='cancelled' WHERE message=? AND status IN ('queued','generating','error')", (mid,))
            self.event(db, sid, 'withdrawn', self.now(s), {'message_id': mid, 'already_seen': bool(row['read_at'])})
        return self.snapshot(sid)

    def retry(self, sid, jid):
        with self.db() as db:
            s = self.session(db, sid)
            job = db.execute('SELECT * FROM jobs WHERE id=? AND session=?', (jid, sid)).fetchone()
            if not job or job['status'] != 'error':
                raise ValueError("这条消息不需要重试。")
            db.execute("UPDATE jobs SET status='queued',due=?,error='',reason='retry' WHERE id=?", (self.now(s), jid))
            db.execute("UPDATE messages SET status='queued' WHERE id=?", (job['message'],))
            self.event(db, sid, 'retry', self.now(s), {'job': jid})
        return self.snapshot(sid)

    def pause(self, sid, paused):
        with self.db() as db:
            s = self.session(db, sid)
            if not paused and self.character(s).get('archive_only'):
                raise ValueError('未确认成年的迁移资料不能恢复模拟。')
            db.execute('UPDATE sessions SET paused=? WHERE id=?', (int(paused), sid))
            self.event(db, sid, 'pause' if paused else 'resume', self.now(s), {})
        return self.snapshot(sid)

    def advance(self, sid, seconds):
        if not math.isfinite(seconds) or seconds < 1 or seconds > 7*86400:
            raise ValueError("时间推进范围为 1 秒到 7 天。")
        with self.db() as db:
            s = self.session(db, sid)
            if s['mode'] != 'demo':
                raise ValueError("真实时间模式不能快进。")
            now = self.now(s) + seconds
            db.execute('UPDATE sessions SET clock=?,anchor=? WHERE id=?', (now, time.time(), sid))
            self.event(db, sid, 'time_advanced', now, {'seconds': seconds})
        self.tick(sid)
        return self.snapshot(sid)

    def recall(self, db, sid, query):
        q = tokens(query)
        rows = [dict(r) for r in db.execute('SELECT * FROM memories WHERE session=? AND active=1', (sid,))]
        def score(r):
            t = tokens(r['text'])
            return len(t & q)/max(1, len(q)) + (0.2 if r['kind']=='promise' else 0)
        return sorted(rows, key=lambda r: (score(r), r['at']), reverse=True)[:8]

    def tick(self, session_id=None):
        """Called by server worker or explicit CLI tick; processes at most one job."""
        work = None
        with self.db() as db:
            # Expired worker leases recover interrupted requests without allowing
            # a new CLI reader to reset an active server's in-flight generation.
            db.execute("UPDATE jobs SET status='queued' WHERE status='generating' AND lease<?"+(' AND session=?' if session_id else ''),
                       (time.time()-120,session_id) if session_id else (time.time()-120,))
            rows=db.execute('SELECT * FROM sessions WHERE id=?',(session_id,)).fetchall() if session_id else db.execute('SELECT * FROM sessions').fetchall()
            for row in rows:
                s = dict(row)
                if s['paused']:
                    continue
                if db.execute("SELECT 1 FROM jobs WHERE session=? AND status='generating'", (s['id'],)).fetchone():
                    continue
                now = self.now(s)
                mind = json.loads(s['mind'])
                if mind['closed']:
                    continue
                start = db.execute("SELECT at FROM events WHERE session=? AND kind='started' ORDER BY at LIMIT 1",(s['id'],)).fetchone()
                for fact in ([] if self.character(s).get('migrated') else due_facts(s['character'],start['at'] if start else s['clock'],now,s['timezone'])):
                    db.execute('INSERT OR IGNORE INTO life_events VALUES(?,?,?,?,?,?,?,NULL,NULL)',
                               (uid(),s['id'],fact['key'],fact['thread'],fact['step'],fact['at'],fact['text']))
                # Consolidation is age-based and idempotent, independent of polling rate.
                changed = db.execute("UPDATE memories SET tier='long' WHERE session=? AND kind='preference' AND tier!='long' AND at<?", (s['id'], now-86400)).rowcount
                changed += db.execute("UPDATE memories SET tier='mid' WHERE session=? AND tier='short' AND at<?", (s['id'], now-3600)).rowcount
                if changed:
                    self.event(db,s['id'],'memory_consolidated',now,{'count':changed})
                availability, wake = self.availability(s)
                if availability == 'sleep':
                    db.execute("UPDATE jobs SET due=MAX(due,?),reason='sleep' WHERE session=? AND status='queued'", (wake, s['id']))
                    continue
                job = db.execute("SELECT * FROM jobs WHERE session=? AND status='queued' AND due<=? ORDER BY due,rowid LIMIT 1", (s['id'], now)).fetchone()
                if not job:
                    # One life event after a quiet interval; no repeated unanswered nudges.
                    last = db.execute('SELECT * FROM messages WHERE session=? ORDER BY at DESC,rowid DESC LIMIT 1', (s['id'],)).fetchone()
                    day = datetime.fromtimestamp(now, ZoneInfo(s['timezone'])).strftime('%Y-%m-%d')
                    active = db.execute("SELECT 1 FROM jobs WHERE session=? AND status IN ('queued','generating','error')", (s['id'],)).fetchone()
                    if not active and last and now-last['at'] > 4*3600 and mind['last_life_day'] != day:
                        proactive = db.execute("SELECT at FROM events WHERE session=? AND kind='life_shared' ORDER BY at DESC LIMIT 1", (s['id'],)).fetchone()
                        user = db.execute("SELECT at FROM messages WHERE session=? AND role='user' ORDER BY at DESC LIMIT 1", (s['id'],)).fetchone()
                        if not proactive or (user and user['at'] > proactive['at']):
                            life = db.execute('SELECT * FROM life_events WHERE session=? AND offered_at IS NULL AND at>=? ORDER BY at DESC LIMIT 1',(s['id'],now-2*86400)).fetchone()
                            if life:
                                jid = uid()
                                db.execute("INSERT INTO jobs(id,session,message,due,status,life,life_id) VALUES(?,?,?,?,?,?,?)", (jid,s['id'],None,now,'queued',life['text'],life['id']))
                                db.execute('UPDATE life_events SET offered_at=? WHERE id=?',(now,life['id']))
                                mind['last_life_day']=day
                                db.execute('UPDATE sessions SET mind=? WHERE id=?',(encode(mind),s['id']))
                                job = db.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
                    if not job:
                        continue
                job = dict(job)
                if job['message']:
                    msg = db.execute('SELECT * FROM messages WHERE id=?', (job['message'],)).fetchone()
                    if not msg or msg['status'] == 'withdrawn':
                        db.execute("UPDATE jobs SET status='cancelled' WHERE id=?", (job['id'],))
                        continue
                    text = msg['content']
                    db.execute("UPDATE messages SET status='read',read_at=COALESCE(read_at,?) WHERE id=?", (now, msg['id']))
                    from .grounding import preference_topic
                    topic=preference_topic(text)
                    if topic:
                        # Capture explicit source evidence before generation; a
                        # failed request must not lose the user's correction.
                        self.store_memory(db,s['id'],msg,'preference',topic,text)
                else:
                    text = ''
                recent = [dict(r) for r in db.execute("SELECT role,content,at FROM messages WHERE session=? AND status!='withdrawn' ORDER BY at DESC,rowid DESC LIMIT 18", (s['id'],))][::-1]
                world = [dict(r) for r in db.execute('SELECT thread,step,at,text,shared_at FROM life_events WHERE session=? AND at<=? ORDER BY at DESC LIMIT 8',(s['id'],now))][::-1]
                day=datetime.fromtimestamp(now,ZoneInfo(s['timezone'])).strftime('%Y-%m-%d')
                life_key='generated:'+day
                allow_life_update=bool(s['mode']=='live' and job['message'] and start and now-start['at']>8*86400
                    and not db.execute('SELECT 1 FROM life_events WHERE session=? AND story_key=?',(s['id'],life_key)).fetchone())
                local_now=datetime.fromtimestamp(now,ZoneInfo(s['timezone']))
                local_start=datetime.fromtimestamp(start['at'] if start else s['created'],ZoneInfo(s['timezone']))
                character=self.character(s)
                model_character={key:value for key,value in character.items() if key not in {'life','scene'}}
                model_character['initial_scene']=character.get('scene','')
                for fact in world:
                    occurred=datetime.fromtimestamp(fact['at'],ZoneInfo(s['timezone']))
                    fact['local_date']=occurred.date().isoformat()
                    fact['days_ago']=(local_now.date()-occurred.date()).days
                ctx = {'character': model_character, 'session': {'mode':s['mode'], 'time':local_now.isoformat(),
                       'started_at':local_start.isoformat(),'relationship_day':max(1,(local_now.date()-local_start.date()).days+1),'month':local_now.month},
                       'mind': mind, 'recent':recent, 'memories':self.recall(db,s['id'],text), 'message':text, 'life_event':job['life'], 'world':world,
                       'allow_life_update':allow_life_update,'life_key':life_key,
                       'turn_count':db.execute("SELECT COUNT(*) FROM events WHERE session=? AND kind='decision'",(s['id'],)).fetchone()[0]}
                db.execute("UPDATE jobs SET status='generating',lease=? WHERE id=?", (time.time(),job['id']))
                self.event(db,s['id'],'reading',now,{'message_id':job['message']})
                work = job, ctx
                break
        if not work:
            return
        job, ctx = work
        try:
            from .grounding import validate_grounding, GroundingError
            result = json.loads(job['result']) if job.get('result') else self.generator(ctx, self.settings())
            self.validate(result)
            try:
                validate_grounding(result,ctx)
            except GroundingError as issue:
                # One bounded rewrite; no recursive retries, no transport retry.
                # Discard the draft: it must never become conversation evidence.
                with self.db() as db:
                    current=db.execute('SELECT status FROM jobs WHERE id=?',(job['id'],)).fetchone()
                    if not current or current['status']!='generating':
                        return
                    if self.session(db,job['session'])['paused']:
                        db.execute("UPDATE jobs SET status='queued',result=NULL WHERE id=?",(job['id'],))
                        return
                    self.event(db,job['session'],'reply_repair',self.now(self.session(db,job['session'])),{'job':job['id'],'reason':issue.code})
                repair_context={**ctx,'repair':{'reason':str(issue),'instruction':'重新生成完整动作；不补充新的个人经历，只接当前话题。'}}
                result=self.generator(repair_context,self.settings())
                self.validate(result)
                validate_grounding(result,ctx)
        except Exception as exc:
            with self.db() as db:
                current = db.execute('SELECT status FROM jobs WHERE id=?',(job['id'],)).fetchone()
                if current and current['status']=='generating':
                    error = str(exc) if isinstance(exc,ProviderError) else '回复生成失败，消息已保留，请重试。'
                    db.execute("UPDATE jobs SET status='error',error=? WHERE id=?",(error,job['id']))
                    db.execute("UPDATE messages SET status='error' WHERE id=?",(job['message'],))
                    self.event(db,job['session'],'generation_failed',time.time(),{'job':job['id'],
                        'error_code':exc.code if isinstance(exc,ProviderError) else 'internal_error'})
            return
        with self.db() as db:
            current = db.execute('SELECT status FROM jobs WHERE id=?',(job['id'],)).fetchone()
            if not current or current['status'] != 'generating':
                return
            s = self.session(db,job['session'])
            now = self.now(s)
            availability, wake = self.availability(s)
            if s['paused'] or availability=='sleep':
                db.execute("UPDATE jobs SET status='queued',result=?,due=?,reason=? WHERE id=?",(encode(result),max(now,wake),'sleep' if availability=='sleep' else 'scheduled',job['id']))
                self.event(db,s['id'],'delivery_deferred',now,{'job':job['id']})
                return
            delay=result.get('delay_minutes',0)
            if delay:
                result['delay_minutes']=0
                db.execute("UPDATE jobs SET status='queued',result=?,due=?,reason='character_delay' WHERE id=?",(encode(result),now+delay*60,job['id']))
                self.event(db,s['id'],'chose_delay',now,{'job':job['id'],'minutes':delay})
                return
            mind = json.loads(s['mind'])
            before_mind = dict(mind)
            update=result.get('life_update')
            if ctx.get('allow_life_update') and isinstance(update,dict):
                fact=update.get('text');thread=update.get('thread')
                if isinstance(fact,str) and 1<=len(fact.strip())<=240 and isinstance(thread,str) and 1<=len(thread.strip())<=60:
                    fact=fact.strip();thread=thread.strip()
                    duplicate=db.execute('SELECT 1 FROM life_events WHERE session=? AND text=?',(s['id'],fact)).fetchone()
                    if not duplicate:
                        step=db.execute('SELECT COALESCE(MAX(step),-1)+1 FROM life_events WHERE session=? AND thread=?',(s['id'],thread)).fetchone()[0]
                        shared=now if any(fact in content for content in result['messages']) else None
                        db.execute('INSERT OR IGNORE INTO life_events VALUES(?,?,?,?,?,?,?,?,?)',
                            (uid(),s['id'],ctx['life_key'],thread,step,now,fact,shared,shared))
                        self.event(db,s['id'],'life_generated',now,{'thread':thread,'source':'model_fiction'})
                        if shared:
                            self.event(db,s['id'],'life_shared',now,{'text':fact})
            mind['feeling'] = str(result.get('feeling','平静'))[:100]
            mind['interpretation'] = str(result.get('interpretation','暂不判断。'))[:220]
            change = result.get('change','neutral')
            mind['trust'] = round(max(0,min(1,mind['trust']+{'warm':.035,'repair':.025,'strained':-.04}.get(change,0))),4)
            mind['boundary'] = round(max(0,min(1,mind['boundary']+{'strained':.15,'repair':-.08}.get(change,0))),4)
            mind['open_loop'] = str(result.get('open_loop',''))[:160]
            if result['action']=='end':
                mind['closed'] = True
                db.execute("UPDATE jobs SET status='cancelled' WHERE session=? AND status='queued'", (s['id'],))
            if job['life'] and result['messages']:
                mind['last_life_day'] = datetime.fromtimestamp(now,ZoneInfo(s['timezone'])).strftime('%Y-%m-%d')
                self.event(db,s['id'],'life_shared',now,{'text':job['life']})
                if job.get('life_id'):
                    db.execute('UPDATE life_events SET shared_at=? WHERE id=?',(now,job['life_id']))
            for i, content in enumerate(result['messages']):
                self.message(db,s['id'],'character',content,now+i*.001,reply_to=job['message'])
            for item in result.get('memories',[])[:4]:
                if not isinstance(item,dict):
                    continue
                quote = str(item.get('quote','')).strip()
                source = db.execute("SELECT id,content,at,rowid FROM messages WHERE session=? AND role='user' AND status!='withdrawn' ORDER BY at DESC,rowid DESC",(s['id'],)).fetchall()
                match = next((r for r in source if quote and quote in r['content']),None)
                kind = item.get('kind')
                if not match or kind not in {'preference','promise','moment'}:
                    continue
                # Store the exact source quote, not unverified model paraphrases.
                topic = str(item.get('key') or quote[:40])[:80]
                self.store_memory(db,s['id'],match,kind,topic,quote)
            db.execute('UPDATE sessions SET mind=? WHERE id=?',(encode(mind),s['id']))
            db.execute("UPDATE jobs SET status='done',result=? WHERE id=?",(encode(result),job['id']))
            self.event(db,s['id'],'decision',now,{'message_id':job['message'],'action':result['action'],'feeling':mind['feeling'],
                       'interpretation':mind['interpretation'],'change':change,'mind_before':before_mind,'mind_after':mind})

    def store_memory(self,db,sid,source,kind,topic,quote):
        from .grounding import preference_topic
        canonical=preference_topic(quote) if kind=='preference' else None
        topic=canonical or topic
        if canonical:
            # Normalize previously extracted variants, without merging unrelated
            # preferences or allergy statements into a drink preference.
            for row in db.execute("SELECT id,quote FROM memories WHERE session=? AND kind='preference'",(sid,)).fetchall():
                if preference_topic(row['quote']):
                    db.execute('UPDATE memories SET topic=? WHERE id=?',(topic,row['id']))
        if not db.execute('SELECT 1 FROM memories WHERE session=? AND source=? AND quote=?',(sid,source['id'],quote)).fetchone():
            db.execute('INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?,0)',(uid(),sid,kind,topic,quote,quote,source['id'],source['at'],'mid' if kind=='promise' else 'short'))
        db.execute('UPDATE memories SET active=0 WHERE session=? AND topic=?',(sid,topic))
        db.execute("UPDATE memories SET active=1 WHERE id=(SELECT m.id FROM memories m JOIN messages s ON s.id=m.source WHERE m.session=? AND m.topic=? AND s.status!='withdrawn' ORDER BY s.at DESC,s.rowid DESC,m.rowid DESC LIMIT 1)",(sid,topic))

    def branch(self,sid,mid):
        """Fork just before a user message. Original history and memory stay intact."""
        with self.db() as db:
            s=self.session(db,sid)
            target=db.execute("SELECT * FROM messages WHERE id=? AND session=? AND role='user' AND status!='withdrawn'",(mid,sid)).fetchone()
            if not target:
                raise ValueError('请选择一条尚未撤回的用户消息。')
            pending=db.execute("SELECT 1 FROM jobs j JOIN messages m ON j.message=m.id WHERE j.session=? AND m.at<? AND j.status IN ('queued','generating','error')",(sid,target['at'])).fetchone()
            if pending:
                raise ValueError('此前还有未完成的消息，请先处理后再创建分支。')
            cutoff=target['at']
            new=uid();mind=initial_mind()
            events=[dict(e) for e in db.execute('SELECT * FROM events WHERE session=? AND at<? ORDER BY at,rowid',(sid,cutoff))]
            for event in events:
                data=json.loads(event['data'])
                if event['kind']=='decision' and data.get('mind_after'):
                    mind=data['mind_after']
            db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?,?,0)',(new,s['character'],s['mode'],cutoff,time.time(),s['timezone'],0,encode(mind),time.time()))
            dossier=db.execute('SELECT data FROM character_profiles WHERE session=?',(sid,)).fetchone()
            if dossier:
                db.execute('INSERT INTO character_profiles VALUES(?,?)',(new,dossier['data']))
                if json.loads(dossier['data']).get('archive_only'):
                    db.execute('UPDATE sessions SET paused=1 WHERE id=?',(new,))
            ids={}
            messages=db.execute('SELECT * FROM messages WHERE session=? AND at<? ORDER BY at,rowid',(sid,cutoff)).fetchall()
            for message in messages:
                ids[message['id']]=self.message(db,new,message['role'],message['content'],message['at'],message['status'],None,ids.get(message['reply_to']))
                db.execute('UPDATE messages SET read_at=? WHERE id=?',(message['read_at'],ids[message['id']]))
            for memory in db.execute('SELECT * FROM memories WHERE session=? AND at<?',(sid,cutoff)).fetchall():
                if memory['source'] in ids:
                    db.execute('INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?,?)',(uid(),new,memory['kind'],memory['topic'],memory['text'],memory['quote'],ids[memory['source']],memory['at'],memory['tier'],memory['active']))
            # Re-evaluate fact validity at the branch point, not at the parent's present.
            topics=db.execute('SELECT DISTINCT topic FROM memories WHERE session=?',(new,)).fetchall()
            for topic in topics:
                db.execute('UPDATE memories SET active=0 WHERE session=? AND topic=?',(new,topic['topic']))
                db.execute('UPDATE memories SET active=1 WHERE id=(SELECT id FROM memories WHERE session=? AND topic=? ORDER BY at DESC,rowid DESC LIMIT 1)',(new,topic['topic']))
            for event in events:
                data=json.loads(event['data'])
                if data.get('message_id'):
                    data['message_id']=ids.get(data['message_id'])
                self.event(db,new,event['kind'],event['at'],data)
            for life in db.execute('SELECT * FROM life_events WHERE session=? AND at<?',(sid,cutoff)).fetchall():
                offered = life['offered_at'] if life['offered_at'] and life['offered_at']<cutoff else None
                shared = life['shared_at'] if life['shared_at'] and life['shared_at']<cutoff else None
                db.execute('INSERT INTO life_events VALUES(?,?,?,?,?,?,?,?,?)',(uid(),new,life['story_key'],life['thread'],life['step'],life['at'],life['text'],offered,shared))
            self.event(db,new,'branch',cutoff,{'from_session':sid,'from_message':mid,'text':'从这一刻尝试另一种表达。原故事保留。'})
        return self.snapshot(new)

    @staticmethod
    def validate(result):
        if not isinstance(result,dict) or result.get('action') not in {'reply','wait','end'}:
            raise ProviderError('模型动作格式无效，可重试。')
        messages = result.get('messages')
        if not isinstance(messages,list) or len(messages)>3 or any(not isinstance(s,str) or not s.strip() or len(s)>1200 for s in messages):
            raise ProviderError('模型消息格式无效，可重试。')
        if result['action'] != 'wait' and not messages:
            raise ProviderError('模型返回了空消息，可重试。')
        if result['action']=='wait' and messages:
            raise ProviderError('等待动作不能包含消息。')
        if not isinstance(result.get('memories',[]),list):
            raise ProviderError('模型记忆格式无效，可重试。')
        delay=result.get('delay_minutes',0)
        if not isinstance(delay,int) or isinstance(delay,bool) or not 0<=delay<=180:
            raise ProviderError('模型延迟时间无效，可重试。')

    def review(self,sid):
        with self.db() as db:
            s = self.session(db,sid)
            events = [dict(r) for r in db.execute("SELECT * FROM events WHERE session=? AND kind IN ('decision','life_shared','withdrawn','started') ORDER BY at DESC,rowid DESC LIMIT 30",(sid,))]
            for event in events:
                event['data'] = json.loads(event['data'])
                mid = event['data'].get('message_id')
                msg = db.execute('SELECT content FROM messages WHERE id=?',(mid,)).fetchone() if mid else None
                event['quote'] = msg['content'] if msg else ''
            return {'events':events,'mind':json.loads(s['mind']), 'note':'以下是虚构角色的状态摘要，不代表现实中任何人的想法。复盘不会改变关系。'}

    def export(self,sid):
        with self.db() as db:
            snapshot=self.snapshot(sid)
            archive=[{'source_table':r['source_table'],'data':json.loads(r['data'])}
                     for r in db.execute('SELECT * FROM legacy_records WHERE session=? ORDER BY rowid',(sid,))]
            return {'session':snapshot,'review':self.review(sid),'legacy_archive':archive,
                    'notice':'导出可能包含私人聊天与原始导入资料，请勿公开上传。'}

    def delete(self,sid):
        with self.db() as db:
            self.session(db,sid)
            for table in ['messages','jobs','events','memories','life_events','character_profiles','legacy_records','legacy_migrations']:
                db.execute(f'DELETE FROM {table} WHERE session=?',(sid,))
            db.execute('DELETE FROM sessions WHERE id=?',(sid,))
