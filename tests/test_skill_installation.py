import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def source_tree(tmp_path):
    repo = tmp_path / 'source'
    for name in ('Crush.skill', 'crush_core'):
        shutil.copytree(ROOT / name, repo / name, ignore=shutil.ignore_patterns(
            'data', 'dist', '__pycache__', 'node_modules', 'output'))
    return repo / 'Crush.skill'


def install(source, target, *options):
    return subprocess.run(['bash', str(ROOT / 'scripts/install_skill.sh'),
                           '--platform', 'claude', '--source-dir', str(source),
                           '--target-dir', str(target), *options],
                          text=True, capture_output=True)


def test_copy_contains_core_and_excludes_private_paths(tmp_path):
    source = source_tree(tmp_path)
    for rel in ('data/memory.json', '.hidden/key', 'nested/.env', 'node_modules/a.js',
                'output/private.txt', 'private/token', 'cache.sqlite3'):
        file = source / rel
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('private')
    (source / 'leak.py').symlink_to(source / 'data/memory.json')
    target = tmp_path / 'skills'
    result = install(source, target)
    assert result.returncode == 0, result.stderr
    destination = target / 'crush-skill'
    assert (destination / 'crush_core/__main__.py').is_file()
    assert not any('private' in p.relative_to(destination).parts or p.is_symlink() or p.name == '.env'
                   for p in destination.rglob('*'))
    assert not (destination / 'data').exists()
    assert not (destination / 'node_modules').exists()
    assert not (destination / 'output').exists()
    result = subprocess.run([sys.executable, str(destination / 'v3.py'), 'start',
                             '--mode', 'demo', '--home', str(tmp_path / 'runtime')],
                            cwd=tmp_path, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert isinstance(json.loads(result.stdout), dict)


def test_invalid_candidate_keeps_existing_skill_then_force_backs_it_up(tmp_path):
    source = source_tree(tmp_path)
    target = tmp_path / 'skills'
    destination = target / 'crush-skill'
    destination.mkdir(parents=True)
    (destination / 'keep.txt').write_text('original')
    manifest = source / 'manifest.json'
    contents = manifest.read_text()
    manifest.unlink()
    result = install(source, target, '--force')
    assert result.returncode != 0
    assert (destination / 'keep.txt').read_text() == 'original'
    manifest.write_text(contents)
    result = install(source, target, '--force')
    assert result.returncode == 0, result.stderr
    assert any(p.read_text() == 'original' for p in target.glob('crush-skill.bak.*/keep.txt'))


def test_reject_traversal_and_overlap_before_writing(tmp_path):
    source = source_tree(tmp_path)
    for name in ('..', '../escape', 'nested/name', '/absolute'):
        result = install(source, tmp_path / 'skills', '--skill-name', name, '--force')
        assert result.returncode != 0
        assert 'skill-name' in result.stderr
    for target in (source, source / 'nested', source.parent):
        result = install(source, target, '--force')
        assert result.returncode != 0
        assert 'overlap' in result.stderr
    assert not (source / 'nested').exists()


def test_remote_symlink_is_rejected_before_clone(tmp_path):
    result = install(tmp_path / 'unused', tmp_path / 'skills',
                     '--repo-url', '/nonexistent-local-repo', '--mode', 'symlink')
    assert result.returncode != 0
    assert 'symlink' in result.stderr and 'temporary' in result.stderr
    assert not (tmp_path / 'skills').exists()


def test_local_symlink_remains_usable(tmp_path):
    source = source_tree(tmp_path)
    target = tmp_path / 'skills'
    result = install(source, target, '--mode', 'symlink')
    assert result.returncode == 0, result.stderr
    assert (target / 'crush-skill').resolve() == source
    result = subprocess.run([sys.executable, str(target / 'crush-skill/v3.py'), '--help'],
                            cwd=tmp_path, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_local_repo_clone_copy_survives_temporary_checkout_cleanup(tmp_path):
    source = source_tree(tmp_path)
    repo = source.parent
    subprocess.run(['git', 'init', str(repo)], check=True, capture_output=True)
    subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True, capture_output=True)
    subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Test',
                    '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false',
                    'commit', '-m', 'fixture'], check=True, capture_output=True)
    target = tmp_path / 'skills'
    result = subprocess.run(['bash', str(ROOT / 'scripts/install_skill.sh'),
                             '--platform', 'openclaw', '--repo-url', str(repo),
                             '--target-dir', str(target)], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    installed = target / 'crush-skill'
    assert not installed.is_symlink()
    result = subprocess.run([sys.executable, str(installed / 'v3.py'), '--help'],
                            cwd=tmp_path, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
