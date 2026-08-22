#!/usr/bin/env python3
"""! @brief 校验仓库关键文件是否齐全。"""

from __future__ import annotations

from pathlib import Path

REQUIRED = [
    'SKILL.md',
    'README.md',
    'LICENSE',
    'agents/openai.yaml',
    'scripts/install.py',
    'scripts/detect_ros_workspace.py',
    'scripts/check_ros_workspace_consistency.py',
    'scripts/check_tf_tree.py',
]


def main() -> None:
    """! @brief CLI 入口。"""
    missing = [item for item in REQUIRED if not Path(item).exists()]
    if missing:
        raise SystemExit(f'缺少关键文件: {missing}')
    print('Project validation passed')


if __name__ == '__main__':
    main()
