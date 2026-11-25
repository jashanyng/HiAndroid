# HiAndroid 兼容性与迁移指南

本文档规定 HiAndroid 效率库的构建与运行环境基线、三阶段演进与裸 `x.y.z` 版本兼容契约，以及消费项目的开发期跟进、正式版切换与跨版本迁移规范。

## 环境与依赖兼容矩阵

### 构建工具与平台基线

| 维度 | 基线要求 | 说明 |
| --- | --- | --- |
| **JDK** | JDK 21 | Gradle Daemon 运行及本地构建环境要求 |
| **Gradle** | `9.5.0` | 由仓库 `gradle/wrapper/gradle-wrapper.properties` 锁定 |
| **Android Gradle Plugin (AGP)** | `9.3.1` | 与 `gradle/libs.versions.toml` 保持一致 |
| **Kotlin** | `2.4.10` | 消费项目需使用 `2.4.10` 或兼容 `2.4` 的编译器 |
| **Android SDK (`compileSdk`)** | `37` | 所有 Android Library 模块统一编译目标 |
| **最低支持系统 (`minSdk`)** | `30`（Android 11） | 所有 Android Library 模块统一最低系统版本 |
| **JVM 字节码目标** | Java `11` / Kotlin `JvmTarget.JVM_11` | 所有纯 JVM 与 Android Library 模块均统一为 `11` |

### 模块运行边界与可选依赖

- **纯 JVM 模块（JAR）**：`:base`、`:nav`、`:net`、`:net:retrofit`、`:store`、`:github:model:core`、`:github:trending` 不引入 Android 框架或 Compose UI 依赖；在同级源码 Composite Build 接入下额外暴露 `androidJvm` 兼容变体，以供 Android 模块直接依赖。
- **Android Library 模块（AAR）**：`:core` 不依赖 Compose；`:suite` 与 `:nav:compose` 等 UI 模块依赖 Jetpack Compose BOM；可选适配器（`:suite:coil`、`:suite:media3`、`:suite:log-timber` 及各厂商 SDK 模块）独立分发，避免强加传递依赖。
- **便捷聚合入口（`:hiandroid`）**：仅聚合 `:base`、`:core`、`:nav`、`:nav:compose`、`:net`、`:net:retrofit`、`:store`、`:store:datastore`、`:store:keystore` 与 `:suite`，不包含厂商 SDK 与 Coil/Media3/Timber 可选模块，也不会自动初始化任何厂商 SDK。

### 核心外部依赖锁定版本

以下版本精确锁定于 [`gradle/libs.versions.toml`](../gradle/libs.versions.toml)（不使用动态版本范围）：

| 依赖组 / 工件 | 锁定版本 | 主要使用范围 |
| --- | --- | --- |
| `androidx.core:core-ktx` | `1.19.1` | `:core`、`:suite` 等 Android 模块 |
| `androidx.compose:compose-bom` | `2026.09.00` | `:suite` 及 Compose 相关模块 |
| `androidx.activity:activity-compose` | `1.13.0` | `:suite` |
| `androidx.navigation:navigation-compose` | `2.10.2` | `:nav:compose` |
| `androidx.lifecycle:lifecycle-runtime-compose` | `2.11.0` | `:suite` |
| `androidx.datastore:datastore-preferences` | `1.3.0` | `:store:datastore` |
| `androidx.media3:*` | `1.11.1` | `:suite:media3` |
| `io.coil-kt.coil3:*` | `3.6.3` | `:suite:coil` |
| `org.jetbrains.kotlinx:kotlinx-coroutines-*` | `1.11.0` | 协程异步契约与测试 |
| `com.squareup.retrofit2:*` | `3.0.0` | `:net:retrofit` |
| `com.squareup.okhttp3:*` | `5.5.1` | `:net:retrofit` |
| `com.squareup.moshi:*` | `1.15.2` | `:net:retrofit` |
| `com.jakewharton.timber:timber` | `5.0.1` | `:suite:log-timber` |
| `org.jsoup:jsoup` | `1.24.1` | `:github:trending` |
| `com.umeng.umsdk:*`（common / asms / uyumao / apm / share / link） | `9.9.6` / `1.8.7.2` / `1.1.4` / `2.1.0` / `7.3.7` / `2.0.0` | `:suite:umeng-core` 及各可选友盟适配器 |
| `com.tencent.mm.opensdk:wechat-sdk-android` | `6.8.24` | `:suite:socialsharing-umeng-wechat`（仅同级源码接入） |
| `com.aliyun.ams:alicloud-apm` | `2.9.0` | `:suite:aliyun-emas-core` |

## 演进阶段与版本兼容契约

### 裸 `x.y.z` 格式约定

HiAndroid 的所有版本号定义、消费端版本锁及 Git 标签一律采用**无 `v` 前缀的三段非负整数裸 `x.y.z` 格式**（如 `0.0.1`、`1.0.0`），严禁使用 `v` 前缀（如 `v0.0.1`）或 `-alpha` / `-SNAPSHOT` 等预发布后缀。全部 22 个公开模块使用同一版本号协同发布。

### 当前 `0.0.1` 制作期与三阶段演进契约

HiAndroid 按成熟度划分为三个演进阶段，当前处于**制作期**（基线 `0.0.1`）：

1. **制作期（当前阶段，`0.0.1` 起步）**：
   - 允许为完成模块化定型调整顶层家族、子模块划分与组织结构；
   - **不保留**代码与公开 API 的向后兼容层、废弃别名或迁移垫片；
   - 日常源码演进仅递增 `z`，不预先创建 Git 标签，也不向 Maven Central 等外部制品源公开发布；开发期消费项目随库变更同批更新。
2. **改进完善期**：
   - 顶层家族与公开模块结构严格冻结（除非获维护者显式批准）；
   - 在既有结构边界内打磨与扩充接口仍无需保留代码向后兼容。
3. **维护期**：
   - 模块组织结构严格冻结；
   - 公开 API 与二进制契约严格保持向后兼容，日常仅进行平台适配、安全升级与缺陷修复；
   - 新增功能须先出具包含复用广度、契约契合度、兼容性与维护成本的评估报告，并获维护者明确同意后方可实施。

阶段切换权完全归属维护者显式决定。智能体在版本调整时仅允许递增 `z`；任何对 `x` 或 `y` 的修改（包括切入 `1.0.0`）必须经维护者同意并在 `scripts/bump_version.py` 中显式传入 `--allow-xy-bump`。

### `1.0.0` 首发及后续 `x` / `y` / `z` 批次与热修语义

- **首次正式发布（`1.0.0`）**：当 HiAndroid 首次正式对外发布至 Maven Central，或首个消费项目进入提审/上架阶段并需锁定正式制品时，版本号定为 `1.0.0` 并创建裸标签 `1.0.0`。已正式发布的版本与标签不可覆盖。
- **`x`（重大代际）**：仅在发生重大架构、模块组织结构或品牌代际跨越时由维护者决定递增。
- **`y`（项目周期批次）**：与消费项目的开发批次协同演进——当同批次中的某个消费项目进入提审上架并锁定已发布版本 `x.y.z` 时，其余仍处于同级源码开发期的消费项目立即切入 `x.(y+1).0` 继续演进。
- **`z`（批次内迭代与紧急热修）**：在同一 `x.y` 批次内代表功能扩充与缺陷修复递增；对于已经正式发布并由线上项目锁定的 `x.y.*` 批次，递增 `z` 仅用于独立的紧急热修通道。

## 升级与迁移指南

### 开发期跟进（同级源码 Composite Build + 40 位 SHA 锁）

开发期消费项目应将 HiAndroid 检出在消费仓库同级目录 `../HiAndroid`，通过根 `settings.gradle.kts` 的 `includeBuild("../HiAndroid")` 将声明的 `com.jashanyng:*` 坐标替换为本地源码工程，并在消费仓库提交包含**40 位完整 Git commit SHA** 的版本锁文件（完整门禁见 [`docs/engineering/sibling-source-dependency.md`](engineering/sibling-source-dependency.md)）。

跟进上游更新步骤：

1. 在 HiAndroid 更新目标提交前，先阅读 [`CHANGELOG.md`](../CHANGELOG.md) 中 `## [Unreleased]` 及新增版本章节，核对模块变更与接口调整；
2. 确认目标提交已推送至可信远端跟踪分支且 HiAndroid 工作区无未提交/未跟踪改动；
3. 更新消费项目版本锁文件至新的 40 位完整 commit SHA；
4. 若消费模块调整了依赖坐标或接口调用，同步修改消费端代码后分别运行 HiAndroid 校验与消费项目根验证门禁，确认通过后再提交消费仓库版本锁。

### 切换至 `1.0.0` 正式 Maven 制品指南

当消费项目进入对外发布、提审或上架阶段时，必须退出同级源码依赖并切换为已发布的固定 Maven 版本：

1. 在消费项目根 `settings.gradle.kts` 中移除 `includeBuild("../HiAndroid")` 及其 `dependencySubstitution` 覆盖配置；
2. 在消费项目依赖管理（如 `gradle/libs.versions.toml`）中移除同级源码版本锁，改在 `repositories` 中启用正式 Maven 仓库（如 `mavenCentral()` 与 `google()`），并将所有 `com.jashanyng:*` 依赖锁定为精确的裸 `x.y.z` 版本（首次正式发布为 `1.0.0`，严禁使用动态版本或 `-SNAPSHOT`）；
3. 多模块消费项目应按各模块编译边界声明最小所需子坐标（例如仅需纯 Kotlin 契约时引用 `com.jashanyng:base:1.0.0`，而非整体引入 `com.jashanyng:hiandroid:1.0.0`）；
4. 运行消费项目的发布构建与校验门禁，确保在仍存在同级源码依赖时发布入口会直接以非零退出码阻断。

### 跨版本破坏性变更记录区

> 当前仓库处于 `0.0.1` 制作期初始基线，尚无已发布版本间的破坏性变更迁移记录。自下一个版本及 `1.0.0` 正式版起，所有涉及公开 API 签名、包名/模块坐标变更、最小运行环境提升或行为不兼容调整的改动，均须按版本号倒序登记于下表：

| 版本过渡 | 影响模块 / 坐标 | 破坏性变更摘要 | 消费端迁移操作 |
| --- | --- | --- | --- |
| `0.0.1`（初始基线） | 全部 22 个公开模块 | 制作期初始公开基线建立 | 按同级源码 Composite Build 接入并锁定 40 位 SHA |
