# 变更日志（Changelog）

本文件记录 HiAndroid 效率库所有公开可见的版本变更，并作为每次版本更新说明（Release Notes）的唯一事实源。日常尚未发版的公开改动统一记入 `## [Unreleased]`；执行 `python3 scripts/bump_version.py <x.y.z>` 递增版本号时，会自动将 `## [Unreleased]` 下的条目归档到对应新版本章节。

## [Unreleased]

## [0.0.1]

### 新增

- 建立 HiAndroid 制作期 `0.0.1` 统一基线与 Maven 发布白名单，覆盖 22 个公开模块（`com.jashanyng:*:0.0.1`）：
  - 基础与平台核心：`:base`（纯 Kotlin 模型及日志、统计、社会化分享契约，无 Android/UI 依赖）、`:core`（轻量 Android 平台工具，无 Compose 依赖）。
  - 导航（Navigation）：`:nav`（URL/URI 导航路由契约与分类模型）、`:nav:compose`（Jetpack Navigation Compose 适配器）、`:nav:umeng-ulink`（可选友盟 U-Link 唤醒与延迟路由适配器）。
  - 网络（Network）：`:net`（网络契约与模型，含 `SseLineParser` 流式行解析器）、`:net:retrofit`（Retrofit、OkHttp 与 Moshi 适配器）。
  - 持久化（Store）：`:store`（`SecureStringStore`、`StringPreferenceStore`、`AppCacheStore` 与 `AppCacheManager` 契约）、`:store:datastore`（AndroidX DataStore 偏好适配器）、`:store:keystore`（Android Keystore 加密安全字符串适配器）。
  - 通用视图与可选扩展（Suite）：`:suite`（通用 Jetpack Compose 组件，含 `SuiteHorizontalDivider`、`SuitePdfViewer`、`SuiteSnackbarHost`、`SuiteActionMenu` 及共享公开字符串资源）、`:suite:coil`（可选 Coil 图片查看器与缓存适配器）、`:suite:media3`（可选 Media3 媒体播放页）、`:suite:log-timber`（可选 Timber 日志适配器，支持 `supportsSensitiveData` 显式声明）、`:suite:aliyun-emas-core`（可选阿里云 EMAS 移动监控适配器）、`:suite:umeng-core`（可选友盟隐私授权生命周期运行时）、`:suite:analytics-umeng`（可选友盟统计适配器）、`:suite:performance-umeng`（可选友盟 U-APM 性能监控适配器）、`:suite:socialsharing-umeng`（可选友盟社会化分享适配器）。
  - 便捷聚合与独立能力库：`:hiandroid`（聚合通用默认模块的可选入口，不包含厂商 SDK 与重型媒体/图片扩展）、`:github:model:core`（独立于 `:base` 的共享 GitHub 数据模型）、`:github:trending`（独立于 `:base` 的 GitHub Trending 接口与 HTML 解析库）。
- 保留 3 个仅通过同级源码复合构建接入的社会化分享平台适配器（`:suite:socialsharing-umeng-sms`、`:suite:socialsharing-umeng-email`、`:suite:socialsharing-umeng-wechat`），暂不纳入公开发布白名单。
- 落地制作期版本与发布校验门禁脚本：`scripts/verify_maven_local.py`、`scripts/bump_version.py` 及配套单元测试 `scripts/test_version_guard.py`。
