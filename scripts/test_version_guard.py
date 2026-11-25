#!/usr/bin/env python3
"""HiAndroid 版本格式校验、一致性门禁与改版脚本的单元测试。"""

from datetime import date
import os
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
    changelog_content: str | None = None,
    compatibility_content: str | None = None,
) -> Path:
    """在临时目录构造用于版本门禁测试的最小仓库结构。"""
    scripts_dir = root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
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
    default_changelog = (
        "# 变更日志（Changelog）\n\n"
        "## [Unreleased]\n\n"
        f"## [{gradle_version}]\n\n"
        "### 新增\n\n"
        "- 初始基线。\n"
    )
    (root / "CHANGELOG.md").write_text(
        default_changelog if changelog_content is None else changelog_content,
        encoding="utf-8",
    )
    default_compatibility = (
        "# 兼容性与迁移指南\n\n"
        "## 环境与依赖兼容矩阵\n\n"
        "- JDK 21\n"
    )
    (docs_dir / "compatibility.md").write_text(
        default_compatibility
        if compatibility_content is None
        else compatibility_content,
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

    def test_accepts_current_version_heading_with_release_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(
                Path(tmp),
                "0.0.1",
                "0.0.1",
                changelog_content=(
                    "# 变更日志（Changelog）\n\n"
                    "## [Unreleased]\n\n"
                    "## [0.0.1] - 2026-11-25\n\n"
                    "- 初始版本。\n"
                ),
            )
            self.assertEqual(
                verify_maven_local.validate_version_sync(root),
                "0.0.1",
            )

    def test_rejects_missing_changelog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(Path(tmp), "0.0.1", "0.0.1")
            (root / "CHANGELOG.md").unlink()
            with self.assertRaises(ValueError):
                verify_maven_local.validate_version_sync(root)

    def test_rejects_missing_or_malformed_unreleased_heading(self) -> None:
        invalid_changelogs = [
            "# 变更日志\n\n## [0.0.1]\n\n- 初始版本。\n",
            "# 变更日志\n\n## Unreleased\n\n## [0.0.1]\n",
            "# 变更日志\n\n### [Unreleased]\n\n## [0.0.1]\n",
            "# 变更日志\n\n## [Unreleased] 待发布\n\n## [0.0.1]\n",
        ]
        for changelog in invalid_changelogs:
            with self.subTest(changelog=changelog):
                with tempfile.TemporaryDirectory() as tmp:
                    root = write_fixture_repo(
                        Path(tmp),
                        "0.0.1",
                        "0.0.1",
                        changelog_content=changelog,
                    )
                    with self.assertRaises(ValueError):
                        verify_maven_local.validate_version_sync(root)

    def test_rejects_missing_or_malformed_current_version_heading(self) -> None:
        invalid_changelogs = [
            "# 变更日志\n\n## [Unreleased]\n\n- 尚未归档。\n",
            "# 变更日志\n\n## [Unreleased]\n\n## [0.0.2]\n",
            "# 变更日志\n\n## [Unreleased]\n\n## [0.0.1] extra\n",
            "# 变更日志\n\n## [Unreleased]\n\n## [0.0.1] - 2026/11/25\n",
        ]
        for changelog in invalid_changelogs:
            with self.subTest(changelog=changelog):
                with tempfile.TemporaryDirectory() as tmp:
                    root = write_fixture_repo(
                        Path(tmp),
                        "0.0.1",
                        "0.0.1",
                        changelog_content=changelog,
                    )
                    with self.assertRaises(ValueError):
                        verify_maven_local.validate_version_sync(root)

    def test_rejects_missing_or_empty_compatibility_doc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(Path(tmp), "0.0.1", "0.0.1")
            (root / "docs" / "compatibility.md").unlink()
            with self.assertRaises(ValueError):
                verify_maven_local.validate_version_sync(root)

        for empty_body in ("", "   \n\t\n"):
            with self.subTest(empty_body=empty_body):
                with tempfile.TemporaryDirectory() as tmp:
                    root = write_fixture_repo(
                        Path(tmp),
                        "0.0.1",
                        "0.0.1",
                        compatibility_content=empty_body,
                    )
                    with self.assertRaises(ValueError):
                        verify_maven_local.validate_version_sync(root)

    def test_verify_maven_local_cli_fails_when_governance_docs_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(Path(tmp), "0.0.1", "0.0.1")
            (root / "CHANGELOG.md").unlink()
            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "verify_maven_local.py")],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("版本校验失败", result.stderr)

    def test_ignores_headings_inside_fenced_code_blocks(self) -> None:
        changelog = (
            "# 变更日志（Changelog）\n\n"
            "## [Unreleased]\n\n"
            "### 示例说明\n\n"
            "```markdown\n"
            "## [Unreleased]\n\n"
            "## [0.0.2]\n"
            "```\n\n"
            "~~~~markdown\n"
            "## [Unreleased]\n"
            "```\n"
            "## [0.0.2]\n"
            "~~~~\n\n"
            "## [0.0.1]\n\n"
            "- 初始基线。\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(
                Path(tmp),
                "0.0.1",
                "0.0.1",
                changelog_content=changelog,
            )
            self.assertEqual(
                verify_maven_local.validate_version_sync(root),
                "0.0.1",
            )
            masked = verify_maven_local.mask_fenced_code_blocks(changelog)
            self.assertEqual(len(masked), len(changelog))
            self.assertEqual(
                [i for i, ch in enumerate(masked) if ch == "\n"],
                [i for i, ch in enumerate(changelog) if ch == "\n"],
            )

    def test_verify_maven_local_version_sync_only_cli_without_m2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as empty_home:
            root = write_fixture_repo(Path(tmp), "0.0.1", "0.0.1")
            env = {**os.environ, "HOME": empty_home}
            ok_result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "verify_maven_local.py"),
                    "--version-sync-only",
                ],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(ok_result.returncode, 0, msg=ok_result.stderr)

            (root / "docs" / "compatibility.md").unlink()
            missing_doc_result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "verify_maven_local.py"),
                    "--version-sync-only",
                ],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(missing_doc_result.returncode, 0)
            self.assertIn("版本校验失败", missing_doc_result.stderr)

        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as empty_home:
            root = write_fixture_repo(Path(tmp), "0.0.1", "0.0.2")
            env = {**os.environ, "HOME": empty_home}
            mismatch_result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "verify_maven_local.py"),
                    "--version-sync-only",
                ],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(mismatch_result.returncode, 0)
            self.assertIn("版本校验失败", mismatch_result.stderr)


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

    def test_archives_unreleased_changelog_body_on_bump(self) -> None:
        initial_changelog = (
            "# 变更日志（Changelog）\n\n"
            "记录所有公开可见版本变更。\n\n"
            "## [Unreleased]\n\n"
            "### 新增\n\n"
            "- 新增流式解析扩展能力。\n\n"
            "### 修复\n\n"
            "- 修复边界解析异常。\n\n"
            "## [0.0.1]\n\n"
            "### 新增\n\n"
            "- 初始基线。\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(
                Path(tmp),
                "0.0.1",
                "0.0.1",
                changelog_content=initial_changelog,
            )
            result = self._run_bump("0.0.2", "--root", str(root))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(
                verify_maven_local.validate_version_sync(root),
                "0.0.2",
            )
            today_str = date.today().isoformat()
            updated_changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
            expected_changelog = (
                "# 变更日志（Changelog）\n\n"
                "记录所有公开可见版本变更。\n\n"
                "## [Unreleased]\n\n"
                f"## [0.0.2] - {today_str}\n\n"
                "### 新增\n\n"
                "- 新增流式解析扩展能力。\n\n"
                "### 修复\n\n"
                "- 修复边界解析异常。\n\n"
                "## [0.0.1]\n\n"
                "### 新增\n\n"
                "- 初始基线。\n"
            )
            self.assertEqual(updated_changelog, expected_changelog)

    def test_fills_placeholder_when_unreleased_changelog_is_empty(self) -> None:
        initial_changelog = (
            "# 变更日志（Changelog）\n\n"
            "## [Unreleased]\n\n"
            "   \n"
            "## [0.0.1]\n\n"
            "### 新增\n\n"
            "- 初始基线。\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(
                Path(tmp),
                "0.0.1",
                "0.0.1",
                changelog_content=initial_changelog,
            )
            result = self._run_bump("0.0.2", "--root", str(root))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(
                verify_maven_local.validate_version_sync(root),
                "0.0.2",
            )
            today_str = date.today().isoformat()
            updated_changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
            expected_changelog = (
                "# 变更日志（Changelog）\n\n"
                "## [Unreleased]\n\n"
                f"## [0.0.2] - {today_str}\n\n"
                "- 版本号对齐（无行为变更）。\n\n"
                "## [0.0.1]\n\n"
                "### 新增\n\n"
                "- 初始基线。\n"
            )
            self.assertEqual(updated_changelog, expected_changelog)

    def test_bump_keeps_all_files_unchanged_when_validation_fails(self) -> None:
        broken_changelog = (
            "# 变更日志（Changelog）\n\n"
            "## [Unreleased]\n\n"
            "## [Unreleased]\n\n"
            "## [0.0.1]\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(
                Path(tmp),
                "0.0.1",
                "0.0.1",
                changelog_content=broken_changelog,
            )
            gradle_before = (root / "build.gradle.kts").read_text(encoding="utf-8")
            verify_before = (root / "scripts" / "verify_maven_local.py").read_text(
                encoding="utf-8"
            )
            result = self._run_bump("0.0.2", "--root", str(root))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(
                (root / "build.gradle.kts").read_text(encoding="utf-8"),
                gradle_before,
            )
            self.assertEqual(
                (root / "scripts" / "verify_maven_local.py").read_text(
                    encoding="utf-8"
                ),
                verify_before,
            )
            self.assertEqual(
                (root / "CHANGELOG.md").read_text(encoding="utf-8"),
                broken_changelog,
            )

    def test_bump_preserves_fenced_code_blocks_containing_headings(self) -> None:
        initial_changelog = (
            "# 变更日志（Changelog）\n\n"
            "## [Unreleased]\n\n"
            "### 新增\n\n"
            "- 新增围栏代码块示例：\n\n"
            "```markdown\n"
            "## [Unreleased]\n\n"
            "## [0.0.2]\n"
            "```\n\n"
            "## [0.0.1]\n\n"
            "### 示例归档\n\n"
            "~~~markdown\n"
            "## [0.0.2]\n"
            "~~~\n\n"
            "- 初始基线。\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = write_fixture_repo(
                Path(tmp),
                "0.0.1",
                "0.0.1",
                changelog_content=initial_changelog,
            )
            result = self._run_bump("0.0.2", "--root", str(root))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(
                verify_maven_local.validate_version_sync(root),
                "0.0.2",
            )
            today_str = date.today().isoformat()
            updated_changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
            expected_changelog = (
                "# 变更日志（Changelog）\n\n"
                "## [Unreleased]\n\n"
                f"## [0.0.2] - {today_str}\n\n"
                "### 新增\n\n"
                "- 新增围栏代码块示例：\n\n"
                "```markdown\n"
                "## [Unreleased]\n\n"
                "## [0.0.2]\n"
                "```\n\n"
                "## [0.0.1]\n\n"
                "### 示例归档\n\n"
                "~~~markdown\n"
                "## [0.0.2]\n"
                "~~~\n\n"
                "- 初始基线。\n"
            )
            self.assertEqual(updated_changelog, expected_changelog)


if __name__ == "__main__":
    unittest.main()
