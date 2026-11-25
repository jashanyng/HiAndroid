#!/usr/bin/env python3
"""HiAndroid 版本格式校验、一致性门禁与改版脚本的单元测试。"""

from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import verify_maven_local  # noqa: E402


def write_fixture_repo(
    root: Path,
    gradle_version: str,
    verify_version: str,
) -> Path:
    """在临时目录构造用于版本门禁测试的最小仓库结构。"""
    scripts_dir = root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (root / "build.gradle.kts").write_text(
        f'val hiAndroidGroupId = "com.jashanyng"\n'
        f'val hiAndroidVersion = "{gradle_version}"\n',
        encoding="utf-8",
    )
    verify_source = (SCRIPTS_DIR / "verify_maven_local.py").read_text(
        encoding="utf-8",
    )
    patched_verify = re.sub(
        r'^VERSION = "[^"]+"',
        f'VERSION = "{verify_version}"',
        verify_source,
        count=1,
        flags=re.MULTILINE,
    )
    (scripts_dir / "verify_maven_local.py").write_text(
        patched_verify,
        encoding="utf-8",
    )
    return root


class BareVersionValidationTest(unittest.TestCase):
    """校验裸 x.y.z 版本字符串格式约束。"""

    def test_accepts_bare_three_part_numeric_versions(self) -> None:
        self.assertEqual(
            verify_maven_local.validate_bare_version("0.0.1"),
            (0, 0, 1),
        )
        self.assertEqual(
            verify_maven_local.validate_bare_version("1.23.45"),
            (1, 23, 45),
        )

    def test_rejects_v_prefix_prerelease_and_malformed_versions(self) -> None:
        invalid_versions = [
            "v0.0.1",
            "V1.0.0",
            "0.0.1-alpha.1",
            "0.0.1-SNAPSHOT",
            "1.0.0+build.1",
            "0.1",
            "1",
            "0.0.1\n",
            "",
            "abc",
        ]
        for version in invalid_versions:
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    verify_maven_local.validate_bare_version(version)


class VersionSyncCheckTest(unittest.TestCase):
    """校验 build.gradle.kts 与 verify_maven_local.py 的版本一致性与入口门禁。"""

    def test_passes_when_versions_match_and_are_bare(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(Path(tmp), "0.0.1", "0.0.1")
            self.assertEqual(
                verify_maven_local.validate_version_sync(root),
                "0.0.1",
            )

    def test_rejects_mismatch_between_gradle_and_verify_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(Path(tmp), "0.0.1", "0.0.2")
            with self.assertRaises(ValueError):
                verify_maven_local.validate_version_sync(root)

    def test_rejects_non_bare_version_in_gradle_or_verify_script(self) -> None:
        for gradle_ver, verify_ver in [
            ("v0.0.1", "v0.0.1"),
            ("0.0.1-SNAPSHOT", "0.0.1-SNAPSHOT"),
        ]:
            with self.subTest(gradle_ver=gradle_ver, verify_ver=verify_ver):
                with tempfile.TemporaryDirectory() as tmp:
                    root = write_fixture_repo(Path(tmp), gradle_ver, verify_ver)
                    with self.assertRaises(ValueError):
                        verify_maven_local.validate_version_sync(root)

    def test_verify_maven_local_cli_fails_immediately_on_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(Path(tmp), "0.0.1", "0.0.2")
            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "verify_maven_local.py")],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("版本校验失败", result.stderr)
            self.assertIn("版本不一致", result.stderr)

    def test_current_repository_versions_are_in_sync(self) -> None:
        version = verify_maven_local.validate_version_sync(REPO_ROOT)
        verify_maven_local.validate_bare_version(version)


class BumpVersionCliTest(unittest.TestCase):
    """通过 CLI 公共边界校验 bump_version.py 的改版门禁与同步更新行为。"""

    def _run_bump(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "bump_version.py"), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_bumps_z_version_without_allow_xy_bump_and_syncs_both_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(Path(tmp), "0.0.1", "0.0.1")
            result = self._run_bump("0.0.2", "--root", str(root))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(
                verify_maven_local.validate_version_sync(root),
                "0.0.2",
            )
            self.assertIn(
                'val hiAndroidVersion = "0.0.2"',
                (root / "build.gradle.kts").read_text(encoding="utf-8"),
            )
            self.assertIn(
                'VERSION = "0.0.2"',
                (root / "scripts" / "verify_maven_local.py").read_text(
                    encoding="utf-8"
                ),
            )

    def test_rejects_non_bare_target_version(self) -> None:
        for invalid in ("v0.0.2", "0.0.2-alpha.1", "0.2"):
            with self.subTest(invalid=invalid):
                with tempfile.TemporaryDirectory() as tmp:
                    root = write_fixture_repo(Path(tmp), "0.0.1", "0.0.1")
                    result = self._run_bump(invalid, "--root", str(root))
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(
                        verify_maven_local.validate_version_sync(root),
                        "0.0.1",
                    )

    def test_rejects_equal_or_older_target_version(self) -> None:
        for current, target in [
            ("0.0.1", "0.0.1"),
            ("0.0.2", "0.0.1"),
            ("1.0.0", "0.9.9"),
        ]:
            with self.subTest(current=current, target=target):
                with tempfile.TemporaryDirectory() as tmp:
                    root = write_fixture_repo(Path(tmp), current, current)
                    result = self._run_bump(
                        target,
                        "--root",
                        str(root),
                        "--allow-xy-bump",
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(
                        verify_maven_local.validate_version_sync(root),
                        current,
                    )

    def test_rejects_x_or_y_bump_without_allow_xy_bump_flag(self) -> None:
        for target in ("0.1.0", "1.0.0"):
            with self.subTest(target=target):
                with tempfile.TemporaryDirectory() as tmp:
                    root = write_fixture_repo(Path(tmp), "0.0.1", "0.0.1")
                    result = self._run_bump(target, "--root", str(root))
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(
                        verify_maven_local.validate_version_sync(root),
                        "0.0.1",
                    )

    def test_allows_x_or_y_bump_when_flag_is_passed(self) -> None:
        for current, target in [("0.0.1", "0.1.0"), ("0.1.2", "1.0.0")]:
            with self.subTest(current=current, target=target):
                with tempfile.TemporaryDirectory() as tmp:
                    root = write_fixture_repo(Path(tmp), current, current)
                    result = self._run_bump(
                        target,
                        "--root",
                        str(root),
                        "--allow-xy-bump",
                    )
                    self.assertEqual(result.returncode, 0, msg=result.stderr)
                    self.assertEqual(
                        verify_maven_local.validate_version_sync(root),
                        target,
                    )

    def test_rejects_when_existing_repo_versions_are_out_of_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(Path(tmp), "0.0.1", "0.0.2")
            result = self._run_bump("0.0.3", "--root", str(root))
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
