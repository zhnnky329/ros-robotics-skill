#!/usr/bin/env python3
"""安装或卸载 ros-robotics 到 Codex 和 Claude Code。"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

PROJECT_NAME = 'ros-robotics'
RUNTIME_ITEMS = [
    'SKILL.md',
    'LICENSE',
    'agents',
    'references',
    'scripts/detect_ros_workspace.py',
    'scripts/check_ros_workspace_consistency.py',
    'scripts/check_tf_tree.py',
]


def codex_skill_dir(home: Path, codex_home_env: str | None = None) -> Path:
    base = Path(codex_home_env) if codex_home_env else home / '.codex'
    return base / 'skills' / PROJECT_NAME


def claude_skill_dir(home: Path) -> Path:
    return home / '.claude' / 'skills' / PROJECT_NAME


def detect_default_targets(home: Path) -> list[str]:
    targets: list[str] = []
    if os.environ.get('CODEX_HOME') or (home / '.codex').exists():
        targets.append('codex')
    if (home / '.claude').exists():
        targets.append('claude')
    return targets or ['codex']


def copy_item(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(
            source,
            destination,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'),
        )
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def install_skill_tree(source_root: Path, destination_root: Path, force: bool) -> None:
    if destination_root.exists() and force:
        shutil.rmtree(destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)
    for name in RUNTIME_ITEMS:
        source = source_root / name
        if source.exists():
            copy_item(source, destination_root / name)


def target_path(target: str, home: Path) -> Path:
    if target == 'codex':
        return codex_skill_dir(home, os.environ.get('CODEX_HOME'))
    return claude_skill_dir(home)


def main() -> None:
    parser = argparse.ArgumentParser(description='安装或卸载 ros-robotics 到 Codex/Claude Code')
    parser.add_argument('--target', choices=['auto', 'codex', 'claude', 'all'], default='auto')
    parser.add_argument('--source-root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--uninstall', action='store_true')
    args = parser.parse_args()

    source_root = Path(args.source_root).resolve()
    home = Path.home()
    if args.target == 'auto':
        targets = detect_default_targets(home)
    elif args.target == 'all':
        targets = ['codex', 'claude']
    else:
        targets = [args.target]

    for target in targets:
        destination = target_path(target, home)
        if args.uninstall:
            remove_path(destination)
            print(f'[{target}] 已卸载: {destination}')
        else:
            install_skill_tree(source_root, destination, args.force)
            print(f'[{target}] 已安装到: {destination}')


if __name__ == '__main__':
    main()
