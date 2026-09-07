#!/usr/bin/env python3
"""Install a source checkout, staging all work before replacing an existing app."""
from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import venv

from package_cli import source_files


def install(args):
    source = Path(args.source_dir).expanduser().resolve()
    prefix = Path(args.prefix).expanduser().resolve()
    forbidden = {Path(p).resolve() for p in ('/', '/usr', '/usr/local', '/opt', '/var', '/tmp', '/private', '/etc')}
    forbidden.add(Path.home().resolve())
    if prefix in forbidden or prefix == source or source in prefix.parents or prefix in source.parents:
        raise ValueError(f'Unsafe install prefix: {prefix}; choose a dedicated directory outside the source tree')
    for name in ('crush_cli/__main__.py', 'crush_core/__init__.py', 'Crush.skill/execute.py', 'requirements.txt'):
        path = source / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'Incomplete source tree: {path}')
    app = prefix / 'app'
    binary = prefix / 'bin/crush'
    for path in (app, prefix / 'bin', prefix / 'data', prefix / 'backups', binary):
        if path.is_symlink():
            raise ValueError(f'Refusing symlink install target: {path}')
    if (app.exists() or binary.exists()) and not args.force:
        raise ValueError('Existing installation; use --force to keep a backup and replace it')
    if binary.exists() and not binary.is_file():
        raise ValueError(f'Launcher target is not a regular file: {binary}')

    prefix.mkdir(parents=True, exist_ok=True)
    # Keep the runtime here after success: moving a virtualenv breaks its scripts.
    stage = Path(tempfile.mkdtemp(prefix='.install-', dir=prefix))
    backup = None
    promoted = False
    try:
        staged_app = stage / 'app'
        staged_app.mkdir()
        for path in source_files(source):
            destination = staged_app / path.relative_to(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
        venv.EnvBuilder(with_pip=not args.offline).create(stage / 'venv')
        python = stage / 'venv/bin/python'
        if not args.offline:
            log = stage / 'install-pip.log'
            with log.open('w') as output:
                result = subprocess.run([str(python), '-m', 'pip', 'install', '--disable-pip-version-check',
                                         '--no-cache-dir', '-r', str(staged_app / 'requirements.txt')],
                                        stdout=output, stderr=subprocess.STDOUT)
            if result.returncode:
                print(f'Dependency installation failed; using lightweight fallbacks. Log: {log}', file=sys.stderr)
        subprocess.run([str(python), '-m', 'crush_cli', '--help'], cwd=staged_app,
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run([str(python), '-m', 'crush_cli', 'v3', '--help'], cwd=staged_app,
                       check=True, stdout=subprocess.DEVNULL)
        launcher = stage / 'crush'
        launcher.write_text('#!/usr/bin/env bash\nset -euo pipefail\n'
                            f'export CRUSH_HOME={shlex.quote(str(prefix))}\n'
                            f'cd {shlex.quote(str(app))}\n'
                            f'exec {shlex.quote(str(python))} -m crush_cli "$@"\n')
        launcher.chmod(0o755)
        binary.parent.mkdir(exist_ok=True)
        (prefix / 'data').mkdir(exist_ok=True)
        if app.exists() or binary.exists():
            (prefix / 'backups').mkdir(exist_ok=True)
            backup = Path(tempfile.mkdtemp(prefix='install-', dir=prefix / 'backups'))
            if app.exists():
                app.rename(backup / 'app')
            if binary.exists():
                binary.rename(backup / 'crush')
        staged_app.rename(app)
        promoted = True
        launcher.rename(binary)
    except BaseException:
        if promoted:
            app.rename(stage / 'app')
        if backup:
            if (backup / 'app').exists():
                (backup / 'app').rename(app)
            if (backup / 'crush').exists():
                (backup / 'crush').rename(binary)
        shutil.rmtree(stage)
        raise
    print(f'Crush CLI installed: {binary}\nMemory: {prefix / "data"}')
    if backup:
        print(f'Previous app and launcher preserved: {backup}')
    print(f'Add to your shell profile: export PATH={shlex.quote(str(binary.parent))}:"$PATH"')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', default='~/.crush', help='Dedicated install directory (default: ~/.crush)')
    parser.add_argument('--source-dir', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--force', action='store_true', help='Back up and replace the existing app and launcher')
    parser.add_argument('--offline', action='store_true', help='Skip pip and use built-in lightweight fallbacks')
    args = parser.parse_args()
    try:
        install(args)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Install failed: {error}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
