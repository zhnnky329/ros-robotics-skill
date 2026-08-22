import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


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
        script_path = Path(__file__).resolve().parents[1] / 'scripts' / 'detect_ros_workspace.py'
        self.module = load_module(script_path, 'detect_ros_workspace')

    def tearDown(self):
        self.temp_dir.cleanup()

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
        result = self.module.detect_workspace(self.root)
        self.assertEqual(result.workspace_type, 'ros2-colcon')
        self.assertEqual(result.ros2_packages, 1)
        self.assertEqual(result.packages[0].build_type, 'ament_cmake')
        self.assertIn('/opt/ros/humble/setup.bash', result.recommended_commands[0])

    def test_rejects_non_ament_package(self):
        package_dir = self.root / 'src' / 'legacy_pkg'
        package_dir.mkdir(parents=True)
        (package_dir / 'package.xml').write_text(
            '<package><name>legacy_pkg</name><buildtool_depend>legacy_build</buildtool_depend></package>',
            encoding='utf-8',
        )
        result = self.module.detect_workspace(self.root)
        self.assertEqual(result.workspace_type, 'unsupported')
        self.assertEqual(result.unsupported_packages, 1)

    def test_handles_broken_package_xml(self):
        package_dir = self.root / 'src' / 'broken_pkg'
        package_dir.mkdir(parents=True)
        (package_dir / 'package.xml').write_text('<package><name>broken_pkg</name>', encoding='utf-8')
        result = self.module.detect_workspace(self.root)
        self.assertEqual(result.unknown_packages, 1)


if __name__ == '__main__':
    unittest.main()
