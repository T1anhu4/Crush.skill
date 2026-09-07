#!/usr/bin/env python3
"""Install a validated Crush skill, preserving an existing installation on failure."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid


EXCLUDED = {'data', 'dist', 'examples', 'node_modules', 'output', 'private', '__pycache__'}
SUFFIXES = {'.pyc', '.sqlite3', '.sqlite', '.db', '.log'}


def copy_source(source, destination):
    destination.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        if child.is_symlink() or child.name.startswith('.') or child.name in EXCLUDED or child.suffix in SUFFIXES:
            continue
        target = destination / child.name
        if child.is_dir():
            copy_source(child, target)
        elif child.is_file():
            shutil.copy2(child, target)


def verify(source):
    for name in ('SKILL.md', 'manifest.json', 'execute.py', 'v3.py'):
        if not (source / name).is_file() or (source / name).is_symlink():
            raise ValueError(f'Invalid skill candidate: missing regular file {name}')
    if not (source / 'engines').is_dir() or (source / 'engines').is_symlink():
        raise ValueError('Invalid skill candidate: missing engines directory')
    json.loads((source / 'manifest.json').read_text())
    # --help imports the shared runtime without creating a database or contacting a model.
    subprocess.run([sys.executable, '-B', str(source / 'v3.py'), '--help'],
                   cwd=source, check=True, stdout=subprocess.DEVNULL)


def target_root(args):
    if args.target_dir:
        return Path(args.target_dir).expanduser().resolve()
    home = Path.home()
    if args.platform == 'claude':
        return home / '.claude/skills'
    if args.platform == 'openclaw':
        override = os.environ.get('OPENCLAW_SKILLS_DIR')
        default = home / '.openclaw/workspace/skills'
        return Path(override).expanduser().resolve() if override else (default if default.is_dir() else home / '.openclaw/skills')
    override = os.environ.get('QWENPAW_SKILLS_DIR')
    default = Path('/app/working/workspaces/default/skills')
    return Path(override).expanduser().resolve() if override else (default if default.is_dir() else home / '.qwen/skills')


def overlaps(a, b):
    return a == b or a in b.parents or b in a.parents


def install(args, source):
    source = source.resolve()
    core = source / 'crush_core'
    if not core.is_dir():
        core = source.parent / 'crush_core'
    if core.is_symlink() or not (core / '__main__.py').is_file():
        raise ValueError('Source requires a regular crush_core directory beside or inside the skill')
    root = target_root(args).resolve()
    if any(overlaps(root, item) for item in (source, core.resolve())):
        raise ValueError('Source and target directories overlap; choose a separate skill root')
    if root in {Path('/'), Path.home().resolve()}:
        raise ValueError('Unsafe target directory; choose a dedicated skill root')
    destination = root / args.skill_name
    if (destination.exists() or destination.is_symlink()) and not args.force:
        raise ValueError(f'Destination already exists: {destination}; use --force to back it up')
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.crush-install-', dir=root) as stage_dir:
        candidate = Path(stage_dir) / 'candidate'
        if args.mode == 'copy':
            copy_source(source, candidate)
            copy_source(core, candidate / 'crush_core')
            verify(candidate)
        else:
            verify(source)
            candidate.symlink_to(source, target_is_directory=True)
        backup = None
        if destination.exists() or destination.is_symlink():
            backup = root / f'{args.skill_name}.bak.{uuid.uuid4().hex}'
            destination.rename(backup)
        try:
            candidate.rename(destination)
        except BaseException:
            if backup:
                backup.rename(destination)
            raise
    print(f'Installed successfully\nPlatform: {args.platform}\nSkill dir: {destination}')
    if backup:
        print(f'Previous installation preserved: {backup}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', required=True, choices=['claude', 'openclaw', 'qwenpaw'])
    parser.add_argument('--repo-url', help='Clone a repository temporarily, then copy its skill')
    parser.add_argument('--source-dir', help='Local skill source, or a relative path inside --repo-url')
    parser.add_argument('--target-dir', help='Override platform skill root')
    parser.add_argument('--skill-name', default='crush-skill')
    parser.add_argument('--mode', choices=['copy', 'symlink'], default='copy')
    parser.add_argument('--force', action='store_true', help='Preserve a backup and replace the existing skill')
    args = parser.parse_args()
    try:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', args.skill_name):
            raise ValueError('--skill-name must be a single directory name without path traversal')
        if args.repo_url and args.mode == 'symlink':
            raise ValueError('--repo-url cannot use symlink mode: the clone is temporary; use copy mode')
        if args.repo_url:
            with tempfile.TemporaryDirectory(prefix='crush-source-') as temp:
                repo = Path(temp) / 'repo'
                subprocess.run(['git', 'clone', '--depth', '1', '--', args.repo_url, str(repo)], check=True)
                source = (repo / args.source_dir).resolve() if args.source_dir else (repo / 'Crush.skill')
                if not args.source_dir and not source.is_dir():
                    source = repo
                if source != repo and repo not in source.parents:
                    raise ValueError('--source-dir must stay inside the cloned repository')
                install(args, source)
        else:
            source = Path(args.source_dir).expanduser() if args.source_dir else Path(__file__).resolve().parents[1] / 'Crush.skill'
            install(args, source)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Install failed: {error}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
