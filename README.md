# HiAndroid

HiAndroid 效率库是与具体业务无关、可独立发布的 Kotlin/Android 通用效率库，提供平台无关基础契约、Android 与 Jetpack Compose 工具组件、Retrofit 网络集成，以及可复用的 GitHub 模型与 GitHub Trending 解析能力，不包含任何消费项目的专属业务逻辑。

> **当前状态**：本仓库处于**制作期**，未发布源码与本地 Maven 构件版本基线统一为 `0.0.1`；制作期日常源码提交暂不预先创建 Git 标签，也不向 Maven Central 等外部制品源公开发布。

## 公开模块与分层

以下为发布白名单中全部 22 个公开模块的 `0.0.1` 源码与 Maven Local 坐标；短信、邮件与微信社会化分享平台适配器（`:suite:socialsharing-umeng-sms`、`:suite:socialsharing-umeng-email`、`:suite:socialsharing-umeng-wechat`）暂仅通过同级源码复合构建接入，待外部 SDK 发布条件核验后另行纳入公开白名单。

| Gradle 模块 | Maven 坐标 | 产物类型 | 核心职责 |
| --- | --- | --- | --- |
| `:base` | `com.jashanyng:base:0.0.1` | JAR | 纯 Kotlin 模型与日志、统计、社会化分享核心契约 |
| `:core` | `com.jashanyng:core:0.0.1` | AAR | 轻量级 Android 平台工具（无 Compose 依赖） |
| `:nav` | `com.jashanyng:nav:0.0.1` | JAR | URL 与 URI 导航路由契约与分类模型 |
| `:nav:compose` | `com.jashanyng:nav-compose:0.0.1` | AAR | Jetpack Navigation Compose 适配器 |
| `:nav:umeng-ulink` | `com.jashanyng:nav-umeng-ulink:0.0.1` | AAR | 可选友盟 U-Link 唤醒与延迟路由适配器 |
| `:net` | `com.jashanyng:net:0.0.1` | JAR | 网络契约与模型（含 `SseLineParser` 流式行解析） |
| `:net:retrofit` | `com.jashanyng:net-retrofit:0.0.1` | JAR | Retrofit、OkHttp 与 Moshi 适配器 |
| `:store` | `com.jashanyng:store:0.0.1` | JAR | 持久化契约与可复用缓存组合 |
| `:store:datastore` | `com.jashanyng:store-datastore:0.0.1` | AAR | AndroidX DataStore 偏好适配器 |
| `:store:keystore` | `com.jashanyng:store-keystore:0.0.1` | AAR | Android Keystore 加密安全字符串适配器 |
| `:suite` | `com.jashanyng:suite:0.0.1` | AAR | 通用 Jetpack Compose 视图组件 |
| `:suite:coil` | `com.jashanyng:suite-coil:0.0.1` | AAR | 可选图片查看器与 Coil 缓存适配器 |
| `:suite:media3` | `com.jashanyng:suite-media3:0.0.1` | AAR | 可选 Media3 媒体播放页 |
| `:suite:log-timber` | `com.jashanyng:suite-log-timber:0.0.1` | AAR | 可选 Timber 日志适配器：`TimberAppLogger` 转发完整 `LogEntry`，`LogEntryTree` 无损接收（含 attributes、tag、throwable）并将直接 Timber 调用合成为条目；是否接收敏感数据由宿主通过 `supportsSensitiveData` 显式声明 |
| `:suite:aliyun-emas-core` | `com.jashanyng:suite-aliyun-emas-core:0.0.1` | AAR | 可选阿里云 EMAS 移动监控适配器 |
| `:suite:umeng-core` | `com.jashanyng:suite-umeng-core:0.0.1` | AAR | 可选友盟隐私授权生命周期运行时 |
| `:suite:analytics-umeng` | `com.jashanyng:suite-analytics-umeng:0.0.1` | AAR | 可选友盟统计适配器 |
| `:suite:performance-umeng` | `com.jashanyng:suite-performance-umeng:0.0.1` | AAR | 可选友盟 U-APM 性能监控适配器 |
| `:suite:socialsharing-umeng` | `com.jashanyng:suite-socialsharing-umeng:0.0.1` | AAR | 可选友盟社会化分享适配器 |
| `:hiandroid` | `com.jashanyng:hiandroid:0.0.1` | AAR | 通用模块与默认适配器的可选便捷聚合入口 |
| `:github:model:core` | `com.jashanyng:github-model-core:0.0.1` | JAR | 独立于 `:base` 的共享 GitHub 数据模型 |
| `:github:trending` | `com.jashanyng:github-trending:0.0.1` | JAR | 独立于 `:base` 的 GitHub Trending 接口与 HTML 解析库 |

### 模块分层与关键契约

- `:base` 不含 Android 或 UI 依赖；
- `:core` 提供轻量 Android 平台工具（字符串资源访问、`Context` 扩展、Google Play 商店与系统支持链接设置跳转等），不引入 Compose；
- `:nav`、`:net` 与 `:store` 分别定义导航、网络与持久化契约，具体实现置于对应子模块并单向依赖父模块；
- `:store` 提供 `SecureStringStore`、`StringPreferenceStore`、`AppCacheStore` 与 `AppCacheManager` 契约，由 `:store:keystore` 提供 Android Keystore 加密实现、`:store:datastore` 提供 DataStore 偏好实现；消费项目自身拥有数据库表结构、业务键与用户数据隔离策略；
- `:suite` 承载通用 Compose 视图（`SuiteHorizontalDivider`、`SuitePdfViewer`、`SuiteSnackbarHost` 等）；Coil（`CoilAppCacheStore`、`SuiteImageViewer`）、Media3（`SuiteMediaPlayerPage`）、Timber 与厂商 SDK 各自置于可选的 `:suite:*` 子模块；`:hiandroid` 仅聚合通用默认模块，不包含厂商 SDK 与重型媒体/图片扩展，也不会自动初始化任何厂商 SDK；
- `:net` 提供行式 Server-Sent Events 流解析器 `SseLineParser`。

### 共享 Android UI 字符串资源

`:suite` 通过 `com.jashanyng.suite.R.string` 公开 `suite_action_retry`（`Retry` / `重试`）与 `suite_navigate_back_content_description`（`Navigate back` / `返回`），并在 `suite/src/main/res/values/public.xml` 登记；其余组件字符串保持内部可见。内置网页组件的后退操作保留自身专属描述以区分浏览器历史导航。修改公共资源时须同步维护默认（英文）与中文翻译。

### 通用 Compose 操作菜单（`SuiteActionMenu`）

`:suite` 提供锚定式纯文字操作菜单 `SuiteActionMenu` 与 `SuiteActionMenuItem`。将菜单与其触发器置于同一 `Box` 内，父边界决定锚点位置；组件采用统一近黑背景、白色文字、16dp 圆角与至少 48dp 触控高度（亮暗主题一致），自动在窗口范围约束位置、将箭头指向触发器中心并在下方空间不足时切换至触发器上方；宽度随最长选项文案加两侧各 30dp（共 60dp）内边距自适应并受可用窗口宽度限制，超长列表可滚动。调用方负责选项文案、顺序与回调，点击可用选项后先关闭菜单再执行回调。详细视觉与交互契约见 [`docs/engineering/ui-components.md`](docs/engineering/ui-components.md)。

## 构建要求与本地验证

- **JDK**：JDK 21（供 Gradle Daemon 运行）
- **Gradle**：仓库自带 Gradle Wrapper（`9.5.0`）
- **Kotlin**：消费项目使用 Kotlin `2.4.10` 或兼容 `2.4` 的编译器
- **Android SDK / 字节码基线**：Android SDK `37`、`minSdk = 30`，Java 与 Kotlin JVM 字节码目标均为 `11`

```bash
# 运行全量检查（单元测试、Android Lint 等）
./gradlew clean check

# 发布白名单内全部 22 个模块至本地 Maven（~/.m2/repository/com/jashanyng/）
./gradlew publishToMavenLocal

# 校验 Maven Local 构件文件、坐标与内部传递依赖
python3 scripts/verify_maven_local.py
```

## 消费接入方式

### 开发期（同级源码依赖）

开发期消费项目将本仓库作为独立 Git 仓库检出在消费项目同级目录 `../HiAndroid`，通过根 `settings.gradle.kts` 的 Gradle Composite Build 将声明的 `com.jashanyng:*` 坐标替换为本地源码工程，同时提交包含 **40 位完整 commit SHA** 的版本锁文件并接入自动化阻断门禁（详见 [`docs/engineering/sibling-source-dependency.md`](docs/engineering/sibling-source-dependency.md)）。

```kotlin
// settings.gradle.kts 示例（仅展示坐标替换，完整锁校验门禁见消费端接入规范）
includeBuild("../HiAndroid") {
    dependencySubstitution {
        substitute(module("com.jashanyng:base")).using(project(":base"))
        substitute(module("com.jashanyng:core")).using(project(":core"))
        substitute(module("com.jashanyng:nav")).using(project(":nav"))
        substitute(module("com.jashanyng:nav-compose")).using(project(":nav:compose"))
        substitute(module("com.jashanyng:net")).using(project(":net"))
        substitute(module("com.jashanyng:net-retrofit")).using(project(":net:retrofit"))
        substitute(module("com.jashanyng:store")).using(project(":store"))
        substitute(module("com.jashanyng:store-datastore")).using(project(":store:datastore"))
        substitute(module("com.jashanyng:store-keystore")).using(project(":store:keystore"))
        substitute(module("com.jashanyng:suite")).using(project(":suite"))
        substitute(module("com.jashanyng:suite-coil")).using(project(":suite:coil"))
        substitute(module("com.jashanyng:suite-media3")).using(project(":suite:media3"))
        substitute(module("com.jashanyng:suite-log-timber")).using(project(":suite:log-timber"))
        substitute(module("com.jashanyng:hiandroid")).using(project(":hiandroid"))
        substitute(module("com.jashanyng:github-model-core")).using(project(":github:model:core"))
        substitute(module("com.jashanyng:github-trending")).using(project(":github:trending"))
    }
}
```

消费模块自身仍使用公开 Maven 坐标声明依赖：

```kotlin
dependencies {
    implementation("com.jashanyng:suite:0.0.1")
}
```

### 本地二进制测试（Maven Local）

在通过 `./gradlew publishToMavenLocal` 发布 `0.0.1` 构件至本地 `~/.m2/repository` 后，独立消费工程可通过 `mavenLocal()` 验证 POM、Module Metadata 与传递依赖解析：

```kotlin
repositories {
    google()
    mavenLocal()
    mavenCentral()
}

dependencies {
    implementation("com.jashanyng:hiandroid:0.0.1")
    implementation("com.jashanyng:github-trending:0.0.1")
}
```

多模块消费项目应按各模块编译边界选择最小所需子坐标；厂商 SDK 与可选 Coil、Media3、Timber 适配器不包含在 `:hiandroid` 中。

### 发布期（已发布固定版本依赖）

消费项目进入对外发布、提审或上架阶段后，**必须**移除 `includeBuild` 同级源码覆盖，改在依赖目录锁定已正式对外发布的精确裸 `x.y.z` 版本（首次正式对外发布至 Maven Central 时版本定为 `1.0.0`，并创建裸标签 `1.0.0`）：

```kotlin
dependencies {
    implementation("com.jashanyng:suite:1.0.0")
    implementation("com.jashanyng:github-trending:1.0.0")
}
```

## 演进生命周期与裸 `x.y.z` 版本规则

- **三阶段演进生命周期**：按成熟度划分为**制作期**（当前阶段，允许重塑组织结构且不留兼容层，主动沉淀通用能力）→ **改进完善期**（组织结构冻结、界内打磨接口仍无需向后兼容）→ **维护期**（结构冻结且严格向后兼容，新增功能须先出具评估报告并获维护者同意）。阶段切换权完全归属维护者显式决定。
- **裸 `x.y.z` 版本与标签规则**：所有版本号定义、锁引用与 Git 标签一律使用无 `v` 前缀的裸 `x.y.z` 格式。制作期从 `0.0.1` 起步并仅递增 `z`（不预先打标签）；首次对外发布/提审锁定正式制品定为 `1.0.0` 并打裸标签 `1.0.0`；`1.0.0` 后 `x` 为重大代际、`y` 为项目周期批次协同递增、`z` 为同批次功能与修复递增。已正式发布的版本与标签不可覆盖。完整规则见 [`AGENTS.md`](AGENTS.md)。

## 可选友盟微信分享模块

`:suite:socialsharing-umeng-wechat` 目前不进入公开发布白名单，供宿主通过复合构建以 `com.jashanyng:suite-socialsharing-umeng-wechat` 消费。它引入 U-Share 7.3.7 微信处理模块与微信 OpenSDK 6.8.24，避免对仅需短信/邮件分享的宿主产生传递依赖。宿主需提供公开 AppID、受限的 `FileProvider` authority，以及位于 `<applicationId>.wxapi.WXEntryActivity` 且继承 `UmengSocialSharingWeChatCallbackActivity` 的回调 Activity，并确保回调就绪检查遵循隐私授权状态。分享场景下 AppSecret 置空，授权与密钥交换应在服务端完成。`SocialSharingContent.image` 仅接受可移植的 HTTPS URL 或本地文件路径，图片选择、资源加载与缩略图策略归属宿主应用。

## 文档与许可证

- 智能体协作与演进规则：[`AGENTS.md`](AGENTS.md)
- 文档索引：[`docs/README.md`](docs/README.md)
- 开源许可证：[Apache License 2.0](LICENSE)
