# HiAndroid 智能体协作说明

HiAndroid（专名“HiAndroid 效率库”，规则与文档叙述使用该专名，仓库名、坐标与代码标识符保持原样）是与 AtlasHub 业务无关、可独立发布的 Kotlin/Android 效率库。公开接口应保持足够小，具体网络、持久化、导航及 SDK 实现通过单向依赖的适配模块接入。

## 模块归属

- 顶级家族只允许 `:base`、`:core`、`:nav`、`:net`、`:store`、`:suite` 和可选聚合入口 `:hiandroid`；GitHub Trending 等确有独立用途的库可作为独立家族。
- `:base` 只含无 Android/UI 依赖的 Kotlin 模型和日志、统计、社会化分享等契约。
- `:core` 放轻量 Android 平台工具；`:nav`、`:net`、`:store` 定义各自的契约，具体实现优先放在本家族的子模块。
- `:store` 涵盖数据库、偏好、凭据和其他持久化的通用契约；消费项目拥有自己的表结构、业务键和用户数据隔离策略。
- `:suite` 放通用视图；Coil、Media3、Timber 与厂商 SDK 分别放可选的 `:suite:*` 子模块。用户可直接选择子模块，`:hiandroid` 只聚合通用默认模块，不自动初始化厂商 SDK。
- 修改 `:suite` 的公共组件、文案或默认视觉时，读取 [`docs/engineering/ui-components.md`](docs/engineering/ui-components.md)。
- 社会化分享的项目模块、包和公开类型使用 `socialsharing` / `SocialSharing`；平台原生 API、外部产品名及既有持久化标识按其原语义保留。
- 子模块依赖必须单向且无环。根 `settings.gradle.kts` 与发布白名单是模块路径和 Maven 坐标的事实源；公开坐标与 Gradle project path 可以不同。

## 演进阶段与版本治理

- **当前阶段与基线**：当前处于**制作期**，未发布版本基线为无 `v` 前缀裸格式 `0.0.1`（日常提交不打标签、不发 Maven Central，全部公开模块统一版本）。
- **版本更新门禁**：版本号调整统一执行 `python3 scripts/bump_version.py <x.y.z>`；智能体仅允许递增 `z`，切换演进阶段或修改 `x`/`y`（以及打正式标签或发布 Maven Central）须获维护者明确同意并显式传入 `--allow-xy-bump`。
- **完整规则指针**：调整家族或子模块结构、跨项目沉淀通用能力、评估维护期新增功能或切换版本批次前，先读取 [`../tech-specs/common/adoption.md#4-效率库准入规则与两阶段门禁`](../tech-specs/common/adoption.md#4-效率库准入规则与两阶段门禁)（本机无同级目录时回退读取 GitHub `jashanyng/tech-specs` 同路径；与消费项目两阶段依赖门禁正交）。

## 发布与验证

- 新纳入通用模块的主流第三方库在实施时核对最新稳定版并精确锁定，不使用动态版本；厂商 SDK 按其独立接入约束核验。遇到 Kotlin、AGP、`minSdk` 或消费者不兼容时先解决冲突，不静默降级。
- 已发布版本号不可覆盖，改动发布新版本号。
- 日志契约只提供与渠道、环境无关的机制。是否接收凭据与原始正文由宿主通过 `LogProvider.supportsSensitiveData` 等参数显式声明并自负其责，默认不接收；本库不内置渠道、环境或加密策略。
- 修改模块或依赖后运行 `./gradlew check`、`./gradlew publishToMavenLocal` 和 `python3 scripts/verify_maven_local.py`，并从独立 Gradle 消费工程核对 POM、Module Metadata 与传递依赖。
- `:hiandroid` 是可选入口，多模块消费项目仍按各自编译边界选择最小子库。厂商 SDK 由宿主在隐私授权后显式初始化。

## 消费项目的同级源码依赖

消费项目选择同级源码检出时，必须遵守 [`docs/engineering/sibling-source-dependency.md`](docs/engineering/sibling-source-dependency.md) 的版本锁和 Git 对齐门禁。该规则适用于任何消费项目；消费项目负责把检查接入自己的 Verification、CI 与 Release 入口。HiAndroid 自身不规定消费项目的锁文件名或发布命令。

新增或移动本库文档时，先读取 [`docs/README.md`](docs/README.md)。

## Agent skills

### Issue tracker

本仓库的工作项和规格说明记录在 `jashanyng/HiAndroid` 的 GitHub Issues 中。详见 `docs/agents/issue-tracker.md`。

### Triage labels

分流使用 `needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix` 五个标签。详见 `docs/agents/triage-labels.md`。

### Domain docs

采用单上下文布局：根目录的 `GLOSSARY.md` 和 `docs/adr/` 分别记录术语与架构决策，按需创建。详见 `docs/agents/domain.md`。
