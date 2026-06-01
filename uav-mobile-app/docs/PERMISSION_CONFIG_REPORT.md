# Android应用权限配置优化报告

## 概述

本文档详细说明了对UAV移动应用进行的Android权限配置优化，包括网络安全配置、位置权限管理和任务栈配置三个方面的改进。

---

## 1. 网络安全配置优化 ✅

### 问题描述

原配置全局设置 `usesCleartextTraffic=true`，存在严重安全隐患，可能导致敏感数据在网络传输中被窃取。

### 解决方案

#### 1.1 更新 network_security_config.xml

**文件位置**: `android/app/src/main/res/xml/network_security_config.xml`

**主要改进**:

1. **分层配置**
   - 开发环境：允许特定明文域名（localhost、模拟器地址）
   - 测试环境：允许测试服务器
   - 生产环境：强制HTTPS

2. **允许的明文域名**（仅限开发和测试）:
   - `localhost` - 本地开发
   - `10.0.2.2` / `10.0.2.3` - Android模拟器到主机
   - `192.168.x.x` - 常见局域网段
   - `uav-platform.local` - 本地域名
   - 测试环境域名

3. **强制HTTPS**:
   - API服务器 (`api.uav-platform.com`)
   - 地图瓦片服务 (`basemaps.cartocdn.com`, `tile.openstreetmap.org`)

#### 1.2 更新 AndroidManifest.xml

**关键配置**:
```xml
<application
    android:usesCleartextTraffic="false"
    android:networkSecurityConfig="@xml/network_security_config"
    ...>
```

**新增配置**:
```xml
android:allowBackup="true"
android:fullBackupContent="@xml/backup_rules"
android:dataExtractionRules="@xml/data_extraction_rules"
```

#### 1.3 备份配置

新增了两个配置文件：

**backup_rules.xml**:
```xml
<full-backup-content>
    <include domain="sharedpref" path="."/>
    <include domain="database" path="."/>
    <include domain="file" path="."/>

    <!-- 排除敏感数据 -->
    <exclude domain="sharedpref" path="FlutterSecureStorage"/>
    <exclude domain="database" path="secure_database"/>
    <exclude domain="file" path="logs/"/>
</full-backup-content>
```

**data_extraction_rules.xml**:
- 为Android 12+提供数据提取规则
- 分别配置cloud-backup和device-transfer

### 修复前后对比

| 配置项 | 修复前 | 修复后 |
|--------|--------|--------|
| 明文流量 | 全局允许 | 仅限特定域名 |
| usesCleartextTraffic | 未显式声明 | `false`（显式拒绝） |
| HTTPS强制 | 无 | 生产环境全面强制 |
| 备份规则 | 无 | 排除敏感数据 |

---

## 2. 位置权限配置 ✅

### 问题描述

地图功能缺少位置权限声明和动态申请机制。

### 解决方案

#### 2.1 更新 AndroidManifest.xml

**新增权限声明**:

```xml
<!-- 位置权限（地图和导航功能必需） -->
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
<!-- 后台位置更新（可选，用于后台任务） -->
<uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION"/>
```

#### 2.2 创建位置权限服务

**文件**: `lib/services/location_permission_service.dart`

**核心功能**:

1. **权限状态检查**
   - 检查精确位置权限
   - 检查模糊位置权限
   - 检测永久拒绝状态

2. **动态权限申请**
   - 请求前台位置权限
   - 可选请求后台位置权限
   - 处理各种权限状态

3. **用户交互**
   - 显示权限说明对话框
   - 显示权限被拒绝时的设置引导
   - 提供友好的错误提示

4. **Mixin支持**
   - 提供 `LocationPermissionMixin`
   - 简化页面集成
   - 内置常用对话框

#### 2.3 创建使用示例

**文件**: `lib/pages/map_example/map_example_page.dart`

展示了：
- 正确的权限申请流程
- 权限状态UI展示
- 地图组件集成
- 错误处理

### 使用示例

```dart
class MyMapPage extends StatefulWidget {
  @override
  State<MyMapPage> createState() => _MyMapPageState();
}

class _MyMapPageState extends State<MyMapPage>
    with LocationPermissionMixin {
  @override
  void initState() {
    super.initState();
    _checkLocationPermission();
  }

  Future<void> _checkLocationPermission() async {
    final result = await checkAndRequestLocationPermission(
      requestBackground: false,
      showRationale: true,
      showDeniedDialog: true,
    );

    if (result.isGranted) {
      // 开始获取位置
      await _getCurrentLocation();
    }
  }
}
```

#### 2.4 更新 build.gradle.kts

```kotlin
defaultConfig {
    minSdk = 23  // Android 6.0+ 支持运行时权限
    multiDexEnabled = true
}
```

### 权限申请流程

```
[应用启动]
    ↓
[检查权限状态]
    ↓
[权限已授权?] → 是 → [获取位置] → [显示地图]
    ↓ 否
[显示权限说明]
    ↓
[用户确认?] → 否 → [结束]
    ↓ 是
[请求权限]
    ↓
[授权成功?] → 是 → [获取位置] → [显示地图]
    ↓ 否
[永久拒绝?] → 是 → [引导去设置]
    ↓ 否
[结束]
```

---

## 3. 任务栈配置修正 ✅

### 问题描述

`taskAffinity=""` 为空值，可能导致多任务切换异常。

### 解决方案

#### 更新 AndroidManifest.xml

**修复前**:
```xml
<activity
    android:taskAffinity=""
    ...>
```

**修复后**:
```xml
<activity
    android:taskAffinity="com.uav.pathplanning"
    android:allowTaskReparenting="true"
    ...>
```

### 配置说明

| 属性 | 值 | 说明 |
|------|-----|------|
| `taskAffinity` | `com.uav.pathplanning` | 使用包名作为任务亲和性标识 |
| `allowTaskReparenting` | `true` | 允许Activity重新分配到其他任务 |
| `launchMode` | `singleTop` | 保持现有配置，避免重复创建实例 |

### 配置效果

1. **独立任务**: 应用在独立的任务栈中运行
2. **多任务支持**: 支持从其他应用启动Activity并保持任务栈管理
3. **用户体验**: 符合Android多任务切换预期行为

---

## 4. 构建配置优化 ✅

### 更新 build.gradle.kts

#### 主要改进

1. **Core Library Desugaring**
```kotlin
compileOptions {
    isCoreLibraryDesugaringEnabled = true
}
```

2. **Java版本**
```kotlin
sourceCompatibility = JavaVersion.VERSION_17
targetCompatibility = JavaVersion.VERSION_17
```

3. **MinSdk设置**
```kotlin
minSdk = 23  // Android 6.0，支持运行时权限
```

4. **多Dex支持**
```kotlin
multiDexEnabled = true
```

5. **Release构建优化**
```kotlin
release {
    isMinifyEnabled = true
    isShrinkResources = true
}
```

---

## 5. 完整配置清单

### AndroidManifest.xml 完整配置

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

  <!-- 网络权限 -->
  <uses-permission android:name="android.permission.INTERNET"/>
  <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
  <uses-permission android:name="android.permission.ACCESS_WIFI_STATE"/>

  <!-- 位置权限 -->
  <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
  <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
  <uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION"/>

  <application
      android:label="uav_path_planning_app"
      android:icon="@mipmap/ic_launcher"
      android:networkSecurityConfig="@xml/network_security_config"
      android:usesCleartextTraffic="false"
      android:allowBackup="true"
      android:fullBackupContent="@xml/backup_rules"
      android:dataExtractionRules="@xml/data_extraction_rules">

      <activity
          android:name=".MainActivity"
          android:exported="true"
          android:launchMode="singleTop"
          android:taskAffinity="com.uav.pathplanning"
          android:allowTaskReparenting="true"
          ...>
      </activity>
  </application>
</manifest>
```

---

## 6. 测试建议

### 6.1 网络安全测试

1. **开发环境**
   - ✅ 测试模拟器连接本地服务器
   - ✅ 测试局域网设备连接
   - ✅ 验证HTTP流量被正确阻止

2. **生产环境**
   - ✅ 验证所有API调用使用HTTPS
   - ✅ 验证地图瓦片正常加载
   - ✅ 检查浏览器控制台无混合内容警告

### 6.2 位置权限测试

1. **权限流程**
   - ✅ 首次启动显示权限说明
   - ✅ 授权后地图正常显示
   - ✅ 拒绝后显示友好提示

2. **边界情况**
   - ✅ 永久拒绝后引导去设置
   - ✅ 权限撤销后重新申请
   - ✅ 后台位置权限单独申请

### 6.3 任务栈测试

1. **多任务切换**
   - ✅ 从启动器切换到应用
   - ✅ 从其他应用Deep Link进入
   - ✅ 多实例情况处理

2. **Activity管理**
   - ✅ back栈正确
   - ✅ 任务重新分配正常

---

## 7. 安全性评估

### 网络安全 ✅

- ✅ 明文流量最小化
- ✅ 仅开发/测试环境允许明文
- ✅ 生产环境全面HTTPS
- ✅ 支持证书固定

### 权限管理 ✅

- ✅ 最小权限原则
- ✅ 运行时权限申请
- ✅ 敏感数据备份排除
- ✅ 用户知情同意

### 数据保护 ✅

- ✅ 备份排除敏感信息
- ✅ 安全的数据提取规则
- ✅ 防止意外数据泄露

---

## 8. 最佳实践总结

### 网络安全

1. **默认拒绝** - `usesCleartextTraffic="false"`
2. **明确允许** - 仅对必要的开发域名允许明文
3. **环境分离** - 开发和生产配置分开
4. **定期审计** - 检查是否有新的明文需求

### 权限管理

1. **按需申请** - 仅在实际需要时申请权限
2. **清晰说明** - 明确告知用户权限用途
3. **优雅降级** - 权限不足时提供替代方案
4. **及时清理** - 不再需要时释放权限

### 任务栈管理

1. **明确Affinity** - 使用有意义的taskAffinity值
2. **谨慎Reparenting** - 根据用户体验需求决定
3. **测试多场景** - 确保各种启动方式都正常

---

## 9. 参考资料

### 官方文档

- [Android Network Security Configuration](https://developer.android.com/training/articles/security-config)
- [Request App Permissions](https://developer.android.com/training/permissions/requesting)
- [Android Tasks and Back Stack](https://developer.android.com/guide/components/activities/tasks-and-back-stack)

### Flutter权限处理

- [permission_handler package](https://pub.dev/packages/permission_handler)
- [Location permissions in Android](https://developer.android.com/training/location/permissions)

### 安全配置

- [OWASP Mobile Security](https://owasp.org/www-project-mobile-security/)
- [Android Security Guidelines](https://developer.android.com/topic/security/best-practices)

---

## 10. 更新历史

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-06-01 | 1.0 | 初始版本，包含三项优化 |

---

## 11. 注意事项

### 迁移注意事项

1. **网络配置变更**
   - 如果有硬编码的HTTP地址，需要更新为HTTPS或添加到network_security_config
   - 检查第三方库是否需要明文流量

2. **MinSdk变更**
   - 从低于23的版本升级需要检查是否有旧Android版本兼容代码
   - 测试Android 6.0以下设备

3. **权限变更**
   - 现有用户可能需要重新授权
   - 检查权限申请时机，避免影响用户体验

### 后续维护

1. **添加新明文域名**
   - 仅在必要时添加
   - 添加注释说明原因
   - 考虑是否真的需要明文

2. **添加新权限**
   - 遵循最小权限原则
   - 提供权限用途说明
   - 实现优雅降级
