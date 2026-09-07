"""Explicit local-only, non-destructive legacy SQLite snapshot import."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from .characters import CHARACTERS
from .engine import encode, uid

TABLES=('sessions','episodes','timeline_events','state_history','summaries','import_records','import_messages','memory_artifacts')


def read_source(path, session):
    source=Path(path).expanduser().resolve(strict=True)
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as db:
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        columns={r['name'] for r in db.execute('PRAGMA table_info(sessions)')}
        if not {'session_id','profile_json','state_json'}.issubset(columns):
            raise ValueError('源文件不是受支持的 v2 SQLite 数据库。')
        tables={r['name'] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        data={}
        for table in TABLES:
            if table in tables:
                data[table]=[dict(r) for r in db.execute(f'SELECT * FROM {table} WHERE session_id=? ORDER BY rowid',(session,))]
        if len(data['sessions'])!=1:
            raise ValueError('源会话不存在或不唯一。')
        return data


def preview(path,session):
    data=read_source(path,session)
    return {'source_session':session,'counts':{k:len(v) for k,v in data.items()},
            'requires_confirmation':True,'notice':'导入后默认暂停。历史记录、人物描述可能含私人信息；恢复自由对话会将相关内容发往模型。原数据库不修改。'}


def timestamp(value):
    try:
        dt=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return dt.replace(tzinfo=timezone.utc).timestamp() if dt.tzinfo is None else dt.timestamp()
    except (ValueError,TypeError,OverflowError):
        raise ValueError('源记录含无效时间，迁移已取消，不写入部分会话。')


def migrate(engine,path,session,confirmed=False):
    if not confirmed:
        raise ValueError('请先预览，再明确确认导入私人数据。')
    if Path(path).resolve()==engine.path.resolve():
        raise ValueError('源库和目标库不能相同。')
    data=read_source(path,session)
    fingerprint=hashlib.sha256(encode(data).encode()).hexdigest()
    try:
        profile=json.loads(data['sessions'][0]['profile_json'])
        if not isinstance(profile,dict):
            raise ValueError()
    except (ValueError,TypeError):
        raise ValueError('旧版人物资料损坏，迁移已取消。')
    messages=[]
    rolemap={'user':'user','me':'user','npc':'character','assistant':'character','target':'character'}
    for row in data.get('episodes',[]):
        if row['role'] in rolemap and isinstance(row['content'],str) and row['content'].strip():
            messages.append((timestamp(row['created_at']),rolemap[row['role']],row['content']))
    messages.sort(key=lambda r:r[0])
    dossier=dict(CHARACTERS['lin'])
    dossier.update(name=str(profile.get('name') or '迁移角色')[:60],title='从旧版继续的相遇',
                   description='从你选择的旧版会话迁移。',scene='这段对话由旧版记录迁移，历史不是新的开场。',
                   occupation='迁移的虚构角色',voice='自然、尊重边界；参考历史表达，但不声称自己是现实中的原人物。',
                   migrated=True)
    age=profile.get('age')
    # Unknown or underage identities are retained as read-only archives.
    adult=isinstance(age,int) and not isinstance(age,bool) and age>=18
    dossier['age']=age if isinstance(age,int) and not isinstance(age,bool) else None
    dossier['archive_only']=not adult
    with engine.db() as db:
        existing=db.execute('SELECT session FROM legacy_migrations WHERE fingerprint=?',(fingerprint,)).fetchone()
        if existing:
            return {'session':engine.snapshot(existing['session']),'already_imported':True}
        sid=engine.create(mode='live')['id']
        db.execute('DELETE FROM messages WHERE session=?',(sid,))
        db.execute('DELETE FROM events WHERE session=?',(sid,))
        db.execute('INSERT INTO character_profiles VALUES(?,?)',(sid,encode(dossier)))
        db.execute('UPDATE sessions SET paused=1 WHERE id=?',(sid,))
        for at,role,content in messages:
            mid=engine.message(db,sid,role,content,at)
            if role=='user':
                db.execute('INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?,1)',(uid(),sid,'moment','legacy:'+mid,content,content,mid,at,'long'))
        for table,rows in data.items():
            for row in rows:
                db.execute('INSERT INTO legacy_records VALUES(?,?,?,?)',(uid(),sid,table,encode(row)))
        db.execute('INSERT INTO legacy_migrations VALUES(?,?)',(fingerprint,sid))
        now=engine.now(engine.session(db,sid))
        engine.event(db,sid,'started',now,{'text':dossier['scene']})
        engine.event(db,sid,'legacy_migrated',now,{'counts':{k:len(v) for k,v in data.items()},'source_session':session})
        return {'session':engine.snapshot(sid),'already_imported':False,
                'notice':'原数据未改动；导入为暂停状态。旧数值状态和推断摘要只归档，不冒充 v3 已核实记忆。'}
