#!/usr/bin/env python3
"""检测 ROS 2 ament/colcon 工作区并给出 Humble 构建命令。"""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class PackageInfo:
    name: str
    path: str
    build_type: str
    markers: list[str]


@dataclass
class DetectionResult:
    workspace: str
    workspace_type: str
    markers: list[str]
    package_count: int
    ros2_packages: int
    unsupported_packages: int
    unknown_packages: int
    recommended_commands: list[str]
    packages: list[PackageInfo]


def read_text_if_exists(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return ''


def parse_package_xml(path: Path) -> tuple[str | None, set[str]]:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None, set()
    name_node = root.find('name')
    package_name = name_node.text.strip() if name_node is not None and name_node.text else None
    buildtools = {
        node.text.strip()
        for node in root.findall('buildtool_depend')
        if node.text and node.text.strip()
    }
    return package_name, buildtools


def looks_like_ament_python(setup_py_text: str) -> bool:
    return 'share/ament_index/resource_index/packages' in setup_py_text


def detect_package(package_xml: Path) -> PackageInfo:
    package_dir = package_xml.parent
    cmake_text = read_text_if_exists(package_dir / 'CMakeLists.txt')
    setup_py_text = read_text_if_exists(package_dir / 'setup.py')
    package_name, buildtools = parse_package_xml(package_xml)

    if 'ament_cmake' in buildtools or 'ament_package(' in cmake_text:
        build_type = 'ament_cmake'
        markers = ['ament_cmake']
    elif 'ament_python' in buildtools or looks_like_ament_python(setup_py_text):
        build_type = 'ament_python'
        markers = ['ament_python']
    elif buildtools:
        build_type = 'unsupported'
        markers = ['unsupported-buildtool:' + ','.join(sorted(buildtools))]
    else:
        build_type = 'unknown'
        markers = []

    return PackageInfo(package_name or package_dir.name, str(package_dir), build_type, markers)


def iter_package_xml_files(root: Path) -> Iterable[Path]:
    ignored = {'build', 'devel', 'install', 'log', '.git', '.svn', '.idea', '__pycache__'}
    for path in root.rglob('package.xml'):
        if not any(part in ignored for part in path.parts):
            yield path


def detect_workspace(root: Path) -> DetectionResult:
    packages = [detect_package(path) for path in iter_package_xml_files(root)]
    markers: list[str] = []
    if (root / 'install').exists():
        markers.append('workspace:install')
    if (root / 'colcon.meta').exists():
        markers.append('workspace:colcon.meta')

    ros2_packages = sum(item.build_type in {'ament_cmake', 'ament_python'} for item in packages)
    unsupported_packages = sum(item.build_type == 'unsupported' for item in packages)
    unknown_packages = sum(item.build_type == 'unknown' for item in packages)

    if packages and ros2_packages == len(packages):
        workspace_type = 'ros2-colcon'
        commands = [
            'source /opt/ros/humble/setup.bash',
            'rosdep install --from-paths src --ignore-src -r -y',
            'colcon build --symlink-install',
            'source install/setup.bash',
            'colcon test && colcon test-result --verbose',
        ]
    elif unsupported_packages:
        workspace_type = 'unsupported'
        commands = ['仅支持 ROS 2 ament package；请单独处理非 ament package']
    else:
        workspace_type = 'unknown'
        commands = ['未识别到 ROS 2 package；请检查 package.xml、CMakeLists.txt 或 setup.py']

    return DetectionResult(
        str(root), workspace_type, markers, len(packages), ros2_packages,
        unsupported_packages, unknown_packages, commands, packages,
    )


def print_human_readable(result: DetectionResult) -> None:
    print(f'workspace: {result.workspace}')
    print(f'workspace_type: {result.workspace_type}')
    print(f'package_count: {result.package_count}')
    print(f'ros2_packages: {result.ros2_packages}')
    print(f'unsupported_packages: {result.unsupported_packages}')
    print(f'unknown_packages: {result.unknown_packages}')
    if result.markers:
        print('markers:')
        for marker in result.markers:
            print(f'  - {marker}')
    print('recommended_commands:')
    for command in result.recommended_commands:
        print(f'  - {command}')
    print('packages:')
    for package in result.packages:
        marker_text = ', '.join(package.markers) if package.markers else 'none'
        print(f'  - {package.name}: {package.build_type} [{marker_text}]')


def main() -> None:
    parser = argparse.ArgumentParser(description='检测 ROS 2 ament/colcon 工作区')
    parser.add_argument('path', nargs='?', default='.', help='工作区根目录，默认当前目录')
    parser.add_argument('--json', action='store_true', help='以 JSON 输出')
    args = parser.parse_args()
    result = detect_workspace(Path(args.path).resolve())
    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print_human_readable(result)


if __name__ == '__main__':
    main()
