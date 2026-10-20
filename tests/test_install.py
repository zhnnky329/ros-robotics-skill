import importlib.util
import json
import subprocess
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


class InstallTests(unittest.TestCase):
    def setUp(self):
        script_path = Path(__file__).resolve().parents[1] / 'scripts' / 'install.py'
        self.module = load_module(script_path, 'install_script')

    def test_codex_path_resolution(self):
        home = Path('/tmp/home')
        path = self.module.codex_skill_dir(home, None)
        self.assertEqual(path.parts[-4:], ('tmp', 'home', '.codex', 'skills', 'ros-robotics')[-4:])
        self.assertEqual(path.name, 'ros-robotics')

    def test_detect_default_targets_falls_back_to_codex(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.assertEqual(self.module.detect_default_targets(home), ['codex'])

    def test_detects_codex_and_claude(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.codex').mkdir()
            (home / '.claude').mkdir()
            self.assertEqual(self.module.detect_default_targets(home), ['codex', 'claude'])

    def test_installed_detector_keeps_jazzy_cli(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / 'ros-robotics'
            self.module.install_skill_tree(source, destination, force=False)
            run = subprocess.run(
                [sys.executable, str(destination / 'scripts' / 'detect_ros_workspace.py'),
                 str(source / 'examples' / 'minimal_ws'), '--ros-distro', 'jazzy', '--json'],
                check=True, capture_output=True, text=True,
            )
            result = json.loads(run.stdout)
            self.assertEqual(result['ros_distro'], 'jazzy')
            self.assertEqual(result['workspace_type'], 'ros2-colcon')
            self.assertTrue((destination / 'references' / 'ros2-colcon.md').is_file())


if __name__ == '__main__':
    unittest.main()
