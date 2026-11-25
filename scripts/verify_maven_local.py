#!/usr/bin/env python3
"""校验 HiAndroid 发布到 Maven Local 的构件和内部依赖。"""

from pathlib import Path
import re
import sys
from xml.etree import ElementTree

GROUP_ID = "com.jashanyng"
VERSION = "0.0.1"
REPOSITORY = Path.home() / ".m2/repository/com/jashanyng"
REPO_ROOT = Path(__file__).resolve().parent.parent

BARE_VERSION_PATTERN = re.compile(r"\A[0-9]+\.[0-9]+\.[0-9]+\Z")
GRADLE_VERSION_PATTERN = re.compile(
    r'^(?P<prefix>\s*val\s+hiAndroidVersion\s*=\s*")(?P<version>[^"\r\n]+)(?P<suffix>"\s*)$',
    re.MULTILINE,
)
VERIFY_VERSION_PATTERN = re.compile(
    r'^(?P<prefix>\s*VERSION\s*=\s*")(?P<version>[^"\r\n]+)(?P<suffix>"\s*)$',
    re.MULTILINE,
)

MODULES = {
    "base": ("jar", set()),
    "core": ("aar", {("base", "compile")}),
    "store": ("jar", {("base", "compile")}),
    "store-datastore": ("aar", {("store", "compile")}),
    "store-keystore": ("aar", {("store", "compile")}),
    "nav": ("jar", {("base", "compile")}),
    "net": ("jar", {("base", "compile")}),
    "net-retrofit": (
        "jar",
        {
            ("base", "compile"),
            ("net", "compile"),
        },
    ),
    "suite": (
        "aar",
        {
            ("base", "compile"),
            ("core", "runtime"),
        },
    ),
    "suite-coil": ("aar", {("suite", "compile"), ("store", "compile")}),
    "suite-media3": ("aar", {("suite", "compile")}),
    "suite-log-timber": ("aar", {("base", "compile")}),
    "suite-aliyun-emas-core": (
        "aar",
        {("base", "compile")},
    ),
    "suite-umeng-core": (
        "aar",
        {("base", "compile")},
    ),
    "suite-analytics-umeng": (
        "aar",
        {
            ("base", "compile"),
            ("suite-umeng-core", "compile"),
        },
    ),
    "suite-performance-umeng": (
        "aar",
        {
            ("base", "compile"),
            ("suite-umeng-core", "compile"),
        },
    ),
    "nav-compose": (
        "aar",
        {("nav", "compile")},
    ),
    "nav-umeng-ulink": (
        "aar",
        {
            ("base", "compile"),
            ("suite-umeng-core", "compile"),
        },
    ),
    "suite-socialsharing-umeng": (
        "aar",
        {
            ("base", "compile"),
            ("suite-umeng-core", "compile"),
        },
    ),
    "hiandroid": (
        "aar",
        {
            ("base", "compile"),
            ("core", "compile"),
            ("nav", "compile"),
            ("nav-compose", "compile"),
            ("net", "compile"),
            ("net-retrofit", "compile"),
            ("store", "compile"),
            ("store-datastore", "compile"),
            ("store-keystore", "compile"),
            ("suite", "compile"),
        },
    ),
    "github-model-core": ("jar", set()),
    "github-trending": (
        "jar",
        {("github-model-core", "compile")},
    ),
}


def validate_bare_version(version):
    """校验版本字符串为无 v 前缀、无预发布后缀的裸 x.y.z，并返回整数三元组。"""
    if not isinstance(version, str) or not BARE_VERSION_PATTERN.fullmatch(version):
        raise ValueError(
            f"版本号必须为无 v 前缀、无预发布后缀的裸 x.y.z 格式，实际为：{version!r}"
        )
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def _extract_single_version(content, pattern, source_label):
    matches = list(pattern.finditer(content))
    if len(matches) != 1:
        raise ValueError(
            f"{source_label} 中必须恰好包含一处版本号定义，实际匹配 {len(matches)} 处"
        )
    return matches[0].group("version")


def read_gradle_version(build_gradle_path):
    """读取 build.gradle.kts 中的 hiAndroidVersion。"""
    content = build_gradle_path.read_text(encoding="utf-8")
    return _extract_single_version(
        content,
        GRADLE_VERSION_PATTERN,
        str(build_gradle_path),
    )


def read_verify_script_version(verify_script_path):
    """读取 verify_maven_local.py 中的 VERSION。"""
    content = verify_script_path.read_text(encoding="utf-8")
    return _extract_single_version(
        content,
        VERIFY_VERSION_PATTERN,
        str(verify_script_path),
    )


def validate_version_sync(repo_root=REPO_ROOT):
    """校验 build.gradle.kts 与 scripts/verify_maven_local.py 的版本均为裸格式且一致。"""
    root = Path(repo_root)
    gradle_version = read_gradle_version(root / "build.gradle.kts")
    verify_version = read_verify_script_version(
        root / "scripts" / "verify_maven_local.py"
    )
    validate_bare_version(gradle_version)
    validate_bare_version(verify_version)
    if gradle_version != verify_version:
        raise ValueError(
            f"版本不一致：build.gradle.kts 为 {gradle_version!r}，"
            f"scripts/verify_maven_local.py 为 {verify_version!r}"
        )
    return gradle_version


def local_name(element):
    """移除 Maven POM XML 元素的命名空间。"""
    return element.tag.rsplit("}", 1)[-1]


def child_text(parent, name):
    """读取指定直接子元素的文本。"""
    for child in parent:
        if local_name(child) == name:
            return child.text
    return None


def verify_module(artifact_id, main_extension, expected_dependencies):
    """校验单个模块的文件、坐标和内部依赖。"""
    artifact_directory = REPOSITORY / artifact_id / VERSION

    required_files = (
        f"{artifact_id}-{VERSION}.{main_extension}",
        f"{artifact_id}-{VERSION}-sources.jar",
        f"{artifact_id}-{VERSION}-javadoc.jar",
        f"{artifact_id}-{VERSION}.pom",
        f"{artifact_id}-{VERSION}.module",
    )

    missing_files = [
        filename
        for filename in required_files
        if not (artifact_directory / filename).is_file()
    ]

    if missing_files:
        raise RuntimeError(
            f"{artifact_id} 缺少发布文件：{missing_files}"
        )

    pom_path = artifact_directory / f"{artifact_id}-{VERSION}.pom"
    pom_root = ElementTree.parse(pom_path).getroot()

    actual_coordinate = (
        child_text(pom_root, "groupId"),
        child_text(pom_root, "artifactId"),
        child_text(pom_root, "version"),
    )
    expected_coordinate = (GROUP_ID, artifact_id, VERSION)

    if actual_coordinate != expected_coordinate:
        raise RuntimeError(
            f"{artifact_id} 坐标错误："
            f"实际 {actual_coordinate}，"
            f"预期 {expected_coordinate}"
        )

    actual_dependencies = set()

    for dependency in pom_root.iter():
        if local_name(dependency) != "dependency":
            continue

        if child_text(dependency, "groupId") != GROUP_ID:
            continue

        dependency_artifact = child_text(
            dependency,
            "artifactId",
        )
        dependency_version = child_text(
            dependency,
            "version",
        )
        dependency_scope = child_text(
            dependency,
            "scope",
        )

        if dependency_version != VERSION:
            raise RuntimeError(
                f"{artifact_id} 的内部依赖版本错误："
                f"{dependency_artifact}:{dependency_version}"
            )

        actual_dependencies.add(
            (dependency_artifact, dependency_scope)
        )

    if actual_dependencies != expected_dependencies:
        raise RuntimeError(
            f"{artifact_id} 内部依赖错误："
            f"实际 {sorted(actual_dependencies)}，"
            f"预期 {sorted(expected_dependencies)}"
        )

    print(
        f"{GROUP_ID}:{artifact_id}:{VERSION} "
        f"-> {main_extension} + sources + javadoc + pom + module"
    )


def main():
    """校验版本门禁及全部 Maven Local 发布模块。"""
    try:
        validated_version = validate_version_sync(REPO_ROOT)
        validate_bare_version(VERSION)
        if validated_version != VERSION:
            raise ValueError(
                f"运行时 VERSION={VERSION!r} 与文件校验结果 {validated_version!r} 不一致"
            )
    except ValueError as error:
        print(f"版本校验失败：{error}", file=sys.stderr)
        sys.exit(1)

    for artifact_id, configuration in MODULES.items():
        main_extension, expected_dependencies = configuration
        verify_module(
            artifact_id,
            main_extension,
            expected_dependencies,
        )

    print(f"{len(MODULES)} 个 Maven Local 构件及内部依赖全部校验通过")


if __name__ == "__main__":
    main()
