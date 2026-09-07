import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def test_packaged_skill_runs_shared_runtime(tmp_path):
    spec=importlib.util.spec_from_file_location('package_skill',ROOT/'scripts/package_skill.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    archive=tmp_path/'skill.zip';module.build_zip(archive)
    installed=tmp_path/'installed'
    with zipfile.ZipFile(archive) as z:
        assert 'crush_core/engine.py' in z.namelist()
        assert not any('__pycache__' in n or n.endswith('.sqlite3') for n in z.namelist())
        z.extractall(installed)
    def run(*args):
        return subprocess.run([sys.executable,str(installed/'v3.py'),*args,'--home',str(tmp_path/'data')],cwd=tmp_path,text=True,capture_output=True)
    started=run('start');assert started.returncode==0,started.stderr
    sid=json.loads(started.stdout)['id']
    assert run('tick').returncode!=0
    assert run('tick','--session',sid).returncode==0
    assert json.loads(run('export','--session',sid).stdout)['legacy_archive']==[]
    assert run('delete','--session',sid).returncode!=0
    assert run('delete','--session',sid,'--confirm-delete').returncode==0


def test_migration_preview_does_not_create_destination(tmp_path):
    target=tmp_path/'target'
    result=subprocess.run([sys.executable,'-m','crush_core','migrate','--source-db',str(tmp_path/'missing'),
                           '--legacy-session','test','--home',str(target)],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==1
    assert not target.exists()
