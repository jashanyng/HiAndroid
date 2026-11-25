#!/usr/bin/env python3
"""校验并同步更新 HiAndroid 的裸 x.y.z 版本号。"""

import argparse
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from verify_maven_local import (  # noqa: E402
    GRADLE_VERSION_PATTERN,
    VERIFY_VERSION_PATTERN,
    validate_bare_version,
    validate_version_sync,
)


def _render_updated_version(path, pattern, new_version):
    """在内存中替换单处版本号定义并校验恰好匹配一次。"""
    content = path.read_text(encoding="utf-8")
    updated, count = pattern.subn(
        rf"\g<prefix>{new_version}\g<suffix>",
        content,
    )
    if count != 1:
        raise ValueError(
            f"{path} 中必须恰好包含一处版本号定义，实际匹配 {count} 处"
        )
    return updated


def bump_version(target_version, root=REPO_ROOT, allow_xy_bump=False):
    """校验目标版本并同步更新 build.gradle.kts 与 verify_maven_local.py。"""
    repo_root = Path(root)
    target_tuple = validate_bare_version(target_version)
    current_version = validate_version_sync(repo_root)
    current_tuple = validate_bare_version(current_version)

    if target_tuple <= current_tuple:
        raise ValueError(
            f"目标版本 {target_version} 必须严格大于当前版本 {current_version}"
        )

    if target_tuple[:2] != current_tuple[:2] and not allow_xy_bump:
        raise ValueError(
            f"默认仅允许保持 x.y 不变并递增 z（当前 {current_version} -> 目标 {target_version}）；"
            "修改 x 或 y 须获维护者明确同意并传入 --allow-xy-bump"
        )

    gradle_path = repo_root / "build.gradle.kts"
    verify_script_path = repo_root / "scripts" / "verify_maven_local.py"
    gradle_updated = _render_updated_version(
        gradle_path,
        GRADLE_VERSION_PATTERN,
        target_version,
    )
    verify_updated = _render_updated_version(
        verify_script_path,
        VERIFY_VERSION_PATTERN,
        target_version,
    )

    gradle_path.write_text(gradle_updated, encoding="utf-8")
    verify_script_path.write_text(verify_updated, encoding="utf-8")
    return current_version, target_version


def parse_args(argv=None):
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="校验并同步更新 HiAndroid 的裸 x.y.z 版本号。",
    )
    parser.add_argument(
        "version",
        help="目标裸 x.y.z 版本号（如 0.0.2）。",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="HiAndroid 仓库根目录（默认为脚本上级目录）。",
    )
    parser.add_argument(
        "--allow-xy-bump",
        action="store_true",
        help="允许修改主版本 x 或批次版本 y（须经维护者明确同意）。",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """脚本主入口。"""
    args = parse_args(argv)
    try:
        previous_version, next_version = bump_version(
            args.version,
            root=args.root,
            allow_xy_bump=args.allow_xy_bump,
        )
    except (FileNotFoundError, ValueError) as error:
        print(f"版本更新被拒绝：{error}", file=sys.stderr)
        return 1

    print(f"已同步更新 HiAndroid 版本号：{previous_version} -> {next_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
