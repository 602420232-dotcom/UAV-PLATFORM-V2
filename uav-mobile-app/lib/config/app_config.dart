import 'dart:io' show Platform;

import 'package:flutter/material.dart';

class AppConfig {
  AppConfig._();

  static const String appName = '无人机路径规划系统';
  static const String appVersion = '1.0.0';

  // API 基础地址（自动适配运行环境）
  // - Android 模拟器: 10.0.2.2 (宿主机的别名)
  // - iOS 模拟器: localhost
  // - 真机/桌面: 替换为 WSL2 IP (172.27.212.53)
  static String get apiBaseUrl {
    if (Platform.isAndroid) {
      return 'http://10.0.2.2:8088';
    }
    return 'http://localhost:8088';
  }

  static const Map<String, String> apiEndpoints = {
    'platform': '/api/v1',
    'wrf': '/api/wrf',
    'forecast': '/api/forecast',
    'planning': '/api/planning',
    'assimilation': '/api/assimilation',
    'weather': '/api/weather',
    // edge 服务地址，用于真机部署时替换
    // 'edge': 'http://172.27.212.53:8000',
    'edge': 'http://localhost:8000',
  };

  /// 获取完整 API 路径
  static String api(String key, [String path = '']) {
    final base = apiEndpoints[key] ?? '';
    if (base.startsWith('http')) return '$base$path';
    return '${apiBaseUrl}$base$path';
  }

  static const Color primaryColor = Color(0xFF1677FF);
  static const Color successColor = Color(0xFF52C41A);
  static const Color warningColor = Color(0xFFFAAD14);
  static const Color errorColor = Color(0xFFFF4D4F);
  static const Color infoColor = Color(0xFF1677FF);

  static ThemeData lightTheme(BuildContext context) {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorSchemeSeed: primaryColor,
      appBarTheme: const AppBarTheme(
        centerTitle: true,
        elevation: 0,
      ),
      cardTheme: CardTheme(
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 12,
        ),
      ),
    );
  }

  static ThemeData darkTheme(BuildContext context) {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorSchemeSeed: primaryColor,
      appBarTheme: const AppBarTheme(
        centerTitle: true,
        elevation: 0,
      ),
      cardTheme: CardTheme(
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 12,
        ),
      ),
    );
  }
}
