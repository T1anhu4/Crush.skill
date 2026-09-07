import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def source_tree(tmp_path):
    source = tmp_path / 'source'
    for name in ('scripts', 'crush_cli', 'crush_core', 'Crush.skill'):
        shutil.copytree(ROOT / name, source / name, ignore=shutil.ignore_patterns(
            'data', 'dist', '__pycache__', 'node_modules', 'output'))
    for name in ('requirements.txt', 'README.md', 'README_EN.md', 'LICENSE',
                 'requirements-web.txt', 'requirements-mem0.txt', 'Makefile'):
        shutil.copy2(ROOT / name, source / name)
    (source / 'assets').mkdir()
    (source / 'web').mkdir()
    return source


def install(source, prefix, *extra):
    return subprocess.run(['bash', str(source / 'scripts/install_cli.sh'),
                           '--source-dir', str(source), '--prefix', str(prefix),
                           '--offline', *extra], text=True, capture_output=True)


def test_offline_install_launcher_and_force_preserve_data(tmp_path):
    source = source_tree(tmp_path)
    prefix = tmp_path / 'install with spaces $dollars'
    (source / 'scripts/output').mkdir()
    (source / 'scripts/output/private.txt').write_text('private')
    result = install(source, prefix)
    assert result.returncode == 0, result.stderr
    assert (prefix / 'app/crush_core/__init__.py').is_file()
    assert not (prefix / 'app/scripts/output').exists()
    result = subprocess.run([str(prefix / 'bin/crush'), '--help'],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(prefix / 'bin/crush'), 'v3', 'start', '--mode', 'demo',
                             '--home', str(prefix / 'data/v3')],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert isinstance(json.loads(result.stdout), dict)
    assert (prefix / 'data/v3/crush.sqlite3').is_file()
    (prefix / 'data/keep.txt').write_text('private memory')
    (prefix / 'app/keep.txt').write_text('previous install')
    assert install(source, prefix).returncode != 0
    result = install(source, prefix, '--force')
    assert result.returncode == 0, result.stderr
    assert (prefix / 'data/keep.txt').read_text() == 'private memory'
    assert any(p.read_text() == 'previous install' for p in prefix.glob('backups/*/app/keep.txt'))


def test_failed_force_install_keeps_previous_launcher_and_app(tmp_path):
    source = source_tree(tmp_path)
    prefix = tmp_path / 'install'
    assert install(source, prefix).returncode == 0
    launcher = (prefix / 'bin/crush').read_text()
    (prefix / 'app/keep.txt').write_text('old app')
    (source / 'crush_cli/__main__.py').write_text('raise RuntimeError("broken candidate")')
    result = install(source, prefix, '--force')
    assert result.returncode != 0
    assert 'broken candidate' in result.stderr
    assert (prefix / 'app/keep.txt').read_text() == 'old app'
    assert (prefix / 'bin/crush').read_text() == launcher


def test_piped_installer_reports_source_requirement(tmp_path):
    result = subprocess.run(['bash'], input=(ROOT / 'scripts/install_cli.sh').read_text(),
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'source tree' in result.stderr


def test_missing_core_candidate_does_not_replace_existing_app(tmp_path):
    source = source_tree(tmp_path)
    prefix = tmp_path / 'install'
    assert install(source, prefix).returncode == 0
    launcher = (prefix / 'bin/crush').read_text()
    (source / 'crush_core/__main__.py').unlink()
    result = install(source, prefix, '--force')
    assert result.returncode != 0
    assert (prefix / 'bin/crush').read_text() == launcher


def test_reject_source_containment_and_home_without_changes(tmp_path):
    source = source_tree(tmp_path)
    for prefix in (source, source / 'install', tmp_path, Path.home(), Path('/')):
        result = install(source, prefix, '--force')
        assert result.returncode != 0
        assert 'Unsafe install prefix' in result.stderr
    assert not (source / 'app').exists()
    assert not (source / 'install').exists()


def test_source_package_excludes_private_and_build_files(tmp_path):
    spec = importlib.util.spec_from_file_location('cli_package', ROOT / 'scripts/package_cli.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = source_tree(tmp_path)
    for rel in ('web/node_modules/pkg/index.js', 'web/output/secret.txt',
                'scripts/.playwright-cli/session.json', 'Crush.skill/data/private.json',
                'web/.env', 'web/.private/key', 'scripts/local.sqlite3'):
        path = source / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('do not distribute')
    secret = tmp_path / 'outside-secret'
    secret.write_text('private')
    (source / 'scripts/leak.py').symlink_to(secret)
    module.ROOT = source
    target = tmp_path / 'cli.zip'
    with zipfile.ZipFile(target, 'w') as archive:
        for name in module.INCLUDE_DIRS:
            module.add_path(archive, source / name)
    with zipfile.ZipFile(target) as archive:
        names = archive.namelist()
    assert 'crush_core/__init__.py' in names
    assert not any('private' in n or 'node_modules' in n or 'output/' in n or 'leak.py' in n for n in names)
