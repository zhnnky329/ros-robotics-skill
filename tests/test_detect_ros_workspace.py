import importlib.util
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DetectWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.ros_install_root = self.root / 'opt' / 'ros'
        environment_patch = patch.dict(os.environ, {'ROS_DISTRO': ''})
        environment_patch.start()
        self.addCleanup(environment_patch.stop)
        script_path = Path(__file__).resolve().parents[1] / 'scripts' / 'detect_ros_workspace.py'
        self.module = load_module(script_path, 'detect_ros_workspace')

    def tearDown(self):
        self.temp_dir.cleanup()

    def install_distro(self, distro):
        setup = self.ros_install_root / distro / 'setup.bash'
        setup.parent.mkdir(parents=True, exist_ok=True)
        setup.touch()
        return setup

    def detect(self, distro=None):
        return self.module.detect_workspace(self.root, distro, self.ros_install_root)

    def write_ament_cmake_workspace(self):
        package_dir = self.root / 'src' / 'demo_pkg'
        package_dir.mkdir(parents=True)
        (package_dir / 'package.xml').write_text(
            '<package><name>demo_pkg</name><buildtool_depend>ament_cmake</buildtool_depend></package>',
            encoding='utf-8',
        )
        (package_dir / 'CMakeLists.txt').write_text(
            'find_package(ament_cmake REQUIRED)\nament_package()', encoding='utf-8'
        )

    def test_detects_ros2_colcon_workspace(self):
        self.write_ament_cmake_workspace()
        setup = self.install_distro('humble')
        result = self.detect()
        self.assertEqual(result.workspace_type, 'ros2-colcon')
        self.assertEqual(result.ros2_packages, 1)
        self.assertEqual(result.packages[0].build_type, 'ament_cmake')
        self.assertEqual(result.ros_distro, 'humble')
        self.assertEqual(result.ros_distro_source, 'installation')
        self.assertEqual(result.recommended_commands[0], f'source {shlex.quote(str(setup))}')
        self.assertIn('--rosdistro humble', result.recommended_commands[1])

    def test_detects_single_jazzy_installation(self):
        self.write_ament_cmake_workspace()
        self.install_distro('jazzy')
        result = self.detect()
        self.assertEqual(result.ros_distro, 'jazzy')
        self.assertEqual(result.ros_distro_source, 'installation')
        self.assertIn('/jazzy/setup.bash', result.recommended_commands[0])
        self.assertIn('--rosdistro jazzy', result.recommended_commands[1])
        self.assertFalse(result.warnings)

    def test_environment_selects_from_multiple_installations(self):
        self.write_ament_cmake_workspace()
        for distro in ('humble', 'jazzy'):
            self.install_distro(distro)
        for distro in ('humble', 'jazzy'):
            with self.subTest(distro=distro), patch.dict(os.environ, {'ROS_DISTRO': distro}):
                result = self.detect()
                self.assertEqual(result.ros_distro, distro)
                self.assertEqual(result.ros_distro_source, 'environment')
                self.assertIn(f'/{distro}/setup.bash', result.recommended_commands[0])

    def test_explicit_target_overrides_environment_with_warning(self):
        self.write_ament_cmake_workspace()
        for distro in ('humble', 'jazzy'):
            self.install_distro(distro)
        with patch.dict(os.environ, {'ROS_DISTRO': 'humble'}):
            result = self.detect('jazzy')
        self.assertEqual(result.ros_distro, 'jazzy')
        self.assertEqual(result.ros_distro_source, 'argument')
        self.assertIn('/jazzy/setup.bash', result.recommended_commands[0])
        self.assertIn('新终端', result.warnings[0])

    def test_missing_environment_and_installation_do_not_guess(self):
        self.write_ament_cmake_workspace()
        result = self.detect()
        self.assertEqual(result.workspace_type, 'ros2-colcon')
        self.assertIsNone(result.ros_distro)
        self.assertEqual(result.ros_distro_source, 'unknown')
        self.assertEqual(result.recommended_commands, [])
        self.assertIn('--ros-distro', result.warnings[0])

    def test_multiple_installations_require_selection(self):
        self.write_ament_cmake_workspace()
        self.install_distro('jazzy')
        for other in ('humble', 'rolling'):
            with self.subTest(other=other):
                setup = self.install_distro(other)
                result = self.detect()
                self.assertIsNone(result.ros_distro)
                self.assertEqual(result.recommended_commands, [])
                self.assertIn(other, result.warnings[0])
                setup.unlink()

    def test_directory_without_setup_does_not_count_as_installation(self):
        self.write_ament_cmake_workspace()
        self.install_distro('jazzy')
        (self.ros_install_root / 'humble').mkdir()
        result = self.detect()
        self.assertEqual(result.ros_distro, 'jazzy')

    def test_unsupported_environment_never_falls_back_to_installed_jazzy(self):
        self.write_ament_cmake_workspace()
        self.install_distro('jazzy')
        for distro in ('rolling', 'noetic', 'jazzy; echo unsafe'):
            with self.subTest(distro=distro), patch.dict(os.environ, {'ROS_DISTRO': distro}):
                result = self.detect()
                self.assertEqual(result.ros_distro, distro)
                self.assertEqual(result.recommended_commands, [])
                self.assertIn('不支持', result.warnings[0])

    def test_unsupported_single_installation_does_not_generate_commands(self):
        self.write_ament_cmake_workspace()
        self.install_distro('rolling')
        result = self.detect()
        self.assertEqual(result.ros_distro, 'rolling')
        self.assertEqual(result.recommended_commands, [])

    def test_missing_selected_setup_does_not_fall_back(self):
        self.write_ament_cmake_workspace()
        self.install_distro('humble')
        with patch.dict(os.environ, {'ROS_DISTRO': 'jazzy'}):
            for target in (None, 'jazzy'):
                with self.subTest(target=target):
                    result = self.detect(target)
                    self.assertEqual(result.ros_distro, 'jazzy')
                    self.assertEqual(result.recommended_commands, [])
                    self.assertIn('未找到', result.warnings[0])

    def test_cli_reports_explicit_target_in_json_and_text(self):
        self.write_ament_cmake_workspace()
        script = Path(self.module.__file__)
        command = [sys.executable, str(script), str(self.root), '--ros-distro', 'jazzy']
        with patch.dict(os.environ, {'ROS_DISTRO': 'humble'}):
            json_run = subprocess.run(command + ['--json'], check=True, capture_output=True, text=True)
            text_run = subprocess.run(command, check=True, capture_output=True, text=True)
        result = json.loads(json_run.stdout)
        self.assertEqual(result['workspace_type'], 'ros2-colcon')
        self.assertEqual(result['ros_distro'], 'jazzy')
        self.assertEqual(result['ros_distro_source'], 'argument')
        self.assertIn('ros_distro: jazzy', text_run.stdout)
        self.assertIn('新终端', text_run.stdout)

    def test_cli_rejects_unsupported_target(self):
        run = subprocess.run(
            [sys.executable, self.module.__file__, '--ros-distro', 'rolling'],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(run.returncode, 2)

    def test_rejects_non_ament_package(self):
        package_dir = self.root / 'src' / 'legacy_pkg'
        package_dir.mkdir(parents=True)
        (package_dir / 'package.xml').write_text(
            '<package><name>legacy_pkg</name><buildtool_depend>legacy_build</buildtool_depend></package>',
            encoding='utf-8',
        )
        result = self.detect()
        self.assertEqual(result.workspace_type, 'unsupported')
        self.assertEqual(result.unsupported_packages, 1)

    def test_handles_broken_package_xml(self):
        package_dir = self.root / 'src' / 'broken_pkg'
        package_dir.mkdir(parents=True)
        (package_dir / 'package.xml').write_text('<package><name>broken_pkg</name>', encoding='utf-8')
        result = self.detect()
        self.assertEqual(result.unknown_packages, 1)


if __name__ == '__main__':
    unittest.main()
