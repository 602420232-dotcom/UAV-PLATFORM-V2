# Flutter 移动端构建指南

> **文档版本**: v1.0  
> **最后更新**: 2026-05-31  
> **适用平台**: Android, iOS, Web, Windows, macOS, Linux

---

## 目录

1. [环境准备](#1-环境准备)
2. [项目结构](#2-项目结构)
3. [依赖安装](#3-依赖安装)
4. [开发运行](#4-开发运行)
5. [构建打包](#5-构建打包)
6. [平台特定配置](#6-平台特定配置)
7. [调试与测试](#7-调试与测试)
8. [部署发布](#8-部署发布)
9. [常见问题](#9-常见问题)

---

## 1. 环境准备

### 1.1 系统要求

| 平台 | 操作系统 | 最低配置 |
|------|---------|---------|
| **Android** | Windows/macOS/Linux | 8GB RAM, 10GB 磁盘空间 |
| **iOS** | macOS | 8GB RAM, 10GB 磁盘空间 |
| **Web** | 任意 | 现代浏览器 |
| **Windows** | Windows 10+ | 8GB RAM, 10GB 磁盘空间 |
| **macOS** | macOS 10.14+ | 8GB RAM, 10GB 磁盘空间 |
| **Linux** | Ubuntu 18.04+ | 8GB RAM, 10GB 磁盘空间 |

### 1.2 安装 Flutter SDK

```bash
# Windows (使用 git)
cd C:\Dev
git clone https://github.com/flutter/flutter.git -b stable

# 设置 PATH 环境变量
# 添加 C:\Dev\flutter\bin 到 PATH

# 验证安装
flutter --version
```

### 1.3 安装依赖工具

| 工具 | 用途 | 安装命令 |
|------|------|---------|
| **Android Studio** | Android 开发 | https://developer.android.com/studio |
| **Xcode** | iOS 开发 | App Store (仅 macOS) |
| **VS Code** | 代码编辑器 | https://code.visualstudio.com |
| **Chrome** | Web 调试 | https://www.google.com/chrome |

### 1.4 配置平台工具

```bash
# Android 授权
flutter doctor --android-licenses

# iOS 授权 (仅 macOS)
sudo xcodebuild -license

# 检查环境
flutter doctor
```

---

## 2. 项目结构

```
uav-mobile-app/
├── lib/
│   ├── main.dart                 # 应用入口
│   ├── app.dart                  # 应用配置
│   ├── config/
│   │   ├── app_config.dart       # 应用配置
│   │   ├── api_endpoints.dart    # API 端点
│   │   └── theme_config.dart     # 主题配置
│   ├── models/
│   │   ├── user.dart
│   │   ├── drone.dart
│   │   ├── task.dart
│   │   └── weather.dart
│   ├── services/
│   │   ├── api_client.dart       # HTTP 客户端
│   │   ├── auth_service.dart     # 认证服务
│   │   ├── drone_service.dart    # 无人机服务
│   │   ├── task_service.dart     # 任务服务
│   │   └── weather_service.dart   # 气象服务
│   ├── providers/
│   │   ├── auth_provider.dart    # 认证状态
│   │   ├── drone_provider.dart    # 无人机状态
│   │   └── task_provider.dart     # 任务状态
│   ├── screens/
│   │   ├── login_page.dart
│   │   ├── home_page.dart
│   │   ├── drone_list_page.dart
│   │   ├── task_page.dart
│   │   └── map_page.dart
│   └── widgets/
│       ├── drone_card.dart
│       ├── task_card.dart
│       └── loading_widget.dart
├── android/                      # Android 原生代码
├── ios/                          # iOS 原生代码
├── web/                          # Web 资源
├── windows/                      # Windows 原生代码
├── macos/                        # macOS 原生代码
├── linux/                        # Linux 原生代码
├── pubspec.yaml                  # 依赖配置
└── README.md                     # 本文档
```

---

## 3. 依赖安装

### 3.1 更新依赖配置

**文件**: `pubspec.yaml`

```yaml
name: uav_mobile_app
description: UAV Path Planning Mobile Application
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter

  # UI
  cupertino_icons: ^1.0.6
  flutter_map: ^6.1.0
  latlong2: ^0.9.0
  
  # 状态管理
  flutter_riverpod: ^2.4.9
  
  # 网络
  dio: ^5.4.0
  retrofit: ^4.0.1
  
  # 存储
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0
  
  # 工具
  intl: ^0.19.0
  logger: ^2.2.0
  permission_handler: ^11.2.0
  
  # 地图
  geolocator: ^12.0.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.1
  build_runner: ^2.4.8
  retrofit_generator: ^8.0.0

flutter:
  uses-material-design: true
  
  assets:
    - assets/images/
    - assets/icons/
```

### 3.2 安装依赖

```bash
# 安装依赖
flutter pub get

# 更新依赖
flutter pub upgrade

# 清理并重新安装
flutter clean
flutter pub get
```

### 3.3 生成代码

```bash
# 如果使用 retrofit
dart run build_runner build
```

---

## 4. 开发运行

### 4.1 启动开发服务器

```bash
# 启动所有平台
flutter run -d chrome,edge

# 指定设备
flutter devices                    # 查看可用设备
flutter run -d <device-id>        # 运行到指定设备
```

### 4.2 Web 开发

```bash
# 启动 Web 服务器
flutter run -d chrome

# 指定端口
flutter run -d chrome --web-port=8080

# 启用热重载
flutter run -d chrome --hot
```

### 4.3 Android 开发

```bash
# 启动 Android 模拟器
emulator -avd Pixel_6_API_33

# 运行到模拟器
flutter run -d emulator-5554

# 运行到真机 (USB 连接)
flutter run -d android
```

### 4.4 iOS 开发 (macOS)

```bash
# 启动 iOS 模拟器
open -a Simulator

# 运行到模拟器
flutter run -d iPhone

# 运行到真机 (需要签名)
flutter run -d iphone --release
```

### 4.5 Windows/macOS/Linux 开发

```bash
# Windows
flutter run -d windows

# macOS
flutter run -d macos

# Linux
flutter run -d linux
```

---

## 5. 构建打包

### 5.1 Web 构建

```bash
# 构建生产版本
flutter build web

# 指定输出目录
flutter build web --output-dir=build/web

# 构建并包含 source maps
flutter build web --source-maps
```

**输出目录**: `build/web/`

**部署文件**:
```
build/web/
├── index.html
├── main.dart.js
├── flutter.js
├── flutter_service_worker.js
└── assets/
```

### 5.2 Android 构建

#### Debug APK

```bash
flutter build apk --debug

# 输出: build/app/outputs/flutter-apk/app-debug.apk
```

#### Release APK

```bash
# 生成签名密钥 (首次)
keytool -genkey -v -keystore ~/upload-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias upload

# 配置签名 (android/app/build.gradle)
android {
  signingConfigs {
    release {
      keyAlias upload
      keyPassword ******
      storeFile keystore.jks
      storePassword ******
    }
  }
  buildTypes {
    release {
      signingConfig signingConfigs.release
    }
  }
}

# 构建 Release APK
flutter build apk --release

# 输出: build/app/outputs/flutter-apk/app-release.apk
```

#### App Bundle (Google Play)

```bash
flutter build appbundle --release

# 输出: build/app/outputs/bundle/release/app-release.aab
```

### 5.3 iOS 构建 (macOS)

#### Simulator Build

```bash
flutter build ios --simulator --no-codesign
```

#### Release Build

```bash
# 打开 Xcode 配置
open ios/Runner.xcworkspace

# 在 Xcode 中:
# 1. 选择 Team (签名)
# 2. 选择 Generic iOS Device
# 3. Product > Archive
# 4. Distribute App (App Store/Ad Hoc/Enterprise)
```

### 5.4 Windows 构建

```bash
# Debug 构建
flutter build windows --debug

# Release 构建
flutter build windows --release

# 输出: build/windows/runner/Release/
```

### 5.5 macOS 构建

```bash
# Debug 构建
flutter build macos --debug

# Release 构建
flutter build macos --release

# 输出: build/macos/Build/Products/Release/
```

### 5.6 Linux 构建

```bash
# Release 构建
flutter build linux --release

# 输出: build/linux/x64/release/bundle/
```

---

## 6. 平台特定配置

### 6.1 Android 配置

**文件**: `android/app/src/main/AndroidManifest.xml`

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <!-- 网络权限 -->
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
    
    <!-- 位置权限 -->
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
    
    <!-- WiFi 权限 -->
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE"/>
    <uses-permission android:name="android.permission.CHANGE_WIFI_STATE"/>
    
    <application
        android:label="UAV Planner"
        android:name="${applicationName}"
        android:icon="@mipmap/ic_launcher"
        android:usesCleartextTraffic="true">  <!-- 开发环境允许 HTTP -->
        
        <!-- Web 平台支持 -->
        <meta-data
            android:name="flutterEmbedding"
            android:value="2" />
    </application>
</manifest>
```

**网络配置**: `android/app/src/main/res/xml/network_security_config.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <!-- 开发环境 -->
        <domain includeSubdomains="true">localhost</domain>
        <domain includeSubdomains="true">10.0.2.2</domain>  <!-- Android 模拟器 -->
    </domain-config>
    <base-config cleartextTrafficPermitted="false">
        <!-- 生产环境强制 HTTPS -->
        <trust-anchors>
            <certificates src="system"/>
        </trust-anchors>
    </base-config>
</network-security-config>
```

### 6.2 iOS 配置

**文件**: `ios/Runner/Info.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- 网络 -->
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <false/>  <!-- 生产环境禁用 -->
        <key>NSAllowsLocalNetworking</key>
        <true/>
    </dict>
    
    <!-- 位置 -->
    <key>NSLocationWhenInUseUsageDescription</key>
    <string>需要位置权限来显示无人机当前位置</string>
    <key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
    <string>需要位置权限来追踪无人机</string>
    
    <!-- 相机 -->
    <key>NSCameraUsageDescription</key>
    <string>需要相机权限来扫描二维码</string>
</dict>
</plist>
```

### 6.3 Web 配置

**文件**: `web/index.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="UAV Path Planning Mobile Application">
    <title>UAV Planner</title>
    
    <!-- PWA 支持 -->
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#2196F3">
    
    <!-- iOS PWA -->
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="apple-touch-icon" href="icons/Icon-192.png">
</head>
<body>
    <script src="flutter.js" defer></script>
</body>
</html>
```

---

## 7. 调试与测试

### 7.1 开发工具

| 工具 | 用途 | 快捷键 |
|------|------|-------|
| **Flutter DevTools** | UI 检查、性能分析 | `Ctrl+Shift+I` |
| **Dart DevTools** | Dart 调试 | `Ctrl+Shift+D` |
| **Chrome DevTools** | Web 调试 | F12 |

### 7.2 日志配置

**文件**: `lib/utils/logger.dart`

```dart
import 'package:logger/logger.dart';

final logger = Logger(
  printer: PrettyPrinter(
    methodCount: 2,
    errorMethodCount: 8,
    lineLength: 120,
    colors: true,
    printEmojis: true,
    printTime: true,
  ),
  level: kReleaseMode ? Level.warning : Level.debug,
);

void logRequest(String method, String url, {Map<String, dynamic>? data}) {
  logger.d('📤 $method $url', data: data);
}

void logResponse(int statusCode, dynamic data) {
  if (statusCode >= 200 && statusCode < 300) {
    logger.d('📥 Response $statusCode', data: data);
  } else {
    logger.e('❌ Response $statusCode', data: data);
  }
}
```

### 7.3 单元测试

```bash
# 运行所有测试
flutter test

# 运行指定测试
flutter test test/auth_service_test.dart

# 生成覆盖率报告
flutter test --coverage
genhtml coverage/lcov.info -o coverage/html
```

### 7.4 集成测试

```bash
# 运行集成测试
flutter test integration_test/app_test.dart

# Web 集成测试
flutter test -platform chrome integration_test/
```

---

## 8. 部署发布

### 8.1 Android 发布

1. **生成签名密钥**
2. **配置 `android/key.properties`**
3. **构建 Release APK**
4. **上传到 Google Play Console**

```bash
# 命令行构建 (需要配置 key.properties)
flutter build apk --release
```

### 8.2 iOS 发布

1. **配置 Xcode 项目签名**
2. **Archive 构建**
3. **上传到 App Store Connect**

```bash
# 导出 IPA
flutter build ipa
```

### 8.3 Web 部署

**静态托管**:

```bash
# 构建
flutter build web

# 部署到 Firebase Hosting
firebase deploy --only hosting

# 部署到 Vercel
vercel --prod

# 部署到 Nginx
cp -r build/web/* /var/www/html/
```

### 8.4 Windows/macOS 发布

```bash
# 构建
flutter build windows --release
flutter build macos --release

# 分发
# - Windows: 生成 .exe 安装包
# - macOS: 生成 .dmg 安装包
```

---

## 9. 常见问题

### 9.1 构建失败

| 问题 | 解决方案 |
|------|---------|
| `Android SDK not found` | 运行 `flutter doctor` 检查 Android SDK |
| `Xcode not installed` | 仅 macOS 支持 iOS 构建 |
| `Gradle build failed` | 清理缓存 `flutter clean && flutter pub get` |
| `Pod install failed` | 删除 `ios/Podfile.lock` 并重新 `flutter pub get` |

### 9.2 运行时错误

| 错误 | 解决方案 |
|------|---------|
| `Network request failed` | 检查网络连接和 API 地址配置 |
| `401 Unauthorized` | 检查 Token 是否过期或无效 |
| `Platform exception` | 检查平台插件是否正确配置 |

### 9.3 性能问题

| 问题 | 解决方案 |
|------|---------|
| 启动慢 | 使用 `FlutterDevTools` 分析启动时间 |
| 列表卡顿 | 使用 `ListView.builder` 懒加载 |
| 图片加载慢 | 使用缓存 `cached_network_image` |

---

## 附录 A: API 端点配置

**文件**: `lib/config/api_endpoints.dart`

```dart
class ApiEndpoints {
  // 开发环境
  static const String baseUrl = 'http://10.0.2.2:8080';  // Android 模拟器
  // static const String baseUrl = 'http://localhost:8080';  // iOS 模拟器/Web
  
  // 生产环境
  // static const String baseUrl = 'https://api.uav-platform.com';
  
  // 端点
  static const String login = '/api/v1/auth/login';
  static const String logout = '/api/v1/auth/logout';
  static const String refresh = '/api/v1/auth/refresh';
  static const String drones = '/api/v1/drones';
  static const String tasks = '/api/v1/tasks';
  static const String weather = '/api/v1/weather';
  static const String planning = '/api/v1/planning';
}
```

## 附录 B: 环境变量

创建 `.env` 文件:

```bash
# API 配置
API_BASE_URL=http://10.0.2.2:8080

# 地图配置
MAP_CESIUM_TOKEN=your_cesium_token_here

# 调试模式
DEBUG_MODE=true
```

## 附录 C: 相关文档

- [Flutter 官方文档](https://flutter.dev/docs)
- [Riverpod 状态管理](https://riverpod.dev/)
- [Dio HTTP 客户端](https://dio.me/)
- [Flutter Map](https://docs.fltmap.dev/)

---

> **维护者**: UAV Platform Team  
> **文档版本**: 1.0  
> **创建日期**: 2026-05-31
